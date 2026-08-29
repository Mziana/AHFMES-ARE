"""
Vault Disaster Recovery & Replicator Invariant Tests (DELEGASI_035B)
100% Python Standard Library.
"""

import json
import os
import tempfile
import time
import unittest

from are.storage import EventStore, VaultReplicator


class TestVaultReplicationInvariants(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.primary_dir = os.path.join(self.tmp_dir.name, "primary")
        self.backup_dir = os.path.join(self.tmp_dir.name, "backup")
        os.makedirs(self.primary_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

        self.db_path = os.path.join(self.primary_dir, "vault.db")
        self.witness_path = f"{self.db_path}.witness.jsonl"

        # Create a sample store with an initial event
        store = EventStore(self.db_path)
        store.append_event("test_stream", b"payload_initial", 0, "0" * 64, "ref_init")
        store.close()

        self.replicator = VaultReplicator(
            primary_db_path=self.db_path,
            witness_jsonl_path=self.witness_path,
            backup_dirs=[self.backup_dir],
            retention_count=3,
            backup_interval_seconds=0.05,
        )

    def tearDown(self):
        self.replicator.stop_scheduled_replication()
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def test_replicate_creates_manifest_with_hashes(self):
        """
        Invariant 1: Replicate creates a backup and writes manifest with SHA-256 hashes.
        """
        manifest_path = self.replicator.replicate()
        self.assertIsNotNone(manifest_path)
        self.assertTrue(os.path.exists(manifest_path))

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertIn("db_hash", manifest)
        self.assertIn("witness_hash", manifest)
        self.assertEqual(len(manifest["db_hash"]), 64)
        self.assertEqual(len(manifest["witness_hash"]), 64)
        self.assertIn("timestamp", manifest)

    def test_manifest_contains_chain_hash(self):
        """
        Invariant 2: Sequential backups link cryptographic previous_manifest_hash in a hash chain.
        """
        m1 = self.replicator.replicate()
        time.sleep(0.01)
        m2 = self.replicator.replicate()

        with open(m1, "r", encoding="utf-8") as f1:
            man1 = json.load(f1)
        with open(m2, "r", encoding="utf-8") as f2:
            man2 = json.load(f2)

        self.assertEqual(man1["previous_manifest_hash"], "0" * 64)
        self.assertNotEqual(man2["previous_manifest_hash"], "0" * 64)
        self.assertEqual(len(man2["previous_manifest_hash"]), 64)

    def test_verify_backup_integrity_true_for_fresh_backup(self):
        """
        Invariant 3: Verification succeeds for untampered fresh backup.
        """
        manifest_path = self.replicator.replicate()
        self.assertTrue(self.replicator.verify_backup_integrity(manifest_path))

    def test_verify_backup_integrity_false_for_tampered_backup(self):
        """
        Invariant 4: Verification fails immediately if backup SQLite or witness is tampered with.
        """
        manifest_path = self.replicator.replicate()
        with open(manifest_path, "r", encoding="utf-8") as f:
            man = json.load(f)

        tampered_db = os.path.join(self.backup_dir, man["db_file"])
        # Tamper backup file directly
        with open(tampered_db, "ab") as f:
            f.write(b"CORRUPT_BYTES_XYZ")

        self.assertFalse(self.replicator.verify_backup_integrity(manifest_path))

    def test_retention_deletes_old_backups(self):
        """
        Invariant 5: Retention policy enforces maximum retention_count (3) and prunes older archives.
        """
        for _ in range(5):
            time.sleep(0.01)
            self.replicator.replicate()

        manifests = [f for f in os.listdir(self.backup_dir) if f.startswith("manifest_")]
        self.assertEqual(len(manifests), 3, f"Expected 3 retained manifests, found {len(manifests)}")

    def test_restore_from_backup_success(self):
        """
        Invariant 6: Restore successfully reconstructs valid SQLite database and witness JSONL.
        """
        manifest_path = self.replicator.replicate()
        restore_dir = os.path.join(self.tmp_dir.name, "restored")

        ok = self.replicator.restore_from_backup(manifest_path, restore_dir)
        self.assertTrue(ok)

        restored_db = os.path.join(restore_dir, os.path.basename(self.db_path))
        restored_wit = os.path.join(restore_dir, os.path.basename(self.witness_path))

        self.assertTrue(os.path.exists(restored_db))
        self.assertTrue(os.path.exists(restored_wit))

        # Check restored store is valid and readable
        restored_store = EventStore(restored_db)
        ev = restored_store.get_event("test_stream", 1)
        self.assertIsNotNone(ev)
        self.assertEqual(ev.event_data, b"payload_initial")
        restored_store.close()

    def test_restore_from_backup_fail_on_hash_mismatch(self):
        """
        Invariant 7: Restore fails closed without writing to target dir if backup is tampered with.
        """
        manifest_path = self.replicator.replicate()
        with open(manifest_path, "r", encoding="utf-8") as f:
            man = json.load(f)

        tampered_wit = os.path.join(self.backup_dir, man["witness_file"])
        with open(tampered_wit, "ab") as f:
            f.write(b"TAMPERED_WITNESS_LINE\n")

        restore_dir = os.path.join(self.tmp_dir.name, "restored_fail")
        ok = self.replicator.restore_from_backup(manifest_path, restore_dir)
        self.assertFalse(ok, "Restore must abort on hash mismatch (Fail-Closed)")


if __name__ == "__main__":
    unittest.main()