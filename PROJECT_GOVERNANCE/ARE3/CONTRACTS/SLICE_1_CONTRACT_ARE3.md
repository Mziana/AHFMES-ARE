# SLICE 1 CONTRACT — ARE-3 (Autonomous Science: Search Tree, Validation & Governor)

Status: **FROZEN T3 — READY FOR CHARTER RATIFICATION T4 / ZERO IMPLEMENTATION AUTHORITY**  
Fase: **ARE-3 Slice-1**  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` & `ENGINEERING/RULES.md`  
Baseline: `@7f57d12` (214 tests pass, Manifest V41)

---

## 1. Lingkup Komponen Slice-1 ARE-3

### A. `SearchTreeEngine` & `ProgramBudgetManager` (`are/search_tree.py`)
- **A1:** Penelusuran pohon hipotesis berbasis genealogi pencarian (`parent_id`, `family_root`, `branch_depth`).
- **A2:** Penegakan konsumsi budget pencarian (*multiplicity accounting* non-reset per SC-05 & SC-06).
- **A3:** Penghentian eksplorasi otomatis (*stopping rules*) saat budget habis $\rightarrow$ status sah `NO_EDGE_FOUND`.

### B. `ValidationService` (`are/validation.py`)
- **B1:** Pengujian statistik out-of-sample yang terikat dengan `EvidenceLedger` holdout reservation.
- **B2:** Penegakan *information-time provenance* (as-of timestamp filtering ketat, zero future lookahead per SC-03).
- **B3:** Perhitungan penalti paparan holdout (*exposure penalty*) secara deterministik.

### C. `CriticEngine` & `GovernorEngine` (`are/governor.py`)
- **C1:** Evaluasi adversarial komparatif antara Challenger vs Champion aktif (SC-14).
- **C2:** Penegakan *Separation of Duties* secara mekanis: penolakan keras jika penemu hipotesis mencoba memvalidasi/mempromosikan sendiri (SC-01, SC-02, G16, G17).
- **C3:** Penerbitan disposisi promosi berkas tanda tangan kriptografis (`PROMOTION_DISPOSITION`).

### D. Penataan Arsitektur Bersama (`are/constants.py` — Resolusi DEBT-04)
- **D1:** Sentralisasi konstanta siklus hidup (`PROBLEM_LIFECYCLES`, `TRANSITIONS`, `SOD_RULES`) ke dalam `are/constants.py`.
- **D2:** Eliminasi duplikasi konstanta di `are/state_machine.py` dan `are/registry.py`.

---

## 2. Kriteria Penerimaan Formal (ACC-301 s/d ACC-310)

| ID | Deskripsi Kriteria Penerimaan | Verifikasi |
|---|---|---|
| **ACC-301** | Search Tree mencatat genealogi lengkap dan budget tidak pernah reset saat eksplorasi cabang baru | `test_are3_search_tree.py` |
| **ACC-302** | Habisnya budget pencarian menghasilkan disposisi sah `NO_EDGE_FOUND` tanpa error | `test_are3_search_tree.py` |
| **ACC-303** | Validation Service menolak data jika timestamp melebihi as-of timestamp klaim (*fail-closed*) | `test_are3_validation.py` |
| **ACC-304** | Konsumsi holdout evidence tercatat rapi di Evidence Ledger dengan exposure tracking | `test_are3_validation.py` |
| **ACC-305** | Percobaan validasi/promosi mandiri oleh creator principal memicu `IllegalTransition` | `test_are3_governor.py` |
| **ACC-306** | Evaluasi Challenger mewajibkan perbandingan inkremental terhadap baseline Champion | `test_are3_governor.py` |
| **ACC-307** | `are/constants.py` menjadi *single source of truth* untuk seluruh konstanta lifecycle | `test_are3_constants.py` |
| **ACC-308** | Integrasi penuh E2E: Search Tree $\rightarrow$ Validation $\rightarrow$ Governor $\rightarrow$ Disposition | `test_are3_e2e_slice1.py` |
| **ACC-309** | Zero external dependencies (murni Python Standard Library) | Code audit |
| **ACC-310** | Seluruh test suite (214 baseline + test baru ARE-3) 100% PASS | `python -m pytest tests/` |

---

## 3. Batasan & Larangan Keras
- **DILARANG** mengakses broker API, socket live trading, atau eksekusi modal riil.
- **DILARANG** melakukan retune atau mengubah estimand saat validasi sedang berjalan (SC-04, SC-10).
- **DILARANG** menggunakan modul acak `random` tanpa seed deterministik.
