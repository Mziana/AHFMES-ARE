"""
AHFMES ARE — Chain Verification

Standalone functions for verifying and rebuilding the event chain:
- Single-stream chain verification
- Dual-layer integrity verification (SQLite + JSONL witness)
- Cache rebuild from witness
- Boot-time verification and self-healing

The JSONL witness is the immutable Source of Truth. SQLite is a cache.
Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from typing import Any, Callable, List, Optional, Tuple

from are.witness import (
    get_last_witness_hash,
    read_witness_records,
    verify_witness_chain,
)


def verify_chain(
    conn: sqlite3.Connection,
    stream_id: str,
    compute_event_hash_fn: Callable[..., str],
) -> bool:
    """Verify previous-event-hash chain integrity for a single stream."""
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
        computed = compute_event_hash_fn(stream_id, rev, event_data, prev_hash, var_ref_val)
        if computed != ev_h:
            return False
        prev_hash = ev_h
    return True


def verify_full_chain_integrity(
    conn: sqlite3.Connection,
    witness_path: str,
    compute_event_hash_fn: Callable[..., str],
) -> Tuple[bool, str]:
    """Dual-layer cryptographic integrity verification.

    1. Verifies the JSONL witness hash chain and event hashes from first to last record.
    2. Compares SQLite primary store records against the JSONL witness.

    Returns (is_valid, status_code).
    Status codes: OK, SQLITE_MISMATCH, WITNESS_CORRUPTED
    """
    witness_records = read_witness_records(witness_path)
    witness_exists = len(witness_records) > 0

    cur = conn.execute(
        "SELECT stream_id, revision, event_data, previous_event_hash, event_hash, var_ref "
        "FROM events ORDER BY rowid ASC"
    )
    sqlite_rows = cur.fetchall()

    if not witness_exists:
        if len(sqlite_rows) > 0:
            return False, "SQLITE_MISMATCH"
        return True, "OK"

    # Verification 1: Witness internal hash chain
    is_valid, status = verify_witness_chain(witness_records, compute_event_hash_fn)
    if not is_valid:
        return False, status

    # Verification 2: Compare SQLite against Witness
    if len(sqlite_rows) != len(witness_records):
        return False, "SQLITE_MISMATCH"

    for row, w_rec in zip(sqlite_rows, witness_records):
        s_stream, s_rev, s_data, s_prev_h, s_ev_h, s_var = row
        w_data = bytes.fromhex(w_rec["event_data_hex"])
        if (
            s_stream != w_rec["stream_id"]
            or s_rev != w_rec["revision"]
            or s_data != w_data
            or s_prev_h != w_rec["previous_event_hash"]
            or s_ev_h != w_rec["event_hash"]
            or (s_var or None) != (w_rec.get("var_ref") or None)
        ):
            return False, "SQLITE_MISMATCH"

    return True, "OK"


def rebuild_cache_from_witness(
    conn: sqlite3.Connection,
    witness_path: str,
    compute_event_hash_fn: Callable[..., str],
    init_schema_fn: Callable[[], None],
) -> int:
    """Reconstruct the primary SQLite cache from the immutable JSONL witness.

    Raises CriticalTamperingError if the witness is compromised.
    Returns the number of records rebuilt.
    """
    from are.storage import CriticalTamperingError

    witness_records = read_witness_records(witness_path)
    if not witness_records:
        return 0

    # Validate witness chain before rebuilding
    is_valid, status = verify_witness_chain(witness_records, compute_event_hash_fn)
    if not is_valid:
        raise CriticalTamperingError("Cannot rebuild: JSONL Witness is compromised")

    # Also verify sequential revisions and stream chains
    curr_prev = "0" * 64
    stream_revs = {}
    stream_hashes = {}
    for rec in witness_records:
        if rec["witness_prev_hash"] != curr_prev:
            raise CriticalTamperingError("Cannot rebuild: JSONL Witness is compromised")
        try:
            data_bytes = bytes.fromhex(rec["event_data_hex"])
        except Exception:
            raise CriticalTamperingError("Cannot rebuild: JSONL Witness is compromised")
        expected_event_hash = compute_event_hash_fn(
            stream_id=rec["stream_id"],
            revision=rec["revision"],
            event_data=data_bytes,
            previous_event_hash=rec["previous_event_hash"],
            var_ref=rec.get("var_ref"),
        )
        if rec["event_hash"] != expected_event_hash:
            raise CriticalTamperingError("Cannot rebuild: JSONL Witness is compromised")
        last_rev = stream_revs.get(rec["stream_id"], 0)
        if rec["revision"] != last_rev + 1:
            raise CriticalTamperingError("Cannot rebuild: JSONL Witness is compromised")
        last_h = stream_hashes.get(rec["stream_id"], "0" * 64)
        if rec["previous_event_hash"] != last_h:
            raise CriticalTamperingError("Cannot rebuild: JSONL Witness is compromised")
        stream_revs[rec["stream_id"]] = rec["revision"]
        stream_hashes[rec["stream_id"]] = rec["event_hash"]
        curr_prev = rec["witness_hash"]

    # Rebuild SQLite cache
    conn.set_authorizer(None)
    try:
        with conn:
            conn.execute("DROP TRIGGER IF EXISTS events_no_update;")
            conn.execute("DROP TRIGGER IF EXISTS events_no_delete;")
            conn.execute("DROP TRIGGER IF EXISTS heads_no_delete;")
            conn.execute("DROP TRIGGER IF EXISTS stream_heads_no_replace;")
            conn.execute("DELETE FROM events;")
            conn.execute("DELETE FROM stream_heads;")

            heads = {}
            for rec in witness_records:
                data_bytes = bytes.fromhex(rec["event_data_hex"])
                conn.execute(
                    "INSERT INTO events (stream_id, revision, event_data, previous_event_hash, event_hash, var_ref) VALUES (?, ?, ?, ?, ?, ?)",
                    (rec["stream_id"], rec["revision"], data_bytes, rec["previous_event_hash"], rec["event_hash"], rec.get("var_ref")),
                )
                heads[rec["stream_id"]] = (rec["revision"], rec["event_hash"])

            for s_id, (l_rev, l_hash) in heads.items():
                conn.execute(
                    "INSERT INTO stream_heads (stream_id, last_revision, last_event_hash) VALUES (?, ?, ?)",
                    (s_id, l_rev, l_hash),
                )
    finally:
        init_schema_fn()

    return len(witness_records)


def verify_and_heal(
    conn: sqlite3.Connection,
    witness_path: Optional[str],
    compute_event_hash_fn: Callable[..., str],
    init_schema_fn: Callable[[], None],
) -> None:
    """Boot-time verification and automatic self-healing cache rebuild.

    Fails closed with CriticalTamperingError if the source of truth is compromised.
    """
    if witness_path is None:
        return
    ok, status = verify_full_chain_integrity(conn, witness_path, compute_event_hash_fn)
    if status == "SQLITE_MISMATCH":
        rebuild_cache_from_witness(conn, witness_path, compute_event_hash_fn, init_schema_fn)
    elif status == "WITNESS_CORRUPTED":
        from are.storage import CriticalTamperingError
        raise CriticalTamperingError("CRITICAL: Witness tampering detected! Halt.")
