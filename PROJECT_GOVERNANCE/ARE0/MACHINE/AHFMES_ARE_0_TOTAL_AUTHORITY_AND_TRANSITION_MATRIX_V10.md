# AHFMES ARE-0 — Canonical Authority & Transition Matrix V10

Status: **SOLE CURRENT MACHINE SOURCE / R9-01 SEALED AUTHORIZATION SLOT + CURRENT KNOWLEDGE-COVERAGE ATTESTATION / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition / replacement

Immutable machine base:

```text
BASE_MATRIX_V9_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V9.md
BASE_MATRIX_V9_GIT_BLOB_SHA = eaa44d9aa9ec8df58ddc0f388276e260b0741ab7
```

All V9->V1 semantics remain except V9 target-authorization uniqueness/usage and genesis-cutoff currentness surfaces are narrowed by this V10.

```text
V10 R9-01 > EXACT V9 > EXACT V8 > EXACT V7 > EXACT V6 > EXACT V5 > EXACT V4 > EXACT V3 > EXACT V2 > EXACT V1
```

R9-02/R9-04/R9-05/R9-06/R9-07 remain unchanged.

## 1. Sealed canonical bootstrap authorization slot

For exact semantic instance define one pre-system slot:

```text
BOOTSTRAP_AUTHORIZATION_SLOT_KEY = hash(
  BOOTSTRAP_INSTANCE_KEY,
  literal SYSTEM_GENESIS_ORDINAL_0
)
```

Independent pre-system authority-sensitive record:

```text
BootstrapAuthorizationSlot
```

states exactly:

```text
ABSENT
AUTHORIZED_SEALED
BOUND_TO_JOURNAL
CONSUMED
```

### 1.1 Authorization issuance closure

The exogenous bootstrap trust issuer may create `AUTHORIZED_SEALED` only with:

```text
BOOTSTRAP_AUTHORIZATION_ISSUANCE_CLOSURE_ROOT
```

that positively attests, for the exact slot key and exact constitutional authorization frontier:

```text
exactly one current BOOTSTRAP_INSTANCE_AUTHORIZATION_ASSERTION_ROOT exists
that assertion targets exact BOOTSTRAP_INSTANCE_KEY/system/domain/ordinal
that assertion targets exact STATIC_GEN0_AUTHORITY_SEMANTICS_COMMITMENT_ROOT
exact Genesis and independent Bootstrap-Audit controls/separation/scope are fixed
issuance for SystemGenesis ordinal-0 is sealed at this frontier
no competing current assertion with different static commitment/control/scope exists
```

If uniqueness is UNKNOWN or two materially conflicting current assertions exist, issuance closure is invalid and the slot remains unusable. Scheduler/CAS order may not choose among competing constitutions.

Exact edge:

```text
BootstrapAuthorizationSlot ABSENT -> AUTHORIZED_SEALED
= A-BOOTSTRAP-AUTHORIZE
```

`A-BOOTSTRAP-AUTHORIZE` is a direct exogenous constitutional issuance action from `BOOTSTRAP_TRUST_ANCHOR_ROOT`; it is **not** a capability granted by the slot it creates and is not retroactively authorized by any ARE object.

Same slot/same payload is idempotent. Same slot/conflicting payload is INVALID/IntegrityDefect; no first-writer constitutional lottery is credited as valid authorization.

No second `AUTHORIZED_SEALED` payload may replace the sealed slot in current ARE-0.

### 1.2 Journal bind / terminal consumption

Initial import atomically performs:

```text
BootstrapAuthorizationSlot AUTHORIZED_SEALED -> BOUND_TO_JOURNAL
+ BootstrapInstanceJournal ABSENT -> IMPORT_RECORDED[0]
```

under exact target/static match.

SystemGenesis atomically performs:

```text
BootstrapAuthorizationSlot BOUND_TO_JOURNAL -> CONSUMED
+ BootstrapInstanceJournal IMPORT_RECORDED[r] -> SYSTEM_GENESIS_COMMITTED
+ exact generation-#0 creation/final binding
```

No legal state contains SystemGenesis #0 with authorization slot unconsumed.

## 2. Authorization binding narrowed to the sealed slot

V9 target assertion remains mandatory. Current binding additionally commits the exact sealed slot/issuance closure:

```text
BOOTSTRAP_AUTHORIZATION_BINDING_ROOT = hash(
  BOOTSTRAP_INSTANCE_KEY,
  BOOTSTRAP_AUTHORIZATION_SLOT_KEY,
  exact BootstrapAuthorizationSlot AUTHORIZED_SEALED payload identity,
  BOOTSTRAP_AUTHORIZATION_ISSUANCE_CLOSURE_ROOT,
  BOOTSTRAP_INSTANCE_AUTHORIZATION_ASSERTION_ROOT,
  BOOTSTRAP_TRUST_ANCHOR_ROOT,
  exact Genesis control identity,
  exact Bootstrap-Audit control identity,
  positive separation evidence root,
  exact bootstrap capability scope root,
  STATIC_GEN0_AUTHORITY_SEMANTICS_COMMITMENT_ROOT
)
```

