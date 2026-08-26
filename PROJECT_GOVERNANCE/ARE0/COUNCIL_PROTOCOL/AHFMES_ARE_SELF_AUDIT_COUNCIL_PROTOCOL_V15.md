# AHFMES ARE — Self-Audit Council Protocol V15

Status: **MANDATORY PRE-EXTERNAL-REAUDIT GOVERNANCE / R9-01 FROZEN MATERIALITY + ONE COVERAGE SLOT / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable base:

```text
BASE_PROTOCOL_V14_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V14.md
BASE_PROTOCOL_V14_GIT_BLOB_SHA = c429fc8f13737ec0e78da5dd826b17a92f9fba99
```

All V14->V2 rules remain except materiality/applicability and coverage opportunity identity attacks/regression ceiling are narrowed here.

Current manifest resolves only through the stable binding. Matrix V11 is sole current machine source; Inventory V11 is current closed-world companion.

## 1. Historical V10 impact disposition

Exact internal impact subject:

```text
16d75c0a27580f6f24de433692e61e705dc39380
```

Disposition:

```text
CHANGES_REQUIRED
ROOT = R9-01
NEW R9 ROOT = NO
```

Findings:

```text
IA10-C01 COVERAGE_ATTESTATION_TIME_REMINT
IA10-E01 PREGENESIS_MATERIALITY_RULE_UNFROZEN
```

No clean-pass credit exists for that subject.

## 2. Materiality/applicability attack charter

Audit the frozen `PREGENESIS_MATERIALITY_APPLICABILITY_ROOT` against known facts that are favorable/unfavorable to later scientific or capital privilege.

Required attacks:

```text
known fact D omitted by declaring it immaterial
materiality UNKNOWN treated as non-applicable
NON_APPLICABLE proof uses result/PnL/desired Champion/desired Safety state
materiality rule altered through r->r+1 reconciliation
fact class omitted from the governed materiality universe despite affecting a final-derived gen0 field or later authority predicate
```

Expected:

```text
TRUE -> obligation
FALSE -> only positive deterministic proof under frozen rule
UNKNOWN -> obligation / conservative include
post-import rule change -> static conflict / denied
```

## 3. Coverage opportunity anti-remint charter

For unchanged exact state:

```text
instance K
current revision r
current knowledge root O
cutoff/materiality rules fixed
```

there is exactly one:

```text
PREGENESIS_COVERAGE_OPPORTUNITY_KEY
```

Attack:

```text
A0 requested at F0
service delayed/restarted
A1 requested at F1 > F0
same K/r/O/rules
```

Expected:

```text
same opportunity key
same attestation key
FIRST_PREGENESIS_COVERAGE_ELIGIBLE_INFORMATION_TIME remains immutable payload
same payload -> existing
conflicting first-eligible time/payload -> IntegrityDefect
```

Time/frontier/retry cannot mint a second current attestation.

## 4. State-change currentness charter

If revision or current knowledge root changes:

```text
r0/O0/Q0/A0
-> D governed-known or revision advances
-> r1/O1
```

Expected:

```text
Q0/A0 non-current
new semantic state may derive exactly one Q1
A0 cannot be replayed
```

A new opportunity requires actual semantic state change, not scheduling.

## 5. Exclusion-proof currentness

Every NON_APPLICABLE exclusion in an attestation is a relied dependency.

If its proof becomes materially invalid before SystemGenesis, attestation is non-current and genesis denied until current coverage is re-established.

A post-outcome or interested-principal classification cannot create/repair an exclusion proof.

## 6. Permanent regression extension

All inherited R7/R8 and R9-X01..R9-X140 remain mandatory.

Add:

```text
R9-X141 same K/r/O, A0 at F0 and retry A1 at F1 -> same opportunity/attestation slot; no time remint
R9-X142 known fact D with UNKNOWN materiality -> D included as required obligation
R9-X143 known fact D excluded without positive frozen-rule NON_APPLICABLE proof -> coverage invalid
R9-X144 r0->r1 reconciliation attempts to alter PREGENESIS_MATERIALITY_APPLICABILITY_ROOT -> static conflict/denied
R9-X145 service fails to materialize attestation at first eligible frontier then retries later with unchanged state -> same opportunity; first eligible time unchanged
R9-X146 knowledge root O0->O1 or revision r0->r1 -> Q0/A0 stale; exactly one new Q1 allowed for new state
R9-X147 same coverage opportunity key with conflicting attestation payload/first-eligible time -> IntegrityDefect; no alternate slot
R9-X148 NON_APPLICABLE proof relied by current attestation becomes invalid before genesis -> attestation stale; genesis denied
R9-X149 post-result/PnL/desired-policy evidence used to classify known fact NON_APPLICABLE -> invalid under frozen performance-blind rule
R9-X150 fact affecting any final-derived gen0 field or later authority predicate omitted from materiality universe -> GEN0/static materiality totality invalid; genesis denied
```

Current explicit ceiling:

```text
R9-X01..R9-X150
```

No prior seed is deleted.

## 7. Isolated lanes

Before Clean Pass #1 rerun independently:

```text
LANE-A instance / target authorization / issuance uniqueness
LANE-B gen0 field partition / materiality / drainability
LANE-C coverage opportunity / timing / crash / CAS / terminality
LANE-D pre-system object / writer / SoD totality
LANE-E legacy/scientific/evidence/debt completeness and exclusion proof
LANE-F Safety/capital/broker/cross-root/outside-family composition
```

One reproducible legal path blocks qualification.

## 8. Clean reset / dispatch

Normative V11/V15 generation resets clean count to zero.

Required sequence:

```text
freeze corrected normative bytes
-> Lane A-F whole-composition impact attack
-> SA-11 whole-blob quarantine on exact corrected pre-pass subject
-> compute exact normative root
-> CP1
-> no normative write
-> CP2 same root
-> R7 + R8 + R9-X01..X150 regression
-> final consistency / qualification lineage
-> self-reference-free candidate
-> one binder-only child
-> independent external whole-architecture re-audit
```

## 9. Firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
