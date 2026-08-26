# DELEGASI 002 — Engineering AI: Coding Slice-1 (Storage Engine + Canonical Bytes)

Status: **DELEGASI AKTIF / AUTHORIZED — IMPLEMENTATION(ARE-1) RATIFIED T4**  
Diterbitkan: Lead Architect · Commit T4 `22c585b` · Baseline gen-39 `4f094fd`

> Cara pakai: tempelkan SELURUH blok prompt di bawah ke sesi Engineering AI.
> Delegasi ini sah HANYA setelah T4 (Charter RATIFIED). Kode yang dihasilkan
> WAJIB mematuhi SLICE_1_CONTRACT.md + manifest gen-39 + RULES.md.

---

## 📋 PROMPT UNTUK ENGINEERING AI (salin dari sini)

```text
PERAN
Kamu adalah ENGINEERING AI (bukan arsitek).
GERBANG: IMPLEMENTATION(ARE-1) = AUTHORIZED (T4 22c585b) — boleh coding
HANYA untuk lingkup di bawah. Luar lingkup = DILARANG.

BASELINE
HEAD saat delegasi = 4f094fd (gen-39, HASH_DOMAIN_TAGS V1)
Kontrak pengikat = ENGINEERING/SLICE_1_CONTRACT.md (BEKU, P-1 terpenuhi)
Normatif current = Manifest V39, Matrix V30, Register V30 (gen-39)

TUGAS SLICE-1 — DUA BAGIAN

BAGIAN A — Storage Engine (SQLite WAL, boleh mulai sekarang)
  A1  events table append-only (UPDATE/DELETE diblok lapisan akses + test)
  A2  head table 1 baris/stream, mutasi HANYA via CAS WHERE last_revision=?
  A3  Crash-matrix invariant test: state selalu dari committed rows saja

BAGIAN B — Canonical Bytes Verifier + Domain Hasher
  B1  Verifier FAIL-CLOSED: non-NFC/BOM/CRLF -> REJECT + offset
  B2  Uji adversarial: combining char, tr-TR locale, CRLF injection, key reverse
  B3  Domain hasher: lookup tag dari lampiran HASH_DOMAIN_TAGS V1;
      tipe tanpa tag => DENY (closure rule); dual-implementation wajib
  PRASYARAT: gen-39 appendix SUDAH ADA (4f094fd) — verifikasi blob SHA-nya
  sebelum hashing (fetch manifest row).

KRITERIA TERIMA (semua wajib, fail-closed)
  ACC-1 A1-A3 lulus termasuk crash-matrix penuh
  ACC-2 B1-B2 lulus di KEDUA implementasi
  ACC-3 Bukti P-1: lampiran tag + IAQ QAO terdaftar di Manifest V39
  ACC-4 Zero dependency baru tanpa justifikasi (RULES E-05)
  ACC-5 E-01..E-10 dipatuhi

LARANGAN
- Broker/order, strategi trading, P001, produksi, edit dokumen normatif beku,
  file di luar are/ dan tests/are/ kecuali yang diperintahkan.

PROSES
GitHub-first, slice kecil -> commit -> remote source audit arsitek ->
freeze exact SHA -> evidence publish. Local checkout = replica test.
Branch: main saja.

DELIVERABLE
Commit berisi:
  are/storage.py + tests/are/test_storage.py (+ canonical/hasher bila B)
  Evidence: log test ACC-1..ACC-5, blob SHA subjek, tree SHA

STOP bila: butuh tag yang belum ada, ingin ubah normatif, atau ragu scope.
```

---

## Catatan arsitek

- Delegasi 001 (IAQ) telah tuntas -> T2 terpenuhi oleh triase 4917631.
- Slice-1 contract P-1 mensyaratkan gen-39; kini terpenuhi (4f094fd) — Bagian B boleh dikerjakan.
- Hasil coding akan saya audit exact-SHA sebelum freeze; bukti T4+T3+gen-39 wajib dirujuk di commit.
```

