# AHFMES ARE-0A — State Machines, Research Episodes, Orthogonal State, and Global Invariants V3

Status: **SECOND-PASS CORRECTED FORMAL DESIGN / INTERNAL RED-TEAM PASS / EXTERNAL AUDIT REQUIRED / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

This is the normative ARE-0A draft for external review. Earlier V1/V2 concepts are historical development only when they conflict with V3.

## 1. Why V3 exists

External audit found:

```text
archive/disposition collapse
evidence-state dimensional collapse
incomplete transition graphs
missing knowledge-only terminal path
concurrent transition fork
```

Internal second-pass review then found one additional semantic risk:

```text
reopening a Problem could overwrite/blur a prior bounded scientific disposition
```

V3 resolves this by separating persistent `Problem` identity from immutable `Research Episode` dispositions.

## 2. Fundamental state theorem

No single enum represents “the state of science”.

ARE uses orthogonal dimensions:

```text
OBJECT IDENTITY
PROCESS LIFECYCLE
SCIENTIFIC DISPOSITION
INTEGRITY STATUS
EPISTEMIC STATUS
RETENTION STATUS
AUTHORITY/TRANSITION HISTORY
```

For evidence, provenance/exposure/independence are additional orthogonal relations.

## 3. Global invariants

```text
G01 identity immutable after freeze
G02 ancestry immutable/append-only
G03 scientific terminal disposition immutable for its research episode
G04 INVALID != REJECTED
G05 integrity PASS != scientific success
G06 archival never replaces scientific disposition
G07 retention never erases debt/provenance/exposure
G08 knowledge-only VALIDATED_BOUNDED is a legal terminal outcome
G09 every state transition must be explicitly legal
G10 unspecified transition is denied
G11 every accepted transition requires verified authority
G12 caller fields/labels are descriptive only
G13 descendants inherit relevant search/evidence debt
G14 descendants never rewrite parent
G15 proof-phase mutation requires descendant or INVALID
G16 Research cannot self-validate/self-promote
G17 Critic cannot rescue/promote
G18 new IDs cannot reset debt/exposure
G19 concurrent transitions require exact revision CAS
G20 stale authority cannot transition state
G21 canonical rights are cross-object predicates, never local flags
G22 Experiment integrity/result/lifecycle are separate
G23 Evidence provenance/origin/exposure/eligibility/retention are separate
G24 Problem history is a sequence of immutable Research Episodes
G25 P001 answer cannot be produced by ARE-0 formalization
```

## 4. Canonical transition event

```yaml
transition_event_id: ...
object_type: ...
object_id: ...
object_root_hash: ...
expected_revision: N
expected_previous_event_hash: ...
from_lifecycle: ...
to_lifecycle: ...
from_disposition: ...
to_disposition: ...
verified_authority_id: ...
authority_proof_hash: ...
prerequisite_proof_refs: [...]
actor_principal_id: ...
actor_trust_domain: ...
timestamp_utc: ...
result: ACCEPTED | DENIED
reason_code: ...
```

Atomic rule:

```text
current_revision must equal expected_revision
current_last_event_hash must equal expected_previous_event_hash
all prerequisites/authority must still be current
then transition + authority consumption commit atomically
```

Otherwise deny.

## 5. Persistent Problem object

A Problem represents a phenomenon/question domain, not one experiment result.

Fields include:

```text
problem_id
problem_root_hash
created_from
problem_statement
research_family_root
known_failed_hypotheses
research_episode_ids
retention_status
```

Problem lifecycle:

```text
OBSERVED
OPEN
DORMANT
RETIRED
```

A Problem does not carry one mutable terminal scientific disposition that gets overwritten after each new investigation.

## 6. Research Episode object

Every bounded investigation of a Problem creates an immutable episode.

Lifecycle:

```text
PLANNED
CONTRACTED
RESEARCHING
ADJUDICATED
```

Episode disposition:

```text
NO_RESULT
UNRESOLVED
CURRENTLY_NON_PREDICTABLE
INSUFFICIENT_SAMPLE
INSUFFICIENT_OBSERVABILITY
NO_STABLE_EDGE
RESOLVED_BOUNDED
REJECTED
INVALID
VALIDATED_BOUNDED
PROMOTION_ELIGIBLE
```

Once `ADJUDICATED`, the episode disposition is immutable.

New research:

```text
Problem P001
  Episode E1 -> REJECTED
  Episode E2 -> NO_STABLE_EDGE
  Episode E3 -> VALIDATED_BOUNDED
```

E3 never rewrites E1/E2.

Problem-level “current understanding” is a derived summary over episodes, not authority.

## 7. Problem lifecycle transitions

```text
OBSERVED -> OPEN
OPEN -> DORMANT
DORMANT -> OPEN       only when a new Research Episode/Contract is authorized
OPEN -> RETIRED       governance decision
DORMANT -> RETIRED    governance decision
```

Research disposition lives in episodes.

Archival is separate retention status.

## 8. Hypothesis object

Lifecycle:

```text
PROPOSED
CONTRACTED
DISCOVERY_ACTIVE
DISCOVERY_CLOSED
VALIDATION_READY
VALIDATION_ACTIVE
VALIDATION_CLOSED
SHADOW_READY
SHADOW_ACTIVE
SHADOW_CLOSED
ADJUDICATED
```

Disposition:

```text
NONE
NO_RESULT
REJECTED
INVALID
VALIDATED_BOUNDED
PROMOTION_ELIGIBLE
PROMOTED_REFERENCE
```

`PROMOTED_REFERENCE` records that a separate Champion Registry transaction succeeded; it is not self-issued by the Hypothesis.

Legal graph:

```text
PROPOSED -> CONTRACTED
CONTRACTED -> DISCOVERY_ACTIVE
DISCOVERY_ACTIVE -> DISCOVERY_CLOSED
DISCOVERY_CLOSED -> ADJUDICATED(NO_RESULT)
DISCOVERY_CLOSED -> VALIDATION_READY
VALIDATION_READY -> VALIDATION_ACTIVE
VALIDATION_ACTIVE -> VALIDATION_CLOSED
VALIDATION_CLOSED -> ADJUDICATED(REJECTED|INVALID|VALIDATED_BOUNDED)
VALIDATION_CLOSED -> SHADOW_READY
SHADOW_READY -> SHADOW_ACTIVE
SHADOW_ACTIVE -> SHADOW_CLOSED
SHADOW_CLOSED -> ADJUDICATED(REJECTED|INVALID|VALIDATED_BOUNDED|PROMOTION_ELIGIBLE)
```

No reverse edges.

## 9. Research Contract object

