"""
Unit Tests for AHFMES P001 Market Data Ingestion Pipeline (ACC-513)
"""

import os
import tempfile
import unittest

from are.evidence import EvidenceLedger
from are.experience_store import ExperienceStore, StreamType
from are.ingestion import MarketIngestionService, MarketTick
from are.storage import EventStore


class TestP001Ingestion(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "ingest_test.db")
        self.store = EventStore(self.db_path)
        self.ledger = EvidenceLedger(self.db_path)
        self.exp_store = ExperienceStore(self.db_path)
        self.service = MarketIngestionService(self.ledger, self.exp_store)

    def tearDown(self):
        self.store.close()
        self.ledger.close()
        self.exp_store.close()
        self.tmp_dir.cleanup()

    def test_ingest_ticks_pipeline(self):
        ticks = [
            {
                "symbol": "BTCUSDT",
                "timestamp": 1728000000.0 + i,
                "price": 60000.0 + i,
                "volume": 1.5,
                "side": "BUY",
                "bid": 59999.0 + i,
                "ask": 60001.0 + i,
                "bid_size": 2.0,
                "ask_size": 1.8,
            }
            for i in range(5)
        ]

        snap = self.service.ingest_ticks("BTCUSDT", ticks, "SNAP_TEST_001")
        self.assertIsNotNone(snap)
        self.assertEqual(snap.evidence_snapshot_id, "SNAP_TEST_001")
        self.assertTrue(self.store.verify_chain("evidence_snapshot:SNAP_TEST_001"))

        # Verify experience records ingested
        records = self.exp_store.get_records(StreamType.DECISION_MEMORY)
        self.assertEqual(len(records), 5)
        self.assertEqual(records[0].provenance["source_id"], "FEED_BTCUSDT")

    def test_ingest_from_csv(self):
        csv_data = """timestamp,price,volume,side,bid,ask,bid_size,ask_size
1728000100.0,61000.0,0.5,BUY,60999.0,61001.0,1.2,0.8
1728000101.0,61005.0,0.8,SELL,61004.0,61006.0,1.5,1.1
"""
        snap = self.service.ingest_from_csv("BTCUSDT", csv_data, "SNAP_CSV_001")
        self.assertIsNotNone(snap)
        self.assertEqual(snap.evidence_snapshot_id, "SNAP_CSV_001")

        records = self.exp_store.get_records(StreamType.DECISION_MEMORY)
        self.assertEqual(len(records), 2)


if __name__ == "__main__":
    unittest.main()
