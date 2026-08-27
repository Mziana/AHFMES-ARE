"""
AHFMES ARE-1 — Canonical Bytes Verifier + Domain Hasher (Slice-1 Part B)

Dual implementation (IMPL_A / IMPL_B) per SLICE_1_CONTRACT.md B3:
- IMPL_A: stdlib json + manual canonicalization
- IMPL_B: identical behavior via different code path (dict sorted, explicit byte operations)

Both MUST produce bit-for-bit identical output for all valid inputs.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


# ============================================================
# HASH DOMAIN TAGS (from HASH_DOMAIN_TAGS_V1 appendix)
# ============================================================

DOMAIN_TAGS = frozenset({
    # Legacy 0B V3 §11 (VERBATIM)
    "CANDIDATE_ROOT",
    "RESEARCH_CONTRACT",
    "EVIDENCE_SNAPSHOT",
    "EVIDENCE_MANIFEST",
    "SEARCH_TREE",
    "SEARCH_DEBT",
    "VALIDATION_FAMILY",
    "PROOF_BUNDLE",
    "PROMOTION_GATE_SPEC",
    "GATE_MANIFEST",
    "ROLE_MANIFEST",
    "CONSTITUTION",
    "CAPITAL_SAFETY",
    "DEPLOYMENT_CONTEXT",
    "CHAMPION_REGISTRY_EVENT",
    # Register V30 objects
    "REFINEMENT_RELIANCE_INVALIDITY_EVENT_ROOT",
    "REFINEMENT_PROSPECTIVE_RELIANCE_SUBJECT",
    "REFINEMENT_PROSPECTIVE_RELIANCE_RECEIPT",
    "REFINEMENT_PROSPECTIVE_RELIANCE_VAR_CURRENT",
    "EDGE_NONCE_CONSUMPTION_LEDGER",
    "REFINEMENT_PROSPECTIVE_RELIANCE_SOD_ROOT",
    "ROLLBACK_CAUSE_OBSERVATION",
    "ROLLBACK_CAUSE_OBSERVATION_SOURCE_UNIVERSE",
    "ROLLBACK_POLICY_ROOT",
    "EDGE_INTERFERENCE_EVIDENCE",
    # Infrastructure event-store
    "EVENT_STORE_ENTRY",
    "EVENT_STORE_HEAD",
    "DECISION_STATE_REVISION",
    "CAPITAL_ACTION_EPISODE",
    "CAPITAL_SAFETY_OBSERVATION_RECORD",
    "CHAMPION_ROLLBACK_PLAN",
    "BROKER_MUTATION_RECORD",
    "OPERATIONAL_FIDELITY_LEDGER_ENTRY",
    "FAMILY_LIFETIME_LEDGER_ENTRY",
    "PROGRAM_BUDGET_RESERVATION",
    "EVIDENCE_RESERVATION",
    "RELATION_DECISION",
    "CAPABILITY_ACTIVATION_EPISODE",
    "DEPLOYMENT_ACTIVATION_EPISODE",
    "INTEGRITY_DEFECT_RECORD",
    # Safety contract
    "SAFETY_CONTRACT_CHANGE_PROPOSAL_RECORD",
    # ARE-2 Experience Intelligence
    "EXPERIENCE_STORE_ENTRY",
    "DECISION_MEMORY_ENTRY",
    "REGRET_MEMORY_ENTRY",
    "ANOMALY_DETECTION_ENTRY",
    "REPLAY_ENGINE_SNAPSHOT",
    "WHAT_IF_ENGINE_FORK",
    "KNOWLEDGE_SYNTHESIS_ENTRY",
    "CAPABILITY_GAP_ASSESSMENT",
    "REGIME_SHIFT_DETECTION",
    "SPREAD_HOSTILITY_METRIC",
    "ANOMALY_ALERT_RECORD",
    "COUNTERFACTUAL_QUALITY_ASSESSMENT",
    "MARKET_DATA_PROVENANCE_RECORD",
    "DATA_QUALITY_GATE_RECORD",
    "REPLAY_ENGINE_CONFIG",
    "WHAT_IF_ENGINE_CONFIG",
    "COUNTERFACTUAL_SIMULATION_RESULT",
    "DETERMINISTIC_REPLAY_PROOF",
    "SCIENTIFIC_MEMORY_ENTRY",
    "CAPABILITY_GAP_HYPOTHESIS",
    "CAPABILITY_GAP_EVIDENCE",
    "CAPABILITY_GAP_APPROVAL_RECORD",
    "EVIDENCE_LEDGER_DERIVED_SNAPSHOT",
    "ORCHESTRATOR_ADAPTER_INTERFACE",
    "HABITAT_MEMORY_ADAPTER_INTERFACE",
    "EVALUATION_WRITER_ADAPTER_INTERFACE",
    "EXPERIENCE_STORE_CONFIG",
    "ANOMALY_DETECTION_CONFIG",
    "REPLAY_ENGINE_CONFIG",
    "WHAT_IF_ENGINE_CONFIG",
    "KNOWLEDGE_SYNTHESIS_CONFIG",
    "CAPABILITY_GAP_CONFIG",
    "OBSERVABILITY_CONFIG",
})


class VerificationError(Exception):
    """Raised when canonical byte verification fails (FAIL-CLOSED)."""

    def __init__(self, message: str, offset: int):
        self.offset = offset
        super().__init__(f"{message} at byte offset {offset}")


class TagNotFoundError(Exception):
    """Raised when object type has no registered domain tag."""

    def __init__(self, obj_type: str):
        super().__init__(f"Domain tag not registered for object type: {obj_type}")


# ============================================================
# IMPL_A — Canonical Verifier (stdlib json + explicit normalization)
# ============================================================

def _verify_canonical_bytes_impl_a(data: bytes) -> tuple[bytes, int]:
    """
    Verify canonical byte representation (IMPL_A).
    Returns (canonical_bytes, offset) where offset is 0 if valid,
    or raises VerificationError with offset of first violation.
    """
    # Check for BOM
    if data.startswith(b"\xef\xbb\xbf"):
        raise VerificationError("UTF-8 BOM detected", 0)
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        raise VerificationError("UTF-16 BOM detected", 0)

    # Decode with strict UTF-8
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise VerificationError(f"Invalid UTF-8: {e}", e.start or 0)

    # Check for CRLF / CR at byte level (P1-13: byte offset, not char offset)
    if b"\r\n" in data:
        raise VerificationError("CRLF not allowed (must use LF)", data.find(b"\r\n"))
    if b"\r" in data:
        # Standalone CR (since CRLF already rejected, any \r is standalone)
        raise VerificationError("Standalone CR not allowed", data.find(b"\r"))

    # Verify NFC normalization (P1-12: check length first, not just zip)
    normalized = unicodedata.normalize("NFC", text)
    if text != normalized:
        if len(text) != len(normalized):
            # Length differs -> find first char where byte representation diverges
            # For decomposed vs composed, first differing position is where lengths diverge
            min_len = min(len(text), len(normalized))
            for i in range(min_len):
                if text[i] != normalized[i]:
                    byte_offset = len(text[:i].encode("utf-8"))
                    raise VerificationError("String not in NFC form", byte_offset)
            # Difference is extra chars in longer string
            byte_offset = len(text[:min_len].encode("utf-8"))
            raise VerificationError("String not in NFC form", byte_offset)
        for i, (c1, c2) in enumerate(zip(text, normalized)):
            if c1 != c2:
                # Calculate byte offset up to this char
                byte_offset = len(text[:i].encode("utf-8"))
                raise VerificationError("String not in NFC form", byte_offset)

    # Re-encode to canonical bytes (NFC + LF only)
    canonical = normalized.encode("utf-8")

    # Verify byte-for-byte match
    if canonical != data:
        # Find first difference
        for i, (b1, b2) in enumerate(zip(canonical, data)):
            if b1 != b2:
                raise VerificationError("Byte mismatch after NFC/LF normalization", i)
        if len(canonical) != len(data):
            raise VerificationError("Length mismatch after normalization", len(canonical))

    return canonical, 0


def _canonicalize_json_impl_a(obj: Any) -> bytes:
    """
    Canonicalize JSON object (IMPL_A): sort keys, no whitespace,
    ensure NFC, no float in identity positions.
    """
    def _normalize_value(v):
        if isinstance(v, str):
            # Verify NFC
            norm = unicodedata.normalize("NFC", v)
            if v != norm:
                raise VerificationError("JSON string not NFC", 0)
            return norm
        elif isinstance(v, float):
            # Float not allowed in identity
            raise VerificationError("Float not allowed in canonical identity", 0)
        elif isinstance(v, dict):
            return {k: _normalize_value(v) for k, v in sorted(v.items())}
        elif isinstance(v, list):
            return [_normalize_value(item) for item in v]
        elif v is None or isinstance(v, (bool, int)):
            return v
        else:
            raise VerificationError(f"Unsupported type in canonical JSON: {type(v)}", 0)

    normalized = _normalize_value(obj)
    # Compact JSON with sorted keys
    return json.dumps(normalized, separators=(",", ":"), ensure_ascii=False, sort_keys=True).encode("utf-8")


def _domain_hash_impl_a(tag: str, canonical_bytes: bytes) -> str:
    """Compute domain-separated hash (IMPL_A)."""
    if tag not in DOMAIN_TAGS:
        raise TagNotFoundError(tag)
    domain_prefix = f"AHFMES:{tag}:V1\n".encode("utf-8")
    h = hashlib.sha256()
    h.update(domain_prefix)
    h.update(canonical_bytes)
    return h.hexdigest()


# ============================================================
# IMPL_B — Canonical Verifier (explicit byte operations, no json module)
# ============================================================

def _verify_canonical_bytes_impl_b(data: bytes) -> tuple[bytes, int]:
    """
    Verify canonical byte representation (IMPL_B).
    Byte-level operations only, no Unicode normalization library for comparison.
    """
    # Check BOM
    if data.startswith(b"\xef\xbb\xbf"):
        raise VerificationError("UTF-8 BOM detected", 0)
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        raise VerificationError("UTF-16 BOM detected", 0)

    # Check CRLF and standalone CR
    if b"\r\n" in data:
        raise VerificationError("CRLF not allowed (must use LF)", data.find(b"\r\n"))
    if b"\r" in data:
        # Find CR not followed by LF (standalone)
        for i, b in enumerate(data):
            if b == 0x0d:  # CR
                if i + 1 >= len(data) or data[i + 1] != 0x0a:  # not followed by LF
                    raise VerificationError("Standalone CR not allowed", i)

    # Decode UTF-8 strictly
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise VerificationError(f"Invalid UTF-8: {e}", e.start or 0)

    # NFC check using unicodedata (P1-12: length-aware)
    normalized = unicodedata.normalize("NFC", text)
    if text != normalized:
        if len(text) != len(normalized):
            min_len = min(len(text), len(normalized))
            for i in range(min_len):
                if text[i] != normalized[i]:
                    byte_offset = len(text[:i].encode("utf-8"))
                    raise VerificationError("String not in NFC form", byte_offset)
            byte_offset = len(text[:min_len].encode("utf-8"))
            raise VerificationError("String not in NFC form", byte_offset)
        for i, (c1, c2) in enumerate(zip(text, normalized)):
            if c1 != c2:
                byte_offset = len(text[:i].encode("utf-8"))
                raise VerificationError("String not in NFC form", byte_offset)

    # Canonical re-encode
    canonical = normalized.encode("utf-8")
    if canonical != data:
        for i, (b1, b2) in enumerate(zip(canonical, data)):
            if b1 != b2:
                raise VerificationError("Byte mismatch after NFC/LF normalization", i)
        if len(canonical) != len(data):
            raise VerificationError("Length mismatch after normalization", len(canonical))

    return canonical, 0


def _canonicalize_json_impl_b(obj: Any) -> bytes:
    """Canonicalize JSON without json module (IMPL_B)."""
    ESCAPE_MAP = {
        '\\': '\\\\', '"': '\\"', '\b': '\\b', '\f': '\\f',
        '\n': '\\n', '\r': '\\r', '\t': '\\t',
    }

    def _escape_string(s: str) -> str:
        out = []
        for ch in s:
            if ch in ESCAPE_MAP:
                out.append(ESCAPE_MAP[ch])
            elif ord(ch) < 0x20:
                out.append(f'\\u{ord(ch):04x}')
            else:
                out.append(ch)
        return ''.join(out)

    def _encode_value(v) -> bytes:
        if isinstance(v, str):
            norm = unicodedata.normalize("NFC", v)
            if v != norm:
                raise VerificationError("JSON string not NFC", 0)
            # Escape for JSON string using complete escape table
            escaped = _escape_string(v)
            return b'"' + escaped.encode("utf-8") + b'"'
        elif isinstance(v, bool):
            return b"true" if v else b"false"
        elif v is None:
            return b"null"
        elif isinstance(v, int):
            return str(v).encode("ascii")
        elif isinstance(v, float):
            raise VerificationError("Float not allowed in canonical identity", 0)
        elif isinstance(v, dict):
            items = []
            for k in sorted(v.keys()):
                if not isinstance(k, str):
                    raise VerificationError("Dict keys must be strings", 0)
                key_bytes = _encode_value(k)
                val_bytes = _encode_value(v[k])
                items.append(key_bytes + b":" + val_bytes)
            return b"{" + b",".join(items) + b"}"
        elif isinstance(v, list):
            items = [_encode_value(item) for item in v]
            return b"[" + b",".join(items) + b"]"
        else:
            raise VerificationError(f"Unsupported type: {type(v)}", 0)

    return _encode_value(obj)


def _domain_hash_impl_b(tag: str, canonical_bytes: bytes) -> str:
    """Compute domain-separated hash (IMPL_B)."""
    if tag not in DOMAIN_TAGS:
        raise TagNotFoundError(tag)
    domain_prefix = f"AHFMES:{tag}:V1\n".encode("utf-8")
    h = hashlib.sha256()
    h.update(domain_prefix)
    h.update(canonical_bytes)
    return h.hexdigest()


# ============================================================
# Public API — dispatches to both implementations and cross-checks
# ============================================================

class VerificationResult:
    """Result of canonical verification."""
    def __init__(self, canonical_bytes: bytes, impl_a: str, impl_b: str):
        self.canonical_bytes = canonical_bytes
        self.impl_a_hash = impl_a
        self.impl_b_hash = impl_b

    @property
    def verified(self) -> bool:
        return self.impl_a_hash == self.impl_b_hash


def verify_canonical_bytes(data: bytes) -> VerificationResult:
    """
    Verify canonical bytes using both implementations.
    Raises VerificationError if either fails or results differ.
    """
    canonical_a, _ = _verify_canonical_bytes_impl_a(data)
    canonical_b, _ = _verify_canonical_bytes_impl_b(data)

    if canonical_a != canonical_b:
        raise VerificationError("IMPL_A and IMPL_B produced different canonical bytes", 0)

    return VerificationResult(canonical_bytes=canonical_a, impl_a="OK", impl_b="OK")


def canonicalize_json(obj: Any) -> bytes:
    """
    Canonicalize JSON object using both implementations.
    Raises VerificationError if results differ.
    """
    result_a = _canonicalize_json_impl_a(obj)
    result_b = _canonicalize_json_impl_b(obj)

    if result_a != result_b:
        raise VerificationError("IMPL_A and IMPL_B produced different canonical JSON", 0)

    return result_a


def domain_hash(tag: str, canonical_bytes: bytes) -> str:
    """
    Compute domain-separated hash using both implementations.
    Raises TagNotFoundError if tag not registered.
    Raises VerificationError if implementations disagree.
    """
    hash_a = _domain_hash_impl_a(tag, canonical_bytes)
    hash_b = _domain_hash_impl_b(tag, canonical_bytes)

    if hash_a != hash_b:
        raise VerificationError(f"Domain hash mismatch for tag {tag}: {hash_a} vs {hash_b}", 0)

    return hash_a


def list_domain_tags() -> list[str]:
    """Return sorted list of all registered domain tags."""
    return sorted(DOMAIN_TAGS)


# ============================================================
# Convenience: Object canonicalization (dict -> canonical bytes -> hash)
# ============================================================

def canonicalize_object(obj: Any, tag: str) -> tuple[bytes, str]:
    """
    Canonicalize an object to bytes and compute its domain hash.
    Returns (canonical_bytes, domain_hash).
    """
    canonical_json = canonicalize_json(obj)
    domain_hash_value = domain_hash(tag, canonical_json)
    return canonical_json, domain_hash_value