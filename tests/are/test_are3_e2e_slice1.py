"""
End-to-End Integration Tests for AHFMES ARE-3 Slice-1 (ACC-308)

Validates the full pipeline:
1. SearchTree exploration with ProgramBudget tracking.
2. Out-of-sample ValidationService with Information-Time gating and evidence exposure accounting.
3. Adversarial evaluation via CriticEngine.
4. Separation of Duties and final PromotionDisposition by GovernorEngine.
"""

import os
import tempfile
import unittest

from are.evidence import EvidenceLedger
from are.governor import CriticEngine, GovernorEngine
from are.search_tree import ProgramBudget, SearchTreeEngine
from are.storage import EventStore
from are.validation import ValidationService


class TestARE3Slice1EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "are3_e2e.db")
        self.event_store = EventStore(self.db_path)
        self.evidence_ledger = EvidenceLedger(self.db_path)
        self.validation_service = ValidationService(self.evidence_ledger, self.event_store)
        self.critic_engine = CriticEngine()
        self.governor_engine = GovernorEngine()

    def tearDown(self):
        self.event_store.close()
        self.evidence_ledger.close()
        self.tmp_dir.cleanup()

    def test_full_pipeline_success_flow(self):
        # 1. Search Tree exploration under strict budget
        budget = ProgramBudget(total_budget=100.0)
        tree = SearchTreeEngine(budget=budget)

        root = tree.spawn_node(
            parent_node=None,
            hypothesis_data={"hypothesis": "Mean Reversion on Volatility Spikes", "regime": "HIGH_VOL"},
            budget_cost=10.0,
        )
        self.assertEqual(budget.remaining_budget, 90.0)

        candidate_node = tree.spawn_node(
            parent_node=root,
            hypothesis_data={"candidate_id": "CAND_ARE3_001", "model": "AdaptiveMeanReversionV1"},
            budget_cost=15.0,
        )
        self.assertEqual(budget.remaining_budget, 75.0)

        # 2. Out-of-sample holdout validation
        as_of_ts = 1724800000.0
        holdout_data = [
            {"timestamp": 1724790000.0, "score": 0.85},
            {"timestamp": 1724795000.0, "score": 0.90},
            {"timestamp": 1724799000.0, "score": 0.88},
        ]

        val_report = self.validation_service.validate_candidate(
            candidate_id="CAND_ARE3_001",
            holdout_token="HOLDOUT_ARE3_S1",
            as_of_ts=as_of_ts,
            dataset=holdout_data,
            performance_threshold=0.70,
        )
        self.assertEqual(val_report.status, "VALIDATED")

        # Mark candidate outcome in tree
        tree.record_node_outcome(candidate_node.node_id, success=True)

        # 3. Critic adversarial comparison against existing champion
        champion_metrics = {"performance": 0.70, "drawdown": 0.15}
        challenger_metrics = {"performance": 0.86, "drawdown": 0.08}
        critic_pass = self.critic_engine.evaluate_adversarial(
            challenger_metrics=challenger_metrics,
            champion_metrics=champion_metrics,
            stress_factor=1.2,
        )
        self.assertTrue(critic_pass)

        # 4. Governor promotion gate with SoD
        disposition = self.governor_engine.evaluate_promotion(
            candidate_id="CAND_ARE3_001",
            champion_id="CHAMPION_V0",
            validation_report=val_report,
            critic_passed=critic_pass,
            creator_principal="Principal_Research_Alice",
            validator_principal="Principal_Validate_Bob",
            promoter_principal="Principal_Govern_Charlie",
            current_ts=as_of_ts,
        )

        self.assertEqual(disposition.decision, "PROMOTED")
        self.assertIn("defeated Champion", disposition.rationale)

        # 5. Verify immutable evidence trail in Evidence Ledger
        conn = self.event_store._get_conn()
        cur = conn.execute("SELECT exposure_event_id, research_program_id FROM evidence_exposures")
        rows = cur.fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "ARE3_RESEARCH")


if __name__ == "__main__":
    unittest.main()
