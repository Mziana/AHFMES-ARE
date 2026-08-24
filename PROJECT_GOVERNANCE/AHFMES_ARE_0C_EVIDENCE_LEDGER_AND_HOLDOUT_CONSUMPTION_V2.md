# AHFMES ARE-0C — Evidence Ledger, Holdout Consumption, Validation Reservation, and Prospective Evidence V2

Status: **SECOND-PASS CORRECTED FORMAL DESIGN / INTERNAL RED-TEAM PASS / EXTERNAL AUDIT REQUIRED / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

This is the normative ARE-0C draft for external review.

## 1. Core theorem

```text
EVIDENCE INDEPENDENCE IS A RELATION
NOT A DATASET LABEL
```

The relation is evaluated over:

```text
Evidence Snapshot
Claim Family
Research Family
Research Program
Research Contract
Candidate/Validation Batch
Ledger Revision
Disclosure History
```

## 2. Evidence Snapshot

Immutable/content-addressed:

```yaml
evidence_snapshot_id: ...
root_hash: ...
source_manifest_hash: ...
source_kind: ...
source_epoch: ...
information_time_contract_hash: ...
row_or_event_identity_contract_hash: ...
completeness_proof_hash: ...
provenance_status: VERIFIED | INVALID
```

New data => new snapshot. Never mutate old snapshot.

## 3. Orthogonal evidence dimensions

### Provenance

```text
UNVERIFIED
VERIFIED
INVALID
```

### Origin

```text
HISTORICAL_DISCOVERY
HISTORICAL_RESERVED
PROSPECTIVE_STRICT_BLIND
PROSPECTIVE_LIVE_FROZEN
SHADOW_LIVE
EXTERNAL_EVENT
SYNTHETIC_DIAGNOSTIC
```

### Exposure

Append-only EvidenceExposureEvents.

### Eligibility

Derived predicate; never caller field.

### Retention

```text
ACTIVE_RECORD
ARCHIVED_RECORD
```

## 4. Evidence roles

```text
DISCOVERY
INTERNAL_VALIDATION
INDEPENDENT_CONFIRMATION
PROSPECTIVE_CONFIRMATION
SHADOW_EVALUATION
DIAGNOSTIC_ONLY
```

Role is contract-specific, not permanent dataset identity.

## 5. Research/Claim family relations

`research_family_root` follows causal ancestry across Problem/Research Episodes/contracts/candidates/capabilities.

`claim_family_root` follows related target decision, estimand, population/economic horizon, mechanism, and outcome-informed reformulation.

Uncertainty rule:

```text
RELATED unless an independent relation gate proves otherwise
```

TD-RESEARCH cannot issue `UNRELATED` authority.

## 6. Relation Gate

Independent TD-EVIDENCE/Scientific Governance service evaluates relation claims.

Inputs:

```text
old/new claim manifests
research ancestry graph
motivation edges
outcome exposure history
timestamps/pre-existing records
```

Outputs:

```text
RELATED
UNRELATED_SUPPORTED
UNKNOWN_RELATED_FAIL_CLOSED
```

The relation decision itself is content-addressed/auditable.

## 7. Evidence Exposure Event V2

```yaml
exposure_event_id: ...
evidence_snapshot_root_hash: ...
research_program_id: ...
research_family_root: ...
claim_family_root: ...
research_contract_root_hash: ...
candidate_or_batch_root_hash: ...
validation_reservation_id: ...
role: ...
access_granularity: METADATA_ONLY | PRECOMMITTED_METRIC | AGGREGATE_OUTCOME | ROW_OUTCOME | RAW_OUTCOME
outcome_awareness: NONE | PARTIAL | BOUNDED | FULL
disclosed_metrics: [...]
disclosed_to_actor_ids: [...]
disclosed_to_trust_domains: [...]
ledger_revision_before: ...
search_tree_root_before: ...
timestamp_utc: ...
```

Actors include automated agents AND humans/auditors if their knowledge can influence later research.

## 8. Human/auditor contamination

If a human or auditor observes validation/shadow outcomes and later proposes a candidate/feature/problem reformulation, the new object's origin/motivation must reflect that exposure.

Human involvement does not magically remove adaptive contamination.

A timestamped idea that demonstrably existed before the exposure may be `EXTERNAL_PRIOR`/independent-origin, subject to relation gate.

## 9. Exposure classes

