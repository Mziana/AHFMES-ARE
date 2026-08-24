# AHFMES ARE-0 — Canonical Authority & Transition Matrix V9

Status: **SOLE CURRENT MACHINE SOURCE / R9-01 TARGET-SCOPED BOOTSTRAP AUTHORIZATION + DRAINABLE FINAL GENESIS BINDING / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition / replacement

Immutable machine base:

```text
BASE_MATRIX_V8_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V8.md
BASE_MATRIX_V8_GIT_BLOB_SHA = 32ba70e906c2afeee1c876a2587151ee65a287b6
```

All V8->V1 semantics remain in force except the V8 R9-01 authorization-binding, generation-#0 full-content commitment, pre-genesis revision/final-binding and SystemGenesis surfaces are replaced/narrowed by this V9.

```text
V9 R9-01 > EXACT V8 > EXACT V7 > EXACT V6 > EXACT V5 > EXACT V4 > EXACT V3 > EXACT V2 > EXACT V1
```

R9-02/R9-04/R9-05/R9-06/R9-07 remain unchanged.

Historical `SYSTEM_GENESIS_PAYLOAD_COMMITMENT_ROOT` is not a current rule requiring every final scientific/legacy-dependent generation-#0 field to be frozen before revision 0. Current semantics use the static/final-derived partition below.

## 1. Stable semantic instance identity remains payload- and authorization-independent

V8 stable identity remains exactly:

```text
BOOTSTRAP_INSTANCE_KEY = hash(
  ARE_SYSTEM_IDENTITY_ROOT,
  BOOTSTRAP_DOMAIN_IDENTITY_ROOT,
  literal SYSTEM_GENESIS_ORDINAL_0
)
```

Trust anchor, control identity, credentials, payload, policy, scientific history, static commitment, final scientific binding, retry/session/time/process/config identity are not instance-key material.

For one semantic ARE system/bootstrap domain/SystemGenesis ordinal #0 there is one durable `BootstrapInstanceJournal` lineage. A genuinely different constitutional system has a different instance key and receives no continuity, debt erasure or inherited privilege from another system.

## 2. Closed generation-#0 field partition and static authority-semantics commitment

Before any bootstrap authorization assertion or import write, every field of every exact generation-#0 object in the incorporated SystemGenesis universe is classified exactly once by an immutable:

```text
GEN0_FIELD_PARTITION_ROOT
```

into one of two disjoint classes:

```text
STATIC_PRECOMMITTED
FINAL_REVISION_DERIVED
```

### 2.1 STATIC_PRECOMMITTED

`STATIC_PRECOMMITTED` contains exact authority/policy/control semantics that may not vary with late scientific discovery, including as applicable:

```text
initial RoleManifest payloads
initial PrincipalRoleBindingRecord payloads
TrustedAuthorityRegistry #0 static authority content
GovernanceRootRotationPolicy #0
GovernanceRootKernelCapabilities #0
GenesisCapitalSafetyContainmentSpec
GenesisSafetyChangePolicy and constitutional Safety trigger/policy semantics
Champion/Challenge eligibility, comparator-selection rule, accounting, error-control and allocation-order policy
registry schemas, writer/transition semantics and static authority envelopes
all other generation-#0 fields whose value can grant, deny, route or widen authority
```

### 2.2 FINAL_REVISION_DERIVED

`FINAL_REVISION_DERIVED` contains only factual state whose exact value is required to depend on the final current pre-genesis scientific/history/exposure/debt lineage, including as applicable:

```text
LegacyCutoffClosureRecord factual closure payload
LegacyScientificStateHead #0 factual lineage payload
seeded ExposureLedger #0 factual state
seeded EvidenceGovernanceHead #0 factual state
seeded OperationalFidelity/completeness/uncertainty factual state where applicable
legacy incumbent/deployed-reference factual identity when the frozen bootstrap comparator-selection rule requires actual reachable legacy behavior
other generation-#0 factual fields mechanically derived from the final imported lineage
```

A FINAL_REVISION_DERIVED field may provide a factual identity consumed by a frozen static rule, but it may not select/change the rule itself.

### 2.3 Partition totality / anti-lottery theorem

For every generation-#0 field the partition freezes:

```text
exact field path
exact class
for STATIC_PRECOMMITTED: exact payload
for FINAL_REVISION_DERIVED:
  exact deterministic derivation-rule root
  exact allowed source coordinates in final pre-genesis lineage
  exact conservative UNKNOWN rule
  exact non-widening authority envelope
```

Define:

