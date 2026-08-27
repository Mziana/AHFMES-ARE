# ARE2 — Index Kategori (Experience Intelligence)

Status: **ARSIP FASE ARE-2 / EVIDENCE-CHRONOLOGY / ZERO MACHINE-CLOSURE-AUTHORITY**  
Fase: **ARE-2 Experience Intelligence** — Experience Store, Anomaly Detection, Replay/What-If, Knowledge Synthesis  
Aturan struktur & diary: [`../GOVERNANCE_FOLDER_STRUCTURE_RULES.md`](../GOVERNANCE_FOLDER_STRUCTURE_RULES.md) `§2 STRUCTURAL_GENERATION_S2`

Seluruh dokumen, keputusan, dan bukti kualifikasi ARE-2 terorganisir di folder ini.
Mirror `ARE0/` dan `ARE1/` untuk kemudahan arsip & pembelajaran lintas fase (`ARE0`, `ARE1`, `ARE2`, ...).

## Subfolder (mirror ARE0/ARE1)

| Folder | Isi (ARE2) | Contoh Dokumen Terarsip | Jumlah File |
|---|---|---|---:|
| `GRAND_DESIGN/` | Desain menyeluruh ARE-2 (human-readable, non-normatif) | Grand Design V1 slice ARE-2 | `.gitkeep` |
| `AUTHORITY_AND_WORKFLOW/` | Otoritas fase & workflow kerja ARE-2 | Charter ARE-2 T4, DELEGASI_005 s/d 009 | 6 |
| `CONTRACTS/` | Kontrak formal & prasyarat ARE-2 | IAQ Ledger ARE-2 (17 QAO), SLICE_1_CONTRACT_ARE2 | 2 |
| `MACHINE/` | Sumber mesin kanonikal ARE-2 | Matrix V30, Register V30, HASH_DOMAIN_TAGS_ARE2 | `.gitkeep` |
| `MANIFEST/` | Manifest normatif ARE-2 | Manifest V41, Manifest Binding V41 | 2 |
| `COUNCIL_PROTOCOL/` | Protokol dewan audit ARE-2 | Protocol V36+ | `.gitkeep` |
| `QUARANTINE/` | Karantina legacy (jika ada) | — | `.gitkeep` |
| `R9_CORRECTIONS/` | Koreksi & impact record (jika ada) | — | `.gitkeep` |
| `EXTERNAL_AUDIT/` | Handoff & audit eksternal ARE-2 | — | `.gitkeep` |
| `QUALIFICATION/` | Bukti kualifikasi internal ARE-2 | AHFMES_ARE_2_FINAL_AUDIT_REPORT.md (20/20 PASS) | 1 |
| `DIARY/` | Diary harian ARE-2 (lokal per kategori) | 2026-08-27-ARE2-EXECUTION-JURNAL.md, template | 2 |

## Titik baca cepat (Fase CLOSED @7f57d12, code `1b2a4fd`, Manifest V41)

1. Entry point otoritas: `../CURRENT_AUTHORITY_INDEX.md` → `ARE-2 CLOSED @360cf76`
2. Kontrak slice: `CONTRACTS/SLICE_1_CONTRACT_ARE2.md`
3. Charter: `AUTHORITY_AND_WORKFLOW/IMPLEMENTATION_AUTHORITY_CHARTER_ARE2.md` (RATIFIED T4)
4. IAQ Ledger: `CONTRACTS/IAQ_LEDGER_ARE2.md` (17 entries, 17/17 ANSWERED)
5. Delegasi: `AUTHORITY_AND_WORKFLOW/DELEGASI_005` s/d `DELEGASI_009`
6. Audit Formal: `QUALIFICATION/AHFMES_ARE_2_FINAL_AUDIT_REPORT.md` (20/20 PASS)
7. Residual Register: `RESIDUAL_REGISTER.md` (IC-5, RES-03, RES-01, ACC-9/18 RESOLVED)
8. Jurnal harian: `DIARY/2026-08-27-ARE2-EXECUTION-JURNAL.md`
9. Global index: `../../PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md`

## Prinsip pencatatan ARE-2

```text
PERBAIKI YANG BISA    → DELEGASI_008 & DELEGASI_009 selesai, 214 tests pass
TUNDA YANG HARUS      → 8 Hutang Arsitektur diwariskan ke ARE-3 via ARCH_DEBT_REGISTER.md
CATAT BIAR TIDAK LUPA → DIARY harian lokal + RESIDUAL_REGISTER.md + GLOBAL DIARY mirror
```

```text
ARE-0 CLOSED              = YES @03aec99 (ROOT 3affbbf0)
ARE-1 Scientific Kernel   = CLOSED @a6711d6 (code 83f73c0, 172 tests, 136/136 blob)
ARE-2 Experience Intel    = CLOSED @7f57d12 (code 1b2a4fd, 214 tests, 344/344 blob, Manifest V41) 🏁
ARE-3 Autonomous Science  = INITIALIZED (DESIGN & READ-MODE ONLY)
IMPLEMENTATION(ARE-3)     = NOT AUTHORIZED (Menunggu Charter T4 ARE-3)
```

## Relasi dengan ARE0 & ARE1

- `ARE0/` = arsip fase 0 (Matrix V1-29, Manifest V1-36, 223 files) — **tidak diubah**
- `ARE1/` = arsip fase 1 (Matrix V30, Manifest V39, code `are/`, `tests/are/`, `TOOLS/`) — **tidak diubah**
- `ARE2/` = arsip fase 2 — mulai `V39` (HASH_DOMAIN_TAGS_ARE2), code `are/` (reuse), `tests/are/`, `TOOLS/`
- `STRUCTURAL_GENERATION_S2` (2026-08-27) mendeklarasikan pembuatan `ARE1/` + `ARE2/` — byte-identical untuk file yang direlokasi

Lihat: `../GOVERNANCE_FOLDER_STRUCTURE_RULES.md` Lampiran R3 (S1) + Lampiran R4 (S2).