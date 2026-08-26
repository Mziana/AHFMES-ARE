# AHFMES ARE-0 — Normative Authority Manifest V2

Status: **CLOSED NORMATIVE AUTHORITY PATH SET / R9 WAVE-4 / STATELESS CLOSURE SUBJECT / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 1. Purpose

This file defines the complete current closure-relevant path set allowed to supply ARE-0 normative or implementation-relevant authority.

A file absent from this manifest cannot add/widen object/state authority, writer, transition, scientific privilege, deployment privilege or capital privilege.

This manifest lists paths/roles and required immutable-base blob IDs but not its own future Git object ID. Exact blob IDs/byte lengths for the frozen root are obtained from the repository tree under Council Protocol V3.

## 2. Current normative authority path set

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V3.md
  role = SOLE CURRENT MACHINE SOURCE / Wave-4 R9-04 + R9-07 replacements

PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V2.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-3 MACHINE BASE ONLY
  required exact blob = c640f144837307331fd2795611bbb7003e7c1e7a
  R9-04/R9-07 surfaces replaced by Matrix V3

PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V1.md
  role = CONTENT-ADDRESSED IMMUTABLE R8 BASE TRANSITIVELY INCORPORATED BY V2
  required exact blob = c9ae503c74d5b94b2dac992b0c4d2fc6a9d00474

PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V3.md
  role = CURRENT CLOSED-WORLD IDENTITY / GENESIS INVENTORY COMPANION
  cannot add rights absent from Matrix V3

PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V2.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-3 INVENTORY BASE ONLY
  required exact blob = 5020e9a7473f9b5ca6ed31b61d563709490c1ae3
  R9-04/R9-07 inventory surfaces replaced by Inventory V3

PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V3.md
  role = CURRENT CLOSURE / AUDIT / WHOLE-TREE FREEZE PROTOCOL
  cannot add live/scientific/capital machine rights

PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V2.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-3 PROTOCOL BASE ONLY
  required exact blob = 0e90018eeae4ad5f24d76930fad70fbb5fdaf889
  manifest reference/regression ceiling/attack overlay superseded by Protocol V3

PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_CORRECTION_PACKAGE_V2.md
  role = CURRENT R9 ROOT / CORRECTION / PERMANENT REGRESSION INVARIANT COMPANION
  cannot widen rights beyond Matrix V3

PROJECT_GOVERNANCE/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V2.md
  role = THIS CLOSED CURRENT NORMATIVE PATH SET
```

No wildcard path is permitted.

## 3. Superseded normative files

The following prior current companions become historical after Manifest V2 exists and are **not** current authority unless explicitly content-addressed above:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V1.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_CORRECTION_PACKAGE_V1.md
```

Older drafts/audit records remain rationale/evidence only.

## 4. Explicitly non-normative surfaces

Outside the normative root:

```text
PROJECT_GOVERNANCE/CURRENT_AUTHORITY_INDEX.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V1.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V3.md
future impact/council/regression/consistency result records
PR / Issue metadata
journals
external auditor packets
binder/handoff metadata
```

These may record status/evidence but cannot create or widen machine authority.

## 5. Pre-clean consistency proof

Before Clean Pass #1, SA-11 must prove:

```text
all current machine authority originates in §2
all required immutable-base blobs exactly match their declared object IDs
Matrix V3 is the sole current machine source and its replacement surfaces are deterministic
Inventory V3 matches Matrix V3 object universe/writers/genesis
Protocol V3 points to this Manifest V2
Correction Package V2 introduces no rights absent from Matrix V3
no unlisted file materially claims current machine authority
no normative file carries mutable audit-progress state requiring post-Pass-#1 edits
```

If any current authority file is missing from §2, formal freeze is denied.

## 6. Exact root membership

`NORMATIVE_CANDIDATE_TREE_ROOT` membership is exactly the paths in §2, including immutable bases and this manifest itself. Exact serialization is defined by Council Protocol V3/V2 composition.

After Clean Pass #1, any byte/path/blob change in §2 resets the clean-pass sequence to zero.

## 7. Static boundary

This manifest grants no ARE-0 closure, implementation, P001 substantive research, production or PR-merge authority. Audit-progress/candidate/external-subject state remains outside the manifest.