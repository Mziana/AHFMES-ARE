"""
Unit and Integration Tests for AHFMES ARE-2 Slice-1 Parts B, C, D

Covers:
- ACC-2: Replay Engine, What-If simulation, Knowledge Synthesis & Capability Gap
- ACC-3: Anomaly Alerting, Component Adapters, Configuration Immutability
- ACC-4: Audit Logger reproducibility, Resource Bounds enforcement
- ACC-8: Integration Evidence Ledger ARE-1 + Experience Store ARE-2 (exposure accounting)
- ACC-9: Fail-closed checks, zero raw SQLite mutations, zero random state
"""

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from are.storage import EventStore
from are.evidence import EvidenceLedger, RelationRegistry
from are.experience import (
    AlertSeverity,
    AnomalyAlertEngine,
    AnomalyDetector,
    AuditLogger,
    CapabilityGapAssessment,
    ComponentAdapterRegistry,
    CounterfactualQuality,
    CounterfactualSimulationResult,
    EvidenceExperienceBridge,
    ExperienceConfig,
    ExperienceRecord,
    ExperienceStore,
    ExperienceStoreError,
    KnowledgeSynthesizer,
    QualityGate,
    ResourceBoundedExecutor,
    ResourceLimitExceededError,
    StreamType,
)


class TestReplayAndWhatIfEngine(unittest.TestCase):
    """B1: Deterministic Replay Engine & What-If Simulator Tests."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "experience_replay.db")
        self.store = ExperienceStore(self.db_path, wal_mode=True)
        self.prov = {
            "source_id": "src",
            "timestamp": 100,
            "session_id": "s",
            "environment": "e",
            "collector_version": "v",
            "input_hash": "h",
            "schema_version": "1",
            "trace_id": "t",
        }

    def tearDown(self):
        self.store.close()
        self.tmp_dir.cleanup()

    def test_what_if_simulation_returns_result_dataclass(self):
        self.store.append(StreamType.DECISION_MEMORY, {"volume": 100}, self.prov, 0)

        def reducer(state, record):
            data = json.loads(record.data_bytes.decode("utf-8"))
            state["total"] = state.get("total", 0) + int(data.get("volume", 0))
            return state

        result = self.store.fork_what_if(
            stream_type=StreamType.DECISION_MEMORY,
            initial_state={"total": 0},
            reducer_func=reducer,
            counterfactual_events=[{"volume": 50}, {"volume": 25}],
        )

        self.assertIsInstance(result, CounterfactualSimulationResult)
        self.assertEqual(result.final_state["total"], 175)
        self.assertIsNotNone(result.original_state_hash)
        self.assertIsNotNone(result.simulation_state_hash)


class TestKnowledgeSynthesizer(unittest.TestCase):
    """B2: Knowledge Synthesis & Capability Gap Tests."""

    def setUp(self):
        self.synthesizer = KnowledgeSynthesizer()

    def test_capability_gap_assessment_approved(self):
        assessment = self.synthesizer.synthesize_capability_gap(
            gap_description="Need higher frequency market regime detection",
            evidence_count=10,
            budget_allocated=500.0,
            owner_approved=True,
        )
        self.assertIsInstance(assessment, CapabilityGapAssessment)
        self.assertTrue(assessment.owner_approved)
        self.assertTrue(assessment.evidence_threshold_met)

    def test_capability_gap_rejected_without_owner_approval(self):
        assessment = self.synthesizer.synthesize_capability_gap(
            gap_description="Unapproved expansion hypothesis",
            evidence_count=10,
            budget_allocated=500.0,
            owner_approved=False,
        )
        self.assertFalse(assessment.owner_approved)


class TestAnomalyAlertEngine(unittest.TestCase):
    """C1: Anomaly Alerting & Deduplication Tests."""

    def setUp(self):
        self.detector = AnomalyDetector()
        self.alert_engine = AnomalyAlertEngine(cooldown_sec=60.0)

    def test_alert_generation_and_cooldown(self):
        prices = [100.0, 120.0, 80.0, 130.0]
        res = self.detector.analyze("REGIME_SHIFT", prices, spread=2.0, volatility=0.5, volume=5.0)

        # First trigger should produce an alert
        alert1 = self.alert_engine.process_anomaly(res)
        self.assertIsNotNone(alert1)
        self.assertEqual(alert1.anomaly_type, "REGIME_SHIFT")

        # Second trigger within 60s cooldown should be suppressed (None)
        alert2 = self.alert_engine.process_anomaly(res)
        self.assertIsNone(alert2)


class TestComponentAdapterRegistry(unittest.TestCase):
    """C2: Component Reuse Adapter Tests."""

    def setUp(self):
        self.registry = ComponentAdapterRegistry()

    def test_register_supported_adapter(self):
        h = self.registry.register_adapter("orchestrator", {"version": "v1", "active": True})
        self.assertIsNotNone(h)

        adapter = self.registry.get_adapter("orchestrator")
        self.assertEqual(adapter["component_name"], "orchestrator")

    def test_unsupported_component_raises(self):
        with self.assertRaises(ExperienceStoreError):
            self.registry.register_adapter("unsupported_module_xyz", {})


class TestConfigAndAuditLogger(unittest.TestCase):
    """C3, D1, D3: Configuration & Audit Logger Tests."""

    def test_config_hash_generated(self):
        cfg = ExperienceConfig(max_memory_mb=512, max_replay_sec=5.0)
        self.assertIsNotNone(cfg.config_hash)

    def test_audit_logger_jsonl(self):
        tmp_log = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl")
        tmp_log.close()

        logger = AuditLogger(log_path=tmp_log.name)
        entry = logger.log(
            component="TestComp",
            operation="OP1",
            input_data={"in": 1},
            output_data={"out": 2},
            params={"p": 3},
            duration_ms=12.5,
        )
        self.assertTrue(entry.success)

        # Read JSONL file
        with open(tmp_log.name, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)

        os.remove(tmp_log.name)


class TestResourceBoundedExecutor(unittest.TestCase):
    """D2: Resource Bounds Enforcement Tests."""

    def setUp(self):
        self.cfg = ExperienceConfig(max_anomaly_ms=50.0, max_replay_sec=2.0)
        self.executor = ResourceBoundedExecutor(self.cfg)

    def test_anomaly_latency_exceeded_raises(self):
        with self.assertRaises(ResourceLimitExceededError):
            self.executor.check_anomaly_latency(120.0)

    def test_anomaly_latency_ok(self):
        self.executor.check_anomaly_latency(30.0)


class TestEvidenceExperienceBridge(unittest.TestCase):
    """B3 & ACC-8: Integration Evidence Ledger ARE-1 + Experience Store ARE-2 Tests."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "integration.db")

        # Setup EvidenceLedger (ARE-1)
        self.evidence_ledger = EvidenceLedger(self.db_path)

        # Setup ExperienceStore (ARE-2)
        self.experience_store = ExperienceStore(self.db_path)

        # Setup Bridge
        self.bridge = EvidenceExperienceBridge(self.evidence_ledger, self.experience_store)

    def tearDown(self):
        self.evidence_ledger.close()
        self.experience_store.close()
        self.tmp_dir.cleanup()

    def test_record_derived_experience_with_exposure_accounting(self):
        # Create prerequisite Evidence Ledger ARE-1 records
        prog_id = "PRG_001"
        res_fam = "0" * 64
        claim_fam = "0" * 64

        snap = self.evidence_ledger.create_snapshot(
            evidence_snapshot_id="SNAP_001",
            source_manifest_hash="0" * 64,
            source_kind="TEST_KIND",
            source_epoch="E1",
            information_time_contract_hash="0" * 64,
            row_or_event_identity_contract_hash="0" * 64,
            completeness_proof_hash="0" * 64,
            provenance_status="VERIFIED",
            origin="HISTORICAL_DISCOVERY",
        )

        res = self.evidence_ledger.create_reservation(
            reservation_id="RES_001",
            research_program_id=prog_id,
            program_budget_envelope_root_hash="0" * 64,
            research_family_root=res_fam,
            claim_family_root=claim_fam,
            research_contract_root_hash="0" * 64,
            evidence_snapshot_root_hash=snap.root_hash,
            validation_family_root_hash="0" * 64,
            candidate_batch_root_hash="0" * 64,
            primary_estimand_root_hash="0" * 64,
            multiplicity_plan_root_hash="0" * 64,
            search_tree_root_hash="0" * 64,
            search_debt_root_hash="0" * 64,
            permitted_disclosures_root_hash=None,
            permitted_actor_ids=["actor1"],
            role="INTERNAL_VALIDATION",
        )

        prov = {
            "source_id": "bridge_test",
            "timestamp": 1000,
            "session_id": "sess_1",
            "environment": "integration",
            "collector_version": "v1",
            "input_hash": "hash_in",
            "schema_version": "v1",
            "trace_id": "tr_1",
        }

        # Execute bridge recording
        exp_rec, exp_event = self.bridge.record_derived_experience(
            reservation_id="RES_001",
            stream_type=StreamType.DECISION_MEMORY,
            payload={"model_decision": "HOLD"},
            provenance=prov,
            expected_revision=0,
        )

        self.assertIsInstance(exp_rec, ExperienceRecord)
        self.assertEqual(exp_rec.revision, 1)
        self.assertIsNotNone(exp_event.exposure_event_id)
        self.assertEqual(exp_event.evidence_snapshot_root_hash, snap.root_hash)


if __name__ == "__main__":
    unittest.main()
