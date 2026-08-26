# AHFMES ARE-0 — Canonical Authority & Transition Matrix V15

Status: **SOLE CURRENT MACHINE SOURCE / R9-01 TRANSACTIONALLY STABLE LOCAL CUT-PREFIX FENCING / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Composition / narrowing

Immutable machine base:

```text
BASE_MATRIX_V14_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V14.md
BASE_MATRIX_V14_GIT_BLOB_SHA = d8a28f78f5169c0c2b2ccd91930cf410d8b29656
```

All V14->V1 semantics remain except LOCAL_CAS admissibility/fencing is narrowed below.

## 1. Internal impact finding

Exact impacted subject:

```text
991c1a02314e994f9cb664370ae8808d71899506
```

Finding:

```text
IA18-B01 = LOCAL_CAS_GLOBAL_HEAD_REFRESH_CAN_STILL_STARVE
ROOT = R9-01
NEW_R9_ROOT = NO
```

Cause: V14 allowed mutable global-head refresh after harmless >cut append, but repeated tail appends can race every refreshed latest-head CAS. Safety holds, drainability does not.

## 2. LOCAL_CAS admissibility is cut-scoped, not latest-head scoped

A source may be classified `LOCAL_CAS` for COMPLETE pregenesis coverage only if the same local atomic SystemGenesis transaction can compare a predicate whose identity is scoped to the exact selected semantic prefix through cut and whose value is unaffected by strictly-post-cut tail appends.

Required exact identity:

```text
LOCAL_CAS_SEMANTIC_PREFIX_FENCE[i] = hash(
  source identity,
  source-contract identity,
  PREGENESIS_SEMANTIC_SOURCE_CUT_ID[i],
  exact <=cut included-prefix root,
  exact <=cut predecessor/causal-closure root,
  transactionally comparable prefix generation/range-version/root
)
```

The atomic transaction must positively compare the exact current value of this prefix fence before committing Genesis.

## 3. Admissible mechanisms

Examples are admissible only if their frozen source contract positively proves the same theorem:

```text
MVCC/range version for exact <=cut keyspace
content-addressed immutable prefix root with atomic authoritative pointer for <=cut semantics
transactional range checksum/version unaffected by >cut inserts
append-only local log with immutable segment/cut root and atomic proof that no <=cut rewrite channel exists
```

Implementation label is irrelevant. Required property is exact atomic comparability of <=cut semantic truth.

## 4. Mutable latest-head-only fallback removed

V14 language permitting global latest-head H_g -> H_g+1 tail-only refresh as sufficient LOCAL_CAS COMPLETE fencing is replaced.

If the only atomically comparable local predicate is a mutable global latest head that changes on harmless strictly >cut append, then:

```text
LOCAL_CAS_COMPLETE_ADMISSIBLE = FALSE
```

unless the same transaction can separately compare the stable cut-scoped prefix predicate above.

Such a source must be reclassified under the frozen contract as a class whose actual theorem is supportable, or remain conservative UNKNOWN/deny. Runtime retry, double-read, delta verification outside the committing transaction, scheduler quiet period, or repeated latest-head refresh cannot manufacture LOCAL_CAS completeness.

## 5. Mechanical evidence generation narrowing

For valid LOCAL_CAS, `SOURCE_COMMIT_EVIDENCE_GENERATION` may carry refreshed descriptive/verification evidence, but SystemGenesis commit authority depends on the transactionally stable `LOCAL_CAS_SEMANTIC_PREFIX_FENCE`, not equality to a mutable global tail head.

Strictly >cut append therefore:

```text
may change global head
may update descriptive evidence
must not change LOCAL_CAS_SEMANTIC_PREFIX_FENCE
must not stale scientific coverage
must not require a new coverage opportunity
must not block Genesis solely because tail grew
```

Any <=cut add/remove/reorder/rewrite or predecessor reinterpretation changes/fails the prefix fence and denies stale Genesis.

## 6. Drainability theorem

For a valid LOCAL_CAS source with stable semantic prefix `C`:

```text
Q/A current for C
post-cut tail appends arbitrarily many times
LOCAL_CAS_SEMANTIC_PREFIX_FENCE(C) unchanged
SystemGenesis transaction compares fence(C)
-> tail growth alone cannot make compare fail
-> no scientific remint
-> Genesis remains drainable subject to other predicates
```

This is stronger than repeated global-head refresh and removes timing dependence on a quiet tail.

If no stable cut-scoped atomic predicate exists, architecture does not promise COMPLETE drainability for that source; it fails conservative rather than inventing an authority edge.

## 7. Post-cut handoff remains mandatory

V14 `POST_CUT_PRECOMMIT_OBLIGATION_SET_ROOT` and atomic `Generation0PostCutCorrectionQueue #0` remain fully in force.

Thus a >cut fact may leave the semantic prefix unchanged for fencing while still creating a durable post-cut obligation before Genesis if governed-knowable/material. Fencing and knowledge handoff are independent controls.

## 8. External finality renewal unchanged

V14 deterministic same-cut `FINALITY_EVIDENCE_GENERATION` successor theorem remains unchanged. Proof renewal cannot select another semantic cut or repair factual <=cut change.

## 9. Forbidden controls

```text
mutable global latest head treated as cut-scoped atomic fence
retry until local tail happens to be quiet
outside-transaction delta proof treated as atomic <=cut fence
>cut append used to remint coverage
<=cut mutation ignored because global head refresh succeeded
LOCAL_CAS label asserted without positive cut-prefix atomicity proof
```

All inherited V14 forbidden controls remain.

## 10. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
