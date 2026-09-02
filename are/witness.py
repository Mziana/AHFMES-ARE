"""
AHFMES ARE — JSONL Witness Layer

Standalone functions for the JSONL witness file operations:
- Writing witness records
- Reading witness records
- Verifying witness internal hash chain
- Getting last witness hash

The JSONL witness is the immutable Source of Truth. SQLite is a cache.
Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Callable, Dict, List, Optional


def get_last_witness_hash(witness_path: str) -> str:
    """Get the last witness hash from the JSONL file. Returns '0'*64 if empty/missing."""
    default = "0" * 64
    if not os.path.exists(witness_path) or os.path.getsize(witness_path) == 0:
        return default
    try:
        with open(witness_path, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
            if lines:
                return json.loads(lines[-1]).get("witness_hash", default)
    except Exception:
        pass
    return default


def write_witness_record(
    witness_path: str,
    stream_id: str,
    revision: int,
    event_data_hex: str,
    previous_event_hash: str,
    event_hash: str,
    var_ref: Optional[str],
    last_witness_hash: str,
) -> str:
    """Write a single witness record to the JSONL file. Returns the new witness_hash."""
    witness_hash = hashlib.sha256(
        f"{last_witness_hash}:{stream_id}:{revision}:{event_hash}".encode("utf-8")
    ).hexdigest()

    witness_record = {
        "stream_id": stream_id,
        "revision": revision,
        "event_data_hex": event_data_hex,
        "previous_event_hash": previous_event_hash,
        "event_hash": event_hash,
        "var_ref": var_ref,
        "witness_prev_hash": last_witness_hash,
        "witness_hash": witness_hash,
    }

    with open(witness_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(witness_record) + "\n")
        f.flush()
        os.fsync(f.fileno())

    return witness_hash


def read_witness_records(witness_path: str) -> List[Dict[str, Any]]:
    """Read all witness records from the JSONL file. Returns empty list if missing/empty."""
    if not os.path.exists(witness_path) or os.path.getsize(witness_path) == 0:
        return []
    records = []
    with open(witness_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                records.append(json.loads(line_str))
            except Exception:
                return []  # Corrupted — caller should handle
    return records


def verify_witness_chain(
    witness_records: List[Dict[str, Any]],
    compute_event_hash_fn: Callable[..., str],
) -> tuple[bool, str]:
    """Verify the internal hash chain of JSONL witness records.

    Returns (is_valid, status_code).
    Status codes: OK, WITNESS_CORRUPTED
    """
    if not witness_records:
        return True, "OK"

    curr_prev_w_hash = "0" * 64
    stream_revs: Dict[str, int] = {}
    stream_hashes: Dict[str, str] = {}

    for rec in witness_records:
        # Check required fields
        for k in ("stream_id", "revision", "event_data_hex", "previous_event_hash",
                   "event_hash", "witness_prev_hash", "witness_hash"):
            if k not in rec:
                return False, "WITNESS_CORRUPTED"

        # Verify witness chain linkage
        if rec["witness_prev_hash"] != curr_prev_w_hash:
            return False, "WITNESS_CORRUPTED"

        # Verify witness hash
        expected_w_hash = hashlib.sha256(
            f"{rec['witness_prev_hash']}:{rec['stream_id']}:{rec['revision']}:{rec['event_hash']}".encode("utf-8")
        ).hexdigest()
        if rec["witness_hash"] != expected_w_hash:
            return False, "WITNESS_CORRUPTED"

        # Verify event hash
        try:
            data_bytes = bytes.fromhex(rec["event_data_hex"])
        except Exception:
            return False, "WITNESS_CORRUPTED"

        expected_event_hash = compute_event_hash_fn(
            stream_id=rec["stream_id"],
            revision=rec["revision"],
            event_data=data_bytes,
            previous_event_hash=rec["previous_event_hash"],
            var_ref=rec.get("var_ref"),
        )
        if rec["event_hash"] != expected_event_hash:
            return False, "WITNESS_CORRUPTED"

        # Verify sequential revisions within stream
        last_rev = stream_revs.get(rec["stream_id"], 0)
        if rec["revision"] != last_rev + 1:
            return False, "WITNESS_CORRUPTED"

        # Verify event chain within stream
        last_h = stream_hashes.get(rec["stream_id"], "0" * 64)
        if rec["previous_event_hash"] != last_h:
            return False, "WITNESS_CORRUPTED"

        stream_revs[rec["stream_id"]] = rec["revision"]
        stream_hashes[rec["stream_id"]] = rec["event_hash"]
        curr_prev_w_hash = rec["witness_hash"]

    return True, "OK"
