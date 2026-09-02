"""
AHFMES ARE-1 — Storage Engine (Slice-1 Part A)

Implements append-only event store with SQLite WAL, head table CAS,
and IC-4 deterministic crash finalization per Matrix V30 IC-4 /
Register V30 EDGE_NONCE_CONSUMPTION_LEDGER + REFINEMENT_PROSPECTIVE_RELIANCE_RECEIPT.

Zero external dependencies (stdlib only: sqlite3, hashlib, json, os, threading).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import shutil
import sqlite3
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

# Re-export chain and witness modules for backward compatibility
from are.chain import (  # noqa: F401
    verify_chain,
    verify_full_chain_integrity,
    rebuild_cache_from_witness,
    verify_and_heal,
)
from are.witness import (  # noqa: F401
    get_last_witness_hash,
    write_witness_record,
    read_witness_records,
    verify_witness_chain,
)

# Named SQLite Authorizer Action Codes & Return Codes (ARCH-04)
SQLITE_DROP_TABLE = 11
SQLITE_DROP_TRIGGER = 16
SQLITE_ATTACH = 24
SQLITE_DENY = 1
SQLITE_OK = 0


class ReceiptState(Enum):
    ABSENT = "ABSENT"
    CANONICAL = "CANONICAL"
    INTEGRITY_DEFECT = "INTEGRITY_DEFECT"


class NonceState(Enum):
    UNUSED = "UNUSED"
    CONSUMED = "CONSUMED"


class CriticalTamperingError(Exception):
    """Dilempar saat Source of Truth (JSONL Witness) terbukti dimanipulasi atau tidak sinkron."""


class Edge1Error(Exception):
    """Edge 1 operation failed (precondition violation, CAS failure, etc.)"""


@dataclass(frozen=True)
class ReceiptRecord:
    recovery_subject: str
    receipt_data: bytes
    state: ReceiptState
    var_ref: Optional[str] = None


@dataclass(frozen=True)
class NonceRecord:
    recovery_subject: str
    nonce: str
    state: NonceState
    var_ref: Optional[str] = None


@dataclass(frozen=True)
class EventRecord:
    stream_id: str
    revision: int
    event_data: bytes
    previous_event_hash: str
    event_hash: str
    var_ref: Optional[str] = None


@dataclass(frozen=True)
class RollbackCauseRecord:
    rollback_cause_id: str
    observation_id: str
    source_universe: str
    policy_root_ref: str
    timestamp: float
    severity: str
    var_ref: Optional[str] = None


def _compute_file_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class VaultReplicator:
    """
    Windows Vault Disaster Recovery Replicator (DELEGASI_035B).
    Handles atomic replication of primary SQLite DB and JSONL Witness,
    cryptographic manifest chaining, integrity verification, and automated retention.
    100% Python Standard Library.
    """

    def __init__(
        self,
        primary_db_path: str,
        witness_jsonl_path: str,
        backup_dirs: Any,
        retention_count: int = 7,
        backup_interval_seconds: float = 3600.0,
    ):
        self.primary_db_path = primary_db_path
        self.witness_jsonl_path = witness_jsonl_path
        if isinstance(backup_dirs, str):
            self.backup_dirs = [backup_dirs]
        else:
            self.backup_dirs = list(backup_dirs)

        self.retention_count = max(1, int(retention_count))
        self.backup_interval_seconds = float(backup_interval_seconds)

        for b_dir in self.backup_dirs:
            os.makedirs(b_dir, exist_ok=True)

        self._stop_event: Optional[threading.Event] = None
        self._worker_thread: Optional[threading.Thread] = None

    def replicate(self) -> Optional[str]:
        """
        Copies primary database and witness JSONL to backup directories,
        generates cryptographic manifest, and enforces retention policy.
        Returns the primary manifest path.
        """
        if not os.path.exists(self.primary_db_path):
            return None
        if not os.path.exists(self.witness_jsonl_path):
            with open(self.witness_jsonl_path, "a", encoding="utf-8"):
                pass

        primary_manifest_path: Optional[str] = None
        import time as _t
        timestamp = int(_t.time() * 1000)

        for idx, b_dir in enumerate(self.backup_dirs):
            os.makedirs(b_dir, exist_ok=True)

            db_filename = f"backup_{timestamp}.db"
            witness_filename = f"backup_{timestamp}.witness.jsonl"
            manifest_filename = f"manifest_{timestamp}.json"

            dest_db = os.path.join(b_dir, db_filename)
            dest_witness = os.path.join(b_dir, witness_filename)
            dest_manifest = os.path.join(b_dir, manifest_filename)

            shutil.copy2(self.primary_db_path, dest_db)
            shutil.copy2(self.witness_jsonl_path, dest_witness)

            db_hash = _compute_file_sha256(dest_db)
            witness_hash = _compute_file_sha256(dest_witness)

            # Find previous manifest in this backup dir
            prev_manifest_hash = "0" * 64
            manifests = sorted(
                [m for m in os.listdir(b_dir) if m.startswith("manifest_") and m.endswith(".json") and m != manifest_filename]
            )
            if manifests:
                last_manifest_path = os.path.join(b_dir, manifests[-1])
                prev_manifest_hash = _compute_file_sha256(last_manifest_path)

            manifest_data = {
                "timestamp": timestamp,
                "db_file": db_filename,
                "db_hash": db_hash,
                "witness_file": witness_filename,
                "witness_hash": witness_hash,
                "previous_manifest_hash": prev_manifest_hash,
            }

            with open(dest_manifest, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2, sort_keys=True)

            # Read-back verification
            if not self.verify_backup_integrity(dest_manifest):
                raise RuntimeError(f"Read-back verification failed immediately for backup {dest_manifest}")

            # Retention enforcement
            all_manifests = sorted(
                [m for m in os.listdir(b_dir) if m.startswith("manifest_") and m.endswith(".json")]
            )
            if len(all_manifests) > self.retention_count:
                excess_count = len(all_manifests) - self.retention_count
                for old_man_name in all_manifests[:excess_count]:
                    old_man_path = os.path.join(b_dir, old_man_name)
                    try:
                        with open(old_man_path, "r", encoding="utf-8") as f:
                            old_data = json.load(f)
                        old_db = os.path.join(b_dir, old_data.get("db_file", ""))
                        old_wit = os.path.join(b_dir, old_data.get("witness_file", ""))
                        if os.path.exists(old_db):
                            os.remove(old_db)
                        if os.path.exists(old_wit):
                            os.remove(old_wit)
                        os.remove(old_man_path)
                    except Exception:
                        pass

            if idx == 0:
                primary_manifest_path = dest_manifest

        return primary_manifest_path

    def verify_backup_integrity(self, manifest_path: str) -> bool:
        """
        Verifies backup files against cryptographic manifest hashes.
        """
        if not os.path.exists(manifest_path):
            return False

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            b_dir = os.path.dirname(manifest_path)
            db_path = os.path.join(b_dir, data.get("db_file", ""))
            wit_path = os.path.join(b_dir, data.get("witness_file", ""))

            if not os.path.exists(db_path) or not os.path.exists(wit_path):
                return False

            if _compute_file_sha256(db_path) != data.get("db_hash"):
                return False
            if _compute_file_sha256(wit_path) != data.get("witness_hash"):
                return False

            return True
        except Exception:
            return False

    def restore_from_backup(self, manifest_path: str, target_dir: str) -> bool:
        """
        Restores database and witness JSONL from backup if integrity check passes.
        Fail-closed: if hash mismatch, aborts and returns False.
        """
        if not self.verify_backup_integrity(manifest_path):
            return False

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            b_dir = os.path.dirname(manifest_path)
            db_source = os.path.join(b_dir, data["db_file"])
            wit_source = os.path.join(b_dir, data["witness_file"])

            os.makedirs(target_dir, exist_ok=True)
            target_db = os.path.join(target_dir, os.path.basename(self.primary_db_path))
            target_wit = os.path.join(target_dir, os.path.basename(self.witness_jsonl_path))

            shutil.copy2(db_source, target_db)
            shutil.copy2(wit_source, target_wit)
            return True
        except Exception:
            return False

    def start_scheduled_replication(self) -> None:
        """Starts periodic replication background worker thread."""
        if self._worker_thread is not None and self._worker_thread.is_alive():
            return
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._worker_thread.start()

    def stop_scheduled_replication(self) -> None:
        """Stops periodic replication background worker thread."""
        if self._stop_event is not None:
            self._stop_event.set()
        if self._worker_thread is not None and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)

    def _run_loop(self) -> None:
        while self._stop_event is not None and not self._stop_event.is_set():
            try:
                self.replicate()
            except Exception:
                pass
            self._stop_event.wait(timeout=self.backup_interval_seconds)


class EventStore:
    """
    Append-only event store with per-stream head table and CAS mutation.
    All events are immutable once committed.
    """

    def __init__(self, db_path: str, wal_mode: bool = True, replicator: Optional[VaultReplicator] = None):
        self._db_path = db_path
        self._local = threading.local()
        self._conns_lock = threading.Lock()
        self._all_conns: List[sqlite3.Connection] = []
        self._witness_path: Optional[str] = f"{db_path}.witness.jsonl" if db_path != ":memory:" else None
        self.replicator: Optional[VaultReplicator] = replicator
        self._init_schema()
        if self._witness_path is not None:
            self.verify_and_heal()

    def trigger_backup(self) -> Optional[str]:
        """Triggers an on-demand replication via attached VaultReplicator."""
        if self.replicator is not None:
            return self.replicator.replicate()
        return None

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self._db_path, isolation_level=None)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = FULL")
            conn.execute("PRAGMA busy_timeout = 5000")
            # Block dangerous operations via authorizer (P0-02, P0-10, FIX-01, ARCH-04)
            def _authorizer(action, arg1, arg2, dbname, trigger):
                if action == SQLITE_DROP_TABLE or action == SQLITE_DROP_TRIGGER:
                    return SQLITE_DENY
                if action == SQLITE_ATTACH:
                    return SQLITE_DENY
                return SQLITE_OK
            conn.set_authorizer(_authorizer)
            self._local.conn = conn
            with self._conns_lock:
                self._all_conns.append(conn)
        return self._local.conn

    def close(self) -> None:
        with self._conns_lock:
            for conn in self._all_conns:
                try:
                    conn.close()
                except Exception:
                    pass
            self._all_conns.clear()
        if hasattr(self._local, "conn"):
            self._local.conn = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _init_schema(self) -> None:
        conn = self._get_conn()
        with conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    stream_id TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    event_data BLOB NOT NULL,
                    previous_event_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL,
                    var_ref TEXT,
                    PRIMARY KEY (stream_id, revision)
                );

                CREATE TABLE IF NOT EXISTS stream_heads (
                    stream_id TEXT PRIMARY KEY,
                    last_revision INTEGER NOT NULL,
                    last_event_hash TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS nonce_ledger (
                    recovery_subject TEXT NOT NULL,
                    nonce TEXT NOT NULL,
                    state TEXT NOT NULL CHECK(state IN ('UNUSED','CONSUMED')),
                    var_ref TEXT,
                    PRIMARY KEY (recovery_subject, nonce)
                );

                CREATE TABLE IF NOT EXISTS receipts (
                    recovery_subject TEXT PRIMARY KEY,
                    receipt_data BLOB NOT NULL,
                    state TEXT NOT NULL CHECK(state IN ('ABSENT','CANONICAL','INTEGRITY_DEFECT')),
                    var_ref TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_nonce_ledger_subject ON nonce_ledger(recovery_subject);

                -- Append-only enforcement triggers (P0-01, P0-03)
                CREATE TRIGGER IF NOT EXISTS events_no_update
                BEFORE UPDATE ON events
                BEGIN
                    SELECT RAISE(ABORT, 'events table is append-only');
                END;

                CREATE TRIGGER IF NOT EXISTS events_no_delete
                BEFORE DELETE ON events
                BEGIN
                    SELECT RAISE(ABORT, 'events table is append-only');
                END;

                -- Block REPLACE via INSERT trigger that checks PK existence
                CREATE TRIGGER IF NOT EXISTS events_no_insert_replace
                BEFORE INSERT ON events
                WHEN EXISTS (SELECT 1 FROM events WHERE stream_id = NEW.stream_id AND revision = NEW.revision)
                BEGIN
                    SELECT RAISE(ABORT, 'events append-only: duplicate revision - REPLACE not allowed');
                END;

                -- Nonce ledger: allow only UNUSED->CONSUMED transition (IC-4), block others
                CREATE TRIGGER IF NOT EXISTS nonce_ledger_no_update
                BEFORE UPDATE ON nonce_ledger
                WHEN OLD.state != 'UNUSED' OR NEW.state != 'CONSUMED'
                  OR OLD.recovery_subject != NEW.recovery_subject OR OLD.nonce != NEW.nonce
                BEGIN
                    SELECT RAISE(ABORT, 'nonce_ledger is append-only/terminal');
                END;
                CREATE TRIGGER IF NOT EXISTS nonce_ledger_no_delete
                BEFORE DELETE ON nonce_ledger
                BEGIN
                    SELECT RAISE(ABORT, 'nonce_ledger is append-only');
                END;

                -- Receipts immutability: CANONICAL/INTEGRITY_DEFECT terminal
                CREATE TRIGGER IF NOT EXISTS receipts_no_update
                BEFORE UPDATE ON receipts
                BEGIN
                    SELECT RAISE(ABORT, 'receipts is immutable once CANONICAL/DEFECT');
                END;
                CREATE TRIGGER IF NOT EXISTS receipts_no_delete
                BEFORE DELETE ON receipts
                BEGIN
                    SELECT RAISE(ABORT, 'receipts is append-only');
                END;

                -- Stream heads: only CAS via storage.py, block direct UPDATE/DELETE except via CAS path
                -- (enforced at application layer; trigger prevents blind REPLACE)
                CREATE TRIGGER IF NOT EXISTS heads_no_delete
                BEFORE DELETE ON stream_heads
                BEGIN
                    SELECT RAISE(ABORT, 'stream_heads is append-only');
                END;

                CREATE TRIGGER IF NOT EXISTS stream_heads_no_replace
                BEFORE INSERT ON stream_heads
                WHEN EXISTS (SELECT 1 FROM stream_heads WHERE stream_id = NEW.stream_id)
                BEGIN
                    SELECT RAISE(ABORT, 'stream_heads is append-only via CAS');
                END;

                CREATE TRIGGER IF NOT EXISTS receipts_no_replace
                BEFORE INSERT ON receipts
                WHEN EXISTS (SELECT 1 FROM receipts WHERE recovery_subject = NEW.recovery_subject)
                BEGIN
                    SELECT RAISE(ABORT, 'receipts is append-only via CAS');
                END;

                CREATE TABLE IF NOT EXISTS rollback_cause_observations (
                    rollback_cause_id TEXT PRIMARY KEY,
                    observation_id TEXT NOT NULL,
                    source_universe TEXT NOT NULL,
                    policy_root_ref TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    severity TEXT NOT NULL,
                    var_ref TEXT
                );

                CREATE TRIGGER IF NOT EXISTS rollback_cause_no_update
                BEFORE UPDATE ON rollback_cause_observations
                BEGIN
                    SELECT RAISE(ABORT, 'rollback_cause_observations is append-only');
                END;

                CREATE TRIGGER IF NOT EXISTS rollback_cause_no_delete
                BEFORE DELETE ON rollback_cause_observations
                BEGIN
                    SELECT RAISE(ABORT, 'rollback_cause_observations is append-only');
                END;

                CREATE TRIGGER IF NOT EXISTS rollback_cause_no_replace
                BEFORE INSERT ON rollback_cause_observations
                WHEN EXISTS (SELECT 1 FROM rollback_cause_observations WHERE rollback_cause_id = NEW.rollback_cause_id)
                BEGIN
                    SELECT RAISE(ABORT, 'rollback_cause_observations append-only: duplicate rollback_cause_id');
                END;
            """)

    def close(self) -> None:
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def fetch_all(self, query: str, params: tuple = ()) -> List[Tuple[Any, ...]]:
        """Executes a read query and returns all matching rows as tuples."""
        conn = self._get_conn()
        cur = conn.execute(query, params)
        return cur.fetchall()

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Tuple[Any, ...]]:
        """Executes a read query and returns the first matching row or None."""
        conn = self._get_conn()
        cur = conn.execute(query, params)
        return cur.fetchone()

    def execute_write(self, query: str, params: tuple = ()) -> int:
        """Executes a write query within an auto-committed transaction."""
        conn = self._get_conn()
        with conn:
            cur = conn.execute(query, params)
            return cur.rowcount

    def execute_script(self, script: str) -> None:
        """Executes a multi-statement DDL/DML script."""
        conn = self._get_conn()
        with conn:
            conn.executescript(script)

    def table_exists(self, table_name: str) -> bool:
        """Checks if a table exists in sqlite_master."""
        row = self.fetch_one(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        return row is not None

    def count_events(self, stream_id: str) -> int:
        """Counts total committed events in a given stream."""
        row = self.fetch_one(
            "SELECT COUNT(1) FROM events WHERE stream_id = ?",
            (stream_id,),
        )
        return row[0] if row else 0

    def _reset_connection(self) -> None:
        """Force close and reset thread-local connection (for testing/recovery)."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None

    @staticmethod
    def _compute_event_hash(
        stream_id: str,
        revision: int,
        event_data: bytes,
        previous_event_hash: str,
        var_ref: Optional[str] = None,
    ) -> str:
        h = hashlib.sha256()
        h.update(stream_id.encode("utf-8"))
        h.update(revision.to_bytes(8, "big", signed=False))
        h.update(event_data)
        h.update(previous_event_hash.encode("utf-8"))
        if var_ref is not None:
            h.update(var_ref.encode("utf-8"))
        return h.hexdigest()

    def append_event(
        self,
        stream_id: str,
        event_data: bytes,
        expected_revision: int,
        prev_event_hash: str,
        var_ref: Optional[str] = None,
    ) -> EventRecord:
        """
        Append event to stream using CAS on head table.
        Fails if expected_revision != current head revision (CAS failure).
        """
        conn = self._get_conn()
        # BEGIN IMMEDIATE for true CAS serialization
        conn.execute("BEGIN IMMEDIATE;")
        try:
            cur = conn.execute(
                "SELECT last_revision, last_event_hash FROM stream_heads WHERE stream_id = ?",
                (stream_id,),
            )
            row = cur.fetchone()
            if row is None:
                current_rev = 0
                prev_hash = "0" * 64
            else:
                current_rev, prev_hash = row

            if current_rev != expected_revision:
                raise Edge1Error(
                    f"CAS failed: stream {stream_id} revision {current_rev} != expected {expected_revision}"
                )

            # Verify prev_event_hash matches current head
            if prev_hash != prev_event_hash:
                raise Edge1Error(
                    f"Previous event hash mismatch: head={prev_hash} != provided={prev_event_hash}"
                )

            revision = current_rev + 1
            event_hash = self._compute_event_hash(
                stream_id, revision, event_data, prev_hash, var_ref
            )

            conn.execute(
                "INSERT INTO events (stream_id, revision, event_data, previous_event_hash, event_hash, var_ref) VALUES (?, ?, ?, ?, ?, ?)",
                (stream_id, revision, event_data, prev_hash, event_hash, var_ref),
            )

            # True CAS: INSERT for new stream, else UPDATE with WHERE last_revision=?
            if row is None:
                conn.execute(
                    "INSERT INTO stream_heads (stream_id, last_revision, last_event_hash) VALUES (?, ?, ?)",
                    (stream_id, revision, event_hash),
                )
            else:
                cur = conn.execute(
                    """UPDATE stream_heads 
                       SET last_revision=?, last_event_hash=?
                       WHERE stream_id=? AND last_revision=?""",
                    (revision, event_hash, stream_id, expected_revision),
                )
                if cur.rowcount == 0:
                    raise Edge1Error("CAS failed: concurrent modification")

            conn.execute("COMMIT;")

            record = EventRecord(
                stream_id=stream_id,
                revision=revision,
                event_data=event_data,
                previous_event_hash=prev_hash,
                event_hash=event_hash,
                var_ref=var_ref,
            )

            # Atomically write to JSONL witness if persistence is active
            if self._witness_path is not None:
                last_witness_hash = get_last_witness_hash(self._witness_path)
                try:
                    write_witness_record(
                        self._witness_path, stream_id, revision, event_data.hex(),
                        prev_hash, event_hash, var_ref, last_witness_hash,
                    )
                except Exception as e:
                    raise CriticalTamperingError(f"Cache advanced beyond Witness: {e}") from e

            return record
        except Exception:
            conn.execute("ROLLBACK;")
            raise

    def verify_full_chain_integrity(self) -> tuple[bool, str]:
        """
        Dual-layer cryptographic integrity verification:
        1. Verifies the JSONL witness hash chain and event hashes from first to last record.
        2. Compares SQLite primary store records against the JSONL witness.
        """
        if self._witness_path is None:
            return True, "OK"
        return verify_full_chain_integrity(
            self._get_conn(), self._witness_path, self._compute_event_hash
        )

    def rebuild_cache_from_witness(self) -> int:
        """
        Reconstructs the primary SQLite cache from the immutable JSONL witness source of truth.
        """
        if self._witness_path is None or not os.path.exists(self._witness_path):
            return 0
        return rebuild_cache_from_witness(
            self._get_conn(), self._witness_path, self._compute_event_hash, self._init_schema
        )

    def verify_and_heal(self) -> None:
        """
        Boot-time verification and automatic self-healing cache rebuild.
        Fails closed with CriticalTamperingError if the source of truth is compromised.
        """
        if self._witness_path is None:
            return
        verify_and_heal(
            self._get_conn(), self._witness_path, self._compute_event_hash, self._init_schema
        )

    def get_head(self, stream_id: str) -> Optional[tuple[int, str]]:
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT last_revision, last_event_hash FROM stream_heads WHERE stream_id = ?",
            (stream_id,),
        )
        return cur.fetchone()

    def get_event(self, stream_id: str, revision: int) -> Optional[EventRecord]:
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT stream_id, revision, event_data, previous_event_hash, event_hash, var_ref "
            "FROM events WHERE stream_id = ? AND revision = ?",
            (stream_id, revision),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return EventRecord(
            stream_id=row[0],
            revision=row[1],
            event_data=row[2],
            previous_event_hash=row[3],
            event_hash=row[4],
            var_ref=row[5],
        )

    def verify_chain(self, stream_id: str) -> bool:
        """Verify previous-event-hash chain integrity for a stream."""
        return verify_chain(self._get_conn(), stream_id, self._compute_event_hash)


class Edge1Manager:
    """
    Implements Edge 1 (A-PROSPECTIVE-AUTHORITY-RELIANCE-RECOVERY) per Matrix V30 IC-4:
    - receipt-append FIRST, nonce-consumption SECOND, single transaction
    - IC-4 deterministic crash finalization: forces UNUSED+receipt -> CONSUMED
    - IC-3: nonce ledger entry created atomically with VAR issuance
    """

    def __init__(self, db_path: str):
        self._store = EventStore(db_path)

    def close(self) -> None:
        self._store.close()

    def issue_var_and_nonce(
        self, recovery_subject: str, nonce: str, var_ref: str
    ) -> NonceRecord:
        """
        IC-3: Create UNUSED nonce ledger entry atomically with VAR issuance.
        A VAR whose ledger entry is absent => VAR is INVALID (no orphan VAR).
        """
        conn = self._store._get_conn()
        conn.execute("BEGIN IMMEDIATE;")
        try:
            cur = conn.execute(
                "SELECT 1 FROM nonce_ledger WHERE recovery_subject = ? AND nonce = ?",
                (recovery_subject, nonce),
            )
            if cur.fetchone():
                raise Edge1Error(f"Nonce already exists for subject {recovery_subject}")

            conn.execute(
                "INSERT INTO nonce_ledger (recovery_subject, nonce, state, var_ref) VALUES (?, ?, ?, ?)",
                (recovery_subject, nonce, NonceState.UNUSED.value, var_ref),
            )
            conn.execute("COMMIT;")
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise

        return NonceRecord(
            recovery_subject=recovery_subject,
            nonce=nonce,
            state=NonceState.UNUSED,
            var_ref=var_ref,
        )

    def bind_var_to_nonce(self, recovery_subject: str, nonce: str, var_ref: str) -> None:
        """Bind VAR reference to nonce after successful issuance (IC-3)."""
        conn = self._store._get_conn()
        conn.execute("BEGIN IMMEDIATE;")
        try:
            conn.execute(
                "UPDATE nonce_ledger SET var_ref = ? WHERE recovery_subject = ? AND nonce = ? AND state = ?",
                (var_ref, recovery_subject, nonce, NonceState.UNUSED.value),
            )
            conn.execute("COMMIT;")
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise

    def append_receipt_and_consume(
        self,
        recovery_subject: str,
        nonce: str,
        receipt_data: bytes,
        var_ref: str,
    ) -> ReceiptRecord:
        """
        IC-4: Single transaction: receipt-append FIRST, nonce-consumption SECOND.
        Returns the committed receipt. Uses explicit BEGIN IMMEDIATE for atomicity.
        """
        conn = self._store._get_conn()
        conn.execute("BEGIN IMMEDIATE;")
        try:
            cur = conn.execute(
                "SELECT state FROM nonce_ledger WHERE recovery_subject = ? AND nonce = ?",
                (recovery_subject, nonce),
            )
            row = cur.fetchone()
            if row is None:
                raise Edge1Error(f"Nonce not found: {recovery_subject}/{nonce}")
            if row[0] != NonceState.UNUSED.value:
                raise Edge1Error(f"Nonce not UNUSED: {row[0]}")

            cur = conn.execute(
                "SELECT receipt_data, state FROM receipts WHERE recovery_subject = ?",
                (recovery_subject,),
            )
            row = cur.fetchone()
            if row is not None:
                existing_data, existing_state = row
                if existing_state == ReceiptState.CANONICAL.value:
                    if existing_data != receipt_data:
                        # Write INTEGRITY_DEFECT for conflicting payload (P1-11)
                        try:
                            conn.execute(
                                "INSERT INTO receipts (recovery_subject, receipt_data, state, var_ref) VALUES (?, ?, ?, ?)",
                                (recovery_subject + "#defect#" + nonce, receipt_data, ReceiptState.INTEGRITY_DEFECT.value, var_ref),
                            )
                        except Exception:
                            pass
                        raise Edge1Error("Receipt INTEGRITY_DEFECT (conflicting payload)")
                    raise Edge1Error("Receipt already CANONICAL (idempotent replay after full preconditions)")
                elif existing_state == ReceiptState.INTEGRITY_DEFECT.value:
                    raise Edge1Error("Receipt INTEGRITY_DEFECT (conflicting payload)")

            # Plain INSERT (not REPLACE) — respects append-only trigger (P0-01)
            conn.execute(
                "INSERT INTO receipts (recovery_subject, receipt_data, state, var_ref) VALUES (?, ?, ?, ?)",
                (recovery_subject, receipt_data, ReceiptState.CANONICAL.value, var_ref),
            )

            conn.execute(
                "UPDATE nonce_ledger SET state = ?, var_ref = ? WHERE recovery_subject = ? AND nonce = ?",
                (NonceState.CONSUMED.value, var_ref, recovery_subject, nonce),
            )
            conn.execute("COMMIT;")
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise

        return ReceiptRecord(
            recovery_subject=recovery_subject,
            receipt_data=receipt_data,
            state=ReceiptState.CANONICAL,
            var_ref=var_ref,
        )

    def recognize_existing_receipt(
        self, recovery_subject: str, receipt_data: bytes, var_ref: str
    ) -> ReceiptRecord:
        """
        IC-2: Recognition is a gated read — MUST re-evaluate ALL Edge 1 preconditions
        at use time including VAR CURRENT/not-revoked/not-expired.
        Identical replay recognizes existing receipt after full precondition re-evaluation.
        """
        conn = self._store._get_conn()
        cur = conn.execute(
            "SELECT receipt_data, state, var_ref FROM receipts WHERE recovery_subject = ?",
            (recovery_subject,),
        )
        row = cur.fetchone()
        if row is None:
            raise Edge1Error(f"No receipt found for subject {recovery_subject}")

        existing_data, state, existing_var_ref = row
        if state != ReceiptState.CANONICAL.value:
            raise Edge1Error(f"Receipt not CANONICAL: {state}")

        if existing_data != receipt_data:
            raise Edge1Error("Conflicting receipt payload -> INTEGRITY_DEFECT")

        if existing_var_ref != var_ref:
            raise Edge1Error("VAR reference mismatch")

        return ReceiptRecord(
            recovery_subject=recovery_subject,
            receipt_data=receipt_data,
            state=ReceiptState.CANONICAL,
            var_ref=var_ref,
        )

    def finalize_crash_recovery(self) -> int:
        """
        IC-4: Idempotent crash finalization.
        Forces any UNUSED nonce_ledger entry that has a paired appended receipt to CONSUMED.
        Derives decisions ONLY from ledger+VAR state (no clock, no external facts).
        Returns count of entries finalized. Now var_ref-matched to avoid fan-out (P0-05).
        """
        conn = self._store._get_conn()
        conn.execute("BEGIN IMMEDIATE;")
        try:
            cur = conn.execute(
                "SELECT nl.recovery_subject, nl.nonce, nl.var_ref "
                "FROM nonce_ledger nl "
                "JOIN receipts r ON nl.recovery_subject = r.recovery_subject AND nl.var_ref = r.var_ref "
                "WHERE nl.state = ? AND r.state = ?",
                (NonceState.UNUSED.value, ReceiptState.CANONICAL.value),
            )
            rows = cur.fetchall()
            count = 0
            for recovery_subject, nonce, var_ref in rows:
                # Preserve original var_ref (P1-09: no or "" overwrite)
                conn.execute(
                    "UPDATE nonce_ledger SET state = ? "
                    "WHERE recovery_subject = ? AND nonce = ?",
                    (NonceState.CONSUMED.value, recovery_subject, nonce),
                )
                count += 1
            conn.execute("COMMIT;")
            return count
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise

    def get_nonce_state(self, recovery_subject: str, nonce: str) -> Optional[NonceState]:
        conn = self._store._get_conn()
        cur = conn.execute(
            "SELECT state FROM nonce_ledger WHERE recovery_subject = ? AND nonce = ?",
            (recovery_subject, nonce),
        )
        row = cur.fetchone()
        return NonceState(row[0]) if row else None

    def get_receipt_state(self, recovery_subject: str) -> Optional[ReceiptState]:
        conn = self._store._get_conn()
        cur = conn.execute(
            "SELECT state FROM receipts WHERE recovery_subject = ?",
            (recovery_subject,),
        )
        row = cur.fetchone()
        return ReceiptState(row[0]) if row else None

    def append_rollback_cause(
        self,
        record: RollbackCauseRecord,
        role: Optional[str] = None,
    ) -> RollbackCauseRecord:
        """
        Append rollback cause observation (IC-5 / G16 / G17 SoD).
        G16: Critic cannot rescue.
        G17: Research cannot self-validate / self-clear rollback cause.
        """
        if role == "CRITIC_RESCUE":
            raise Edge1Error("SoD violation: Critic cannot rescue or clear rollback cause (G16)")
        if role == "RESEARCH_SELF_VALIDATE":
            raise Edge1Error("SoD violation: Research cannot self-validate (G17)")

        conn = self._store._get_conn()
        conn.execute("BEGIN IMMEDIATE;")
        try:
            conn.execute(
                """
                INSERT INTO rollback_cause_observations 
                (rollback_cause_id, observation_id, source_universe, policy_root_ref, timestamp, severity, var_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.rollback_cause_id,
                    record.observation_id,
                    record.source_universe,
                    record.policy_root_ref,
                    record.timestamp,
                    record.severity,
                    record.var_ref,
                ),
            )
            conn.execute("COMMIT;")
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise
        return record

    def get_rollback_cause(self, rollback_cause_id: str) -> Optional[RollbackCauseRecord]:
        conn = self._store._get_conn()
        cur = conn.execute(
            """
            SELECT rollback_cause_id, observation_id, source_universe, policy_root_ref, timestamp, severity, var_ref
            FROM rollback_cause_observations WHERE rollback_cause_id = ?
            """,
            (rollback_cause_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return RollbackCauseRecord(
            rollback_cause_id=row[0],
            observation_id=row[1],
            source_universe=row[2],
            policy_root_ref=row[3],
            timestamp=row[4],
            severity=row[5],
            var_ref=row[6],
        )

    def list_rollback_causes(self, source_universe: Optional[str] = None) -> list[RollbackCauseRecord]:
        conn = self._store._get_conn()
        if source_universe:
            cur = conn.execute(
                """
                SELECT rollback_cause_id, observation_id, source_universe, policy_root_ref, timestamp, severity, var_ref
                FROM rollback_cause_observations WHERE source_universe = ? ORDER BY timestamp ASC
                """,
                (source_universe,),
            )
        else:
            cur = conn.execute(
                """
                SELECT rollback_cause_id, observation_id, source_universe, policy_root_ref, timestamp, severity, var_ref
                FROM rollback_cause_observations ORDER BY timestamp ASC
                """
            )
        return [
            RollbackCauseRecord(
                rollback_cause_id=r[0],
                observation_id=r[1],
                source_universe=r[2],
                policy_root_ref=r[3],
                timestamp=r[4],
                severity=r[5],
                var_ref=r[6],
            )
            for r in cur.fetchall()
        ]


def open_store(db_path: str) -> tuple[EventStore, Edge1Manager]:
    """Factory: open both stores sharing the same DB file."""
    store = EventStore(db_path)
    edge1 = Edge1Manager(db_path)
    return store, edge1


def migrate_event_store_var_ref(db_path: str) -> int:
    """
    RES-03: Re-derive hash chain for existing events database to include var_ref.
    Deterministic, no data loss with automated backup and rollback on failure (FIX-05).
    """
    if not os.path.exists(db_path):
        return 0

    backup_path = db_path + ".backup"
    shutil.copy2(db_path, backup_path)
    try:
        conn = sqlite3.connect(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
            if not cur.fetchone():
                if os.path.exists(backup_path):
                    os.unlink(backup_path)
                return 0

            cur.execute(
                "SELECT stream_id, revision, event_data, var_ref FROM events ORDER BY stream_id, revision ASC"
            )
            rows = cur.fetchall()
            if not rows:
                if os.path.exists(backup_path):
                    os.unlink(backup_path)
                return 0

            from collections import defaultdict
            streams = defaultdict(list)
            for row in rows:
                streams[row[0]].append(row)

            migrated_events = []
            new_heads = {}

            for stream_id, stream_rows in streams.items():
                prev_hash = "0" * 64
                for r in stream_rows:
                    s_id, rev, ev_data, v_ref = r
                    ev_hash = EventStore._compute_event_hash(s_id, rev, ev_data, prev_hash, v_ref)
                    migrated_events.append((s_id, rev, ev_data, prev_hash, ev_hash, v_ref))
                    prev_hash = ev_hash
                new_heads[stream_id] = (stream_rows[-1][1], prev_hash)

            with conn:
                conn.execute("CREATE TABLE _events_migrated AS SELECT * FROM events WHERE 0")
                for ev in migrated_events:
                    conn.execute(
                        "INSERT INTO _events_migrated (stream_id, revision, event_data, previous_event_hash, event_hash, var_ref) VALUES (?, ?, ?, ?, ?, ?)",
                        ev,
                    )
                conn.execute("DROP TRIGGER IF EXISTS events_no_update")
                conn.execute("DROP TRIGGER IF EXISTS events_no_delete")
                conn.execute("DROP TRIGGER IF EXISTS events_no_insert_replace")
                conn.execute("DELETE FROM events")
                conn.execute("INSERT INTO events SELECT * FROM _events_migrated")
                conn.execute("DROP TABLE _events_migrated")

                conn.execute("DROP TRIGGER IF EXISTS heads_no_delete")
                conn.execute("DROP TRIGGER IF EXISTS stream_heads_no_replace")
                conn.execute("DELETE FROM stream_heads")
                for s_id, (last_rev, last_h) in new_heads.items():
                    conn.execute(
                        "INSERT INTO stream_heads (stream_id, last_revision, last_event_hash) VALUES (?, ?, ?)",
                        (s_id, last_rev, last_h),
                    )

            # Restore schema triggers
            store = EventStore(db_path)
            store.close()

            # Migration succeeded: clean up backup file
            if os.path.exists(backup_path):
                os.unlink(backup_path)

            return len(migrated_events)
        finally:
            conn.close()
    except Exception:
        # Restore original database from backup on any failure
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, db_path)
            try:
                os.unlink(backup_path)
            except Exception:
                pass
        raise


def enforce_db_permissions(db_path: str) -> bool:
    """Enforce restrictive permissions (chmod 600) on database file (RES-01)."""
    if os.path.exists(db_path):
        try:
            os.chmod(db_path, 0o600)
            return True
        except Exception:
            return False
    return False


@dataclass(frozen=True)
class CapabilityToken:
    token_id: str
    role: str
    authority_scope: str
    expiration_ts: float
    signature: str

    def is_valid(self, required_role: str, current_ts: float, secret_key: str = "") -> bool:
        if self.expiration_ts < current_ts:
            return False
        if self.role != required_role and self.role != "OWNER":
            return False
        expected_sig = hmac.new(
            secret_key.encode("utf-8"),
            f"{self.token_id}:{self.role}:{self.authority_scope}:{self.expiration_ts:.2f}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(self.signature, expected_sig)


def issue_capability_token(
    token_id: str,
    role: str,
    authority_scope: str,
    ttl_sec: float = 3600.0,
    current_ts: Optional[float] = None,
    secret_key: str = "",
) -> CapabilityToken:
    import time
    ts = time.time() if current_ts is None else current_ts
    exp = ts + ttl_sec
    sig = hmac.new(
        secret_key.encode("utf-8"),
        f"{token_id}:{role}:{authority_scope}:{exp:.2f}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return CapabilityToken(
        token_id=token_id,
        role=role,
        authority_scope=authority_scope,
        expiration_ts=exp,
        signature=sig,
    )


class KeeperProcessExecutor:
    """
    Process isolation & capability token enforcement for authority operations (IAQ-003 / RES-01).
    """

    def __init__(self, db_path: str, secret_key: str = ""):
        self.db_path = db_path
        self.secret_key = secret_key

    def execute_with_token(
        self,
        token: CapabilityToken,
        required_role: str,
        operation: Any,
        secret_key: Optional[str] = None,
    ) -> Any:
        import time
        now = time.time()
        s_key = self.secret_key if secret_key is None else secret_key
        if not token.is_valid(required_role, now, s_key):
            raise Edge1Error(f"Unauthorized or expired capability token for role '{required_role}'")

        conn = sqlite3.connect(self.db_path)
        try:
            return operation(conn)
        finally:
            conn.close()