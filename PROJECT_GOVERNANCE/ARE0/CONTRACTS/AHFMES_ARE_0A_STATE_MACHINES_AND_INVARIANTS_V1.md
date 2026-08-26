# AHFMES ARE-0A — State Machines & Invariants V1

Status: **FORMAL DESIGN DRAFT / ADVERSARIAL REVIEW REQUIRED / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

## 1. Purpose

ARE-0A defines the legal state space and cross-object invariants for the future Autonomous Research Engine.

The purpose is not to select a strategy. The purpose is to make illegal scientific transitions explicit and fail-closed.

This document is subordinate to:

`PROJECT_GOVERNANCE/AHFMES_ARE_V0_FORMALIZATION_AUTHORITY.md`

## 2. Global invariant model

All scientific objects obey these global rules:

```text
INV-G01  identity is immutable after creation
INV-G02  parent/ancestry is immutable after creation
INV-G03  terminal scientific dispositions are immutable
INV-G04  state changes require verified transition authority
INV-G05  caller-supplied state strings do not create authority
INV-G06  illegal transition => INVALID_TRANSITION / fail closed
INV-G07  descendant creation never rewrites parent history
INV-G08  evidence exposure is append-only
INV-G09  Research Brain cannot mark its own candidate VALIDATED/PROMOTED
INV-G10  proof-phase mutation creates a descendant or invalidates the candidate
INV-G11  INVALID and REJECTED are distinct terminal semantics
INV-G12  archival does not erase scientific debt, exposure, ancestry, or rejection
INV-G13  new IDs do not reset inherited search/evidence debt
INV-G14  every transition records actor, authority proof, timestamp, parent state, next state
INV-G15  missing authority evidence => transition denied
```

## 3. Problem state machine

Allowed states:

```text
OBSERVED
OPEN
RESEARCHING
UNRESOLVED
CURRENTLY_NON_PREDICTABLE
INSUFFICIENT_SAMPLE
INSUFFICIENT_OBSERVABILITY
NO_STABLE_EDGE
RESOLVED_BOUNDED
ARCHIVED
```

Legal transitions:

```text
OBSERVED -> OPEN
OPEN -> RESEARCHING
RESEARCHING -> UNRESOLVED
RESEARCHING -> CURRENTLY_NON_PREDICTABLE
RESEARCHING -> INSUFFICIENT_SAMPLE
RESEARCHING -> INSUFFICIENT_OBSERVABILITY
RESEARCHING -> NO_STABLE_EDGE
RESEARCHING -> RESOLVED_BOUNDED
UNRESOLVED -> RESEARCHING        only via new locked Research Contract
INSUFFICIENT_SAMPLE -> RESEARCHING only with materially new sample authority
INSUFFICIENT_OBSERVABILITY -> RESEARCHING only with separately proven capability change
CURRENTLY_NON_PREDICTABLE -> RESEARCHING only with materially new evidence/capability authority
NO_STABLE_EDGE -> RESEARCHING only with materially new problem/evidence authority
RESOLVED_BOUNDED -> ARCHIVED
CURRENTLY_NON_PREDICTABLE -> ARCHIVED
NO_STABLE_EDGE -> ARCHIVED
UNRESOLVED -> ARCHIVED
```

Prohibited examples:

```text
OBSERVED -> RESOLVED_BOUNDED
OPEN -> PROMOTED
CURRENTLY_NON_PREDICTABLE -> RESOLVED_BOUNDED without new research lineage
ARCHIVED -> RESEARCHING in-place
```

An archived problem can only be revisited by a **new problem lineage/descendant reference** that cites the archived parent and material new evidence.

## 4. Hypothesis state machine

Allowed states:

```text
PROPOSED
CONTRACTED
DISCOVERY_ACTIVE
DISCOVERY_CLOSED
VALIDATION_ELIGIBLE
VALIDATING
SHADOW_ELIGIBLE
SHADOW_ACTIVE
PROMOTION_ELIGIBLE
PROMOTED
REJECTED
INVALID
ARCHIVED
```

Legal forward path:

```text
PROPOSED
-> CONTRACTED
-> DISCOVERY_ACTIVE
-> DISCOVERY_CLOSED
-> VALIDATION_ELIGIBLE
-> VALIDATING
-> SHADOW_ELIGIBLE
-> SHADOW_ACTIVE
-> PROMOTION_ELIGIBLE
-> PROMOTED
```

At bounded gates, the hypothesis may instead enter:

