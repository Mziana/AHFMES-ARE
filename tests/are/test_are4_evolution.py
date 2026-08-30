"""
Unit Tests for AHFMES ARE-4 Evolutionary Slow Loop (ACC-411, ACC-412, ACC-415)
"""

import json
import os
import tempfile
import unittest

from are.champion import ChampionRegistry
from are.coordinator import AgentAssignment, ResearchCoordinator, ResearchCycleResult
from are.evidence import EvidenceLedger
from are.evolution import AdaptationTrigger, EvolutionaryLoop, RegretAnalyzer
from are.governor import CriticEngine, GovernorEngine
from are.habitat import ConditionAtlas, HabitatAdapter
from are.registry import Registry
from are.sandbox import CapabilitySandbox
from are.search_tree import ProgramBudget, SearchTreeEngine
from are.storage import EventStore
from are.telemetry import TelemetryAggregator
from are.validation import ValidationService


class TestEvolutionaryLoop(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "evol_test.db")
        self.store = EventStore(self.db_path)
        self.ledger = EvidenceLedger(self.db_path)
        self.registry = Registry(self.db_path)

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

        self.regret_analyzer = RegretAnalyzer(self.store)
        self.evolutionary_loop = EvolutionaryLoop(
            regret_analyzer=self.regret_analyzer,
            research_coordinator=self.coordinator,
            registry=self.registry,
        )

        self.assignment = AgentAssignment(
            discovery_agent="Researcher_Agent_1",
            validation_agent="Validator_Agent_2",
            governor_agent="Governor_Agent_3",
        )

    def tearDown(self):
        self.store.close()
        self.ledger.close()
        self.registry.close()
        self.tmp_dir.cleanup()

    def test_regret_analyzer_detects_anomaly(self):
        # 1. Normal signals -> No trigger
        for i in range(5):
            ev = {
                "symbol": "BTCUSDT",
                "final_action": "BUY",
                "safety_decision": {"allowed": True},
                "timestamp": 1000.0 + i,
            }
            head = self.store.get_head("operational_signals")
            exp_rev = 0 if head is None else head[0]
            prev_h = "0" * 64 if head is None else head[1]
            self.store.append_event("operational_signals", json.dumps(ev).encode("utf-8"), exp_rev, prev_h)

        trigger_none = self.regret_analyzer.analyze_operational_stream("BTCUSDT", lookback_events=5, regret_threshold=0.40)
        self.assertIsNone(trigger_none)

        # 2. Add multiple veto/abstention events -> Breaches threshold
        for i in range(5):
            ev = {
                "symbol": "BTCUSDT",
                "final_action": "ABSTAIN",
                "safety_decision": {"allowed": False},
                "timestamp": 1010.0 + i,
            }
            head = self.store.get_head("operational_signals")
            self.store.append_event("operational_signals", json.dumps(ev).encode("utf-8"), head[0], head[1])

        # 5 out of 10 are vetoed (50% >= 40%)
        trigger = self.regret_analyzer.analyze_operational_stream("BTCUSDT", lookback_events=10, regret_threshold=0.40)
        self.assertIsNotNone(trigger)
        self.assertIsInstance(trigger, AdaptationTrigger)
        self.assertEqual(trigger.symbol, "BTCUSDT")
        self.assertIn("regret breach", trigger.source_anomaly)
        self.assertTrue(len(trigger.trigger_hash) > 0)

    def test_evolutionary_loop_triggers_autonomous_cycle(self):
        # Populate operational vetoes
        for i in range(5):
            ev = {
                "symbol": "ETHUSDT",
                "final_action": "ABSTAIN",
                "safety_decision": {"allowed": False},
                "timestamp": 2000.0 + i,
            }
            head = self.store.get_head("operational_signals")
            exp_rev = 0 if head is None else head[0]
            prev_h = "0" * 64 if head is None else head[1]
            self.store.append_event("operational_signals", json.dumps(ev).encode("utf-8"), exp_rev, prev_h)

        res = self.evolutionary_loop.evaluate_and_evolve(
            symbol="ETHUSDT",
            current_features={"volatility": 1.2, "trend_strength": 1.4},
            holdout_dataset=[{"timestamp": 2050.0, "score": 0.88}],
            assignment=self.assignment,
            as_of_cutoff=2100.0,
            evaluation_func=lambda f: {"performance": 0.88, "score": 0.88},
        )

        self.assertIsNotNone(res)
        self.assertIsInstance(res, ResearchCycleResult)
        self.assertIn(res.status, ("PROMOTED", "REJECTED"))

        # Verify active champion exists (updated if promoted)
        active = self.champion_registry.get_active_champion()
        self.assertIsNotNone(active)
        if res.status == "PROMOTED":
            self.assertEqual(active.champion_id, res.details["champion_id"])


if __name__ == "__main__":
    unittest.main()
