"""
Unit Tests for AHFMES ARE-3 Telemetry Aggregator (ACC-313, ACC-314)
"""

import os
import tempfile
import unittest

from are.storage import EventStore
from are.telemetry import ExperimentTrace, TelemetryAggregator


class TestTelemetryAggregator(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "telemetry_test.db")
        self.store = EventStore(self.db_path)
        self.aggregator = TelemetryAggregator(self.store)

    def tearDown(self):
        self.store.close()
        self.tmp_dir.cleanup()

    def test_record_trace_and_retrieve_history(self):
        t1 = ExperimentTrace(
            experiment_id="EXP_001",
            candidate_id="CAND_ALPHA",
            timestamp=1000.0,
            metrics={"sharpe": 1.5, "latency_ms": 12.0},
            tags=["volatility", "mean_reversion"],
        )
        t2 = ExperimentTrace(
            experiment_id="EXP_002",
            candidate_id="CAND_ALPHA",
            timestamp=1010.0,
            metrics={"sharpe": 1.7, "latency_ms": 10.0},
            tags=["volatility", "mean_reversion"],
        )
        t3 = ExperimentTrace(
            experiment_id="EXP_003",
            candidate_id="CAND_BETA",
            timestamp=1020.0,
            metrics={"sharpe": 0.8, "latency_ms": 25.0},
            tags=["trend_following"],
        )

        h1 = self.aggregator.record_trace(t1)
        h2 = self.aggregator.record_trace(t2)
        h3 = self.aggregator.record_trace(t3)

        self.assertTrue(len(h1) > 0)
        self.assertTrue(len(h2) > 0)
        self.assertTrue(len(h3) > 0)

        traces_alpha = self.aggregator.get_experiment_traces("CAND_ALPHA")
        self.assertEqual(len(traces_alpha), 2)
        self.assertEqual(traces_alpha[0].experiment_id, "EXP_001")
        self.assertEqual(traces_alpha[1].experiment_id, "EXP_002")

        traces_beta = self.aggregator.get_experiment_traces("CAND_BETA")
        self.assertEqual(len(traces_beta), 1)
        self.assertEqual(traces_beta[0].experiment_id, "EXP_003")

    def test_deterministic_aggregate_metrics(self):
        for i, val in enumerate([1.0, 2.0, 3.0, 4.0, 5.0]):
            t = ExperimentTrace(
                experiment_id=f"EXP_{i}",
                candidate_id="CAND_STAT",
                timestamp=100.0 + i,
                metrics={"score": val},
                tags=["batch_test"],
            )
            self.aggregator.record_trace(t)

        aggs = self.aggregator.compute_aggregate_metrics("CAND_STAT")
        self.assertEqual(aggs["trace_count"], 5.0)
        self.assertEqual(aggs["score_mean"], 3.0)
        self.assertEqual(aggs["score_p50"], 3.0)
        self.assertEqual(aggs["score_p95"], 5.0)
        self.assertEqual(aggs["score_variance"], 2.0)
        self.assertAlmostEqual(aggs["score_stability_index"], 1.0 / 3.0, places=5)


if __name__ == "__main__":
    unittest.main()