```text
REJECTED
INVALID
```

Terminal rules:

```text
REJECTED -> ARCHIVED only
INVALID  -> ARCHIVED only
PROMOTED -> ARCHIVED only after supersession/retirement record
```

A materially changed hypothesis creates a new `hypothesis_id` with immutable parent linkage.

## 5. Research Contract state machine

Allowed states:

```text
DRAFT
PRECOMMIT_REVIEW
LOCKED
DISCOVERY_ACTIVE
DISCOVERY_CLOSED
VALIDATION_ACTIVE
VALIDATION_CLOSED
SHADOW_ACTIVE
SHADOW_CLOSED
ADJUDICATED
INVALID
ARCHIVED
```

Key invariant:

```text
LOCKED means the scientific question, primary population,
primary estimand, allowed search space, research budget,
stopping rule, evidence boundary, and authority roles
are immutable for that contract identity.
```

Any modification after `LOCKED`:

```text
material change -> descendant Research Contract
unauthorized in-place mutation -> INVALID
```

Legal lifecycle:

```text
DRAFT -> PRECOMMIT_REVIEW -> LOCKED
LOCKED -> DISCOVERY_ACTIVE -> DISCOVERY_CLOSED
DISCOVERY_CLOSED -> VALIDATION_ACTIVE -> VALIDATION_CLOSED
VALIDATION_CLOSED -> SHADOW_ACTIVE -> SHADOW_CLOSED
SHADOW_CLOSED -> ADJUDICATED
```

Not every contract must reach validation or shadow. A contract may close discovery with `NO_EDGE_FOUND` and proceed directly to `ADJUDICATED` with no candidate.

## 6. Evidence state and exposure model

Evidence does not become `VALIDATED` by itself. Evidence has **eligibility and exposure state**, distinct from claim status.

Proposed eligibility states:

```text
RAW_UNREGISTERED
REGISTERED
DISCOVERY_ELIGIBLE
DISCOVERY_CONSUMED
VALIDATION_ELIGIBLE
VALIDATION_EXPOSED
VALIDATION_CONSUMED
INDEPENDENCE_EXHAUSTED
PROSPECTIVE_NEW
INVALID_PROVENANCE
ARCHIVED
```

Critical invariant:

```text
Evidence eligibility is derived from provenance + exposure ledger + lineage relation.
It is not a caller-controlled status flag.
```

Exact quantitative consumption mechanics are deferred to ARE-0C, but ARE-0A freezes that `INDEPENDENCE_EXHAUSTED` is a legal fail-closed state and cannot be reset by renaming the dataset or minting a new evidence ID.

## 7. Candidate / Challenger state machine

Allowed states:

```text
DRAFT
DISCOVERY_CANDIDATE
FROZEN
VALIDATION_ACTIVE
VALIDATION_REJECTED
VALIDATION_INVALID
SHADOW_ELIGIBLE
SHADOW_ACTIVE
SHADOW_REJECTED
SHADOW_INVALID
PROMOTION_ELIGIBLE
PROMOTED
RETIRED
ARCHIVED
```

Critical immutable boundary:

```text
DRAFT / DISCOVERY_CANDIDATE = mutable research object
FROZEN and beyond          = immutable candidate identity
```

After `FROZEN`, any substantive change to:

```text
policy logic
model artifact
feature set
threshold
population binding
execution behavior
capability dependency
```

requires a new descendant candidate.

Example:

```text
C1 -> FROZEN -> SHADOW_ACTIVE
shadow suggests threshold change

C1 remains unchanged
C2 is created
parent = C1
reason = SHADOW_MOTIVATED_DESCENDANT
```

C2 inherits relevant evidence/search debt; it does not receive a clean scientific slate.

## 8. Capability state machine

Allowed states:

```text
AVAILABLE
RESEARCH_ONLY
CAPABILITY_GAP_HYPOTHESIS
DESIGN_CANDIDATE
CODE_CANDIDATE
SANDBOX_VALIDATED
SCIENTIFIC_VALIDATION_ELIGIBLE
SHADOW_ELIGIBLE
PROMOTION_ELIGIBLE
PRODUCTION_AVAILABLE
REJECTED
INVALID
RETIRED
```

Important:

`CAPABILITY_GAP_HYPOTHESIS` is not proof that a capability is needed.

The path:

```text
problem unresolved
-> capability gap suspected
-> capability-gap hypothesis
-> bounded proof
-> only then capability candidate
```

is required.

