# IAQ LEDGER — Implementability Questions (Engineering AI)

```text
STATUS   = ENGINEERING DELIVERABLE / DELEGASI_001 / ZERO AUTHORITY
           (input untuk triase Lead Architect; bukan keputusan)
DIBUAT   = 2026-08-26
SUBJEK   = HEAD 2c682e8fa0d9bb1f62a3ccac577499d61b3642a2 (terverifikasi)
MANIFEST = V38 gen-38: 134 non-self + 1 SELF, 0 duplikat, SELF 22479 B,
           disk-vs-manifest 134/134 cocok, tree-vs-manifest 134/134 cocok,
           ROOT direproduksi implementasi sendiri =
           3affbbf079cef439879c64169938ef8798828097d1143f45ced8947b7f2bc4e2
REFERENSI= ENGINEERING/DELEGASI_001_IAQ_READMODE.md ; ENGINEERING/RULES.md
METODE   = E-02 RULES.md: setiap entri lahir dari kalimat spesifikasi yang
           tidak bisa diterjemahkan langsung menjadi modul/test/field/transisi.
CATATAN  = Disposisi akhir tiap entri (ANSWERED-WITH-CLAUSE |
           NEEDS-NEW-GENERATION | DEFERRED) ditetapkan saat triase arsitek,
           sesuai IMPLEMENTATION_AUTHORITY_CHARTER.md §2 T2.
```

---

## IAQ-001

```text
PERTANYAAN : Engine penyimpanan apa yang merealisasikan event store
             append-only + previous-event-hash + compare-and-append atomik
             di satu PC, dan bagaimana "append-only" ditegakkan secara
             mekanis (bukan sekadar disiplin)?
KLAUSE     : PROJECT_GOVERNANCE/ARE0/MACHINE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V30.md:15-26
             (semua objek immutable/append-only; sole writer per objek);
             GRAND DESIGN/AHFMES_ARE_GRAND_DESIGN_V1.md:368-371 (G19 revisi
             monotonik + previous-event-hash + compare-and-append atomik;
             partial failure tidak memajukan state);
             PROJECT_GOVERNANCE/ARE0/MACHINE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V30.md:42-48 (IC-4).
MENGAPA    : Salah pilih primitif -> jendela partial-write melahirkan state
             yang tak terdecide dari byte tersimpan; replay nondeterministik
             mematahkan regresi X-series dan proof lineage (X302-class).
OPSI-JAWAB :
  (a) SQLite (WAL) — events table append-only, head table satu baris/stream
      dimutasi hanya via CAS `WHERE last_revision=?`; UPDATE/DELETE pada
      events diblokir di lapisan akses + regression test membuktikannya.
      stdlib Python -> nol dependency.
  (b) File log content-addressed per stream + lock file eksklusif untuk CAS
      (pola git-object); paling transparan byte-wise, tapi CAS lintas-proses
      harus dibuat manual.
  (c) Embedded KV non-stdlib (LMDB) — transaksi kuat, tapi menambah
      dependency yang butuh justifikasi tertulis (RULES E-05/TOOLS prinsip).
  USULAN-REKOMENDASI : (a), dengan invariant test: setelah crash simulasi
  di titik mana pun, state selalu dapat direkonstruksi dari committed rows
  saja (menyatu dengan IAQ-006).
```

## IAQ-002

