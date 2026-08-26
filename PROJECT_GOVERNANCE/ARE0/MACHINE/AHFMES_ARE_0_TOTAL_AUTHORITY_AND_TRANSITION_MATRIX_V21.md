# AHFMES ARE-0 — Canonical Authority & Transition Matrix V21

Status: **SOLE CURRENT MACHINE SOURCE / R9-01 SEMANTIC REFINEMENT FRONTIER / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Composition / narrowing

Immutable machine base:

```text
BASE_MATRIX_V20_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V20.md
BASE_MATRIX_V20_GIT_BLOB_SHA = 5829bd082bd49bacc340c0aa69d12f49886de957
```

All V20->V1 semantics remain except refinement frontier identity, support renewal, and current-batch derivation are narrowed below.

```text
V21 R9-01 > EXACT V20 > ... > EXACT V1
```

## 1. Finding closed

Exact pre-clean subject:

```text
47007292333382bf1c1ba53528aedbe61fa40f8e
```

Finding:

```text
IA25-D01 = RAW_EVIDENCE_FRONTIER_CHURN_CAN_STARVE_REFINEMENT_FOREVER
ROOT = R9-01
NEW_R9_ROOT = NO
```

V20 binds current batch identity to the raw canonical set of all current/admissible evidence. Classification-irrelevant evidence growth can therefore roll the frontier continuously and make an otherwise semantically stable refinement perpetually miss commit. V21 separates authority-bearing semantic state from renewable proof/support mechanics.

## 2. Sealed semantic projection

For each immutable UNKNOWN anchor D, derive under the already sealed classifier/source/materiality/causal contracts:

```text
CURRENT_REFINEMENT_SEMANTIC_FRONTIER[D]
CURRENT_REFINEMENT_SEMANTIC_ROOT[D]
```

The semantic frontier contains exactly the canonical classification-relevant claim/projection tuples needed to determine the exact class set, affected scopes, causal dependencies and successor-obligation set for D.

Its derivation MUST be a deterministic function of frozen normative contracts and current governed evidence. No actor may choose relevance, omit adverse evidence, or select a favorable projection.

Excluded from semantic identity when they do not change any classification-relevant claim/projection:

```text
support artifact byte identity
equivalent proof renewal
duplicate equivalent support
arrival order
scheduler/retry order
actor identity
wall-clock time except governed semantic time facts
```

A governed item is NOT projectable-away if it changes, contradicts, revokes, qualifies, causally reinterprets, or creates uncertainty about any classification-relevant claim or required finality/currentness predicate.

Ambiguous projection => `IntegrityDefect`; conservative UNKNOWN remains effective.

## 3. Renewable support set

Separately derive non-writable:

```text
CURRENT_REFINEMENT_SUPPORT_SET[D]
CURRENT_REFINEMENT_SUPPORT_VALID[D, semantic_claim]
CURRENT_REFINEMENT_SUPPORT_COMPLETE[D]
CURRENT_REFINEMENT_SUPPORT_FINAL_ENOUGH[D]
```

The support set may change while `CURRENT_REFINEMENT_SEMANTIC_ROOT[D]` remains identical.

For a semantic root to be relied upon, every semantic claim/projection required by the sealed classifier MUST have at least one mechanically admissible support path that is current, final-enough, causally complete and non-revoked under its frozen source contract.

Equivalent support additions/renewals/removals that leave those predicates TRUE do not deauthorize the semantic batch.

If any required claim loses all valid support, becomes contradicted/ambiguous, or loses required completeness/finality:

```text
CURRENT_REFINEMENT_BATCH[D] = NONE
UNKNOWN_EFFECTIVE_GATE[D] = conservative inherited UNKNOWN gate
```

No grace window is permitted.

## 4. Semantic-exact batch identity

A refinement batch is authority-current iff:

