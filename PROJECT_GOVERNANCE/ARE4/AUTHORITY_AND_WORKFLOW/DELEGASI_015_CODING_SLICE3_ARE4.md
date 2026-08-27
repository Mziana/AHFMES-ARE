# DELEGASI 015 — Engineering AI: Coding Slice-3 ARE-4 (Experience Modularization DEBT-02 & Final System Qualification)

Status: **DELEGASI AKTIF / AUTHORIZED — CHARTER T4 RATIFIED**  
Diterbitkan: Lead Architect & Auditor · Baseline `@1fc57c9` (259 tests pass)

> Cara pakai: Tempelkan SELURUH blok prompt di bawah ke sesi Engineering AI.

---

## 📋 PROMPT UNTUK ENGINEERING AI (salin dari sini)

```text
PERAN
Kamu adalah ENGINEERING AI (bukan arsitek).
GERBANG: DELEGASI_015 — CODING SLICE-3 ARE-4 — AUTHORIZED
HANYA untuk lingkup di bawah. Luar lingkup = DILARANG.

BASELINE
HEAD saat delegasi = 1fc57c9 (ARE-4 Slice-2 CLOSED, 259 tests pass, Manifest V41)
Kontrak rujukan = PROJECT_GOVERNANCE/ARE4/CONTRACTS/SLICE_3_CONTRACT_ARE4.md

═══════════════════════════════════════════════════════
BAGIAN A — MODULARISASI are/experience.py (DEBT-02 RESOLUTION)
═══════════════════════════════════════════════════════

Pecah file besar `are/experience.py` menjadi 4 submodul kohesif:
1. `are/experience_store.py`:
   - Exception classes: `ExperienceStoreError`, `QualityGateError`, `AnomalyDetectionError`, `ResourceLimitExceededError`, `AlertError`.
   - Quality Gates: `QualityGateRule`, `QualityGateVerdict`, `QualityGateEngine`.
   - Record & Store: `ExperienceRecord`, `ExperienceStore`.
2. `are/anomaly.py`:
   - `AnomalyType`, `AnomalySeverity`, `AnomalyRecord`, `StatisticalBaseline`, `AnomalyDetector`, `AnomalyAlertingEngine`.
3. `are/replay.py`:
   - `ReplayMode`, `ReplayFilter`, `ReplayTrace`, `DeterministicReplayEngine`, `WhatIfScenario`, `WhatIfEngine`, `SynthesisEngine`.
4. `are/adapters.py`:
   - `ModelAdapter`, `PolicyAdapter`, `AuditLogger`, `ResourceBoundsEnforcer`, `ConfigManager`.

5. Perbarui `are/experience.py` sebagai fasad publik (*public facade*):
   - Import dan re-export seluruh simbol dari ke-4 submodul di atas sehingga pemanggil yang melakukan `from are.experience import ...` tidak ada yang patah (ACC-421, ACC-422).

═══════════════════════════════════════════════════════
BAGIAN B — FINAL SYSTEM-WIDE QUALIFICATION TEST
═══════════════════════════════════════════════════════

Buat modul pengujian kualifikasi sistem penuh di `tests/are/`:
`tests/are/test_are4_system_qualification.py`:
- Menguji integrasi end-to-end menyeluruh dari seluruh 4 gelombang ARE (ACC-423):
  1. `ARE-1 Kernel`: EventStore append-only, EvidenceLedger cryptographic CAS, CAS hash chains.
  2. `ARE-2 Experience Intelligence`: ExperienceStore ingestion, QualityGate verification, AnomalyDetector baseline tracking, Deterministic Replay.
  3. `ARE-3 Autonomous Science`: SearchTree hypothesis generation, CapabilitySandbox isolated execution, Telemetry recording, ValidationService holdout validation, CriticEngine adversarial comparison, GovernorEngine SoD promotion, ChampionRegistry succession & rollback.
  4. `ARE-4 Governed Evolution`: CapitalSafetyKernel risk firewall (drawdown, volatility, kill-switch veto), OperationalBrain fast-loop signal processing, RegretAnalyzer anomaly detection, EvolutionaryLoop automated adaptation.

KRITERIA TERIMA (fail-closed, semuanya wajib)
  ACC-421 s/d ACC-430 terpenuhi 100%.
  `python -m pytest tests/ -q` $\rightarrow$ seluruh test PASS (259 baseline + test baru Slice-3).
  Zero test regression (semua test historis di `test_experience.py`, `test_experience_b_c_d.py`, `test_slice2_*.py` lulus 100%).
  Zero external dependencies (Python Standard Library only).
  Working tree clean.

LARANGAN
- Dilarang merusak satupun nama kelas atau fungsi publik yang di-export oleh `are.experience`.
- Dilarang menyentuh broker API, live socket trading, atau eksekusi modal riil.

PROSES
1. Buat 4 submodul di `are/` dan jadikan `are/experience.py` sebagai facade re-export.
2. Buat `tests/are/test_are4_system_qualification.py`.
3. Jalankan `python -m pytest tests/ -q` -> pastikan seluruh 259+ test PASS.
4. Commit di main: "feat(are4): implement Slice-3 Modularize experience.py DEBT-02 & System Qualification (DELEGASI_015)"
5. Laporkan hasilnya ke Lead Architect.
```