## 9. Epistemic state machine

Epistemic states describe claim strength, not object authority.

Allowed states:

```text
OBSERVED
SUSPECTED
DISCOVERY_CLUE
VALIDATED_BOUNDED
PRODUCTION_ELIGIBLE
REJECTED
INVALID
```

Rules:

```text
OBSERVED -> SUSPECTED
SUSPECTED -> DISCOVERY_CLUE | REJECTED | INVALID
DISCOVERY_CLUE -> VALIDATED_BOUNDED | REJECTED | INVALID
VALIDATED_BOUNDED -> PRODUCTION_ELIGIBLE | REJECTED
```

`PRODUCTION_ELIGIBLE` still does not equal `PROMOTED`; promotion is a separate Governor disposition.

## 10. Experiment state machine

Allowed states:

```text
PLANNED
BOUND_TO_LOCKED_CONTRACT
READY
RUNNING
COMPLETED_VALID
COMPLETED_REJECTING
INVALID
CONSUMED
ARCHIVED
```

Rules:

- an experiment cannot start without exact locked contract identity;
- input/evidence identities must be frozen before `READY`;
- repeated execution beyond the contract must produce `INVALID` or a new explicitly authorized experiment identity;
- a valid negative result is `COMPLETED_REJECTING`, not `INVALID`;
- after adjudication, evidence usage becomes `CONSUMED` according to ARE-0C semantics.

## 11. Shadow state machine

Allowed states:

```text
NOT_STARTED
FROZEN_READY
ACTIVE
CLOSED
ADJUDICATED
INVALID
```

Invariant:

```text
ACTIVE shadow cannot feed outcome-driven mutation back into the same candidate identity.
```

If this happens:

```text
same candidate -> INVALID
or
create descendant -> new proof lineage
```

## 12. Promotion state machine

Promotion is not a candidate field. It is an independently derived Governor disposition.

Allowed Governor dispositions:

```text
NOT_ELIGIBLE
REJECT
INVALID
PROMOTION_ELIGIBLE
PROMOTE
ROLLBACK_REQUIRED
RETIRED
```

A candidate cannot directly set any Governor disposition.

Exact numerical gates are deferred to ARE-0E, but the state separation is frozen here.

## 13. Cross-object invariants

```text
INV-X01 Problem must exist before a Research Contract may lock.
INV-X02 Hypothesis must reference exact Problem + Research Contract lineage.
INV-X03 Candidate must reference exact hypothesis/contract/search genealogy.
INV-X04 Experiment must bind exact frozen candidate + exact evidence identities.
INV-X05 Validation eligibility requires Evidence Ledger approval, not Research Brain assertion.
INV-X06 Promotion eligibility requires completed validation and required shadow lifecycle.
INV-X07 Governor disposition must be derived from verified proof records.
INV-X08 Critic cannot mutate candidate/contract/evidence.
INV-X09 Research Brain cannot issue transition authority for validation/promotion states.
INV-X10 New descendants inherit relevant multiplicity and exposure lineage.
INV-X11 Rejected/invalid parent remains immutable when descendants are created.
INV-X12 Archive operations cannot delete provenance or scientific debt.
INV-X13 P001 substantive answer cannot be written by ARE-0 formalization objects.
```

## 14. Illegal-transition handling

Any illegal or unverifiable transition must fail closed:

```text
requested transition
-> verify current identity/state
-> verify exact authority capability
-> verify prerequisites/invariants
-> verify immutable hashes/ancestry where applicable
-> if any check fails: deny transition + append audit event
```

No best-effort coercion to the nearest legal state.

## 15. Audit event minimum

Every accepted or denied transition should eventually emit an append-only event containing at least:

```text
transition_event_id
object_type
object_id
from_state
to_state
requested_by
verified_authority_id
authority_proof_hash
prerequisite_proof_refs
timestamp
result = ACCEPTED | DENIED
reason_code
```

## 16. Unresolved design questions for adversarial audit

ARE-0A is **not closed**. The next adversarial review must attempt to find:

- missing states;
- cycles that permit scientific reset;
- paths that skip proof;
- archive/reactivation loopholes;
- parent/descendant debt-reset loopholes;
- evidence eligibility reset paths;
- race/concurrency state ambiguity;
- partial failure semantics;
- rollback interactions with promoted candidates;
- capability retirement/reintroduction loopholes.

Disposition remains:

```text
ARE-0A = FORMAL DESIGN DRAFT / REVIEW REQUIRED
```