```text
batch.semantic_root == CURRENT_REFINEMENT_SEMANTIC_ROOT[D]
batch.semantic_frontier == CURRENT_REFINEMENT_SEMANTIC_FRONTIER[D]
CURRENT_REFINEMENT_SUPPORT_COMPLETE[D] == TRUE
CURRENT_REFINEMENT_SUPPORT_FINAL_ENOUGH[D] == TRUE
all required semantic claims have CURRENT_REFINEMENT_SUPPORT_VALID == TRUE
batch.result == deterministic sealed-classifier result for that semantic root
batch.successor_set_root == deterministic exact successor set for that semantic root
```

Raw support-set identity is evidence/audit material and MUST NOT be part of the authority-sensitive refinement batch key.

Canonical key:

```text
REFINEMENT_SEMANTIC_BATCH_KEY = hash(
  stable fact identity,
  POST_CUT_OBLIGATION_CLASSIFICATION_ROOT,
  CURRENT_REFINEMENT_SEMANTIC_ROOT[D],
  exact successor obligation set root
)
```

Same semantic root + equivalent renewable support => same authority batch. No remint is required.

## 5. Total transition theorem

```text
semantic root S0 + current valid support + B0
-> equivalent support churn E0->E1->E2...
-> semantic root remains S0
-> B0 remains current while support predicates remain TRUE

semantic-relevant change S0->S1
-> B0 immediately non-current
-> conservative UNKNOWN gate
-> derive exact S1 result
-> atomically append/recognize B1 + complete successor visibility
-> B1 current only with valid support predicates

support loss without semantic replacement
-> B0 immediately non-current
-> conservative UNKNOWN until support is restored or a new semantic root is proven
```

Continuous semantically-equivalent evidence churn cannot by itself starve or remint refinement authority.

## 6. Adverse evidence / correction firewall

The semantic projection MUST preserve adverse facts and uncertainty effects. In particular:

```text
contradictory evidence
revocation
source-finality loss
causal predecessor change
scope expansion
materiality change
correction evidence
```

cannot be treated as irrelevant merely because an old classifier output would otherwise remain convenient.

If evidence proves a true `<=cut` correction, reorg, missing predecessor or relied-prefix reinterpretation, refinement is denied and inherited semantic coverage invalidation/reconciliation/new-cut discipline applies.

## 7. Historical obligations and supersession

All historical batches, support records, adverse evidence and successor obligations remain append-only.

A new semantic root or support-set change cannot silently delete a prior adverse obligation. Leaving dependency effect requires explicit inherited correction/revalidation/supersession proof.

## 8. Writer / anti-selection theorem

`A-POSTGENESIS-CLASSIFICATION-REFINEMENT-COMMIT` remains verifier/committer only. It cannot:

```text
choose semantic projection
choose support artifact
declare semantic equivalence
suppress adverse evidence
choose class/scope/successor set
supersede obligations
alter Safety/broker/capital state
execute
```

All current semantic/support predicates are derived/non-writable.

## 9. Crash / retry / concurrency

```text
equivalent support renews during commit
-> semantic key unchanged; valid existing/current batch remains usable if support predicates remain TRUE

semantic root changes during commit
-> old semantic compare fails or old batch is immediately non-current; UNKNOWN effective

support validity disappears during commit
-> no authority; UNKNOWN effective

concurrent equivalent semantic commits
-> one semantic batch / idempotent duplicate recognition

same semantic key + conflicting payload
-> IntegrityDefect + UNKNOWN; no first-writer privilege

continuous equivalent support churn
-> cannot create new semantic batch keys and cannot starve solely due raw proof movement
```

## 10. Human–ARE interface

Human–ARE chat may explain evidence, semantic projection, support status and simulated refinement outcomes. Chat has zero authority to admit evidence, decide relevance/equivalence, classify, supersede, clear dependencies, mutate capital or execute.

## 11. Forbidden control planes

```text
raw evidence bytes directly defining authority batch identity
equivalent proof renewal forcing semantic batch remint
operator/chat selecting relevant evidence
projecting away contradictory/adverse evidence
using stale semantic batch after semantic root change
using batch after required support becomes non-current
support churn creating authority lottery
new semantic root silently deleting old adverse obligation
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
