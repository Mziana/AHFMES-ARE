"""
Hourly Stability & Resilience Harness (Phase 5 Operational Readiness).
Supports discrete hourly / step-based stability runs with memory drift,
latency telemetry, and circuit breaker health tracking.
"""

import math
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from are.evidence import EvidenceLedger
from are.hasher import compute_sha256
from are.health_monitor import HealthStatus, SystemHealthMonitor, _get_process_memory_mb
from are.mt5_gateway import MT5ExecutionGateway, MT5OrderRequest
from are.safety import CapitalSafetyKernel, SafetyLimits
from are.storage import EventStore


@dataclass
class HourlyTelemetryRecord:
    hour_index: int
    start_timestamp: float
    end_timestamp: float
    ticks_processed: int
    orders_dispatched: int
    orders_vetoed: int
    p50_latency_ms: float
    p95_latency_ms: float
    max_latency_ms: float
    health_status: str
    circuit_breaker_trips: int
    peak_drawdown_observed: float
    estimated_memory_kb: float
    checkpoint_hash: str = ""


class HourlyStabilityHarness:
    """
    Executes and monitors discrete hourly stability test blocks for Phase 5 verification.
    Provides rigorous audit logs per hour block without requiring 24/7 continuous online monitoring.
    """

    def __init__(
        self,
        safety_kernel: CapitalSafetyKernel,
        gateway: MT5ExecutionGateway,
        health_monitor: SystemHealthMonitor,
        evidence_ledger: EvidenceLedger,
        event_store: EventStore,
    ):
        self.safety_kernel = safety_kernel
        self.gateway = gateway
        self.health_monitor = health_monitor
        self.evidence_ledger = evidence_ledger
        self.event_store = event_store
        self.hourly_records: List[HourlyTelemetryRecord] = []
        self._circuit_breaker_trips = 0

    def run_simulated_hour_block(
        self,
        hour_index: int,
        ticks_per_hour: int = 3600,
        base_price: float = 50000.0,
        volatility_scale: float = 1.0,
        inject_anomaly: bool = False,
    ) -> HourlyTelemetryRecord:
        """
        Executes a single 1-hour simulation block (3,600 ticks by default)
        and computes operational telemetry.
        """
        t_start = time.time()
        latencies: List[float] = []
        orders_dispatched = 0
        orders_vetoed = 0
        peak_dd = 0.0

        current_price = base_price
        for i in range(ticks_per_hour):
            t_tick_start = time.perf_counter()

            # Price diffusion
            drift = math.sin(i * 0.02) * (10.0 * volatility_scale)
            current_price = max(100.0, current_price + drift)

            # Drawdown check from gateway
            acc_info = self.gateway.get_account_info(default_equity=10000.0)
            cur_dd = float(acc_info.get("drawdown", 0.0))
            peak_dd = max(peak_dd, cur_dd)

            # Simulated signal injection
            if i % 120 == 0:  # Order every 2 minutes of simulated time
                action = "BUY" if i % 240 == 0 else "SELL"
                if inject_anomaly and i == ticks_per_hour // 2:
                    # Injected anomaly: huge volume to test veto
                    req = MT5OrderRequest(symbol="BTCUSD", action=action, volume=50.0, price=current_price)
                else:
                    req = MT5OrderRequest(symbol="BTCUSD", action=action, volume=0.01, price=current_price)

                risk_state = {
                    "drawdown": cur_dd,
                    "volatility": volatility_scale,
                    "order_count": self.gateway.get_recent_order_count(60.0),
                }

                success, _, status_msg = self.gateway.execute_order(req, risk_state)
                if success:
                    orders_dispatched += 1
                else:
                    orders_vetoed += 1
                    if "CSK_VETO" in status_msg:
                        self._circuit_breaker_trips += 1

            t_tick_end = time.perf_counter()
            latencies.append((t_tick_end - t_tick_start) * 1000.0)

        t_end = time.time()

        # Telemetry calculations
        latencies.sort()
        p50 = latencies[int(0.50 * len(latencies))] if latencies else 0.0
        p95 = latencies[int(0.95 * len(latencies))] if latencies else 0.0
        max_lat = max(latencies) if latencies else 0.0

        # Real Process Working Set RAM via OS ctypes (RES-REV-02)
        process_ram_mb = _get_process_memory_mb()
        mem_kb = float(process_ram_mb * 1024.0)

        health = self.health_monitor.get_status()
        health_str = health.name if hasattr(health, "name") else str(health)

        record = HourlyTelemetryRecord(
            hour_index=hour_index,
            start_timestamp=t_start,
            end_timestamp=t_end,
            ticks_processed=ticks_per_hour,
            orders_dispatched=orders_dispatched,
            orders_vetoed=orders_vetoed,
            p50_latency_ms=round(p50, 4),
            p95_latency_ms=round(p95, 4),
            max_latency_ms=round(max_lat, 4),
            health_status=health_str,
            circuit_breaker_trips=self._circuit_breaker_trips,
            peak_drawdown_observed=round(peak_dd, 4),
            estimated_memory_kb=round(mem_kb, 2),
        )

        # Compute tamper-evident checksum
        rec_dict = asdict(record)
        rec_dict.pop("checkpoint_hash", None)
        record.checkpoint_hash = compute_sha256(str(sorted(rec_dict.items())))

        self.hourly_records.append(record)
        return record

    def get_stability_summary(self) -> Dict[str, Any]:
        """Aggregates all hourly records into an overall stability report."""
        total_hours = len(self.hourly_records)
        total_ticks = sum(r.ticks_processed for r in self.hourly_records)
        total_dispatched = sum(r.orders_dispatched for r in self.hourly_records)
        total_vetoed = sum(r.orders_vetoed for r in self.hourly_records)
        max_p95 = max((r.p95_latency_ms for r in self.hourly_records), default=0.0)

        # Memory growth rate
        if total_hours > 1:
            initial_mem = self.hourly_records[0].estimated_memory_kb
            final_mem = self.hourly_records[-1].estimated_memory_kb
            mem_growth_rate_kb_per_hour = (final_mem - initial_mem) / (total_hours - 1)
        else:
            mem_growth_rate_kb_per_hour = 0.0

        is_stable = (
            total_hours > 0
            and max_p95 < 50.0  # sub-50ms p95 latency invariant
            and all(r.health_status != "CRITICAL" for r in self.hourly_records)
            and mem_growth_rate_kb_per_hour < 5000.0  # < 5MB/hour
        )

        return {
            "total_hours_evaluated": total_hours,
            "total_ticks_processed": total_ticks,
            "total_orders_dispatched": total_dispatched,
            "total_orders_vetoed": total_vetoed,
            "max_p95_latency_ms": round(max_p95, 4),
            "memory_growth_rate_kb_per_hour": round(mem_growth_rate_kb_per_hour, 2),
            "circuit_breaker_trips": self._circuit_breaker_trips,
            "stability_status": "STABLE" if is_stable else "UNSTABLE_OR_INSUFFICIENT",
            "hourly_records": [asdict(r) for r in self.hourly_records],
        }
