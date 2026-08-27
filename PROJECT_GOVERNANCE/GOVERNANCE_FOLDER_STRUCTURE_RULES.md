# GOVERNANCE FOLDER STRUCTURE RULES

Status: **ORGANIZATION RULE / STRUCTURAL_GENERATION_S2 / ZERO MACHINE-CLOSURE-AUDIT-RULE AUTHORITY**  
Effective date: **2026-08-26** (S1) · **2026-08-27** (S2: ARE1 arsip)

Aturan ini mengatur struktur folder `PROJECT_GOVERNANCE/` dan sistem diary
dua tingkat. Aturan ini TIDAK memberikan otoritas machine/closure/audit-rule,
TIDAK mengubah satu byte dokumen normatif mana pun, dan tidak membuka
implementasi/P001/produksi/trading.

---

## 1. Deklarasi STRUCTURAL_GENERATION_S1

Reorganisasi fisik ini dideklarasikan sebagai **STRUCTURAL_GENERATION_S1**:

1. Semua relokasi dilakukan **byte-identical** — konten file tidak berubah,
   Git blob SHA setiap file TETAP SAMA yang berubah hanya path-nya.
2. Nama file TIDAK berubah saat relokasi. Versi tetap diekspresikan dalam
   nama file (`_V<n>`) dan riwayat tetap milik Git.
3. Referensi old-path di dokumen historis yang sudah beku tetap valid sebagai
   sitasi sejarah — mereka menunjuk blob identik.
4. **Generasi manifest berikutnya wajib memakai path baru** sesuai tabel
   routing di Lampiran R1. Manifest lama (V1–V35) dengan old-path menjadi
   bukti historis generasi sebelumnya.
5. Stabil binding akan diperbarui pada generasi manifest berikutnya agar
   menunjuk path manifest baru.
6. Reorganisasi fisik serupa hanya boleh terjadi: (a) sebelum S0 baru
   dibekukan, atau (b) melalui deklarasi structural generation eksplisit
   seperti ini oleh pemilik proyek.

## 2. Struktur folder resmi

```text
PROJECT_GOVERNANCE/
├── GOVERNANCE_FOLDER_STRUCTURE_RULES.md   (file ini)
├── CURRENT_AUTHORITY_INDEX.md             (entry point orientasi — tetap di root)
├── ENGINEERING/                           (working agreement Engineering AI)
├── ARE0/                                  (semua dokumen ARE-0)
│   └── ... (11 kategori + DIARY, lihat §3)
├── ARE1/                                  (semua dokumen ARE-1 — Scientific Kernel) [S2 2026-08-27]
│   ├── README.md                          (index kategori ARE1)
│   ├── GRAND_DESIGN/                      desain menyeluruh human-readable
│   ├── AUTHORITY_AND_WORKFLOW/            otoritas fase + workflow kerja
│   ├── CONTRACTS/                         kontrak formal 0A–0F
│   ├── MACHINE/                           Matrix + Inventory (sumber mesin)
│   ├── MANIFEST/                          manifest normatif + stable binding
│   ├── COUNCIL_PROTOCOL/                  protokol Self-Audit Council
│   ├── QUARANTINE/                        kebijakan & record karantina legacy
│   ├── R9_CORRECTIONS/                    paket koreksi R9 + impact attack record
│   ├── EXTERNAL_AUDIT/                    handoff, pass record, paket koreksi audit eksternal
│   ├── QUALIFICATION/                     bukti kualifikasi internal (clean pass, regresi, konsistensi)
│   └── DIARY/                             diary khusus ARE-1 (lokal per kategori)
└── ARE2/                                  (semua dokumen ARE-2 — Experience Intelligence) [S2 2026-08-27]
    ├── README.md                          (index kategori ARE2)
    ├── GRAND_DESIGN/                      desain menyeluruh human-readable
    ├── AUTHORITY_AND_WORKFLOW/            otoritas fase + workflow kerja
    ├── CONTRACTS/                         kontrak formal (Slice Contract, IAQ, HASH_DOMAIN_TAGS)
    ├── MACHINE/                           Matrix + Inventory (sumber mesin)
    ├── MANIFEST/                          manifest normatif + stable binding
    ├── COUNCIL_PROTOCOL/                  protokol Self-Audit Council
    ├── QUARANTINE/                        kebijakan & record karantina legacy
    ├── R9_CORRECTIONS/                    paket koreksi R9 + impact attack record
    ├── EXTERNAL_AUDIT/                    handoff, pass record, paket koreksi audit eksternal
    ├── QUALIFICATION/                     bukti kualifikasi internal (clean pass, regresi, konsistensi)
    └── DIARY/                             diary khusus ARE-2 (lokal per kategori)
```

