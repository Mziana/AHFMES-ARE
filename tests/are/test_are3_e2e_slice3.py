"""
End-to-End Integration Tests for AHFMES ARE-3 Slice-3 (ACC-326)

Validates the full multi-agent autonomous scientific discovery lifecycle:
1. Multi-iteration autonomous cycle with succession of champions.
2. Cryptographic Promotion gating and Separation of Duties.
3. Rollback of compromised or degraded champion.
4. Fail-closed rejection of underperforming candidates.
5. Monotonic budget depletion terminating at NO_EDGE_FOUND.
"""

import os
import tempfile
import unittest

from are.champion import ChampionRegistry
from are.coordinator import AgentAssignment, ResearchCoordinator
from are.evidence import EvidenceLedger
from are.governor import CriticEngine, GovernorEngine
from are.habitat import ConditionAtlas, HabitatAdapter
from are.sandbox import CapabilitySandbox
from are.search_tree import ProgramBudget, SearchTreeEngine
from are.storage import EventStore
from are.telemetry import TelemetryAggregator
from are.validation import ValidationService


class TestARE3Slice3EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "slice3_e2e.db")
        self.store = EventStore(self.db_path)
        self.ledger = EvidenceLedger(self.db_path)

        self.budget = ProgramBudget(total_budget=30.0)
        self.search_tree = SearchTreeEngine(self.budget)
        self.sandbox = CapabilitySandbox(default_timeout_sec=2.0)
        self.telemetry = TelemetryAggregator(self.store)
        self.atlas = ConditionAtlas()
        self.habitat = HabitatAdapter(self.atlas, self.store)
        self.validation = ValidationService(self.ledger, self.store)
        self.critic = CriticEngine()
        self.governor = GovernorEngine()
        self.champion_registry = ChampionRegistry(self.store)

        self.coordinator = ResearchCoordinator(
            search_tree_engine=self.search_tree,
            sandbox=self.sandbox,
            telemetry=self.telemetry,
            habitat=self.habitat,
            validation=self.validation,
            critic=self.critic,
            governor=self.governor,
            champion_registry=self.champion_registry,
        )

        self.assignment = AgentAssignment(
            discovery_agent="Autonomous_Researcher_1",
            validation_agent="Autonomous_Validator_2",
            governor_agent="Autonomous_Governor_3",
        )

    def tearDown(self):
        self.store.close()
        self.ledger.close()
        self.tmp_dir.cleanup()

    def test_complete_autonomous_discovery_lifecycle(self):
        cutoff_1 = 1726000000.0

        # === Iteration 1: Promote First Champion ===
        res_1 = self.coordinator.run_autonomous_cycle(
            hypothesis_spec={"hypothesis": "Mean Reversion Alpha", "symbol": "BTCUSDT", "budget_cost": 10.0},
            evaluation_func=lambda f: {"performance": 0.85, "score": 0.85},
            market_features={"volatility": 1.1, "trend_strength": 0.8},
            holdout_dataset=[{"timestamp": cutoff_1 - 100, "score": 0.85}, {"timestamp": cutoff_1 - 50, "score": 0.88}],
            assignment=self.assignment,
            as_of_cutoff=cutoff_1,
        )
        self.assertEqual(res_1.status, "PROMOTED")
        champ_1_id = res_1.details["champion_id"]
        self.assertEqual(self.champion_registry.get_active_champion().champion_id, champ_1_id)

        # === Iteration 2: Promote Superior Challenger as Second Champion ===
        cutoff_2 = 1726100000.0
        res_2 = self.coordinator.run_autonomous_cycle(
            hypothesis_spec={
                "hypothesis": "Nonlinear Volatility Expansion Alpha",
                "symbol": "BTCUSDT",
                "budget_cost": 10.0,
                "champion_metrics": {"performance": 0.85, "drawdown": 0.10},
            },
            evaluation_func=lambda f: {"performance": 0.95, "score": 0.95},
            market_features={"volatility": 2.2, "trend_strength": 1.5},
            holdout_dataset=[{"timestamp": cutoff_2 - 100, "score": 0.94}, {"timestamp": cutoff_2 - 50, "score": 0.96}],
            assignment=self.assignment,
            as_of_cutoff=cutoff_2,
        )
        self.assertEqual(res_2.status, "PROMOTED")
        champ_2_id = res_2.details["champion_id"]
        self.assertEqual(self.champion_registry.get_active_champion().champion_id, champ_2_id)

        # === Rollback Champion 2 -> Champion 1 Restored ===
        restored = self.champion_registry.rollback_champion(reason="Regime shift instability", timestamp=cutoff_2 + 500)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.champion_id, champ_1_id)
        self.assertEqual(self.champion_registry.get_active_champion().champion_id, champ_1_id)

        # === Iteration 3: Underperforming Candidate Rejected ===
        cutoff_3 = 1726200000.0
        res_3 = self.coordinator.run_autonomous_cycle(
            hypothesis_spec={
                "hypothesis": "Weak Trend Follower",
                "symbol": "BTCUSDT",
                "budget_cost": 10.0,
                "performance_threshold": 0.75,
            },
            evaluation_func=lambda f: {"performance": 0.50, "score": 0.50},
            market_features={"volatility": 0.9, "trend_strength": 0.3},
            holdout_dataset=[{"timestamp": cutoff_3 - 100, "score": 0.50}],
            assignment=self.assignment,
            as_of_cutoff=cutoff_3,
        )
        self.assertEqual(res_3.status, "REJECTED")
        self.assertEqual(self.champion_registry.get_active_champion().champion_id, champ_1_id)

        # === Iteration 4: Budget Depleted -> NO_EDGE_FOUND ===
        cutoff_4 = 1726300000.0
        self.assertTrue(self.budget.is_exhausted)
        res_4 = self.coordinator.run_autonomous_cycle(
            hypothesis_spec={"hypothesis": "Post Exhaustion Attempt", "symbol": "BTCUSDT", "budget_cost": 1.0},
            evaluation_func=lambda f: {"performance": 0.90},
            market_features={"volatility": 1.0},
            holdout_dataset=[{"timestamp": cutoff_4 - 100, "score": 0.90}],
            assignment=self.assignment,
            as_of_cutoff=cutoff_4,
        )
        self.assertEqual(res_4.status, "NO_EDGE_FOUND")


if __name__ == "__main__":
    unittest.main()
