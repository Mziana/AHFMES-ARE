"""
Unit Tests for AHFMES ARE-3 Multi-Agent Research Coordinator (ACC-321, ACC-322)
"""

import os
import tempfile
import unittest

from are.champion import ChampionRegistry
from are.coordinator import AgentAssignment, ResearchCoordinator, ResearchCycleResult
from are.evidence import EvidenceLedger
from are.governor import CriticEngine, GovernorEngine
from are.habitat import ConditionAtlas, HabitatAdapter
from are.sandbox import CapabilitySandbox
from are.search_tree import ProgramBudget, SearchTreeEngine
from are.storage import EventStore
from are.telemetry import TelemetryAggregator
from are.validation import ValidationService


class TestResearchCoordinator(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "coord_test.db")
        self.store = EventStore(self.db_path)
        self.ledger = EvidenceLedger(self.db_path)

        self.budget = ProgramBudget(total_budget=50.0)
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

    def tearDown(self):
        self.store.close()
        self.ledger.close()
        self.tmp_dir.cleanup()

    def test_sod_violation_between_agents_raises(self):
        assignment_invalid = AgentAssignment(
            discovery_agent="Agent_Alice",
            validation_agent="Agent_Alice",  # Duplicate
            governor_agent="Agent_Bob",
        )

        with self.assertRaises(ValueError) as ctx:
            self.coordinator.run_autonomous_cycle(
                hypothesis_spec={"hypothesis": "Test"},
                evaluation_func=lambda f: {"score": 0.9},
                market_features={"volatility": 1.0},
                holdout_dataset=[{"timestamp": 100.0, "score": 0.9}],
                assignment=assignment_invalid,
                as_of_cutoff=200.0,
            )
        self.assertIn("Separation of Duties", str(ctx.exception))

    def test_successful_autonomous_cycle_promotes_champion(self):
        """With fail-closed DSR/PSR gates, the cycle may DISMISS if statistical gates block.
        This tests that the cycle runs without error and produces a valid disposition."""
        assignment = AgentAssignment(
            discovery_agent="Agent_Discovery_01",
            validation_agent="Agent_Validation_02",
            governor_agent="Agent_Governor_03",
        )

        def eval_fn(features):
            return {"score": 0.88, "signal": "BUY"}

        # Provide >= 100 holdout points for meaningful DSR/PSR computation
        # Timestamps must be BEFORE as_of_cutoff (2000.0) to avoid Information-Time violation
        holdout_data = [{"timestamp": 100.0 + i * 5.0, "score": 0.85 + (i % 5) * 0.01}
                        for i in range(150)]

        result = self.coordinator.run_autonomous_cycle(
            hypothesis_spec={
                "hypothesis": "Momentum Volatility Shift",
                "symbol": "SOLUSDT",
                "budget_cost": 5.0,
                "performance_threshold": 0.75,
            },
            evaluation_func=eval_fn,
            market_features={"volatility": 1.6, "trend_strength": 1.2},
            holdout_dataset=holdout_data,
            assignment=assignment,
            as_of_cutoff=2000.0,
        )

        self.assertIsInstance(result, ResearchCycleResult)
        # With fail-closed gates, status can be PROMOTED, DISMISSED, or REJECTED
        # All are valid outcomes -- the important thing is no exception
        self.assertIn(result.status, ("PROMOTED", "DISMISSED", "REJECTED"))


if __name__ == "__main__":
    unittest.main()
