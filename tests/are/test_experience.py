"""
Unit and Integration Tests for AHFMES ARE-2 Experience Store & Anomaly Detection (Slice-1 Part A)

Covers:
- ACC-1: Full A1-A3 test suite including crash-matrix invariant test and deterministic replay test.
"""

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from are.experience import (
    AnomalyDetector,
    AnomalyResult,
    CounterfactualQuality,
    ExperienceRecord,
    ExperienceStore,
    ExperienceStoreError,
    GateMetrics,
    ProvenancedRecord,
    QualityGate,
    QualityGateError,
    RegimeState,
    StreamType,
)


class TestQualityGate(unittest.TestCase):
    """A3: Observability & Data Quality Gate Tests."""

    def setUp(self):
        self.gate = QualityGate(max_latency_ms=100.0, min_completeness_rate=0.999)
        self.valid_provenance = {
            "source_id": "src_001",
            "timestamp": 1724796000,
            "session_id": "sess_abc",
            "environment": "test_env",
            "collector_version": "1.0.0",
            "input_hash": "hash_123",
            "schema_version": "v1",
            "trace_id": "tr_999",
        }

    def test_valid_provenance_passes(self):
        self.gate.validate_provenance(self.valid_provenance)

    def test_missing_provenance_field_fails(self):
        invalid_prov = dict(self.valid_provenance)
        del invalid_prov["trace_id"]
        with self.assertRaises(QualityGateError) as ctx:
            self.gate.validate_provenance(invalid_prov)
        self.assertIn("trace_id", str(ctx.exception))

    def test_latency_gate_rejection(self):
        rec = ProvenancedRecord(provenance=self.valid_provenance, payload={"data": 123})
        passed, reason = self.gate.validate_and_ingest(rec, latency_ms=150.0)
        self.assertFalse(passed)
        self.assertIn("LATENCY_FAIL", reason)
        self.assertEqual(len(self.gate.get_quarantine()), 1)

    def test_valid_ingestion(self):
        rec = ProvenancedRecord(provenance=self.valid_provenance, payload={"data": 123})
        passed, reason = self.gate.validate_and_ingest(rec, latency_ms=15.0)
        self.assertTrue(passed)
        self.assertEqual(reason, "PASSED")
        self.assertEqual(len(self.gate.get_quarantine()), 0)


class TestAnomalyDetector(unittest.TestCase):
    """A2: Deterministic Anomaly Detection Tests."""

    def setUp(self):
        self.detector = AnomalyDetector(seed=20260827)

    def test_config_hash_deterministic(self):
        hash1 = self.detector.config_hash
        detector2 = AnomalyDetector(seed=20260827)
        self.assertEqual(hash1, detector2.config_hash)

    def test_spread_hostility_metric(self):
        # f(spread, volatility, volume) = (spread * volatility * 100.0) / max(volume, 1.0)
        # (1.5 * 0.2 * 100.0) / 10.0 = 30.0 / 10.0 = 3.0
        val = self.detector.compute_spread_hostility(spread=1.5, volatility=0.2, volume=10.0)
        self.assertEqual(val, 3.0)

    def test_spread_hostility_negative_input_raises(self):
        with self.assertRaises(Exception):
            self.detector.compute_spread_hostility(spread=-1.0, volatility=0.1, volume=10.0)

    def test_detect_regime_shift_stable(self):
        prices = [100.0, 100.1, 100.05, 100.15, 100.1]
        regime = self.detector.detect_regime_shift(prices)
        self.assertIn(regime, (RegimeState.STABLE, RegimeState.TRANSITIONING))

    def test_detect_regime_shift_high_volatility(self):
        prices = [100.0, 110.0, 90.0, 120.0, 80.0, 130.0]
        regime = self.detector.detect_regime_shift(prices)
        self.assertEqual(regime, RegimeState.HIGH_VOLATILITY)

    def test_classify_counterfactual_quality(self):
        self.assertEqual(
            self.detector.classify_counterfactual_quality("REGIME_SHIFT", 3.0),
            CounterfactualQuality.CF_HIGH,
        )
        self.assertEqual(
            self.detector.classify_counterfactual_quality("SPREAD_HOSTILITY", 1.5),
            CounterfactualQuality.CF_MED,
        )
        self.assertEqual(
            self.detector.classify_counterfactual_quality("LIQUIDITY_DROP", 0.5),
            CounterfactualQuality.CF_LOW,
        )

    def test_analyze_full_pipeline(self):
        prices = [100.0, 105.0, 95.0, 110.0, 90.0]
        res = self.detector.analyze(
            anomaly_type="REGIME_SHIFT",
            price_series=prices,
            spread=2.0,
            volatility=0.5,
            volume=5.0,
        )
        self.assertIsInstance(res, AnomalyResult)
        self.assertIsNotNone(res.artifact_hash)
        self.assertGreater(res.severity, 0.0)