```text
GEN0_FIELD_PARTITION_TOTALITY_VALID =
  every generation-#0 field classified exactly once
  + no overlap
  + no unclassified field
  + every FINAL_REVISION_DERIVED mapping deterministic/total for admitted inputs
  + FINAL_REVISION_DERIVED cannot create/alter Role/SoD/writer/transition/Safety bound/
    comparator-selection rule/accounting/error/order/governance or any authority envelope
  + material UNKNOWN maps only to conservative/no-wider authority state
```

UNKNOWN/overlap/unclassified/dynamic privilege => SystemGenesis DENIED.

Freeze before authorization/import:

```text
STATIC_GEN0_AUTHORITY_SEMANTICS_COMMITMENT_ROOT = hash(
  GEN0_FIELD_PARTITION_ROOT,
  exact payload of every STATIC_PRECOMMITTED field,
  exact derivation-rule/source/UNKNOWN/non-widening specification for every FINAL_REVISION_DERIVED field
)
```

This root is immutable for the bootstrap journal lineage. It freezes authority semantics and factual derivation rules, not final scientific factual values that may legitimately advance through reconciliation.

## 3. Target-instance-scoped exogenous bootstrap authorization

A generic trust/control assertion is not sufficient bootstrap authority.

Before initial import, the exogenous bootstrap trust issuer must positively attest an exact:

```text
BOOTSTRAP_INSTANCE_AUTHORIZATION_ASSERTION_ROOT
```

whose attested payload binds at minimum:

```text
target BOOTSTRAP_INSTANCE_KEY
target ARE_SYSTEM_IDENTITY_ROOT
target BOOTSTRAP_DOMAIN_IDENTITY_ROOT
literal SYSTEM_GENESIS_ORDINAL_0
STATIC_GEN0_AUTHORITY_SEMANTICS_COMMITMENT_ROOT
BOOTSTRAP_TRUST_ANCHOR_ROOT / exact issuer-trust identity
exact Genesis control identity
exact independent Bootstrap-Audit control identity
positive common-control separation evidence root
exact bootstrap capability scope root
```

The attestation must be verifiably issued for that exact target. A generic/untargeted assertion cannot be locally re-hashed into authorization for another instance.

Define:

```text
BOOTSTRAP_AUTHORIZATION_BINDING_ROOT = hash(
  BOOTSTRAP_INSTANCE_KEY,
  BOOTSTRAP_INSTANCE_AUTHORIZATION_ASSERTION_ROOT,
  BOOTSTRAP_TRUST_ANCHOR_ROOT,
  exact Genesis control identity,
  exact Bootstrap-Audit control identity,
  positive separation evidence root,
  exact bootstrap capability scope root,
  STATIC_GEN0_AUTHORITY_SEMANTICS_COMMITMENT_ROOT
)
```

Mandatory predicate:

```text
BOOTSTRAP_AUTHORIZATION_TARGET_VALID =
  assertion.target_instance == journal.BOOTSTRAP_INSTANCE_KEY
  AND assertion.target_system == ARE_SYSTEM_IDENTITY_ROOT
  AND assertion.target_domain == BOOTSTRAP_DOMAIN_IDENTITY_ROOT
  AND assertion.ordinal == SYSTEM_GENESIS_ORDINAL_0
  AND assertion.static_commitment == STATIC_GEN0_AUTHORITY_SEMANTICS_COMMITMENT_ROOT
  AND issuer/trust/controls/separation/scope verification = PASS
```

Authorization for instance `KA` cannot satisfy import/genesis on `KB != KA`. Reusing the same operator, credential or trust anchor does not confer cross-instance authority without a distinct valid issuer assertion explicitly targeting `KB`.

After `IMPORT_RECORDED[0]`, target authorization and static commitment are immutable for the lineage. Changed trust/control/separation/scope/static commitment => conflict/denial on the same instance, not a new slot.

## 4. Pre-genesis scientific revision lineage

For revision `r` define:

```text
PREGENESIS_IMPORT_REVISION_ROOT[r] = hash(
  BOOTSTRAP_INSTANCE_KEY,
  BOOTSTRAP_AUTHORIZATION_BINDING_ROOT,
  STATIC_GEN0_AUTHORITY_SEMANTICS_COMMITMENT_ROOT,
  revision r,
  exact parent revision identity or EMPTY,
  exact pre-genesis scientific-state payload root,
  exact legacy/search/evidence/exposure/debt lineage root,
  exact uncertainty/conservative-state root,
  GOVERNED_PREGENESIS_INFORMATION_FRONTIER_ROOT[r],
  KNOWN_PREGENESIS_MATERIAL_FACT_SET_ROOT[r]
)
```

