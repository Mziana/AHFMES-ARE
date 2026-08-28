"""
The Windows Vault Protocol Invariant Tests (DELEGASI_029, ACC-1001..ACC-1005)
True Immutable Storage with Dual-Layer JSONL Witness and Self-Healing Cache.
"""

import json
import os
import sqlite3
import tempfile
import unittest

from are.evidence import EvidenceLedger
from are.storage import CriticalTamperingError, EventStore


class TestVaultInvariants(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "vault_test.db")
        self.witness_path = f"{self.db_path}.witness.jsonl"

    def tearDown(self):
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def test_sqlite_tampering_auto_healed_from_witness(self):
        """
        Invariant 1: If SQLite cache is tampered / modified behind EventStore's back,
        verify_and_heal() automatically detects the mismatch and reconstructs SQLite from JSONL Witness.
        """
        # 1. Initialize store and commit 5 events
        store = EventStore(self.db_path)
        original_data = []
        for i in range(1, 6):
            data = f"event_payload_content_{i}".encode("utf-8")
            original_data.append(data)
            head = store.get_head("stream_test")
            prev_rev = head[0] if head else 0
            prev_hash = head[1] if head else "0" * 64
            store.append_event(
                stream_id="stream_test",
                event_data=data,
                expected_revision=prev_rev,
                prev_event_hash=prev_hash,
                var_ref=f"ref_{i}",
            )
        store.close()

        # 2. Tamper SQLite directly via raw connection (bypassing EventStore security)
        raw_conn = sqlite3.connect(self.db_path)
        with raw_conn:
            # Drop update trigger directly to simulate malicious out-of-band manipulation
            raw_conn.execute("DROP TRIGGER IF EXISTS events_no_update;")
            raw_conn.execute("UPDATE events SET event_data = X'deadbeef' WHERE revision = 3;")
        raw_conn.close()

        # Verify tampering is present in raw db
        raw_conn2 = sqlite3.connect(self.db_path)
        row = raw_conn2.execute("SELECT event_data FROM events WHERE revision = 3;").fetchone()
        self.assertEqual(row[0], b"\xde\xad\xbe\xef")
        raw_conn2.close()

        # 3. Boot new EventStore -> Must detect mismatch and auto-heal from JSONL Witness
        healed_store = EventStore(self.db_path)

        # 4. Assert that event 3 is restored to original payload, not deadbeef
        event_3 = healed_store.get_event("stream_test", 3)
        self.assertIsNotNone(event_3)
        self.assertEqual(event_3.event_data, original_data[2])
        self.assertNotEqual(event_3.event_data, b"\xde\xad\xbe\xef")

        # 5. Assert all 5 events are intact and verification passes
        ok, status = healed_store.verify_full_chain_integrity()
        self.assertTrue(ok)
        self.assertEqual(status, "OK")
        healed_store.close()

    def test_jsonl_witness_tampering_fails_closed(self):
        """
        Invariant 2: If the Source-of-Truth (JSONL Witness) is tampered,
        EventStore / EvidenceLedger MUST raise CriticalTamperingError and refuse to boot (Fail-Closed).
        """
        # 1. Initialize store and write 5 events
        store = EventStore(self.db_path)
        for i in range(1, 6):
            data = f"critical_event_{i}".encode("utf-8")
            head = store.get_head("stream_critical")
            prev_rev = head[0] if head else 0
            prev_hash = head[1] if head else "0" * 64
            store.append_event(
                stream_id="stream_critical",
                event_data=data,
                expected_revision=prev_rev,
                prev_event_hash=prev_hash,
                var_ref=f"ref_{i}",
            )
        store.close()

        # 2. Tamper JSONL witness file (corrupt hash on line 3)
        with open(self.witness_path, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]

        self.assertEqual(len(lines), 5)
        rec_3 = json.loads(lines[2])
        # Tamper event_hash
        rec_3["event_hash"] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        lines[2] = json.dumps(rec_3)

        with open(self.witness_path, "w", encoding="utf-8") as f:
            for ln in lines:
                f.write(ln + "\n")

        # 3. Assert EventStore boot throws CriticalTamperingError
        with self.assertRaises(CriticalTamperingError):
            EventStore(self.db_path)

        # 4. Assert EvidenceLedger boot throws CriticalTamperingError
        with self.assertRaises(CriticalTamperingError):
            EvidenceLedger(self.db_path)

    def test_append_only_no_delete_no_update_interface(self):
        """
        Invariant 3: EventStore class MUST NOT expose public update_event, delete_event, or truncate methods.
        """
        forbidden_methods = ["update_event", "delete_event", "truncate", "drop_table", "clear_all"]
        for method in forbidden_methods:
            self.assertFalse(
                hasattr(EventStore, method),
                f"Security Vulnerability: EventStore exposes forbidden mutable method '{method}'",
            )


if __name__ == "__main__":
    unittest.main()