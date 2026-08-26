# SPEC — blob_verifier

```text
STATUS   = TOOL CONTRACT / ZERO AUTHORITY / DUAL-IMPLEMENTATION REQUIRED
DIBUAT   = 2026-08-26
```

## Tujuan

Memverifikasi bahwa setiap anggota manifest benar-benar ada di working tree
dengan identitas konten eksak: Git blob SHA-1 dan byte length harus cocok
tuple `<path>\0<blob-sha>\0<bytes>` pada manifest.

## Input

```text
--manifest <file>     manifest sumber tuple anggota
--worktree <dir>      root working tree
--git-dir <dir>       opsional; bila diberikan, blob SHA dibaca via git;
                      default: hitung SHA-1 blob langsung dari bytes file
                      ("blob <len>\0<content>")
```

## Output

```text
stdout : tabel per anggota: PATH | EXPECTED_SHA | ACTUAL_SHA | BYTES | OK/FAIL
         + ringkasan TOTAL / PASS / FAIL
exit 0 = semua PASS; exit 3 = minimal satu FAIL atau manifest tak terbaca
```

## Aturan keras

1. Fail-closed: file hilang, unreadable, ukuran beda, atau SHA beda = FAIL.
2. Byte length diverifikasi dari disk, bukan dari klaim manifest saja.
3. Blob SHA-1 dihitung dengan header objek Git (`blob <n>\0`) agar bisa
   disilangkan dengan `git ls-tree`.
4. Laporan ditulis utuh sebelum exit non-zero (tidak berhenti di FAIL pertama).
5. Deterministik; urutan output mengikuti urutan leksikografis path.

## Kriteria terima

- [ ] Seluruh anggota manifest V35 di repo ini = PASS saat repo bersih
      (`git status` kosong pada path terkait).
- [ ] Uji negatif: ubah 1 byte file anggota -> FAIL terdeteksi tepat di
      baris itu, lainnya tetap dilaporkan.
- [ ] Hasil IMPL_A == hasil IMPL_B pada tree yang sama, bit-per-bit.
- [ ] Stdlib only.
