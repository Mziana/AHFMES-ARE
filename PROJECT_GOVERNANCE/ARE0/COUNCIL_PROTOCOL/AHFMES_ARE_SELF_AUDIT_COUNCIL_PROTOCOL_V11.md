# AHFMES ARE — Self-Audit Council Protocol V11

Status: **MANDATORY PRE-EXTERNAL-REAUDIT GOVERNANCE / SELF-REFERENCE-FREE SA-11 / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable base:

```text
BASE_PROTOCOL_V10_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V10.md
BASE_PROTOCOL_V10_GIT_BLOB_SHA = 19e7eb84ec6603c3a229aad89a9aa91e9bad3554
```

All V10->V2 rules remain except SA-11 exact-subject construction, regression ceiling and dispatch sequence are replaced/narrowed here. Manifest routing remains exclusively through the stable binding.

## 1. Current manifest and machine source

The current normative manifest is resolved only through:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_CURRENT_NORMATIVE_MANIFEST_BINDING.md
```

Matrix V8 remains the sole current machine-semantic source. Inventory V8 remains the current closed-world companion. This protocol adds no machine right.

## 2. Self-reference-free SA-11 qualification

The current Quarantine Policy defines the exact finite `QUALIFICATION_AUDIT_OUTPUT_SET (QAO)`, `QUALIFICATION_INPUT_FRONTIER (QIF)`, deterministic `SA11_INPUT_FRONTIER_ROOT`, and `QUALIFICATION_EVIDENCE_SET_ROOT`.

SA-11 PASS requires, for one frozen QIF root:

```text
SUBJECT_BOUND_CURRENT_NORMATIVE_MANIFEST_VALID
QUALIFICATION_AUDIT_OUTPUT_SET_EXACT_AND_PRECOMMITTED
EXHAUSTIVE_QIF_FRONTIER_PROVEN
AUTHORITY_CLAIM_TRIGGER_LEDGER_COMPLETE
AUTHORITY_LIKE_CLAIM_INVENTORY_COMPLETE
NO_QAO_SEMANTIC_DEPENDENCY
NO_UNLISTED_CURRENT_SEMANTIC_DEPENDENCY
SA11_INPUT_FRONTIER_ROOT_FINAL_CANDIDATE_EQUAL
QUALIFICATION_EVIDENCE_SET_INTEGRITY_VALID
```

The trigger ledger and quarantine record are QAO outputs; they do not recursively inspect/content-address themselves. Every non-QAO governance blob remains in the inspected input frontier unless it is a current normative member.

## 3. Final-candidate projection rule

Let `R0` be the QIF root used for SA-11 inspection and `C` a later candidate containing audit outputs.

Qualification requires:

```text
SA11_INPUT_FRONTIER_ROOT(C) = R0
```

Therefore only exact QAO output changes may occur without re-running the QIF scan. Any non-QAO governance path/blob change changes the projection and invalidates SA-11 evidence.

QAO exclusion never confers authority. If any current machine/closure/audit semantic depends on a QAO path, qualification fails.

## 4. Isolated audit lanes

Required lanes remain independently adjudicated:

```text
LANE-A BOOTSTRAP IDENTITY / CRASH / CONCURRENCY
LANE-B CLOSED-WORLD STATE / WRITER / AUTHORITY TOTALITY
LANE-C SCIENTIFIC / CHALLENGE / REVALIDATION / ROLLBACK
LANE-D CAPITAL / BROKER / COMPLETENESS / SAFETY
LANE-E CLOSURE / MANIFEST / QUARANTINE / SUBJECT IDENTITY
LANE-F OUTSIDE-FAMILY ADVERSARIAL INTEGRATOR
```

No lane inherits another lane's PASS. One reproducible legal exploit blocks qualification.

## 5. Clean-pass semantics

Before Clean Pass #1:

```text
all normative corrections complete
normative bytes frozen
QAO exact path set frozen
Lane A-F impact attack complete
SA-11 QIF scan complete with no unresolved blocker
```

After Clean Pass #1:

```text
ANY byte/path/blob change to any current normative manifest member -> CLEAN PASS COUNT = 0
```

QAO audit records may be created after CP1 without changing the normative root or QIF projection, but they cannot alter normative semantics. Any non-QAO governance write after the frozen SA-11 scan invalidates the QIF equality and requires rescan; if normative, it also resets clean-pass count.

## 6. Permanent regression extension

All inherited R7/R8 and R9-X01..R9-X99 remain mandatory.

Add:

```text
R9-X100 trigger ledger required to hash/list its own blob -> construction invalid; QIF/QAO separation required
R9-X101 similarly named but non-exact QAO path omitted from scan -> SA-11 denied
R9-X102 exact QAO path used as current semantic/audit-rule dependency -> qualification denied
R9-X103 final candidate changes any non-QAO governance blob while claiming old QIF root -> denied
R9-X104 QAO evidence blob changes after dependent evidence-root/final-consistency check without refresh -> dispatch denied
R9-X105 QAO exact path set expanded/narrowed after results observed -> normative change; impact rerun; clean count 0
R9-X106 candidate adds audit output at a path not in exact QAO set and excludes it by prefix inference -> denied
R9-X107 candidate QIF root equals audited root but current normative root/manifest differs -> denied
```

No prior regression seed is deleted.

## 7. Required qualification sequence

```text
integrated pre-clean normative correction
-> freeze normative bytes and exact QAO path set
-> isolated Lane A-F whole-composition impact attack
-> compute exact QIF + QIF root
-> complete recursive trigger ledger + per-claim quarantine evidence against QIF
-> resolve any blocker; normative correction returns count to 0
-> freeze exact normative root and QIF root
-> Clean Pass #1
-> NO normative write
-> Clean Pass #2 on exact same normative root and QIF root
-> R7 + R8 + R9-X01..X107 regression
-> create/update only exact QAO evidence records as required
-> final cross-document consistency
-> recompute final-candidate QIF projection and require equality
-> compute qualification evidence-set integrity
-> self-reference-free candidate
-> exactly one binder-only child
-> independent external whole-architecture audit
```

No internal result is an independent external verdict.

## 8. Dispatch invariants

Before dispatch:

```text
FULL COUNCIL CLEAN PASS #1 = CLEAN
FULL COUNCIL CLEAN PASS #2 = CLEAN
PASS_1_NORMATIVE_ROOT = PASS_2_NORMATIVE_ROOT
PASS_1_QIF_ROOT = PASS_2_QIF_ROOT
PERMANENT REGRESSION = PASS
FINAL CONSISTENCY = PASS
SA11_FINAL_QIF_EQUALITY = PASS
BINDER_ONLY_CHILD = EXACTLY ONE COMMIT / EXACTLY ONE HANDOFF PATH
```

Any UNKNOWN in a required gate is non-PASS.

## 9. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
