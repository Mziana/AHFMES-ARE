# ARE2 — Index Kategori (Experience Intelligence)

Status: **ARSIP FASE ARE-2 / EVIDENCE-CHRONOLOGY / ZERO MACHINE-CLOSURE-AUTHORITY**  
Fase: **ARE-2 Experience Intelligence** — Experience Store, Anomaly Detection, Replay/What-If, Knowledge Synthesis  
Aturan struktur & diary: [`../GOVERNANCE_FOLDER_STRUCTURE_RULES.md`](../GOVERNANCE_FOLDER_STRUCTURE_RULES.md) `§2 STRUCTURAL_GENERATION_S2`

Seluruh dokumen, keputusan, dan bukti kualifikasi ARE-2 terorganisir di folder ini.
Mirror `ARE0/` dan `ARE1/` untuk kemudahan arsip & pembelajaran lintas fase (`ARE0`, `ARE1`, `ARE2`, ...).

## Subfolder (mirror ARE0/ARE1)

| Folder | Isi (ARE2) | Contoh | Jumlah |
|---|---|---|---:|
| `GRAND_DESIGN/` | Desain menyeluruh ARE-2 (human-readable, non-normatif) | Wave Design S1, Grand Design V1 slice ARE-2 | 0 |
| `AUTHORITY_AND_WORKFLOW/` | Otoritas fase & workflow kerja ARE-2 | Implementation Authority Charter ARE-2 T4, Slice-1 Contract | 0 |
| `CONTRACTS/` | Kontrak formal & prasyarat ARE-2 | IAQ Ledger ARE-2, SLICE_1_CONTRACT_ARE2, HASH_DOMAIN_TAGS_ARE2 | 0 |
| `MACHINE/` | Sumber mesin kanonikal ARE-2 | Matrix V30, Register V30, HASH_DOMAIN_TAGS_ARE2 | 0 |
| `MANIFEST/` | Manifest normatif ARE-2 | Manifest V40+ (next), Manifest V39 (warisan) | 0 |
| `COUNCIL_PROTOCOL/` | Protokol dewan audit ARE-2 | Protocol V36+ (reuse dari ARE-0/1) | 0 |
| `QUARANTINE/` | Karantina legacy (jika ada) | — | 0 |
| `R9_CORRECTIONS/` | Koreksi & impact record (jika ada) | — | 0 |
| `EXTERNAL_AUDIT/` | Handoff & audit eksternal ARE-2 | — (akan: candidate binder external audit) | 0 |
| `QUALIFICATION/` | Bukti kualifikasi internal ARE-2 | SA-11, Impact, CP1/CP2, Regresi, Final Consistency | 0 |
| `DIARY/` | Diary harian ARE-2 (lokal) | IAQ ledger creation, triase, slice contract, charter | 0 |

## Titik baca cepat (current generation = 39, code `83f73c0`, binder `697b53a`)

1. Entry point otoritas: `../CURRENT_AUTHORITY_INDEX.md` → `IMPLEMENTATION(ARE-2) = NOT AUTHORIZED`
2. Kontrak slice: `../../ENGINEERING/SLICE_1_CONTRACT_ARE2.md` (beku T3, frozen T3)
3. Charter: `../../ENGINEERING/IMPLEMENTATION_AUTHORITY_CHARTER_ARE2.md` (draft, menunggu T4)
3. IAQ Ledger: `../../ENGINEERING/IAQ_LEDGER_ARE2.md` (17 entries, triase DONE)
4. Residual Register: `../ARE1/RESIDUAL_REGISTER.md` (FIX/DEFERRED ledger ARE-1)
5. Sumber mesin: `../ARE0/MACHINE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V30.md` + `..._REGISTER_V30.md`
6. Manifest current: `../ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V39.md` (next: `ARE2/MANIFEST/V40`)
7. Code subject: `83f73c0` (`are/storage.py:86` DENY ALL DROP, `are/canonical.py:255` dual-impl) → `172 tests PASS`
8. Jurnal harian: `DIARY/2026-08-27-ARE1-RESIDUAL-JURNAL.md` + `RESIDUAL_REGISTER.md` (FIX/DEFERRED ledger)
9. Global index: `../../PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md` (mirror `2026-08-27`)

## Prinsip pencatatan ARE-2

```
PERBAIKI YANG BISA  → 1 commit 1 file, file:line, pytest 172, TRIGGER 10, dual 60bc57
TUNDA YANG HARUS    → DEFERRED justified + ticket Slice-2, debt G07/G18 persist
CATAT BIAR TIDAK LUPA → DIARY harian + RESIDUAL_REGISTER.md + GLOBAL DIARY mirror
```

```text
ARE-0 CLOSED              = YES @03aec99 (ROOT 3affbbf0)
ARE-1 Scientific Kernel   = CLOSED @a6711d6 (code 83f73c0, 172 tests, 136/136 blob, 41 tags)
ARE-2 Experience Intel    = DESAIN / READ-MODE (DELEGASI_005 issued, IAQ_LEDGER_ARE2.md 17 entries)
ARE-3 Autonomous Science  = LOCKED
ARE-4 Governed Evolution  = LOCKED
IMPLEMENTATION(ARE-2)     = NOT AUTHORIZED (menunggu charter T4)
P001                      = NOT AUTHORIZED
PRODUCTION                = CLOSED
LIVE/PAPER TRADING        = NOT AUTHORIZED
NEXT                      = IAQ triase → SLICE_1_CONTRACT frozen → Charter T4 → DELEGASI_006 coding
```

## Relasi dengan ARE0 & ARE1

- `ARE0/` = arsip fase 0 (Matrix V1-29, Manifest V1-36, 223 files) — **tidak diubah**
- `ARE1/` = arsip fase 1 (Matrix V30, Manifest V39, code `are/`, `tests/are/`, `TOOLS/`) — **tidak diubah**
- `ARE2/` = arsip fase 2 — mulai `V39` (HASH_DOMAIN_TAGS_ARE2), code `are/` (reuse), `tests/are/`, `TOOLS/`
- `STRUCTURAL_GENERATION_S2` (2026-08-27) mendeklarasikan pembuatan `ARE1/` + `ARE2/` — byte-identical untuk file yang direlokasi

Lihat: `../GOVERNANCE_FOLDER_STRUCTURE_RULES.md` Lampiran R3 (S1) + Lampiran R4 (S2).