Only scientific/history/exposure/debt/uncertainty factual lineage may advance through reconciliation. Authorization, partition, static payload and derivation rules remain frozen.

Exact same-instance reconciliation:

```text
IMPORT_RECORDED[r] -> IMPORT_RECORDED[r+1]
= A-PREGENESIS-IMPORT[RECONCILE]
```

requires all:

```text
same BOOTSTRAP_INSTANCE_KEY
BOOTSTRAP_AUTHORIZATION_TARGET_VALID
same BOOTSTRAP_AUTHORIZATION_BINDING_ROOT
same STATIC_GEN0_AUTHORITY_SEMANTICS_COMMITMENT_ROOT
parent = exact current revision r
revision = r+1 exactly
all previously governed-known history/search/evidence/exposure/debt retained
new material facts appended, never selectively deleted
known debt/exposure/uncertainty not reduced merely by reconciliation
no change to STATIC_PRECOMMITTED field or FINAL_REVISION_DERIVED derivation rule
no outcome/PnL/performance-selected retention
Safety/containment cannot weaken
CAS exact current journal head
```

Non-monotone or static-policy-changing reconciliation is denied and cannot mint a new instance.

## 5. Canonical final cutoff and final generation-#0 factual binding

SystemGenesis closes one exact canonical governed information frontier:

```text
GENESIS_CUTOFF_INFORMATION_FRONTIER_ROOT
```

The final current revision `r` must positively satisfy:

```text
PREGENESIS_KNOWLEDGE_COVERAGE_CURRENT(r, cutoff) =
  every material fact governed-knowable through cutoff is represented in the current revision lineage
  + every known legacy/search/evidence/exposure/debt obligation through cutoff is accounted
  + no known material fact is hidden by labeling the universe UNKNOWN
```

`UNKNOWN` is allowed only for genuinely unresolved/unknowable universe portions and must carry conservative unknown-debt/unknown-lineage consequences. A governed-known material fact omitted through the cutoff makes closure invalid regardless of COMPLETE/UNKNOWN label.

Derive terminal factual closure:

```text
FINAL_PREGENESIS_CLOSURE_ROOT[r] = hash(
  PREGENESIS_IMPORT_REVISION_ROOT[r],
  GENESIS_CUTOFF_INFORMATION_FRONTIER_ROOT,
  exact LegacyCutoffClosureRecord payload,
  exact known-material coverage root,
  COMPLETE or conservative UNKNOWN class,
  exact conservative unknown-debt/unknown-lineage consequences
)
```

Then deterministically derive every FINAL_REVISION_DERIVED field under the frozen partition/rules:

```text
FINAL_GEN0_FACTUAL_BINDING_ROOT[r] = hash(
  STATIC_GEN0_AUTHORITY_SEMANTICS_COMMITMENT_ROOT,
  PREGENESIS_IMPORT_REVISION_ROOT[r],
  FINAL_PREGENESIS_CLOSURE_ROOT[r],
  exact deterministic output of every FINAL_REVISION_DERIVED field
)
```

For one exact static commitment + current revision + cutoff/closure there is exactly one admissible final factual binding. Alternate derived payload => invalid/IntegrityDefect; no lottery.

The complete terminal generation-#0 object set is content-addressed at SystemGenesis as:

```text
SYSTEM_GENESIS_COMPOSITE_OBJECT_SET_ROOT = hash(
  exact STATIC_PRECOMMITTED field payloads,
  exact FINAL_REVISION_DERIVED field outputs,
  GEN0_FIELD_PARTITION_ROOT
)
```

This composite root is a terminal result, not a pre-import commitment to final scientific factual values.

## 6. BootstrapInstanceJournal state machine

The V8 journal remains the sole pre-system persistence lineage:

```text
ABSENT
IMPORT_RECORDED[r]
SYSTEM_GENESIS_COMMITTED
```

### 6.1 Initial import

```text
ABSENT -> IMPORT_RECORDED[0]
= A-PREGENESIS-IMPORT[INITIAL]
```

Atomic creation binds:

```text
BOOTSTRAP_INSTANCE_KEY
GEN0_FIELD_PARTITION_ROOT
STATIC_GEN0_AUTHORITY_SEMANTICS_COMMITMENT_ROOT
BOOTSTRAP_INSTANCE_AUTHORIZATION_ASSERTION_ROOT
BOOTSTRAP_AUTHORIZATION_BINDING_ROOT
PREGENESIS_IMPORT_REVISION_ROOT[0]
```

