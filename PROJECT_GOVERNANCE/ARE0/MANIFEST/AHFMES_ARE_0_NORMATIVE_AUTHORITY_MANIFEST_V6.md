# AHFMES ARE-0 — Normative Authority Manifest V6

Status: **CLOSED NORMATIVE AUTHORITY PATH SET / R9 WAVE-8 LEGACY-AUTHORITY QUARANTINE / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 1. Closed-set theorem

Only exact paths in §2 may supply current ARE-0 normative authority.

For every path absent from §2:

```text
CURRENT MACHINE AUTHORITY = NONE
CURRENT CLOSURE AUTHORITY = NONE
INTERNAL SELF-CLAIM OF NORMATIVE/CURRENT/CANONICAL STATUS = HISTORICAL_TEXT_ONLY
```

The detailed historical-self-claim rule is defined by the current Legacy Authority Quarantine Policy in §2.

## 2. Current normative authority path set

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V6.md
  role = SOLE CURRENT MACHINE SOURCE / R9 Wave-7 machine semantics

PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V5.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-6 BASE
  required exact blob = 257539aa3d6a4cc113a39ff1358bb7ed58b3bbe7

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

PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V6.md
  role = CURRENT CLOSED-WORLD IDENTITY / GENESIS INVENTORY COMPANION

PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V5.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-6 BASE
  required exact blob = 2e295a0bde1dc936c18e18893c6e2edabf13f779

PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V4.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-5 BASE
  required exact blob = fccc1c1b3563a17b920f2c7fa395d420d0ef6c63

PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V3.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-4 BASE
  required exact blob = cc2179907ac619b7534be976fa55c715a075b0ef

PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V2.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-3 BASE
  required exact blob = 5020e9a7473f9b5ca6ed31b61d563709490c1ae3

PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V7.md
  role = CURRENT CLOSURE / AUDIT / WHOLE-TREE FREEZE PROTOCOL

PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V6.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-7 PROTOCOL BASE
  required exact blob = 0fbf0a6655cfed1ada28597c57d11e9ec935fc1d

PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V5.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-6 PROTOCOL BASE
  required exact blob = a9fe27e8dabb8790307aa65fc616985f18d07191

PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V4.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-5 PROTOCOL BASE
  required exact blob = 81a71c71556cea69d8d348b26017c1968b8ee7d3

PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V3.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-4 PROTOCOL BASE
  required exact blob = fb2cc6b4cd1ccdffff748f63d0ad8b47910b2623

PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V2.md
  role = CONTENT-ADDRESSED IMMUTABLE WAVE-3 PROTOCOL BASE
  required exact blob = 0e90018eeae4ad5f24d76930fad70fbb5fdaf889

PROJECT_GOVERNANCE/AHFMES_ARE_0_LEGACY_AUTHORITY_QUARANTINE_POLICY_V1.md
  role = CURRENT CLOSURE/AUTHORITY-HYGIENE POLICY FOR UNLISTED HISTORICAL SELF-CLAIMS
  cannot add machine rights

PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_CORRECTION_PACKAGE_V6.md
  role = CURRENT R9 ROOT / CORRECTION / PERMANENT REGRESSION COMPANION
  cannot add machine rights absent from Matrix V6

PROJECT_GOVERNANCE/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V6.md
  role = THIS CLOSED CURRENT NORMATIVE PATH SET
```

No wildcard normative path is permitted.

## 3. Supersession rule

All earlier manifests/correction packages and all other ARE drafts/specs are historical/non-current unless explicitly content-addressed in §2.

An unlisted historical file's own prose cannot override this manifest.

## 4. Explicitly non-normative surfaces

```text
PROJECT_GOVERNANCE/CURRENT_AUTHORITY_INDEX.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V1.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V3.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V4.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V5.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V6.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V7.md
LEGACY_AUTHORITY_QUARANTINE_RECORD
future council/regression/consistency/root records
PR / Issue metadata
journals
external packets
binder/handoff metadata
```

They may record evidence/status only.

## 5. Pre-clean consistency proof

Before Clean Pass #1, SA-11 must prove:

```text
all current machine/closure authority originates in §2
all immutable base blobs match exactly
Matrix V6 remains sole machine source
Inventory V6 matches Matrix V6
Protocol V7 points to this Manifest V6
Quarantine Policy is applied to all detected unlisted authority-like self-claims
Correction Package V6 adds no rights absent from Matrix V6
V2 §6.5 normal-new-risk gates remain preserved through composition
no current semantic dependency relies on an unlisted path
LEGACY_AUTHORITY_QUARANTINE_RECORD binds exact inspected path/blob evidence
```

## 6. Exact root membership

`NORMATIVE_CANDIDATE_TREE_ROOT` membership is exactly §2. Exact inherited length-prefixed serialization applies.

After Clean Pass #1 any byte/path/blob change in §2 resets clean-pass sequence to zero.

## 7. Static boundary

This manifest grants no ARE-0 closure, implementation, P001 substantive research, production or PR-merge authority.