```text
PERTANYAAN : Bagaimana tepatnya kanonikal byte (UTF-8 NFC, pemisah NUL,
           newline LF, sort ordinal-byte) ditegakkan di platform Windows —
           dan apakah loader MEMVERIFIKASI input sudah kanonikal atau
           MENORMALISASI diam-diam?
KLAUSE     : PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V38.md:172-181
           (root algorithm: raw UTF-8 path bytes, \0, sort leksikografis,
           no EOL conversion); GRAND DESIGN ...V1.md:424-431
           (AHFMES_CANONICAL_OBJECT_V1: NFC, key urut, tanpa float,
           RFC3339-Z); ledger ENTRI 2 (pelajaran Sort-Object culture-sensitive
           & CRLF sudah dinetralkan); .gitattributes `* -text`.
MENGAPA    : Collation culture-sensitive atau auto-normalize yang salah
           memberi root berbeda antar mesin = gagal rekonsiliasi IC-1
           (fail-closed total) atau lebih buruk: identitas ganda.
OPSI-JAWAB :
  (a) Verifier fail-closed: input non-NFC/BOM/CRLF -> REJECT dengan laporan
      offset byte; normalisasi TIDAK PERNAH implisit.
  (b) Normalizer eksplisit sebagai tahap pipeline terpisah yang mencatat
      transformasi sebagai event.
  (c) String-based + StringComparer.Ordinal — risiko jika ada jalur yang
      lolos ke default culture.
  USULAN-REKOMENDASI : (a) untuk boundary otoritas + uji adversarial wajib
  (karakter penggabung, locale tr-TR, CRLF injection); identitas SELALU
  dihitung atas byte[], bukan string.
```

## IAQ-003

```text
PERTANYAAN : Tanpa boundary OS-level, apa wujud konkret Governance Root ->
           Trusted Gate Registry -> Principal Role Manifest -> VAR, dan siapa
           yang menegakkan verify-at-use bila kode riset dianggap bisa
           compromised?
KLAUSE     : GRAND DESIGN ...V1.md:404-420 (rantai bootstrap; perubahan root =
           operasi governance eksternal; nama ramah bukan otoritas);
           PROJECT_GOVERNANCE/ARE0/MACHINE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V30.md:28-34 (IC-2:
           recognition wajib re-evaluasi VAR CURRENT/not-revoked/not-expired
           saat use); REGISTER V30:20 (VAR_CURRENT states; absent pair =>
           INVALID).
MENGAPA    : Bila authority store dapat dicapai/mutasi oleh proses riset,
           pemisahan THINK->PROVE->ACT runtuh = blocker kelas A
           (konstitusional, reset kredit per advisory D1).
OPSI-JAWAB :
  (a) Proses OS terpisah pemilik authority store (client library untuk
      riset; tidak ada shared memory); ko-lokasi fisik tetap dipisah izin
      (GRAND DESIGN ...V1.md:400-401).
  (b) Satu proses, modul terpisah + ACL file — termurah, terlemah.
  (c) Capability token bertanda tangan diverifikasi terhadap registry
      append-only lokal (komposabel dengan (a)).
  USULAN-REKOMENDASI : (a)+(c) untuk ARE-1: minimal SATU proses penjaga
  otoritas yang tidak mengeksekusi kode riset; token content-addressed.
```

## IAQ-004

```text
PERTANYAAN : Mekanisme apa yang membuat hidden-trial MUSTAHIL secara
           struktural (bukan dilarang policy) — bagaimana SETIAP evaluasi
           outcome-aware, termasuk di dalam loop optimizer/LLM, terpaksa
           menerbitkan Search Node?
KLAUSE     : GRAND DESIGN ...V1.md:597-625 (setiap keputusan adaptif
           outcome-aware = Search Node immutable; optimizer dihitung per
           evaluasi EMITTED; unknown action class tidak gratis; Search
           Completeness Proof; UNKNOWN_SEARCH_DEBT menolak validasi),
           :569-596 (Program Budget Envelope beku pra-outcome);
           PROJECT_GOVERNANCE/ARE0/R9_CORRECTIONS/AHFMES_ARE_0_R9_CORRECTION_PACKAGE_V35.md:26-29 (IA2-R01/R02 pairing & oracle DENY).
MENGAPA    : Satu saja hidden trial = multiplicity accounting palsu ->
           SEMUA proof downstream INVALID (SC-05); ini cacat yang paling
           mahal dideteksi belakangan.
OPSI-JAWAB :
  (a) Chokepoint gateway: satu-satunya API yang mengembalikan outcome;
      akses data lain cuma handle terbatas yang konsumsinya wajib emit node.
  (b) Rekonsiliasi pasca-hoc log komputasi vs search tree (regression check).
  (c) Sandbox IO-interception menyeluruh.
  USULAN-REKOMENDASI : (a) sebagai desain inti + (b) sebagai regresi
  permanen; (c) tidak memadai sendirian.
```

## IAQ-005

