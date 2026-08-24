# Cakupan ekstraksi ARE

## Yang dibawa

Tepat 228 file yang dipertahankan byte-identical dari commit sumber
`dcecafd1f9caae130da3880170f018026b1d5183`:

- 215 dokumen `PROJECT_GOVERNANCE/AHFMES_ARE*`;
- 4 dokumen legacy `AHFMES_AUTONOMOUS_RESEARCH_ENGINE*`;
- `PROJECT_GOVERNANCE/CURRENT_AUTHORITY_INDEX.md`;
- 8 catatan jurnal khusus ARE.

## Yang sengaja tidak dibawa

- Seluruh implementasi, data, dan bukti hasil Condition Atlas serta Position
  Path Replay.
- Kode production/runtime, test, dashboard, folder riset, dan agent memory.
- `PROJECT_JOURNAL/DIARY/2026-08-20-PPR-G1-CLOSURE-AND-ARE-DIRECTION.md`, karena
  mencampur konten PPR dan ARE.
- `PROJECT_JOURNAL/STATUS/CURRENT_RESEARCH_STATUS_2026-08-20.md`, karena
  mencampur status Atlas, PPR, dan ARE.

Satu dokumen ARE historis yang dipertahankan menyitir artefak PPR sebagai asal
masalah P001. Itu bukan dependency aktif dan artefaknya tidak ikut diimpor.
