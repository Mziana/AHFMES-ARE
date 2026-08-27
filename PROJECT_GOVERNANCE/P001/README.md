# P001 — Autonomous Alpha Research Program & Operational Runner Suite

Status: **WAVE INITIALIZED / IMPLEMENTATION AUTHORIZED**  
Kategori: **P001 (Research Program P001 & Tooling)**  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` & `ENGINEERING/RULES.md`  
Baseline: `@c2db321` (260 tests pass, Manifest V41)

---

## Ringkasan Gelombang P001

Gelombang **P001** adalah fase operasionalisasi mesin riset sains otonom AHFMES-ARE untuk melakukan penemuan strategi/alpha kuantitatif nyata, dilengkapi runner daemon dan antarmuka CLI/Dashboard:

1. **Slice-1 (Operational Tooling, CLI & Terminal Dashboard):**
   - `are/cli.py`: Antarmuka baris perintah lengkap (`status`, `run-cycle`, `run-daemon`, `telemetry`, `champion`, `safety-kill`).
   - `are/runner.py`: Background runner daemon yang mengoordinasikan *Fast Loop* dan *Slow Loop*.
   - `are/dashboard.py`: Rich visual terminal dashboard untuk memantau performa, status CSK, drawdown, dan Champion aktif.
2. **Slice-2 (P001 Alpha Discovery Engine, Feature Library & Market Ingestion):**
   - `are/features.py`: Library ekstraksi fitur kuantitatif (Orderbook Imbalance, Volatility, Momentum).
   - `are/alpha_generator.py`: Generator hipotesis kuantitatif berbasis template *SearchTreeEngine*.
   - `are/ingestion.py`: Pipeline ingestion data pasar ke dalam *EvidenceLedger* dan *ExperienceStore*.
   - `are/p001_program.py`: End-to-end autonomous research program execution.

---

## Subfolder (Mirror Standar Tata Kelola)

| Folder | Isi (P001) | Status |
|---|---|:---:|
| `GRAND_DESIGN/` | Desain riset alpha & arsitektur CLI runner | `.gitkeep` |
| `AUTHORITY_AND_WORKFLOW/` | Charter P001 & Delegasi eksekusi | Charter T4 Ratified, DELEGASI_016 |
| `CONTRACTS/` | Kontrak formal Slice-1 & Slice-2 P001 | SLICE_1_CONTRACT_P001.md (FROZEN) |
| `MACHINE/` | Sumber mesin kanonikal P001 | `.gitkeep` |
| `MANIFEST/` | Manifest normatif P001 | Manifest V41 Binding |
| `COUNCIL_PROTOCOL/` | Protokol audit P001 | `.gitkeep` |
| `QUARANTINE/` | Kebijakan karantina data/model | `.gitkeep` |
| `R9_CORRECTIONS/` | Koreksi dampak | `.gitkeep` |
| `EXTERNAL_AUDIT/` | Handoff & audit eksternal P001 | `.gitkeep` |
| `QUALIFICATION/` | Bukti kualifikasi internal P001 | AHFMES_P001_SLICE1_AUDIT_REPORT.md (10/10 PASS) | 1 file |
| `DIARY/` | Diary harian P001 | 2026-08-28-P001-OPENING-JURNAL.md | 1 file |

---

## Titik Baca Cepat (Fase Eksekusi Slice-1 P001, Baseline `@c2db321`)

1. **Entry point otoritas:** `../CURRENT_AUTHORITY_INDEX.md` $\rightarrow$ `P001 = IMPLEMENTATION AUTHORIZED`
2. **Kontrak Slice-1 (ACTIVE):** `CONTRACTS/SLICE_1_CONTRACT_P001.md` (ACC-501..510 FROZEN)
3. **Charter Otoritas:** `AUTHORITY_AND_WORKFLOW/IMPLEMENTATION_AUTHORITY_CHARTER_P001.md` (RATIFIED T4)
4. **Delegasi Aktif:** `AUTHORITY_AND_WORKFLOW/DELEGASI_016_CODING_SLICE1_P001.md`
5. **Jurnal harian P001:** `DIARY/2026-08-28-P001-OPENING-JURNAL.md`
6. **Indeks Progres Global:** `../../PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md`
