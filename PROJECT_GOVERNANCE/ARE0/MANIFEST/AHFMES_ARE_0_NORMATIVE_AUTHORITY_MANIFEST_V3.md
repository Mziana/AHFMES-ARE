# AHFMES ARE-0 — Normative Authority Manifest V3

Status: **CLOSED NORMATIVE AUTHORITY PATH SET / R9 WAVE-5 / STATELESS CLOSURE SUBJECT / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 1. Purpose

This file defines the complete current closure-relevant path set allowed to supply ARE-0 normative or implementation-relevant authority.

A file absent from this manifest cannot add/widen object/state authority, writer, transition, scientific privilege, deployment privilege or capital privilege.

## 2. Current normative authority path set

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V4.md
  role = SOLE CURRENT MACHINE SOURCE / Wave-5 hardening

PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V3.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-4 MACHINE BASE ONLY
  required exact blob = 5c8b2e53000253a069de1c0765beec79fc33e631
  completeness resolution lifecycle and §6.5 replacement ambiguity narrowed by Matrix V4

PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V2.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-3 MACHINE BASE TRANSITIVELY INCORPORATED BY V3
  required exact blob = c640f144837307331fd2795611bbb7003e7c1e7a

PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V1.md
  role = CONTENT-ADDRESSED IMMUTABLE R8 BASE TRANSITIVELY INCORPORATED BY V2
  required exact blob = c9ae503c74d5b94b2dac992b0c4d2fc6a9d00474

PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V4.md
  role = CURRENT CLOSED-WORLD IDENTITY / GENESIS INVENTORY COMPANION

PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V3.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-4 INVENTORY BASE ONLY
  required exact blob = cc2179907ac619b7534be976fa55c715a075b0ef

PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V2.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-3 INVENTORY BASE TRANSITIVELY INCORPORATED BY V3
  required exact blob = 5020e9a7473f9b5ca6ed31b61d563709490c1ae3

PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V4.md
  role = CURRENT CLOSURE / AUDIT / WHOLE-TREE FREEZE PROTOCOL

PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V3.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-4 PROTOCOL BASE ONLY
  required exact blob = fb2cc6b4cd1ccdffff748f63d0ad8b47910b2623

PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V2.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-3 PROTOCOL BASE TRANSITIVELY INCORPORATED BY V3
  required exact blob = 0e90018eeae4ad5f24d76930fad70fbb5fdaf889

PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_CORRECTION_PACKAGE_V3.md
  role = CURRENT R9 ROOT / CORRECTION / PERMANENT REGRESSION INVARIANT COMPANION

PROJECT_GOVERNANCE/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V3.md
  role = THIS CLOSED CURRENT NORMATIVE PATH SET
```

No wildcard path is permitted.

## 3. Superseded current companions

Prior manifests/correction packages are historical after this V3 exists unless explicitly content-addressed above:

```text
AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V1.md
AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V2.md
AHFMES_ARE_0_R9_CORRECTION_PACKAGE_V1.md
AHFMES_ARE_0_R9_CORRECTION_PACKAGE_V2.md
```

## 4. Explicitly non-normative surfaces

Outside the normative root:

```text
PROJECT_GOVERNANCE/CURRENT_AUTHORITY_INDEX.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V1.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V3.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V4.md
future impact/council/regression/consistency records
PR / Issue metadata
journals
external auditor packets
binder/handoff metadata
```

These can record evidence/status only and cannot create or widen machine authority.

## 5. Pre-clean consistency proof

Before Clean Pass #1, SA-11 must prove:

```text
all current machine authority originates in §2
all required immutable-base blobs exactly match declared object IDs
Matrix V4 is sole current machine source
Matrix V4 explicitly preserves V2 §6.5 normal-new-risk narrowing
Inventory V4 matches Matrix V4 object/writer/genesis identities
Protocol V4 points to this Manifest V3
Correction Package V3 adds no rights absent from Matrix V4
no unlisted file materially claims current machine authority
no normative file carries mutable audit-progress state
```

## 6. Exact root membership

`NORMATIVE_CANDIDATE_TREE_ROOT` membership is exactly §2, including immutable bases and this manifest. Exact serialization is the inherited Protocol V2 grammar as incorporated/narrowed by Protocol V3/V4.

After Clean Pass #1, any byte/path/blob change in §2 resets the clean-pass sequence to zero.

## 7. Static boundary

This manifest grants no ARE-0 closure, implementation, P001 substantive research, production or PR-merge authority.