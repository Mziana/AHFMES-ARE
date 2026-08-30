"""
AHFMES ARE-4 — Final System-Wide Qualification Test Suite (ACC-423)

Validates the full, coherent, end-to-end integration across all 4 ARE waves:
1. ARE-1: Core Kernel (Append-Only EventStore, EvidenceLedger, Hash Chains, CAS)
2. ARE-2: Experience Intelligence (ExperienceStore, QualityGate, AnomalyDetector, Replay, Bridge)
3. ARE-3: Autonomous Science (SearchTree, Sandbox, Telemetry, Habitat, Validation, Critic, Governor, ChampionRegistry)
4. ARE-4: Governed Evolution (CapitalSafetyKernel, OperationalBrain, RegretAnalyzer, EvolutionaryLoop)
"""

import json
import os
import tempfile
import unittest

# ARE-1 Kernel
from are.canonical import canonicalize_json, canonicalize_object
from are.evidence import EvidenceLedger, EvidenceSnapshot
from are.registry import Registry
from are.storage import EventStore

# ARE-2 Experience Intelligence
from are.anomaly import AlertSeverity, AnomalyDetector
from are.experience_store import (
    ExperienceRecord,
    ExperienceStore,
    QualityGate,
    StreamType,
    EvidenceExperienceBridge,
    REQUIRED_PROVENANCE_FIELDS,
)
from are.replay import BatchReplayEngine, WhatIfSensitivityEngine

# ARE-3 Autonomous Science
from are.champion import ChampionRecord, ChampionRegistry
from are.coordinator import AgentAssignment, ResearchCoordinator, ResearchCycleResult
from are.governor import CriticEngine, GovernorEngine, PromotionDisposition
from are.habitat import ConditionAtlas, HabitatAdapter
from are.sandbox import CapabilitySandbox
from are.search_tree import ProgramBudget, SearchTreeEngine
from are.telemetry import TelemetryAggregator
from are.validation import ValidationService

# ARE-4 Governed Evolution
from are.evolution import AdaptationTrigger, EvolutionaryLoop, RegretAnalyzer
from are.operational import OperationalBrain, OperationalSignal
from are.safety import CapitalSafetyKernel, SafetyDecision, SafetyLimits


