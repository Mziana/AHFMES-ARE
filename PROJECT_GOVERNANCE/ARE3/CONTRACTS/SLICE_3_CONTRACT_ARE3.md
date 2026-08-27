# SLICE 3 CONTRACT — ARE-3 (Autonomous Science: Multi-Agent Coordinator & Champion Registry)

Status: **FROZEN T3 — RATIFIED FOR IMPLEMENTATION / AUTHORIZED**  
Fase: **ARE-3 Slice-3 (Final Slice ARE-3)**  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` & `ENGINEERING/RULES.md`  
Baseline: `@691cc97` (239 tests pass, Manifest V41)

---

## 1. Lingkup Komponen Slice-3 ARE-3

### A. `ResearchCoordinator` & `AgentAssignment` (`are/coordinator.py`)
- **A1:** Orkestrasi siklus riset otonom terintegrasi:
  `Habitat/Market Observation` $\rightarrow$ `Search Tree Hypothesis` $\rightarrow$ `Capability Sandbox Execution` $\rightarrow$ `Telemetry Recording` $\rightarrow$ `Validation Service` $\rightarrow$ `Adversarial Critic` $\rightarrow$ `Governor Promotion Gate`.
- **A2:** Penegakan *Multi-Agent Separation of Duties*: Menetapkan dan memvalidasi bahwa agen Penemu (*Discovery Agent*), agen Penguji (*Validation Agent*), dan agen Pengambil Keputusan (*Governor Agent*) memiliki principal identity yang berbeda secara mekanis (SC-01, SC-02, G16, G17).
- **A3:** Penanganan status *No Edge Found* atau *Rejected* secara elegan tanpa crash atau infinite loop (SC-06, SC-12).

### B. `ChampionRegistry` (`are/champion.py`)
- **B1:** Pengelolaan status model/strategi aktif (*Champion*) secara terenkapsulasi di atas `EventStore` stream `"champion_registry"`.
- **B2:** Penolakan mutlak terhadap aktivasi kandidat yang tidak memiliki berkas `PromotionDisposition` berstatus `PROMOTED` yang valid dan bertanda tangan kriptografis dari Governor.
- **B3:** Riwayat suksesi Champion dan mekanisme *rollback* ke versi Champion sebelumnya jika terjadi anomali kritis.

---

## 2. Kriteria Penerimaan Formal (ACC-321 s/d ACC-330)

| ID | Deskripsi Kriteria Penerimaan | Verifikasi |
|---|---|---|
| **ACC-321** | Research Coordinator mengorkestrasi siklus riset otonom penuh secara deterministik | `test_are3_coordinator.py` |
| **ACC-322** | Research Coordinator menegakkan SoD antar agen (Creator $\neq$ Validator $\neq$ Promoter) | `test_are3_coordinator.py` |
| **ACC-323** | Champion Registry mencatat suksesi Champion ke EventStore stream `"champion_registry"` | `test_are3_champion.py` |
| **ACC-324** | Champion Registry menolak aktivasi kandidat tanpa `PromotionDisposition` sah (*fail-closed*) | `test_are3_champion.py` |
| **ACC-325** | Champion Registry mendukung rollback ke Champion sebelumnya dengan jejak audit | `test_are3_champion.py` |
| **ACC-326** | Integrasi E2E Otonom Penuh: Siklus riset lengkap hingga aktivasi Champion | `test_are3_e2e_slice3.py` |
| **ACC-327** | Zero external dependencies (murni Python Standard Library) | Code audit |
| **ACC-328** | Seluruh test suite (239 baseline + test baru ARE-3 Slice-3) 100% PASS | `python -m pytest tests/` |
| **ACC-329** | Tidak ada file temporer, untracked artifacts, atau cache di repositori | `git status` |
| **ACC-330** | Dual-implementation `manifest_hash` & `blob_verifier` 100% PASS | `TOOLS/` verification |

---

## 3. Batasan & Larangan Keras
- **DILARANG** membuka akses eksekusi order ke broker live atau paper trading (Hukum Otoritas Fundamental `THINK -> PROVE -> ACT`).
- **DILARANG** melemahkan authorizer atau triggers append-only di `are/storage.py`.
- **DILARANG** menggunakan modul acak `random` tanpa seed deterministik.
