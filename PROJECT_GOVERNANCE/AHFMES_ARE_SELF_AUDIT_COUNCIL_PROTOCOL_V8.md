# AHFMES ARE — Self-Audit Council Protocol V8

Status: **MANDATORY PRE-EXTERNAL-REAUDIT GOVERNANCE / R9-01 INSTANCE-IDENTITY + SA-11 CLAIM-EVIDENCE HARDENING / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable protocol base:

```text
BASE_PROTOCOL_V7_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V7.md
BASE_PROTOCOL_V7_GIT_BLOB_SHA = 11ca2dbf2aee8a6ca06ece8ff00a9c8694be889a
```

All V7->V2 protocol rules remain except the current-manifest reference, external-audit provenance handling, SA-11 quarantine-evidence sufficiency test and regression ceiling are replaced/narrowed here.

The 12-role council, exact whole-tree root discipline, two clean passes on one root, permanent regression, final consistency, self-reference-free candidate and one-binder-only-child rules remain mandatory.

## 1. Current manifest

The complete current normative path set is declared only by:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V7.md
```

Matrix V7 is the sole current machine-semantic source. No protocol or correction companion may add a machine edge, writer, genesis mode, scientific privilege, selection privilege, Safety privilege or capital privilege absent from Matrix V7 composition.

## 2. External-audit reconciliation rule

External audit dispositions are recorded outside the normative root. This protocol does not carry mutable audit-progress state.

For any exact candidate:

```text
one reproducible closure blocker
=> candidate disposition CHANGES_REQUIRED
```

even if another auditor accepted the same subject.

Auditor voting cannot override a reproducible legal exploit/deadlock/protocol-qualification failure. A finding must still satisfy the inherited concrete-path standard.

A corrected candidate is a new subject and receives no closure credit from acceptance of an older subject.

## 3. R9-01 bootstrap-instance attack charter

SA-01/SA-09/SA-12 must attack the **semantic instance identity**, not only same-key retries.

At minimum attack:

```text
initial payload P1 imports, crash, retry with P2 != P1
bootstrap policy Q1 imports, crash/restart, retry with Q2 != Q1
same system identity but different legacy/search/evidence/debt payload
same system identity but changed generation-#0 template payload
concurrent first imports with distinct payloads
late pre-genesis history discovered after initial import
late discovery used to delete/reduce legacy debt/exposure/uncertainty
retry/session/process/config wrapper attempting new instance identity
caller attempting to rotate ARE_SYSTEM_IDENTITY_ROOT or BOOTSTRAP_DOMAIN_IDENTITY_ROOT
SystemGenesis committed followed by any import/reconcile/genesis attempt
```

Expected theorem:

```text
same semantic system/bootstrap instance
=> same payload-independent BOOTSTRAP_INSTANCE_KEY
=> exactly one BootstrapInstanceJournal lineage
```

Changed payload cannot mint a second authority slot. Late history may use only exact same-instance monotone-conservative reconciliation. Non-monotone correction blocks genesis rather than minting a new instance.

## 4. SA-11 quarantine evidence — path coverage and claim evidence are separate proofs

The V7 exhaustive unlisted-frontier rule remains, but a Merkle/set-difference proof of path coverage **does not by itself satisfy** the current Legacy Authority Quarantine Policy's per-detected-claim evidence requirement.

Before Clean Pass #1, SA-11 must establish both:

```text
A. EXHAUSTIVE_UNLISTED_FRONTIER_PROVEN
B. AUTHORITY_LIKE_CLAIM_INVENTORY_COMPLETE
```

### 4.1 Exhaustive frontier

Bind exact recursive `PROJECT_GOVERNANCE` tree and exact current manifest. Let:

```text
G = every recursive governance blob path/blob identity in the bound tree
N = exact current manifest paths
U = G minus N
```

Every `U` path is non-authoritative under the Quarantine Policy, but that blanket classification is only the authority theorem, not sufficient inspection evidence.

### 4.2 Detected-claim inventory

Every detected authority-like self-claim in `U` must have one evidence entry with all:

```text
exact repository path
exact Git blob ID
exact location: line/range where available
bounded verbatim quote or exact claim locator
claim class
classification = HISTORICAL_TEXT_ONLY / QUARANTINED
```

Claim classes include at minimum statements/statuses asserting or materially implying:

```text
normative/current/canonical authority
approved/ready/closed status
formalization/implementation/execution authority
production/trading/merge authority
external-audit/audited/verdict authority
```

A scanner/token match is not automatically a positive claim; semantic review determines whether the text actually self-claims authority/status. But once a claim is detected, omission of any required evidence field is a blocker.

The successor quarantine record must separately state the detection/inspection method and list negative/skipped non-text surfaces as applicable so an auditor can reproduce coverage.

### 4.3 Dependency test remains independent

Even a perfectly quarantined claim cannot supply missing current semantics:

```text
current machine/closure dependency on unlisted path
=> BLOCKER
```

## 5. Multi-lane internal pre-audit discipline

Before a corrected candidate is dispatched externally, internal review should be executed as multiple isolated audit lanes with separate charters. A lane must not inherit another lane's PASS as evidence.

Required lanes for this correction cycle:

```text
LANE-A BOOTSTRAP IDENTITY / CRASH / CONCURRENCY
LANE-B CLOSED-WORLD STATE / WRITER / AUTHORITY TOTALITY
LANE-C SCIENTIFIC / CHALLENGE / REVALIDATION / ROLLBACK REGRESSION
LANE-D CAPITAL / BROKER / COMPLETENESS / SAFETY COMPOSITION
LANE-E CLOSURE / MANIFEST / QUARANTINE / SUBJECT IDENTITY
LANE-F OUTSIDE-FAMILY ADVERSARIAL INTEGRATOR
```

These are logical independence lanes, not a substitute for an actually independent external auditor.

Any lane with one reproducible blocker resets/prevents clean-pass qualification.

## 6. Permanent regression extension

All V7 inherited R7/R8 and R9-X01..R9-X81 scenarios remain mandatory.

Add:

```text
R9-X82 same semantic bootstrap instance: P1 import succeeds, crash, P2 != P1 -> same BOOTSTRAP_INSTANCE_KEY; P2 cannot obtain second initial slot
R9-X83 late legacy/scientific history after initial import -> only same-instance monotone reconciliation revision; no new instance/epoch
R9-X84 bootstrap policy commitment Q1 recorded, retry with Q2 != Q1 -> conflict/denied; no payload-derived alternate slot
R9-X85 concurrent same-instance initial imports with P1/P2 -> at most one canonical initial journal creation; loser has no alternate identity
R9-X86 SystemGenesis committed -> all later import/reconcile/genesis under same instance denied permanently
R9-X87 quarantine record proves exhaustive U set but omits path/blob/location-or-quote/classification for one detected self-claim -> SA-11 FAIL / dispatch denied
R9-X88 current semantic dependency attempts to use quarantined old claim to supply missing edge/writer -> BLOCKER, not inherited authority
```

No earlier regression seed is deleted merely because it passed on a prior candidate.

## 7. Clean-pass reset for this correction class

A Matrix/Inventory/Protocol/Manifest/Correction-Package normative change produces a new normative root.

Therefore:

```text
old clean-pass credit = historical evidence only
new corrected root clean-pass count = 0
```

The quarantine evidence correction alone would not change the root, but this cycle also changes R9-01 machine semantics; the complete clean-pass/regression sequence must therefore run again on the new exact root.

## 8. Dispatch sequence

```text
integrated normative correction
-> exact-byte impact attack by isolated lanes
-> exhaustive per-claim quarantine evidence
-> freeze new normative root
-> full council Clean Pass #1
-> no normative write
-> full council Clean Pass #2 on same root
-> R7+R8+R9-X01..X88 regression
-> final cross-document consistency + SA-11 refresh
-> freeze new self-reference-free candidate
-> one binder-only child
-> new independent external whole-architecture audit
```

## 9. Static boundary

This protocol grants no ARE-0 closure, implementation, P001 substantive research, production, live/paper trading or PR-merge authority.