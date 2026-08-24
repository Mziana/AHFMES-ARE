# AHFMES ARE — Self-Audit Council Protocol V18

Status: **MANDATORY PRE-EXTERNAL-REAUDIT GOVERNANCE / EXTERNAL SOURCE FINALITY ATTACK + SUBJECT-BOUND QUARANTINE / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Composition

Immutable base:

```text
BASE_PROTOCOL_V17_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V17.md
BASE_PROTOCOL_V17_GIT_BLOB_SHA = fd0495c4777771d22f121525c00da26deab5c100
```

All V17->V2 rules remain except current manifest generation, machine/inventory generation and regression ceiling are advanced below.

Current machine source = Matrix V13. Current closed-world companion = Inventory V13. Current quarantine policy remains Policy V5 and resolves current membership only through the stable binding.

## 1. Historical impact subject / finding

Exact historical pre-pass subject:

```text
b241eb96566e5fbe18af8cb4d4ec2e100caf5896
```

Disposition:

```text
CHANGES_REQUIRED
IA17-C01 = EXTERNAL_SOURCE_HEAD_TOCTOU_AT_SYSTEMGENESIS
ROOT = R9-01
NEW R9 ROOT = NO
```

Exploit/deadlock class:

```text
read external non-CAS head H
verify freshness/currentness of H
external source advances or corrects H
local SystemGenesis transaction commits using H
```

Loose interpretation commits stale source state. Strict requirement that H remain latest through local commit cannot be positively proven without an external fencing/finality theorem and can deadlock.

## 2. Current correction theorem

Matrix V13 + Inventory V13 replace last-read freshness with:

```text
LOCAL_CAS -> same-transaction compare
EXTERNAL_FINALIZABLE -> immutable finalized canonical cut prefix
EXTERNAL_NONFINALIZABLE -> conservative UNKNOWN or denial
```

The canonical multi-source cut is selected only by the frozen performance-blind `GENESIS_CUTOFF_RULE_ROOT`, must be causally closed and cannot be caller-selected for favorable history.

Post-cut source advance does not create a new same-state opportunity; <=cut correction/reorg invalidates currentness.

## 3. Independent attack lanes

Retain V17 Lane A-H and add explicit finality/cut attacks:

```text
LANE-A instance / target authorization / sealed slot
LANE-B gen0 partition / reconciliation drainability / materiality
LANE-C crash / retry / CAS / external-source TOCTOU / terminality
LANE-D writer/control SoD / import-vs-coverage / finality-proof control
LANE-E source universe / cut finality / causal closure / legacy-evidence-debt completeness
LANE-F Challenge / revalidation / rollback
LANE-G Safety / broker / exposure / external mutation across cut
LANE-H manifest / binding / quarantine / historical authority / candidate construction
```

One reproducible legal exploit/deadlock/closure defect blocks CP1.

## 4. Mandatory finality attacks

Before CP1 explicitly test:

```text
verify H then H+1 before local genesis commit
non-CAS source without positive finality proof
post-cut event strictly >cut
retroactive correction/reorg <=cut
caller chooses older finalized cut despite newer canonical eligible cut
multi-source cut with missing predecessor/causal dependency
finality proof controlled by source-forging principal
LOCAL_CAS source mutates after precheck but before transaction
```

Expected outcomes are fixed by Matrix V13/Inventory V13; double-read/retry cannot substitute for finality.

## 5. Permanent regression extension

All inherited R7/R8 and R9-X01..R9-X166 remain mandatory.

Add:

```text
R9-X167 external head H verified then source advances before local genesis commit, no finalized cut -> genesis denied/UNKNOWN; stale H cannot commit as COMPLETE
R9-X168 EXTERNAL_NONFINALIZABLE source represented COMPLETE from latest-head/freshness proof only -> denied
R9-X169 finalized canonical cut C; source publishes strictly >C event before local commit -> same cut remains valid; no timing remint
R9-X170 source correction/reorg changes semantic fact <=C after attestation before genesis -> coverage stale; genesis denied until new valid closure
R9-X171 caller selects older favorable finalized cut C0 while frozen rule requires canonical C1 -> denied
R9-X172 multi-source vector contains fact whose required predecessor lies outside another source cut -> causal closure FAIL; COMPLETE denied
R9-X173 finality proof is forgeable/common-controlled by principal able to rewrite relied source prefix without independent self-verification -> finality invalid; COMPLETE denied
R9-X174 LOCAL_CAS source head changes between preparation and atomic SystemGenesis transaction -> CAS fails; no partial genesis
```

Current explicit R9 ceiling:

```text
R9-X01..R9-X174
```

Current totals:

```text
R7 = 26
R8 = 40
R9 = 174
TOTAL = 240 explicit regression scenarios
```

## 6. Current manifest / quarantine resolution

Current normative manifest is resolved only through the stable binding and must resolve Manifest V17 in the same exact subject.

Policy V5 remains generation-agnostic and obtains `M(S)` only from that binding. Protocol current selector, Policy selector and binding selector must resolve exactly one identical `M(S)`.

Any stale/historical selector or member count remains fail-closed under inherited V17 regression R9-X163..X166.

## 7. Qualification reset / sequence

Matrix V13 / Inventory V13 / Protocol V18 / Correction V17 / binding / Manifest V17 are normative changes before CP1.

```text
CLEAN PASS COUNT = 0
ALL PRIOR ROOT/PASS/CANDIDATE CREDIT = HISTORICAL ONLY
```

Required sequence:

```text
freeze exact corrected normative subject S0
-> Lane A-H whole-composition impact attack including finality/cut attacks
-> subject-bound SA-11 via Policy V5
-> exact normative root
-> CP1
-> NO normative write
-> CP2 same root
-> R7 + R8 + R9-X01..X174 regression = 240/240 required
-> final consistency + exact QAO-only lineage proof
-> self-reference-free candidate
-> exactly one binder-only child
-> independent external whole-architecture re-audit
```

## 8. Future Human–ARE interface requirement

Preserve the future Human–ARE conversational interface for explanation/status/research/hypothesis/simulation/audit inspection and structured operator intent. Chat has zero ambient broker/capital authority and cannot bypass THINK->PROVE->ACT, Safety, scientific, selection, mutation-boundary, reconciliation or execution gates.

## 9. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
