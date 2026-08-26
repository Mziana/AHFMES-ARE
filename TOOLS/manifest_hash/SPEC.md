# SPEC — manifest_hash

```text
STATUS   = TOOL CONTRACT / ZERO AUTHORITY / DUAL-IMPLEMENTATION REQUIRED
DIBUAT   = 2026-08-26
```

## Tujuan

Menghitung **normative root** sebuah Manifest Normatif secara deterministik:
SHA-256 atas daftar tuple anggota terurut, sesuai spesifikasi kanonikal
(`AHFMES_CANONICAL_OBJECT_V1` + skema root Manifest V35):

```text
root = SHA-256( concat( "<path>\0<blob-sha>\0<byte-length>\n" untuk setiap
                        anggota, terurut leksikografis by path ) )
```

## Input

```text
--manifest <file>     file manifest berisi closed exact path set + blob SHA + bytes
--worktree <dir>      root working tree repositori (opsional; bila diberikan,
                      tuple diverifikasi ulang dari disk sebelum hashing)
```

## Output

```text
stdout : root hex (lowercase, 64 char) + jumlah member + status baris
exit 0 = sukses; exit 2 = input tidak valid; exit 3 = mismatch verifikasi
         (fail-closed: missing/malformed member TIDAK pernah di-hash diam-diam)
```

## Aturan keras

1. Encoding UTF-8 tanpa BOM; newline literal `\n`; pemisah `\0` eksak.
2. Urutan tuple: leksikografis byte-wise atas path. Tanpa normalisasi path
   lain (tanpa lowercase, tanpa resolve symlink).
3. Missing/malformed/mismatch -> FAIL keseluruhan (fail-closed), tanpa
   prefix repair, tanpa fallback historis.
4. Deterministik: tree sama + input sama -> output sama persis.

## Kriteria terima

- [ ] `IMPL_A` dan `IMPL_B` menghasilkan root identik pada seluruh anggota
      Manifest V35 yang ada di repo.
- [ ] Uji negatif: satu byte diubah pada salah satu file worktree -> exit 3.
- [ ] Uji negatif: satu anggota hilang dari worktree -> exit 3.
- [ ] Tidak ada dependency di luar stdlib.