```text
PERTANYAAN : Struktur runtime seperti apa yang menegakkan principal/capability
           BERBEDA untuk layanan THINK/PROVE/ACT dalam SATU mesin fisik,
           sehingga separation-of-duty tidak runtuh menjadi nama class?
KLAUSE     : GRAND DESIGN ...V1.md:160-182 (trust worlds; pemisahan MEKANIS),
           :377-400 (matriks SoD; ko-lokasi != runtuh izin);
           PROJECT_GOVERNANCE/ARE0/CONTRACTS/AHFMES_ARE_0B_AUTHORITY_NON_FORGEABILITY_V3.md (seluruh kontrak).
MENGAPA    : SoD runtuh -> rantai promosi bisa dipalsukan dari dalam riset;
           ini kelas temuan eksternal berulang (R8/R9 family).
OPSI-JAWAB :
  (a) Tiga proses OS berbeda + pesan capability bertanda tangan + bus
      auditable; shared-nothing kecuali bus.
  (b) Satu proses, principal logikal via library (paling lemah).
  (c) Container/job object per world (Windows-specific overhead).
  USULAN-REKOMENDASI : (a) minimal-viable (proses terpisah + token),
  (c) opsional belakangan; (b) hanya untuk design spike, bukan produksi.
```

## IAQ-006

```text
PERTANYAAN : Primitif transaksional apa yang mewujudkan IC-4 "receipt-append
           FIRST, nonce-consumption SECOND, satu transaksi" plus SATU langkah
           finalize idempoten yang keputusannya HANYA dari ledger+VAR state?
KLAUSE     : PROJECT_GOVERNANCE/ARE0/MACHINE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V30.md:42-48
           (IC-4 verbatim; "Behavior never depends on unobserved external
           facts"); REGISTER V30:21 (crash finalization derives ONLY from
           this object + VAR state; absent/ambiguous => CONSUMED fail-closed).
MENGAPA    : Urutan/primitif salah -> orphan VAR (INVALID per IC-3) atau
           receipt hilang; ambigu CONSUMED vs UNUSED memblokir recovery sah
           atau membolehkan konsumsi ganda.
OPSI-JAWAB :
  (a) Transaksi DB tunggal (BEGIN IMMEDIATE) menulis kedua efek; finalize =
     predikat deterministik f(state ledger row, ada-tidaknya receipt)
     dieksekusi idempoten saat recovery.
  (b) Journal dua-fase buatan manual di atas file.
  (c) Rename atomik bundle berisi kedua record.
  USULAN-REKOMENDASI : (a); finalize WAJIB tanpa jam/tanpa fakta eksternal;
  uji: crash matrix per instruksi (antara dua write) -> hasil state selalu
  sama untuk input byte sama (E-RULES determinism).
```

## IAQ-007

```text
PERTANYAAN : Jam mana yang menandai timestamp RFC3339-Z dan mengevaluasi
           EXPIRED pada verify-at-use, sedangkan wall-clock DILARANG jadi
           key material — bagaimana expiry tetap deterministic saat replay/test?
KLAUSE     : REGISTER V30:17-25 (states EXPIRED/CONSUMED; rule 5: no object
           key includes ... wall-clock ...); GRAND DESIGN ...V1.md:433-446
           (freshness: otoritas stale tak bisa mentransisi); Bab 13 L424-427
           (timestamp UTC RFC3339-Z di identitas kanonikal).
MENGAPA    : Expiry dievaluasi dari jam sistem mentah = replay test tak
           deterministik & side-channel schedule (risiko RS-5 warisan V25/V31).
OPSI-JAWAB :
  (a) Clock port terinjeksi (interface tunggal) + waktu tercatat sebagai
      event; evaluasi currentness murni fungsi event tercatat.
  (b) System UTC langsung di layer evaluasi (tidak deterministik untuk test).
  USULAN-REKOMENDASI : (a); aturan: keputusan EXPIRED selalu derivable dari
  (recorded_time, validity_window) yang tersimpan — bukan dari now() saat query.
```

## IAQ-008

