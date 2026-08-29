"""
Phase 5 Pre-Flight Readiness & Hourly Stability Invariant Tests.
Verifies all 7 Iron Pre-Flight Checkpoints, Black Swan Crisis Survival,
Hourly Stability Harness, and DSR Multiple-Testing Interlock.
"""

import os
import tempfile
import time
import unittest
from unittest.mock import MagicMock

import polars as pl

from are.evidence import EvidenceLedger
from are.health_monitor import HealthStatus, SystemHealthMonitor
from are.mt5_gateway import MT5ExecutionGateway, MT5OrderRequest
from are.preflight import Phase5PreFlightAuditor, Phase5PreFlightReport
from are.safety import CapitalSafetyKernel, SafetyLimits
from are.stability_harness import HourlyStabilityHarness
from are.storage import EventStore


class TestPhase5PreFlightInvariants(unittest.TestCase):
    def setUp(self):
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

        # Run 2 simulated hour blocks
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
        # Trend strategy with tight stop logic
        def trend_strategy(df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns([
                pl.col("price").rolling_mean(window_size=10).alias("ma"),
            ]).with_columns(
                pl.when(pl.col("price") > pl.col("ma"))
                .then(pl.lit(1.0))
                .otherwise(pl.lit(0.0))  # Flat during crashes
                .alias("signal")
            )

        res = self.auditor.audit_checkpoint_4_triple_crisis_survival(strategy_logic=trend_strategy)
        self.assertTrue(res.passed)
        self.assertEqual(res.checkpoint_id, 4)
        self.assertIn("2008_GFC_CRASH", res.details)
        self.assertIn("2015_EURCHF_DEPEG", res.details)
        self.assertIn("2020_COVID_PLUNGE", res.details)

    # =========================================================================
    # CHECKPOINT 5: Institutional Statistical Rigor
    # =========================================================================
    def test_checkpoint_5_institutional_rigor_verification(self):
        """Checkpoint 5: PSR, DSR, and Monte Carlo Wilson CI verification."""
        res = self.auditor.audit_checkpoint_5_institutional_rigor()
        self.assertTrue(res.passed)
        self.assertEqual(res.checkpoint_id, 5)
        self.assertIn("psr", res.details)
        self.assertIn("mc_ruin_ci_95", res.details)

    # =========================================================================
    # CHECKPOINT 6: Emergency Alerting CCTV Heartbeat
    # =========================================================================
    def test_checkpoint_6_alerting_heartbeat(self):
        """Checkpoint 6: Health monitor status active and healthy."""
        res = self.auditor.audit_checkpoint_6_alerting_heartbeat()
        self.assertTrue(res.passed)
        self.assertEqual(res.checkpoint_id, 6)

    # =========================================================================
    # CHECKPOINT 7: SEC 15c3-5 Pre-Trade Risk Collar
    # =========================================================================
    def test_checkpoint_7_sec_risk_collar(self):
        """Checkpoint 7: CSK limits, rate counting, and position tracking active."""
        res = self.auditor.audit_checkpoint_7_sec_risk_collar()
        self.assertTrue(res.passed)
        self.assertEqual(res.checkpoint_id, 7)

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

        report = self.auditor.run_full_preflight_battery(strategy_logic=safe_strategy)
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
            return df.with_columns(pl.lit(1.0).alias("signal"))  # Always long into crash

        report = self.auditor.run_full_preflight_battery(strategy_logic=crash_loser_strategy)
        self.assertNotEqual(report.passed_checkpoints, 7)
        self.assertEqual(report.readiness_disposition, "NO_GO")

    def test_checkpoint_5_fails_closed_on_negative_sharpe_strategy(self):
        """
        REV-01: Checkpoint 5 WAJIB menolak strategi dengan Sharpe buruk/negatif.
        Dilarang menggunakan artificial floor max(1.5, sr).
        """
        # Strategi rugi konstan (selalu posisi salah)
        def loser_strategy(df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns(pl.lit(-1.0).alias("signal"))

        res = self.auditor.audit_checkpoint_5_institutional_rigor(strategy_logic=loser_strategy)
        self.assertFalse(res.passed, "Strategi Sharpe negatif WAJIB gagal di Checkpoint 5")
        self.assertLess(res.details["psr"], 0.50, "PSR untuk Sharpe negatif harus < 0.50")

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
        # Process memory Python di Windows biasanya >= 10 MB (10,240 KB)
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
