# ARE1 — Index Kategori (Scientific Kernel)

Status: **ARSIP FASE ARE-1 / EVIDENCE-CHRONOLOGY / ZERO MACHINE-CLOSURE-AUTHORITY**  
Fase: **ARE-1 Scientific Kernel** — registries, Evidence Ledger, canonical engine, storage CAS  
Aturan struktur & diary: [`../GOVERNANCE_FOLDER_STRUCTURE_RULES.md`](../GOVERNANCE_FOLDER_STRUCTURE_RULES.md) `§2 STRUCTURAL_GENERATION_S2`

Seluruh dokumen, keputusan, dan bukti kualifikasi ARE-1 terorganisir di folder ini.
Mirror `ARE0/` untuk kemudahan arsip & pembelajaran lintas fase (`ARE0`, `ARE1`, `ARE2`, ...).

## Subfolder (mirror ARE0)

| Folder | Isi (ARE1) | Contoh Dokumen Terarsip | Jumlah File |
|---|---|---|---:|
| `GRAND_DESIGN/` | Desain menyeluruh ARE-1 (human-readable, non-normatif) | Grand Design V1 slice ARE-1 | `.gitkeep` |
| `AUTHORITY_AND_WORKFLOW/` | Otoritas fase & workflow kerja ARE-1 | Charter T4 `22c585b`, DELEGASI_001 s/d 004 | 5 |
| `CONTRACTS/` | Kontrak formal & prasyarat ARE-1 | SLICE_1_CONTRACT.md, IAQ_LEDGER.md | 2 |
| `MACHINE/` | Sumber mesin kanonikal ARE-1 | Matrix V30, Register V30, HASH_DOMAIN_TAGS V1 | `.gitkeep` |
| `MANIFEST/` | Manifest normatif ARE-1 | Manifest V39 | `.gitkeep` |
| `COUNCIL_PROTOCOL/` | Protokol dewan audit ARE-1 | Protocol V36 | `.gitkeep` |
| `QUARANTINE/` | Karantina legacy (jika ada) | — | `.gitkeep` |
| `R9_CORRECTIONS/` | Koreksi & impact record (jika ada) | — | `.gitkeep` |
| `EXTERNAL_AUDIT/` | Handoff & audit eksternal ARE-1 | AHFMES_ARE_1_CANDIDATE_HANDOFF.md | 1 |
| `QUALIFICATION/` | Bukti kualifikasi internal ARE-1 | AHFMES_ARE_1_FINAL_CONSISTENCY_V1.md, ARE1_SELF_AUDIT_REPORT.md | 2 |
| `DIARY/` | Diary harian ARE-1 (lokal) | 2026-08-27-ARE1-RESIDUAL-JURNAL.md, template | 2 |


## Titik baca cepat (current generation = 39, code `83f73c0`)

1. Entry point otoritas: `../CURRENT_AUTHORITY_INDEX.md` → `IMPLEMENTATION(ARE-1)=AUTHORIZED`
2. Kontrak slice: `../../ENGINEERING/SLICE_1_CONTRACT.md` (beku `1d567fa`, ACC-1..5)
3. Charter: `../../ENGINEERING/IMPLEMENTATION_AUTHORITY_CHARTER.md` (`22c585b` RATIFIED=YES)
4. Sumber mesin: `MACHINE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V30.md` + `...REGISTER_V30.md`
5. Manifest current: `../ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V39.md` (next: `ARE1/MANIFEST/V40`)
6. Code subject: `83f73c0` (`are/storage.py:86` DENY ALL DROP, `are/canonical.py:255` dual-impl) — `172 tests PASS`
7. Jurnal harian: `DIARY/2026-08-27-ARE1-RESIDUAL-JURNAL.md` + `RESIDUAL_REGISTER.md` (FIX/DEFERRED ledger)
8. Global index: `../../PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md` (mirror `2026-08-27`)

## Prinsip pencatatan ARE-1

```
PERBAIKI YANG BISA  → 1 commit 1 file, file:line, pytest 172, TRIGGER 10, dual 60bc57
TUNDA YANG HARUS    → DEFERRED justified + ticket Slice-2, debt G07/G18 persist
CATAT BIAR TIDAK LUPA → DIARY harian + RESIDUAL_REGISTER.md + GLOBAL DIARY mirror
```

```text
ARE-0 CLOSED              = YES @03aec99 (ROOT 3affbbf0)
ARE-1 Scientific Kernel   = IN PROGRESS — Slice-1 DONE 83f73c0 (HEAD d0d24af)
  FIX RES-01 71e50b6→83f73c0 DONE | DEFERRED IC-5 + RES-03 → Slice-2 | 172/172 PASS
ARE-2 Experience Intel    = LOCKED
ARE-3 Autonomous Science  = LOCKED
ARE-4 Governed Evolution  = LOCKED
IMPLEMENTATION(ARE-1)     = AUTHORIZED (22c585b)
P001 / PRODUCTION          = NOT AUTHORIZED / CLOSED
NEXT                      = Final Consistency → candidate freeze 83f73c0 → binder → external audit
```

## Relasi dengan ARE0

- `ARE0/` = arsip fase 0 (Matrix V1-29, Manifest V1-36, 223 files) — **tidak diubah**
- `ARE1/` = arsip fase 1 — mulai `V39` (HASH_DOMAIN_TAGS), code `are/`, `tests/are/`, `TOOLS/`
- `STRUCTURAL_GENERATION_S2` (2026-08-27) mendeklarasikan pembuatan `ARE1/` — byte-identical untuk file yang direlokasi

Lihat: `../GOVERNANCE_FOLDER_STRUCTURE_RULES.md` Lampiran R3.
