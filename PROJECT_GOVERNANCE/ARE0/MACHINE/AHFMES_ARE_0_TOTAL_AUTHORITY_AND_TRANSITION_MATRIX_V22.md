# AHFMES ARE-0 — Canonical Authority & Transition Matrix V22

Status: **SOLE CURRENT MACHINE SOURCE / R9-01 SEALED SEMANTIC-PROJECTION AUTHORITY / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Composition / narrowing

```text
BASE_MATRIX_V21_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V21.md
BASE_MATRIX_V21_GIT_BLOB_SHA = 20f1970af6e72bb5f26c37db34439bccf1a21fd1
V22 R9-01 > EXACT V21 > ... > EXACT V1
```

All inherited semantics remain except the static authority source for V21 semantic projection/equivalence is made explicit and mandatory below.

## 1. Finding closed

```text
PRE_CLEAN_SUBJECT = 1494044997dd712f7edb7086fa9821b7d11cd75c
FINDING = IA26-A01
CLASS = SEMANTIC_EQUIVALENCE_PROJECTION_HAS_NO_SEALED_STATIC_AUTHORITY
ROOT = R9-01
NEW_R9_ROOT = NO
```

## 2. Static precommitted semantic-projection authority

Add exact generation-0 static authority object:

```text
POSTGENESIS_REFINEMENT_SEMANTIC_PROJECTION_ROOT
```

It is `STATIC_PRECOMMITTED` under Matrix V9 `GEN0_FIELD_PARTITION_ROOT` and therefore its exact payload is included in `STATIC_GEN0_AUTHORITY_SEMANTICS_COMMITMENT_ROOT` before authorization/import.

The exact root MUST bind all of:

```text
canonical semantic-claim schema and types
raw governed evidence -> canonical semantic-claim normalization
semantic support-equivalence relation
classification-relevance projection rules
non-projectable adverse / contradiction / revocation qualifiers
source-finality/currentness and causal-qualification projection rules
support admission rules
per-claim support-valid/current/final-enough aggregation rules
canonical claim/support ordering and hash encoding
ambiguity / unsupported evidence-type / UNKNOWN conservative behavior
```

Every governed evidence type reachable under frozen source/materiality contracts MUST have an exact projection/admission rule or explicit conservative UNKNOWN mapping. Missing/overlap/ambiguity is invalid static totality.

## 3. Bootstrap binding theorem

Because the projection root is `STATIC_PRECOMMITTED`, all V9 requirements apply without a new authorization slot:

```text
GEN0_FIELD_PARTITION_TOTALITY_VALID must classify it exactly once
STATIC_GEN0_AUTHORITY_SEMANTICS_COMMITMENT_ROOT binds its exact payload
BOOTSTRAP_INSTANCE_AUTHORIZATION_ASSERTION_ROOT binds that static commitment
BOOTSTRAP_AUTHORIZATION_BINDING_ROOT binds that static commitment
```

Any different projection root after target authorization/import is a static conflict/denial on the same bootstrap instance. It cannot create a retry, alternative authorization, new scientific opportunity or new instance unless the actual constitutional system/domain identity is genuinely different under inherited rules.

## 4. Canonical semantic derivation

V21 objects are narrowed to:

```text
CURRENT_REFINEMENT_SEMANTIC_FRONTIER[D] = PROJECT_SEMANTICS(
  D,
  current governed evidence,
  POST_CUT_OBLIGATION_CLASSIFICATION_ROOT,
  POSTGENESIS_REFINEMENT_SEMANTIC_PROJECTION_ROOT,
  frozen source/materiality/causal contracts
)

CURRENT_REFINEMENT_SEMANTIC_ROOT[D] = hash(
  POST_CUT_OBLIGATION_CLASSIFICATION_ROOT,
  POSTGENESIS_REFINEMENT_SEMANTIC_PROJECTION_ROOT,
  canonical semantic frontier
)
```

Thus two different equivalence/projection policies cannot yield the same authority identity merely because their class/scope output happens to coincide.

## 5. Support derivation

`CURRENT_REFINEMENT_SUPPORT_SET[D]` and every V21 per-claim support predicate MUST be derived using the exact sealed projection root. No actor may select one admissible equivalence relation over another.

Equivalent raw support churn preserves semantic root only when the sealed root mechanically says so and every required current/finality/causal predicate remains TRUE.

Evidence that the sealed root classifies as adverse, contradictory, revoking, causal-changing, scope/materiality-changing, or ambiguity-producing cannot be treated as equivalent support.

## 6. Totality / no implementation invention

```text
raw evidence class covered + deterministic projection
-> derive exact claim/equivalence/currentness effect

raw evidence class not covered
or overlapping rules disagree
or normalization is ambiguous
-> IntegrityDefect / conservative UNKNOWN
-> no semantic batch privilege
```

Implementation, operator, chat, evidence producer and refinement committer have zero authority to invent normalization/equivalence/relevance rules.

## 7. Batch identity / transition

`REFINEMENT_SEMANTIC_BATCH_KEY` additionally binds `POSTGENESIS_REFINEMENT_SEMANTIC_PROJECTION_ROOT`.

Same sealed root + same semantic frontier + renewable equivalent support => same batch authority. Projection-root change is not a refinement event; after bootstrap seal it is static conflict.

All V21 stale-batch, support-loss, adverse-history, supersession and <=cut firewalls remain.

## 8. Crash / concurrency / anti-selection

```text
same evidence under same sealed projection root -> same semantic normalization
same support presented in different order -> same canonical result
competing actor interpretations -> irrelevant; actors do not write projection
unsupported evidence form -> UNKNOWN, never actor-defined fallback
projection root mutation after authorization -> static conflict; no batch/currentness transition
```

## 9. Human–ARE interface

Chat may explain the sealed projection rules and simulate their effect. Chat has zero authority to author, alter, choose, waive, or reinterpret the projection root or any resulting scientific/Safety/broker/capital state.

## 10. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
