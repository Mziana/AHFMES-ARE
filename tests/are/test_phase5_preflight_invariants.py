"""
Phase 5 Pre-Flight Readiness & Hourly Stability Invariant Tests.
Verifies all 7 Iron Pre-Flight Checkpoints, Black Swan Crisis Survival,
Hourly Stability Harness, and DSR Multiple-Testing Interlock.
"""

import dataclasses
import hashlib
import json
import os
import tempfile
import time
import unittest
from unittest.mock import MagicMock

import polars as pl

from are.backtest import (
    WFOEvidence,
    WFOFoldEvidence,
    build_wfo_provenance_payload,
)
from are.evidence import EvidenceLedger
from are.health_monitor import HealthStatus, SystemHealthMonitor
from are.mt5_gateway import MT5ExecutionGateway, MT5OrderRequest
from are.preflight import Phase5PreFlightAuditor, Phase5PreFlightReport
from are.safety import CapitalSafetyKernel, SafetyLimits
from are.stability_harness import HourlyStabilityHarness
from are.storage import EventStore


def _compute_wfo_hash(ev: WFOEvidence) -> str:
    import dataclasses
    from are.backtest import calculate_sharpe_ratio, build_wfo_provenance_payload
    
    cum_eq = 1.0
    peak = 1.0
    calc_max_dd = 0.0
    for r in ev.pooled_oos_returns:
        cum_eq *= (1.0 + r)
        if cum_eq > peak:
            peak = cum_eq
        dd = (peak - cum_eq) / peak if peak > 0.0 else 0.0
        if dd > calc_max_dd:
            calc_max_dd = dd
    calc_return = cum_eq - 1.0
    calc_sharpe = calculate_sharpe_ratio(list(ev.pooled_oos_returns), timeframe_seconds=60.0)
    
    recomputed_ev = dataclasses.replace(
        ev,
        pooled_oos_return=calc_return,
        pooled_oos_max_drawdown=calc_max_dd,
        pooled_oos_sharpe=calc_sharpe
    )
    payload = build_wfo_provenance_payload(recomputed_ev)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()