class TestExperienceStore(unittest.TestCase):
    """A1: Experience Store & Replay Engine Tests."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "experience.db")
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

    def test_append_and_verify_chain(self):
        rec1 = self.store.append(
            stream_type=StreamType.DECISION_MEMORY,
            payload={"action": "buy", "confidence": 0.95},
            provenance=self.prov,
            expected_revision=0,
        )
        self.assertEqual(rec1.revision, 1)

        rec2 = self.store.append(
            stream_type=StreamType.DECISION_MEMORY,
            payload={"action": "sell", "confidence": 0.88},
            provenance=self.prov,
            expected_revision=1,
        )
        self.assertEqual(rec2.revision, 2)

        self.assertTrue(self.store.verify_chain(StreamType.DECISION_MEMORY))

    def test_cas_mismatch_raises(self):
        self.store.append(
            stream_type=StreamType.REGRET_MEMORY,
            payload={"reason": "missed_entry"},
            provenance=self.prov,
            expected_revision=0,
        )
        # Expected revision 0 again should fail because current revision is 1
        with self.assertRaises(ExperienceStoreError) as ctx:
            self.store.append(
                stream_type=StreamType.REGRET_MEMORY,
                payload={"reason": "late_exit"},
                provenance=self.prov,
                expected_revision=0,
            )
        self.assertIn("CAS mismatch", str(ctx.exception))

    def test_deterministic_replay_engine(self):
        self.store.append(
            StreamType.DECISION_MEMORY,
            {"delta": 10},
            self.prov,
            expected_revision=0,
        )
        self.store.append(
            StreamType.DECISION_MEMORY,
            {"delta": -3},
            self.prov,
            expected_revision=1,
        )
        self.store.append(
            StreamType.DECISION_MEMORY,
            {"delta": 5},
            self.prov,
            expected_revision=2,
        )

        def reducer(state, record):
            data = json.loads(record.data_bytes.decode("utf-8"))
            state["value"] += data["delta"]
            return state

        final_state = self.store.replay(
            stream_type=StreamType.DECISION_MEMORY,
            initial_state={"value": 0},
            reducer_func=reducer,
        )
        self.assertEqual(final_state["value"], 12)

    def test_what_if_fork_engine(self):
        self.store.append(
            StreamType.DECISION_MEMORY,
            {"delta": 10},
            self.prov,
            expected_revision=0,
        )

        def reducer(state, record):
            data = json.loads(record.data_bytes.decode("utf-8"))
            state["value"] += data["delta"]
            return state

        # Original state replay
        base_state = self.store.replay(StreamType.DECISION_MEMORY, {"value": 0}, reducer)
        self.assertEqual(base_state["value"], 10)

        # What-if simulation with counterfactual events
        counterfactuals = [{"delta": 100}, {"delta": -20}]
        fork_res = self.store.fork_what_if(
            StreamType.DECISION_MEMORY,
            {"value": 0},
            reducer,
            counterfactuals,
        )
        self.assertEqual(fork_res.final_state["value"], 90)

        # Confirm original database remains completely unchanged (value is still 10)
        recheck_base = self.store.replay(StreamType.DECISION_MEMORY, {"value": 0}, reducer)
        self.assertEqual(recheck_base["value"], 10)

    def test_crash_matrix_invariant(self):
        """
        Simulate crash in intermediate state and confirm database state
        is always reconstructed cleanly from committed rows.
        """
        self.store.append(StreamType.ANOMALY_DETECTION, {"event": "start"}, self.prov, 0)

        # Direct connection simulating aborted transaction
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("BEGIN TRANSACTION")
            conn.execute(
                "INSERT INTO experience_events (stream_id, revision, entry_hash, previous_hash, data_bytes, provenance_json) VALUES (?, ?, ?, ?, ?, ?)",
                ("anomaly_detection", 99, "bad_hash", "prev", b"data", "{}"),
            )
            # Simulate crash before commit
            conn.close()
        except Exception:
            pass

        # Verify store state is completely clean
        recs = self.store.get_records(StreamType.ANOMALY_DETECTION)
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0].revision, 1)
        self.assertTrue(self.store.verify_chain(StreamType.ANOMALY_DETECTION))


if __name__ == "__main__":
    unittest.main()
