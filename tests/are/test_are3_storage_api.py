"""
Unit Tests for AHFMES ARE-3 EventStore Encapsulated API (ACC-317, DEBT-03)
"""

import glob
import os
import tempfile
import unittest

from are.storage import EventStore


class TestEventStoreEncapsulatedAPI(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "encap_test.db")
        self.store = EventStore(self.db_path)

    def tearDown(self):
        self.store.close()
        self.tmp_dir.cleanup()

    def test_table_exists_and_count_events(self):
        self.assertTrue(self.store.table_exists("events"))
        self.assertTrue(self.store.table_exists("stream_heads"))
        self.assertTrue(self.store.table_exists("nonce_ledger"))
        self.assertFalse(self.store.table_exists("non_existent_table_xyz"))

        self.assertEqual(self.store.count_events("test_stream"), 0)

        # Append event
        self.store.append_event("test_stream", b"payload_1", 0, "0" * 64)
        self.assertEqual(self.store.count_events("test_stream"), 1)

    def test_fetch_one_and_fetch_all(self):
        self.store.append_event("stream_a", b"data_a1", 0, "0" * 64)
        self.store.append_event("stream_a", b"data_a2", 1, self.store.get_head("stream_a")[1])

        row = self.store.fetch_one("SELECT revision, event_data FROM events WHERE stream_id=? AND revision=?", ("stream_a", 1))
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 1)
        self.assertEqual(row[1], b"data_a1")

        rows = self.store.fetch_all("SELECT revision, event_data FROM events WHERE stream_id=? ORDER BY revision ASC", ("stream_a",))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], 1)
        self.assertEqual(rows[1][0], 2)

    def test_zero_get_conn_outside_storage_py(self):
        are_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "are"))
        py_files = glob.glob(os.path.join(are_dir, "*.py"))

        for fpath in py_files:
            fname = os.path.basename(fpath)
            if fname == "storage.py":
                continue
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertNotIn(
                "_get_conn",
                content,
                f"Found illegal private attribute access '_get_conn' in {fname} (DEBT-03 / ACC-317 violation)"
            )


if __name__ == "__main__":
    unittest.main()