Lifecycle:

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
```

Legal graph:

```text
DRAFT -> PRECOMMIT_REVIEW
PRECOMMIT_REVIEW -> DRAFT                pre-lock correction only
PRECOMMIT_REVIEW -> LOCKED
LOCKED -> DISCOVERY_ACTIVE
DISCOVERY_ACTIVE -> DISCOVERY_CLOSED
DISCOVERY_CLOSED -> ADJUDICATED          no-candidate path
DISCOVERY_CLOSED -> VALIDATION_ACTIVE    fresh reservation/authority
VALIDATION_ACTIVE -> VALIDATION_CLOSED
VALIDATION_CLOSED -> ADJUDICATED         no-shadow path
VALIDATION_CLOSED -> SHADOW_ACTIVE       shadow contract frozen
SHADOW_ACTIVE -> SHADOW_CLOSED
SHADOW_CLOSED -> ADJUDICATED
```

Material mutation after LOCKED:

```text
current contract INVALID
or
new descendant contract
```

A descendant inherits family-level research debt; it is not a budget reset.

## 10. Evidence object

Evidence does NOT have a single master lifecycle enum.

Immutable identity:

```text
evidence snapshot root
source manifest root
information-time contract root
source epoch
```

Provenance:

```text
UNVERIFIED
VERIFIED
INVALID
```

Origin:

```text
HISTORICAL_DISCOVERY
HISTORICAL_RESERVED
PROSPECTIVE_EMBARGOED
PROSPECTIVE_RELEASED
SHADOW_LIVE
EXTERNAL_EVENT
SYNTHETIC_DIAGNOSTIC
```

Exposure:

```text
append-only EvidenceExposureEvents
```

Eligibility:

```text
derived predicate from exact ledger revision + claim/research lineage
```

Retention:

```text
ACTIVE_RECORD
ARCHIVED_RECORD
```

No reclassification resets exposure.

## 11. Candidate object

Lifecycle:

```text
DRAFT
DISCOVERY_CANDIDATE
FROZEN
VALIDATION_READY
VALIDATION_ACTIVE
VALIDATION_CLOSED
SHADOW_READY
SHADOW_ACTIVE
SHADOW_CLOSED
ADJUDICATED
RETIRED
```

Disposition:

```text
NONE
REJECTED
INVALID
VALIDATED_BOUNDED
PROMOTION_ELIGIBLE
PROMOTED_REFERENCE
RETIRED
```

Legal graph:

```text
DRAFT -> DISCOVERY_CANDIDATE
DISCOVERY_CANDIDATE -> FROZEN
FROZEN -> VALIDATION_READY
VALIDATION_READY -> VALIDATION_ACTIVE
VALIDATION_ACTIVE -> VALIDATION_CLOSED
VALIDATION_CLOSED -> ADJUDICATED
VALIDATION_CLOSED -> SHADOW_READY
SHADOW_READY -> SHADOW_ACTIVE
SHADOW_ACTIVE -> SHADOW_CLOSED
SHADOW_CLOSED -> ADJUDICATED
ADJUDICATED -> RETIRED
```

At FROZEN, transitive material content closure is immutable.

Mutation creates descendant.

## 12. Candidate promotion reference

Promotion is NOT a lifecycle edge of the Candidate.

If the Champion Registry later atomically promotes the candidate, a separate append-only reference event may update the candidate's historical disposition to `PROMOTED_REFERENCE` only if:

```text
Champion Registry transition proof exists
exact candidate root matches
registry generation transition is committed
```

This event cannot create promotion itself; it mirrors already-completed authority.

## 13. Capability object

Kind:

```text
SENSOR
DATA_SOURCE
FEATURE_EXTRACTOR
MODEL_CLASS
POLICY_OPERATOR
EXECUTION_PRIMITIVE
RESEARCH_TOOL
```

Lifecycle:

```text
BASELINE_AVAILABLE
GAP_HYPOTHESIS
DESIGN_CANDIDATE
CODE_CANDIDATE
SANDBOX_READY
SANDBOX_VALIDATED
SCIENTIFIC_VALIDATION_READY
SCIENTIFIC_VALIDATION_ACTIVE
SHADOW_READY
SHADOW_ACTIVE
ADJUDICATED
PRODUCTION_AVAILABLE
RETIRED
```

Disposition:

```text
NONE
REJECTED
INVALID
VALIDATED_BOUNDED
PROMOTION_ELIGIBLE
PROMOTED_REFERENCE
```

A Problem being unresolved cannot directly enter `GAP_HYPOTHESIS`; an explicit capability-gap Research Episode must support it.

## 14. Epistemic Claim object

States:

```text
OBSERVED
SUSPECTED
DISCOVERY_CLUE
VALIDATED_BOUNDED
PRODUCTION_ELIGIBLE
REJECTED
INVALID
```

Legal graph:

```text
OBSERVED -> SUSPECTED
SUSPECTED -> DISCOVERY_CLUE | REJECTED | INVALID
DISCOVERY_CLUE -> VALIDATED_BOUNDED | REJECTED | INVALID
VALIDATED_BOUNDED -> PRODUCTION_ELIGIBLE | REJECTED
```

`VALIDATED_BOUNDED` may end permanently as knowledge.

## 15. Experiment object

Lifecycle:

```text
PLANNED
BOUND
READY
RUNNING
COMPLETED
ADJUDICATED
```

Integrity:

```text
NOT_CHECKED
PASS
INVALID
```

Scientific result:

```text
NONE
NO_RESULT
REJECTED
VALIDATED_BOUNDED
PROMOTION_ELIGIBLE
```

No `COMPLETED_VALID`; no `CONSUMED` lifecycle state.

Evidence consumption belongs to Evidence Ledger.

## 16. Shadow Episode object

Lifecycle:

```text
PLANNED
FROZEN_READY
ACTIVE
CLOSED
ADJUDICATED
```

Integrity:

```text
NOT_CHECKED
PASS
INVALID
```

Disposition:

```text
NONE
REJECTED
VALIDATED_BOUNDED
PROMOTION_ELIGIBLE
```

Any outcome-driven mutation during ACTIVE invalidates the same candidate's shadow claim or creates a descendant.

## 17. Retention / archive theorem

Retention is universally orthogonal:

```text
retention_status = ACTIVE_RECORD | ARCHIVED_RECORD
```

Archiving NEVER changes:

```text
disposition
integrity
epistemic status
evidence exposure
search debt
genealogy
authority history
champion history
```

There is no semantic `REJECTED -> ARCHIVED` edge.

## 18. Tombstone rule

V3 removes `TOMBSTONED_RECORD` from normal scientific lifecycle.

If future legal/privacy/corruption handling requires a tombstone, it must be a separate governance feature that preserves hashes/audit references and cannot be used to erase scientific debt. It is not part of ARE-0A normal scientific state.

## 19. Canonical global predicates

Validation right:

```text
CAN_VALIDATE
= candidate exact frozen root
+ locked contract exact root
+ fresh Evidence Ledger eligibility
+ within family/program research budget
+ valid multiplicity plan
+ principal separation
+ fresh A-VALIDATE
```

Shadow right:

```text
CAN_SHADOW
= bounded validation proof
+ unchanged candidate
+ frozen shadow contract
+ fresh evidence/search snapshots
```

Promotion eligibility:

```text
CAN_BE_PROMOTION_ELIGIBLE
= comparative proof bundle passes precommitted Governor gates
+ Critic bounded disposition
+ Capital Safety pass
+ current champion context verified
```

Actual promotion:

```text
CAN_PROMOTE
= all above
+ fresh single-use A-PROMOTE
+ exact champion registry generation
+ atomic compare-and-swap
```

No local flag can establish any predicate.

## 20. Concurrency invariants

All authority-sensitive streams require:

```text
monotonic revision
previous-event hash
expected revision on write
atomic compare-and-append
```

Stale concurrent write:

```text
DENY_STALE_TRANSITION
```

No “last writer wins” for scientific authority.

## 21. Partial failure

A transition is authoritative only if one committed transaction proves:

```text
authority verified
single-use authority consumed if applicable
state event appended
revision advanced
ledger/registry effects committed where required
```

On uncertain partial persistence:

```text
canonical state does NOT advance
```

unless recovery can prove the transaction committed.

## 22. Derived summaries are non-authoritative

UI/cache fields such as:

```text
current_problem_status
candidate_status
validated
promoted
archive_state
```

may be derived for convenience.

They never replace canonical event/authority predicates.

## 23. External adversarial tests

Required attack families:

```text
archive a REJECTED episode and attempt to erase rejection
open new episode and overwrite previous disposition
new Problem ID to reset family debt
new Evidence ID to reset exposure
candidate FROZEN mutation
candidate direct promotion flag
knowledge-only claim forced to shadow
Experiment integrity PASS interpreted as scientific PASS
concurrent candidate transitions
stale authority transition
partial authority/state persistence
capability gap asserted from failure alone
retired capability reintroduced as clean research family
```

Expected result: preserved history or fail closed.

## 24. Current disposition

```text
ARE-0A V3
= SECOND-PASS CORRECTED FORMAL DESIGN
= INTERNAL RED-TEAM PASS
= READY FOR EXTERNAL ADVERSARIAL AUDIT
= NOT CLOSED
= NO IMPLEMENTATION AUTHORITY
```
