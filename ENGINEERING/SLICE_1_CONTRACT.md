# SLICE-1 CONTRACT — Storage Engine + Canonical Bytes (ARE-1)

Status: **FROZEN T3 / LEAD ARCHITECT / prasyarat & kriteria terima mengikat**  
Dibekukan: 2026-08-26 · Baseline: lineage gen-38 → T2 commit `4917631`  
Penerima delegasi: Engineering AI (via DELEGASI bernomor berikutnya)

## 0. Prasyarat mutlak

```text
P-1 GEN-39 TERMINT sebelum Bagian B dieksekusi/diterima, membawa SEKALIGUS:
    (a) lampiran AHFMES_ARE_HASH_DOMAIN_TAGS — SUPERSET-TERTUTUP:
        memuat 9 tag 0B V3 §11 VERBATIM (makna string tidak berubah),
        + tag untuk SEMUA tipe objek Register V30,
        + aturan penutupan: "tipe objek tanpa tag terdaftar =>
          operasi hashing DENY fail-closed" sampai lampiran diamendemen
          lewat generasi baru;                                   [syarat S1]
    (b) registrasi ENGINEERING/IAQ_LEDGER.md sebagai QAO record pembuka
        ARE-1.                                                  [syarat S2]
P-2 Baseline kerja = HEAD main saat mulus; tanpa branch baru.
```

## 1. Lingkup Bagian A — Storage Engine

```text
A1  Event store append-only di SQLite (WAL):
    tabel events append-only; tabel head satu baris/stream;
    mutasi head HANYA via CAS WHERE last_revision=?;
    UPDATE/DELETE pada events DIBLOKIR di lapisan akses.
A2  Crash-matrix invariant test wajib:
    simulasi crash di setiap titik antara dua write => state selalu
    direkonstruksi dari committed rows saja (menyatu IAQ-006 / IC-4).
A3  Finalize idempoten IC-4: predikat deterministik f(ledger row,
    receipt presence); tanpa jam; tanpa fakta eksternal.
```

## 2. Lingkup Bagian B — Canonical Bytes Verifier + Domain Hasher

```text
B1  Verifier kanonikal byte FAIL-CLOSED:
    non-NFC / BOM / CRLF => REJECT dengan offset byte;
    identitas SELALU dihitung atas byte[], bukan string.
B2  Uji adversarial wajib: combining character, locale tr-TR,
    CRLF injection, key urutan terbalik.
B3  Domain hasher: WAJIB menunggu P-1(a);
    setiap tipe objek memakai tag dari lampiran; tipe tanpa tag => DENY;
    dual-implementation wajib untuk hasher ini.
```

## 3. Kriteria terima (fail-closed, semuanya wajib)

```text
ACC-1 seluruh test A1–A3 lulus termasuk crash-matrix penuh
ACC-2 seluruh test B1–B2 lulus pada kedua implementasi (dual)
ACC-3 bukti P-1 terpenuhi: blob lampiran tag + QAO IAQ tercantum
      di Manifest V39 (member), diverifikasi via git objects
ACC-4 zero dependency baru tanpa justifikasi tertulis (RULES E-05)
ACC-5 vocabulary E-01..E-10 dipatuhi; tanpa kosakata status resolutif
```

## 4. Di luar lingkup keras

Broker/order apa pun · strategi trading · riset substantif P001 · produksi ·
edit dokumen normatif beku · modul ARE-2+ · file di luar `are/` dan `tests/are/`
kecuali yang diperintahkan delegasi.

## 5. Proses

GitHub-first: slice kecil → commit → remote source audit arsitek → koreksi →
freeze exact SHA → pull lokal → test Antigravity → evidence publish balik
(workflow beku Bab 27 Grand Design). Local checkout = replica test.
