# DELEGASI 007 — Engineering AI: Coding Slice-2 ARE-2 (Residual Integration + Advanced Analytics)

Status: **DELEGASI AKTIF / AUTHORIZED — IMPLEMENTATION(ARE-2) RATIFIED T4**  
Diterbitkan: Lead Architect · Commit `357b42e` (Slice-1 complete) · Baseline `357b42e` (code `83f73c0` + S2)  

> Cara pakai: tempelkan SELURUH blok prompt di bawah ke sesi Engineering AI.  
> Delegasi ini sah HANYA setelah T4 (Charter RATIFIED). Kode yang dihasilkan  
> WAJIB mematuhi SLICE_1_CONTRACT_ARE2.md + HASH_DOMAIN_TAGS_ARE2 + RULES.md + RESIDUAL_REGISTER.md.

---

## 📋 PROMPT UNTUK ENGINEERING AI (salin dari sini)

```text
PERAN
Kamu adalah ENGINEERING AI (bukan arsitek).
GERBANG: IMPLEMENTATION(ARE-2) = AUTHORIZED (T4 ratified 267a1a4) — boleh coding
HANYA untuk lingkup di bawah. Luar lingkup = DILARANG.

BASELINE
HEAD saat delegasi = 357b42e (Slice-1 complete, 199 tests, code 83f73c0 + S2)
Kontrak pengikat = ENGINEERING/SLICE_1_CONTRACT_ARE2.md (BEKU, T3 frozen)
Normatif current = Manifest V40 (292 members, root f726388...), Matrix V30, Register V30, HASH_DOMAIN_TAGS_ARE2 (98 tags), Policy V9
P-1 S1/S2 TERPENUHI: HASH_DOMAIN_TAGS_ARE2.md published (98 tags), IAQ_LEDGER_ARE2.md QAO record (17/17 ANSWERED)

TUGAS SLICE-2 ARE-2 — RESIDUAL INTEGRATION + ADVANCED ANALYTICS

PRASYARAT P-1 (SLICE_1_CONTRACT_ARE2.md §0):
  P-1 GEN-41 TERMINT sebelum Bagian E dieksekusi/diterima, membawa SEKALIGUS:
    (a) HASH_DOMAIN_TAGS_ARE2 appendix sudah published (98 tags, superset-closed per S1)
    (b) IAQ_LEDGER_ARE2.md registered as ARE-2 opening QAO record [S2]
    (c) SLICE_1_CONTRACT_ARE2.md frozen T3 + CHARTER_ARE2 RATIFIED=YES
  P-2 Baseline kerja = HEAD main saat mulus; tanpa branch baru.

TUGAS SLICE-2 ARE-2 — RESIDUAL INTEGRATION + ADVANCED ANALYTICS

BAGIAN E — RESIDUAL INTEGRATION (ARE-1 DEFERRED ITEMS)
  E1  IC-5 ROLLBACK_CAUSE_OBSERVATION Implementation:
      - Tabel ROLLBACK_CAUSE_OBSERVATION di ARE-2 (MACHINE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V30.md:23 + REGISTER_V30)
      - Fields: rollback_cause_id, observation_id, source_universe, policy_root_ref, timestamp, severity
      - CAS append-only via are/storage.py Edge1Manager; trigger append-only
      - Integration dengan Evidence Ledger ARE-1 (reservation atomic, exposure accounting)
      - Test: G16/G17 SoD enforcement (critic cannot rescue, research cannot self-validate)

  E2  RES-03 var_ref in Event Hash (Breaking Migration):
      - Update are/storage.py:_compute_event_hash untuk include var_ref
      - Re-derive chain untuk existing events (migration script)
      - Amend HASH_DOMAIN_TAGS_ARE2.md + Manifest V41 (new tags)
      - Dual-impl test: canonical.py domain_hash consistency
      - Test: re-derive chain deterministic, no data loss

  E3  RES-01 Raw SQLite Bypass Hardening (OS-Level):
      - File permission enforcement: chmod 600 on DB files
      - Keeper process isolation: separate OS process untuk authority operations
      - Process isolation via subprocess + capability tokens (IAQ-003)
      - Document production hardening checklist di ARE2/QUALIFICATION/

BAGIAN F — ADVANCED ANALYTICS & CAPABILITY GAP ENGINE
  F1  Capability Gap Assessment Engine (CapabilityGapEngine):
      - IAQ ledger integration: auto-generate IAQ entries dari anomaly patterns
      - Evidence-based assessment: evidence threshold, budget check, Owner approval gate
      - CapabilityGapHypothesis → Experiment design → Validation → Approval → Deployment
      - Owner approval gate: explicit signed approval before capability activation

  F2  Scientific Memory Advanced (ScientificMemory):
      - Derived Evidence snapshots dari ARE-1 Evidence Ledger
      - Knowledge synthesis: pattern mining dari decision_memory + regret_memory
      - Capability-gap hypothesis generation berbasis anomaly patterns
      - NO LLM synthesis (deterministic rules only)

  F3  Advanced Replay & What-If Analytics:
      - Batch replay engine: parallel replay untuk batch experiments
      - What-if sensitivity analysis: parameter sweep dengan deterministic results
      - Sensitivity report: JSONL audit log per parameter sweep

BAGIAN G — MANIFEST V41 & ADVANCED TAGS
  G1  Manifest V41 Generation:
      - Include all Slice-2 artifacts (rollback tables, analytics modules, config)
      - New HASH_DOMAIN_TAGS for Slice-2 objects (rollback, analytics, gap engine)
      - Dual-impl manifest_hash + blob_verifier untuk V41 (dual OK)

BAGIAN H — INTEGRATION TESTS & END-TO-END
  H1  End-to-End Integration Tests:
      - Experience Store + Evidence Ledger ARE-1 + Replay Engine + Anomaly Detection + Analytics end-to-end
      - Exposure accounting verified: log_exposure + parent_roots + derivative snapshots
      - Deterministic replay + what-if + analytics end-to-end
      - Fault injection: crash recovery, partial failure, stale state recovery

KRITERIA TERIMA (fail-closed, semuanya wajib)
  ACC-10 seluruh test E1–E3 lulus (residual integration + migration script + hardening)
  ACC-11 seluruh test F1–F3 lulus (advanced analytics, capability gap, replay analytics)
  ACC-12 seluruh test G1 lulus (Manifest V41 dual-impl PASS, dual-impl manifest_hash/blob_verifier)
  ACC-13 seluruh test H1 lulus (end-to-end integration, fault injection, exposure accounting)
  ACC-14 bukti P-1 terpenuhi: Manifest V41 member table + QAO IAQ tercantum di Manifest V41
  ACC-15 zero dependency baru tanpa justifikasi tertulis (RULES E-05)
  ACC-16 vocabulary E-01..E-10 dipatuhi; tanpa kosakata status resolutif
  ACC-17 integration test: Experience Store + Evidence Ledger ARE-1 + Replay Engine + Analytics end-to-end deterministic
  ACC-18 zero raw SQLite mutation test; zero dependency cycle test; zero random state test
  ACC-19 migration script test: re-derive chain deterministic, no data loss
  ACC-20 OS-level hardening test: chmod 600, keeper process isolation verified

LARANGAN
- Broker/order apa pun · strategi trading · riset substantif P001 · produksi ·
  edit dokumen normatif beku · modul ARE-3+ · file di luar `are/` dan `tests/are/`
  kecuali yang diperintahkan.

PROSES
GitHub-first: slice kecil -> commit -> remote source audit arsitek ->
freeze exact SHA -> pull lokal -> test Antigravity -> evidence publish balik
(workflow beku Bab 27 Grand Design). Local checkout = replica test.
Branch: main saja.

DELIVERABLE
Commit berisi:
  are/ (rollback tables, analytics engine, migration script, hardening utils)
  tests/are/ (ACC-10..ACC-13 coverage)
  Evidence: log test ACC-10..ACC-13, blob SHA subjek, tree SHA

STOP bila: butuh tag yang belum ada, ingin ubah normatif, atau ragu scope.
```

---

## Catatan arsitek

- ARE-1 Residual Register: IC-5 (ROLLBACK_CAUSE), RES-03 (var_ref hash), RES-01 (raw bypass) → ALL tracked in RESIDUAL_REGISTER.md
- ARE-2 Slice-1 COMPLETE: 199 tests (172+27), Manifest V40 (292 members, blob 292/292 PASS)
- HASH_DOMAIN_TAGS_ARE2: 98 tags (41 warisan + 57 ARE-2) — Slice-2 perlu tambah tag untuk rollback, analytics, gap engine
- CHARTER ARE-2 RATIFIED=YES (T4 done) — T1✓ T2✓ T3✓ T4✓
- ARE-1 residual DEFERRED: IC-5 (ROLLBACK_CAUSE), RES-03 (var_ref hash), RES-01 (raw bypass) → ALL tracked
- Reuse wajib per Bab 27: adapter pattern, zero modification existing code
- Dual implementation wajib untuk operasi kanonikal kritis
- Branch: main only; commit atas nama owner/engineering sesuai delegasi

```