Folder kategori lain (misal `ARE3/`, `ARE4/`, ...) mengikuti pola yang sama
khi fasenya dibuka, dengan `README.md` index dan subfolder `DIARY/`
tersendiri.

**S2 aktif (2026-08-27):** `ARE1/` dan `ARE2/` telah dibuka per deklarasi STRUCTURAL_GENERATION_S2
(Lampiran R3 + R4). Struktur `ARE1/` dan `ARE2/` mirror `ARE0/` — 11 kategori + `DIARY/` + ledger
`RESIDUAL_REGISTER.md` untuk sistem FIX/DEFERRED/CATAT.

## 3. Definisi kategori

| Folder | Berisi | Contoh |
|---|---|---|
| `GRAND_DESIGN` | Peta desain terintegrasi human-readable | Formal Architecture Master, Architecture/Constitution/Object Model/Flowcharts V0 |
| `AUTHORITY_AND_WORKFLOW` | Dokumen otoritas fase & proses kerja | Formalization Authority, Publication Audit, Batched Workflow, GitHub-First Workflow, Source Reuse Hygiene |
| `CONTRACTS` | Kontrak formal normatif ARE-0A s/d 0F beserta versinya | 0A V1/V3, 0B V1/V3, 0C V2, 0D V2, 0E V2, 0F V1 |
| `MACHINE` | Sumber mesin kanonikal: authority/transition matrix + object inventory | Matrix V1–V28, Inventory/Register V1–V28 |
| `MANIFEST` | Closed exact path set + resolver stabil | Manifest V1–V38, Current Normative Manifest Binding |
| `COUNCIL_PROTOCOL` | Protokol dewan audit internal semua versi | Protocol V1–V35 |
| `QUARANTINE` | Kebijakan & ledger karantina authority legacy | Quarantine Policy V1–V8, Record, Record V3 |
| `R9_CORRECTIONS` | Koreksi root R9 + rekam serangan dampaknya | Correction Package V6–V34 (jendela normatif), Impact Attack Record V1–V9 |
| `EXTERNAL_AUDIT` | Seluruh siklus audit eksternal | Handoff V1–V8, Reaudit Handoff, Pass Record 1–3, Correction Package/Internal Review/Amendment, Filtered Record |
| `QUALIFICATION` | Bukti kualifikasi internal pra-audit | SA11 Ledger, Clean Pass 1&2, Regression, Final Consistency, Impact Audit, Qualification Root, Closure Batch Review, Pre-External-Audit x4, Council Run R7/R8 |

## 4. Aturan penempatan file baru

1. File baru WAJIB masuk tepat satu folder kategori sesuai fungsinya
   (tabel §3). Jika fungsi baru tidak cocok dengan kategori mana pun,
   buat kategori baru hanya dengan justifikasi tertulis + pembaruan
   aturan ini.
2. Versi baru dari seri existing masuk folder seri yang sama dan melanjutkan
   nomor versi terakhir (jangan mulai ulang dari V1).
3. Dilarang membuat file di root `PROJECT_GOVERNANCE/` selain:
   file ini, `CURRENT_AUTHORITY_INDEX.md`, dan folder kategori.
4. Dilarang membuat duplikat `_copy/_new/_final/backup`.
   Riwayat = Git.

## 5. Konvensi penamaan

