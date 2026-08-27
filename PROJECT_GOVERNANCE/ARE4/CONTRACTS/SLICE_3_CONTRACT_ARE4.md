# SLICE 3 CONTRACT — ARE-4 (Experience Modularization DEBT-02 & Final System Qualification)

Status: **FROZEN T3 — RATIFIED FOR IMPLEMENTATION / AUTHORIZED**  
Fase: **ARE-4 Slice-3 (Final Slice of ARE-4 Wave)**  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` & `ENGINEERING/RULES.md`  
Baseline: `@1fc57c9` (259 tests pass, Manifest V41)

---

## 1. Lingkup Komponen Slice-3 ARE-4

### A. Resolusi `DEBT-02` — Modularisasi God File `experience.py`
- **A1:** Memecah file monolithic `are/experience.py` (~1184 baris, 43 kelas) menjadi submodul mandiri yang kohesif:
  1. `are/experience_store.py`: Pengecualian (`ExperienceStoreError`, dll.), Quality Gates (`QualityGateEngine`, `QualityGateRule`), dataclass `ExperienceRecord`, dan kelas `ExperienceStore`.
  2. `are/anomaly.py`: `AnomalyRecord`, `AnomalyDetector`, `StatisticalBaseline`, `AnomalyAlertingEngine`.
  3. `are/replay.py`: `DeterministicReplayEngine`, `WhatIfEngine`, `SynthesisEngine`.
  4. `are/adapters.py`: Component Adapters, `AuditLogger`, dan `ResourceBounds`.
- **A2:** Mempertahankan `are/experience.py` sebagai fasad publik (*public facade*) yang mengekspor seluruh simbol secara backward-compatible 100% tanpa mengubah satupun import path pada test suite yang sudah ada (ACC-421, ACC-422).

### B. Pengujian Kualifikasi Sistem Penuh (Full System-Wide Qualification)
- **B1:** Test integrasi komprehensif lintas 4 generasi (`tests/are/test_are4_system_qualification.py`):
  `Scientific Kernel (ARE-1)` $\rightarrow$ `Experience Intelligence (ARE-2)` $\rightarrow$ `Autonomous Discovery Tree & Champion Registry (ARE-3)` $\rightarrow$ `Fast/Slow Dual Loop & Capital Safety Kernel (ARE-4)` (ACC-423).

---

## 2. Kriteria Penerimaan Formal (ACC-421 s/d ACC-430)

| ID | Deskripsi Kriteria Penerimaan | Verifikasi |
|---|---|---|
| **ACC-421** | `are/experience.py` dipecah menjadi submodul kohesif (`experience_store.py`, `anomaly.py`, `replay.py`, `adapters.py`) (`DEBT-02`) | Code audit |
| **ACC-422** | `are/experience.py` mempertahankan 100% kompatibilitas ke belakang untuk seluruh pemanggil | `test_experience*.py` |
| **ACC-423** | System-Wide Qualification Test memvalidasi alur terpadu ARE-1 s/d ARE-4 secara utuh | `test_are4_system_qualification.py` |
| **ACC-424** | Seluruh 4 hutang arsitektur utama (`DEBT-01`, `DEBT-02`, `DEBT-03`, `DEBT-04`) berstatus **RESOLVED & VERIFIED** | `RESIDUAL_REGISTER.md` |
| **ACC-425** | Zero external dependencies (murni Python Standard Library) | Code audit |
| **ACC-426** | Seluruh test suite (259 baseline + pengujian baru Slice-3) 100% PASS | `python -m pytest tests/` |
| **ACC-427** | Repositori bersih tanpa file sementara (`working tree clean`) | `git status` |
| **ACC-428** | Dual-implementation `manifest_hash` & `blob_verifier` 100% PASS | `TOOLS/` verification |
| **ACC-429** | Laporan audit kualifikasi penutupan gelombang ARE-4 lengkap | Audit report |
| **ACC-430** | Gerbang eksekusi modal/live broker terkunci aman (*fail-closed firewall*) | `are/safety.py` & audit |

---

## 3. Batasan & Larangan Keras
- **DILARANG** merusak satupun import path atau nama kelas dari `are.experience`.
- **DILARANG** membuka akses eksekusi order live ke broker eksternal.