```text
E0 metadata only
E1 precommitted bounded outcome result
E2 expanded aggregate outcomes
E3 row/raw outcome access
```

Even E1 pass/fail consumes independence for adaptive related descendants.

E2/E3 create stronger contamination.

## 10. Validation Reservation V2

Before outcome access:

```yaml
reservation_id: ...
research_program_id: ...
program_budget_envelope_root_hash: ...
research_family_root: ...
claim_family_root: ...
research_contract_root_hash: ...
evidence_snapshot_root_hash: ...
ledger_revision_at_reservation: ...
validation_family_root_hash: ...
candidate_batch_root_hash: ...
primary_estimand_root_hash: ...
multiplicity_plan_root_hash: ...
search_tree_root_hash: ...
search_debt_root_hash: ...
permitted_disclosures_root_hash: ...
permitted_actor_ids: [...]
role: ...
state: RESERVED
```

Reservation creation is atomic against ledger revision and competing relevant reservations/exposures.

## 11. Independent-for predicate

```text
INDEPENDENT_FOR(E, claim, lineage, program, role, ledger_revision)
```

requires ALL:

```text
provenance verified
information-time valid
snapshot exact
lineage/claim relation evaluated
no prior relevant outcome-aware exposure before freeze
candidate/batch pre-existed disclosure
contract locked
Program/Contract search budgets valid
validation family frozen
multiplicity/sequential plan frozen
reservation fresh
permitted disclosure not exceeded
```

Unknown => false/fail closed.

## 12. Holdout consumption

No arbitrary `N uses` rule.

First outcome-aware disclosure consumes independence for related adaptive descendants in that research/claim lineage unless a precommitted sequential/batch plan already includes them.

The evidence can remain useful for discovery/diagnostic work, but cannot be called untouched confirmation for that related lineage.

## 13. Precommitted validation batch

Allowed:

```text
C1,C2,C3 + exact claims/metrics/correction frozen
-> one reservation
-> one validation family
-> result disclosure
```

Prohibited:

```text
C1 result seen
-> create C2 because of result
-> same holdout called independent
```

## 14. Contamination graph

```text
Exposure
-> Knowledge gained
-> Motivation edge
-> New hypothesis/candidate/problem/capability
-> Descendant lineage
```

Contamination follows causal information flow, not names.

## 15. Motivation classes

```text
PRECOMMITTED_BEFORE_EXPOSURE
MOTIVATED_BY_EXPOSURE
INDEPENDENT_EXTERNAL_ORIGIN
HUMAN_PRIOR_NOT_EXPOSURE_DERIVED
```

Ambiguous => MOTIVATED_BY_EXPOSURE for independence purposes.

## 16. Blinded Validation Service

Preferred:

```text
Research sends frozen request
-> Validation Service verifies reservation
-> computes only permitted metrics
-> Disclosure Gate emits bounded result
-> Ledger commits exposure atomically
```

Blinding reduces leakage but result disclosure still consumes independence for related future adaptation.

## 17. Validator oracle defense

Reservation freezes:

```text
candidate batch
metrics
populations
subgroups
query count
stopping rule
```

Extra query after seeing outcome is denied or logged as stronger exposure.

## 18. Prospective evidence is not one thing

### 18.1 PROSPECTIVE_STRICT_BLIND

Strongest class.

During epoch, research principals that could adapt the candidate are prevented from accessing outcome-bearing evidence sufficient to reconstruct candidate performance.

Candidate/batch and stopping rule are frozen before permitted result release.

Use when the architecture can enforce genuine embargo/isolation.

### 18.2 PROSPECTIVE_LIVE_FROZEN

Research system may observe public/live market information during the epoch, but:

```text
candidate identity frozen
candidate-specific evaluation cannot be used to mutate same candidate
stopping rule frozen
result disclosures logged
```

This is valuable forward evidence, but is not described as fully blind if research principals could infer outcomes from observed market paths.

Any descendant motivated by epoch observations inherits exposure/contamination.

PromotionGateSpec must state which prospective class it requires.

## 19. Prospective epoch

```yaml
prospective_epoch_id: ...
class: STRICT_BLIND | LIVE_FROZEN
start_utc: ...
end_rule_root_hash: ...
source_contract_root_hash: ...
research_program_id: ...
embargo/access_manifest_hash: ...
candidate_freeze_deadline: ...
state: SEALED | ACTIVE | CLOSED | SNAPSHOTTED | RELEASED
```