- Pola nama existing dipertahankan: `AHFMES_<AREA>_<TOPIK>_V<n>.md`,
  UPPERCASE, pemisah underscore, tanpa spasi.
- Diary: `YYYY-MM-DD-<SUBJEK-SINGKAT>.md` (konvensi existing dipertahankan).
- Tidak ada rename atas file yang sudah menjadi anggota manifest beku kecuali
  lewat structural generation baru.

## 6. Sistem diary dua tingkat

### Tingkat lokal (per kategori)

- Setiap folder fase/kategori memiliki subfolder `DIARY/` sendiri
  (contoh: `ARE0/DIARY/`).
- Diary lokal mencatat detail teknis harian lingkup kategori tersebut:
  keputusan desain, hasil attack, koreksi, status kualifikasi lokal.
- Format nama: `YYYY-MM-DD-<SUBJEK>.md`.

### Tingkat global (indeks progres)

- Satu diary global: `PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md`.
- Fungsi: **catat kemajuan progres lintas kategori dan MERUJUK** entri diary
  lokal — BUKAN menduplikasi isinya.
- Setiap entri global minimal berisi:

```text
## YYYY-MM-DD — <judul progres>
KATEGORI : <mis. ARE0>
STATUS   : <satu baris>
DETAIL   : <rujuk path entri diary lokal terkait>
DAMPAK   : <apa yang berubah secara global>
```

- Entri global ditambah di ATAS (terbaru dulu), append-only, tanpa rewrite
  histori.

### Mode wave aktif

Selama gelombang kualifikasi aktif (post-S0 sebelum candidate freeze),
Policy yang berlaku mewajibkan exact-path output set: diary lokal ARE-0
dikonsolidasikan ke SATU file ledger wave yang ditunjuk (lihat Policy V8,
JQO_LOCAL) dan file diary bertanggal baru ditangguhkan hingga wave ditutup.
Konvensi `YYYY-MM-DD` di atas berlaku kembali setelah wave.

### Batasan otoritas diary

Diary (lokal maupun global) adalah evidence/chronology saja:
nol otoritas machine/closure/audit-rule; tidak bisa memperbaiki semantik,
mengganti proof, atau menerbitkan PASS/CLOSED/READY — konsisten dengan
disposisi QAO/JQO pada gelombang kualifikasi sebelumnya.

## 7. Larangan yang tetap berlaku

```text
branch baru, worktree baru, force push        = DILARANG
edit byte dokumen normatif saat relokasi     = DILARANG
rename file anggota manifest beku            = DILARANG tanpa structural generation
file duplikat _v2/_new/_final/_backup        = DILARANG
folder liar di root governance               = DILARANG
```

---

## LAMPIRAN R1 — Tabel routing pattern → folder (untuk manifest berikutnya)

