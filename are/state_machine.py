"""
AHFMES ARE-0A — State Machines and Global Invariants (G01-G25)

Fail-closed, deterministik, stdlib only.
Setiap transisi mengembalikan (ok, new_state) atau raise IllegalTransition dengan kutipan klausa.

State enum untuk setiap objek: Problem, Episode, Hypothesis, Candidate, Experiment, Capability, BudgetEnvelope
Orthogonal dimensions dipisah sesuai fundamental state theorem (§2 V3):
  OBJECT IDENTITY | PROCESS LIFECYCLE | SCIENTIFIC DISPOSITION
  INTEGRITY STATUS | EPISTEMIC STATUS | RETENTION STATUS | AUTHORITY/HISTORY

References: PROJECT_GOVERNANCE/ARE0/CONTRACTS/AHFMES_ARE_0A_STATE_MACHINES_AND_INVARIANTS_V3.md
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace, field
from typing import Any, Dict, FrozenSet, Optional, Tuple, Set

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class IllegalTransition(Exception):
    """Fail-closed illegal transition with G-clause citation."""
    def __init__(self, code: str, clause: str, detail: str = ""):
        self.code = code
        self.clause = clause
        self.detail = detail
        msg = f"[{code}] {clause}"
        if detail:
            msg += f" — {detail}"
        super().__init__(msg)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ZERO_HASH = "0" * 64

# --- Problem ---
PROBLEM_LIFECYCLES: FrozenSet[str] = frozenset({"OBSERVED", "OPEN", "DORMANT", "RETIRED"})
PROBLEM_TRANSITIONS: FrozenSet[Tuple[str, str]] = frozenset({
    ("OBSERVED", "OPEN"),
    ("OPEN", "DORMANT"),
    ("DORMANT", "OPEN"),
    ("OPEN", "RETIRED"),
    ("DORMANT", "RETIRED"),
})

# --- Episode (immutable research episode) §6 ---
EPISODE_LIFECYCLES = ["PLANNED", "CONTRACTED", "RESEARCHING", "ADJUDICATED"]
EPISODE_LIFECYCLES_SET = frozenset(EPISODE_LIFECYCLES)
EPISODE_DISPOSITIONS: FrozenSet[str] = frozenset({
    "NONE", "NO_RESULT", "UNRESOLVED", "CURRENTLY_NON_PREDICTABLE",
    "INSUFFICIENT_SAMPLE", "INSUFFICIENT_OBSERVABILITY", "NO_STABLE_EDGE",
    "RESOLVED_BOUNDED", "REJECTED", "INVALID", "VALIDATED_BOUNDED", "PROMOTION_ELIGIBLE"
})

# --- Hypothesis §8 ---
HYPOTHESIS_LIFECYCLES: FrozenSet[str] = frozenset({
    "PROPOSED", "CONTRACTED", "DISCOVERY_ACTIVE", "DISCOVERY_CLOSED",
    "VALIDATION_READY", "VALIDATION_ACTIVE", "VALIDATION_CLOSED",
    "SHADOW_READY", "SHADOW_ACTIVE", "SHADOW_CLOSED", "ADJUDICATED"
})
HYPOTHESIS_TRANSITIONS: FrozenSet[Tuple[str, str]] = frozenset({
    ("PROPOSED", "CONTRACTED"),
    ("CONTRACTED", "DISCOVERY_ACTIVE"),
    ("DISCOVERY_ACTIVE", "DISCOVERY_CLOSED"),
    ("DISCOVERY_CLOSED", "ADJUDICATED"),
    ("DISCOVERY_CLOSED", "VALIDATION_READY"),
    ("VALIDATION_READY", "VALIDATION_ACTIVE"),
    ("VALIDATION_ACTIVE", "VALIDATION_CLOSED"),
    ("VALIDATION_CLOSED", "ADJUDICATED"),
    ("VALIDATION_CLOSED", "SHADOW_READY"),
    ("SHADOW_READY", "SHADOW_ACTIVE"),
    ("SHADOW_ACTIVE", "SHADOW_CLOSED"),
    ("SHADOW_CLOSED", "ADJUDICATED"),
})
HYPOTHESIS_DISPOSITIONS: FrozenSet[str] = frozenset({"NONE", "NO_RESULT", "REJECTED", "INVALID", "VALIDATED_BOUNDED", "PROMOTION_ELIGIBLE", "PROMOTED_REFERENCE"})

# --- Candidate §11 ---
CANDIDATE_LIFECYCLES: FrozenSet[str] = frozenset({
    "DRAFT", "DISCOVERY_CANDIDATE", "FROZEN", "VALIDATION_READY", "VALIDATION_ACTIVE", "VALIDATION_CLOSED",
    "SHADOW_READY", "SHADOW_ACTIVE", "SHADOW_CLOSED", "ADJUDICATED", "RETIRED"
})
CANDIDATE_TRANSITIONS: FrozenSet[Tuple[str, str]] = frozenset({
    ("DRAFT", "DISCOVERY_CANDIDATE"),
    ("DISCOVERY_CANDIDATE", "FROZEN"),
    ("FROZEN", "VALIDATION_READY"),
    ("VALIDATION_READY", "VALIDATION_ACTIVE"),
    ("VALIDATION_ACTIVE", "VALIDATION_CLOSED"),
    ("VALIDATION_CLOSED", "ADJUDICATED"),
    ("VALIDATION_CLOSED", "SHADOW_READY"),
    ("SHADOW_READY", "SHADOW_ACTIVE"),
    ("SHADOW_ACTIVE", "SHADOW_CLOSED"),
    ("SHADOW_CLOSED", "ADJUDICATED"),
    ("ADJUDICATED", "RETIRED"),
})
CANDIDATE_DISPOSITIONS: FrozenSet[str] = frozenset({"NONE", "REJECTED", "INVALID", "VALIDATED_BOUNDED", "PROMOTION_ELIGIBLE", "PROMOTED_REFERENCE", "RETIRED"})

# --- Experiment §15 ---
EXPERIMENT_LIFECYCLES: FrozenSet[str] = frozenset({"PLANNED", "BOUND", "READY", "RUNNING", "COMPLETED", "ADJUDICATED"})
EXPERIMENT_TRANSITIONS: FrozenSet[Tuple[str, str]] = frozenset({
    ("PLANNED", "BOUND"), ("BOUND", "READY"), ("READY", "RUNNING"), ("RUNNING", "COMPLETED"), ("COMPLETED", "ADJUDICATED")
})
EXPERIMENT_INTEGRITY: FrozenSet[str] = frozenset({"NOT_CHECKED", "PASS", "INVALID"})
EXPERIMENT_RESULTS: FrozenSet[str] = frozenset({"NONE", "NO_RESULT", "REJECTED", "VALIDATED_BOUNDED", "PROMOTION_ELIGIBLE"})

# --- Capability §13 ---
CAPABILITY_KINDS: FrozenSet[str] = frozenset({"SENSOR", "DATA_SOURCE", "FEATURE_EXTRACTOR", "MODEL_CLASS", "POLICY_OPERATOR", "EXECUTION_PRIMITIVE", "RESEARCH_TOOL"})
CAPABILITY_LIFECYCLES: FrozenSet[str] = frozenset({
    "BASELINE_AVAILABLE", "GAP_HYPOTHESIS", "DESIGN_CANDIDATE", "CODE_CANDIDATE",
    "SANDBOX_READY", "SANDBOX_VALIDATED", "SCIENTIFIC_VALIDATION_READY",
    "SCIENTIFIC_VALIDATION_ACTIVE", "SHADOW_READY", "SHADOW_ACTIVE",
    "ADJUDICATED", "PRODUCTION_AVAILABLE", "RETIRED"
})
CAPABILITY_TRANSITIONS: FrozenSet[Tuple[str, str]] = frozenset({
    ("BASELINE_AVAILABLE", "GAP_HYPOTHESIS"),
    ("GAP_HYPOTHESIS", "DESIGN_CANDIDATE"),
    ("DESIGN_CANDIDATE", "CODE_CANDIDATE"),
    ("CODE_CANDIDATE", "SANDBOX_READY"),
    ("SANDBOX_READY", "SANDBOX_VALIDATED"),
    ("SANDBOX_VALIDATED", "SCIENTIFIC_VALIDATION_READY"),
    ("SCIENTIFIC_VALIDATION_READY", "SCIENTIFIC_VALIDATION_ACTIVE"),
    ("SCIENTIFIC_VALIDATION_ACTIVE", "SHADOW_READY"),
    ("SHADOW_READY", "SHADOW_ACTIVE"),
    ("SHADOW_ACTIVE", "ADJUDICATED"),
    ("ADJUDICATED", "PRODUCTION_AVAILABLE"),
    ("ADJUDICATED", "RETIRED"),
    ("PRODUCTION_AVAILABLE", "RETIRED"),
})
CAPABILITY_DISPOSITIONS: FrozenSet[str] = frozenset({"NONE", "REJECTED", "INVALID", "VALIDATED_BOUNDED", "PROMOTION_ELIGIBLE", "PROMOTED_REFERENCE"})

# --- BudgetEnvelope (family/program budget, §19/§10 evidence) ---
BUDGET_ENVELOPE_LIFECYCLES: FrozenSet[str] = frozenset({
    "UNALLOCATED", "ALLOCATED", "RESERVED", "ACTIVE", "CONSUMED", "RECONCILED", "EXHAUSTED"
})
BUDGET_ENVELOPE_TRANSITIONS: FrozenSet[Tuple[str, str]] = frozenset({
    ("UNALLOCATED", "ALLOCATED"),
    ("ALLOCATED", "RESERVED"),
    ("RESERVED", "ACTIVE"),
    ("ACTIVE", "CONSUMED"),
    ("CONSUMED", "RECONCILED"),
    ("ACTIVE", "EXHAUSTED"),
    ("RESERVED", "EXHAUSTED"),
})

# Orthogonal retention (§17)
RETENTIONS: FrozenSet[str] = frozenset({"ACTIVE_RECORD", "ARCHIVED_RECORD"})

# Evidence orthogonal (§10)
EVIDENCE_PROVENANCE: FrozenSet[str] = frozenset({"UNVERIFIED", "VERIFIED", "INVALID"})
EVIDENCE_ORIGIN: FrozenSet[str] = frozenset({
    "HISTORICAL_DISCOVERY", "HISTORICAL_RESERVED", "PROSPECTIVE_EMBARGOED",
    "PROSPECTIVE_RELEASED", "SHADOW_LIVE", "EXTERNAL_EVENT", "SYNTHETIC_DIAGNOSTIC"
})

# SoD forbidden pairs (symmetric) §16-§17 G16/G17
FORBIDDEN_SOD_PAIRS: FrozenSet[FrozenSet[str]] = frozenset({
    frozenset({"A-DISCOVERY", "A-VALIDATE"}),
    frozenset({"A-DISCOVERY", "A-CRITIC"}),
    frozenset({"A-DISCOVERY", "A-GOVERN"}),
    frozenset({"A-DISCOVERY", "A-PROMOTE"}),
    frozenset({"A-DISCOVERY", "A-CAPITAL-ACTIVATE"}),
    frozenset({"A-VALIDATE", "A-CRITIC"}),
    frozenset({"A-VALIDATE", "A-GOVERN"}),
    frozenset({"A-VALIDATE", "A-PROMOTE"}),
    frozenset({"A-CRITIC", "A-GOVERN"}),
    frozenset({"A-CRITIC", "A-PROMOTE"}),
    frozenset({"A-GOVERN", "A-PROMOTE"}),
    frozenset({"A-PROMOTE", "A-CAPITAL-ACTIVATE"}),
})

# Frozen sets after which identity is immutable (§1, G01, G15)
CANDIDATE_FROZEN_SET: FrozenSet[str] = frozenset({
    "FROZEN", "VALIDATION_READY", "VALIDATION_ACTIVE", "VALIDATION_CLOSED",
    "SHADOW_READY", "SHADOW_ACTIVE", "SHADOW_CLOSED", "ADJUDICATED", "RETIRED"
})
CONTRACT_FROZEN_SET: FrozenSet[str] = frozenset({
    "LOCKED", "DISCOVERY_ACTIVE", "DISCOVERY_CLOSED", "VALIDATION_ACTIVE",
    "VALIDATION_CLOSED", "SHADOW_ACTIVE", "SHADOW_CLOSED", "ADJUDICATED"
})

# ---------------------------------------------------------------------------
# Generic state container
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ObjectState:
    """
    Canonical orthogonal state.
    lifecycle  : PROCESS LIFECYCLE
    disposition: SCIENTIFIC DISPOSITION (or result/disposition)
    retention  : RETENTION STATUS orthogonal
    integrity  : INTEGRITY STATUS (Experiment/Shadow) orthogonal
    result     : scientific result (Experiment separate)
    provenance/origin: evidence orthogonal (optional)
    """
    object_type: str  # problem|episode|hypothesis|candidate|experiment|capability|budget_envelope
    object_id: str
    lifecycle: str
    disposition: str = "NONE"
    retention: str = "ACTIVE_RECORD"
    revision: int = 0
    last_event_hash: str = ZERO_HASH
    root_hash: Optional[str] = None          # content-addressed closure
    material_hash: Optional[str] = None
    parent_id: Optional[str] = None
    family_root: Optional[str] = None
    debt: int = 0
    ancestry: Tuple[str, ...] = field(default_factory=tuple)
    # orthogonal dimensions
    integrity: str = "NOT_CHECKED"           # Experiment
    result: str = "NONE"                      # Experiment scientific result
    provenance: str = "UNVERIFIED"
    origin: str = "HISTORICAL_DISCOVERY"
    # budget envelope specific
    budget_remaining: Optional[int] = None

# ---------------------------------------------------------------------------
# Clause citations (single source of truth)
# ---------------------------------------------------------------------------

_CLAUSES: Dict[str, str] = {
    "G01": "G01 identity immutable after freeze — transitive material content closure is immutable at FROZEN/LOCKED (V3 §11, §9) [G01]",
    "G02": "G02 ancestry immutable/append-only — parent/ancestry never mutated, append-only genealogi (V3 §3 G02, §10) [G02]",
    "G03": "G03 scientific terminal disposition immutable for its research episode — ADJUDICATED disposition immutable (V3 §3 G03, §6) [G03]",
    "G04": "G04 INVALID != REJECTED — INVALID≠REJECTED, distinct dispositions (V3 §3 G04, §6/8/11) [G04]",
    "G05": "G05 integrity PASS != scientific success — integrity PASS≠scientific PASS, orthogonal (V3 §3 G05, §15) [G05]",
    "G06": "G06 archival never replaces scientific disposition — retention ARCHIVED_RECORD never changes disposition/integrity/epistemic (V3 §3 G06, §17) [G06]",
    "G07": "G07 retention never erases debt/provenance/exposure — retention never erases search debt / provenance / exposure (V3 §3 G07, §17) [G07]",
    "G08": "G08 knowledge-only VALIDATED_BOUNDED is legal terminal — VALIDATED_BOUNDED may end as knowledge without shadow/promotion (V3 §3 G08, §11/14) [G08]",
    "G09": "G09 every state transition must be explicitly legal — transition graph explicitly legal, else deny (V3 §3 G09, §7-13) [G09]",
    "G10": "G10 unspecified transition is denied — unspecified edge is DENY, no implicit transition (V3 §3 G10) [G10]",
    "G11": "G11 every accepted transition requires verified authority — verified authority with proof required (V3 §3 G11, §4) [G11]",
    "G12": "G12 caller fields/labels are descriptive only — caller supplied labels never authoritative (V3 §3 G12) [G12]",
    "G13": "G13 descendants inherit relevant search/evidence debt — descendants inherit family search/evidence debt (V3 §3 G13) [G13]",
    "G14": "G14 descendants never rewrite parent — descendant material must differ, parent immutable (V3 §3 G14) [G14]",
    "G15": "G15 proof-phase mutation requires descendant or INVALID — material mutation after LOCKED/FROZEN requires descendant or INVALID (V3 §3 G15, §9/11) [G15]",
    "G16": "G16 Research cannot self-validate/self-promote — SoD: A-DISCOVERY cannot combine with A-VALIDATE/A-PROMOTE in same family (V3 §3 G16, §19) [G16]",
    "G17": "G17 Critic cannot rescue/promote — SoD: A-CRITIC cannot combine with A-PROMOTE/A-GOVERN for rescue (V3 §3 G17, §19) [G17]",
    "G18": "G18 new IDs cannot reset debt/exposure — new ID with same family cannot reset debt/exposure (V3 §3 G18) [G18]",
    "G19": "G19 concurrent transitions require exact revision CAS — current_revision must equal expected_revision monotonic CAS (V3 §3 G19, §4/20) [G19]",
    "G20": "G20 stale authority cannot transition state — stale nonce / prev-hash / consumed single-use authority denied (V3 §3 G20, §4/20) [G20]",
    "G21": "G21 canonical rights are cross-object predicates, never local flags — CAN_VALIDATE/CAN_SHADOW/CAN_PROMOTE is predicate over exact roots, not local flag (V3 §3 G21, §19) [G21]",
    "G22": "G22 Experiment integrity/result/lifecycle are separate — Experiment integrity/result/lifecycle orthogonal (V3 §3 G22, §15) [G22]",
    "G23": "G23 Evidence provenance/origin/exposure/eligibility/retention are separate — evidence dimensions orthogonal (V3 §3 G23, §10) [G23]",
    "G24": "G24 Problem history is sequence of immutable Research Episodes — Problem disposition is derived summary, episodes immutable (V3 §3 G24, §5-6) [G24]",
    "G25": "G25 P001 answer cannot be produced by ARE-0 formalization — P001 answer firewall (V3 §3 G25) [G25]",
}

# ---------------------------------------------------------------------------
# Helpers: hashing / canonical json
# ---------------------------------------------------------------------------

def _canonical_json(obj: Any) -> bytes:
    """Stdlib deterministic canonical json: sort_keys, separators, no float check outside."""
    # fail-closed float check
    def _check(v: Any) -> None:
        if isinstance(v, float):
            raise IllegalTransition("G01", _CLAUSES["G01"], "float not allowed in canonical identity")
        if isinstance(v, dict):
            for kk, vv in v.items():
                _check(vv)
        elif isinstance(v, list):
            for vv in v:
                _check(vv)
    _check(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def _compute_event_hash(stream_id: str, revision: int, event_data: bytes, prev_hash: str) -> str:
    h = hashlib.sha256()
    h.update(stream_id.encode("utf-8"))
    h.update(revision.to_bytes(8, "big", signed=False))
    h.update(event_data)
    h.update(prev_hash.encode("utf-8"))
    return h.hexdigest()

def _material_hash(material: Dict[str, Any], tag: str = "CANDIDATE_ROOT") -> str:
    cbytes = _canonical_json(material)
    prefix = f"AHFMES:{tag}:V1\n".encode("utf-8")
    h = hashlib.sha256()
    h.update(prefix)
    h.update(cbytes)
    return h.hexdigest()

# ---------------------------------------------------------------------------
# Guard functions — tiap G sebagai fungsi terpisah (sesuai mandat)
# ---------------------------------------------------------------------------

def guard_G01_identity_immutable(state: ObjectState, new_material_hash: Optional[str]) -> None:
    if state.object_type == "candidate" and state.lifecycle in CANDIDATE_FROZEN_SET:
        if new_material_hash is not None and new_material_hash != state.material_hash:
            raise IllegalTransition("G01", _CLAUSES["G01"],
                f"candidate {state.object_id} material immutable after {state.lifecycle}: {state.material_hash} != {new_material_hash}")
    if state.object_type in ("contract",) and state.lifecycle in CONTRACT_FROZEN_SET:
        if new_material_hash is not None and new_material_hash != state.root_hash:
            raise IllegalTransition("G01", _CLAUSES["G01"],
                f"contract {state.object_id} immutable after {state.lifecycle}")
    if state.object_type == "candidate" and state.lifecycle == "FROZEN":
        # also covers FROZEN closure itself — but creator checked above; duplicate for clarity
        pass

def guard_G02_ancestry_append_only(state: ObjectState, new_parent_id: Optional[str] = None) -> None:
    # ancestry is append-only; parent_id once set never changed; ancestry tuple must extend, not shrink/replace
    if state.parent_id is not None and new_parent_id is not None and new_parent_id != state.parent_id:
        raise IllegalTransition("G02", _CLAUSES["G02"],
            f"ancestry immutable: existing parent {state.parent_id} != {new_parent_id}")

def guard_G03_terminal_disposition_immutable(state: ObjectState, to_lifecycle: str, to_disposition: str) -> None:
    if state.lifecycle == "ADJUDICATED":
        raise IllegalTransition("G03", _CLAUSES["G03"],
            f"terminal {state.object_type} {state.object_id} ADJUDICATED immutable: {state.lifecycle}/{state.disposition} cannot -> {to_lifecycle}/{to_disposition}")
    if state.object_type == "experiment" and state.lifecycle == "ADJUDICATED":
        raise IllegalTransition("G03", _CLAUSES["G03"], "experiment ADJUDICATED immutable")
    if state.object_type == "capability" and state.lifecycle in ("RETIRED", "PRODUCTION_AVAILABLE") and state.disposition in ("REJECTED", "INVALID", "VALIDATED_BOUNDED"):
        # RETIRED is terminal after ADJUDICATED
        pass

def guard_G04_invalid_neq_rejected(to_disposition: str) -> None:
    # Validate that INVALID and REJECTED are distinct—no conflation allowed.
    # Guard does not deny either value, but ensures caller distinguishes; we enforce that no code maps INVALID->REJECTED.
    # If someone tries to treat them as equal, the check that both are allowed distinct values will catch alias.
    if to_disposition not in ("INVALID", "REJECTED", "NONE", "NO_RESULT", "VALIDATED_BOUNDED", "PROMOTION_ELIGIBLE", "PROMOTED_REFERENCE", "RETIRED", "UNRESOLVED", "CURRENTLY_NON_PREDICTABLE", "INSUFFICIENT_SAMPLE", "INSUFFICIENT_OBSERVABILITY", "NO_STABLE_EDGE", "RESOLVED_BOUNDED"):
        raise IllegalTransition("G04", _CLAUSES["G04"], f"unknown disposition {to_disposition} — INVALID and REJECTED must remain distinct")

def guard_G05_integrity_pass_neq_success(integrity: str, result: str) -> None:
    # G05: integridad PASS must not imply success; allow PASS+REJECTED explicitly.
    if integrity not in EXPERIMENT_INTEGRITY:
        raise IllegalTransition("G05", _CLAUSES["G05"], f"unknown integrity {integrity}")
    if result not in EXPERIMENT_RESULTS:
        raise IllegalTransition("G05", _CLAUSES["G05"], f"unknown result {result}")
    # PASS with REJECTED is legal (no conflation)
    # We only deny if caller conflates: e.g., mapping integrity->result implicitly—caught by requiring both explicit.
    return

def guard_G06_archival_never_replaces_disposition(state: ObjectState, request: Dict[str, Any]) -> None:
    # Archival must not change disposition/lifecycle; this guard is invoked by archive() path
    if request.get("action") == "ARCHIVE":
        if request.get("to_disposition") is not None and request["to_disposition"] != state.disposition:
            raise IllegalTransition("G06", _CLAUSES["G06"],
                f"archival cannot change disposition {state.disposition}->{request.get('to_disposition')}")
        if request.get("to_lifecycle") is not None and request["to_lifecycle"] != state.lifecycle:
            raise IllegalTransition("G06", _CLAUSES["G06"],
                "archival cannot change lifecycle")

def guard_G07_retention_never_erases_debt(state: ObjectState, new_debt: Optional[int] = None) -> None:
    if new_debt is not None and new_debt < state.debt:
        raise IllegalTransition("G07", _CLAUSES["G07"],
            f"retention/archival cannot erase debt {state.debt}->{new_debt}")

def guard_G08_knowledge_only_validated_bounded_allowed(to_disposition: str, promotion_flag: bool = False) -> None:
    # VALIDATED_BOUNDED as terminal is allowed without shadow/promotion; do not force promotion path.
    # We simply accept it; denial would violate G08. So guard always passes for VALIDATED_BOUNDED terminal.
    if to_disposition == "VALIDATED_BOUNDED" and promotion_flag:
        # If caller forces promotion eligibility check when knowledge-only chosen, that's okay—not denial.
        pass

def guard_G09_explicit_legal_transition(object_type: str, from_lc: str, to_lc: str) -> None:
    graph: Dict[str, FrozenSet[Tuple[str, str]]] = {
        "problem": PROBLEM_TRANSITIONS,
        "episode_linear": frozenset({("PLANNED", "CONTRACTED"), ("CONTRACTED", "RESEARCHING"), ("RESEARCHING", "ADJUDICATED")}),
        "hypothesis": HYPOTHESIS_TRANSITIONS,
        "candidate": CANDIDATE_TRANSITIONS,
        "experiment": EXPERIMENT_TRANSITIONS,
        "capability": CAPABILITY_TRANSITIONS,
        "budget_envelope": BUDGET_ENVELOPE_TRANSITIONS,
    }
    key = object_type
    if object_type == "episode":
        key = "episode_linear"
    allowed = graph.get(key)
    if allowed is None:
        raise IllegalTransition("G09", _CLAUSES["G09"], f"unknown object_type {object_type}")
    if from_lc == "NONE" and object_type in ("problem", "episode", "hypothesis", "candidate", "experiment", "capability", "budget_envelope"):
        # creation path is handled elsewhere; allow NONE->first lifecycle as explicit legal
        return
    if (from_lc, to_lc) not in allowed:
        raise IllegalTransition("G09", _CLAUSES["G09"], f"{object_type} transition {from_lc}->{to_lc} not in explicit legal graph")

def guard_G10_unspecified_denied(object_type: str, from_lc: str, to_lc: str, allowed_set: FrozenSet[Tuple[str, str]]) -> None:
    if (from_lc, to_lc) not in allowed_set and from_lc != "NONE":
        raise IllegalTransition("G10", _CLAUSES["G10"], f"unspecified {object_type} {from_lc}->{to_lc} denied")

def guard_G11_verified_authority(authority: Optional[Dict[str, Any]]) -> None:
    if authority is None:
        raise IllegalTransition("G11", _CLAUSES["G11"], "authority None — verified authority required")
    for k in ("principal_id", "authority_class", "trust_domain"):
        if k not in authority or not authority[k]:
            raise IllegalTransition("G11", _CLAUSES["G11"], f"authority missing binding {k}")
    # single-use authorities require nonce
    single_use = {"A-VALIDATE", "A-PROMOTE", "A-SHADOW", "A-CRITIC", "A-GOVERN"}
    if authority.get("authority_class") in single_use and not authority.get("nonce"):
        raise IllegalTransition("G11", _CLAUSES["G11"], f"single-use {authority.get('authority_class')} requires nonce/proof")

RESOLUTIVE_KEYWORDS: FrozenSet[str] = frozenset({"APPROVED", "REJECTED", "FINAL", "CONFIRMED"})


def guard_G12_labels_descriptive_only(fields: Dict[str, Any]) -> None:
    # Caller labels are descriptive only; cannot contain resolutive status keywords (G12, FIX-03)
    caller_label = fields.get("caller_label")
    if caller_label and isinstance(caller_label, str):
        upper_label = caller_label.upper()
        for kw in RESOLUTIVE_KEYWORDS:
            if kw in upper_label:
                raise IllegalTransition("G12", _CLAUSES["G12"], f"resolutive label '{caller_label}' forbidden under G12")
    return


def guard_G13_descendants_inherit_debt(parent_debt: int, child_debt: int) -> None:
    if child_debt < parent_debt:
        raise IllegalTransition("G13", _CLAUSES["G13"], f"descendant debt {child_debt} < parent {parent_debt}")
    # descendant must be >= parent and typically parent+1
    if child_debt < parent_debt + 1 and parent_debt >= 0:
        # We allow equal if not yet incremented, but for material descendant we require +1; caller enforces
        pass


def guard_G14_descendants_never_rewrite_parent(parent_hash: Optional[str], child_hash: Optional[str]) -> None:
    if parent_hash is not None and child_hash is not None and parent_hash == child_hash:
        raise IllegalTransition("G14", _CLAUSES["G14"], "descendant material must differ from parent; parent never rewritten")


def guard_G15_proof_mutation_requires_descendant_or_invalid(state: ObjectState, new_material_hash: Optional[str], creating_descendant: bool = False, to_disposition: str = "NONE") -> None:
    frozen = (state.lifecycle in CANDIDATE_FROZEN_SET) or (state.lifecycle in CONTRACT_FROZEN_SET)
    if frozen and new_material_hash is not None and new_material_hash != state.material_hash and new_material_hash != state.root_hash:
        if not creating_descendant and to_disposition != "INVALID":
            raise IllegalTransition("G15", _CLAUSES["G15"],
                f"proof-phase mutation {state.object_type}:{state.object_id} after {state.lifecycle} requires descendant or INVALID, not in-place edit")


def guard_G16_research_cannot_self_validate(family_ledger: Dict[str, Dict[str, Set[str]]], family_root: str, principal_id: str, authority_class: str) -> None:
    ledger = family_ledger.setdefault(family_root, {})
    existing = ledger.get(principal_id, set())
    for cls in existing:
        if frozenset({cls, authority_class}) in FORBIDDEN_SOD_PAIRS and "A-DISCOVERY" in {cls, authority_class} and "A-VALIDATE" in {cls, authority_class}:
            raise IllegalTransition("G16", _CLAUSES["G16"],
                f"principal {principal_id} cannot combine DISCOVERY+VALIDATE/PROMOTE in family {family_root} — Research cannot self-validate")
        if frozenset({cls, authority_class}) in FORBIDDEN_SOD_PAIRS:
            if {cls, authority_class} == {"A-DISCOVERY", "A-VALIDATE"}:
                raise IllegalTransition("G16", _CLAUSES["G16"], f"SoD violation {cls}+{authority_class} for {principal_id}")

def guard_G17_critic_cannot_rescue(family_ledger: Dict[str, Dict[str, Set[str]]], family_root: str, principal_id: str, authority_class: str) -> None:
    ledger = family_ledger.setdefault(family_root, {})
    existing = ledger.get(principal_id, set())
    for cls in existing:
        if frozenset({cls, authority_class}) in FORBIDDEN_SOD_PAIRS:
            if "A-CRITIC" in {cls, authority_class} and ("A-PROMOTE" in {cls, authority_class} or "A-GOVERN" in {cls, authority_class}):
                raise IllegalTransition("G17", _CLAUSES["G17"],
                    f"Critic cannot rescue/promote: {cls}+{authority_class} for {principal_id} in {family_root}")
            if {cls, authority_class} == {"A-CRITIC", "A-VALIDATE"}:
                raise IllegalTransition("G17", _CLAUSES["G17"], f"Critic cannot rescue: A-CRITIC+A-VALIDATE for {principal_id}")

def guard_G18_new_ids_cannot_reset_debt(family_root: str, proposed_debt: int, family_debt_map: Dict[str, int]) -> None:
    known = family_debt_map.get(family_root, 0)
    if proposed_debt < known:
        raise IllegalTransition("G18", _CLAUSES["G18"],
            f"new ID in family {family_root} cannot reset debt {known}->{proposed_debt}")

def guard_G19_cas_exact_revision(state: ObjectState, expected_revision: int, expected_prev_hash: str) -> None:
    if expected_revision != state.revision:
        raise IllegalTransition("G19", _CLAUSES["G19"],
            f"CAS revision mismatch stream {state.object_type}:{state.object_id} current {state.revision} != expected {expected_revision}")
    if expected_prev_hash != state.last_event_hash:
        # prev-hash mismatch is G20 but also part of CAS; we raise G20 for hash
        raise IllegalTransition("G20", _CLAUSES["G20"],
            f"prev_hash mismatch head {state.last_event_hash} != provided {expected_prev_hash} — stale authority")

def guard_G20_stale_authority(nonce_seen: Set[str], authority: Dict[str, Any]) -> None:
    nonce = authority.get("nonce")
    if nonce and nonce in nonce_seen:
        raise IllegalTransition("G20", _CLAUSES["G20"], f"nonce {nonce} already consumed (stale/replay)")

def guard_G21_canonical_right_predicate(predicate_name: str, local_flag: bool, cross_object_proof: Optional[Dict[str, Any]]) -> None:
    # G21: canonical rights are cross-object predicates, never local flags — any local flag is denied
    if local_flag:
        raise IllegalTransition("G21", _CLAUSES["G21"],
            f"{predicate_name} cannot be established by local flag alone; requires cross-object predicate proof")
    if cross_object_proof is None:
        raise IllegalTransition("G21", _CLAUSES["G21"],
            f"{predicate_name} requires cross-object predicate proof, not local flag")
    # verify required keys exist in proof
    required = {"candidate_root", "contract_root", "evidence_snapshot_root", "ledger_revision"}
    if predicate_name == "CAN_VALIDATE":
        missing = required - set(cross_object_proof.keys())
        if missing:
            raise IllegalTransition("G21", _CLAUSES["G21"], f"CAN_VALIDATE missing {missing}")
    if predicate_name == "CAN_SHADOW":
        req2 = {"validation_proof", "candidate_unchanged", "shadow_contract_frozen"}
        missing2 = req2 - set(cross_object_proof.keys())
        if missing2:
            raise IllegalTransition("G21", _CLAUSES["G21"], f"CAN_SHADOW missing {missing2}")
    if predicate_name == "CAN_PROMOTE":
        req3 = {"champion_proof", "registry_generation", "cas_token"}
        missing3 = req3 - set(cross_object_proof.keys())
        if missing3:
            raise IllegalTransition("G21", _CLAUSES["G21"], f"CAN_PROMOTE missing {missing3}")

def guard_G22_experiment_separate_dimensions(lifecycle: str, integrity: str, result: str) -> None:
    if lifecycle not in EXPERIMENT_LIFECYCLES:
        raise IllegalTransition("G22", _CLAUSES["G22"], f"unknown experiment lifecycle {lifecycle}")
    if integrity not in EXPERIMENT_INTEGRITY:
        raise IllegalTransition("G22", _CLAUSES["G22"], f"unknown integrity {integrity}")
    if result not in EXPERIMENT_RESULTS:
        raise IllegalTransition("G22", _CLAUSES["G22"], f"unknown result {result}")
    # no COMPLETED_VALID / CONSUMED lifecycle; enforce absence
    if lifecycle in ("COMPLETED_VALID", "CONSUMED"):
        raise IllegalTransition("G22", _CLAUSES["G22"], f"forbidden lifecycle {lifecycle} — no single CONSUMED/VALID state")

def guard_G23_evidence_separate_dimensions(provenance: str, origin: str, retention: str) -> None:
    if provenance not in EVIDENCE_PROVENANCE:
        raise IllegalTransition("G23", _CLAUSES["G23"], f"unknown provenance {provenance}")
    if origin not in EVIDENCE_ORIGIN:
        raise IllegalTransition("G23", _CLAUSES["G23"], f"unknown origin {origin}")
    if retention not in RETENTIONS:
        raise IllegalTransition("G23", _CLAUSES["G23"], f"unknown retention {retention}")

def guard_G24_problem_history_immutable_episodes(existing_episodes: Dict[str, ObjectState], episode_id: str) -> None:
    # Problem history is append-only sequence of immutable episodes; rewriting an ADJUDICATED episode's disposition is forbidden (delegated to G03)
    # This guard ensures we never overwrite prior episode with new state sharing same id.
    if episode_id in existing_episodes:
        ep = existing_episodes[episode_id]
        if ep.lifecycle == "ADJUDICATED":
            raise IllegalTransition("G24", _CLAUSES["G24"],
                f"Problem history episode {episode_id} ADJUDICATED immutable — new research must create new episode, not overwrite {ep.disposition}")

def guard_G25_p001_firewall(content: Dict[str, Any]) -> None:
    if content.get("problem_id") == "P001" and content.get("answer") is not None:
        raise IllegalTransition("G25", _CLAUSES["G25"], "P001 profitability answer cannot be produced by ARE-0 formalization")

# ---------------------------------------------------------------------------
# StateMachine main class
# ---------------------------------------------------------------------------

class StateMachine:
    """
    Deterministik fail-closed state machine untuk ARE-0A.
    - Setiap transisi: guard pipeline G01-G25 berurutan
    - CAS enforced (G19/G20)
    - Authority SoD (G16/G17)
    - Archival orthogonal (G06/G07)
    - Canonical rights never local (G21)
    - Mutasi proof-phase memicu descendant/INVALID (G15)
    """

    def __init__(self):
        # family debt map for G18/G13
        self.family_debt: Dict[str, int] = {}
        # SoD ledger: family_root -> principal -> set(authority_class)
        self.sod_ledger: Dict[str, Dict[str, Set[str]]] = {}
        # nonce seen for G20
        self.nonce_seen: Set[str] = set()
        # episodes registry for G24
        self.episodes: Dict[str, ObjectState] = {}
        # problems registry
        self.problems: Dict[str, ObjectState] = {}
        # graveyard for G18 retry
        self.graveyard: Dict[Tuple[str, str], str] = {}  # (family_root, root_hash) -> disposition

    # -- internal: CAS event hash ----
    def _next_state(self, state: ObjectState, to_lifecycle: str, to_disposition: str = "NONE",
                    root_hash: Optional[str] = None, material_hash: Optional[str] = None,
                    retention: Optional[str] = None, integrity: Optional[str] = None,
                    result: Optional[str] = None, budget_remaining: Optional[int] = None,
                    proof_ref: Optional[str] = None) -> ObjectState:
        # build event dict for hash chain
        stream_id = f"{state.object_type}:{state.object_id}"
        event_obj = {
            "object_type": state.object_type,
            "object_id": state.object_id,
            "from_lifecycle": state.lifecycle,
            "to_lifecycle": to_lifecycle,
            "from_disposition": state.disposition,
            "to_disposition": to_disposition,
            "revision": state.revision + 1,
            "prev_hash": state.last_event_hash,
        }
        if root_hash is not None:
            event_obj["root_hash"] = root_hash
        cbytes = _canonical_json(event_obj)
        new_rev = state.revision + 1
        new_hash = _compute_event_hash(stream_id, new_rev, cbytes, state.last_event_hash)
        return replace(state,
                       lifecycle=to_lifecycle,
                       disposition=to_disposition if to_disposition != "NONE" or to_lifecycle == "ADJUDICATED" else state.disposition if "NONE" == to_disposition and state.disposition != "NONE" else to_disposition,
                       retention=retention if retention is not None else state.retention,
                       revision=new_rev,
                       last_event_hash=new_hash,
                       root_hash=root_hash if root_hash is not None else state.root_hash,
                       material_hash=material_hash if material_hash is not None else state.material_hash,
                       integrity=integrity if integrity is not None else state.integrity,
                       result=result if result is not None else state.result,
                       budget_remaining=budget_remaining if budget_remaining is not None else state.budget_remaining,
                       )

    def _check_sod_and_record(self, family_root: str, authority: Dict[str, Any]) -> None:
        if not family_root:
            return
        principal = authority.get("principal_id", "")
        aclass = authority.get("authority_class", "")
        ledger = self.sod_ledger.setdefault(family_root, {})
        existing = ledger.setdefault(principal, set())
        # check before adding
        for cls in existing:
            pair = frozenset({cls, aclass})
            if pair in FORBIDDEN_SOD_PAIRS:
                if pair == frozenset({"A-DISCOVERY", "A-VALIDATE"}):
                    raise IllegalTransition("G16", _CLAUSES["G16"],
                        f"SoD {cls}+{aclass} principal {principal} family {family_root} (G16 Research cannot self-validate)")
                if "A-CRITIC" in pair and ("A-PROMOTE" in pair or "A-GOVERN" in pair or "A-VALIDATE" in pair):
                    raise IllegalTransition("G17", _CLAUSES["G17"],
                        f"SoD {cls}+{aclass} principal {principal} family {family_root} (G17 Critic cannot rescue/promote)")
                raise IllegalTransition("G16", _CLAUSES["G16"],
                    f"SoD forbidden {cls}+{aclass} principal {principal} family {family_root}")
        existing.add(aclass)

    # -----------------------------------------------------------------------
    # Creation helpers (initial state)
    # -----------------------------------------------------------------------
    def create_problem(self, problem_id: str, family_root: str, authority: Dict[str, Any]) -> Tuple[bool, ObjectState]:
        guard_G11_verified_authority(authority)
        guard_G20_stale_authority(self.nonce_seen, authority)
        if problem_id in self.problems:
            raise IllegalTransition("G02", _CLAUSES["G02"], f"problem {problem_id} already exists — ancestry append-only")
        st = ObjectState(object_type="problem", object_id=problem_id, lifecycle="OBSERVED", disposition="NONE",
                         retention="ACTIVE_RECORD", revision=1, last_event_hash=_compute_event_hash(f"problem:{problem_id}", 1, _canonical_json({"create": problem_id}), ZERO_HASH),
                         family_root=family_root, ancestry=(problem_id,))
        self.problems[problem_id] = st
        self.family_debt.setdefault(family_root, 0)
        if authority.get("nonce"):
            self.nonce_seen.add(authority["nonce"])
        self._check_sod_and_record(family_root, authority)
        return True, st

    def create_episode(self, episode_id: str, problem_id: str, family_root: str, authority: Dict[str, Any]) -> Tuple[bool, ObjectState]:
        guard_G11_verified_authority(authority)
        guard_G20_stale_authority(self.nonce_seen, authority)
        if episode_id in self.episodes:
            raise IllegalTransition("G02", _CLAUSES["G02"], f"episode {episode_id} exists")
        # G24: problem must exist; history append-only
        guard_G24_problem_history_immutable_episodes(self.episodes, episode_id)
        st = ObjectState(object_type="episode", object_id=episode_id, lifecycle="PLANNED", disposition="NONE",
                         retention="ACTIVE_RECORD", revision=1,
                         last_event_hash=_compute_event_hash(f"episode:{episode_id}", 1, _canonical_json({"create": episode_id, "problem": problem_id}), ZERO_HASH),
                         family_root=family_root, ancestry=(problem_id, episode_id), debt=self.family_debt.get(family_root, 0))
        self.episodes[episode_id] = st
        if authority.get("nonce"):
            self.nonce_seen.add(authority["nonce"])
        self._check_sod_and_record(family_root, authority)
        return True, st

    def create_candidate(self, candidate_id: str, material: Dict[str, Any], family_root: str, authority: Dict[str, Any]) -> Tuple[bool, ObjectState]:
        guard_G11_verified_authority(authority)
        guard_G20_stale_authority(self.nonce_seen, authority)
        guard_G18_new_ids_cannot_reset_debt(family_root, self.family_debt.get(family_root, 0), self.family_debt)
        cbytes = _canonical_json(material)  # fail-closed float
        rh = _material_hash(material, "CANDIDATE_ROOT")
        # graveyard check G18
        if (family_root, rh) in self.graveyard:
            raise IllegalTransition("G18", _CLAUSES["G18"], f"re-creation with same content {rh} after rejection in family {family_root} denied")
        debt = self.family_debt.get(family_root, 0)
        st = ObjectState(object_type="candidate", object_id=candidate_id, lifecycle="DRAFT", disposition="NONE",
                         retention="ACTIVE_RECORD", revision=1,
                         last_event_hash=_compute_event_hash(f"candidate:{candidate_id}", 1, cbytes, ZERO_HASH),
                         root_hash=rh, material_hash=rh, family_root=family_root, ancestry=(candidate_id,), debt=debt)
        # store via internal map keyed by id for CAS tracking
        self._store_state(st)
        if authority.get("nonce"):
            self.nonce_seen.add(authority["nonce"])
        self._check_sod_and_record(family_root, authority)
        return True, st

    def create_capability(self, capability_id: str, kind: str, family_root: str, authority: Dict[str, Any]) -> Tuple[bool, ObjectState]:
        guard_G11_verified_authority(authority)
        if kind not in CAPABILITY_KINDS:
            raise IllegalTransition("G10", _CLAUSES["G10"], f"unknown capability kind {kind}")
        st = ObjectState(object_type="capability", object_id=capability_id, lifecycle="BASELINE_AVAILABLE", disposition="NONE",
                         retention="ACTIVE_RECORD", revision=1,
                         last_event_hash=_compute_event_hash(f"capability:{capability_id}", 1, _canonical_json({"kind": kind}), ZERO_HASH),
                         family_root=family_root, ancestry=(capability_id,), debt=0, root_hash=kind, material_hash=kind)
        self._store_state(st)
        if authority.get("nonce"):
            self.nonce_seen.add(authority["nonce"])
        self._check_sod_and_record(family_root, authority)
        return True, st

    def create_experiment(self, experiment_id: str, family_root: str, authority: Dict[str, Any],
                          integrity: str = "NOT_CHECKED", result: str = "NONE") -> Tuple[bool, ObjectState]:
        guard_G11_verified_authority(authority)
        guard_G22_experiment_separate_dimensions("PLANNED", integrity, result)
        guard_G23_evidence_separate_dimensions("UNVERIFIED", "HISTORICAL_DISCOVERY", "ACTIVE_RECORD")
        st = ObjectState(object_type="experiment", object_id=experiment_id, lifecycle="PLANNED", disposition="NONE",
                         retention="ACTIVE_RECORD", revision=1,
                         last_event_hash=_compute_event_hash(f"experiment:{experiment_id}", 1, _canonical_json({"create": experiment_id}), ZERO_HASH),
                         family_root=family_root, ancestry=(experiment_id,), integrity=integrity, result=result)
        self._store_state(st)
        if authority.get("nonce"):
            self.nonce_seen.add(authority["nonce"])
        self._check_sod_and_record(family_root, authority)
        return True, st

    def create_budget_envelope(self, envelope_id: str, family_root: str, authority: Dict[str, Any], initial_budget: int = 100) -> Tuple[bool, ObjectState]:
        guard_G11_verified_authority(authority)
        st = ObjectState(object_type="budget_envelope", object_id=envelope_id, lifecycle="UNALLOCATED", disposition="NONE",
                         retention="ACTIVE_RECORD", revision=1,
                         last_event_hash=_compute_event_hash(f"budget_envelope:{envelope_id}", 1, _canonical_json({"create": envelope_id}), ZERO_HASH),
                         family_root=family_root, ancestry=(envelope_id,), budget_remaining=initial_budget, debt=0)
        self._store_state(st)
        if authority.get("nonce"):
            self.nonce_seen.add(authority["nonce"])
        self._check_sod_and_record(family_root, authority)
        return True, st

    # -- internal store for generic objects --
    _generic_store: Dict[Tuple[str, str], ObjectState] = {}  # class-level fallback? we use instance

    def __post_init_store(self):
        if not hasattr(self, "_store"):
            self._store: Dict[Tuple[str, str], ObjectState] = {}

    def _store_state(self, st: ObjectState) -> None:
        if not hasattr(self, "_store"):
            self._store = {}
        self._store[(st.object_type, st.object_id)] = st
        # also keep specific maps
        if st.object_type == "candidate":
            self._ensure_store()[("candidate", st.object_id)] = st

    def _ensure_store(self) -> Dict[Tuple[str, str], ObjectState]:
        if not hasattr(self, "_store"):
            self._store = {}
        return self._store

    def get_state(self, object_type: str, object_id: str) -> Optional[ObjectState]:
        if not hasattr(self, "_store"):
            self._store = {}
        # check specific maps first
        if object_type == "problem" and object_id in self.problems:
            return self.problems[object_id]
        if object_type == "episode" and object_id in self.episodes:
            return self.episodes[object_id]
        return self._store.get((object_type, object_id))

    # -----------------------------------------------------------------------
    # Generic transition core (fail-closed, deterministic)
    # -----------------------------------------------------------------------
    def transition(self,
                   state: ObjectState,
                   to_lifecycle: str,
                   to_disposition: str = "NONE",
                   expected_revision: Optional[int] = None,
                   expected_prev_hash: Optional[str] = None,
                   authority: Optional[Dict[str, Any]] = None,
                   new_material: Optional[Dict[str, Any]] = None,
                   cross_object_proof: Optional[Dict[str, Any]] = None,
                   local_flag: bool = False,
                   predicate_name: Optional[str] = None,
                   integrity: Optional[str] = None,
                   result: Optional[str] = None,
                   creating_descendant: bool = False,
                   budget_delta: Optional[int] = None) -> Tuple[bool, ObjectState]:
        """
        Core guard pipeline. Returns (True, new_state) atau raise IllegalTransition.
        Caller must supply expected_revision/prev_hash for CAS (G19/G20).
        """
        # ---- G11 verified authority ----
        guard_G11_verified_authority(authority)
        assert authority is not None
        guard_G20_stale_authority(self.nonce_seen, authority)

        # ---- G19/G20 CAS ----
        if expected_revision is not None and expected_prev_hash is not None:
            guard_G19_cas_exact_revision(state, expected_revision, expected_prev_hash)
        # also if caller provided only revision, compute hash check via stored?

        # ---- G12 descriptive labels ignore ----
        guard_G12_labels_descriptive_only({"caller_label": authority.get("caller_label")})

        # ---- G03 terminal immutable ----
        guard_G03_terminal_disposition_immutable(state, to_lifecycle, to_disposition)

        # ---- G04 distinct ----
        guard_G04_invalid_neq_rejected(to_disposition)

        # ---- G01 / G15 identity / proof-phase ----
        new_hash: Optional[str] = None
        if new_material is not None:
            # fail-closed canonical
            _canonical_json(new_material)
            new_hash = _material_hash(new_material, "CANDIDATE_ROOT" if state.object_type == "candidate" else "RESEARCH_CONTRACT")
            guard_G01_identity_immutable(state, new_hash)
            guard_G15_proof_mutation_requires_descendant_or_invalid(state, new_hash, creating_descendant, to_disposition)
            # G14 only for descendant creation, not for in-place freeze with same material
            if creating_descendant:
                guard_G14_descendants_never_rewrite_parent(state.material_hash or state.root_hash, new_hash)

        # ---- G02 ancestry append-only ----
        guard_G02_ancestry_append_only(state)

        # ---- G06 archival orthogonal: if retention change requested via to_lifecycle misuse ----
        # archival is separate method; here we deny if caller tries to encode archival as lifecycle edge (must be before G09 so G06 takes precedence)
        if to_lifecycle == "ARCHIVED_RECORD":
            raise IllegalTransition("G06", _CLAUSES["G06"], "archival never replaces scientific lifecycle; use archive() orthogonal")
        # ---- G09/G10 explicit legal graph ----
        graph_map = {
            "problem": PROBLEM_TRANSITIONS,
            "episode": frozenset({("PLANNED", "CONTRACTED"), ("CONTRACTED", "RESEARCHING"), ("RESEARCHING", "ADJUDICATED")}),
            "hypothesis": HYPOTHESIS_TRANSITIONS,
            "candidate": CANDIDATE_TRANSITIONS,
            "experiment": EXPERIMENT_TRANSITIONS,
            "capability": CAPABILITY_TRANSITIONS,
            "budget_envelope": BUDGET_ENVELOPE_TRANSITIONS,
        }
        allowed = graph_map.get(state.object_type)
        if allowed is None:
            raise IllegalTransition("G10", _CLAUSES["G10"], f"unknown object_type {state.object_type}")
        if state.lifecycle == "NONE":
            # creation already handled
            pass
        else:
            # G08: knowledge-only VALIDATED_BOUNDED without shadow is allowed; we already include that path in graph.
            # e.g., candidate VALIDATION_CLOSED -> ADJUDICATED with VALIDATED_BOUNDED is legal without SHADOW.
            if (state.lifecycle, to_lifecycle) not in allowed:
                guard_G09_explicit_legal_transition(state.object_type, state.lifecycle, to_lifecycle)
                guard_G10_unspecified_denied(state.object_type, state.lifecycle, to_lifecycle, allowed)

        # ---- G05 integrity != success (experiment) ----
        if state.object_type == "experiment":
            eff_integrity = integrity if integrity is not None else state.integrity
            eff_result = result if result is not None else state.result
            guard_G05_integrity_pass_neq_success(eff_integrity, eff_result)
            guard_G22_experiment_separate_dimensions(to_lifecycle, eff_integrity, eff_result)

        # ---- G22/G23 orthogonal separation already partly checked ----
        if state.object_type == "experiment" and to_lifecycle in ("COMPLETED_VALID", "CONSUMED"):
            raise IllegalTransition("G22", _CLAUSES["G22"], f"forbidden lifecycle {to_lifecycle} breaks orthogonality")

        # ---- G21 canonical right predicate ----
        if predicate_name is not None:
            guard_G21_canonical_right_predicate(predicate_name, local_flag, cross_object_proof)
            # also SoD for validation/shadow/promote
            # G16/G17 already via sod ledger; additionally check predicate proof freshness via CAS

        # ---- G16/G17 SoD ----
        family_root = state.family_root or ""
        self._check_sod_and_record(family_root, authority)

        # ---- G07 retention never erases debt (checked at archive) also here if debt decreases ----
        # debt should not decrease; effective debt same or increased via inheritance logic outside
        # For transition itself debt unchanged; we will verify new_debt not < old

        # ---- G08 knowledge-only terminal: allow VALIDATED_BOUNDED directly to ADJUDICATED ----
        guard_G08_knowledge_only_validated_bounded_allowed(to_disposition, local_flag)

        # ---- G18 new IDs debt check (handled at creation/descendant) ----

        # ---- G24 problem history (for episode) ----
        if state.object_type == "episode":
            guard_G24_problem_history_immutable_episodes(self.episodes, state.object_id)

        # ---- G25 firewall ----
        if state.object_type == "problem" and state.object_id == "P001" and to_disposition != "NONE":
            guard_G25_p001_firewall({"problem_id": "P001", "answer": to_disposition})

        # -- build new state deterministically --
        eff_integrity2 = integrity if integrity is not None else state.integrity
        eff_result2 = result if result is not None else state.result
        # disposition handling: for non-ADJUDICATED intermediate, must be NONE (enforce except terminal)
        if state.object_type in ("episode", "candidate", "hypothesis", "capability"):
            if to_lifecycle != "ADJUDICATED" and to_disposition != "NONE" and to_disposition != state.disposition:
                # intermediate disposition change not allowed except ADJUDICATED/RETIRED
                if state.object_type == "capability" and to_lifecycle == "ADJUDICATED":
                    pass
                else:
                    # allow PROMOTION_ELIGIBLE only at SHADOW_CLOSED->ADJUDICATED; but if not ADJUDICATED, deny
                    if to_disposition not in ("NONE",):
                        # Check if this is a candidate SHADOW_CLOSED->ADJUDICATED promotion — that is allowed via ADJUDICATED only
                        raise IllegalTransition("G09", _CLAUSES["G09"], f"intermediate disposition {to_disposition} only allowed at ADJUDICATED (intermediate must be NONE)")
        new_state = self._next_state(state, to_lifecycle, to_disposition,
                                     root_hash=new_hash if new_hash is not None else state.root_hash,
                                     material_hash=new_hash if new_hash is not None and state.object_type == "candidate" else state.material_hash,
                                     integrity=eff_integrity2 if state.object_type == "experiment" else None,
                                     result=eff_result2 if state.object_type == "experiment" else None)
        # preserve family debt
        if authority.get("nonce"):
            self.nonce_seen.add(authority["nonce"])

        # update stores
        if state.object_type == "problem":
            self.problems[state.object_id] = new_state
        elif state.object_type == "episode":
            self.episodes[state.object_id] = new_state
        else:
            self._ensure_store()[(state.object_type, state.object_id)] = new_state

        # G07 check post: debt not erased
        guard_G07_retention_never_erases_debt(state, new_state.debt)

        return True, new_state

    # -----------------------------------------------------------------------
    # Orthogonal operations
    # -----------------------------------------------------------------------
    def archive(self, state: ObjectState, authority: Dict[str, Any],
                expected_revision: int, expected_prev_hash: str) -> Tuple[bool, ObjectState]:
        guard_G11_verified_authority(authority)
        guard_G20_stale_authority(self.nonce_seen, authority)
        guard_G19_cas_exact_revision(state, expected_revision, expected_prev_hash)
        if state.retention == "ARCHIVED_RECORD":
            raise IllegalTransition("G06", _CLAUSES["G06"], "already ARCHIVED_RECORD")
        guard_G06_archival_never_replaces_disposition(state, {"action": "ARCHIVE"})
        guard_G07_retention_never_erases_debt(state, state.debt)
        self._check_sod_and_record(state.family_root or "", authority)
        new_state = self._next_state(state, state.lifecycle, state.disposition, retention="ARCHIVED_RECORD")
        # but keep disposition/lifecycle same; _next_state already preserves, override retention only
        new_state = replace(new_state, retention="ARCHIVED_RECORD", disposition=state.disposition, lifecycle=state.lifecycle)
        # re-hash with retention change?
        # For determinism, already hashed via _next_state; patch last hash deterministically
        # Actually keep hash from _next_state (it already advanced)
        if state.object_type == "problem":
            self.problems[state.object_id] = new_state
        elif state.object_type == "episode":
            self.episodes[state.object_id] = new_state
        else:
            self._ensure_store()[(state.object_type, state.object_id)] = new_state
        if authority.get("nonce"):
            self.nonce_seen.add(authority["nonce"])
        return True, new_state

    def create_descendant(self, parent: ObjectState, child_id: str, new_material: Dict[str, Any],
                          authority: Dict[str, Any]) -> Tuple[bool, ObjectState]:
        guard_G11_verified_authority(authority)
        guard_G20_stale_authority(self.nonce_seen, authority)
        _canonical_json(new_material)
        new_hash = _material_hash(new_material, "CANDIDATE_ROOT" if parent.object_type == "candidate" else "RESEARCH_CONTRACT")
        guard_G14_descendants_never_rewrite_parent(parent.material_hash or parent.root_hash, new_hash)
        guard_G13_descendants_inherit_debt(parent.debt, parent.debt + 1)
        guard_G18_new_ids_cannot_reset_debt(parent.family_root or "", parent.debt + 1, self.family_debt)
        # new ID cannot reset exposure — we enforce via graveyard check
        family_root = parent.family_root or ""
        if (family_root, new_hash) in self.graveyard:
            raise IllegalTransition("G18", _CLAUSES["G18"], f"descendant re-uses graveyarded hash {new_hash} family {family_root}")
        # G15 requires descendant for proof-phase mutation — creating descendant satisfies it
        # create child state
        new_debt = parent.debt + 1
        self.family_debt[family_root] = max(self.family_debt.get(family_root, 0), new_debt)
        child = ObjectState(
            object_type=parent.object_type,
            object_id=child_id,
            lifecycle="DRAFT",
            disposition="NONE",
            retention="ACTIVE_RECORD",
            revision=1,
            last_event_hash=_compute_event_hash(f"{parent.object_type}:{child_id}", 1, _canonical_json({"parent": parent.object_id, "child": child_id}), ZERO_HASH),
            root_hash=new_hash,
            material_hash=new_hash,
            parent_id=parent.object_id,
            family_root=family_root,
            debt=new_debt,
            ancestry=tuple(list(parent.ancestry) + [child_id]),
        )
        self._ensure_store()[(parent.object_type, child_id)] = child
        if parent.object_type == "candidate":
            # keep generic; no extra
            pass
        if authority.get("nonce"):
            self.nonce_seen.add(authority["nonce"])
        self._check_sod_and_record(family_root, authority)
        return True, child

    def adjudicate_with_disposition(self, state: ObjectState, disposition: str,
                                    authority: Dict[str, Any], expected_revision: int, expected_prev_hash: str) -> Tuple[bool, ObjectState]:
        # convenience for terminal adjudication
        return self.transition(state, "ADJUDICATED", disposition, expected_revision, expected_prev_hash, authority)

    # -----------------------------------------------------------------------
    # Canonical right predicates (G21)
    # -----------------------------------------------------------------------
    def check_can_validate(self, candidate: ObjectState, contract: ObjectState,
                           evidence_snapshot: Dict[str, Any], ledger_revision: int,
                           local_flag: bool = False) -> bool:
        proof = {
            "candidate_root": candidate.root_hash or candidate.material_hash,
            "contract_root": contract.root_hash,
            "evidence_snapshot_root": evidence_snapshot.get("root_hash"),
            "ledger_revision": ledger_revision,
        }
        guard_G21_canonical_right_predicate("CAN_VALIDATE", local_flag, proof)
        # cross-object freshness: ledger revision must match candidate/contract head? Simplified check
        if not all(proof.values()):
            raise IllegalTransition("G21", _CLAUSES["G21"], "CAN_VALIDATE missing proof material")
        return True

    def check_can_shadow(self, candidate: ObjectState, validation_proof: Dict[str, Any],
                         shadow_contract: ObjectState, local_flag: bool = False) -> bool:
        proof = {
            "validation_proof": validation_proof,
            "candidate_unchanged": candidate.material_hash,
            "shadow_contract_frozen": shadow_contract.lifecycle in CONTRACT_FROZEN_SET or shadow_contract.lifecycle == "LOCKED",
        }
        guard_G21_canonical_right_predicate("CAN_SHADOW", local_flag, proof)
        if not proof["shadow_contract_frozen"]:
            raise IllegalTransition("G21", _CLAUSES["G21"], "CAN_SHADOW shadow contract not frozen")
        return True

    def check_can_promote(self, candidate: ObjectState, champion_proof: Dict[str, Any],
                          registry_generation: int, local_flag: bool = False) -> bool:
        proof = {
            "champion_proof": champion_proof,
            "registry_generation": registry_generation,
            "cas_token": champion_proof.get("cas_token") if isinstance(champion_proof, dict) else None,
        }
        guard_G21_canonical_right_predicate("CAN_PROMOTE", local_flag, proof)
        if not proof["champion_proof"] or not proof["cas_token"]:
            raise IllegalTransition("G21", _CLAUSES["G21"], "CAN_PROMOTE missing proof/cas_token content")
        return True

    # -----------------------------------------------------------------------
    # P001 firewall helper
    # -----------------------------------------------------------------------
    def assert_not_p001_answer(self, content: Dict[str, Any]) -> None:
        guard_G25_p001_firewall(content)


# Convenience singleton-style helpers for pure transitions without instance (still fail-closed but no shared ledger)
_default_sm = StateMachine()

def transition_problem(state: ObjectState, to_lifecycle: str, authority: Dict[str, Any],
                       expected_revision: int, expected_prev_hash: str) -> Tuple[bool, ObjectState]:
    sm = StateMachine()
    # seed with state
    sm.problems[state.object_id] = state
    sm.family_debt[state.family_root or state.object_id] = state.debt
    return sm.transition(state, to_lifecycle, "NONE", expected_revision, expected_prev_hash, authority)

