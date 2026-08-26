# SPEC — path_router

```text
STATUS   = TOOL CONTRACT / ZERO AUTHORITY / DUAL-IMPLEMENTATION REQUIRED
DIBUAT   = 2026-08-26
```

## Tujuan

Menerapkan tabel routing STRUCTURAL_GENERATION_S1 (Lampiran R1
`GOVERNANCE_FOLDER_STRUCTURE_RULES.md`) secara mekanis: memetakan
old-path → new-path untuk transform manifest generasi berikutnya, dan
membuktikan relokasi **byte-identical** (blob tidak berubah).

## Input

```text
--source-manifest <file>    manifest lama (old-path)
--routing-table <file>      tabel pattern → folder tujuan (ekspor R1)
--worktree <dir>            root working tree struktur baru
--out <file>                tujuan laporan relokasi (JSON)
```

## Output

Laporan JSON per anggota:

```json
{
  "old_path": "...",
  "new_path": "...",
  "matched_pattern": "AHFMES_ARE_0[A-F]_*",
  "old_blob_sha": "...",
  "new_blob_sha": "...",
  "byte_length_equal": true,
  "status": "RELOCATED_IDENTICAL | UNMATCHED | MISSING | MUTATED"
}
```

`exit 0` hanya jika seluruh anggota `RELOCATED_IDENTICAL`.

## Aturan keras

1. Satu old-path dipetakan tepat satu new-path. Pattern ganda yang cocok =
   error konfigurasi (fail-closed), bukan pilihan pertama.
2. Old-path tanpa pattern cocok -> `UNMATCHED` -> exit 3 (tidak ada
   fallback heuristik).
3. `MUTATED` (blob SHA beda) -> exit 4. Relokasi S1 menjanjikan byte-identical;
   pelanggarannya harus terlihat, tidak pernah diam.
4. Alat TIDAK menulis/mengubah file manapun — read-only + laporan.

## Kriteria terima

- [ ] Seluruh anggota manifest V35 direkonstruksi ke layout ARE0/* dengan
      status RELOCATED_IDENTICAL.
- [ ] Uji negatif: pattern tabel dibuat ambigu -> exit 3 dengan pesan jelas.
- [ ] Uji negatif: satu file target dimutasi -> status MUTATED, exit 4.
- [ ] IMPL_A ≡ IMPL_B pada dataset uji yang sama; stdlib only.
