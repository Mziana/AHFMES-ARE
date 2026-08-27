# SLICE 2 CONTRACT — ARE-4 (Evolutionary Slow Loop & Registry Modularization DEBT-01)

Status: **FROZEN T3 — RATIFIED FOR IMPLEMENTATION / AUTHORIZED**  
Fase: **ARE-4 Slice-2**  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` & `ENGINEERING/RULES.md`  
Baseline: `@0ee66ed` (256 tests pass, Manifest V41)

---

## 1. Lingkup Komponen Slice-2 ARE-4

### A. `EvolutionaryLoop` & `RegretAnalyzer` (`are/evolution.py`)
- **A1:** Dataclass `AdaptationTrigger`: `trigger_id: str`, `source_anomaly: str`, `problem_id: str`, `suggested_hypothesis: Dict[str, Any]`, `timestamp: float`.
- **A2:** Kelas `RegretAnalyzer`:
  - Menganalisis stream `"operational_signals"` dan performa aktual.
  - Mendeteksi anomali (*regret*, degradasi win-rate, atau deviasi rezim berkepanjangan) dan menerbitkan `AdaptationTrigger` (ACC-411).
- **A3:** Kelas `EvolutionaryLoop`:
  - Menghubungkan `RegretAnalyzer` $\rightarrow$ pendaftaran/pembaruan `Problem` di `Registry` $\rightarrow$ pemicuan siklus riset otonom di `ResearchCoordinator` (ACC-412).
  - Menjamin mutasi policy tidak pernah dilakukan in-place di Fast Loop melainkan wajib melalui suksesi Champion yang ter-governed (ACC-415).

### B. Resolusi `DEBT-01` — Modularisasi God Class `Registry` (`are/registry.py`)
- **B1:** Memisahkan logika CRUD dan validasi 8 entitas ke dalam delegate class / submodule helper yang kohesif:
  - `ProblemManager`, `HypothesisManager`, `ExperimentManager`, `CandidateManager`, `CapabilityManager`, `GraveyardManager`.
- **B2:** Mempertahankan kelas `Registry` sebagai fasad publik (*public facade*) dengan antarmuka yang 100% kompatibel ke belakang (*backward-compatible*) tanpa mengubah signature metode publik yang sudah ada (ACC-413, ACC-414).

---

## 2. Kriteria Penerimaan Formal (ACC-411 s/d ACC-420)

| ID | Deskripsi Kriteria Penerimaan | Verifikasi |
|---|---|---|
| **ACC-411** | Regret Analyzer mendeteksi anomali performa dan menerbitkan `AdaptationTrigger` | `test_are4_evolution.py` |
| **ACC-412** | Evolutionary Loop memicu siklus riset otonom lambat dari anomali operasional | `test_are4_evolution.py` |
| **ACC-413** | God Class `Registry` direfaktor menggunakan Strategy / Delegate Pattern (`DEBT-01`) | `are/registry.py` audit |
| **ACC-414** | Fasad `Registry` mempertahankan kompatibilitas penuh 100% dengan test suite lama | `tests/are/test_registry.py` |
| **ACC-415** | Evolutionary Loop menegakkan SoD dan ProgramBudget non-reset secara fail-closed | `test_are4_evolution.py` |
| **ACC-416** | Zero external dependencies (murni Python Standard Library) | Code audit |
| **ACC-417** | Integrasi E2E Penuh: Fast Loop Anomaly $\rightarrow$ Slow Loop Discovery $\rightarrow$ Champion Succession | `test_are4_e2e_slice2.py` |
| **ACC-418** | Seluruh test suite (256 baseline + test baru ARE-4 Slice-2) 100% PASS | `python -m pytest tests/` |
| **ACC-419** | Repositori bersih tanpa file sementara (`working tree clean`) | `git status` |
| **ACC-420** | Dual-implementation `manifest_hash` & `blob_verifier` 100% PASS | `TOOLS/` verification |

---

## 3. Batasan & Larangan Keras
- **DILARANG** melakukan mutasi parameter operasional atau policy secara langsung (*in-place bypass*) tanpa melalui alur riset penuh.
- **DILARANG** memecah antarmuka publik `Registry` yang dapat menyebabkan regresi pada kode pemanggil yang ada.
