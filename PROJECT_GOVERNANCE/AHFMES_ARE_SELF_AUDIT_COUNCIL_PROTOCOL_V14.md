# AHFMES ARE — Self-Audit Council Protocol V14

Status: **MANDATORY PRE-EXTERNAL-REAUDIT GOVERNANCE / R9-01 SEALED AUTHORIZATION + CURRENT COVERAGE / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable base:

```text
BASE_PROTOCOL_V13_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V13.md
BASE_PROTOCOL_V13_GIT_BLOB_SHA = 84837b0a1e29025784ce7b87df0fec8de8aac174
```

All V13->V2 rules remain except current machine/inventory references, authorization-uniqueness/cutoff-currentness attacks and regression ceiling are extended/narrowed here.

Current manifest resolves only through the stable binding. Matrix V10 is the sole machine-semantic source; Inventory V10 is the current closed-world companion.

## 1. Historical V9 impact disposition

Exact internal impact subject:

```text
7c8111fe78f8b6c47609c024f4cb34ac885e474f
```

Disposition:

```text
CHANGES_REQUIRED
NEW R9 ROOT = NO
ROOT = R9-01
```

Findings:

```text
IA9-A01 BOOTSTRAP_AUTHORIZATION_RACE_LOTTERY
IA9-C01 GENESIS_CUTOFF_STALE_FRONTIER_SELECTION
```

No clean-pass credit exists for that subject.

## 2. Authorization-slot independence attack

Audit must prove one semantic authorization slot per instance/ordinal and no scheduler-selected constitution.

Attack:

```text
same instance K
journal ABSENT
two materially conflicting issuer assertions A1/S1 and A2/S2
concurrent bootstrap attempts
```

Expected:

```text
BOOTSTRAP_AUTHORIZATION_ISSUANCE_CLOSURE_ROOT = INVALID/UNKNOWN
no usable AUTHORIZED_SEALED slot
no initial import
time/CAS order cannot choose A1 or A2
```

Duplicate semantically identical assertion may be idempotent; materially conflicting assertions are not alternatives.

`A-BOOTSTRAP-AUTHORIZE` is a direct exogenous constitutional issuance action. It MUST NOT be interpreted as authority granted by the `BootstrapAuthorizationSlot` that it creates. Any self-authorized slot-creation interpretation is bootstrap circularity and fails.

## 3. Authorization-slot lifecycle attacks

Required:

```text
slot ABSENT -> AUTHORIZED_SEALED only after unique sealed issuance closure
initial import atomically AUTHORIZED_SEALED -> BOUND_TO_JOURNAL + journal r0
genesis atomically BOUND_TO_JOURNAL -> CONSUMED + journal terminal + gen0
```

Attack partial/crash states:

```text
journal r0 exists while slot still AUTHORIZED_SEALED
slot BOUND but journal absent
SystemGenesis exists while slot BOUND/reusable
CONSUMED slot reused for second journal/genesis
```

All are invalid/unreachable under atomic semantics.

## 4. Knowledge-obligation / coverage-currentness attacks

Every material pre-genesis fact first governed-knowable creates a semantic obligation under V10.

Attack:

```text
current revision r covers F0
coverage attestation A0 binds obligation root O0
material D becomes governed-knowable -> O1 != O0
SystemGenesis tries A0
```

Expected:

```text
A0 non-current/stale
SystemGenesis denied
reconcile current journal if D absent
fresh attestation against current revision/O1 required
```

Caller may not select an older exact frontier to avoid D.

## 5. Coverage-attestation SoD / replay attacks

Required attacks:

```text
coverage attestation by Genesis/common-control alias
attestation for instance KA used on KB
attestation for revision r used on r+1
attestation obligation root O0 used after current root O1
known material obligation placed in UNKNOWN bucket
same coverage key with conflicting payload
```

All denied. `Bootstrap-Audit != Genesis` remains mandatory by common-control equivalence.

## 6. Drainability after late discovery

Re-run V13 drainability with current coverage object:

```text
r0 + current A0
D becomes known -> A0 stale
r0 -> r1 monotone reconciliation includes D
fresh A1 binds r1/current obligation set
SystemGenesis
```

Expected:

```text
same instance
same sealed/bound authorization slot
same static gen0 semantics
D included
final factual binding derives from r1
slot consumed + journal terminal atomically
```

No stale attestation, no second instance, no static-policy mutation.

## 7. Post-terminal timing boundary

A fact whose first governed information time is after the exact terminal genesis cutoff cannot reopen bootstrap.

It must enter incorporated post-genesis `A-LEGACY-RECONCILE` / proof-dependency invalidation / Safety/completeness consequences as applicable.

Attack delayed reporting intended to backdate the fact before cutoff. Information-time is governed first knowability, not source event timestamp. If evidence proves the fact was governed-known before cutoff, omission is a bootstrap/legacy defect and current downstream reliance must fail closed; it still does not create a second SystemGenesis.

## 8. Permanent regression extension

All inherited R7/R8 and R9-X01..R9-X128 remain mandatory.

Add:

```text
R9-X129 two conflicting target-valid authorization assertions for same slot -> issuance closure invalid; scheduler cannot select constitution
R9-X130 duplicate exact same authorization assertion for same slot -> one idempotent AUTHORIZED_SEALED semantic result
R9-X131 authorization-slot creation claimed to be authorized by the slot being created -> circular / denied; issuance must be exogenous
R9-X132 initial import commits journal r0 without atomic slot AUTHORIZED_SEALED->BOUND -> invalid state
R9-X133 SystemGenesis commits without atomic slot BOUND->CONSUMED -> invalid/reusable bootstrap authority denied
R9-X134 knowledge obligation root advances O0->O1 after coverage attestation -> old attestation stale; genesis denied
R9-X135 coverage attestation for revision r replayed after r->r+1 -> stale/revision mismatch
R9-X136 Genesis/common-control principal self-attests pregenesis coverage -> SoD invalid
R9-X137 known material obligation hidden in UNKNOWN bucket -> coverage attestation invalid
R9-X138 r0->r1 late discovery + fresh current coverage -> SystemGenesis remains drainable with static semantics unchanged
R9-X139 fact first knowable after terminal cutoff -> post-genesis legacy correction; no bootstrap reopen
R9-X140 same coverage key conflicting payload -> IntegrityDefect/invalid, no retry lottery
```

Current explicit ceiling:

```text
R9-X01..R9-X140
```

No prior seed is deleted.

## 9. Isolated lanes remain mandatory

Before Clean Pass #1 rerun independently:

```text
LANE-A instance / authorization / issuance uniqueness
LANE-B static/final-derived partition / drainability
LANE-C crash / CAS / cutoff / currentness / terminal consumption
LANE-D object / writer / pre-system authority / SoD totality
LANE-E scientific / legacy / debt / knowledge-obligation completeness
LANE-F Safety / capital / broker / outside-family composition
```

One reproducible legal path blocks qualification.

## 10. Clean reset / sequence

Normative V10/V14 generation resets clean count to zero.

Required sequence remains:

```text
freeze corrected normative bytes
-> Lane A-F whole-composition impact attack
-> SA-11 whole-blob quarantine on corrected pre-pass subject
-> exact normative root
-> CP1
-> no normative write
-> CP2 same root
-> R7 + R8 + R9-X01..X140 regression
-> final consistency / qualification lineage
-> self-reference-free candidate
-> one binder-only child
-> independent external whole-architecture re-audit
```

## 11. Firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
