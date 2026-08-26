# AHFMES ARE-0 — Hash Domain Tags V1

Status: **NORMATIVE APPENDIX / SUPERSET-CLOSED ENUMERATION / MEMBER OF MANIFEST V39 / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-26** · Melahirkan dari IAQ-008 (syarat S1 auditor)

## Aturan penutupan (closure rule)

> **Tipe objek tanpa tag terdaftar di tabel ini => SETIAP operasi hashing atas
> objek tersebut DENY fail-closed**, sampai lampiran ini diamendemen lewat
> generasi baru. Tidak ada inferensi tag dari nama file/kelas/string lain.

## Tag warisan 0B V3 §11 (VERBATIM — makna string tidak berubah)

```text
CANDIDATE_ROOT
RESEARCH_CONTRACT
EVIDENCE_SNAPSHOT
EVIDENCE_MANIFEST
SEARCH_TREE
SEARCH_DEBT
VALIDATION_FAMILY
PROOF_BUNDLE
PROMOTION_GATE_SPEC
GATE_MANIFEST
ROLE_MANIFEST
CONSTITUTION
CAPITAL_SAFETY
DEPLOYMENT_CONTEXT
CHAMPION_REGISTRY_EVENT
```

## Tag untuk seluruh tipe objek Register V30 (+ pelengkap mesin)

```text
REFINEMENT_RELIANCE_INVALIDITY_EVENT_ROOT
REFINEMENT_PROSPECTIVE_RELIANCE_SUBJECT
REFINEMENT_PROSPECTIVE_RELIANCE_RECEIPT
REFINEMENT_PROSPECTIVE_RELIANCE_VAR_CURRENT
EDGE_NONCE_CONSUMPTION_LEDGER
REFINEMENT_PROSPECTIVE_RELIANCE_SOD_ROOT
ROLLBACK_CAUSE_OBSERVATION
ROLLBACK_CAUSE_OBSERVATION_SOURCE_UNIVERSE
ROLLBACK_POLICY_ROOT
EDGE_INTERFERENCE_EVIDENCE
```

## Tag infrastruktur event-store (dipakai previous-event-hash chain)

```text
EVENT_STORE_ENTRY
EVENT_STORE_HEAD
DECISION_STATE_REVISION
CAPITAL_ACTION_EPISODE
SAFETY_CONTRACT_CHANGE_PROPOSAL_RECORD
CAPITAL_SAFETY_OBSERVATION_RECORD
CHAMPION_ROLLBACK_PLAN
BROKER_MUTATION_RECORD
OPERATIONAL_FIDELITY_LEDGER_ENTRY
FAMILY_LIFETIME_LEDGER_ENTRY
PROGRAM_BUDGET_RESERVATION
EVIDENCE_RESERVATION
RELATION_DECISION
CAPABILITY_ACTIVATION_EPISODE
DEPLOYMENT_ACTIVATION_EPISODE
INTEGRITY_DEFECT_RECORD
```

## Aturan penggunaan

```text
1. Hash identitas objek tipe T:
   SHA256("AHFMES:" || <TAG(T)> || ":V1\n" || canonical_bytes)
   TAG(T) wajib lookup EXAKT (case-sensitive) ke tabel di atas.
2. Tipe baru lahir hanya lewat generasi dokumen baru yang mengamendemen
   lampiran ini (baris ditambah, tag lama tak pernah diubah maknanya).
3. Dua implementasi hasher wajib lolos uji silang atas SELURUH tabel.
4. Tag tidak pernah menjadi key material untuk data runtime — ia hanya
   pemisah domain hash.
```

## Firewall

```text
ARE-0 CLOSED (formal design) | IMPLEMENTATION = NOT AUTHORIZED sampai
IMPLEMENTATION_AUTHORITY_CHARTER RATIFIED oleh owner (T4).
P001 = NOT AUTHORIZED ; PRODUCTION = CLOSED ; LIVE/PAPER = NOT AUTHORIZED.
```
