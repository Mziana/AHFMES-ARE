"""
Tests for AHFMES ARE-2 Slice-2 Part E: Residual Integration
Covers:
- ACC-10: Residual integration (IC-5, RES-03, RES-01)
- ACC-19: Migration script test (re-derive chain deterministic, no data loss)
- ACC-20: OS-level hardening & keeper process isolation
"""

import gc
import os
import sqlite3
import tempfile
import time
import unittest

from are.storage import (
    CapabilityToken,
    Edge1Error,
    Edge1Manager,
    EventStore,
    KeeperProcessExecutor,
    RollbackCauseRecord,
    enforce_db_permissions,
    issue_capability_token,
    migrate_event_store_var_ref,
    open_store,
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


class TestRollbackCauseObservation(unittest.TestCase):
    """E1 / IC-5: ROLLBACK_CAUSE_OBSERVATION Table, CAS, Append-only, and SoD Tests."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_rollback.db")
        self.store, self.edge1 = open_store(self.db_path)

    def tearDown(self):
        self.edge1.close()
        self.store.close()
        gc.collect()
        _cleanup_db(self.db_path)
        try:
            os.rmdir(self.tmpdir)
        except Exception:
            pass

    def test_append_and_get_rollback_cause(self):
        rec = RollbackCauseRecord(
            rollback_cause_id="RC_001",
            observation_id="OBS_999",
            source_universe="UNIV_GOLD_M1",
            policy_root_ref="ROOT_POL_123",
            timestamp=1724796000.0,
            severity="CRITICAL",
            var_ref="VAR_REF_001",
        )
        saved = self.edge1.append_rollback_cause(rec)
        self.assertEqual(saved.rollback_cause_id, "RC_001")

        fetched = self.edge1.get_rollback_cause("RC_001")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.observation_id, "OBS_999")
        self.assertEqual(fetched.source_universe, "UNIV_GOLD_M1")
        self.assertEqual(fetched.severity, "CRITICAL")
        self.assertEqual(fetched.var_ref, "VAR_REF_001")

    def test_rollback_cause_append_only_triggers(self):
        rec = RollbackCauseRecord(
            rollback_cause_id="RC_002",
            observation_id="OBS_100",
            source_universe="UNIV_GOLD_M1",
            policy_root_ref="ROOT_POL_123",
            timestamp=1724796000.0,
            severity="HIGH",
        )
        self.edge1.append_rollback_cause(rec)

        conn = sqlite3.connect(self.db_path)
        # Attempt update -> trigger raises ABORT
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("UPDATE rollback_cause_observations SET severity='LOW' WHERE rollback_cause_id='RC_002'")

        # Attempt delete -> trigger raises ABORT
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("DELETE FROM rollback_cause_observations WHERE rollback_cause_id='RC_002'")

        # Attempt replace duplicate -> trigger raises ABORT
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO rollback_cause_observations VALUES ('RC_002', 'OBS_101', 'UNIV_GOLD_M1', 'ROOT_POL_123', 100.0, 'LOW', NULL)"
            )
        conn.close()

    def test_g16_g17_sod_enforcement(self):
        rec = RollbackCauseRecord(
            rollback_cause_id="RC_003",
            observation_id="OBS_102",
            source_universe="UNIV_GOLD_M1",
            policy_root_ref="ROOT_POL_123",
            timestamp=1724796000.0,
            severity="CRITICAL",
        )
        # G16: Critic cannot rescue
        with self.assertRaises(Edge1Error) as ctx1:
            self.edge1.append_rollback_cause(rec, role="CRITIC_RESCUE")
        self.assertIn("G16", str(ctx1.exception))

        # G17: Research cannot self-validate
        with self.assertRaises(Edge1Error) as ctx2:
            self.edge1.append_rollback_cause(rec, role="RESEARCH_SELF_VALIDATE")
        self.assertIn("G17", str(ctx2.exception))


class TestVarRefEventHashMigration(unittest.TestCase):
    """E2 / RES-03: var_ref in Event Hash & Migration Tests (ACC-19)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_varref.db")
        self.store = EventStore(self.db_path)

    def tearDown(self):
        self.store.close()
        gc.collect()
        _cleanup_db(self.db_path)
        try:
            os.rmdir(self.tmpdir)
        except Exception:
            pass

    def test_var_ref_included_in_event_hash(self):
        rec1 = self.store.append_event("stream_vr", b"data_1", 0, "0" * 64, var_ref="VAR_A")
        self.assertTrue(self.store.verify_chain("stream_vr"))
        self.assertEqual(rec1.var_ref, "VAR_A")

        rec2 = self.store.append_event("stream_vr", b"data_2", 1, rec1.event_hash, var_ref="VAR_B")
        self.assertTrue(self.store.verify_chain("stream_vr"))
        self.assertEqual(rec2.var_ref, "VAR_B")

    def test_migration_script_recomputes_chain_deterministically(self):
        rec1 = self.store.append_event("stream_mig", b"mig_1", 0, "0" * 64, var_ref="VAR_X")
        rec2 = self.store.append_event("stream_mig", b"mig_2", 1, rec1.event_hash, var_ref="VAR_Y")
        self.store.close()

        count = migrate_event_store_var_ref(self.db_path)
        self.assertEqual(count, 2)

        store_new = EventStore(self.db_path)
        self.assertTrue(store_new.verify_chain("stream_mig"))
        ev1 = store_new.get_event("stream_mig", 1)
        ev2 = store_new.get_event("stream_mig", 2)
        self.assertEqual(ev1.var_ref, "VAR_X")
        self.assertEqual(ev2.var_ref, "VAR_Y")
        store_new.close()


class TestOSHardeningAndKeeperProcess(unittest.TestCase):
    """E3 / RES-01: OS-Level Hardening & Keeper Process Isolation (ACC-20)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_hardening.db")
        self.store = EventStore(self.db_path)
        self.store.close()

    def tearDown(self):
        gc.collect()
        _cleanup_db(self.db_path)
        try:
            os.rmdir(self.tmpdir)
        except Exception:
            pass

    def test_enforce_db_permissions(self):
        res = enforce_db_permissions(self.db_path)
        self.assertTrue(res)

    def test_keeper_process_isolation_and_tokens(self):
        executor = KeeperProcessExecutor(self.db_path)
        token = issue_capability_token("TOK_001", "GOVERNOR", "STATE_MUTATION", ttl_sec=60.0)
        self.assertTrue(token.is_valid("GOVERNOR", time.time()))

        def op(conn):
            cur = conn.cursor()
            cur.execute("SELECT 1")
            return cur.fetchone()[0]

        res = executor.execute_with_token(token, "GOVERNOR", op)
        self.assertEqual(res, 1)

        # Expired token
        expired_token = issue_capability_token("TOK_002", "GOVERNOR", "STATE_MUTATION", ttl_sec=-10.0)
        with self.assertRaises(Edge1Error):
            executor.execute_with_token(expired_token, "GOVERNOR", op)

        # Wrong role token
        with self.assertRaises(Edge1Error):
            executor.execute_with_token(token, "CRITIC", op)


if __name__ == "__main__":
    unittest.main()