| Pattern nama file | Folder tujuan |
|---|---|
| `AHFMES_ARE_FORMAL_ARCHITECTURE_MASTER_*` | `ARE0/GRAND_DESIGN/` |
| `AHFMES_AUTONOMOUS_RESEARCH_ENGINE_*` | `ARE0/GRAND_DESIGN/` |
| `AHFMES_ARE_V0_FORMALIZATION_AUTHORITY*` | `ARE0/AUTHORITY_AND_WORKFLOW/` |
| `AHFMES_ARE_V0_DOCUMENTATION_PUBLICATION_AUDIT*` | `ARE0/AUTHORITY_AND_WORKFLOW/` |
| `AHFMES_ARE_BATCHED_ARCHITECTURE*` | `ARE0/AUTHORITY_AND_WORKFLOW/` |
| `AHFMES_ARE_GITHUB_FIRST*` | `ARE0/AUTHORITY_AND_WORKFLOW/` |
| `AHFMES_ARE_SOURCE_REUSE*` | `ARE0/AUTHORITY_AND_WORKFLOW/` |
| `AHFMES_ARE_0[A-F]_*` | `ARE0/CONTRACTS/` |
| `AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_*` | `ARE0/MACHINE/` |
| `AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_*` | `ARE0/MACHINE/` |
| `AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_*` | `ARE0/MANIFEST/` |
| `AHFMES_ARE_0_CURRENT_NORMATIVE_MANIFEST_BINDING*` | `ARE0/MANIFEST/` |
| `AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_*` | `ARE0/COUNCIL_PROTOCOL/` |
| `AHFMES_ARE_0_LEGACY_AUTHORITY_QUARANTINE_*` | `ARE0/QUARANTINE/` |
| `AHFMES_ARE_0_R9_CORRECTION_PACKAGE_*` | `ARE0/R9_CORRECTIONS/` |
| `AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_*` | `ARE0/R9_CORRECTIONS/` |
| `AHFMES_ARE_0_EXTERNAL_AUDIT_*` | `ARE0/EXTERNAL_AUDIT/` |
| `AHFMES_ARE_0_EXTERNAL_REAUDIT_*` | `ARE0/EXTERNAL_AUDIT/` |
| `AHFMES_ARE_0_FINAL_CLOSURE_AUDIT_FILTERED_RECORD*` | `ARE0/EXTERNAL_AUDIT/` |
| `AHFMES_ARE_0_SA11_*` | `ARE0/QUALIFICATION/` |
| `AHFMES_ARE_0_CLEAN_PASS_*` | `ARE0/QUALIFICATION/` |
| `AHFMES_ARE_0_REGRESSION_R7_R8_R9*` | `ARE0/QUALIFICATION/` |
| `AHFMES_ARE_0_FINAL_CONSISTENCY_RECORD*` | `ARE0/QUALIFICATION/` |
| `AHFMES_ARE_0_INTERNAL_IMPACT_AUDIT_RECORD*` | `ARE0/QUALIFICATION/` |
| `AHFMES_ARE_0_QUALIFICATION_ROOT_RECORD*` | `ARE0/QUALIFICATION/` |
| `AHFMES_ARE_0_CLOSURE_BATCH_INTERNAL_REVIEW*` | `ARE0/QUALIFICATION/` |
| `AHFMES_ARE_0_PRE_EXTERNAL_AUDIT_*` | `ARE0/QUALIFICATION/` |
| `AHFMES_ARE_0_SELF_AUDIT_COUNCIL_RUN_*` | `ARE0/QUALIFICATION/` |

Old-path → new-path untuk semua file lainnya mengikuti tabel di atas secara
mekanis (nama file identik, prefiks folder bertambah).

## LAMPIRAN R2 — Rekap eksekusi STRUCTURAL_GENERATION_S1

```text
TANGGAL              = 2026-08-26
FILE DIRLOKASI       = 223 (governance) + 8 (diary ARE0 dari PROJECT_JOURNAL/DIARY)
BYTE CHANGES         = NONE (relokasi murni, blob SHA tidak berubah)
ROOT SETELAH         = GOVERNANCE_FOLDER_STRUCTURE_RULES.md, CURRENT_AUTHORITY_INDEX.md, ARE0/
GLOBAL DIARY         = PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md (baru)
```
 
## LAMPIRAN R4 — Rekap eksekusi STRUCTURAL_GENERATION_S2 (ARE2 arsip)
 
