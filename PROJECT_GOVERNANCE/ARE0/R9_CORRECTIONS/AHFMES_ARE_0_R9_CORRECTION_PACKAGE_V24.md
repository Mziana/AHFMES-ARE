# AHFMES ARE-0 — R9 Correction Package V24

Status: **NORMATIVE R9-01 CORRECTION COMPANION / UNIQUE CURRENT REFINEMENT FRONTIER / NO MACHINE RIGHTS BEYOND MATRIX V20 / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 1. Current pre-clean subject / finding

```text
b157649dca91f62f2ed88a39c9ae8bc055d64a54 = CHANGES_REQUIRED
IA24-D01 = MULTIPLE_CURRENT_REFINEMENT_BATCHES_HAVE_NO_TOTAL_GATE_DERIVATION
ROOT = R9-01
NEW_R9_ROOT = NO
```

V19 permits multiple historical refinement batches with individually current support but defines gate derivation only for zero or one current admissible batch. V24 closes that ambiguity by making currentness exact to one unique canonical current evidence frontier.

## 2. Unique frontier theorem

For every UNKNOWN anchor D:

```text
one governed current evidence state
-> exactly one CURRENT_CANONICAL_REFINEMENT_FRONTIER[D]
-> exactly one CURRENT_CANONICAL_REFINEMENT_EVIDENCE_ROOT[D]
```

The frontier is derived solely from frozen evidence/source/currentness/causal contracts. Order, retry, scheduler, operator and chat are excluded.

## 3. Frontier-exact currentness

A historical refinement batch is CURRENT only if its exact frontier/root equals the unique current frontier/root and all V19 completeness/finality/currentness/classifier/result predicates remain TRUE.

Frontier change alone is sufficient to make an old-frontier batch non-current for authority-sensitive reliance, even if every old support artifact remains individually valid.

## 4. Total gate

```text
no exact current-frontier batch
-> conservative UNKNOWN gate

one deterministic exact current-frontier batch B
-> exact successor dependency union plus independently persistent inherited adverse obligations
```

Two semantically different current batches are impossible under valid state. Equivalent duplicates are idempotent. Conflicting same-key payload is `IntegrityDefect` and cannot gain privilege.

## 5. Rollover safety

```text
F0/B0 current
-> evidence changes to F1
-> B0 immediately non-current
-> UNKNOWN conservative gate resumes
-> derive/verify F1 result
-> atomically append B1 + exact successor visibility
-> substitute gate to B1 dependency union
```

There is no stale-batch or clean-privilege gap while B1 is absent.

## 6. Adverse history preservation

Historical batches and successor obligations remain append-only. New-frontier omission does not delete old adverse scope. Removal requires explicit inherited correction/revalidation/supersession proof.

## 7. Concurrency / crash

A frontier compare is part of batch admissibility. Frontier movement during verification/commit cannot authorize stale state. Crash before new batch leaves conservative UNKNOWN. Retry/time cannot select a historical batch.

## 8. Regression extension

Protocol V25 adds R9-X233..R9-X240.

```text
R7 = 26
R8 = 40
R9 = 240
TOTAL = 306 formal architecture scenarios
```

## 9. Qualification reset

```text
CLEAN PASS COUNT = 0
ALL HISTORICAL ROOT/PASS/CANDIDATE CREDIT = HISTORICAL ONLY
NEW ROOT = REQUIRED
NEW LANE A-H IMPACT ATTACK = REQUIRED
NEW SA-11 = REQUIRED
NEW CP1 + CP2 = REQUIRED
FULL 306-SCENARIO FORMAL REGRESSION = REQUIRED
NEW SELF-REFERENCE-FREE CANDIDATE = REQUIRED
EXACTLY ONE NEW BINDER-ONLY CHILD = REQUIRED
```

## 10. Firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
