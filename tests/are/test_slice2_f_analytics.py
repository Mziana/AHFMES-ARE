"""
Tests for AHFMES ARE-2 Slice-2 Part F: Advanced Analytics & Capability Gap Engine
Covers:
- ACC-11: Advanced Analytics, Capability Gap Engine, Replay Analytics
"""

import gc
import os
import tempfile
import time
import unittest

from are.experience import (
    AnomalyDetector,
    AnomalyResult,
    AuditLogger,
    BatchReplayEngine,
    CapabilityGapEngine,
    CapabilityGapHypothesis,
    CounterfactualQuality,
    ExperienceRecord,
    ExperienceStore,
    ExperienceStoreError,
    RegimeState,
    ScientificMemory,
    StreamType,
    WhatIfSensitivityEngine,
)


def _cleanup_db(db_path: str) -> None:
    for suffix in ["", "-wal", "-shm"]:
        p = db_path + suffix
        for _ in range(5):
            try:
                if os.path.exists(p):
                    os.unlink(p)
                break
            except (OSError, PermissionError):
                gc.collect()
                time.sleep(0.05)


class TestCapabilityGapEngine(unittest.TestCase):
    """F1: Capability Gap Assessment Engine Tests."""

    def setUp(self):
        self.engine = CapabilityGapEngine(owner_key="SECRET_OWNER_KEY_123")
        self.detector = AnomalyDetector()

    def test_iaq_generation_from_anomalies(self):
        anomalies = [
            AnomalyResult(
                anomaly_type="REGIME_SHIFT",
                severity=2.8,
                counterfactual_quality=CounterfactualQuality.CF_HIGH,
                regime_state=RegimeState.HIGH_VOLATILITY,
                spread_hostility=1.5,
                artifact_hash="hash_anom_1",
                details={"info": "high vol shift"},
            ),
            AnomalyResult(
                anomaly_type="SPREAD_HOSTILITY",
                severity=0.5,
                counterfactual_quality=CounterfactualQuality.CF_LOW,
                regime_state=RegimeState.STABLE,
                spread_hostility=0.2,
                artifact_hash="hash_anom_2",
                details={"info": "low spread"},
            ),
        ]
        iaq_entries = self.engine.generate_iaq_entries_from_anomalies(anomalies)
        self.assertEqual(len(iaq_entries), 1)
        self.assertIn("IAQ_ARE2_AUTO_001", iaq_entries[0]["iaq_id"])
        self.assertEqual(iaq_entries[0]["regime"], "HIGH_VOLATILITY")

    def test_full_capability_gap_lifecycle(self):
        # 1. Create Hypothesis
        hyp = self.engine.create_hypothesis(
            gap_id="GAP_001",
            title="High Volatility Regime Gap",
            description="System lacks dynamic position sizing under fast transition regimes",
            source_anomalies=["ANOM_001", "ANOM_002"],
        )
        self.assertEqual(hyp.gap_id, "GAP_001")
        self.assertTrue(len(hyp.hypothesis_hash) == 64)

        # 2. Design Experiment
        exp = self.engine.design_experiment(hyp, budget_allocated=500.0)
        self.assertEqual(exp["status"], "DESIGNED")
        self.assertEqual(exp["target_evidence_threshold"], 5)

        # 3. Validate Gap (evidence threshold check)
        val_fail = self.engine.validate_gap(exp, evidence_count=3)
        self.assertFalse(val_fail["evidence_threshold_met"])

        val_pass = self.engine.validate_gap(exp, evidence_count=6)
        self.assertTrue(val_pass["evidence_threshold_met"])

        # 4. Request Owner Approval
        # Without valid owner signature -> rejected
        assess_rejected = self.engine.request_owner_approval("GAP_001", val_pass, owner_signature="WRONG_KEY")
        self.assertFalse(assess_rejected.owner_approved)

        # With valid owner signature -> approved
        assess_approved = self.engine.request_owner_approval(
            "GAP_001", val_pass, owner_signature="SECRET_OWNER_KEY_123"
        )
        self.assertTrue(assess_approved.owner_approved)

        # 5. Deploy Capability
        with self.assertRaises(ExperienceStoreError):
            self.engine.deploy_capability(assess_rejected)

        deployment = self.engine.deploy_capability(assess_approved)
        self.assertEqual(deployment["deployment_status"], "ACTIVATED")


