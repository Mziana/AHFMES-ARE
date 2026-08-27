"""
AHFMES ARE — Centralized Lifecycle Constants, Transitions & Invariants (DEBT-04)

Single source of truth for entity lifecycles, valid state transitions,
orthogonal dimensions, Separation of Duties (SoD) forbidden pairs, and
resolutive keywords across the ARE subsystem.

Zero external dependencies (stdlib only).
"""

from __future__ import annotations
from typing import Dict, FrozenSet, List, Set, Tuple

ZERO_HASH: str = "0" * 64

# ---------------------------------------------------------------------------
# Problem (§5)
# ---------------------------------------------------------------------------
PROBLEM_LIFECYCLES: FrozenSet[str] = frozenset({"OBSERVED", "OPEN", "DORMANT", "RETIRED"})
PROBLEM_TRANSITIONS: FrozenSet[Tuple[str, str]] = frozenset({
    ("OBSERVED", "OPEN"),
    ("OPEN", "DORMANT"),
    ("DORMANT", "OPEN"),
    ("OPEN", "RETIRED"),
    ("DORMANT", "RETIRED"),
})

# ---------------------------------------------------------------------------
# Episode (Immutable Research Episode §6)
# ---------------------------------------------------------------------------
EPISODE_LIFECYCLES: List[str] = ["PLANNED", "CONTRACTED", "RESEARCHING", "ADJUDICATED"]
EPISODE_LIFECYCLES_SET: FrozenSet[str] = frozenset(EPISODE_LIFECYCLES)
EPISODE_TRANSITIONS: FrozenSet[Tuple[str, str]] = frozenset({
    ("PLANNED", "CONTRACTED"),
    ("CONTRACTED", "RESEARCHING"),
    ("RESEARCHING", "ADJUDICATED"),
})
EPISODE_LINEAR: Set[Tuple[str, str]] = {
    ("PLANNED", "CONTRACTED"),
    ("CONTRACTED", "RESEARCHING"),
    ("RESEARCHING", "ADJUDICATED"),
}
EPISODE_DISPOSITIONS: FrozenSet[str] = frozenset({
    "NONE", "NO_RESULT", "UNRESOLVED", "CURRENTLY_NON_PREDICTABLE",
    "INSUFFICIENT_SAMPLE", "INSUFFICIENT_OBSERVABILITY", "NO_STABLE_EDGE",
    "RESOLVED_BOUNDED", "REJECTED", "INVALID", "VALIDATED_BOUNDED", "PROMOTION_ELIGIBLE"
})
EPISODE_DISPOSITION_NONE: str = "NONE"

# ---------------------------------------------------------------------------
# Hypothesis (§8)
# ---------------------------------------------------------------------------
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
HYPOTHESIS_DISPOSITIONS: FrozenSet[str] = frozenset({
    "NONE", "NO_RESULT", "REJECTED", "INVALID", "VALIDATED_BOUNDED",
    "PROMOTION_ELIGIBLE", "PROMOTED_REFERENCE"
})

# ---------------------------------------------------------------------------
# Research Contract (§9)
# ---------------------------------------------------------------------------
CONTRACT_LIFECYCLES: FrozenSet[str] = frozenset({
    "DRAFT", "PRECOMMIT_REVIEW", "LOCKED", "DISCOVERY_ACTIVE", "DISCOVERY_CLOSED",
    "VALIDATION_ACTIVE", "VALIDATION_CLOSED", "SHADOW_ACTIVE", "SHADOW_CLOSED", "ADJUDICATED"
})
CONTRACT_TRANSITIONS: FrozenSet[Tuple[str, str]] = frozenset({
    ("DRAFT", "PRECOMMIT_REVIEW"),
    ("PRECOMMIT_REVIEW", "DRAFT"),
    ("PRECOMMIT_REVIEW", "LOCKED"),
    ("LOCKED", "DISCOVERY_ACTIVE"),
    ("DISCOVERY_ACTIVE", "DISCOVERY_CLOSED"),
    ("DISCOVERY_CLOSED", "ADJUDICATED"),
    ("DISCOVERY_CLOSED", "VALIDATION_ACTIVE"),
    ("VALIDATION_ACTIVE", "VALIDATION_CLOSED"),
    ("VALIDATION_CLOSED", "ADJUDICATED"),
    ("VALIDATION_CLOSED", "SHADOW_ACTIVE"),
    ("SHADOW_ACTIVE", "SHADOW_CLOSED"),
    ("SHADOW_CLOSED", "ADJUDICATED"),
})
CONTRACT_FROZEN_SET: FrozenSet[str] = frozenset({
    "LOCKED", "DISCOVERY_ACTIVE", "DISCOVERY_CLOSED", "VALIDATION_ACTIVE",
    "VALIDATION_CLOSED", "SHADOW_ACTIVE", "SHADOW_CLOSED", "ADJUDICATED"
})

