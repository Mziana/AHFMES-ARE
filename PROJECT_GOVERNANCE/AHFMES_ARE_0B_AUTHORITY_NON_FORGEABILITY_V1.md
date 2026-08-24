# AHFMES ARE-0B — Authority / Non-Forgeability Contract V1

Status: **FORMAL DESIGN DRAFT / ADVERSARIAL REVIEW REQUIRED / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

## 1. Purpose

ARE-0B defines how scientific authority is represented so that Research Brain, candidate code, callers, serialized objects, or reconstructed state cannot forge `VALIDATED`, `PROMOTION_ELIGIBLE`, `PROMOTED`, evidence eligibility, or capital authority.

This is the ARE analogue of the class of failure previously discovered in PPR where caller-constructible membership/authority objects could have substituted for exact frozen authority.

Core rule:

```text
DATA / CLAIM OBJECT
!=
VERIFIED AUTHORITY CAPABILITY
```

## 2. Threat model

Assume future ARE components may accidentally or intentionally attempt any of the following:

```text
1. write candidate.status = VALIDATED
2. write candidate.promotion_eligible = true
3. reconstruct a token/sentinel that looks authoritative
4. create a new object ID to bypass inherited restrictions
5. replay an old valid authority in a new context
6. substitute a compatible-looking evidence set
7. copy a hash/string without proving the bound object set
8. mutate an object after proof but preserve its visible ID
9. forge Critic/Governor output through caller-controlled payload
10. promote by deserializing a previously accepted state
```

ARE design must fail closed against all ten classes.

## 3. Authority classes

Authority is separated into non-interchangeable classes:

```text
A-CREATE       object creation authority
A-LOCK         Research Contract lock authority
A-DISCOVERY    bounded discovery execution authority
A-VALIDATE     validation execution authority
A-SHADOW       frozen shadow authority
A-CRITIC       adversarial review authority
A-GOVERN       adjudication authority
A-PROMOTE      promotion authority
A-ROLLBACK     rollback/retirement authority
A-CAPABILITY   capability/code candidate progression authority
```

Possession of one class never implies another.

Examples:

```text
A-DISCOVERY does not imply A-VALIDATE
A-VALIDATE does not imply A-PROMOTE
A-CRITIC does not imply A-PROMOTE
A-GOVERN does not imply broker execution authority
```

## 4. Verified Authority Record (VAR)

Future implementation should derive transitions from a verified authority record rather than caller-supplied booleans.

Conceptual immutable record:

```yaml
authority_id: VAR-...
authority_class: A-VALIDATE
issued_for:
  object_type: CANDIDATE
  object_id: C184
  object_content_hash: sha256:...
bound_contract_id: RC-P001-007
bound_contract_hash: sha256:...
bound_evidence_manifest_hash: sha256:...
bound_genealogy_root: ...
allowed_from_state: FROZEN
allowed_to_state: VALIDATION_ACTIVE
issued_by_gate: GATE-VALIDATION-ELIGIBILITY-V1
prerequisite_proofs:
  - ...
issued_at: ...
expires_or_single_use: SINGLE_USE
signature_or_verifier_proof: ...
```

The exact cryptographic mechanism is not frozen in V1, but the semantic binding is mandatory.

## 5. Authority binding invariants

```text
INV-A01 authority is bound to exact object ID + exact content hash
INV-A02 authority is bound to exact Research Contract identity/hash
INV-A03 authority is bound to exact evidence manifest where evidence matters
INV-A04 authority is bound to exact genealogy context
INV-A05 authority is bound to one transition class
INV-A06 authority cannot be widened by caller parameters
INV-A07 authority cannot be reused after substantive object mutation
INV-A08 stale authority cannot validate a descendant unless explicitly re-issued
INV-A09 authority issuance requires prerequisite proof, not status labels
INV-A10 promotion authority is separate from scientific claim state
INV-A11 production/broker authority is separate from promotion eligibility
INV-A12 failed verification => deny + audit event
```

## 6. Non-authoritative fields

The following fields are always descriptive/cache/UI only unless independently verified from canonical gate outputs:

```text
status
validated
promotion_eligible
promoted
passed
confidence
critic_pass
shadow_pass
production_ready
authority_token string copied from storage
human-readable verdict text
```

They may mirror a verified state but can never create it.

## 7. State derivation rule

Authoritative state should be computed from append-only verified transition records.

Conceptually:

```text
canonical_state(object)
= fold(valid_transition_events_for_exact_identity)
```

Not:

```text
canonical_state(object)
= object.status
```

A serialized object's status field is never the source of truth by itself.

## 8. Content-addressed immutability

At `FROZEN` or equivalent proof boundary, exact content identity must be bound.

Candidate identity should include or reference immutable hashes for all material components:

```text
policy specification
model artifact
feature schema
thresholds/configuration
execution semantics
capability dependencies
Research Contract
population/evidence manifest
```

If any material content changes, the old authority becomes inapplicable and a descendant identity is required.

## 9. Descendant inheritance rule

A descendant may inherit lineage debt and references, but never inherited proof authority automatically.