class TestPhase5PreFlightInvariants(unittest.TestCase):
    def setUp(self):
        from unittest.mock import patch
        from are.validation import WFOIntegrityResult
        
        self.patcher = patch("are.preflight.validate_wfo_integrity")
        self.mock_validate = self.patcher.start()
        self.mock_validate.return_value = WFOIntegrityResult(is_valid=True, fail_reason=None, overlap_count=0)
        
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "phase5_test.db")
        self.event_store = EventStore(self.db_path)
        self.evidence_ledger = EvidenceLedger(self.db_path)
        self.limits = SafetyLimits(
            max_position_size=1.0,
            max_drawdown_pct=0.15,
            volatility_cutoff=2.5,
            max_order_rate_per_min=10,
            kill_switch_active=False,
        )
        self.safety_kernel = CapitalSafetyKernel(self.limits)
        self.gateway = MT5ExecutionGateway(safety_kernel=self.safety_kernel, use_mock=True)
        self.health_monitor = SystemHealthMonitor()
        self.auditor = Phase5PreFlightAuditor(
            event_store=self.event_store,
            evidence_ledger=self.evidence_ledger,
            safety_kernel=self.safety_kernel,
            gateway=self.gateway,
            health_monitor=self.health_monitor,
        )

    def tearDown(self):
        self.patcher.stop()
        self.gateway.close()
        self.event_store.close()
        if hasattr(self.evidence_ledger, "_store") and self.evidence_ledger._store:
            self.evidence_ledger._store.close()
        if hasattr(self.evidence_ledger, "close"):
            self.evidence_ledger.close()
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    # =========================================================================
    # CHECKPOINT 1: Dynamic Account Balance & Peak-Equity Drawdown
    # =========================================================================
    def test_checkpoint_1_dynamic_drawdown_binding_passes(self):
        """Checkpoint 1: Account info includes peak_equity and drawdown."""
        res = self.auditor.audit_checkpoint_1_dynamic_drawdown()
        self.assertTrue(res.passed)
        self.assertEqual(res.checkpoint_id, 1)
        self.assertIn("peak_equity", res.details)
        self.assertIn("drawdown", res.details)

    # =========================================================================
    # CHECKPOINT 2: Hourly Stability & Zero-Leakage Harness
    # =========================================================================
    def test_checkpoint_2_hourly_stability_harness_execution(self):
        """Checkpoint 2: Hourly stability harness tracks telemetry per hour block."""
        harness = HourlyStabilityHarness(
            safety_kernel=self.safety_kernel,
            gateway=self.gateway,
            health_monitor=self.health_monitor,
            evidence_ledger=self.evidence_ledger,
            event_store=self.event_store,
        )

        rec0 = harness.run_simulated_hour_block(hour_index=0, ticks_per_hour=100)
        rec1 = harness.run_simulated_hour_block(hour_index=1, ticks_per_hour=100)

        self.assertEqual(rec0.hour_index, 0)
        self.assertEqual(rec1.hour_index, 1)
        self.assertEqual(rec0.ticks_processed, 100)
        self.assertGreaterEqual(len(rec0.checkpoint_hash), 64)

        summary = harness.get_stability_summary()
        self.assertEqual(summary["total_hours_evaluated"], 2)
        self.assertEqual(summary["total_ticks_processed"], 200)
        self.assertEqual(summary["stability_status"], "STABLE")

    # =========================================================================
    # CHECKPOINT 3: Windows Vault Dual-Layer Verification
    # =========================================================================
    def test_checkpoint_3_vault_integrity_probe(self):
        """Checkpoint 3: EventStore streams write and verify event continuity."""
        res = self.auditor.audit_checkpoint_3_vault_integrity()
        self.assertTrue(res.passed)
        self.assertEqual(res.checkpoint_id, 3)

    # =========================================================================
    # CHECKPOINT 4: Black Swan Triple Crisis Survival Certificate
    # =========================================================================
    def test_checkpoint_4_triple_crisis_survival_certificate(self):
        """Checkpoint 4: Strategy evaluated across 2008 GFC, 2015 EURCHF, 2020 COVID."""
        def trend_strategy(df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns([
                pl.col("price").rolling_mean(window_size=10).alias("ma"),
            ]).with_columns(
                pl.when(pl.col("price") > pl.col("ma"))
                .then(pl.lit(1.0))
                .otherwise(pl.lit(0.0))
                .alias("signal")
            )

        res = self.auditor.audit_checkpoint_4_triple_crisis_survival(strategy_logic=trend_strategy)
        self.assertTrue(res.passed)
        self.assertEqual(res.checkpoint_id, 4)
        self.assertIn("2008_GFC_CRASH", res.details)
        self.assertIn("2015_EURCHF_DEPEG", res.details)
        self.assertIn("2020_COVID_PLUNGE", res.details)

    def test_cp4_none_strategy_fails(self):
        """CP4: None strategy must fail-closed with STRATEGY_REQUIRED_NO_DEFAULT."""
        res = self.auditor.audit_checkpoint_4_triple_crisis_survival(strategy_logic=None)
        self.assertFalse(res.passed)
        self.assertEqual(res.details.get("reason"), "STRATEGY_REQUIRED_NO_DEFAULT")

    # =========================================================================
    # CHECKPOINT 5: Institutional Statistical Rigor
    # =========================================================================
    def test_checkpoint_5_institutional_rigor_verification(self):
        """Checkpoint 5: Strict WFOEvidence consumer."""
        f1 = WFOFoldEvidence(1, 0, 100, 101, 105, 106, 200, 2, "sr", {"a":1}, 1.0, None, None, 0, "", {}, {"sharpe_ratio": 2.5}, (0.01,), 1.0)
        valid_ev_proto = WFOEvidence(
            run_id="test",
            dataset_hash="hash",
            timeframe_seconds=60.0,
            data_start_ts=0,
            data_end_ts=250,
            folds=(f1,),
            fold_count=1,
            parameter_family_size=1,
            evaluation_count=1,
            effective_trial_count=1,
            effective_trial_method="M",
            effective_trial_assumption="A",
            training_overlap_ratio=0.0,
            oos_overlap_ratio=0.0,
            purge_bars=0,
            label_horizon_bars=0,
            label_horizon_unit="BARS",
            warmup_bars=0,
            pooled_oos_returns=tuple([0.01]*1000), 
            pooled_oos_equity=tuple([1.0]*1000),
            pooled_oos_sharpe=2.5,
            pooled_oos_return=0.1,
            pooled_oos_max_drawdown=0.05,
            mean_fold_oos_sharpe=1.0,
            median_fold_oos_sharpe=1.0,
            worst_fold_oos_sharpe=1.0,
            std_fold_oos_sharpe=0.0,
            mean_wfe=1.0,
            median_wfe=1.0,
            worst_wfe=1.0,
            provenance_hash=""
        )
        valid_ev = dataclasses.replace(valid_ev_proto, provenance_hash=_compute_wfo_hash(valid_ev_proto))

        res = self.auditor.audit_checkpoint_5_institutional_rigor(wfo_evidence=valid_ev)
        self.assertTrue(res.passed)
        self.assertEqual(res.checkpoint_id, 5)
        self.assertEqual(res.details["gate_status"], "PASS")

    # =========================================================================
    # CHECKPOINT 6: Emergency Alerting & System Health Monitor Heartbeat
    # =========================================================================
    def test_checkpoint_6_alerting_heartbeat(self):
        """Checkpoint 6: Health monitor status active and healthy."""
        res = self.auditor.audit_checkpoint_6_alerting_heartbeat()
        self.assertTrue(res.passed)
        self.assertEqual(res.checkpoint_id, 6)

    def test_cp6_injects_critical_and_recovers(self):
        """CP6: Two-phase probe injects CRITICAL and recovers to HEALTHY."""
        res = self.auditor.audit_checkpoint_6_alerting_heartbeat()
        self.assertTrue(res.passed)
        self.assertTrue(res.details.get("phase1_inject_critical_ok"))
        self.assertTrue(res.details.get("phase2_recover_healthy_ok"))

    # =========================================================================
    # CHECKPOINT 7: SEC 15c3-5 Pre-Trade Risk Collar
    # =========================================================================
    def test_checkpoint_7_sec_risk_collar(self):
        """Checkpoint 7: CSK limits, rate counting, and position tracking active."""
        res = self.auditor.audit_checkpoint_7_sec_risk_collar()
        self.assertTrue(res.passed)
        self.assertEqual(res.checkpoint_id, 7)

    def test_cp7_rate_limit_vetoes(self):
        """CP7: Exceeding max_order_rate_per_min triggers CSK veto."""
        res = self.auditor.audit_checkpoint_7_sec_risk_collar()
        self.assertTrue(res.passed)
        self.assertTrue(res.details.get("rate_veto_passed"))

    def test_cp7_lot_clamping_enforced(self):
        """CP7: Excessive lot size request is clamped to max_position_size."""
        res = self.auditor.audit_checkpoint_7_sec_risk_collar()
        self.assertTrue(res.passed)
        self.assertTrue(res.details.get("lot_clamp_passed"))
        self.assertEqual(res.details.get("computed_lot_size"), self.limits.max_position_size)

    # =========================================================================
    # FULL BATTERY & IMMUTABLE CERTIFICATE
    # =========================================================================
    def test_full_preflight_battery_generates_go_certificate(self):
        """Full Battery: 7/7 Checkpoints Passed produces GO disposition with certificate."""
        def safe_strategy(df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns([
                pl.col("price").rolling_mean(window_size=5).alias("ma"),
            ]).with_columns(
                pl.when(pl.col("price") > pl.col("ma"))
                .then(pl.lit(1.0))
                .otherwise(pl.lit(0.0))
                .alias("signal")
            )

        f1 = WFOFoldEvidence(1, 0, 100, 101, 105, 106, 200, 2, "sr", {"a":1}, 1.0, None, None, 0, "", {}, {"sharpe_ratio": 2.5}, (0.01,), 1.0)
        valid_ev_proto = WFOEvidence(
            run_id="test",
            dataset_hash="hash",
            timeframe_seconds=60.0,
            data_start_ts=0,
            data_end_ts=250,
            folds=(f1,),
            fold_count=1,
            parameter_family_size=1,
            evaluation_count=1,
            effective_trial_count=1,
            effective_trial_method="M",
            effective_trial_assumption="A",
            training_overlap_ratio=0.0,
            oos_overlap_ratio=0.0,
            purge_bars=0,
            label_horizon_bars=0,
            label_horizon_unit="BARS",
            warmup_bars=0,
            pooled_oos_returns=tuple([0.01]*1000), 
            pooled_oos_equity=tuple([1.0]*1000),
            pooled_oos_sharpe=2.5,
            pooled_oos_return=0.1,
            pooled_oos_max_drawdown=0.05,
            mean_fold_oos_sharpe=1.0,
            median_fold_oos_sharpe=1.0,
            worst_fold_oos_sharpe=1.0,
            std_fold_oos_sharpe=0.0,
            mean_wfe=1.0,
            median_wfe=1.0,
            worst_wfe=1.0,
            provenance_hash=""
        )
        valid_ev = dataclasses.replace(valid_ev_proto, provenance_hash=_compute_wfo_hash(valid_ev_proto))

        report = self.auditor.run_full_preflight_battery(strategy_logic=safe_strategy, wfo_evidence=valid_ev)
        self.assertEqual(report.total_checkpoints, 7)
        self.assertEqual(report.passed_checkpoints, 7)
        self.assertEqual(report.readiness_disposition, "GO")
        self.assertEqual(len(report.certificate_hash), 64)

        # Verify certificate stream was recorded in event store
        rows = self.event_store.fetch_all(
            "SELECT var_ref FROM events WHERE stream_id = ? ORDER BY revision ASC",
            ("governance_certificates",),
        )
        self.assertGreaterEqual(len(rows), 1)
        self.assertEqual(rows[-1][0], report.certificate_hash)

    def test_full_preflight_battery_fails_closed_on_catastrophic_strategy(self):
        """Fail-Closed: Strategy that goes 100% long on -60% crash fails Checkpoint 4."""
        def crash_loser_strategy(df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns(pl.lit(1.0).alias("signal"))

        report = self.auditor.run_full_preflight_battery(strategy_logic=crash_loser_strategy)
        self.assertNotEqual(report.passed_checkpoints, 7)
        self.assertEqual(report.readiness_disposition, "NO_GO")

    def test_checkpoint_5_fails_closed_on_negative_sharpe_strategy(self):
        """
        REV-01 / WFO-01: Checkpoint 5 WAJIB menolak strategi dengan Sharpe buruk/negatif via WFOEvidence.
        Dilarang menggunakan artificial floor max(1.5, sr).
        """
        f1 = WFOFoldEvidence(1, 0, 100, 101, 105, 106, 200, 2, "sr", {"a":1}, 1.0, None, None, 0, "", {}, {"sharpe_ratio": -1.0}, (0.01,), 1.0)
        bad_ev_proto = WFOEvidence(
            run_id="test",
            dataset_hash="hash",
            timeframe_seconds=60.0,
            data_start_ts=0,
            data_end_ts=250,
            folds=(f1,),
            fold_count=1,
            parameter_family_size=1,
            evaluation_count=1,
            effective_trial_count=1,
            effective_trial_method="M",
            effective_trial_assumption="A",
            training_overlap_ratio=0.0,
            oos_overlap_ratio=0.0,
            purge_bars=0,
            label_horizon_bars=0,
            label_horizon_unit="BARS",
            warmup_bars=0,
            pooled_oos_returns=tuple([0.01]*1000), 
            pooled_oos_equity=tuple([1.0]*1000),
            pooled_oos_sharpe=-1.0,
            pooled_oos_return=-0.1,
            pooled_oos_max_drawdown=0.50,
            mean_fold_oos_sharpe=1.0,
            median_fold_oos_sharpe=1.0,
            worst_fold_oos_sharpe=1.0,
            std_fold_oos_sharpe=0.0,
            mean_wfe=1.0,
            median_wfe=1.0,
            worst_wfe=1.0,
            provenance_hash=""
        )
        bad_ev = dataclasses.replace(bad_ev_proto, provenance_hash=_compute_wfo_hash(bad_ev_proto))

        res = self.auditor.audit_checkpoint_5_institutional_rigor(wfo_evidence=bad_ev)
        self.assertFalse(res.passed, "Strategi Sharpe negatif WAJIB gagal di Checkpoint 5")
        self.assertIn(res.details["gate_status"], ["FAIL", "BORDERLINE"])

    def test_hourly_stability_harness_uses_real_process_memory(self):
        """
        REV-02: HourlyStabilityHarness WAJIB mencatat memori proses nyata (> 1 MB),
        bukan sekadar shallow pointer size sys.getsizeof (< 10 KB).
        """
        harness = HourlyStabilityHarness(
            safety_kernel=self.safety_kernel,
            gateway=self.gateway,
            health_monitor=self.health_monitor,
            evidence_ledger=self.evidence_ledger,
            event_store=self.event_store,
        )
        rec = harness.run_simulated_hour_block(hour_index=0, ticks_per_hour=50)
        self.assertGreater(rec.estimated_memory_kb, 1024.0, "Memori harus mencerminkan Process RAM nyata (> 1MB)")

    def test_three_hour_continuous_stability_battery(self):
        """
        Bagian 2: 3-Jam Simulative Hourly Stability Battery.
        Verifies 3 sequential hour blocks maintain STABLE status,
        sub-50ms P95 latency, and memory growth < 5MB/hr.
        """
        harness = HourlyStabilityHarness(
            safety_kernel=self.safety_kernel,
            gateway=self.gateway,
            health_monitor=self.health_monitor,
            evidence_ledger=self.evidence_ledger,
            event_store=self.event_store,
        )
        for h in range(3):
            rec = harness.run_simulated_hour_block(hour_index=h, ticks_per_hour=1000)
            self.assertIsNotNone(rec.checkpoint_hash)
            self.assertEqual(len(rec.checkpoint_hash), 64)
            self.assertLess(rec.p95_latency_ms, 50.0)

        summary = harness.get_stability_summary()
        self.assertEqual(summary["total_hours_evaluated"], 3)
        self.assertEqual(summary["total_ticks_processed"], 3000)
        self.assertEqual(summary["stability_status"], "STABLE")
        self.assertLess(summary["max_p95_latency_ms"], 50.0)
        self.assertLess(summary["memory_growth_rate_kb_per_hour"], 5000.0)


if __name__ == "__main__":
    unittest.main()