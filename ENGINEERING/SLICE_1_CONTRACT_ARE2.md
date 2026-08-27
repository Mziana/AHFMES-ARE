# SLICE-1 CONTRACT — Experience Store + Anomaly Detection + Replay Engine (ARE-2)

Status: **FROZEN T3 / LEAD ARCHITECT / prasyarat & kriteria terima mengikat**  
Dibekukan: 2026-08-27 · Baseline: lineage gen-39 → ARE-1 CLOSED @a6711d6 (code 83f73c0)  
Penerima delegasi: Engineering AI (via DELEGASI bernomor berikutnya)

## 0. Prasyarat mutlak

```text
P-1 GEN-40 TERMINT sebelum Bagian B dieksekusi/diterima, membawa SEKALIGUS:
    (a) lampiran AHFMES_ARE_HASH_DOMAIN_TAGS_ARE2 — SUPERSET-TERTUTUP:
        memuat tag warisan ARE-1 (VERBATIM, makna string tidak berubah),
        + tag untuk SEMUA tipe objek Experience Intelligence (ARE-2),
        + aturan penutupan: "tipe objek tanpa tag terdaftar =>
          operasi hashing DENY fail-closed" sampai lampiran diamendemen
          lewat generasi baru;                                   [syarat S1]
    (b) registrasi ENGINEERING/IAQ_LEDGER_ARE2.md sebagai QAO record pembuka
        ARE-2.                                                  [syarat S2]
P-2 Baseline kerja = HEAD main saat mulus; tanpa branch baru.
```

## 1. Lingkup Bagian A — Experience Store + Anomaly Detection

```text
A1  Experience Store append-only di SQLite (WAL, reuse are/storage.py):
    - 3 stream terpisah: decision_memory, regret_memory, anomaly_detection
    - CAS per stream via WHERE last_revision=? (reuse are/storage.py)
    - Crash-matrix invariant test wajib: simulasi crash di setiap titik
      antara dua write => state selalu direkonstruksi dari committed rows
    - Replay engine: pure function replay + fork snapshot what-if;
      original state immutable; verify_chain deterministic

A2  Anomaly Detection deterministik:
    - Regime shift detection: threshold-based, fixed-seed HMM
    - Spread hostility: deterministic function(spread, volatility, volume)
    - Counterfactual quality: CF-HIGH/MED/LOW/UNOBSERVABLE rule-based per anomaly type
    - Model artifact content-addressed via are/canonical.py; NO random state
    - Deterministic thresholds, fixed-seed HMM; model artifact content-addressed

A3  Observability & Data Quality Gates:
    - Pipeline gates: completeness 99.9%, latency <100ms, provenance 8-field,
      schema validation; reject fail-closed
    - Quarantine statistik untuk suspicious data; Owner daily review
    - Metrics + audit log per gate; reject invalid at ingestion
```

## 2. Lingkup Bagian B — Replay Engine + What-If Engine + Knowledge Synthesis

```text
B1  Deterministic Replay Engine:
    - Pure function replay: input (market_data, initial_state, decision_logic)
      → output; zero side effects; state machine pure; reuse are/storage.py
    - What-If Engine: fork snapshot → apply counterfactual → simulate → discard
      fork; original state immutable; content-addressed snapshots
    - Counterfactual quality: CF-HIGH/MED/LOW/UNOBSERVABLE rule-based per
      anomaly type; config frozen, auditable; NO ML-based

B2  Knowledge Synthesis & Capability Gap:
    - Scientific Memory = derived Evidence snapshots (reuse are/evidence.py)
    - Capability-gap = IAQ ledger entry + Owner approval gate; NO LLM synthesis
    - Assessment = deterministic rules (evidence threshold, budget check) + Owner approval

B3  Integration: Evidence Ledger ARE-1 + Experience Store:
    - Experience Store = consumer Evidence Ledger via reservation API
    - Derivative snapshot dengan parent_roots; exposure accounting
      reuse are/evidence.py:870 log_exposure
    - NO IPC for MVP; same process, shared SQLite, separate tables
```

## 3. Lingkup Bagian C — Observability + Reuse + Configuration

```text
C1  Observability & Anomaly Alerting:
    - Deterministic alert rules: threshold/cooldown/dedup + audit log per alert
    - Emergency-flat DILARANG di IAQ (memerlukan authority ACT terpisah)
    - Integration CSK: critical anomaly → emergency flat trigger (separate authority)

C2  Reuse Existing Components (Bab 27 Grand Design):
    - Adapter pattern per component: orchestrator.py, habitat_memory.py,
      evaluation_writer.py, pattern_events.py, pattern_recovery.py,
      policy_contract.py, freeze_snapshot.py, runtime_identity.py,
      telemetry.py, direction_discovery.py, micro_executor.py
    - Zero modification existing code; Experience Store ARE-2 package terpisah

C3  Configuration & Version Management:
    - Config as typed Python module (frozen dataclass); git versioned;
      hash via are/canonical.py:183 domain_hash; load-once immutable
    - Secrets via env var only; config structural di file
```

## 4. Lingkup Bagian D — Observability + Audit + Performance

```text
D1  Auditor Reproducibility:
    - Structured JSONL audit log per component: timestamp, operation,
      input_hash, output_hash, params_hash, duration_ms, success
    - Deterministic output dual-check; future MANIFEST V40+ integration
    - Reuse TOOLS/manifest_hash, blob_verifier pattern

D2  Performance & Resource Bounds:
    - Config-driven bounds: max_memory_mb, max_replay_sec, max_anomaly_ms
    - Quota per component: replay, what-if, anomaly detector masing-masing
    - Rejection fail-closed + metrics logging

D3  Audit Trail & External Auditor Reproducibility:
    - Structured JSONL audit log per component
    - Deterministic output dual-check; future MANIFEST V40+ integration
    - Reuse TOOLS/manifest_hash, blob_verifier pattern
```

## 5. Kriteria terima (fail-closed, semuanya wajib)

```text
ACC-1 seluruh test A1–A3 lulus termasuk crash-matrix penuh + deterministic replay test
ACC-2 seluruh test B1–B3 lulus pada implementasi (deterministic replay, what-if, knowledge synthesis)
ACC-3 seluruh test C1–C3 lulus (observability gates, reuse adapters, config immutability)
ACC-4 seluruh test D1–D3 lulus (audit trail reproducibility, resource bounds, performance bounds)
ACC-5 bukti P-1 terpenuhi: blob lampiran tag ARE-2 + QAO IAQ tercantum
      di Manifest V40 (member), diverifikasi via git objects
ACC-6 zero dependency baru tanpa justifikasi tertulis (RULES E-05)
ACC-7 vocabulary E-01..E-10 dipatuhi; tanpa kosakata status resolutif
ACC-8 integration test: Experience Store + Evidence Ledger ARE-1 + Replay Engine
      end-to-end deterministic; exposure accounting verified
ACC-9 zero raw SQLite mutation test; zero dependency cycle test; zero random state test
```

## 6. Di luar lingkup keras

Broker/order apa pun · strategi trading · riset substantif P001 · produksi ·
edit dokumen normatif beku · modul ARE-3+ · file di luar `are/` dan `tests/are/`
kecuali yang diperintahkan delegasi.

## 7. Proses

GitHub-first: slice kecil → commit → remote source audit arsitek → koreksi →
freeze exact SHA → pull lokal → test Antigravity → evidence publish balik
(workflow beku Bab 27 Grand Design). Local checkout = replica test.