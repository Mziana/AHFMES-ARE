# AUDITOR ADVISORY — TUGAS DESAIN UNTUK LEAD ARCHITECT (GELOMBANG V36)

```text
STATUS   = AUDIT INPUT / NON-NORMATIF / ZERO AUTHORITY
TANGGAL  = 2026-08-26
ASAL     = Sesi review audit independen atas repositori ini (pra-audit formal)
PENERIMA = LEAD ARCHITECT, gelombang kualifikasi V36
```

## 0. Cara memakai dokumen ini

1. Dokumen ini **bukan koreksi wajib**. Sesuai preseden Pass 1–3: temuan auditor
   adalah **input adversarial** yang wajib difilter, direproduksi, lalu
   di-merge root-cause. Arsitek berwenang menolak butir dengan justifikasi.
2. Setiap butir adalah **tugas desain** (bukan teks normatif jadi). Arsitek
   yang memutuskan bentuk formalnya (amendemen protokol, dokumen baru, atau
   penolakan terdokumentasi).
3. Butir **D2 (Definition of Done) SENGAJA TIDAK ADA** di dokumen ini —
   disiapkan langsung oleh pemilik proyek, di luar lingkup arsitek.

---

## D1 — Ekonomi reset kualifikasi berbasis severitas

### Masalah yang diamati

```text
V35 = PRE_S0, tidak pernah dimulai, langsung digantikan V36.
Aturan kini  : setiap blocker baru -> CLEAN_PASS_COUNT = 0 (blunt).
Akibat empiris: kredit kualifikasi berulang kali terbakar oleh temuan
                yang tidak semuanya setara bobotnya; gelombang sulit konvergen.
```

### Usulan desain

Ganti satu aturan blunt dengan tiga kelas temuan:

```text
KELAS A — konstitusional (THINK->ACT, bypass safety, otoritas palsu)
          -> CLEAN_PASS_COUNT = 0 (reset penuh, seperti aturan kini)

KELAS B — semantik lokal (bug logika gate, invarian bocor, field salah)
          -> rerun HANYA auditor yang terdampak + skenario regresi terkait;
             clean pass pada area lain dipertahankan

KELAS C — struktural/editorial (path, typo, format, konsolidasi)
          -> catat di ledger; TIDAK menyentuh kredit apa pun
```

Ditambah prinsip pengikat kredit:

```text
Kredit kualifikasi terikat pada NORMATIVE ROOT HASH, bukan nomor gelombang.
Root tidak berubah -> pass yang sudah sah tetap sah lintas gelombang.
```

### Syarat verifikasi bila diadopsi

- Definisi operasional tiap kelas harus fail-closed (ambigu -> naik kelas).
- Regresi permanen ditambah skenario uji klasifikasi severitas.
- Preseden historis (EXT2-081-01, EA1-V25-01 dst.) dipetakan ke kelas
  sebagai testcase klasifikasi.

---

## D2 — (KOSONG SENGAJA) Definition of Done

Butir ini disiapkan langsung oleh **pemilik proyek** untuk tahap
perencanaan engineering dan berada di luar mandat Lead Architect.
Jangan didesain, jangan digantikan.

---

## D3 — Aturan anti-loop patching

### Masalah yang diamati

```text
R9 Correction Package mencapai V34 dalam satu keluarga dokumen.
Pola "patch atas patch" pada area normatif yang sama adalah sinyal
desainnya sendiri yang terus retak, bukan kurangnya patch.
```

### Usulan desain

```text
Jika satu area normatif membutuhkan koreksi ke-N dengan N > 3
dalam satu gelombang:
  -> WAJIB review penyederhanaan desain (simplification review)
  -> patch ke-N+1 DILARANG diterbitkan sebelum review tersebut
     menghasilkan salah satu dari:
     (a) keputusan eksplisit "pertahankan, patch lagi", atau
     (b) revisi penyederhanaan yang menghapus akar masalah.
Kompleksitas adalah biaya. Mekanisme yang berulang kali retak
dihapus/disederhanakan, bukan ditambal lagi.
```

Catatan: counter N dihitung per keluarga dokumen per gelombang,
append-only, non-authoritative (mengikuti pola debt vector yang ada).

---

## D4 — Implementability audit pra-freeze eksternal

### Masalah yang diamati

