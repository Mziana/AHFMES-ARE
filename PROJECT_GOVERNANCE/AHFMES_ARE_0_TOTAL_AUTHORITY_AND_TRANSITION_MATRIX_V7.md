# AHFMES ARE-0 — Canonical Authority & Transition Matrix V7

Status: **SOLE CURRENT MACHINE SOURCE / R9-01 PAYLOAD-INDEPENDENT BOOTSTRAP INSTANCE / STATELESS CLOSURE SUBJECT / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition and replacement surface

Immutable machine base:

```text
BASE_MATRIX_V6_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V6.md
BASE_MATRIX_V6_GIT_BLOB_SHA = 0980bcb91b301788f07a17b98b921a7c67bc0553
```

The exact V6->V1 composition remains fully in force except the R9-01 bootstrap slot/key/initial-import/SystemGenesis authority surface inherited from V2 is replaced in full by this V7.

```text
V7 R9-01 > EXACT V6 > EXACT V5 > EXACT V4 > EXACT V3 > EXACT V2 > EXACT V1
```

All R9-02/R9-04/R9-05/R9-06/R9-07 semantics remain unchanged.

```text
UNKNOWN MATERIAL BOOTSTRAP INSTANCE / CONTROL / PAYLOAD LINEAGE / RECONCILIATION
= FAIL CLOSED
```

The historical `BOOTSTRAP_EPOCH_KEY` is **not** a current authority-slot identity. No current authority, retry identity, one-shot scope or SystemGenesis uniqueness theorem may be keyed by payload-derived epoch identity.

## 1. Exogenous bootstrap premise and stable system identity

`BOOTSTRAP_TRUST_ANCHOR_ROOT` remains an explicit exogenous pre-system root-of-trust premise, not an ARE-created object, RoleManifest, VAR, TrustedAuthorityRegistry entry or GovernanceRoot generation.

For one intended ARE system instance, the exogenous anchor positively binds before any bootstrap write:

```text
ARE_SYSTEM_IDENTITY_ROOT
BOOTSTRAP_DOMAIN_IDENTITY_ROOT
exact Genesis control identity
exact independent Bootstrap-Audit control identity
positive control-separation evidence
constitutional/bootstrap trust root
```

These instance-identity inputs are not caller-selectable runtime payload. They cannot be changed by retry/session/process/time/config wrappers.

Changing the exogenous constitutional/system identity after bootstrap work has begun is not an ARE retry. It is an external constitutional reconstitution and cannot erase, overwrite, inherit or silently supersede the already-reserved instance journal.

Absent/UNKNOWN anchor, system identity, domain identity, control identity or separation => bootstrap authority unavailable.

## 2. Payload-independent bootstrap instance identity

Define exactly:

```text
BOOTSTRAP_INSTANCE_KEY = hash(
  BOOTSTRAP_TRUST_ANCHOR_ROOT,
  ARE_SYSTEM_IDENTITY_ROOT,
  BOOTSTRAP_DOMAIN_IDENTITY_ROOT,
  exact Genesis control identity,
  exact Bootstrap-Audit control identity
)
```

The following MUST NOT participate in `BOOTSTRAP_INSTANCE_KEY`:

```text
pre-genesis scientific-state payload
legacy/search/evidence debt payload
SystemGenesis generation-#0 content payload
Genesis containment/change-policy payload
bootstrap Champion/comparator/error/order payload
retry/session/time/process/config identity
```

For one exact `BOOTSTRAP_INSTANCE_KEY`, pre-system persistence provides exactly one canonical `BootstrapInstanceJournal` lineage.

```text
same semantic ARE system/bootstrap instance
=> same BOOTSTRAP_INSTANCE_KEY
```

A changed payload cannot mint a second bootstrap authority slot.

## 3. Frozen bootstrap policy commitment versus scientific import lineage

Before the first import write, derive:

```text
BOOTSTRAP_POLICY_COMMITMENT_ROOT = hash(
  exact SystemGenesis generation-#0 schema/template root,
  Genesis containment/change-policy roots,
  bootstrap Champion/comparator/accounting/error/order roots,
  every other bootstrap policy input that may affect generation-#0 authority
)
```

The policy commitment is immutable after the first successful import for the instance.

For import revision `r`:

```text
PREGENESIS_IMPORT_REVISION_ROOT[r] = hash(
  BOOTSTRAP_INSTANCE_KEY,
  BOOTSTRAP_POLICY_COMMITMENT_ROOT,
  revision r,
  exact parent revision identity or EMPTY,
  exact pre-genesis scientific-state payload root,
  exact legacy/search/evidence/exposure/debt lineage root,
  exact uncertainty/conservative-state root
)
```

`BOOTSTRAP_PAYLOAD_COMMITMENT_ROOT` means the exact current import revision root plus the immutable policy commitment. It is payload evidence, never instance identity.

## 4. BootstrapInstanceJournal state machine

`BootstrapInstanceJournal` is a pre-system authority-sensitive persistence record governed directly by the exogenous bootstrap premise. It is not retroactively authorized by generation-#0 ARE objects.

Legal states:

```text
ABSENT
IMPORT_RECORDED[r]
SYSTEM_GENESIS_COMMITTED
```

### 4.1 Initial import

```text
BootstrapInstanceJournal absent at exact BOOTSTRAP_INSTANCE_KEY
-> IMPORT_RECORDED[0]
= A-PREGENESIS-IMPORT[INITIAL]
```

