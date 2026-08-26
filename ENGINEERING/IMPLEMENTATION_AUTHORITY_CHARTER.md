# IMPLEMENTATION AUTHORITY CHARTER — Fase ARE-1 Scientific Kernel

```text
STATUS   = DRAFT v0.95 (ARCHITECT-REVIEWED: ACCEPT WITH AMENDMENTS A1-A7) / ZERO AUTHORITY sampai diratifikasi owner
           lewat satu commit khusus yang menaikkan RATIFIED = YES
SUSUN    : External Auditor (2026-08-26), atas permintaan owner
REVIEW   : Lead Architect (filter sesuai AUDIT_COLLABORATION_CHARTER §2.4),
           lalu ratifikasi OWNER
RATIFIED = YES (2026-08-26, owner — commit T4)
```

## 1. Objek dan cakupan otoritas

Charter ini, begitu diratifikasi, memberikan **otoritas implementasi untuk
FASE ARE-1 Scientific Kernel SAJA**:

```text
DALAM CAKUPAN :
  - registry ilmiah (Problem/Episode/Hypothesis/Candidate/Capability/
    Graveyard) sebagai kode
  - Evidence Ledger infrastruktur (snapshot content-addressed, reservation,
    exposure accounting)
  - mesin kanonikal: canonical encoding V1, domain-separated hashing,
    append-only event store dengan previous-event-hash + CAS transaksi
  - state machine & invarian G01..G25 sesuai Matrix current
  - promosi TOOLS/*/SPEC menjadi implementasi uji dual-implementation
DI LUAR CAKUPAN KERAS (tetap tertutup tanpa charter baru) :
  - strategi/policy trading apa pun          - koneksi broker / order mutation
  - riset substantif P001                    - produksi & paper trading
  - fase ARE-2 Experience Intelligence dan seterusnya
  - edit byte dokumen normatif beku (perubahan semantik = generasi baru)
```

## 1B. Baseline subjek ARE-1

```text
BASELINE COMMIT = HEAD saat ratifikasi (dituliskan owner di commit T4)
NORMATIVE SET   = Manifest V38 gen-38 + warisannya; perubahan semantik
                  dokumen normatif selama ARE-1 => generasi baru lewat
                  proses koreksi biasa, lalu kode direbase ke subjek baru.
FREEZE LAMA     : disiplin output-set Policy V9 berlaku HANYA untuk gelombang
                  V36 yang telah tertutup; gelombang ARE-1 membuka policy
                  output-set sendiri pada S0-ARE-1 (wajib dibuat sebelum
                  commit kode pertama).
```

## 2. Pemicu pemberian otoritas (obyektif, dapat diverifikasi mesin)

```text
T1 DISPOSISI EKSTERNAL  : ACCEPT_ARE0_FORMAL_DESIGN_CLOSED @03aec99
                          terekam (commit d7e2d82; CURRENT_AUTHORITY_INDEX
                          baris GEN38_WAVE = CLOSED)            [TERPENUHI]
T2 IAQ LEDGER TUNTAS    : file ENGINEERING/IAQ_LEDGER.md memuat >= entri
                          cakupan-minimal (storage/CAS; kanonikal byte Windows;
                          root-of-trust lokal; instrumentasi anti hidden-trial;
                          pemisahan principal satu PC; transaksi IC-4);
                          tiap entri berdisposisi ANSWERED-WITH-CLAUSE |
                          NEEDS-NEW-GENERATION | DEFERRED(justified);
                          ditriase Lead Architect; nol blocker terbuka;
                          direkam sebagai QAO pembuka gelombang ARE-1  [BELUM]
T3 SLICE-1 CONTRACT     : unit kerja pertama ditulis eksplisit (modul,
                          kriteria terima, test fail-closed) dan diratifikasi
                          arsitek                              [BELUM]
T4 RATIFIKASI OWNER     : satu commit khusus oleh pemilik proyek yang
                          mengubah baris RATIFIKASI di file ini menjadi
                          YES + memperbarui CURRENT_AUTHORITY_INDEX:
                          IMPLEMENTATION(ARE-1) = AUTHORIZED   [BELUM]
```

Otoritas LAHIR pada commit T4 — bukan pada tanggal dokumen ini.

## 3. Mekanisme kerja setelah aktif

1. **GitHub-first** (Grand Design Bab 27): kontrak normatif → slice kecil →
   remote source audit → freeze exact SHA → pull SHA lokal → test →
   evidence publish balik. Local checkout = replica test.
2. **Source reuse** wajib (Bab 27): dilarang orchestrator/komponen kedua;
   kode ARE di package `are/`, test di `tests/are/`; versi = Git.
3. **Dual implementation** untuk operasi kanonikal kritis; regresi permanen;
   fail-closed; vocabulary suci (E-01..E-10 ENGINEERING/RULES.md tetap ikat).
4. Branch: hanya main; commit atas nama owner/engineering sesuai delegasi.
5. INTERAKSI DELEGASI-ONLY: Engineering AI menerima pekerjaan HANYA melalui
   delegasi bernomor dari Lead Architect (pola DELEGASI_001), tiap delegasi
   merujuk slice contract beku + larangan eksplisit.

## 3B. Firewall absolut (tidak tersentuh charter ini)

```text
P001 riset substantif ; produksi/live/paper trading ; broker mutation ;
strategi trading ; penutupan ARE-0 formal design  => TETAP TERKUNCI.
Charter ini TIDAK memberi, menyiratkan, atau dapat dibaca memberi salah satunya.
```

## 4. Pembatalan

Owner dapat mencabut via satu commit eksplisit `charter-revoke`. Efek:
pekerjaan baru berhenti; artefak eksisting dikarantina non-authoritative;
riwayat tidak pernah ditulis ulang; melanjutkan kembali butuh charter baru
dengan ceremony penuh. Pembatalan tidak menghapus kredit kualifikasi yang
sudah sah diperoleh sebelum pencabutan.

## 5. Bukti pemicu pada saat penyusunan draft

```text
CANDIDATE/BINDER : 03aec99 / a7287e7 (ROOT 3affbbf0…)
WAVE-CLOSE       : d7e2d82 (KL-1..KL-11; Index -> next wave ARE-1)
DELEGASI ENGINEERING READ-MODE : 2c682e8
CATATAN KOSMETIK : Index baris 40 masih "ARE-0 CLOSED = NO" -> sinkronkan
                   saat commit T4 (menjadi: ARE-0 DESIGN CLOSED @03aec99)

## 6. Amandemen arsitek (v0.95)
```

```text
A1 baseline subject pin (§1B)          A2 definisi tuntas T2 + coverage minimal
A3 interaksi delegation-only (§3.5)    A4 evidence test wajib commit dengan
                                       referensi exact SHA (workflow §12)
A5 firewall restatement (§3B)          A6 typo ENGINNERING -> ENGINEERING
A7 deklarasi policy output-set baru untuk gelombang ARE-1 (§1B)
```
```
