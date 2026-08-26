# AHFMES ARE — Self-Audit Council Protocol V9

Status: **MANDATORY PRE-EXTERNAL-REAUDIT GOVERNANCE / R9-01 STABLE SYSTEM IDENTITY + SA-11 CLAIM INVENTORY / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable protocol base:

```text
BASE_PROTOCOL_V8_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V8.md
BASE_PROTOCOL_V8_GIT_BLOB_SHA = 89b856d09a5ac633fef103b78fbfd9bedb2f9c56
```

All V8->V2 protocol rules remain except current-manifest reference and R9-01 attack/regression ceiling are extended/narrowed here.

The 12-role council, multi-lane isolation, exact whole-tree root, two clean passes, permanent regression, final consistency, self-reference-free candidate and one-binder-only-child requirements remain mandatory.

## 1. Current manifest

Current normative path set is declared only by:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V8.md
```

Matrix V8 is sole current machine-semantic source.

## 2. R9-01 identity hierarchy attack rule

Bootstrap review MUST distinguish three layers:

```text
SEMANTIC INSTANCE IDENTITY
AUTHORIZATION BINDING
BOOTSTRAP / GENESIS PAYLOAD COMMITMENT
```

None of the latter two may participate in semantic instance identity.

Required attack assertions:

```text
same ARE_SYSTEM_IDENTITY_ROOT + same bootstrap domain + gen0 ordinal
+ changed trust anchor
+ changed Genesis operator
+ changed Bootstrap-Audit operator
+ credential/process/machine rotation
=> SAME BOOTSTRAP_INSTANCE_KEY
=> conflict/blocked on the existing journal, not a second slot
```

A new system identity may exist only as an actually different constitutional system; it cannot inherit or sanitize the old system's journal/scientific/debt lineage while claiming continuity.

## 3. Full generation-#0 commitment attack rule

Audit must mutate every authority-bearing generation-#0 payload while holding schema/template shape constant, including:

```text
initial RoleManifest payloads
PrincipalRoleBinding payloads
TrustedAuthorityRegistry #0
GovernanceRoot policy/kernel payloads
Champion/Challenge comparator/accounting/error/order payloads
Safety containment/change-policy payloads
Decision/risk/broker registry payloads
other authority-bearing embedded specs
```

Expected:

```text
any changed generation-#0 content after initial journal creation
=> changed SYSTEM_GENESIS_PAYLOAD_COMMITMENT_ROOT
=> conflict/denial on same BOOTSTRAP_INSTANCE_KEY
=> no new bootstrap slot
```

SystemGenesis must prove exact full generation-#0 content matches the frozen commitment.

## 4. Pre-genesis knowledge-closure attack

Attack:

```text
r0 import recorded
material legacy/scientific fact D becomes governed-knowable before genesis
D omitted from journal
SystemGenesis attempts COMPLETE cutoff
```

Expected:

```text
COMPLETE = INVALID
```

unless D is incorporated before commit. If completeness cannot be positively established, inherited LegacyCutoff closure must be `UNKNOWN` and conservative unknown-debt/lineage semantics apply. UNKNOWN cannot become clean scientific privilege.

## 5. SA-11 claim evidence remains mandatory

V8 §4 remains unchanged:

```text
EXHAUSTIVE_UNLISTED_FRONTIER_PROVEN
AND
AUTHORITY_LIKE_CLAIM_INVENTORY_COMPLETE
```

For every detected claim: exact path + blob + location/range where available + bounded quote/locator + claim class + `HISTORICAL_TEXT_ONLY / QUARANTINED` classification.

A manifest/set-difference proof without claim evidence is insufficient.

## 6. Isolated audit lanes

Required lanes remain:

```text
LANE-A BOOTSTRAP IDENTITY / CRASH / CONCURRENCY
LANE-B CLOSED-WORLD STATE / WRITER / AUTHORITY TOTALITY
LANE-C SCIENTIFIC / CHALLENGE / REVALIDATION / ROLLBACK
LANE-D CAPITAL / BROKER / COMPLETENESS / SAFETY
LANE-E CLOSURE / MANIFEST / QUARANTINE / SUBJECT IDENTITY
LANE-F OUTSIDE-FAMILY ADVERSARIAL INTEGRATOR
```

No lane inherits another lane's PASS.

## 7. Permanent regression extension

All inherited R7/R8 and R9-X01..R9-X88 remain mandatory.

Add:

```text
R9-X89 partial bootstrap under authorization A1, same system reauthorized A2 -> same instance key; A2 cannot create a second journal/slot
R9-X90 same system, same gen0 schema, changed initial RoleManifest/PrincipalRoleBinding/registry payload -> same instance; frozen full gen0 commitment conflicts; genesis denied
R9-X91 trust-anchor/credential/process rotation after r0 -> no new instance identity; absent explicit recovery edge bootstrap remains blocked
R9-X92 r0 recorded, material pre-genesis fact D becomes governed-knowable, D omitted while COMPLETE claimed -> COMPLETE denied; reconcile or UNKNOWN-conservative closure required
R9-X93 standalone/unbound PreGenesisScientificStateManifest/import evidence -> cannot satisfy SystemGenesis or create clean scientific privilege
```

No prior regression seed is deleted.

## 8. Clean-pass reset

Because Matrix/Inventory/Protocol/Manifest/Correction normative bytes change in this cycle:

```text
new corrected normative root clean-pass count = 0
```

No previous candidate's pass credit carries forward.

## 9. Dispatch sequence

```text
integrated correction
-> isolated-lane whole-composition impact attack
-> complete per-claim quarantine evidence
-> freeze exact normative root
-> Clean Pass #1
-> NO normative write
-> Clean Pass #2 same root
-> R7 + R8 + R9-X01..X93 regression
-> final consistency / SA-11 refresh
-> self-reference-free candidate
-> exactly one binder-only child
-> new independent external whole-architecture audit
```

## 10. Static boundary

This protocol grants no ARE-0 closure, implementation, P001 substantive research, production, live/paper trading or PR-merge authority.