class TestScientificMemory(unittest.TestCase):
    """F2: Scientific Memory & Deterministic Synthesis Tests."""

    def setUp(self):
        self.memory = ScientificMemory()

    def test_record_snapshot_and_mine_patterns(self):
        fake_prov = {
            "source_id": "src",
            "timestamp": 100,
            "session_id": "s",
            "environment": "e",
            "collector_version": "v",
            "input_hash": "h",
            "schema_version": "1",
            "trace_id": "t",
        }
        dec_records = [
            ExperienceRecord("decision_memory", 1, "hash_dec_1", "prev_0", b"data1", fake_prov),
            ExperienceRecord("decision_memory", 2, "hash_dec_2", "prev_1", b"data2", fake_prov),
        ]
        reg_records = [
            ExperienceRecord("regret_memory", 1, "hash_dec_1", "prev_0", b"data1", fake_prov),
            ExperienceRecord("regret_memory", 2, "hash_reg_2", "prev_1", b"data3", fake_prov),
        ]

        # Record snapshot
        snap_hash = self.memory.record_snapshot("SNAP_001", dec_records, {"program_id": "P001_TEST"})
        self.assertEqual(len(snap_hash), 64)

        # Mine patterns
        patterns = self.memory.mine_patterns(dec_records, reg_records)
        self.assertTrue(len(patterns) >= 1)
        collision = [p for p in patterns if p["pattern_type"] == "DECISION_REGRET_COLLISION"]
        self.assertEqual(len(collision), 1)

        # Synthesize gap hypotheses (deterministic, no LLM)
        hypotheses = self.memory.generate_gap_hypotheses(patterns)
        self.assertTrue(len(hypotheses) >= 1)
        self.assertTrue(len(hypotheses[0]["hypothesis_hash"]) == 64)


class TestAdvancedReplayAndWhatIf(unittest.TestCase):
    """F3: Batch Replay Engine & What-If Parameter Sweeps Tests."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_batch.db")
        self.store = ExperienceStore(self.db_path)
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
        gc.collect()
        _cleanup_db(self.db_path)
        try:
            os.rmdir(self.tmpdir)
        except Exception:
            pass

    def test_batch_replay_engine(self):
        self.store.append(StreamType.DECISION_MEMORY, {"val": 10}, self.prov, 0)
        self.store.append(StreamType.REGRET_MEMORY, {"val": 20}, self.prov, 0)

        batch_engine = BatchReplayEngine()

        def reducer(state, rec):
            import json
            payload = json.loads(rec.data_bytes.decode("utf-8"))
            state["sum"] = state.get("sum", 0) + int(payload.get("val", 0))
            return state

        res = batch_engine.replay_batch(
            self.store,
            [StreamType.DECISION_MEMORY, StreamType.REGRET_MEMORY],
            {StreamType.DECISION_MEMORY: {"sum": 0}, StreamType.REGRET_MEMORY: {"sum": 0}},
            reducer,
        )
        self.assertEqual(res["decision_memory"]["sum"], 10)
        self.assertEqual(res["regret_memory"]["sum"], 20)

    def test_whatif_sensitivity_engine_parameter_sweep(self):
        self.store.append(StreamType.DECISION_MEMORY, {"val": 100}, self.prov, 0)

        sensitivity_engine = WhatIfSensitivityEngine()
        log_path = os.path.join(self.tmpdir, "audit_sweep.jsonl")
        logger = AuditLogger(log_path)

        def reducer(state, rec):
            import json
            payload = json.loads(rec.data_bytes.decode("utf-8"))
            state["value"] = payload.get("val", 0)
            return state

        variations = [
            {"spread_mult": 1.0, "risk_pct": 0.01},
            {"spread_mult": 1.5, "risk_pct": 0.02},
            {"spread_mult": 2.0, "risk_pct": 0.05},
        ]

        sweep = sensitivity_engine.run_parameter_sweep(
            store=self.store,
            stream_type=StreamType.DECISION_MEMORY,
            initial_state={"value": 0},
            reducer_func=reducer,
            parameter_variations=variations,
            audit_logger=logger,
        )

        self.assertEqual(len(sweep), 3)
        self.assertTrue(all("result_hash" in r for r in sweep))
        self.assertTrue(os.path.exists(log_path))


if __name__ == "__main__":
    unittest.main()