Prerequisites include `BOOTSTRAP_AUTHORIZATION_TARGET_VALID` and `GEN0_FIELD_PARTITION_TOTALITY_VALID`.

Same instance + exact same bound payload => existing/idempotent result. Conflicting authorization/static commitment/revision-0 payload => INVALID; no second journal.

### 6.2 Reconciliation

Reconciliation is exactly §4. It can advance only scientific/factual lineage on the same journal and remains legally drainable to SystemGenesis.

## 7. SystemGenesis atomic terminal commit

For exact current revision `r`:

```text
IMPORT_RECORDED[r] -> SYSTEM_GENESIS_COMMITTED
= A-SYSTEM-GENESIS
```

One local semantic transaction atomically:

```text
CAS exact current BootstrapInstanceJournal head/revision r
verify BOOTSTRAP_INSTANCE_KEY
verify BOOTSTRAP_AUTHORIZATION_TARGET_VALID
verify immutable BOOTSTRAP_AUTHORIZATION_BINDING_ROOT
verify GEN0_FIELD_PARTITION_TOTALITY_VALID
verify immutable STATIC_GEN0_AUTHORITY_SEMANTICS_COMMITMENT_ROOT
verify PREGENESIS_KNOWLEDGE_COVERAGE_CURRENT through exact cutoff
verify current PREGENESIS_IMPORT_REVISION_ROOT[r]
derive FINAL_PREGENESIS_CLOSURE_ROOT[r]
derive exact FINAL_GEN0_FACTUAL_BINDING_ROOT[r]
instantiate every generation-#0 field according to the frozen partition
verify exact SYSTEM_GENESIS_COMPOSITE_OBJECT_SET_ROOT
bind SystemGenesisManifest to instance/auth/static/final-revision/cutoff/final-binding/composite roots
bind gen-0 scientific/legacy/exposure/evidence factual heads to final revision r
mark BootstrapInstanceJournal SYSTEM_GENESIS_COMMITTED
consume bootstrap authority permanently
```

### 7.1 Reconcile/genesis race

If reconciliation `r -> r+1` commits before SystemGenesis, the stale genesis CAS on `r` loses and may retry only against `r+1` on the same instance/static/auth lineage.

If SystemGenesis commits first, any pre-genesis reconcile/import/genesis retry loses against terminal state. A material fact first governed-knowable after the bound genesis cutoff follows incorporated post-genesis legacy/scientific correction + dependency-invalidation semantics; it cannot reopen bootstrap or create SystemGenesis #0 again.

### 7.2 Crash theorem

Crash after terminal semantic commit observes the same terminal SystemGenesis result. Crash before commit observes the same journal/current revision. Retry cannot change target authorization, static commitment, partition or instance key.

## 8. Exact bootstrap authorities

| Authority | Issuer approval | Executor | Usage | Exact prerequisites | Capital |
|---|---|---|---|---|---|
| `A-PREGENESIS-IMPORT[INITIAL]` | exogenous issuer assertion explicitly targeting exact instance + static commitment | Bootstrap-Audit | ONE_SHOT per `BOOTSTRAP_INSTANCE_KEY` initial import | journal ABSENT; target-valid authorization; partition total; bind r0 | NO |
| `A-PREGENESIS-IMPORT[RECONCILE]` | same immutable target-scoped authorization | Bootstrap-Audit | ONE_SHOT per exact next revision | same instance/auth/static/partition; monotone factual lineage; CAS current head | NO |
| `A-SYSTEM-GENESIS` | same immutable target-scoped authorization | Genesis | ONE_SHOT per `BOOTSTRAP_INSTANCE_KEY` | exact current revision + canonical cutoff/coverage + deterministic final binding + atomic terminal consumption | NO |

A pre-system authorization assertion for another instance, an untargeted assertion, or import evidence not bound to the current journal cannot satisfy any row.

## 9. Forbidden control planes

```text
authorization issued for KA used on KB
untargeted/generic trust assertion locally rebound to arbitrary instance
static Role/Safety/governance/comparator/error/order policy changed through scientific reconciliation
FINAL_REVISION_DERIVED field used to add/widen authority or choose a new rule
known-before-cutoff material fact hidden under UNKNOWN
late scientific discovery forces stale gen-0 factual head or mutation of frozen static semantics
same final revision producing two different final factual bindings
reconcile/genesis race allowing two terminal results
post-genesis fact reopening bootstrap or SystemGenesis #0
changed trust/control/static content reminting instance identity
```

## 10. Static boundary

This Matrix grants no ARE-0 closure, implementation, P001 substantive research, production, live/paper trading or PR-merge authority.