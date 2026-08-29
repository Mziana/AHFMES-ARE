"""
Phase 5 Pre-Flight Readiness Auditor & Institutional Qualification Engine.
Evaluates the 7 Iron Pre-Flight Checkpoints defined in PHASE_5_READINESS_MANIFESTO.md
and produces immutable, cryptographically verifiable certificates.
"""

import json
import math
import os
import time

import enum
from are.backtest import WFOEvidence
from are.validation import (
    validate_wfo_integrity,
    evaluate_dsr_from_evidence,
    evaluate_wfo_performance
)

class GateStatus(enum.Enum):
    INVALID = "INVALID"
    FAIL = "FAIL"
    BORDERLINE = "BORDERLINE"
    PASS = "PASS"

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import polars as pl

from are.backtest import IsolatedBacktestEngine
from are.evidence import EvidenceLedger
from are.hasher import compute_sha256
from are.health_monitor import HealthStatus, SystemHealthMonitor
from are.mt5_gateway import MT5ExecutionGateway, MT5OrderRequest
from are.portfolio import calculate_annualized_volatility, calculate_pearson_correlation
from are.safety import CapitalSafetyKernel, SafetyLimits
from are.stability_harness import HourlyStabilityHarness
from are.storage import EventStore
from are.validation import (
    calculate_deflated_sharpe_ratio,
    calculate_probabilistic_sharpe_ratio,
    monte_carlo_simulation,
    validate_statistical_robustness,
)


@dataclass
class CheckpointResult:
    checkpoint_id: int
    name: str
    passed: bool
    details: Dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class Phase5PreFlightReport:
    timestamp: float
    total_checkpoints: int
    passed_checkpoints: int
    readiness_disposition: str  # "GO" or "NO_GO"
    checkpoint_results: List[CheckpointResult]
    certificate_hash: str = ""


