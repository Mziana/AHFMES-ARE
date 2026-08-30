"""
Explainable AI (XAI) & Post-Trade Shadow Diagnostics Invariant Tests (DELEGASI_030)
"""

import os
import tempfile
import unittest

from are.copilot import ConversationalCopilot, STATIC_SYSTEM_PREFIX
from are.diagnostics import PostTradeDiagnostics, SlippageReport
from are.storage import EventStore


class TestXAIDiagnosticsInvariants(unittest.TestCase):
    def setUp(self):
        self.diagnostics = PostTradeDiagnostics()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "xai_test.db")
        self.store = EventStore(self.db_path)
        # Hermetic (DELEGASI_051 P0-2): point Ollama at a dead port so the
        # deterministic builtin fallback engine is always exercised.
        # Otherwise a live Ollama daemon on the host hijacks the response
        # and the deterministic assertions below become flaky.
        self.copilot = ConversationalCopilot(
            event_store=self.store,
            ollama_url="http://127.0.0.1:1/api/generate",
        )

    def tearDown(self):
        try:
            self.store.close()
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def test_slippage_drift_anomaly_detection(self):
        """
        Invariant 1: PostTradeDiagnostics accurately measures drift and flags anomalies > 3.0 pips.
        """
        expected = {
            "strategy_id": "P001_ALPHA_V1",
            "symbol": "EURUSD",
            "price": 1.1000,
        }
        actual_anomaly = {
            "strategy_id": "P001_ALPHA_V1",
            "symbol": "EURUSD",
            "price": 1.1005,  # 5.0 pips slippage (0.0005 / 0.0001)
            "latency_ms": 120.0,
        }

        report = self.diagnostics.analyze_execution_drift(
            expected_order=expected,
            actual_fill=actual_anomaly,
            pip_size=0.0001,
            slippage_threshold_pips=3.0,
        )

        self.assertTrue(report.is_anomaly)
        self.assertEqual(report.slippage_pips, 5.0)
        self.assertEqual(report.expected_price, 1.1000)
        self.assertEqual(report.actual_price, 1.1005)
        self.assertIn("Excessive slippage", report.anomaly_reason)

        # Test nominal execution (< 3.0 pips)
        actual_nominal = {
            "strategy_id": "P001_ALPHA_V1",
            "symbol": "EURUSD",
            "price": 1.1001,  # 1.0 pip slippage
            "latency_ms": 50.0,
        }
        report_nominal = self.diagnostics.analyze_execution_drift(
            expected_order=expected,
            actual_fill=actual_nominal,
            pip_size=0.0001,
            slippage_threshold_pips=3.0,
        )
        self.assertFalse(report_nominal.is_anomaly)
        self.assertEqual(report_nominal.slippage_pips, 1.0)
        self.assertEqual(report_nominal.anomaly_reason, "NOMINAL_EXECUTION")

    def test_copilot_text_to_query_diagnostics_response(self):
        """
        Invariant 2: Copilot text-to-query queries EvidenceLedger and returns factual slippage data.
        """
        # 1. Record an execution anomaly to the EventStore
        report = SlippageReport(
            strategy_id="STRAT_VOL_SPIKE",
            symbol="EURUSD",
            expected_price=1.0850,
            actual_price=1.08542,
            slippage_pips=4.2,
            execution_latency_ms=1650.0,
            is_anomaly=True,
            anomaly_reason="Excessive slippage (4.2 pips > 3.0 pips); Execution latency spike (1650.0ms > 1500.0ms)",
        )
        self.diagnostics.record_diagnostic_event(report, self.store)

        # 2. Query Copilot
        response = self.copilot.generate_response("Mengapa order terakhir mengalami slippage broker?")

        # 3. Assert factual, non-hallucinated response
        self.assertIn("Laporan Shadow Diagnostics", response)
        self.assertIn("EURUSD", response)
        self.assertIn("4.2 pips", response)
        self.assertIn("1.08500", response)
        self.assertIn("1.08542", response)
        self.assertIn("1650.0ms", response)

    def test_prompt_cache_prefix_integrity(self):
        """
        Invariant 3: STATIC_SYSTEM_PREFIX and build_prompt deterministically isolate static vs dynamic state.
        """
        self.assertIsInstance(STATIC_SYSTEM_PREFIX, str)
        self.assertIn("Autonomous Research Engine", STATIC_SYSTEM_PREFIX)
        self.assertIn("Capital Safety Kernel", STATIC_SYSTEM_PREFIX)
        self.assertIn("Windows Vault Protocol", STATIC_SYSTEM_PREFIX)

        dynamic_ctx = {
            "champion": {"champion_id": "CHAMPION_TEST_XYZ", "candidate_id": "CAND_99", "status": "ACTIVE"},
            "safety": {"kill_switch_active": False, "max_drawdown_pct": 0.12, "volatility_cutoff": 2.2},
            "stream_stats": {"total_ticks": 500, "veto_count": 2, "chain_health": "VERIFIED_OK"},
        }

        prompt = self.copilot.build_prompt("Halo Copilot", dynamic_ctx)
        self.assertTrue(prompt.startswith(STATIC_SYSTEM_PREFIX))
        self.assertIn("CHAMPION_TEST_XYZ", prompt)
        self.assertIn("User: Halo Copilot", prompt)
        self.assertIn("AI Copilot:", prompt)


if __name__ == "__main__":
    unittest.main()