```text
PERTANYAAN : Skema hash domain-separated merujuk domain_tag per tipe objek,
           tetapi enumerasi tag yang normatif per tipe (CANDIDATE_ROOT,
           EVIDENCE_SNAPSHOT, dst.) tidak ditemukan dalam satu tabel tunggal —
           di mana daftar kanonikel tag itu hidup?
KLAUSE     : GRAND DESIGN ...V1.md:427 ("SHA256(\"AHFMES:\" || domain_tag ||
           \":V1\n\" || bytes)" dengan "tag eksplisit per tipe"); TIDAK
           DITEMUKAN tabel enumerasi tag di Matrix V30/Register V30/
           Correction V35/Manifest V38 yang saya baca (LANGKAH 2).
MENGAPA    : Tag yang salah/saling bentrok = identitas konten tidak dapat
           diverifikasi silang antar implementasi; dual-implementation akan
           "lolos" dengan dua kesalahan yang kebetulan sama.
OPSI-JAWAB :
  (a) Arsitek menerbitkan lampiran enumerasi tag (generasi dokumen baru).
  (b) Tag diturunkan mekanis dari nama objek Register V30 kolom pertama.
  (c) DEFERRED sampai slice pertama yang membutuhkan.
  USULAN-REKOMENDASI : (a) — ini kandidat NEEDS-NEW-GENERATION; tanpa itu,
  implementasi tag mana pun adalah tebak-tebakan (melanggar E-02).
```

## IAQ-009

```text
PERTANYAAN : Binding mensyaratkan pencocokan path byte-exact case-sensitive,
           padahal NTFS default case-insensitive — bagaimana dua path kanonikel
           yang berbeda huruf dicegah bertabrakan di disk?
KLAUSE     : PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_CURRENT_NORMATIVE_MANIFEST_BINDING.md:24-25
           ("byte-exact and case-sensitive ordinal comparison"; varian casing
           fails closed); Policy V9:40-43 (tanpa exemption apa pun).
MENGAPA    : Tabrakan casing = dua anggota manifest berbagi satu inode file
           -> blob verification bisa lolos salah satu dan FAIL yang lain
           (X302-class), atau lebih halus: resolver membuka file yang salah.
OPSI-JAWAB :
  (a) Identitas selalu dari konten record (path tersimpan DI DALAM record,
       diverifikasi saat use), bukan dari lookup FS; startup scan mendeteksi
       case-collision -> fail-closed stop.
  (b) Aktifkan case-sensitivity per direktori (Windows 10+ WSL flag) —
       bergantung konfigurasi mesin, fragile.
  USULAN-REKOMENDASI : (a) wajib; (b) boleh sebagai hardening tambahan,
       tidak boleh prasyarat.
```

## IAQ-010

```text
PERTANYAAN : Kolom "sole writer" Register V30 harus menjadi PEMETAAN
           objek->proses/peran runtime yang eksak — siapa yang memilikinya
           dan di mana tabel pemetaan itu didefinisikan agar tidak ada dua
           proses mengklaim writer yang sama?
KLAUSE     : REGISTER V30:16-26 (kolom Sole writer per objek; IC-5 writer
           binding (holder-control-id, RoleManifest-generation) di Matrix
           V30:50-55); Matrix V29 Edge 1 precondition (ledger entry UNUSED
           wajib ada — IC-3).
MENGAPA    : Dua kandidat writer = CAS jadi pertarungan proses; pelanggaran
           sole-writer = INTEGRITY_DEFECT massal yang sulit dibedakan dari
           serangan sungguhan.
OPSI-JAWAB :
  (a) Tabel routing writer-to-process diterbitkan sebagai bagian konfigurasi
       ARE-1 yang diratifikasi arsitek (statis per deployment, diikat by-hash
       pada Role Manifest).
  (b) Dinamis via lease/lock — kompleks, menambah sumber race baru.
  USULAN-REKOMENDASI : (a) statis-by-hash untuk ARE-1; pelanggaran deteksi =
       regression permanen.
```

---

## Penutup

