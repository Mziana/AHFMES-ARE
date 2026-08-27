# ARE3 — Index Kategori (Autonomous Science & Direction Intelligence)

Status: **ARSIP FASE ARE-3 / EVIDENCE-CHRONOLOGY / INITIALIZATION / ZERO IMPLEMENTATION AUTHORITY**  
Fase: **ARE-3 Autonomous Science** — Direction Discovery, Habitat Integration, Telemetry Aggregation, Micro-Execution Boundaries  
Aturan struktur & diary: [`../GOVERNANCE_FOLDER_STRUCTURE_RULES.md`](../GOVERNANCE_FOLDER_STRUCTURE_RULES.md) `§2 STRUCTURAL_GENERATION_S3`

Seluruh dokumen, keputusan, desain, dan bukti kualifikasi ARE-3 terorganisir di folder ini.
Mirror struktur `ARE0/`, `ARE1/`, dan `ARE2/` untuk kemudahan arsip & pembelajaran lintas fase (`ARE0` $\rightarrow$ `ARE1` $\rightarrow$ `ARE2` $\rightarrow$ `ARE3`).

---

## Subfolder (Mirror ARE0 / ARE1 / ARE2)

| Folder | Isi (ARE3) | Dokumen Awal yang Terpasang | Status |
|---|---|---|:---:|
| `GRAND_DESIGN/` | Desain menyeluruh ARE-3 (human-readable, non-normatif) | Peta Desain Autonomous Science | `.gitkeep` |
| `AUTHORITY_AND_WORKFLOW/` | Otoritas fase & workflow kerja ARE-3 | Charter ARE-3 (RATIFIED T4), DELEGASI_010, DELEGASI_011 | 3 file |
| `CONTRACTS/` | Kontrak formal & prasyarat ARE-3 | IAQ_LEDGER_ARE3.md, SLICE_1_CONTRACT_ARE3.md, SLICE_2_CONTRACT_ARE3.md | 3 file |
| `MACHINE/` | Sumber mesin kanonikal ARE-3 | Matrix, Inventory, Domain Tags ARE-3 | `.gitkeep` |
| `MANIFEST/` | Manifest normatif ARE-3 | Manifest V41, Manifest Binding V41 | 2 file |
| `COUNCIL_PROTOCOL/` | Protokol dewan audit ARE-3 | Protocol V36+ | `.gitkeep` |
| `QUARANTINE/` | Kebijakan & record karantina legacy (jika ada) | — | `.gitkeep` |
| `R9_CORRECTIONS/` | Koreksi & impact record (jika ada) | — | `.gitkeep` |
| `EXTERNAL_AUDIT/` | Handoff & audit eksternal ARE-3 | — | `.gitkeep` |
| `QUALIFICATION/` | Bukti kualifikasi internal ARE-3 | AHFMES_ARE_3_SLICE1_AUDIT_REPORT.md, AHFMES_ARE_3_SLICE2_AUDIT_REPORT.md | 2 file |
| `DIARY/` | Diary harian ARE-3 (lokal per kategori) | 2026-08-28-ARE3-OPENING-JURNAL.md, template | 2 file |

---

## Titik Baca Cepat (Fase Eksekusi Slice-2, Baseline `@b93b7e9`)

1. **Entry point otoritas:** `../CURRENT_AUTHORITY_INDEX.md` $\rightarrow$ `IMPLEMENTATION(ARE-3) = AUTHORIZED`
2. **Kontrak Slice-1 (CERTIFIED):** `CONTRACTS/SLICE_1_CONTRACT_ARE3.md` (ACC-301..310 PASS)
3. **Kontrak Slice-2 (ACTIVE):** `CONTRACTS/SLICE_2_CONTRACT_ARE3.md` (ACC-311..320 FROZEN)
4. **Charter Otoritas:** `AUTHORITY_AND_WORKFLOW/IMPLEMENTATION_AUTHORITY_CHARTER_ARE3.md` (RATIFIED T4)
5. **Delegasi Aktif:** `AUTHORITY_AND_WORKFLOW/DELEGASI_011_CODING_SLICE2_ARE3.md`
6. **Hutang Arsitektur:** `RESIDUAL_REGISTER.md` (DEBT-04 RESOLVED, DEBT-03 target Slice-2)
7. **Jurnal harian ARE-3:** `DIARY/2026-08-28-ARE3-OPENING-JURNAL.md`
8. **Indeks Progres Global:** `../../PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md`


---

## Prinsip Tata Kelola ARE-3

```text
PERBAIKI YANG BISA   → Refactor bertahap, modular, 100% pytest green, fail-closed
TUNDA YANG HARUS     → DEFERRED justified dicatat di ARCH_DEBT_REGISTER.md & RESIDUAL_REGISTER.md
CATAT BIAR TIDAK LUPA → DIARY harian lokal + GLOBAL DIARY mirror
```

```text
ARE-0 Formal Design       = CLOSED @03aec99
ARE-1 Scientific Kernel   = CLOSED @a6711d6 (172 tests, 136/136 blob)
ARE-2 Experience Intel    = CLOSED @360cf76 (214 tests, Manifest V41)
ARE-3 Autonomous Science  = INITIALIZED / DESIGN & READ-MODE (Implementation NOT Authorized until Charter Ratified)
P001 Substantive Research = NOT AUTHORIZED
PRODUCTION                = CLOSED
LIVE/PAPER TRADING        = NOT AUTHORIZED
```