Atomic payload binds the immutable instance identity, policy commitment, revision-0 import root and complete current conservative legacy/scientific lineage.

Retry rules:

```text
same instance + same revision-0 payload
= return canonical existing result

same instance + conflicting revision-0 payload or policy commitment
= INVALID / WRITE DENIED / NO SECOND INSTANCE SLOT
```

A conflicting payload never changes `BOOTSTRAP_INSTANCE_KEY`.

### 4.2 Same-instance late-discovery reconciliation

Late-discovered pre-genesis history may not create a new instance/epoch. It may advance only the existing journal:

```text
IMPORT_RECORDED[r]
-> IMPORT_RECORDED[r+1]
= A-PREGENESIS-IMPORT[RECONCILE]
```

only if:

```text
PREGENESIS_RECONCILIATION_MONOTONE_VALID = TRUE
```

which requires all:

```text
exact same BOOTSTRAP_INSTANCE_KEY
exact same BOOTSTRAP_POLICY_COMMITMENT_ROOT
exact parent revision = current r
all prior known history/exposure/search/evidence/debt lineage preserved
newly discovered material history appended, never deleted
known debt/exposure/uncertainty is not reduced merely by reconciliation
Safety/containment is not weakened
no result/outcome/performance information selects which history to retain
revision number = r+1 exactly
CAS current journal head
```

If a discovered correction cannot be represented as monotone-conservative reconciliation, SystemGenesis remains denied for this instance pending external constitutional remediation. A new payload-derived instance is not a legal escape hatch.

Same revision/same payload is idempotent. Same revision/conflicting payload is invalid. Concurrent revisions compete on the same current-head CAS; loser receives no alternate slot.

### 4.3 SystemGenesis commit

For exact current revision `r`:

```text
IMPORT_RECORDED[r]
-> SYSTEM_GENESIS_COMMITTED
= A-SYSTEM-GENESIS
```

The successful local semantic transaction atomically:

```text
CAS exact current BootstrapInstanceJournal head
bind exact BOOTSTRAP_INSTANCE_KEY
bind exact BOOTSTRAP_POLICY_COMMITMENT_ROOT
bind exact PREGENESIS_IMPORT_REVISION_ROOT[r]
create the exact incorporated generation-#0 ARE object set
bind generation-#0 objects to the same current import/policy lineage
mark BootstrapInstanceJournal SYSTEM_GENESIS_COMMITTED
consume A-SYSTEM-GENESIS for this BOOTSTRAP_INSTANCE_KEY permanently
```

No legal state may contain generation #0 plus an unconsumed bootstrap instance.

After `SYSTEM_GENESIS_COMMITTED`:

```text
A-PREGENESIS-IMPORT[INITIAL] = DENIED
A-PREGENESIS-IMPORT[RECONCILE] = DENIED
A-SYSTEM-GENESIS = DENIED
new BootstrapInstanceJournal for same BOOTSTRAP_INSTANCE_KEY = DENIED
```

Crash after local semantic commit observes the same terminal journal/generation-#0 result. Crash before commit observes the prior `IMPORT_RECORDED[r]` state and may retry only against that same instance/current revision.

## 5. Exact bootstrap authorities

| Authority | Issuer approval | Executor / holder | Usage | Exact scope / prerequisites | Capital |
|---|---|---|---|---|---|
| `A-PREGENESIS-IMPORT[INITIAL]` | exogenous BootstrapTrust: exact Genesis + independent Bootstrap-Audit | Bootstrap-Audit | ONE_SHOT per `BOOTSTRAP_INSTANCE_KEY` initial import | journal ABSENT; exact instance; frozen policy commitment; complete/conservative revision-0 lineage | NO |
| `A-PREGENESIS-IMPORT[RECONCILE]` | exogenous BootstrapTrust: exact Genesis + independent Bootstrap-Audit | Bootstrap-Audit | ONE_SHOT per exact next import revision | exact same instance/policy; parent=current; monotone-conservative reconciliation; CAS current head | NO |
| `A-SYSTEM-GENESIS` | exogenous BootstrapTrust: exact Genesis + independent Bootstrap-Audit | Genesis | ONE_SHOT per `BOOTSTRAP_INSTANCE_KEY` | current import revision; exact policy commitment; base generation-#0 set; atomic journal terminalization/consumption | NO |

No post-genesis root/VAR/RoleManifest can retroactively authorize these pre-system edges.

## 6. Required bootstrap conflict theorems

```text
same instance + P1 import succeeds + crash + P2 != P1
=> P2 cannot obtain a new authority slot
=> either exact governed RECONCILE revision is monotone-valid
   or bootstrap remains blocked

same instance + policy Q1 recorded + retry with Q2 != Q1
=> INVALID

same instance + concurrent initial payloads P1/P2
=> at most one initial journal creation wins
=> loser cannot remint identity from its payload

SystemGenesis #0 exists
=> exact BOOTSTRAP_INSTANCE_KEY is permanently terminal
```

## 7. Forbidden hidden control planes

```text
payload-derived bootstrap identity
policy-derived bootstrap instance identity
retry wrapper changing system identity
late legacy discovery creating a fresh bootstrap slot
conflicting import presented as a new epoch
reconciliation deleting prior scientific/search/exposure/debt history
non-monotone reconciliation weakening containment or uncertainty
second SystemGenesis #0 under a new payload key for the same system identity
```

## 8. Static boundary

This design grants no ARE-0 closure, implementation, P001 substantive research, production, live/paper trading or PR-merge authority.