```text
C1 VALIDATED
-> C2 created from C1

C2 inherits:
- parent lineage
- search multiplicity debt
- evidence exposure debt
- rejected/accepted ancestry references

C2 does NOT inherit:
- C1 validation authority
- C1 shadow authority
- C1 promotion authority
```

Each proof gate must re-issue authority for C2 if eligible.

## 10. Evidence eligibility authority

Evidence eligibility must be computed by the Evidence Ledger gate.

Research Brain may request:

```text
"use EV-W2-X for validation"
```

but only an Evidence Eligibility Gate may issue:

```text
A-VALIDATE evidence authorization
```

after checking:

```text
provenance
as-of integrity
prior exposure
lineage relation
holdout exhaustion
claim-family relation
contract compatibility
```

Exact consumption mechanics are deferred to ARE-0C.

## 11. Research Contract lock authority

`LOCKED` cannot be created by setting `contract.status = LOCKED`.

A valid lock requires a gate to verify at least:

```text
question frozen
primary population frozen
primary estimand frozen
search family frozen
budget frozen
stopping rule frozen
evidence roles frozen
prohibited information frozen
critic/governor roles frozen
```

Then issue a single transition authority:

```text
DRAFT/PRECOMMIT_REVIEW -> LOCKED
```

Post-lock edits invalidate the bound authority for that contract identity.

## 12. Critic authority boundary

Critic outputs are authoritative only for bounded dispositions such as:

```text
CRITIC_ACCEPTS_BOUNDED_CLAIM
CRITIC_LIMITS_CLAIM
CRITIC_INVALIDATES
CRITIC_REJECTS_SUPPORT
```

Critic cannot issue:

```text
PROMOTE
RETHRESHOLD
RESCUE_POPULATION
CHANGE_PRIMARY_METRIC
REOPEN_SAME_CANDIDATE_AS_NEW
```

Critic findings that suggest modifications must create a new research lead/descendant, not modify proof authority.

## 13. Governor authority boundary

Governor consumes verified proof records; it does not trust candidate-reported metrics.

Inputs should come from exact gate outputs bound to the candidate identity:

```text
validation proof
shadow proof
cost/economic proof
stability proof
tail/support proof
safety proof
Critic disposition
Evidence Ledger eligibility proof
```

Governor produces an append-only disposition record.

Candidate cannot invoke `PROMOTE` by presenting a self-constructed metric summary.

## 14. Promotion firewall

Conceptual promotion chain:

```text
FROZEN CANDIDATE
-> verified validation authority
-> verified validation completion
-> verified shadow authority
-> verified shadow completion
-> Critic bounded disposition
-> Governor exact gate evaluation
-> separate promotion authority
-> active champion registry update
```

Every arrow must be independently verifiable.

No direct:

```text
Candidate -> Champion
Research Brain -> Champion
Critic -> Champion
serialized state -> Champion
```

## 15. Champion registry

The active champion pointer is itself protected state.

Changing champion requires:

```text
exact current champion identity
exact challenger identity/hash
valid A-PROMOTE authority
rollback target registration
atomic registry transition
append-only audit event
```

A candidate becoming `PROMOTION_ELIGIBLE` does not automatically change champion.

## 16. Replay and context binding

Authority records must be context-bound so an accepted record cannot be replayed in a different scientific context.

At minimum, bind where relevant:

```text
candidate hash
contract hash
evidence manifest hash
genealogy root
gate version
population identity
metric/estimand identity
scientific constitution version
```

Changing context requires re-issuance.

## 17. Fail-closed behavior

If any authority dependency is missing, ambiguous, stale, mismatched, or unverifiable:

```text
TRANSITION = DENIED
SCIENTIFIC STATE = UNCHANGED
AUDIT EVENT = APPENDED
```

Never infer authority from intent, nearest match, compatible schema, or copied labels.

## 18. Adversarial test obligations for future implementation

Before implementation closure, tests must eventually attempt at least:

```text
forge status field
forge authority ID string
reuse authority on mutated candidate
reuse parent authority on descendant
swap evidence manifest
swap contract with same visible fields but different hash
replay expired/single-use authority
skip validation state
skip shadow state
Critic tries to promote
Research Brain tries to mark validated
candidate tries to update champion registry
archive/reload then attempt authority reset
new ID attempts to reset inherited debt
```

Expected result for all forbidden cases:

```text
DENY / FAIL CLOSED
```

No such implementation/tests are authorized yet; this section freezes future adversarial obligations only.

## 19. Open questions

ARE-0B remains a draft until adversarial review resolves:

- exact mechanism for unforgeable gate proof (signed record, internal capability object, content-addressed verified event, or equivalent);
- single-use vs scoped multi-use authority semantics;
- atomicity/concurrency behavior;
- recovery after partial persistence failure;
- gate-version migration;
- rollback authority lifetime;
- cross-process trust boundary;
- local compromise assumptions.

Disposition:

```text
ARE-0B = FORMAL DESIGN DRAFT / REVIEW REQUIRED
```
