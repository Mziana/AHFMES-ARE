# AHFMES ARE-0 — Canonical Authority & Transition Matrix V8

Status: **SOLE CURRENT MACHINE SOURCE / R9-01 STABLE SYSTEM INSTANCE + FULL GENESIS PAYLOAD COMMITMENT / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition / replacement

Immutable machine base:

```text
BASE_MATRIX_V7_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V7.md
BASE_MATRIX_V7_GIT_BLOB_SHA = fc725fb8ea603f879dfa44ddd91a4c983c6de1fb
```

All V7->V1 semantics remain except V7 §§1–6 bootstrap instance identity, bootstrap authorization binding, generation-#0 commitment and corresponding bootstrap authority prerequisites are replaced/narrowed by this V8.

```text
V8 R9-01 > EXACT V7 > EXACT V6 > EXACT V5 > EXACT V4 > EXACT V3 > EXACT V2 > EXACT V1
```

R9-02/R9-04/R9-05/R9-06/R9-07 remain unchanged.

Historical `BOOTSTRAP_EPOCH_KEY` and V7 control-derived `BOOTSTRAP_INSTANCE_KEY` are not current authority-slot identities.

## 1. Immutable semantic system identity

Before any bootstrap write, external constitutional setup establishes exactly one immutable:

```text
ARE_SYSTEM_IDENTITY_ROOT
BOOTSTRAP_DOMAIN_IDENTITY_ROOT
```

for the intended semantic ARE system/bootstrap domain.

These are **system-birth identities**, not operator, key, machine, process, retry, configuration, payload or policy identities. They are not caller-selectable after any bootstrap attempt exists.

For the same semantic ARE system:

```text
ARE_SYSTEM_IDENTITY_ROOT = invariant forever
BOOTSTRAP_DOMAIN_IDENTITY_ROOT = invariant for SystemGenesis ordinal #0
```

A trust-anchor rotation, Genesis operator replacement, Bootstrap-Audit replacement, credential rotation, process/machine move or configuration change **does not** create a new ARE system identity.

A genuinely new `ARE_SYSTEM_IDENTITY_ROOT` denotes a different constitutional system and cannot inherit, overwrite, sanitize, supersede or claim continuity with the prior system's scientific/debt/bootstrap lineage.

## 2. Payload- and authorization-independent bootstrap instance key

Define exactly:

```text
BOOTSTRAP_INSTANCE_KEY = hash(
  ARE_SYSTEM_IDENTITY_ROOT,
  BOOTSTRAP_DOMAIN_IDENTITY_ROOT,
  literal SYSTEM_GENESIS_ORDINAL_0
)
```

The key MUST NOT contain:

```text
BOOTSTRAP_TRUST_ANCHOR_ROOT
Genesis control identity
Bootstrap-Audit control identity
control-separation evidence
credential/key/process/machine identity
scientific/legacy/search/evidence/debt payload
generation-#0 payload or schema
containment/change/Safety policy
Champion/comparator/accounting/error/order policy
retry/session/time/config identity
```

Thus every attempt to create SystemGenesis #0 for the same semantic system/domain collides on exactly one durable `BootstrapInstanceJournal` lineage regardless of authorization or payload changes.

## 3. Bootstrap authorization binding is payload, not instance identity

At the first successful journal creation derive:

```text
BOOTSTRAP_AUTHORIZATION_BINDING_ROOT = hash(
  BOOTSTRAP_TRUST_ANCHOR_ROOT,
  exact Genesis control identity,
  exact independent Bootstrap-Audit control identity,
  positive common-control separation evidence root,
  exact bootstrap capability scope root
)
```

Required capability scope remains only governed pre-genesis import/reconciliation + SystemGenesis. It grants no Research/Validation/Promotion/Safety/Execution/broker privilege.

The authorization binding is immutable for the current bootstrap journal lineage once `IMPORT_RECORDED[0]` exists.

```text
same BOOTSTRAP_INSTANCE_KEY + changed trust anchor/control identity/separation/scope
=> conflicting authorization
=> bootstrap transition DENIED
=> NO second journal / NO alternate key
```

If bound bootstrap controls are lost before SystemGenesis, the same system remains fail-closed. This formalization supplies **no control-replacement recovery edge**. External constitutional recovery, if ever designed, must preserve the same instance collision and undergo a later formal proof; it cannot use a new key to bypass the blocked journal.

## 4. Full exact SystemGenesis payload commitment

Before the first successful import, derive an immutable:

```text
SYSTEM_GENESIS_PAYLOAD_COMMITMENT_ROOT = hash(
  exact complete generation-#0 object-set payload,
  exact payload of every initial RoleManifest,
  exact payload of every initial PrincipalRoleBindingRecord,
  exact TrustedAuthorityRegistry #0 payload,
  exact GovernanceRootRotationPolicy #0 payload,
  exact GovernanceRootKernelCapabilities #0 payload,
  exact Champion/Challenge/Capability/Deployment/Safety/decision/risk/broker registry #0 payloads,
  Genesis containment/Safety-change embedded specs,
  bootstrap Champion/comparator/accounting/error/order roots,
  every other generation-#0 authority-bearing embedded payload
)
```

This is a **content commitment**, not merely a schema/template commitment.

The commitment is immutable after journal creation.

```text
same instance + alternate generation-#0 payload
=> conflicting commitment
=> DENIED
=> cannot obtain alternate bootstrap authority slot
```

No initial role, binding, registry, comparator, Safety policy or other authority-bearing generation-#0 payload may be caller-selected after initial import by keeping the same schema while changing content.

## 5. Scientific/legacy import revision lineage

For import revision `r`:

