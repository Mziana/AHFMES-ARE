# ARE3 — Index Kategori (Autonomous Science & Direction Intelligence)

Status: **ARSIP FASE ARE-3 / EVIDENCE-CHRONOLOGY / INITIALIZATION / ZERO IMPLEMENTATION AUTHORITY**  
Fase: **ARE-3 Autonomous Science** — Direction Discovery, Habitat Integration, Telemetry Aggregation, Micro-Execution Boundaries  
Aturan struktur & diary: [`../GOVERNANCE_FOLDER_STRUCTURE_RULES.md`](../GOVERNANCE_FOLDER_STRUCTURE_RULES.md) `§2 STRUCTURAL_GENERATION_S3`

Seluruh dokumen, keputusan, desain, dan bukti kualifikasi ARE-3 terorganisir di folder ini.
Mirror struktur `ARE0/`, `ARE1/`, dan `ARE2/` untuk kemudahan arsip & pembelajaran lintas fase (`ARE0` $\rightarrow$ `ARE1` $\rightarrow$ `ARE2` $\rightarrow$ `ARE3`).

---

## Subfolder (Mirror ARE0 / ARE1 / ARE2)

| Folder | Isi (ARE3) | Status |
|---|---|:---:|
| `GRAND_DESIGN/` | Desain menyeluruh ARE-3 (human-readable, non-normatif) | Initialized |
| `AUTHORITY_AND_WORKFLOW/` | Otoritas fase & workflow kerja ARE-3 (Charter, Workflow) | Initialized |
| `CONTRACTS/` | Kontrak formal & prasyarat ARE-3 (Slice Contracts, IAQ, Tags) | Initialized |
| `MACHINE/` | Sumber mesin kanonikal ARE-3 (Matrix, Inventory, Domain Tags) | Initialized |
| `MANIFEST/` | Manifest normatif ARE-3 (Manifest V41+) | Initialized |
| `COUNCIL_PROTOCOL/` | Protokol dewan audit ARE-3 | Initialized |
| `QUARANTINE/` | Kebijakan & record karantina legacy (jika ada) | Initialized |
| `R9_CORRECTIONS/` | Koreksi & impact record (jika ada) | Initialized |
| `EXTERNAL_AUDIT/` | Handoff & audit eksternal ARE-3 | Initialized |
| `QUALIFICATION/` | Bukti kualifikasi internal ARE-3 (clean pass, regresi) | Initialized |
| `DIARY/` | Diary harian ARE-3 (lokal per kategori) | Active |

---

## Titik Baca Cepat (Opening Generation = 41, Baseline `360cf76`)

1. **Entry point otoritas:** `../CURRENT_AUTHORITY_INDEX.md` $\rightarrow$ `ARE-2 CLOSED @360cf76`, `ARE-3 INITIALIZED (DESIGN/READ-MODE)`
2. **Hutang Arsitektur Terbawa:** `../../ENGINEERING/ARCH_DEBT_REGISTER.md` (DEBT-01..08 diwariskan ke ARE-3)
3. **Kontrak ARE-2 Sebelumnya:** `../../ENGINEERING/SLICE_1_CONTRACT_ARE2.md` (FULL PASS @1b2a4fd)
4. **Jurnal harian ARE-3:** `DIARY/2026-08-28-ARE3-OPENING-JURNAL.md`
5. **Indeks Progres Global:** `../../PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md`

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
