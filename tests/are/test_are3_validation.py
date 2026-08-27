"""
Unit Tests for AHFMES ARE-3 Validation Service (ACC-303, ACC-304)
"""

import os
import tempfile
import unittest

from are.evidence import EvidenceLedger
from are.storage import EventStore
from are.validation import ValidationReport, ValidationService


class TestValidationService(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "evidence_test.db")
        self.event_store = EventStore(self.db_path)
        self.evidence_ledger = EvidenceLedger(self.db_path)
        self.service = ValidationService(self.evidence_ledger, self.event_store)

    def tearDown(self):
        self.event_store.close()
        self.evidence_ledger.close()
        self.tmp_dir.cleanup()

    def test_information_time_violation_raises(self):
        dataset = [
            {"timestamp": 100.0, "score": 0.8},
            {"timestamp": 105.0, "score": 0.75},
            {"timestamp": 120.0, "score": 0.9},  # Future point relative to as_of_ts=110.0
        ]

        with self.assertRaises(ValueError) as ctx:
            self.service.validate_candidate(
                candidate_id="CAND_001",
                holdout_token="HOLDOUT_TOK_1",
                as_of_ts=110.0,
                dataset=dataset,
            )
        self.assertIn("Information-Time violation", str(ctx.exception))

    def test_valid_out_of_sample_validation_and_exposure(self):
        dataset = [
            {"timestamp": 100.0, "score": 0.8},
            {"timestamp": 105.0, "score": 0.85},
            {"timestamp": 108.0, "score": 0.9},
        ]

        report = self.service.validate_candidate(
            candidate_id="CAND_001",
            holdout_token="HOLDOUT_TOK_1",
            as_of_ts=110.0,
            dataset=dataset,
            performance_threshold=0.7,
        )

        self.assertIsInstance(report, ValidationReport)
        self.assertEqual(report.status, "VALIDATED")
        self.assertEqual(report.sample_count, 3)
        self.assertGreater(report.performance_metric, 0.7)
        self.assertIsNotNone(report.report_hash)

        # Verify exposure was recorded in Evidence Ledger
        conn = self.event_store._get_conn()
        cur = conn.execute("SELECT exposure_event_id, research_program_id FROM evidence_exposures")
        rows = cur.fetchall()
        self.assertGreaterEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "ARE3_RESEARCH")


if __name__ == "__main__":
    unittest.main()