```text
PREGENESIS_IMPORT_REVISION_ROOT[r] = hash(
  BOOTSTRAP_INSTANCE_KEY,
  BOOTSTRAP_AUTHORIZATION_BINDING_ROOT,
  SYSTEM_GENESIS_PAYLOAD_COMMITMENT_ROOT,
  revision r,
  exact parent revision identity or EMPTY,
  exact pre-genesis scientific-state payload root,
  exact legacy/search/evidence/exposure/debt lineage root,
  exact uncertainty/conservative-state root
)
```

Scientific/legacy history is the only payload family permitted to advance through bootstrap reconciliation revisions; authorization and generation-#0 content remain frozen.

## 6. BootstrapInstanceJournal state machine

The V7 pre-system `BootstrapInstanceJournal` remains the sole bootstrap persistence lineage for `BOOTSTRAP_INSTANCE_KEY`.

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
BOOTSTRAP_AUTHORIZATION_BINDING_ROOT
SYSTEM_GENESIS_PAYLOAD_COMMITMENT_ROOT
PREGENESIS_IMPORT_REVISION_ROOT[0]
```

Same instance + exact same bound payload => existing/idempotent result.
Any conflicting authorization/genesis/scientific revision-0 payload => INVALID; no second initial slot.

### 6.2 Same-instance monotone reconciliation

```text
IMPORT_RECORDED[r] -> IMPORT_RECORDED[r+1]
= A-PREGENESIS-IMPORT[RECONCILE]
```

only when `PREGENESIS_RECONCILIATION_MONOTONE_VALID` is positively true and all:

```text
same BOOTSTRAP_INSTANCE_KEY
same BOOTSTRAP_AUTHORIZATION_BINDING_ROOT
same SYSTEM_GENESIS_PAYLOAD_COMMITMENT_ROOT
parent = exact current revision r
all prior known scientific/search/evidence/exposure/debt history preserved
new material history appended, never deleted
known debt/exposure/uncertainty not reduced merely by reconciliation
Safety/containment not weakened
no outcome/performance information selects retained history
revision = r+1 exactly
CAS current journal head
```

Non-monotone correction, changed authorization or changed genesis payload blocks SystemGenesis for this system; it cannot mint another instance.

### 6.3 Genesis knowledge closure prerequisite

The inherited `LegacyCutoffClosureRecord` / `LegacyScientificStateHead #0` semantics remain and are narrowed for V8:

At SystemGenesis commit the current bootstrap import lineage must close the pre-genesis scientific/history frontier as either:

```text
COMPLETE through the exact governed genesis cutoff frontier
OR
materially UNKNOWN with the incorporated conservative unknown-debt/unknown-lineage consequences
```

A known material legacy/scientific fact may not be omitted while claiming COMPLETE. If the governed import/audit universe cannot positively establish completeness, the closure is UNKNOWN; unknown never becomes clean scientific privilege.

## 7. SystemGenesis atomic terminal commit

For exact current revision `r`:

```text
IMPORT_RECORDED[r] -> SYSTEM_GENESIS_COMMITTED
= A-SYSTEM-GENESIS
```

The one local semantic transaction atomically:

```text
CAS exact current journal head
verify immutable BOOTSTRAP_INSTANCE_KEY
verify immutable BOOTSTRAP_AUTHORIZATION_BINDING_ROOT
verify immutable SYSTEM_GENESIS_PAYLOAD_COMMITMENT_ROOT
verify current PREGENESIS_IMPORT_REVISION_ROOT[r]
verify LegacyCutoff closure COMPLETE or conservative UNKNOWN
create exact generation-#0 objects whose complete payload hashes exactly to SYSTEM_GENESIS_PAYLOAD_COMMITMENT_ROOT
bind gen-0 scientific/legacy heads to current revision/closure lineage
mark journal SYSTEM_GENESIS_COMMITTED
consume bootstrap instance authority permanently
```

Crash after semantic commit observes the same terminal generation-#0 result. Crash before commit observes the same instance/current revision and cannot change authorization or genesis payload to get another slot.

After terminal state all import/reconcile/genesis authority for that instance is denied.

## 8. Exact bootstrap authorities

| Authority | Issuer approval | Executor | Usage | Exact prerequisites | Capital |
|---|---|---|---|---|---|
| `A-PREGENESIS-IMPORT[INITIAL]` | exact bound exogenous bootstrap authorization | Bootstrap-Audit | ONE_SHOT per payload-independent instance | journal ABSENT; bind auth + full gen0 commitment + conservative r0 lineage | NO |
| `A-PREGENESIS-IMPORT[RECONCILE]` | exact immutable bound authorization | Bootstrap-Audit | ONE_SHOT per exact next revision | same instance/auth/gen0 commitment; monotone lineage; CAS current head | NO |
| `A-SYSTEM-GENESIS` | exact immutable bound authorization | Genesis | ONE_SHOT per payload-independent instance | current revision + cutoff closure + exact full gen0 payload commitment + atomic terminal consumption | NO |

All inherited generic `A-PREGENESIS-IMPORT` usages are narrowed to these two journal-bound modes. A `PreGenesisScientificStateManifest` or equivalent import evidence not bound to the current journal revision cannot satisfy SystemGenesis or create scientific privilege.

## 9. Forbidden control planes

```text
changed trust anchor/operator/control identity -> new bootstrap instance
credential rotation -> new bootstrap slot
same schema but different initial RoleManifest/registry/Safety/comparator payload -> accepted genesis
unbound PreGenesisScientificStateManifest used for genesis
known legacy discovery omitted while claiming COMPLETE
non-monotone reconciliation deletes debt/history
post-genesis import/reconcile/genesis reuse
```

## 10. Static boundary

This Matrix grants no ARE-0 closure, implementation, P001 substantive research, production, live/paper trading or PR-merge authority.