"""
End-to-End Integration Tests for AHFMES ARE-3 Slice-2 (ACC-318)

Validates the complete Slice-2 pipeline:
1. Capability Sandbox execution (isolated, timeout-bounded).
2. Telemetry Aggregator recording traces to EventStore and computing deterministic aggregates.
3. Habitat Adapter ingesting environment state observations with Information-Time gating.
4. Validation Service testing out-of-sample holdouts with evidence ledger exposure accounting.
5. Governor Engine verifying SoD and issuing cryptographic PromotionDisposition.
"""

import os
import tempfile
import unittest

from are.evidence import EvidenceLedger
from are.governor import CriticEngine, GovernorEngine
from are.habitat import ConditionAtlas, HabitatAdapter
from are.sandbox import CapabilitySandbox
from are.storage import EventStore
from are.telemetry import ExperimentTrace, TelemetryAggregator
from are.validation import ValidationService


class TestARE3Slice2EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "are3_s2_e2e.db")
        self.store = EventStore(self.db_path)
        self.ledger = EvidenceLedger(self.db_path)
        self.sandbox = CapabilitySandbox(default_timeout_sec=2.0)
        self.telemetry = TelemetryAggregator(self.store)
        self.atlas = ConditionAtlas()
        self.habitat = HabitatAdapter(self.atlas, self.store)
        self.validation = ValidationService(self.ledger, self.store)
        self.critic = CriticEngine()
        self.governor = GovernorEngine()

    def tearDown(self):
        self.store.close()
        self.ledger.close()
        self.tmp_dir.cleanup()

    def test_full_slice2_pipeline_success_flow(self):
        candidate_id = "CAND_ARE3_SLICE2_001"
        champion_id = "CHAMPION_ARE3_V0"
        as_of_cutoff = 1725000000.0

        # 1. Sandbox Execution: pure feature transformation
        def model_eval(features):
            score = features["trend_strength"] * 0.5 + (1.0 / max(0.1, features["volatility"])) * 0.5
            return {"signal": "LONG", "score": score}

        raw_features = {"volatility": 1.2, "trend_strength": 1.8}
        exec_res = self.sandbox.execute(model_eval, args=(raw_features,))
        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.output["signal"], "LONG")

        # 2. Habitat Ingestion: capture market environment observation
        obs = self.habitat.ingest_market_state(
            symbol="BTCUSDT",
            timestamp=1724990000.0,
            features=raw_features,
            as_of_cutoff=as_of_cutoff,
        )
        self.assertEqual(obs.regime, "TRENDING_EXPANSION")

        # 3. Telemetry Recording: log execution traces
        for i, score_val in enumerate([0.82, 0.85, 0.88, 0.84, 0.86]):
            trace = ExperimentTrace(
                experiment_id=f"EXP_TR_{i:03d}",
                candidate_id=candidate_id,
                timestamp=1724990000.0 + (i * 60),
                metrics={"accuracy": score_val, "score": score_val},
                tags=["slice2", "e2e"],
            )
            self.telemetry.record_trace(trace)

        aggs = self.telemetry.compute_aggregate_metrics(candidate_id)
        self.assertEqual(aggs["trace_count"], 5.0)
        self.assertGreater(aggs["score_mean"], 0.80)

        # 4. Out-of-Sample Validation with Evidence Ledger exposure
        holdout_dataset = [
            {"timestamp": 1724991000.0, "score": 0.85},
            {"timestamp": 1724992000.0, "score": 0.88},
            {"timestamp": 1724993000.0, "score": 0.84},
        ]
        val_report = self.validation.validate_candidate(
            candidate_id=candidate_id,
            holdout_token="HOLDOUT_S2_TOKEN",
            as_of_ts=as_of_cutoff,
            dataset=holdout_dataset,
            performance_threshold=0.75,
        )
        self.assertEqual(val_report.status, "VALIDATED")

        # 5. Critic Adversarial Evaluation
        challenger_metrics = {"performance": aggs["score_mean"], "drawdown": 0.05}
        champion_metrics = {"performance": 0.70, "drawdown": 0.12}
        critic_pass = self.critic.evaluate_adversarial(challenger_metrics, champion_metrics, stress_factor=1.1)
        self.assertTrue(critic_pass)

        # 6. Governor SoD Verification and Promotion
        disposition = self.governor.evaluate_promotion(
            candidate_id=candidate_id,
            champion_id=champion_id,
            validation_report=val_report,
            critic_passed=critic_pass,
            creator_principal="Principal_Alpha_Author",
            validator_principal="Principal_Beta_Validator",
            promoter_principal="Principal_Gamma_Promoter",
            current_ts=as_of_cutoff,
        )
        self.assertEqual(disposition.decision, "PROMOTED")
        self.assertIn("defeated Champion", disposition.rationale)


if __name__ == "__main__":
    unittest.main()