```text
JUMLAH ENTRI   = 10 (cakupan-minimal delegasi terpetakan: IAQ-001 storage/
                 CAS, 002 kanonikal Windows, 003 root-of-trust lokal,
                 004 anti-hidden-trial, 005 principal satu PC, 006 IC-4;
                 perluasan: 007 clock, 008 domain_tag, 009 casing NTFS,
                 010 sole-writer map)
BLOCKER UNTUK  = TIDAK ADA yang mengubah semantik dokumen normatif dari
CODING         sisi engineer; IAQ-008 berpotensi butuh generasi dokumen baru
                 (keputusan arsitek).
LARANGAN       = file ini evidence/chronology engineering; zero authority;
                 tidak menjawab P001; tidak menyentuh dokumen normatif.
```


---

## TRIASE LEAD ARCHITECT — DISPOSISI FINAL T2 (2026-08-26)

```text
METODE   : setiap entri diadili terhadap klausa normatif current;
           rekomendasi engineer diterima bila konsisten IC/Matrix dan
           paling mudah diuji deterministik.
HASIL    : 9 ANSWERED-WITH-CLAUSE · 1 NEEDS-NEW-GENERATION · 0 DEFERRED
           · 0 OPEN BLOCKER  =>  T2 = TERPENUHI (menunggu verifikasi auditor)
```

| ID | DISPOSISI | KEPUTUSAN ARSITEK |
|---|---|---|
| IAQ-001 | ANSWERED | Terima (a) SQLite WAL: events append-only (UPDATE/DELETE diblok lapisan akses + regression test), head CAS `WHERE last_revision=?`; crash-reconstruction invariant test wajib |
| IAQ-002 | ANSWERED | Terima (a) verifier FAIL-CLOSED: non-NFC/BOM/CRLF => REJECT dengan offset; identitas SELALU dari byte[]; uji adversarial (combining char, locale tr-TR, CRLF injection) wajib |
| IAQ-003 | ANSWERED | Terima (a)+(c): minimal SATU proses penjaga otoritas terpisah yang tidak mengeksekusi kode riset + capability token content-addressed; ko-lokasi tetap dipisah izin |
| IAQ-004 | ANSWERED | Terima (a) chokepoint gateway sebagai desain inti + (b) rekonsiliasi log-vs-tree sebagai regresi permanen; detail enforcement masuk slice contract pertama |
| IAQ-005 | ANSWERED | Terima (a) minimal-viable: proses OS terpisah per world + capability token bertanda tangan; (c) opsional belakangan; (b) hanya design spike |
| IAQ-006 | ANSWERED | Terima (a): satu transaksi BEGIN IMMEDIATE untuk kedua efek; finalize = predikat deterministik f(ledger row, receipt presence), idempoten, tanpa jam/tanpa fakta eksternal; crash-matrix test wajib |
| IAQ-007 | ANSWERED | Terima (a): clock port terinjeksi; EXPIRED selalu derivable dari (recorded_time, validity_window) tersimpan — never from now() at query time |
| IAQ-008 | **NEEDS-NEW-GENERATION** | Setuju dgn engineer: enumerasi domain_tag memang belum normatif. ARSITEK AKAN MENERBITKAN lampiran `HASH_DOMAIN_TAGS` (tabel tag per tipe objek, content-addressed) sebagai bagian generasi pembuka ARE-1 (gen-39). Sampai itu: DILARANG mengimplementasikan hashing apa pun |
| IAQ-009 | ANSWERED | Terima (a): identitas dari konten record; startup scan case-collision => stop fail-closed; opsi (b) hanya hardening tambahan |
| IAQ-010 | ANSWERED | Terima (a): tabel routing writer-to-process statis per deployment, diratifikasi arsitek, diikat by-hash pada Role Manifest; pelanggaran = regresi permanen |

## Konsekuensi terhadap alur

```text
T2 = TERPENUHI (10/10 terdisposisi; coverage-minimal 6/6 hadir)
GEN-39 (pembuka ARE-1) wajib membawa: lampiran HASH_DOMAIN_TAGS
       (IAQ-008) + sinkronisasi label minor KL bila ada.
LANGKAH BERIKUTNYA:
  1. Auditor verifikasi triase ini (T2 adjudikasi silang)
  2. Arsitek membekukan SLICE-1 CONTRACT (T3)
  3. OWNER commit ratifikasi (T4) => IMPLEMENTATION(ARE-1) = AUTHORIZED
```