The target assertion's bootstrap capability scope is exactly:

```text
A-PREGENESIS-IMPORT[INITIAL]
A-PREGENESIS-IMPORT[RECONCILE]
A-PREGENESIS-COVERAGE-AUDIT
A-SYSTEM-GENESIS
```

and grants no Research/Validation/Promotion/Safety/Execution/broker privilege. `A-BOOTSTRAP-AUTHORIZE` remains solely the exogenous constitutional issuance edge of §1.1 and is outside the authority granted by the resulting slot.

`BOOTSTRAP_AUTHORIZATION_TARGET_VALID` additionally requires exact current slot state `AUTHORIZED_SEALED` before initial bind or `BOUND_TO_JOURNAL` afterward, with all slot/assertion/static fields matching the journal.

## 3. Pre-genesis governed knowledge obligations

Every material fact that becomes governed-knowable to the authorized pre-genesis audit universe before SystemGenesis creates a semantic append-only obligation at its first canonical information frontier:

```text
PREGENESIS_KNOWLEDGE_OBLIGATION_KEY = hash(
  BOOTSTRAP_INSTANCE_KEY,
  FIRST_PREGENESIS_KNOWLEDGE_INFORMATION_TIME,
  stable source/fact identity under frozen tie-break
)
```

Derived current fold:

```text
CURRENT_PREGENESIS_KNOWLEDGE_OBLIGATION_SET_ROOT(frontier)
```

includes every such obligation through the frontier whether or not a service materialized a convenient record. Duplicate same semantic fact does not mint novelty; materially distinct facts remain distinct.

The V9 `GEN0_FIELD_PARTITION_ROOT` / static commitment is narrowed to also freeze:

```text
GENESIS_CUTOFF_RULE_ROOT
FIRST_PREGENESIS_KNOWLEDGE_INFORMATION_TIME definition
knowledge-obligation stable identity/tie-break
coverage/UNKNOWN semantics
coverage-attestation freshness rule
```

These rules cannot change through scientific reconciliation.

## 4. PreGenesisKnowledgeCoverageAttestation

Add independent pre-system authority-sensitive evidence object:

```text
PreGenesisKnowledgeCoverageAttestation
```

Canonical one-slot key:

```text
PREGENESIS_COVERAGE_ATTESTATION_KEY = hash(
  BOOTSTRAP_INSTANCE_KEY,
  exact current PREGENESIS_IMPORT_REVISION_ROOT[r],
  CURRENT_PREGENESIS_KNOWLEDGE_OBLIGATION_SET_ROOT(frontier),
  GENESIS_CUTOFF_RULE_ROOT,
  exact canonical frontier
)
```

Exact authority:

```text
A-PREGENESIS-COVERAGE-AUDIT
```

Executor/attester = exact bound Bootstrap-Audit control, independent by common control from Genesis.

One exact key writes one immutable disposition payload:

```text
COVERAGE_CURRENT_COMPLETE
or
COVERAGE_CURRENT_UNKNOWN_CONSERVATIVE
```

with exact:

```text
instance/auth/static/partition identity
current revision r
canonical knowledge-obligation-set root
canonical cutoff frontier
known-material covered-set root
unresolved/unknowable universe root
conservative unknown-debt/lineage consequences
attester/control/separation identity
```

Known material obligations cannot be placed in the unknown-universe bucket.

Same key/same payload -> existing. Conflict -> IntegrityDefect/invalid.

## 5. Canonical cutoff currentness

SystemGenesis does not choose an arbitrary historical cutoff.

Define:

```text
CURRENT_PREGENESIS_COVERAGE_ATTESTATION
```

as the unique admissible attestation whose:

```text
instance == current journal instance
authorization/static/partition == current journal
revision == exact current journal revision
knowledge-obligation-set root == exact CURRENT_PREGENESIS_KNOWLEDGE_OBLIGATION_SET_ROOT at commit frontier
cutoff frontier == exact frontier bound by the current attestation under GENESIS_CUTOFF_RULE_ROOT
attestation not stale/invalidated
Bootstrap-Audit != Genesis by common control
```

Then:

```text
GENESIS_CUTOFF_INFORMATION_FRONTIER_ROOT
= CURRENT_PREGENESIS_COVERAGE_ATTESTATION.canonical_cutoff_frontier
```

If a new material knowledge obligation becomes governed-knowable after attestation and before SystemGenesis semantic commit, the current obligation-set root advances; the old attestation is stale and SystemGenesis is denied until reconciliation/coverage is current.

