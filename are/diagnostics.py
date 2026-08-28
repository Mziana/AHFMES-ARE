"""
AHFMES ARE — Post-Trade Shadow Diagnostics & Slippage Drift Engine (DELEGASI_030, XAI)

Compares intended execution parameters (Expected Slippage / Price) against actual broker fills.
Records factual execution evidence to EvidenceLedger / EventStore.
100% Python Standard Library.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from are.hasher import compute_sha256
from are.storage import EventStore


@dataclass(frozen=True)
class SlippageReport:
    strategy_id: str
    symbol: str
    expected_price: float
    actual_price: float
    slippage_pips: float
    execution_latency_ms: float
    is_anomaly: bool
    anomaly_reason: str


class PostTradeDiagnostics:
    """
    Shadow Diagnostics Engine evaluating order execution fidelity and broker drift.
    """

    def analyze_execution_drift(
        self,
        expected_order: Dict[str, Any],
        actual_fill: Dict[str, Any],
        pip_size: Optional[float] = None,
        slippage_threshold_pips: float = 3.0,
        latency_threshold_ms: float = 1500.0,
    ) -> SlippageReport:
        """
        Compares expected order intent with actual fill reality to detect execution anomalies.
        """
        strategy_id = str(expected_order.get("strategy_id", actual_fill.get("strategy_id", "P001_STRATEGY")))
        symbol = str(expected_order.get("symbol", actual_fill.get("symbol", "UNKNOWN"))).upper()

        expected_price = float(expected_order.get("price", expected_order.get("expected_price", 0.0)))
        actual_price = float(actual_fill.get("price", actual_fill.get("actual_price", 0.0)))
        latency_ms = float(actual_fill.get("latency_ms", actual_fill.get("execution_latency_ms", 0.0)))

        # Determine pip size (0.01 for JPY pairs / commodities or 0.0001 standard forex)
        if pip_size is not None:
            pip_sz = float(pip_size)
        elif "JPY" in symbol or "XAU" in symbol or "BTC" in symbol:
            pip_sz = 0.01
        else:
            pip_sz = 0.0001

        price_diff = abs(actual_price - expected_price)
        slippage_pips = round(price_diff / pip_sz, 2) if pip_sz > 0 else 0.0

        # Anomaly evaluation
        reasons: List[str] = []
        if slippage_pips > slippage_threshold_pips:
            reasons.append(f"Excessive slippage ({slippage_pips:.1f} pips > {slippage_threshold_pips:.1f} pips)")
        if latency_ms > latency_threshold_ms:
            reasons.append(f"Execution latency spike ({latency_ms:.1f}ms > {latency_threshold_ms:.1f}ms)")

        is_anomaly = len(reasons) > 0
        anomaly_reason = "; ".join(reasons) if reasons else "NOMINAL_EXECUTION"

        return SlippageReport(
            strategy_id=strategy_id,
            symbol=symbol,
            expected_price=round(expected_price, 5),
            actual_price=round(actual_price, 5),
            slippage_pips=slippage_pips,
            execution_latency_ms=round(latency_ms, 2),
            is_anomaly=is_anomaly,
            anomaly_reason=anomaly_reason,
        )

    def record_diagnostic_event(self, report: SlippageReport, event_store: EventStore) -> str:
        """
        Persists a diagnostic report into the EventStore stream as immutable factual evidence.
        """
        payload = asdict(report)
        payload["timestamp"] = time.time()
        payload_json = json.dumps(payload, sort_keys=True)
        proof_hash = compute_sha256(payload_json)

        head = event_store.get_head("trade_diagnostics")
        rev = head[0] if head else 0
        prev_h = head[1] if head else "0" * 64

        rec = event_store.append_event(
            stream_id="trade_diagnostics",
            event_data=payload_json.encode("utf-8"),
            expected_revision=rev,
            prev_event_hash=prev_h,
            var_ref=proof_hash,
        )
        return rec.event_hash

    def query_recent_anomalies(self, event_store: Optional[Any] = None, limit: int = 10) -> List[SlippageReport]:
        """
        Queries recent verified execution anomalies from the Evidence Ledger / EventStore.
        Utilizes encapsulated EventStore API (fetch_all) per ACC-317.
        """
        if event_store is None:
            return []

        try:
            rows = event_store.fetch_all(
                "SELECT event_data FROM events WHERE stream_id = ? ORDER BY revision DESC LIMIT ?",
                ("trade_diagnostics", limit * 3),
            )
            anomalies: List[SlippageReport] = []
            for (data_blob,) in rows:
                try:
                    if isinstance(data_blob, str):
                        data = json.loads(data_blob)
                    else:
                        data = json.loads(data_blob.decode("utf-8"))

                    if data.get("is_anomaly", False):
                        anomalies.append(
                            SlippageReport(
                                strategy_id=data.get("strategy_id", "N/A"),
                                symbol=data.get("symbol", "UNKNOWN"),
                                expected_price=float(data.get("expected_price", 0.0)),
                                actual_price=float(data.get("actual_price", 0.0)),
                                slippage_pips=float(data.get("slippage_pips", 0.0)),
                                execution_latency_ms=float(data.get("execution_latency_ms", 0.0)),
                                is_anomaly=True,
                                anomaly_reason=data.get("anomaly_reason", "ANOMALY_DETECTED"),
                            )
                        )
                        if len(anomalies) >= limit:
                            break
                except Exception:
                    continue
            return anomalies
        except Exception:
            return []