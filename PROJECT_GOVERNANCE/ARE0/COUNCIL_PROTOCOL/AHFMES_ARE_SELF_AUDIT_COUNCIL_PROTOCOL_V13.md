# AHFMES ARE — Self-Audit Council Protocol V13

Status: **MANDATORY PRE-EXTERNAL-REAUDIT GOVERNANCE / R9-01 TARGET-SCOPED AUTHORIZATION + DRAINABLE GENESIS COMPOSITION / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable base:

```text
BASE_PROTOCOL_V12_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V12.md
BASE_PROTOCOL_V12_GIT_BLOB_SHA = b2b92b11a6461e004ddda91e03a1b311889579d0
```

All V12->V2 rules remain except current machine/inventory references, R9-01 external-reconciliation attack charter, regression ceiling and dispatch reset are extended/narrowed here.

Current manifest is resolved only through:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_CURRENT_NORMATIVE_MANIFEST_BINDING.md
```

Matrix V9 is the sole current machine-semantic source. Inventory V9 is the current closed-world companion. Protocol adds no machine right.

## 1. External audit reconciliation for historical candidate cbb7907

Exact externally audited historical subject:

```text
cbb7907a4434306dc949ff10da45eb9bdce61c48
```

Recorded independent dispositions:

```text
AUDITOR_LOCAL = CHANGES_REQUIRED
  blocker = bootstrap authorization not target-instance scoped
  root = R9-01

AUDITOR_1 = ACCEPT_ARE0_FORMAL_DESIGN_CLOSED
  blocker = NONE FOUND in attacked surfaces

AUDITOR_2 = CHANGES_REQUIRED
  blocker = full exact pre-import gen0 content commitment conflicts with legal late scientific reconciliation
  root = R9-01
