# IMPLEMENTATION AUTHORITY CHARTER — Fase ARE-2 Experience Intelligence

```text
STATUS   = DRAFT v0.90 (ARCHITECT-DRAFT) / RATIFIED BY OWNER
           lewat satu commit khusus yang menaikkan RATIFIED = YES
SUSUN    : Lead Architect (2026-08-27), berdasarkan ARE-1 ACCEPT + IAQ_LEDGER_ARE2 triase
REVIEW   : Lead Architect (filter sesuai AUDIT_COLLABORATION_CHARTER §2.4),
           lalu ratifikasi OWNER
RATIFIED = YES (2026-08-27, owner — commit T4)
```

## 1. Objek dan cakupan otoritas

Charter ini, begitu diratifikasi, memberikan **otoritas implementasi untuk
FASE ARE-2 Experience Intelligence SAJA**:

```text
DALAM CAKUPAN :
  - Experience Store (decision memory, regret memory, anomaly detection)
    append-only, content-addressed, deterministic replay
  - Anomaly Detection deterministik (regime shift, spread hostility, CF quality)
  - Replay Engine + What-If Engine (pure function, fork snapshot, deterministic)
  - Knowledge Synthesis + Capability Gap Assessment (evidence-based, Owner approval)
  - Evidence Ledger ARE-1 integration (consumer via reservation, derivative snapshots)
  - Observability & Data Quality Gates (pipeline gates, quarantine, metrics)
  - Anomaly Alerting & Notification (deterministic, audit log, CSK integration)
  - Configuration & Version Management (frozen typed config, content-hash)
  - Audit Trail & External Auditor Reproducibility (JSONL, dual-check)
  - Performance & Resource Bounds (config-driven bounds, quotas)
  - Reuse Existing Components (adapter pattern, zero modification)
  - state machine & invarian G01..G25 sesuai Matrix current (reuse ARE-1)
  - promosi TOOLS/*/SPEC menjadi implementasi uji dual-implementation
DI LUAR CAKUPAN KERAS (tetap tertutup tanpa charter baru) :
  - strategi/policy trading apa pun          - koneksi broker / order mutation
  - riset substantif P001                    - produksi & paper trading
  - fase ARE-3 Autonomous Science dan seterusnya
  - edit byte dokumen normatif beku (perubahan semantik = generasi baru)
```

## 1B. Baseline subjek ARE-2

```text
BASELINE COMMIT = HEAD saat ratifikasi (dituliskan owner di commit T4)
NORMATIVE SET   = Manifest V39 gen-39 + ARE-1 warisannya + HASH_DOMAIN_TAGS_ARE2
                  perubahan semantik dokumen normatif selama ARE-2 => generasi baru
                  lewat proses koreksi biasa, lalu kode direbase ke subjek baru.
FREEZE LAMA     : disiplin output-set Policy V9 berlaku HANYA untuk gelombang
                  V36 yang telah tertutup; gelombang ARE-2 membuka policy
                  output-set sendiri pada S0-ARE-2 (wajib dibuat sebelum
                  commit kode pertama).
```

## 2. Pemicu pemberian otoritas (obyektif, dapat diverifikasi mesin)

```text
T1 DISPOSISI EKSTERNAL  : ACCEPT_ARE1_SCIENTIFIC_KERNEL_CLOSED @a6711d6
                          terekam (CURRENT_AUTHORITY_INDEX
                          baris GEN39_WAVE = CLOSED, GEN39_WAVE = CLOSED)   [TERPENUHI]
T2 IAQ LEDGER TUNTAS    : file ENGINEERING/IAQ_LEDGER_ARE2.md memuat >= entri
                          cakupan-minimal (Experience Store, Anomaly Detection,
                          Replay/What-If, Knowledge Synthesis, Evidence Ledger
                          Integration, Observability, Reuse, Config, Audit,
                          Performance, Prerequisites, Residual Integration);
                          tiap entri berdisposisi ANSWERED-WITH-CLAUSE |
                          NEEDS-NEW-GENERATION | DEFERRED(justified);
                          ditriase Lead Architect; nol blocker terbuka;
                          direkam sebagai QAO pembuka gelombang ARE-2  [TERPENUHI 2026-08-27, triase 17/17 ANSWERED-WITH-CLAUSE]
T3 SLICE-1 CONTRACT     : unit kerja pertama ditulis eksplisit (modul,
                          kriteria terima, test fail-closed) dan diratifikasi
                          arsitek                              [TERPENUHI 2026-08-27, frozen SLICE_1_CONTRACT_ARE2.md]
T4 RATIFIKASI OWNER     : satu commit khusus oleh pemilik proyek yang
                          mengubah baris RATIFIKASI di file ini menjadi
                          YES + memperbarui CURRENT_AUTHORITY_INDEX:
                          IMPLEMENTATION(ARE-2) = AUTHORIZED   [TERPENUHI 2026-08-27, owner commit T4]
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
strategi trading ; penutupan ARE-0/1 formal design  => TETAP TERKUNCI.
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
CANDIDATE/BINDER : a6711d6 (ARE-1 binder) / 697b53a (ARE-1 binder final)
WAVE-CLOSE       : 697b53a (ARE-1 CLOSED @a6711d6; binder lineage)
DELEGASI ENGINEERING READ-MODE : 6958905 (DELEGASI_005 issued)
IAQ LEDGER       : ENGINEERING/IAQ_LEDGER_ARE2.md (17 entries, triase DONE)
HASH_DOMAIN_TAGS : AHFMES_ARE_HASH_DOMAIN_TAGS_ARE2.md (published)
SLICE CONTRACT   : ENGINEERING/SLICE_1_CONTRACT_ARE2.md (frozen T3)
```

## 6. Amandemen arsitek (v0.90)

```text
A1 baseline subject pin (§1B)          A2 definisi tuntas T2 + coverage minimal
A3 interaksi delegation-only (§3.5)    A4 evidence test wajib commit dengan
                                        referensi exact SHA (workflow §12)
A5 firewall restatement (§3B)          A6 typo ENGINNERING -> ENGINEERING
A7 deklarasi policy output-set baru untuk gelombang ARE-2 (§1B)
```

## 7. Integrasi ARE-1 Residual (DEFERRED items)

```text
ARE-1 DEFERRED items yang relevan ARE-2:
  - IC-5 ROLLBACK_CAUSE_OBSERVATION: ARE-2 design document dependency;
    provide requirements feedback ke ARE-1 slice-2
  - RES-03 var_ref hash: ARE-2 design assume fixed di ARE-1 slice-2;
    defensive coding untuk current state
  - RES-01 raw SQLite bypass: ARE-2 implement workaround defensif
    (file permission + process isolation); tidak claim closure
  - ARE-2 TIDAK MENYAMARKAN deferred sebagai fixed
```

## 8. Reuse Mandate (Bab 27 Grand Design)

```text
WAJIB REUSE (zero modification):
  - orchestrator.py, habitat_memory.py, evaluation_writer.py
  - pattern_events.py, pattern_recovery.py, policy_contract.py
  - freeze_snapshot.py, runtime_identity.py, telemetry.py
  - direction_discovery.py, micro_executor.py, executor_factory
  - broker transport (ARE-1 reuse)
Adapter pattern untuk setiap component; Experience Store ARE-2
package terpisah; zero modification existing code.
```