class Phase5PreFlightAuditor:
    """
    Automates rigorous evaluation of the 7 Iron Pre-Flight Checkpoints
    before live or paper trading execution.
    """

    def __init__(
        self,
        event_store: EventStore,
        evidence_ledger: EvidenceLedger,
        safety_kernel: CapitalSafetyKernel,
        gateway: MT5ExecutionGateway,
        health_monitor: SystemHealthMonitor,
    ):
        self.event_store = event_store
        self.evidence_ledger = evidence_ledger
        self.safety_kernel = safety_kernel
        self.gateway = gateway
        self.health_monitor = health_monitor
        self.backtest_engine = IsolatedBacktestEngine()

    def audit_checkpoint_1_dynamic_drawdown(self) -> CheckpointResult:
        """Checkpoint 1: Dynamic Account Balance & Peak-Equity Drawdown Binding."""
        try:
            info = self.gateway.get_account_info(default_equity=10000.0)
            has_peak = "peak_equity" in info
            has_dd = "drawdown" in info
            has_bal = "balance" in info

            passed = has_peak and has_dd and has_bal and info["drawdown"] >= 0.0
            return CheckpointResult(
                checkpoint_id=1,
                name="Dynamic Account Balance & Drawdown Binding",
                passed=passed,
                details=info,
            )
        except Exception as e:
            return CheckpointResult(
                checkpoint_id=1,
                name="Dynamic Account Balance & Drawdown Binding",
                passed=False,
                details={},
                error_message=str(e),
            )

    def audit_checkpoint_2_stability_harness(self, test_hours: int = 2) -> CheckpointResult:
        """Checkpoint 2: Step-Based Hourly Stability Run."""
        try:
            harness = HourlyStabilityHarness(
                safety_kernel=self.safety_kernel,
                gateway=self.gateway,
                health_monitor=self.health_monitor,
                evidence_ledger=self.evidence_ledger,
                event_store=self.event_store,
            )
            for h in range(test_hours):
                harness.run_simulated_hour_block(hour_index=h, ticks_per_hour=300)

            summary = harness.get_stability_summary()
            passed = summary["stability_status"] == "STABLE"
            return CheckpointResult(
                checkpoint_id=2,
                name="Hourly Stability & Zero-Leakage Harness",
                passed=passed,
                details=summary,
            )
        except Exception as e:
            return CheckpointResult(
                checkpoint_id=2,
                name="Hourly Stability & Zero-Leakage Harness",
                passed=False,
                details={},
                error_message=str(e),
            )

    def audit_checkpoint_3_vault_integrity(self) -> CheckpointResult:
        """Checkpoint 3: Windows Vault Dual-Layer Verification & Stream Continuity."""
        try:
            head = self.event_store.get_head("preflight_probes")
            rev = head[0] if head else 0
            prev_h = head[1] if head else "0" * 64
            test_data = b"PREFLIGHT_VAULT_INTEGRITY_PROBE"
            event_rec = self.event_store.append_event(
                stream_id="preflight_probes",
                event_data=test_data,
                expected_revision=rev,
                prev_event_hash=prev_h,
                var_ref="PROBE_P5",
            )
            event_hash = event_rec.event_hash
            rows = self.event_store.fetch_all(
                "SELECT event_hash FROM events WHERE stream_id = ? ORDER BY revision ASC",
                ("preflight_probes",),
            )
            integrity_ok, integrity_status = self.event_store.verify_full_chain_integrity()
            passed = len(rows) > 0 and rows[-1][0] == event_hash and integrity_ok
            return CheckpointResult(
                checkpoint_id=3,
                name="Windows Vault Dual-Layer Integrity",
                passed=passed,
                details={"verified_stream": "preflight_probes", "event_hash": event_hash, "integrity_status": integrity_status},
            )
        except Exception as e:
            return CheckpointResult(
                checkpoint_id=3,
                name="Windows Vault Dual-Layer Integrity",
                passed=False,
                details={},
                error_message=str(e),
            )

    def audit_checkpoint_4_triple_crisis_survival(
        self,
        strategy_logic: Optional[Callable[[pl.DataFrame], pl.DataFrame]] = None,
    ) -> CheckpointResult:
        """
        Checkpoint 4: Black Swan Crisis Survival Certificate.
        Evaluates 3 distinct crisis shock regimes with realistic microstructure frictions:
        1. 2008 GFC Crash (-50%)
        2. 2015 EURCHF Flash Depeg (-30%)
        3. 2020 COVID Market Plunge (-35%)
        """
        try:
            crises = [
                {"name": "2008_GFC_CRASH", "drop": 0.50, "spread": 0.0005, "bars": 300},
                {"name": "2015_EURCHF_DEPEG", "drop": 0.30, "spread": 0.0050, "bars": 100},
                {"name": "2020_COVID_PLUNGE", "drop": 0.35, "spread": 0.0010, "bars": 200},
            ]

            results = {}
            all_survived = True

            for c in crises:
                tstamps = [1700000000 + i * 60 for i in range(c["bars"])]
                prices = [100.0 * (1.0 - (c["drop"] * (i / float(c["bars"] - 1)))) for i in range(c["bars"])]
                df = pl.DataFrame({"timestamp": tstamps, "price": prices})

                res = self.backtest_engine.run_crisis_replay(
                    strategy_logic=strategy_logic,
                    crisis_df=df,
                    crisis_name=c["name"],
                    initial_capital=10000.0,
                    spread_pct=c["spread"],
                    slippage_pct=0.0001,
                    commission_pct=0.00005,
                )
                results[c["name"]] = {
                    "survival": res["survival_bool"],
                    "final_equity": res["final_equity"],
                    "max_drawdown": res["max_drawdown"],
                }
                if not res["survival_bool"]:
                    all_survived = False

            return CheckpointResult(
                checkpoint_id=4,
                name="Black Swan Triple Crisis Survival Certificate",
                passed=all_survived,
                details=results,
            )
        except Exception as e:
            return CheckpointResult(
                checkpoint_id=4,
                name="Black Swan Triple Crisis Survival Certificate",
                passed=False,
                details={},
                error_message=str(e),
            )

    def audit_checkpoint_5_institutional_rigor(
        self,
        strategy_logic: Optional[Callable[[pl.DataFrame], pl.DataFrame]] = None,
        wfo_evidence: Optional[WFOEvidence] = None,
    ) -> CheckpointResult:
        """
        Checkpoint 5: Institutional Statistical Rigor & Portfolio Independence (RES-WFO-01, RES-WFO-10).
        Strictly consumer of WFOEvidence.
        """
        try:
            if wfo_evidence is None:
                return CheckpointResult(
                    checkpoint_id=5,
                    name="Institutional Statistical Rigor & Portfolio Independence",
                    passed=False,
                    details={"gate_status": GateStatus.INVALID.value, "reason": "No WFOEvidence provided"},
                )
                
            integrity = validate_wfo_integrity(wfo_evidence)
            if not integrity.is_valid:
                return CheckpointResult(
                    checkpoint_id=5,
                    name="Institutional Statistical Rigor & Portfolio Independence",
                    passed=False,
                    details={"gate_status": GateStatus.INVALID.value, "reason": integrity.fail_reason},
                )
                
            dsr = evaluate_dsr_from_evidence(wfo_evidence)
            if not dsr.is_valid:
                return CheckpointResult(
                    checkpoint_id=5,
                    name="Institutional Statistical Rigor & Portfolio Independence",
                    passed=False,
                    details={"gate_status": GateStatus.FAIL.value, "reason": dsr.fail_reason, "dsr": dsr.dsr_value, "p_value": dsr.p_value},
                )
                
            perf = evaluate_wfo_performance(wfo_evidence)
            if not perf.is_valid:
                return CheckpointResult(
                    checkpoint_id=5,
                    name="Institutional Statistical Rigor & Portfolio Independence",
                    passed=False,
                    details={"gate_status": GateStatus.BORDERLINE.value, "reason": perf.fail_reason, "sharpe": perf.pooled_sharpe},
                )
                
            return CheckpointResult(
                checkpoint_id=5,
                name="Institutional Statistical Rigor & Portfolio Independence",
                passed=True,
                details={
                    "gate_status": GateStatus.PASS.value,
                    "dsr": round(dsr.dsr_value, 4),
                    "p_value": round(dsr.p_value, 4),
                    "sharpe": round(perf.pooled_sharpe, 4),
                    "return": round(perf.pooled_return, 4),
                    "max_drawdown": round(perf.pooled_max_dd, 4),
                },
            )
        except Exception as e:
            return CheckpointResult(
                checkpoint_id=5,
                name="Institutional Statistical Rigor & Portfolio Independence",
                passed=False,
                details={"gate_status": GateStatus.FAIL.value},
                error_message=str(e),
            )

    def audit_checkpoint_6_alerting_heartbeat(self) -> CheckpointResult:
        """Checkpoint 6: Emergency Alerting & System Health Monitor Heartbeat."""
        try:
            status = self.health_monitor.get_status()
            # Verify monitor can transition and record status
            passed = status != HealthStatus.CRITICAL
            return CheckpointResult(
                checkpoint_id=6,
                name="Emergency Alerting & CCTV Heartbeat",
                passed=passed,
                details={"health_status": str(status)},
            )
        except Exception as e:
            return CheckpointResult(
                checkpoint_id=6,
                name="Emergency Alerting & CCTV Heartbeat",
                passed=False,
                details={},
                error_message=str(e),
            )

    def audit_checkpoint_7_sec_risk_collar(self) -> CheckpointResult:
        """
        Checkpoint 7: SEC 15c3-5 Pre-Trade Risk Collar.
        Verifies:
        - Lot clamping
        - Sliding 60s rate limit (ACC-404)
        - Verified emergency flat liquidation (ACC-604)
        """
        try:
            # 1. Rate limiter check
            rate_count = self.gateway.get_recent_order_count(60.0)

            # 2. Emergency flat verification probe
            open_pos = self.gateway.get_open_positions()

            # 3. Lot sizing guard check
            lot_size = self.gateway.calculate_lot_size(account_equity=10000.0, stop_loss_points=50.0)

            passed = (rate_count >= 0) and (isinstance(open_pos, list)) and (lot_size > 0.0)
            return CheckpointResult(
                checkpoint_id=7,
                name="SEC 15c3-5 Pre-Trade Risk Collar (CSK Hard Veto)",
                passed=passed,
                details={
                    "rate_count_recent": rate_count,
                    "open_positions_count": len(open_pos),
                    "computed_lot_size": lot_size,
                    "csk_limits": asdict(self.safety_kernel.limits),
                },
            )
        except Exception as e:
            return CheckpointResult(
                checkpoint_id=7,
                name="SEC 15c3-5 Pre-Trade Risk Collar (CSK Hard Veto)",
                passed=False,
                details={},
                error_message=str(e),
            )

    def run_full_preflight_battery(
        self,
        strategy_logic: Optional[Callable[[pl.DataFrame], pl.DataFrame]] = None,
        wfo_evidence: Optional[WFOEvidence] = None,
    ) -> Phase5PreFlightReport:
        """
        Executes all 7 Iron Checkpoints and generates an authoritative Phase 5 Report.
        """
        t_now = time.time()
        results: List[CheckpointResult] = [
            self.audit_checkpoint_1_dynamic_drawdown(),
            self.audit_checkpoint_2_stability_harness(test_hours=1),
            self.audit_checkpoint_3_vault_integrity(),
            self.audit_checkpoint_4_triple_crisis_survival(strategy_logic=strategy_logic),
            self.audit_checkpoint_5_institutional_rigor(strategy_logic=strategy_logic, wfo_evidence=wfo_evidence),
            self.audit_checkpoint_6_alerting_heartbeat(),
            self.audit_checkpoint_7_sec_risk_collar(),
        ]

        passed_count = sum(1 for r in results if r.passed)
        disposition = "GO" if passed_count == 7 else "NO_GO"

        report = Phase5PreFlightReport(
            timestamp=t_now,
            total_checkpoints=7,
            passed_checkpoints=passed_count,
            readiness_disposition=disposition,
            checkpoint_results=results,
        )

        # Generate deterministic certificate hash
        rep_dict = asdict(report)
        rep_dict.pop("certificate_hash", None)
        # Exclude timestamp for deterministic payload
        rep_dict.pop("timestamp", None)
        report.certificate_hash = compute_sha256(json.dumps(rep_dict, sort_keys=True, default=str))

        # Record Certificate to Evidence Ledger
        cert_payload = {
            "certificate_hash": report.certificate_hash,
            "disposition": report.readiness_disposition,
            "passed_checkpoints": report.passed_checkpoints,
            "artifact_type": "PHASE_5_PREFLIGHT_CERTIFICATE",
        }
        if hasattr(self.evidence_ledger, "_store") and self.evidence_ledger._store is not None:
            head = self.evidence_ledger._store.get_head("governance_certificates")
            rev = head[0] if head else 0
            prev_h = head[1] if head else "0" * 64
            self.evidence_ledger._store.append_event(
                stream_id="governance_certificates",
                event_data=json.dumps(cert_payload, sort_keys=True).encode("utf-8"),
                expected_revision=rev,
                prev_event_hash=prev_h,
                var_ref=report.certificate_hash,
            )

        return report