```

Canonical project-level rule remains:

```text
one reproducible legal exploit/deadlock
=> subject CHANGES_REQUIRED
```

Auditor voting cannot erase a reproducible blocker. Auditor 1 acceptance remains evidence that many other surfaces survived its independent attack, but it does not transfer closure credit to the corrected subject.

```text
ARE0_FORMALIZATION_INVALID = NO
NEW R9 ROOT = NONE
NEW CORRECTED ROOT CLEAN PASS COUNT = 0
```

## 2. Required isolated correction lanes

Before Clean Pass #1, the exact integrated corrected subject must be attacked independently through all lanes:

```text
LANE-A semantic instance / cross-system authorization / trust-control rotation
LANE-B static-vs-final-derived gen0 partition / reconciliation drainability
LANE-C crash / retry / concurrency / CAS / cutoff / terminal consumption
LANE-D closed-world object / writer / transition / SoD totality
LANE-E scientific / legacy / evidence / exposure / debt reconciliation completeness
LANE-F Safety / capital / broker / cross-root / outside-family composition
```

No lane inherits another lane's PASS. One reproducible path blocks qualification.

## 3. R9-01 target-scoped authorization attack charter

Audit must distinguish:

```text
semantic instance identity
target-instance authorization assertion
authorization binding
static authority-semantics commitment
final scientific/factual binding
```

Required attacks include:

```text
A. authorization assertion issued for KA replayed against KB != KA
B. generic/untargeted trust assertion locally re-hashed with KB
C. same trust anchor/operators authorized for two systems without two distinct target assertions
D. authorization for KA with static commitment S1 used with S2
E. trust/control/credential rotation after r0 attempting alternate authorization on same instance
```

Expected:

```text
A/B/D/E -> DENIED
C -> legal only if issuer produced a distinct valid assertion explicitly targeting KB and its exact static commitment
```

Merely hashing `BOOTSTRAP_INSTANCE_KEY` together with generic evidence is insufficient; the exogenous issuer assertion itself must attest the target instance/static commitment.

## 4. R9-01 static/final-derived generation-#0 attack charter

Audit every generation-#0 field under `GEN0_FIELD_PARTITION_ROOT`.

Required theorem:

```text
EVERY GEN0 FIELD
= exactly one of STATIC_PRECOMMITTED or FINAL_REVISION_DERIVED
```

Attack:

```text
unclassified field
overlap between classes
FINAL_REVISION_DERIVED field carrying Role/SoD/writer/transition/Safety bound/governance privilege
reconciliation changing static RoleManifest/PrincipalRoleBinding/Safety/comparator/accounting/error/order content
same final revision producing two different derived factual payloads
```

All must fail closed.

For factual fields whose exact value legitimately depends on final imported history—such as legacy scientific head, exposure/evidence seeds, or legacy incumbent factual identity—the **derivation rule and authority envelope** must be frozen before r0 while the factual value may be deterministically derived from the final current revision.

## 5. Reconciliation-to-genesis drainability attack charter

Mandatory composition attack:

```text
r0 valid initial import
-> material history D becomes governed-knowable
-> valid monotone r1 reconciliation
-> SystemGenesis
```

Expected simultaneously:

```text
same BootstrapInstanceJournal
same target-scoped authorization
same static authority-semantics commitment
all r0 history retained
D included
final gen0 scientific/factual fields bind exact r1
static Role/Safety/governance/comparator/error/order semantics unchanged
SystemGenesis remains legally drainable
bootstrap consumed terminally
```

The corrected design must not require stale r0 scientific heads and must not mutate precommitted static semantics to reach terminal genesis.

## 6. Cutoff / race / crash attacks

Attack canonical cutoff and concurrent transitions:

```text
D governed-known before cutoff but omitted + UNKNOWN claimed
reconcile r->r+1 racing SystemGenesis on r
material fact first known after terminal cutoff
genesis crash before local semantic commit
genesis crash after local semantic commit
retry wrapper changes authorization/static/final payload
```

Expected:

```text
known-before-cutoff omission -> INVALID even under UNKNOWN
reconcile wins -> stale genesis CAS loses; retry same instance on r+1
genesis wins -> journal terminal; later fact uses post-genesis legacy/scientific correction, never bootstrap reopen
pre-commit crash -> same journal/current revision
post-commit crash -> same terminal SystemGenesis
retry cannot alter instance/auth/static partition or mint second genesis
```

## 7. Downstream non-widening attacks

Final-revision-derived factual values may not silently grant ACT privilege.

Attack at minimum:

```text
late discovered legacy incumbent factual identity -> promoted/current production authority
late exposure seed -> relaxed Safety/mutation boundary
UNKNOWN factual state -> wider action envelope
new system identity -> inherited old-system proof/debt/Champion continuity
```

Expected: denied/conservative. Existing R9-04/R9-06/R9-07 and V2 §6.5 normal-new-risk narrowing remain mandatory.

## 8. Permanent regression extension

All inherited R7/R8 and R9-X01..R9-X115 remain mandatory.

Add:

```text
R9-X116 r0 -> late material D -> valid r1 reconcile -> SystemGenesis drainable; static semantics unchanged; final factual heads bind r1
R9-X117 authorization assertion for KA + journal KB absent + KA != KB -> import/genesis on KB DENIED
R9-X118 generic/untargeted trust assertion locally combined with KB -> target authorization invalid; no bootstrap authority
R9-X119 r1 reconciliation attempts RoleManifest/Safety/comparator/accounting/error/order/governance mutation -> DENIED
R9-X120 FINAL_REVISION_DERIVED field attempts writer/Role/Safety-bound/authority-envelope widening -> partition invalid; genesis denied
R9-X121 same static commitment + same final revision/cutoff + two different final factual bindings -> conflicting derivation; no alternate genesis
R9-X122 reconcile r->r+1 races genesis on r -> exactly one CAS winner; stale side cannot mint alternate slot
R9-X123 known-before-cutoff material fact omitted while UNKNOWN claimed -> closure invalid; UNKNOWN cannot hide known fact
R9-X124 fact first governed-knowable after terminal cutoff -> post-genesis legacy/scientific correction path; bootstrap remains terminal
R9-X125 late legacy incumbent/comparator factual identity re-derived under frozen rule -> factual binding may change pre-genesis; comparator-selection/accounting/error/Safety rules unchanged; no direct new-risk authority
R9-X126 same trust/control principals bootstrap KA and KB -> requires two independently target-valid assertions; KA assertion replay on KB denied
R9-X127 changed target-scoped authorization after r0 on same instance -> conflict/denial; no alternate binding/journal
R9-X128 authorization assertion targets correct instance but wrong static commitment -> import/genesis denied
```

Current explicit ceiling:

```text
R9-X01..R9-X128
```

No prior regression seed is deleted.

## 9. Clean-pass reset / dispatch sequence

Because Matrix V9, Inventory V9, Protocol V13, manifest binding, Correction V12 and Manifest V12 are normative changes:

```text
OLD CP1/CP2/REGRESSION CREDIT = HISTORICAL ONLY
NEW CLEAN PASS COUNT = 0
```

Required sequence:

```text
integrated normative correction
-> freeze exact corrected normative bytes
-> isolated Lane A-F whole-composition impact attack
-> SA-11 whole-blob quarantine against corrected pre-pass subject
-> freeze exact normative root
-> Full Council Clean Pass #1
-> NO normative write
-> Full Council Clean Pass #2 on same root
-> R7 + R8 + R9-X01..X128 permanent regression
-> final cross-document consistency + qualification-lineage verification
-> self-reference-free candidate
-> exactly one binder-only child
-> independent external whole-architecture re-audit
```

No internal PASS is an external verdict.

## 10. Progress-update discipline

Every completed external audit/re-audit cycle must be reflected in GitHub progress metadata/evidence with exact subject, auditor class, disposition, normalized findings, qualification-credit reset/survival, firewall state and next authorized activity.

## 11. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