There is no legal caller-selected earlier cutoff escape.

## 6. Reconciliation and coverage interaction

V9 scientific revision semantics remain, narrowed:

```text
new governed-known material fact D
-> knowledge obligation appears
-> if current revision does not cover D, old coverage attestation stale/non-current
-> monotone reconciliation r->r+1 incorporates D
-> fresh coverage attestation must bind r+1 and current obligation-set root
-> SystemGenesis may then proceed
```

A coverage attestation for revision `r` cannot be replayed after journal advances to `r+1`.

Coverage audit does not alter static authority semantics or scientific history; it attests current coverage only.

## 7. SystemGenesis terminal transaction — V10 narrowing

V9 SystemGenesis transaction remains and additionally atomically/positively verifies:

```text
BootstrapAuthorizationSlot = BOUND_TO_JOURNAL
BOOTSTRAP_AUTHORIZATION_ISSUANCE_CLOSURE_ROOT valid/sealed
CURRENT_PREGENESIS_COVERAGE_ATTESTATION exists
coverage attestation exact revision == current journal revision
coverage attestation obligation-set root == current governed knowledge obligation-set root
coverage disposition COMPLETE or UNKNOWN_CONSERVATIVE
known material obligations all covered
Bootstrap-Audit / Genesis SoD current
```

Then it derives V9 final closure/factual binding/composite gen0 root and atomically:

```text
BootstrapAuthorizationSlot BOUND_TO_JOURNAL -> CONSUMED
BootstrapInstanceJournal -> SYSTEM_GENESIS_COMMITTED
create exact generation-#0 object set
consume all bootstrap authority for ordinal0
```

Any authorization-slot, journal-head, current-revision, knowledge-head, coverage-attestation or static/partition mismatch makes the transaction lose/deny.

## 8. Race / timing theorem

```text
two conflicting authorization assertions for same slot
=> issuance closure invalid / no usable AUTHORIZED_SEALED slot
=> scheduler cannot select constitution

new fact D appears after coverage attestation but before genesis commit
=> knowledge-obligation root advances
=> old attestation stale
=> genesis denied until current reconciliation/attestation

reconcile r->r+1 wins before genesis
=> journal revision changes
=> old attestation and stale genesis lose

genesis wins first
=> auth slot + journal terminal atomically
=> facts first knowable after terminal cutoff use post-genesis legacy/scientific correction only
```

## 9. Exact R9-01 authorities

| Authority | Issuer approval | Executor | Usage | Exact prerequisites | Capital |
|---|---|---|---|---|---|
| `A-BOOTSTRAP-AUTHORIZE` | exogenous `BOOTSTRAP_TRUST_ANCHOR_ROOT` directly | exogenous bootstrap trust plane | ONE_SHOT per `BOOTSTRAP_AUTHORIZATION_SLOT_KEY` | target-valid assertion + unique sealed issuance closure; no ARE object can grant this edge | NO |
| `A-PREGENESIS-IMPORT[INITIAL]` | exact sealed authorization slot | Bootstrap-Audit | ONE_SHOT per instance | slot AUTHORIZED_SEALED; journal ABSENT; partition/static valid; atomic slot bind+journal r0 | NO |
| `A-PREGENESIS-IMPORT[RECONCILE]` | exact bound authorization slot | Bootstrap-Audit | ONE_SHOT per next revision | slot BOUND; same instance/auth/static/partition; monotone lineage; CAS | NO |
| `A-PREGENESIS-COVERAGE-AUDIT` | exact bound authorization slot | Bootstrap-Audit | ONE_SHOT per coverage key | exact current revision + exact current knowledge-obligation root + SoD | NO |
| `A-SYSTEM-GENESIS` | exact bound authorization slot | Genesis | ONE_SHOT per instance | slot BOUND; current revision/coverage/static/final binding; atomic slot+journal terminalization | NO |

No post-genesis ARE authority can retroactively create/replace these pre-system edges.

## 10. Forbidden control planes

```text
slot authorizes its own creation / circular bootstrap authorization
first-CAS-wins selection among conflicting bootstrap constitutions
multiple conflicting current authorization assertions treated as valid alternatives
authorization slot not consumed atomically with SystemGenesis
caller chooses historical genesis cutoff
stale coverage attestation reused after knowledge-head advance
coverage attestation for r replayed on r+1
Genesis self-attests pregenesis coverage under common control
known material obligation hidden in UNKNOWN bucket
new knowledge appears pre-commit but old attestation remains current
```

All V9 forbidden controls remain.

## 11. Static boundary

This Matrix grants no ARE-0 closure, implementation, P001 substantive research, production, live/paper trading or PR-merge authority.