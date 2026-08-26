# AHFMES ARE — Self-Audit Council Protocol V16

Status: **MANDATORY PRE-EXTERNAL-REAUDIT GOVERNANCE / R9-01 PREGENESIS COVERAGE INDEPENDENCE / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Composition

Immutable base:

```text
BASE_PROTOCOL_V15_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V15.md
BASE_PROTOCOL_V15_GIT_BLOB_SHA = c27aacc15247c062a5bb86f737913510cf96fcfa
```

All V15->V2 rules remain except current Matrix/Inventory/Manifest generation, pregenesis coverage-independence attacks and regression ceiling are extended/narrowed here.

Current manifest resolves only through the stable binding. Matrix V12 is sole current machine source; Inventory V12 is current closed-world companion.

## 1. Historical impact disposition

Exact internal impact subject:

```text
deda94ea56520bfa2324031206b0a23c82a77eec
```

Disposition:

```text
CHANGES_REQUIRED
ROOT = R9-01
NEW R9 ROOT = NO
```

Finding:

```text
IA11-DE01 PREGENESIS_COVERAGE_SELF_ATTESTATION
```

V9-V11 correctly closed target-instance authorization replay, static-vs-final gen0 drainability, authorization race, stale cutoff, coverage time remint and materiality-rule omission. The residual arose because the same Bootstrap-Audit control imported/reconciled discretionary history and attested completeness of that history.

## 2. Coverage independence attack charter

Audit must distinguish:

```text
Bootstrap-Import control
Bootstrap-Coverage-Audit control
exact source/capture producer controls
Genesis control
```

Required attacks:

```text
Importer omits material legacy/search/debt fact D then self-attests COMPLETE
Importer and coverage auditor are different processes but same common-control principal
coverage auditor common-controlled with source/capture producer
same-control exception claimed without external/self-verifying unsuppressible source proof
unknown control relation treated independent
```

Expected:

```text
discretionary source -> independent common-control boundary required
same-control only with positively external/self-verifying source that importer cannot forge/suppress/rewrite
UNKNOWN independence -> COMPLETE denied
```

## 3. Source-contract / source-frontier charter

Freeze before authorization/import:

```text
PREGENESIS_COVERAGE_SOURCE_CONTRACT_ROOT
```

Attack:

```text
materiality rule covers class C but source contract omits C
source contract maps C to a source importer can suppress without independent witness
capture/gap/canonicalization rule changed after r0
source head advances after attestation but before genesis
unbound source evidence substituted at coverage time
```

Expected: source-contract totality/currentness fails; COMPLETE/genesis denied or conservative UNKNOWN consequences apply.

## 4. Knowledge-obligation anti-suppression charter

The current knowledge-obligation fold must be derived from the independent source observation frontier plus frozen materiality rule, not from importer journal contents alone.

Attack:

```text
source contains D
D is material/applicable
import revision r omits D
```

Expected:

```text
D still creates semantic obligation OD
coverage COMPLETE invalid while OD absent from revision
reconcile same instance including D or retain conservative UNKNOWN lineage
```

A missing importer record cannot erase an independently observable obligation.

## 5. UNKNOWN source completeness

`SOURCE_UNKNOWN_CONSERVATIVE` is not clean scientific history.

Attack:

```text
source completeness unknown
coverage attestation UNKNOWN_CONSERVATIVE
later proof/Challenge tries to treat legacy/search/debt lineage as zero/complete
```

Expected: inherited unknown debt/lineage consequences remain and no clean privilege is obtained until positively resolved under later governed evidence.

## 6. Downstream cross-root attack

Attack full path:

```text
suppress adverse pregenesis scientific/search fact D
-> attempt clean genesis
-> research/proof/Challenge
-> Promotion/current reliance
-> normal new risk
```

Expected: independent source coverage catches D or UNKNOWN debt persists; suppression cannot create clean proof/selection/capital privilege.

R9-06 broker/exposure reconciliation remains an additional downstream gate but is not relied upon to repair scientific-history laundering.

## 7. Permanent regression extension

All inherited R7/R8 and R9-X01..R9-X150 remain mandatory.

Add:

```text
R9-X151 Bootstrap-Import and Bootstrap-Coverage-Audit same common-control principal on discretionary legacy source -> COVERAGE_CURRENT_COMPLETE denied
R9-X152 same control but exact source is externally self-verifying and importer cannot forge/suppress/rewrite -> exception may be valid only with positive proof
R9-X153 authoritative source contains material D; importer omits D -> source-derived obligation still appears; COMPLETE denied until reconcile/UNKNOWN
R9-X154 materiality universe includes class C but PREGENESIS_COVERAGE_SOURCE_CONTRACT_ROOT has no authoritative source mapping -> source-contract totality invalid
R9-X155 source head/gap/freshness state advances after coverage attestation before genesis -> old coverage non-current; stale genesis loses
R9-X156 coverage auditor common-controlled with Genesis -> coverage SoD invalid
R9-X157 coverage auditor independent of importer but common-controlled with discretionary capture producer -> COMPLETE denied absent self-verifying exception
R9-X158 source completeness UNKNOWN represented SOURCE_COMPLETE/COVERAGE_COMPLETE -> denied; conservative UNKNOWN required
R9-X159 r->r+1 reconciliation attempts to alter source contract/capture/gap rules -> static conflict/denied
R9-X160 coverage attestation uses proof from source/frontier not bound by current source contract -> invalid
R9-X161 UNKNOWN_CONSERVATIVE legacy/search/debt state treated later as zero debt/clean history -> proof/selection privilege denied
R9-X162 two processes/machines under same control principal represented as independent import/coverage witnesses -> common-control collapse; COMPLETE denied
```

Current explicit ceiling:

```text
R9-X01..R9-X162
```

## 8. Independent lanes before Clean Pass #1

Run independently:

```text
LANE-A instance / target authorization / authorization-slot uniqueness
LANE-B gen0 static/final partition / drainability / materiality
LANE-C crash / coverage opportunity / source-currentness / CAS / terminality
LANE-D pre-system object/writer/control SoD including importer-vs-coverage independence
LANE-E source contract / legacy/scientific/evidence/debt completeness / UNKNOWN propagation
LANE-F Challenge/revalidation/rollback regression
LANE-G Safety/capital/broker/mutation-boundary composition
LANE-H outside-family integrator / temporal/remint / historical-authority laundering
```

No lane inherits another PASS. One reproducible legal path blocks qualification.

## 9. Clean reset / sequence

Normative V12/V16 generation resets clean count to zero.

Required sequence:

```text
freeze corrected normative bytes
-> Lane A-H whole-composition impact attack
-> SA-11 whole-blob quarantine on exact corrected S0
-> compute exact normative root
-> CP1
-> no normative write
-> CP2 same root
-> R7 + R8 + R9-X01..X162 regression
-> final consistency / QAO-only qualification lineage
-> self-reference-free candidate
-> exactly one binder-only child
-> independent external whole-architecture re-audit
```

## 10. Progress discipline / chat requirement

Every completed external audit/re-audit result must be recorded in GitHub progress metadata. The future Human–ARE conversational interface requirement remains preserved: chat is structured intent/explanation only and cannot bypass THINK->PROVE->ACT, Safety, scientific, capital or broker gates.

## 11. Firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