No result-driven extension of the epoch unless a precommitted sequential rule permits it.

## 20. Co-resident operational system issue

AHFMES champion may continue operating while challenger prospective proof runs.

The architecture must distinguish:

```text
Operational Brain needs market data to act
Research Brain access may be embargoed/restricted for strict prospective proof
Validation Service may record challenger counterfactual/shadow outcomes privately
```

Trust-domain separation is therefore relevant even on one physical PC.

If strict separation cannot be enforced, evidence class is downgraded to LIVE_FROZEN rather than falsely called blind.

## 21. Reservation concurrency

Atomic compare-and-append on ledger revision.

Conflicting relevant exposure/reservation => recompute eligibility.

Unused A-VALIDATE bound to older ledger snapshot becomes stale unless reservation protects exact episode.

## 22. Reservation lifecycle

```text
REQUESTED
RESERVED
ACTIVE
RESULT_COMMITTED
DISCLOSED
CLOSED
INVALID
```

Result cannot be disclosed unless corresponding exposure can commit atomically.

## 23. Derived evidence

Any transformed/subset/joined evidence snapshot keeps parent roots.

```text
rename/copy/CSV->Parquet/new ID
```

never resets exposure.

Outcome-informed subset creation is discovery and contaminates validation eligibility.

## 24. Cross-problem contamination

If P002 exists because P001 validation showed a failure mode, P002 inherits motivation/contamination even with a new Problem ID.

Unrelatedness requires independent gate proof.

## 25. News/external as-of provenance

Required where relevant:

```text
scheduled_event_time
source_publish_time
first_machine_available_time
received_time
parsed_time
decision_available_time
revision identity
source identity
```

Revised historical values cannot masquerade as live-known values.

## 26. Counterfactual quality

```text
CF-HIGH
CF-MEDIUM
CF-LOW
CF-UNOBSERVABLE
```

Quality is a gate-derived property of the counterfactual method, not Research assertion.

## 27. Evidence Ledger stream

Append-only:

```text
revision
previous_event_hash
root_hash
```

Corrections append superseding events; prior events remain visible.

## 28. Evidence Debt Summary

Non-authoritative convenience summary may show:

```text
validation episodes
outcome exposure classes
strict prospective epochs
live-frozen epochs
raw accesses
independent evidence currently available: yes/no/unknown
```

Exact authority comes from ledger proof.

## 29. Fail-closed reasons

```text
PROVENANCE_INVALID
INFORMATION_TIME_INVALID
SNAPSHOT_MISMATCH
RELATED_EXPOSURE_ALREADY_SEEN
HOLDOUT_EXHAUSTED_FOR_LINEAGE
RELATION_UNKNOWN
RESERVATION_CONFLICT
LEDGER_STALE
BATCH_NOT_PRECOMMITTED
DISCLOSURE_SCOPE_EXCEEDED
QUERY_ORACLE_LIMIT
PROSPECTIVE_EMBARGO_VIOLATION
PROSPECTIVE_CLASS_DOWNGRADE_REQUIRED
```

## 30. Second-pass attacks

Internal Red-Team attacked:

```text
1 new Evidence ID reset
2 new Problem ID reset
3 human sees holdout then suggests candidate
4 auditor result leaks into later research
5 validator queried repeatedly
6 pass/fail treated as no exposure
7 same holdout used for adaptive candidate sequence
8 claim-family relabeled unrelated
9 prospective called blind while Research sees full market path
10 candidate modified mid-prospective
11 derived subset called fresh holdout
12 same snapshot reserved concurrently
13 historical news revision leakage
```

V2 contains explicit handling for all thirteen.

## 31. Bounded residual for external audit

One difficult design surface remains intentionally exposed for audit:

> How conservative should automated `RELATED` versus `UNRELATED_SUPPORTED` semantics be for genuinely different claims sharing the same market epoch?

V2 resolves authority safety by defaulting uncertainty to RELATED. External audit may refine the relation proof schema, but Research Brain cannot choose the favorable classification.

## 32. Current disposition

```text
ARE-0C V2
= SECOND-PASS CORRECTED FORMAL DESIGN
= INTERNAL RED-TEAM PASS
= READY FOR EXTERNAL ADVERSARIAL AUDIT
= NOT CLOSED
= NO IMPLEMENTATION AUTHORITY
```