# ---------------------------------------------------------------------------
# Experiment (§15)
# ---------------------------------------------------------------------------
EXPERIMENT_LIFECYCLES: FrozenSet[str] = frozenset({
    "PLANNED", "BOUND", "READY", "RUNNING", "COMPLETED", "ADJUDICATED"
})
EXPERIMENT_TRANSITIONS: FrozenSet[Tuple[str, str]] = frozenset({
    ("PLANNED", "BOUND"),
    ("BOUND", "READY"),
    ("READY", "RUNNING"),
    ("RUNNING", "COMPLETED"),
    ("COMPLETED", "ADJUDICATED"),
})
EXPERIMENT_INTEGRITY: FrozenSet[str] = frozenset({"NOT_CHECKED", "PASS", "INVALID"})
EXPERIMENT_RESULTS: FrozenSet[str] = frozenset({
    "NONE", "NO_RESULT", "REJECTED", "VALIDATED_BOUNDED", "PROMOTION_ELIGIBLE"
})

# ---------------------------------------------------------------------------
# Candidate / Challenger (§11)
# ---------------------------------------------------------------------------
CANDIDATE_LIFECYCLES: FrozenSet[str] = frozenset({
    "DRAFT", "DISCOVERY_CANDIDATE", "FROZEN", "VALIDATION_READY", "VALIDATION_ACTIVE",
    "VALIDATION_CLOSED", "SHADOW_READY", "SHADOW_ACTIVE", "SHADOW_CLOSED",
    "ADJUDICATED", "RETIRED"
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
CANDIDATE_DISPOSITIONS: FrozenSet[str] = frozenset({
    "NONE", "REJECTED", "INVALID", "VALIDATED_BOUNDED", "PROMOTION_ELIGIBLE",
    "PROMOTED_REFERENCE", "RETIRED"
})
CANDIDATE_FROZEN_SET: FrozenSet[str] = frozenset({
    "FROZEN", "VALIDATION_READY", "VALIDATION_ACTIVE", "VALIDATION_CLOSED",
    "SHADOW_READY", "SHADOW_ACTIVE", "SHADOW_CLOSED", "ADJUDICATED", "RETIRED"
})

CHALLENGER_LIFECYCLES: FrozenSet[str] = CANDIDATE_LIFECYCLES
CHALLENGER_TRANSITIONS: FrozenSet[Tuple[str, str]] = CANDIDATE_TRANSITIONS
CHALLENGER_DISPOSITIONS: FrozenSet[str] = CANDIDATE_DISPOSITIONS

# ---------------------------------------------------------------------------
# Capability (§13)
# ---------------------------------------------------------------------------
CAPABILITY_KINDS: FrozenSet[str] = frozenset({
    "SENSOR", "DATA_SOURCE", "FEATURE_EXTRACTOR", "MODEL_CLASS",
    "POLICY_OPERATOR", "EXECUTION_PRIMITIVE", "RESEARCH_TOOL"
})
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
CAPABILITY_DISPOSITIONS: FrozenSet[str] = frozenset({
    "NONE", "REJECTED", "INVALID", "VALIDATED_BOUNDED", "PROMOTION_ELIGIBLE", "PROMOTED_REFERENCE"
})

# ---------------------------------------------------------------------------
# Graveyard
# ---------------------------------------------------------------------------
GRAVEYARD_LIFECYCLES: FrozenSet[str] = frozenset({"ACTIVE", "ARCHIVED"})
GRAVEYARD_TRANSITIONS: FrozenSet[Tuple[str, str]] = frozenset({("ACTIVE", "ARCHIVED")})

# ---------------------------------------------------------------------------
# Budget Envelope (§19/§10)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Retention & Evidence Orthogonal Dimensions (§10, §17)
# ---------------------------------------------------------------------------
RETENTIONS: FrozenSet[str] = frozenset({"ACTIVE_RECORD", "ARCHIVED_RECORD"})
EVIDENCE_PROVENANCE: FrozenSet[str] = frozenset({"UNVERIFIED", "VERIFIED", "INVALID"})
EVIDENCE_ORIGIN: FrozenSet[str] = frozenset({
    "HISTORICAL_DISCOVERY", "HISTORICAL_RESERVED", "PROSPECTIVE_STRICT_BLIND",
    "PROSPECTIVE_LIVE_FROZEN", "SHADOW_LIVE", "EXTERNAL_EVENT", "SYNTHETIC_DIAGNOSTIC"
})

# ---------------------------------------------------------------------------
# Separation of Duties (SoD) Forbidden Pairs (§16-§17, G16/G17)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Resolutive Status Keywords (G12, FIX-03)
# ---------------------------------------------------------------------------
RESOLUTIVE_KEYWORDS: FrozenSet[str] = frozenset({"APPROVED", "REJECTED", "FINAL", "CONFIRMED"})

# ---------------------------------------------------------------------------
# Domain Tag Mapping for Content Hashing
# ---------------------------------------------------------------------------
TAG_FOR: Dict[str, str] = {
    "candidate": "CANDIDATE_ROOT",
    "contract": "RESEARCH_CONTRACT",
    "problem": "SEARCH_TREE",
    "episode": "RESEARCH_CONTRACT",
    "hypothesis": "SEARCH_TREE",
    "experiment": "EVIDENCE_SNAPSHOT",
    "capability": "CANDIDATE_ROOT",
}
