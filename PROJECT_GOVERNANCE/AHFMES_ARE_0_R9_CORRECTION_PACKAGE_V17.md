# AHFMES ARE-0 — R9 Correction Package V17

Status: **NORMATIVE R9-01 EXTERNAL SOURCE FINALITY / CUT-VECTOR CORRECTION COMPANION / NO MACHINE RIGHTS BEYOND MATRIX V13 / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 1. Historical subject / finding

```text
b241eb96566e5fbe18af8cb4d4ec2e100caf5896 = INTERNAL IMPACT / CHANGES_REQUIRED
IA17-C01 = EXTERNAL_SOURCE_HEAD_TOCTOU_AT_SYSTEMGENESIS
ROOT = R9-01
NEW R9 ROOT = NO
```

The preceding closure-routing correction succeeded, but impact attack found that V12 could not atomically prove an external non-CAS source head remained unchanged through local SystemGenesis commit.

## 2. Correction theorem

Matrix V13 / Inventory V13 distinguish:

```text
LOCAL_CAS
EXTERNAL_FINALIZABLE
EXTERNAL_NONFINALIZABLE
```

and replace `latest/fresh at last read` with a canonical source cut theorem.

For external COMPLETE coverage, exact finalized prefix proof must establish that no eligible fact/event <=cut can later be added/removed/reordered/rewritten and that predecessor/causal closure is complete. Otherwise affected source state is conservative UNKNOWN or genesis is denied where UNKNOWN cannot satisfy inherited predicates.

## 3. Canonical cut / anti-lottery

The exact multi-source cut vector is selected deterministically under frozen `GENESIS_CUTOFF_RULE_ROOT`; no caller may choose an older favorable finalized cut.

Local sources are fenced by same-transaction CAS. External finalized sources are fenced by immutable cut finality rather than mutable later `latest` head. Cross-source cuts must be causally closed.

## 4. Retry / timing

```text
post-cut >cut source event -> does not remint same opportunity
<=cut correction/reorg -> current coverage invalid
same revision/knowledge/cut retry -> idempotent
older/different favorable cut -> denied
last-read/double-read without finality -> not an external fence
```

## 5. Closure routing unchanged

Policy V5 remains current and generation-agnostic. Current manifest resolution remains only through stable binding. Matrix V13/Inventory V13 introduce no alternate closure selector.

## 6. Regression extension

Protocol V18 adds R9-X167..R9-X174 covering external TOCTOU, nonfinalizable source misuse, post-cut advance, retroactive correction, cutoff cherry-pick, cross-source causal gap, forgeable finality proof and local CAS race.

Current regression requirement:

```text
R7 = 26
R8 = 40
R9 = 174
TOTAL = 240
```

## 7. Qualification reset

Because normative machine/inventory/protocol/correction/binding/manifest bytes change before CP1:

```text
CLEAN PASS COUNT = 0
OLD ROOT/PASS/CANDIDATE CREDIT = HISTORICAL ONLY
```

Next authorized sequence is exact integrated-byte Lane A-H impact attack -> subject-bound SA-11 -> root -> CP1 -> no normative write -> CP2 -> 240/240 regression -> final consistency -> self-reference-free candidate -> one binder-only child -> external re-audit.

## 8. Firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