Desain ditulis arsitektur tunggal (+AI). Spesifikasi dari penulis tunggal
sering membawa ambiguitas yang hanya muncul saat pihak lain mencoba
membangunnya — ketahuan pada sprint coding = termahal.

### Usulan desain

Satu pass audit baru pada urutan kualifikasi, posisi: setelah clean pass
pertama, SEBELUM handoff audit eksternal:

```text
Pelaksana : peran ENGINEER NAIF (independen dari arsitek; boleh agent
            dengan prompt peran engineer yang belum tahu rationale).
Input     : Grand Design konsolidasi + Matrix current + kontrak 0A-0F.
Tugas     : tandai SETIAP kalimat yang tidak bisa diterjemahkan langsung
            menjadi modul / test / field / transisi state.
Output    : daftar pertanyaan bernomor (IAQ-xx) — bukan keputusan.
Penutupan : setiap IAQ dijawab arsitek; jawaban yang mengubah semantik
            masuk jalur koreksi normal; jawaban klarifikasi saja dicatat.
```

Hasil audit ini murah sekarang, mahal kemudian. Skenario regresi baru:
"IAQ yang sudah dijawab tidak boleh muncul lagi di gelombang berikutnya."

---

## D5 — Pre-commit Implementation Authority Charter

### Masalah yang diamati

Firewall saat ini hanya MENAHAN otoritas (`IMPLEMENTATION = NOT AUTHORIZED`)
tanpa mendefinisikan **kapan dan oleh siapa** otoritas itu diberikan.
Gerbang akhir yang kabur adalah akar pola tidak-konvergen: tidak ada
kondisi "menang" yang bisa dipenuhi secara objektif.

### Usulan desain

Satu dokumen singkat, diterbitkan pemilik proyek, berisi minimal:

```text
NAMA      : IMPLEMENTATION_AUTHORITY_CHARTER
PEMICU    : kondisi obyektif yang bisa diverifikasi mesin
            (rujukan ke status kualifikasi, bukan penilaian subjektif)
PEMBERI   : pemilik proyek — eksplisit, tertulis, commit khusus
CAKUPAN   : ARE-1 Scientific Kernel SAJA; fase berturut-butur butuh
            charter sendiri (urutan roadmap tidak boleh dibalik)
LARANGAN  : charter tidak bisa lahir dari dokumen lain; diary, LLM,
            hasil council/audit TIDAK berwenang menerbitkannya
            (konsisten QAO/JQO)
PEMBATALAN: syarat revoke eksplisit + apa yang terjadi pada artefak
            yang sudah lahir saat charter dicabut
```

Efek utama: sistem berhenti menjadi gerbang tak berujung dan menjadi
gerbang BERKONDISI — semua pihak tahu persis apa yang membuat pintu terbuka.

---

## USULAN STRUKTUR FOLDER BARU (tingkat root repo)

Di luar jurisdiksi `PROJECT_GOVERNANCE/` (tidak menyentuh manifest, tidak
ada byte normatif berubah), mengikuti preseden folder pendukung root
(`GRAND DESIGN/`, `PROJECT_JOURNAL/`):

```text
AHFMES-ARE/
├── AUDIT_INPUT/            masukan auditor eksternal (folder ini)
├── TOOLS/                  alat verifikasi ZERO-AUTHORITY (.py)
│   ├── README.md           aturan umum + batasan otoritas
│   ├── manifest_hash/SPEC.md
│   ├── blob_verifier/SPEC.md
│   └── path_router/SPEC.md
└── IMPLEMENTATION/
    └── README.md           KOSONG & TERKUNCI sampai charter (D5) aktif
```

Rationale: alat verifikasi (skrip mekanis F2) adalah kode, tapi bukan
implementasi runtime. Memisahkannya secara fisik mencegah kontaminasi
vocabulary "IMPLEMENTATION" sekaligus memberi spike desain empiris
sebelum freeze.

---

## Firewall (tidak berubah oleh dokumen ini)

```text
ARE-0 CLOSED = NO | IMPLEMENTATION = NOT AUTHORIZED | P001 = NOT AUTHORIZED
PRODUCTION = CLOSED | LIVE/PAPER TRADING = NOT AUTHORIZED
```

*Dokumen advisory ini memiliki nol otoritas machine/closure/audit-rule.
Kepemilikan keputusan sepenuhnya pada Lead Architect dan pemilik proyek.*
