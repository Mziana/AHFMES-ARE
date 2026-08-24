# AHFMES ARE-0 — Normative Authority Manifest V4

Status: **CLOSED NORMATIVE AUTHORITY PATH SET / R9 WAVE-6 / STATELESS CLOSURE SUBJECT / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 1. Purpose

This file defines the complete current closure-relevant path set allowed to supply ARE-0 normative or implementation-relevant authority. A file absent here cannot add/widen machine authority.

## 2. Current normative authority path set

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V5.md
  role = SOLE CURRENT MACHINE SOURCE / Wave-6 sticky resolution invalidation

PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V4.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-5 BASE
  required exact blob = 7e642490446df3b5733aeca1b80da533a29b1f54

PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V3.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-4 BASE
  required exact blob = 5c8b2e53000253a069de1c0765beec79fc33e631

PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V2.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-3 BASE
  required exact blob = c640f144837307331fd2795611bbb7003e7c1e7a

PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V1.md
  role = CONTENT-ADDRESSED IMMUTABLE R8 BASE
  required exact blob = c9ae503c74d5b94b2dac992b0c4d2fc6a9d00474

PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V5.md
  role = CURRENT CLOSED-WORLD IDENTITY / GENESIS INVENTORY COMPANION

PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V4.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-5 INVENTORY BASE
  required exact blob = fccc1c1b3563a17b920f2c7fa395d420d0ef6c63

PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V3.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-4 INVENTORY BASE
  required exact blob = cc2179907ac619b7534be976fa55c715a075b0ef

PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V2.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-3 INVENTORY BASE
  required exact blob = 5020e9a7473f9b5ca6ed31b61d563709490c1ae3

PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V5.md
  role = CURRENT CLOSURE / AUDIT / WHOLE-TREE FREEZE PROTOCOL

PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V4.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-5 PROTOCOL BASE
  required exact blob = 81a71c71556cea69d8d348b26017c1968b8ee7d3

PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V3.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-4 PROTOCOL BASE
  required exact blob = fb2cc6b4cd1ccdffff748f63d0ad8b47910b2623

PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V2.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-3 PROTOCOL BASE
  required exact blob = 0e90018eeae4ad5f24d76930fad70fbb5fdaf889

PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_CORRECTION_PACKAGE_V4.md
  role = CURRENT R9 ROOT / CORRECTION / PERMANENT REGRESSION COMPANION

PROJECT_GOVERNANCE/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V4.md
  role = THIS CLOSED CURRENT NORMATIVE PATH SET
```

No wildcard path is permitted.

## 3. Superseded companions

Earlier manifest/correction-package versions are historical unless explicitly content-addressed in §2. They cannot add current authority.

## 4. Non-normative surfaces

Outside the normative root:

```text
CURRENT_AUTHORITY_INDEX.md
AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V1.md
AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V2.md
AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V3.md
AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V4.md
AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V5.md
future council/regression/consistency result records
PR / Issue metadata
journals
external auditor packets
binder/handoff metadata
```

These cannot add machine rights.

## 5. Pre-clean consistency proof

Before Clean Pass #1, SA-11 must prove:

```text
all current machine authority originates in §2
all immutable-base blob IDs match exactly
Matrix V5 is sole current machine source
Inventory V5 matches Matrix V5 object/identity semantics
Protocol V5 points to this Manifest V4
Correction Package V4 adds no rights absent from Matrix V5
V2 §6.5 normal-new-risk gates remain preserved through the composed Matrix
no unlisted file materially claims current authority
no normative file contains mutable audit-progress state
```

## 6. Exact root membership

`NORMATIVE_CANDIDATE_TREE_ROOT` membership is exactly §2. Exact serialization uses the inherited Protocol V2 grammar through Protocol V3/V4/V5.

After Clean Pass #1 any byte/path/blob change in §2 resets clean-pass sequence to zero.

## 7. Static boundary

This manifest grants no ARE-0 closure, implementation, P001 substantive research, production or PR-merge authority.