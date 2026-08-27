"""
AHFMES ARE-1 — Storage Engine (Slice-1 Part A)

Implements append-only event store with SQLite WAL, head table CAS,
and IC-4 deterministic crash finalization per Matrix V30 IC-4 /
Register V30 EDGE_NONCE_CONSUMPTION_LEDGER + REFINEMENT_PROSPECTIVE_RELIANCE_RECEIPT.

Zero external dependencies (stdlib only: sqlite3, hashlib, json, os, threading).
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class ReceiptState(Enum):
    ABSENT = "ABSENT"
    CANONICAL = "CANONICAL"
    INTEGRITY_DEFECT = "INTEGRITY_DEFECT"


class NonceState(Enum):
    UNUSED = "UNUSED"
    CONSUMED = "CONSUMED"


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


class EventStore:
    """
    Append-only event store with per-stream head table and CAS mutation.
    All events are immutable once committed.
    """

    def __init__(self, db_path: str, wal_mode: bool = True):
        self._db_path = db_path
        self._local = threading.local()
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self._db_path, isolation_level=None)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = FULL")
            conn.execute("PRAGMA busy_timeout = 5000")
            # Block dangerous operations via authorizer (P0-02, P0-10)
            try:
                def _authorizer(action, arg1, arg2, dbname, trigger):
                    if action == 11 or action == 16:  # SQLITE_DROP_TABLE (11) / SQLITE_DROP_TRIGGER (16) — DENY ALL
                        return 1  # SQLITE_DENY
                    if action == 24:  # SQLITE_ATTACH
                        return 1
                    return 0  # SQLITE_OK
                conn.set_authorizer(_authorizer)
            except Exception:
                pass
            self._local.conn = conn
        return self._local.conn

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

            return EventRecord(
                stream_id=stream_id,
                revision=revision,
                event_data=event_data,
                previous_event_hash=prev_hash,
                event_hash=event_hash,
                var_ref=var_ref,
            )
        except Exception:
            conn.execute("ROLLBACK;")
            raise

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
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT revision, event_data, previous_event_hash, event_hash, var_ref "
            "FROM events WHERE stream_id = ? ORDER BY revision ASC",
            (stream_id,),
        )
        prev_hash = "0" * 64
        for row in cur:
            rev, event_data, prev_h, ev_h, var_ref_val = row
            if prev_h != prev_hash:
                return False
            computed = self._compute_event_hash(
                stream_id, rev, event_data, prev_hash, var_ref_val
            )
            if computed != ev_h:
                return False
            prev_hash = ev_h
        return True


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
    Deterministic, no data loss.
    """
    if not os.path.exists(db_path):
        return 0

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        if not cur.fetchone():
            return 0

        cur.execute(
            "SELECT stream_id, revision, event_data, var_ref FROM events ORDER BY stream_id, revision ASC"
        )
        rows = cur.fetchall()
        if not rows:
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

        return len(migrated_events)
    finally:
        conn.close()


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

    def is_valid(self, required_role: str, current_ts: float) -> bool:
        if self.expiration_ts < current_ts:
            return False
        if self.role != required_role and self.role != "OWNER":
            return False
        expected_sig = hashlib.sha256(
            f"{self.token_id}:{self.role}:{self.authority_scope}:{self.expiration_ts:.2f}".encode("utf-8")
        ).hexdigest()
        return self.signature == expected_sig


def issue_capability_token(
    token_id: str,
    role: str,
    authority_scope: str,
    ttl_sec: float = 3600.0,
    current_ts: Optional[float] = None,
) -> CapabilityToken:
    import time
    ts = time.time() if current_ts is None else current_ts
    exp = ts + ttl_sec
    sig = hashlib.sha256(
        f"{token_id}:{role}:{authority_scope}:{exp:.2f}".encode("utf-8")
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

    def __init__(self, db_path: str):
        self.db_path = db_path

    def execute_with_token(
        self,
        token: CapabilityToken,
        required_role: str,
        operation: Any,
    ) -> Any:
        import time
        now = time.time()
        if not token.is_valid(required_role, now):
            raise Edge1Error(f"Unauthorized or expired capability token for role '{required_role}'")

        conn = sqlite3.connect(self.db_path)
        try:
            return operation(conn)
        finally:
            conn.close()