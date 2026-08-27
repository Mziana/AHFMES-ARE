# TOOLS — Alat Verifikasi Zero-Authority

```text
STATUS   = VERIFICATION TOOLING / ZERO MACHINE-CLOSURE-AUDIT-RULE AUTHORITY
DIBUAT   = 2026-08-26 (usulan auditor, lihat AUDIT_INPUT/)
LINGKUP  = alat bantu verifikasi mekanis untuk kualifikasi manifest/blob/path
BUKAN    = implementasi runtime, bukan bagian Manifest, bukan otoritas apa pun
```

## Prinsip

1. Alat di folder ini **tidak pernah menjadi otoritas**. Output-nya adalah
   evidence/chronology untuk dinilai proses kualifikasi — sama seperti diary.
2. Alat **boleh dibangun kapan saja** (termasuk pra-S0) karena bukan
   implementasi runtime yang dikunci firewall. Ia malah WAJIB ada lebih
   awal sebagai *design spike*: memvalidasi spesifikasi kanonikalisaasi
   secara empiris sebelum freeze.
3. Setiap alat diimplementasikan **dua kali secara independen**
   (`IMPL_A/`, `IMPL_B/`). Hasil kedua implementasi atas tree yang sama
   wajib identik bit-per-bit. Beda hasil = bug spesifikasi, bukan bug kode.
4. Python stdlib saja (`hashlib`, `os`, `json`, `argparse`). Tanpa
   dependency pihak ketiga kecuali dijustifikasi tertulis di SPEC.
5. Alat tidak pernah dirujuk dokumen normatif sebagai sumber otoritas.
6. Versi alat mengikuti Git (commit SHA), bukan `_v2/_final/_backup`.

## Struktur

```text
TOOLS/
├── README.md              (file ini)
├── manifest_hash/
│   └── SPEC.md            kontrak alat + kriteria terima
├── blob_verifier/
│   └── SPEC.md
└── path_router/
    └── SPEC.md
```

Saat dieksekusi, tiap alat diisi:

```text
<alat>/
├── SPEC.md
├── IMPL_A/<alat>_a.py     implementasi independen A
└── IMPL_B/<alat>_b.py     implementasi independen B
```

## Alat prioritas gelombang V36

| Alat | Fungsi | Melayani |
|---|---|---|
| `manifest_hash` | hitung normative root: SHA-256 atas tuple kanonikal terurut | F2 verifikasi dua metode |
| `blob_verifier` | cocokkan Git blob SHA + byte length anggota manifest vs worktree | X302, F2 |
| `path_router` | terapkan tabel routing R1 (old-path → new-path), buktikan blob identik | F1 transform manifest |

## Status eksekusi

```text
MANIFEST_HASH = TERSEDIA (IMPL_A, IMPL_B) — LULUS UJI DUAL-IMPL
BLOB_VERIFIER = TERSEDIA (IMPL_A, IMPL_B) — LULUS UJI DUAL-IMPL
PATH_ROUTER   = TERSEDIA (IMPL_A, IMPL_B) — LULUS UJI DUAL-IMPL
```
