# AHFMES ARE-0 — Canonical Authority & Transition Matrix V20

Status: **SOLE CURRENT MACHINE SOURCE / R9-01 UNIQUE CURRENT REFINEMENT FRONTIER / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Composition / narrowing

Immutable machine base:

```text
BASE_MATRIX_V19_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V19.md
BASE_MATRIX_V19_GIT_BLOB_SHA = 84eb9d3b6ccb560aea19107bc503e05a143d1e5e
```

All V19->V1 semantics remain except refinement-currentness and gate derivation are narrowed below.

```text
V20 R9-01 > EXACT V19 > ... > EXACT V1
```

## 1. Finding closed

Exact pre-clean subject:

```text
b157649dca91f62f2ed88a39c9ae8bc055d64a54
```

Finding:

```text
IA24-D01 = MULTIPLE_CURRENT_REFINEMENT_BATCHES_HAVE_NO_TOTAL_GATE_DERIVATION
ROOT = R9-01
NEW_R9_ROOT = NO
```

V19 permits a new batch for a changed evidence frontier while historical batches can retain individually valid support. Its gate theorem handles zero or one current batch but does not define two individually admissible historical batches. V20 makes currentness frontier-exact and therefore single-valued.

## 2. Unique current canonical refinement frontier

For each immutable UNKNOWN anchor D derive exactly one non-writable:

```text
CURRENT_CANONICAL_REFINEMENT_FRONTIER[D]
CURRENT_CANONICAL_REFINEMENT_EVIDENCE_ROOT[D]
```

The frontier is the deterministic canonical ordered set of all evidence that is CURRENT and admissible under the frozen source/domain evidence contracts, causal predecessor rules, source-class finality rules, materiality rules and revocation/correction rules.

Excluded from identity:

```text
arrival order
scheduler order
retry count
actor identity
operator/chat preference
wall-clock time except where an inherited evidence-currentness rule explicitly uses governed time evidence
```

For one exact governed repository/evidence state there is exactly one current frontier/root for D. Ambiguous frontier construction is `IntegrityDefect` and leaves conservative UNKNOWN effective.

## 3. Frontier-exact batch currentness

A historical `POSTGENESIS_CLASSIFICATION_REFINEMENT_BATCH[D,E]` is CURRENT if and only if all are TRUE:

```text
batch.evidence_root == CURRENT_CANONICAL_REFINEMENT_EVIDENCE_ROOT[D]
batch.frontier == CURRENT_CANONICAL_REFINEMENT_FRONTIER[D]
CLASSIFICATION_SCOPE_COMPLETE[D] == TRUE under that exact frontier
CLASSIFICATION_SUPPORT_FINAL_ENOUGH[D] == TRUE under that exact frontier
POSTGENESIS_CLASSIFICATION_REFINEMENT_SUPPORT_CURRENT[D] == TRUE
batch.result == deterministic sealed-classifier result for that exact frontier
batch successor-set root == deterministic exact successor set for that exact frontier
```

Individual support artifacts remaining valid is insufficient once the canonical current frontier changes.

A frontier change F0->F1 immediately makes every F0 batch non-current for authority-sensitive reliance, even if all F0 artifacts remain historically valid.

## 4. Total gate derivation

Derived gate semantics are total:

```text
if there is no frontier-exact CURRENT batch for D:
    CURRENT_REFINEMENT_BATCH[D] = NONE
    UNKNOWN_EFFECTIVE_GATE[D] = conservative V18 UNKNOWN gate set

if a frontier-exact batch B exists:
    CURRENT_REFINEMENT_BATCH[D] = B
    UNKNOWN_EFFECTIVE_GATE[D] = dependency_union(exact successor obligations in B)
```

There cannot be two semantically distinct current batches because both would have to bind the same current evidence root/frontier and the same deterministic sealed-classifier result/successor root. Byte-equivalent duplicate commits are idempotent duplicate recognition. Conflicting payload for the same deterministic key is `IntegrityDefect`; conservative UNKNOWN remains effective and no conflicting batch receives authority.

## 5. Frontier rollover / no clean window

When governed evidence changes the current frontier:

```text
F0 current batch B0
-> evidence state changes
-> canonical frontier becomes F1
-> B0 becomes non-current immediately
-> conservative UNKNOWN gate resumes
-> derive F1 result
-> only if F1 completeness/finality predicates are TRUE may exact B1 be atomically committed
-> B1 visibility and exact successor visibility occur atomically
-> gate substitutes from conservative UNKNOWN to B1 successor union
```

There is no state in which old-frontier B0 retains privilege after F1 is canonical merely because B1 has not yet been committed.

Continuous evidence churn may conservatively keep UNKNOWN effective; this is fail-closed availability loss, not authority ambiguity and not a license to use a stale batch.

## 6. Historical obligations / supersession

All refinement batches and successor obligations remain append-only history. Making B0 non-current does not delete its obligations, adverse evidence or causal history.

A successor obligation/scope created by any historical batch may cease to affect current dependency derivation only under the explicit correction/revalidation/supersession rules inherited from V19. A newer frontier omitting a scope is not deletion evidence.

If inherited rules require an old adverse obligation to persist independently, it remains in the dependency union in addition to the frontier-exact batch.

## 7. Writer and anti-selection theorem

`A-POSTGENESIS-CLASSIFICATION-REFINEMENT-COMMIT` remains verifier/committer only. It cannot choose the frontier, evidence root, class, scope, successor set, current batch, supersession, Safety state, broker state, capital state or execution.

No actor writes `CURRENT_CANONICAL_REFINEMENT_FRONTIER[D]`, `CURRENT_CANONICAL_REFINEMENT_EVIDENCE_ROOT[D]`, `CURRENT_REFINEMENT_BATCH[D]` or `UNKNOWN_EFFECTIVE_GATE[D]`.

## 8. Concurrency / crash / retry

```text
same current frontier + concurrent equivalent commits -> one semantic batch / idempotent duplicates
same current frontier + conflicting payload -> IntegrityDefect; UNKNOWN effective
frontier changes during attempted commit -> old-frontier compare fails or committed old batch is immediately non-current; no stale privilege
crash after frontier rollover before new batch -> UNKNOWN effective
crash during new batch atomic commit -> either UNKNOWN remains or complete B1+successor visibility; no half-transfer
retry/time alone -> cannot change frontier or create authority
```

## 9. <=cut firewall

Actual `<=cut` correction, reorg, missing predecessor or relied-prefix reinterpretation remains forbidden from refinement. It must use inherited semantic coverage invalidation/reconciliation/new-cut discipline.

## 10. Human–ARE interface

Human–ARE chat may explain current frontier, historical batches and simulated refinement outcomes. Chat has zero authority to admit evidence, select frontier/current batch, classify, supersede, clear dependencies, mutate capital or execute.

## 11. Forbidden control planes

```text
two different frontier roots simultaneously treated CURRENT for one D
old-frontier batch retaining privilege after canonical frontier rollover
latest historical admissible batch chosen by timestamp/arrival/order
operator/chat choosing which admissible batch governs
conflicting same-key batch selecting authority by first writer
new frontier silently deleting old adverse obligation
stale batch used while new current frontier has no committed batch
<=cut correction routed through refinement
```

All inherited forbidden controls remain.

## 12. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
