# AHFMES-ARE

Repositori terpisah untuk arsitektur dan tata kelola **AHFMES Autonomous
Research Engine (ARE)**.

## Batas migrasi

Repositori ini merupakan ekstraksi byte-identical dokumen ARE dari
`Mziana/AHFMES-CHATGPT` pada commit sumber
`dcecafd1f9caae130da3880170f018026b1d5183`.

Condition Atlas, Position Path Replay, data riset, kode production/runtime,
test, artefak hasil, serta dokumen status campuran sengaja tidak dibawa ke
sini. Rujukan historis terhadap sistem tersebut yang masih ada di dokumen ARE
hanya merupakan sitasi sejarah; artefak sumbernya tidak ada di repositori ini.

## Aturan branch — keras

- Repositori ini hanya memakai branch `main`.
- **Dilarang membuat branch baru**, worktree baru, branch per-AI, branch audit,
  branch perbaikan, maupun branch handoff.
- Pengecualian hanya boleh terjadi atas instruksi eksplisit pemilik proyek.

## Status keselamatan saat ini

Migrasi ini **tidak** memindahkan authority untuk menjalankan apa pun.

- Penutupan desain ARE-0: **SELESAI @03aec99**
- Penutupan desain ARE-1: **SELESAI @a6711d6** (code 83f73c0, binder 697b53a, ACCEPT_ARE1_SCIENTIFIC_KERNEL_CLOSED)
- Kesiapan external audit: **SELESAI** (ARE-1 ACCEPT_ARE1_SCIENTIFIC_KERNEL_CLOSED)
- Implementasi ARE-1: **SELESAI** (code 83f73c0, 172 tests, 136/136 blob, 41 tags)
- Implementasi ARE-2: **AUTHORIZED** (Charter T4 ratified 2026-08-27, DELEGASI_005 issued, IAQ_LEDGER_ARE2.md 17 entries)
- Riset substantif / P001: **TIDAK DIIZINKAN**
- Production, paper trading, atau live trading: **DITUTUP**

Mulailah dari
[`PROJECT_GOVERNANCE/CURRENT_AUTHORITY_INDEX.md`](PROJECT_GOVERNANCE/CURRENT_AUTHORITY_INDEX.md).
Identitas commit di repositori sumber tetap merupakan bukti provenance
historis, bukan identitas kandidat audit baru untuk repositori ini.