class TestARE4SystemWideQualification(unittest.TestCase):
    """Full End-to-End System-Wide Qualification Test."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "system_qualification.db")

        # 1. Initialize ARE-1 Kernel
        self.store = EventStore(self.db_path)
        self.ledger = EvidenceLedger(self.db_path)
        self.registry = Registry(self.db_path)

        # 2. Initialize ARE-2 Experience Intelligence
        self.quality_gate = QualityGate()
        self.exp_store = ExperienceStore(self.db_path)
        self.bridge = EvidenceExperienceBridge(self.ledger, self.exp_store)
        self.anomaly_detector = AnomalyDetector()

        # 3. Initialize ARE-3 Autonomous Science
        self.champion_registry = ChampionRegistry(self.store)
        self.budget = ProgramBudget(total_budget=200.0)
        self.search_tree = SearchTreeEngine(self.budget)
        self.sandbox = CapabilitySandbox(default_timeout_sec=2.0)
        self.telemetry = TelemetryAggregator(self.store)
        self.atlas = ConditionAtlas()
        self.habitat = HabitatAdapter(self.atlas, self.store)
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

        # 4. Initialize ARE-4 Governed Evolution
        self.safety_limits = SafetyLimits(max_drawdown_pct=0.10, volatility_cutoff=2.5)
        self.safety_kernel = CapitalSafetyKernel(self.safety_limits)
        self.brain = OperationalBrain(
            champion_registry=self.champion_registry,
            safety_kernel=self.safety_kernel,
            habitat=self.habitat,
            event_store=self.store,
        )
        self.regret_analyzer = RegretAnalyzer(self.store)
        self.evolutionary_loop = EvolutionaryLoop(
            regret_analyzer=self.regret_analyzer,
            research_coordinator=self.coordinator,
            registry=self.registry,
        )

        self.assignment = AgentAssignment(
            discovery_agent="SystemQual_Discovery_Agent",
            validation_agent="SystemQual_Validation_Agent",
            governor_agent="SystemQual_Governor_Agent",
        )

        self.prov = {
            "source_id": "QUAL_SRC_001",
            "timestamp": 1728000000.0,
            "session_id": "QUAL_SESS_001",
            "environment": "TEST_ENV",
            "collector_version": "1.0.0",
            "input_hash": "0" * 64,
            "schema_version": "1.0",
            "trace_id": "TRACE_001",
        }

    def tearDown(self):
        self.store.close()
        self.ledger.close()
        self.registry.close()
        self.exp_store.close()
        self.tmp_dir.cleanup()

    def test_full_system_lifecycle_qualification(self):
        """
        Comprehensive test exercising:
        ARE-1 Storage/Ledger -> ARE-2 Experience & Replay -> ARE-3 Science & Promotion -> ARE-4 Fast/Slow Evolution
        """
        t0 = 1728000000.0

        # -------------------------------------------------------------
        # STEP 1: ARE-1 Evidence Ledger & Cryptographic Integrity
        # -------------------------------------------------------------
        snap = self.ledger.create_snapshot(
            evidence_snapshot_id="SNAP_QUAL_001",
            source_manifest_hash="a" * 64,
            source_kind="L2_ORDERBOOK",
            source_epoch="2026_Q3",
            information_time_contract_hash="b" * 64,
            row_or_event_identity_contract_hash="c" * 64,
            completeness_proof_hash="d" * 64,
            provenance_status="VERIFIED",
            origin="HISTORICAL_DISCOVERY",
        )
        self.assertIsNotNone(snap)
        self.assertTrue(self.store.verify_chain(f"evidence_snapshot:SNAP_QUAL_001"))

        # -------------------------------------------------------------
        # STEP 2: ARE-2 Experience Ingestion & Bridge
        # -------------------------------------------------------------
        res_id = "RES_QUAL_001"
        self.ledger.create_reservation(
            reservation_id=res_id,
            research_program_id="PROGRAM_QUAL_P01",
            program_budget_envelope_root_hash="1" * 64,
            research_family_root="2" * 64,
            claim_family_root="3" * 64,
            research_contract_root_hash="4" * 64,
            evidence_snapshot_root_hash=snap.root_hash,
            validation_family_root_hash="5" * 64,
            candidate_batch_root_hash="6" * 64,
            primary_estimand_root_hash="7" * 64,
            multiplicity_plan_root_hash="8" * 64,
            search_tree_root_hash="9" * 64,
            search_debt_root_hash="a" * 64,
            permitted_disclosures_root_hash=None,
            permitted_actor_ids=["actor_qual"],
            role="INTERNAL_VALIDATION",
        )

        exp_rec, _ = self.bridge.record_derived_experience(
            reservation_id=res_id,
            stream_type=StreamType.DECISION_MEMORY,
            payload={"action": "HOLD", "confidence": "0.85"},
            provenance=self.prov,
            expected_revision=0,
        )
        self.assertEqual(exp_rec.revision, 1)

        # -------------------------------------------------------------
        # STEP 3: ARE-3 Autonomous Science Cycle & Initial Promotion
        # -------------------------------------------------------------
        cycle_res = self.coordinator.run_autonomous_cycle(
            hypothesis_spec={"hypothesis_id": "HYP_QUAL_001", "formula": "alpha_qual_1"},
            evaluation_func=lambda f: {"performance": 0.90, "score": 0.90},
            market_features={"volatility": 1.1, "trend_strength": 1.5},
            holdout_dataset=[{"timestamp": t0, "score": 0.90}],
            assignment=self.assignment,
            as_of_cutoff=t0 + 100,
        )
        self.assertIn(cycle_res.status, ("PROMOTED", "REJECTED"))
        champ_v1 = self.champion_registry.get_active_champion()
        self.assertIsNotNone(champ_v1)
        if cycle_res.status == "PROMOTED":
            self.assertEqual(champ_v1.champion_id, cycle_res.details["champion_id"])

        # -------------------------------------------------------------
        # STEP 4: ARE-4 Fast Loop Operation & Anomaly Shock
        # -------------------------------------------------------------
        # Normal Fast Loop Tick
        sig_norm = self.brain.process_tick(
            symbol="BTCUSDT",
            timestamp=t0 + 200,
            market_features={"volatility": 1.1, "trend_strength": 1.5},
            current_risk_state={"drawdown": 0.01, "volatility": 1.1, "order_count": 1},
            as_of_cutoff=t0 + 300,
        )
        self.assertEqual(sig_norm.final_action, "BUY")

        # Shock Ticks -> Consecutive Safety Vetoes
        for i in range(5):
            self.brain.process_tick(
                symbol="BTCUSDT",
                timestamp=t0 + 300 + (i * 10),
                market_features={"volatility": 3.2, "trend_strength": 0.1},
                current_risk_state={"drawdown": 0.08, "volatility": 3.2, "order_count": i + 2},
                as_of_cutoff=t0 + 400,
            )

        # -------------------------------------------------------------
        # STEP 5: ARE-4 Slow Loop Evolution & Succession
        # -------------------------------------------------------------
        evol_res = self.evolutionary_loop.evaluate_and_evolve(
            symbol="BTCUSDT",
            current_features={"volatility": 1.2, "trend_strength": 1.9},
            holdout_dataset=[{"timestamp": t0 + 500, "score": 0.95}],
            assignment=self.assignment,
            as_of_cutoff=t0 + 600,
            evaluation_func=lambda f: {"performance": 0.95, "score": 0.95},
        )
        self.assertIsNotNone(evol_res)
        self.assertIn(evol_res.status, ("PROMOTED", "REJECTED"))

        champ_v2 = self.champion_registry.get_active_champion()
        self.assertIsNotNone(champ_v2)
        if evol_res.status == "PROMOTED":
            self.assertNotEqual(champ_v2.champion_id, champ_v1.champion_id)

        # Fast Loop operates on current Champion
        sig_evolved = self.brain.process_tick(
            symbol="BTCUSDT",
            timestamp=t0 + 700,
            market_features={"volatility": 1.2, "trend_strength": 1.9},
            current_risk_state={"drawdown": 0.01, "volatility": 1.2, "order_count": 1},
            as_of_cutoff=t0 + 800,
        )
        self.assertEqual(sig_evolved.final_action, "BUY")
        self.assertEqual(sig_evolved.raw_decision["champion_id"], champ_v2.champion_id)

        # -------------------------------------------------------------
        # STEP 6: Cryptographic Verification Across All Streams
        # -------------------------------------------------------------
        self.assertTrue(self.store.verify_chain("champion_registry"))
        self.assertTrue(self.store.verify_chain("operational_signals"))
        self.assertTrue(self.store.verify_chain("research_telemetry"))


if __name__ == "__main__":
    unittest.main()
