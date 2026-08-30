"""
End-to-End Integration Tests for AHFMES ARE-4 Slice-2 (ACC-417)

Validates the full dual-loop architecture:
Fast Loop (Operational) -> Anomaly Regret -> Evolutionary Trigger -> Slow Loop (Research) -> Champion Succession
"""

import os
import tempfile
import unittest

from are.champion import ChampionRegistry
from are.coordinator import AgentAssignment, ResearchCoordinator
from are.evidence import EvidenceLedger
from are.evolution import EvolutionaryLoop, RegretAnalyzer
from are.governor import CriticEngine, GovernorEngine, PromotionDisposition
from are.habitat import ConditionAtlas, HabitatAdapter
from are.operational import OperationalBrain
from are.registry import Registry
from are.sandbox import CapabilitySandbox
from are.search_tree import ProgramBudget, SearchTreeEngine
from are.safety import CapitalSafetyKernel, SafetyLimits
from are.storage import EventStore
from are.telemetry import TelemetryAggregator
from are.validation import ValidationService


class TestARE4Slice2EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "slice2_e2e.db")
        self.store = EventStore(self.db_path)
        self.ledger = EvidenceLedger(self.db_path)
        self.registry = Registry(self.db_path)

        self.champion_registry = ChampionRegistry(self.store)
        self.limits = SafetyLimits(max_drawdown_pct=0.15, volatility_cutoff=2.0)
        self.safety_kernel = CapitalSafetyKernel(self.limits)
        self.atlas = ConditionAtlas()
        self.habitat = HabitatAdapter(self.atlas, self.store)

        # Operational Fast Loop
        self.brain = OperationalBrain(
            champion_registry=self.champion_registry,
            safety_kernel=self.safety_kernel,
            habitat=self.habitat,
            event_store=self.store,
        )

        # Scientific Slow Loop
        self.budget = ProgramBudget(total_budget=100.0)
        self.search_tree = SearchTreeEngine(self.budget)
        self.sandbox = CapabilitySandbox(default_timeout_sec=2.0)
        self.telemetry = TelemetryAggregator(self.store)
        self.validation = ValidationService(self.ledger, self.store)
        self.critic = CriticEngine()
        self.governor = GovernorEngine()

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

        self.regret_analyzer = RegretAnalyzer(self.store)
        self.evolutionary_loop = EvolutionaryLoop(
            regret_analyzer=self.regret_analyzer,
            research_coordinator=self.coordinator,
            registry=self.registry,
        )

        self.assignment = AgentAssignment(
            discovery_agent="Evolution_Researcher_01",
            validation_agent="Evolution_Validator_02",
            governor_agent="Evolution_Governor_03",
        )

    def tearDown(self):
        self.store.close()
        self.ledger.close()
        self.registry.close()
        self.tmp_dir.cleanup()

    def test_full_fast_slow_loop_evolution_cycle(self):
        t0 = 1728000000.0

        # Phase 1: Deploy Champion V1
        disp_v1 = PromotionDisposition(
            candidate_id="CAND_INITIAL_V1",
            champion_id="GENESIS",
            decision="PROMOTED",
            rationale="Initial baseline",
            governor_signature="GOV_SIG_001",
            timestamp=t0 - 1000,
        )
        c1 = self.champion_registry.promote_champion("CAND_INITIAL_V1", disp_v1)
        self.assertEqual(self.champion_registry.get_active_champion().champion_id, c1.champion_id)

        # Phase 2: Fast Loop operates normally
        sig1 = self.brain.process_tick(
            symbol="BTCUSDT",
            timestamp=t0 - 500,
            market_features={"volatility": 1.0, "trend_strength": 1.2},
            current_risk_state={"drawdown": 0.01, "volatility": 1.0, "order_count": 0},
            as_of_cutoff=t0,
        )
        self.assertEqual(sig1.final_action, "BUY")

        # Phase 3: Market Regime Shock -> Consecutive CSK Vetoes
        for i in range(4):
            self.brain.process_tick(
                symbol="BTCUSDT",
                timestamp=t0 - 400 + (i * 50),
                market_features={"volatility": 2.8, "trend_strength": 0.2},  # Volatility shock
                current_risk_state={"drawdown": 0.05, "volatility": 2.8, "order_count": i + 1},
                as_of_cutoff=t0,
            )

        # Phase 4: Evolutionary Slow Loop detects regret and autonomously discovers Champion V2
        evol_res = self.evolutionary_loop.evaluate_and_evolve(
            symbol="BTCUSDT",
            current_features={"volatility": 1.4, "trend_strength": 1.8},
            holdout_dataset=[
                {"timestamp": t0 - 50, "score": 0.92},
                {"timestamp": t0 - 20, "score": 0.94},
            ],
            assignment=self.assignment,
            as_of_cutoff=t0,
            evaluation_func=lambda f: {"performance": 0.93, "score": 0.93},
        )

        self.assertIsNotNone(evol_res)
        self.assertIn(evol_res.status, ("PROMOTED", "REJECTED"))

        # Phase 5: Champion V2 is now Active (if promoted)
        active_champ = self.champion_registry.get_active_champion()
        self.assertIsNotNone(active_champ)
        if evol_res.status == "PROMOTED":
            self.assertEqual(active_champ.champion_id, evol_res.details["champion_id"])
            self.assertNotEqual(active_champ.champion_id, c1.champion_id)

        # Phase 6: Fast Loop now uses current champion seamlessly
        sig_evolved = self.brain.process_tick(
            symbol="BTCUSDT",
            timestamp=t0 + 100,
            market_features={"volatility": 1.1, "trend_strength": 1.6},
            current_risk_state={"drawdown": 0.01, "volatility": 1.1, "order_count": 0},
            as_of_cutoff=t0 + 200,
        )
        self.assertEqual(sig_evolved.final_action, "BUY")
        self.assertEqual(sig_evolved.raw_decision["champion_id"], active_champ.champion_id)


if __name__ == "__main__":
    unittest.main()
