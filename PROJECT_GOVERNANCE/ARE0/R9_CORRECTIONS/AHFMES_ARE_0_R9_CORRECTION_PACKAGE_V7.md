# AHFMES ARE-0 — R9 Correction Package V7

Status: **NORMATIVE EXTERNAL-AUDIT CORRECTION COMPANION / R9-01 + R9-03-SA11 / PERMANENT REGRESSION / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable correction-companion base:

```text
BASE_R9_CORRECTION_PACKAGE_V6_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_CORRECTION_PACKAGE_V6.md
BASE_R9_CORRECTION_PACKAGE_V6_GIT_BLOB_SHA = 7107bb0a1efae8350b19f202aa7eba04b138b773
```

V6 remains historical correction context. This V7 replaces its pending R9-01 correction requirement with the exact current correction semantics and adds the closure-evidence correction requirement.

This companion cannot add machine rights absent from Matrix V7.

## 1. External audit reconciliation

Historical exact candidate:

```text
6bf6b2ab8e83983da7e4291f20624c0e026438e8
```

Substantive external results included:

```text
External Auditor 1 = ACCEPT_ARE0_FORMAL_DESIGN_CLOSED
External Auditor 2 = CHANGES_REQUIRED
```

Reproducible-blocker precedence yields:

```text
CANONICAL HISTORICAL CANDIDATE DISPOSITION = CHANGES_REQUIRED
ARE0_FORMALIZATION_INVALID = NO
```

Accepted external blocker:

```text
EXT2-C01 BOOTSTRAP_EPOCH_IDENTITY_IS_PAYLOAD_DERIVED
normalization = R9-01
new R9 root family = NO
```

Accepted local closure blocker:

```text
LOCAL-CLOSURE-C01 QUARANTINE_RECORD_POLICY_NONCOMPLIANCE
normalization = R9-03 / SA-11 evidence discipline
new R9 root family = NO
```

## 2. R9-01 correction theorem

Current bootstrap design MUST distinguish stable semantic instance identity from mutable/committed payload.

```text
BOOTSTRAP_INSTANCE_KEY
= hash(exogenous trust anchor,
       stable ARE system identity,
       bootstrap-domain identity,
       exact Genesis control identity,
       exact Bootstrap-Audit control identity)
```

It MUST NOT include:

```text
scientific-state payload
legacy/search/evidence/debt payload
generation-#0 content payload
containment/change-policy payload
Champion/comparator/error/order payload
retry/session/time/process/config identity
```

For one instance there is exactly one durable `BootstrapInstanceJournal` lineage.

```text
initial import
-> IMPORT_RECORDED[0]

late material discovery
-> IMPORT_RECORDED[r+1]
   only through same-instance monotone-conservative reconciliation

SystemGenesis
-> SYSTEM_GENESIS_COMMITTED terminal
```

Changed payload/policy cannot create a new authority slot. Non-monotone correction blocks genesis rather than minting a new bootstrap identity.

## 3. Scientific-import versus policy commitment separation

The first successful import immutably freezes:

```text
BOOTSTRAP_POLICY_COMMITMENT_ROOT
```

including generation-#0 schema/template and bootstrap policy roots.

Scientific/legacy import may advance only as explicit same-instance revision lineage satisfying:

```text
PREGENESIS_RECONCILIATION_MONOTONE_VALID
```

which cannot delete known history or reduce debt/exposure/uncertainty, cannot weaken Safety/containment, and cannot be selected using outcome/performance information.

This separation prevents both:

```text
PAYLOAD LOTTERY
POLICY LOTTERY
```

after partial bootstrap/crash.

## 4. R9-03 / SA-11 quarantine evidence correction

The normative Quarantine Policy V1 remains authoritative for unlisted historical self-claims.

Two independent proofs are required before Clean Pass #1:

```text
EXHAUSTIVE_UNLISTED_FRONTIER_PROVEN
AUTHORITY_LIKE_CLAIM_INVENTORY_COMPLETE
```

A set-difference/Merkle proof may establish the first but not the second.

For every detected self-claim, successor evidence must contain:

```text
exact path
exact Git blob ID
exact location/range where available
bounded verbatim quote or exact claim locator
claim class
classification = HISTORICAL_TEXT_ONLY / QUARANTINED
```

Omitting any detected claim or evidence field means SA-11 FAIL and external dispatch denied.

Quarantine evidence never supplies missing machine/closure semantics.

## 5. Permanent regression additions

Protocol V8 defines and makes mandatory R9-X82..R9-X88. Their root purposes are:

```text
X82 alternate scientific payload cannot create alternate bootstrap slot
X83 late history uses same-instance monotone revision only
X84 alternate bootstrap policy cannot create alternate slot
X85 concurrent conflicting initial imports serialize on one instance journal
X86 post-genesis bootstrap reuse permanently denied
X87 exhaustive frontier without per-claim evidence fails SA-11
X88 quarantined old claim cannot supply missing current semantics
```

## 6. Internal independent-lane qualification

Before any new external dispatch, current exact bytes must survive isolated audit lanes for:

```text
bootstrap identity/crash/concurrency
closed-world state/writer/authority totality
scientific/Challenge/revalidation/rollback
capital/broker/completeness/Safety
closure/manifest/quarantine/subject identity
outside-family composition
```

A PASS in one lane is not inherited by another lane.

## 7. Clean-pass consequence

Because this correction changes machine/protocol/manifest normative bytes:

```text
previous normative root = historical only
previous Clean Pass #1/#2 = historical evidence only
new clean-pass count = 0
```

The full impact→two clean passes→R7/R8/R9 regression→consistency→candidate→binder sequence must run again.

## 8. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 substantive research = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