```text
TANGGAL              = 2026-08-27
DEKLARASI            = STRUCTURAL_GENERATION_S2 — pembukaan arsip fase ARE-2
PEMICU               = ARE-1 CLOSED @a6711d6 (ACCEPT), ARE-2 DESAIN dibuka
DASAR                = §1.6(a) sebelum S0-ARE2 dibekukan + §2 "ARE2/ mirror ARE0"
FOLDER DIBUAT        = PROJECT_GOVERNANCE/ARE2/ (11 kategori mirror ARE0)
                      ├── README.md                          (index ARE2, 63 baris)
                      ├── GRAND_DESIGN/                      (kosong, siap isi)
                      ├── AUTHORITY_AND_WORKFLOW/            (kosong, siap isi)
                      ├── CONTRACTS/                         (kosong, siap isi)
                      ├── MACHINE/                           (kosong, siap isi)
                      ├── MANIFEST/                          (kosong, siap isi)
                      ├── COUNCIL_PROTOCOL/                  (kosong, siap isi)
                      ├── QUARANTINE/                        (kosong, siap isi)
                      ├── R9_CORRECTIONS/                    (kosong, siap isi)
                      ├── EXTERNAL_AUDIT/                    (kosong, siap isi)
                      ├── QUALIFICATION/                     (kosong, siap isi)
                      └── DIARY/
                          └── .gitkeep                       (placeholder)
LEDGER BARU          = PROJECT_GOVERNANCE/ARE1/RESIDUAL_REGISTER.md (FIX/DEFERRED/CATAT, 158+ baris)
                      — ledger terpusat agar DEFERRED tidak PR lupa (G07/G18 persist)
BYTE CHANGES         = README.md baru + 11× .gitkeep (0 bytes each)
                       Tidak ada manifest member lama yang diubah byte-nya
ROOT SETELAH         = GOVERNANCE_FOLDER_STRUCTURE_RULES.md, CURRENT_AUTHORITY_INDEX.md, ARE0/, ARE1/, ARE2/
NEXT                 = Generasi manifest V40+ wajib pakai path ARE2/MANIFEST/ per tabel R1 (update R1 next)
                       Diary ARE2 selanjutnya langsung di ARE2/DIARY/ (bukan ARE0/ARE1)
```

```text
TANGGAL              = 2026-08-27
DEKLARASI            = STRUCTURAL_GENERATION_S2 — pembukaan arsip fase ARE-1
PEMICU               = ARE-1 Scientific Kernel selesai 83f73c0 (HEAD d0d24af), perlu arsip
                      terpisah agar pembelajaran lintas fase (ARE0/ARE1/ARE2...) mudah
DASAR                = §1.6(a) sebelum S0-ARE1 dibekukan + §2 "ARE1/ mirror ARE0"
FOLDER DIBUAT        = PROJECT_GOVERNANCE/ARE1/ (11 kategori mirror ARE0)
                      ├── README.md                          (index ARE1, 38 baris)
                      ├── GRAND_DESIGN/                      (kosong, siap isi)
                      ├── AUTHORITY_AND_WORKFLOW/
                      ├── CONTRACTS/
                      ├── MACHINE/
                      ├── MANIFEST/
                      ├── COUNCIL_PROTOCOL/
                      ├── QUARANTINE/
                      ├── R9_CORRECTIONS/
                      ├── EXTERNAL_AUDIT/
                      ├── QUALIFICATION/
                      └── DIARY/
                          ├── 2026-08-27-ARE1-RESIDUAL-JURNAL.md (73 baris, relokasi byte-identical dari ARE0/DIARY/)
                          └── _TEMPLATE_HARIAN.md            (template 2-tingkat)
LEDGER BARU          = PROJECT_GOVERNANCE/ARE1/RESIDUAL_REGISTER.md (FIX/DEFERRED/CATAT, 158+ baris)
                      — ledger terpusat agar DEFERRED tidak PR lupa (G07/G18 persist)
RELOKASI             = 1 file byte-identical: ARE0/DIARY/2026-08-27-ARE1-RESIDUAL-JURNAL.md
                      → ARE1/DIARY/2026-08-27-ARE1-RESIDUAL-JURNAL.md (SHA1 8481C84F...)
                      + patch internal path ARE0→ARE1 (1 baris) — ARE0 copy dipertahankan sebagai jejak S2
BYTE CHANGES         = README.md baru + RESIDUAL_REGISTER.md baru + TEMPLATE baru + relokasi 1 file (copy)
                      Tidak ada manifest member lama yang diubah byte-nya
ROOT SETELAH         = GOVERNANCE_FOLDER_STRUCTURE_RULES.md, CURRENT_AUTHORITY_INDEX.md, ARE0/, ARE1/
NEXT                 = Generasi manifest V40+ wajib pakai path ARE1/MANIFEST/ per tabel R1 (update R1 next)
                       Diary ARE1 selanjutnya langsung di ARE1/DIARY/ (bukan ARE0)
```
