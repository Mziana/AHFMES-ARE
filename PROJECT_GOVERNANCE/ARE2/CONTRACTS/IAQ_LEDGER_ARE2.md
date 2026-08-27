# IAQ LEDGER - Implementability Questions (Engineering AI) - ARE-2 Experience Intelligence

```text
STATUS   = ENGINEERING DELIVERABLE / DELEGASI_005 / ZERO AUTHORITY
DIBUAT   = 2026-08-27
SUBJEK   = HEAD 6958905 (ARE-1 CLOSED @a6711d6, ARE-2 AUTHORIZED @267a1a4)
SCOPE    = Read-mode analysis only; recommendations below are not decisions.
ATURAN   = ENGINEERING/RULES.md; DELEGASI_005_ARE2_READMODE_IAQ.md
```

> Ledger ini adalah evidence/chronology untuk triase Lead Architect. Ia tidak
> memberi implementation authority, tidak mengubah dokumen normatif, tidak
> menjawab P001, dan tidak memilih strategi trading.

**TRIASE LEAD ARCHITECT — HASIL: 17/17 ANSWERED-WITH-CLAUSE**

| ID | DISPOSISI | KEPUTUSAN ARSITEK |
|----|-----------|-------------------|
| IAQ-001 | ANSWERED-WITH-CLAUSE | TERIMA (a) — reuse EventStore 3 stream |
| IAQ-002 | ANSWERED-WITH-CLAUSE | TERIMA (a)+(b) — ingestion + middleware |
| IAQ-003 | ANSWERED-WITH-CLAUSE | TERIMA (a) — deterministic threshold, fixed-seed |
| IAQ-004 | ANSWERED-WITH-CLAUSE | TERIMA (a)+(b) — pure replay + fork snapshot |
| IAQ-005 | ANSWERED-WITH-CLAUSE | TERIMA (a)+(c) — derived snapshots + Owner approval |
| IAQ-006 | ANSWERED-WITH-CLAUSE | TERIMA (a) — consumer via reservation API |
| IAQ-007 | ANSWERED-WITH-CLAUSE | TERIMA (a) — adapter pattern, zero mod |
| IAQ-008 | ANSWERED-WITH-CLAUSE | TERIMA (a)+(b) — gates + quarantine + review |
| IAQ-009 | ANSWERED-WITH-CLAUSE | TERIMA (a) — rule-based CF mapping |
| IAQ-010 | ANSWERED-WITH-CLAUSE | TERIMA (a) — reuse EventStore 2 stream |
| IAQ-011 | ANSWERED-WITH-CLAUSE | TERIMA (a) — import ARE-1 storage API |
| IAQ-012 | ANSWERED-WITH-CLAUSE | TERIMA (a)+(b) — observability only, NO emergency-flat |
| IAQ-013 | ANSWERED-WITH-CLAUSE | TERIMA (a)+(c) — config bounds + quota |
| IAQ-014 | ANSWERED-WITH-CLAUSE | TERIMA (a)+(b) — JSONL audit + dual-check |
| IAQ-015 | ANSWERED-WITH-CLAUSE | TERIMA (a) — frozen typed config, hash via canonical |
| IAQ-016 | ANSWERED-WITH-CLAUSE | TERIMA (a)+(b)+(c) — tags + IAQ QAO + triase→contract→charter |
| IAQ-017 | ANSWERED-WITH-CLAUSE | TERIMA (a)+(b)+(c) — dependency doc + feedback + defensive |

**HASIL: 17/17 ANSWERED-WITH-CLAUSE — 0 NEEDS-NEW-GENERATION, 0 DEFERRED, 0 BLOCKER**

## IAQ-001 - Experience Store Schema & Storage

```text
PERTANYAAN : Struktur data apa yang merealisasikan decision memory, regret memory, dan anomaly detection secara append-only, content-addressed, dan replayable?
KLAUSE     : GRAND DESIGN/AHFMES_ARE_GRAND_DESIGN_V1.md#Bab 27; are/storage.py; Matrix V30 IC-4
MENGAPA    : Schema yang salah dapat merusak replay deterministik, audit trail, dan batas memory.
OPSI-JAWAB : (a) Reuse EventStore dengan stream terpisah; (b) file content-addressed log; (c) embedded KV baru dengan justifikasi.
USULAN     : (a), dengan CAS per stream dan test recovery dari committed rows.
```

## IAQ-002 - Market Data Provenance & As-Of Timestamps

```text
PERTANYAAN : Bagaimana setiap market/news event membawa provenance as-of lengkap dan terlindung dari manipulasi retroaktif?
KLAUSE     : GRAND DESIGN V1#Bab 13 dan Bab 18; are/evidence.py; REGISTER V30
MENGAPA    : Provenance tidak lengkap membuat information-time dan backtest tidak valid.
OPSI-JAWAB : (a) ingestion menghasilkan record provenance; (b) middleware memaksa validasi; (c) post-hoc reconstruction (dilarang).
USULAN     : (a)+(b), fail-closed bila field wajib kosong.
```

## IAQ-003 - Deterministic Anomaly Detection

```text
PERTANYAAN : Bagaimana regime shift, spread hostility, dan counterfactual quality dideteksi secara deterministik dan reproducible?
KLAUSE     : GRAND DESIGN V1#Bab 18; are/evidence.py COUNTERFACTUAL_QUALITIES; REGISTER V30
MENGAPA    : Hasil berbeda antar-run akan membuat keputusan dan audit tidak reproducible.
OPSI-JAWAB : (a) threshold deterministik; (b) model ber-seed dan artifact versioned; (c) hybrid.
USULAN     : (a) untuk MVP; setiap artifact model harus content-addressed bila kelak dipakai.
```

## IAQ-004 - Deterministic Replay & What-If

```text
PERTANYAAN : Bagaimana replay menghasilkan output identik dan what-if tidak mengubah state asli?
KLAUSE     : GRAND DESIGN V1#Bab 27 dan Bab 33; are/storage.py verify_chain; Matrix V30 IC-4
MENGAPA    : Replay nondeterministik atau mutasi state asli merusak bukti dan simulasi.
OPSI-JAWAB : (a) pure replay function; (b) fork snapshot lalu discard; (c) time-travel state hash.
USULAN     : (a)+(b), dengan original state immutable dan fork terpisah.
```

## IAQ-005 - Knowledge Synthesis & Capability Gap

```text
PERTANYAAN : Bagaimana scientific memory dan capability-gap assessment dibuat berbasis evidence tanpa bias atau synthesis nondeterministik?
KLAUSE     : GRAND DESIGN V1#Bab 6 dan Bab 33; are/registry.py; REGISTER V30
MENGAPA    : Knowledge tanpa evidence dapat menggelembungkan capability gap dan menghabiskan budget.
OPSI-JAWAB : (a) derived Evidence snapshots + deterministic rules; (b) LLM synthesis; (c) human review.
USULAN     : (a)+(c); LLM tidak menjadi sumber keputusan authority.
```

## IAQ-006 - Evidence Ledger Integration

```text
PERTANYAAN : Bagaimana Experience Store mengonsumsi Evidence Ledger ARE-1 tanpa exposure leak, holdout contamination, atau reset ancestry?
KLAUSE     : GRAND DESIGN V1#Bab 17-18; are/evidence.py; ARE1/RESIDUAL_REGISTER.md
MENGAPA    : Integrasi yang salah dapat menjadikan evidence turunan seolah-olah evidence independen.
OPSI-JAWAB : (a) consumer melalui reservation API dan derivative parent roots; (b) tabel bersama dengan foreign key; (c) proses IPC.
USULAN     : (a) untuk desain awal; setiap exposure dan parent root wajib dipertahankan.
```

## IAQ-007 - Reuse Existing Components

```text
PERTANYAAN : Bagaimana orchestrator.py, habitat_memory.py, dan evaluation_writer.py direuse tanpa membuat komponen kedua?
KLAUSE     : GRAND DESIGN V1#Bab 27; AHFMES_ARE_SOURCE_REUSE_AND_WORKTREE_HYGIENE.md
MENGAPA    : Duplikasi dapat memecah telemetry, persistence, dan audit boundary.
OPSI-JAWAB : (a) adapter; (b) migrasi bertahap; (c) fork/modify komponen kedua (dilarang).
USULAN     : (a), setelah interface dan ketersediaan source dikonfirmasi oleh arsitek.
```

## IAQ-008 - Observability & Data Quality Gates

```text
PERTANYAAN : Gate deterministik apa yang menolak market data tidak lengkap, terlambat, atau provenance-invalid sebelum masuk Experience Store?
KLAUSE     : GRAND DESIGN V1#Bab 13 dan Bab 33; are/evidence.py; REGISTER V30
MENGAPA    : Data buruk menghasilkan anomaly dan decision memory yang tidak dapat dipercaya.
OPSI-JAWAB : (a) completeness/latency/schema/provenance gates; (b) quarantine statistik; (c) review manual.
USULAN     : (a)+(b), dengan metrics dan audit record; review manusia bukan bypass gate.
```

## IAQ-009 - Counterfactual Quality

```text
PERTANYAAN : Bagaimana CF-HIGH, CF-MEDIUM, CF-LOW, dan CF-UNOBSERVABLE ditentukan secara auditable?
KLAUSE     : GRAND DESIGN V1#Bab 18; are/evidence.py COUNTERFACTUAL_QUALITIES; REGISTER V30
MENGAPA    : Kualitas counterfactual yang tidak konsisten membuat anomaly tidak comparable.
OPSI-JAWAB : (a) rule-based mapping; (b) ML-based; (c) human assertion.
USULAN     : (a), dengan mapping anomaly type yang dibekukan dan dapat diaudit.
```

## IAQ-010 - Decision & Regret Memory

```text
PERTANYAAN : Bagaimana decision memory dan regret memory disimpan append-only, content-addressed, dan dapat diverifikasi ulang?
KLAUSE     : GRAND DESIGN V1#Bab 16 dan Bab 27; are/storage.py; Matrix V30 IC-4
MENGAPA    : Memory yang berubah atau tidak dapat direplay membuat regret dan evaluasi historis tidak valid.
OPSI-JAWAB : (a) EventStore streams; (b) tabel terpisah; (c) embedded pada schema Experience Store.
USULAN     : (a), dengan CAS, verify_chain, dan domain hash yang ditentukan sebelum coding.
```

## IAQ-011 - Replay Integration Boundary

```text
PERTANYAAN : Bagaimana replay engine ARE-2 memakai EventStore ARE-1 tanpa dependency cycle atau source authority baru?
KLAUSE     : are/storage.py; GRAND DESIGN V1#Bab 27; ENGINEERING/RULES.md E-05
MENGAPA    : Dependency cycle atau library kedua dapat memecah determinisme dan governance boundary.
OPSI-JAWAB : (a) ARE-2 import API ARE-1; (b) shared library baru; (c) IPC.
USULAN     : (a), dengan dependency direction satu arah dan baseline SHA terdokumentasi.
```

## IAQ-012 - Anomaly Alerting & Notification

```text
PERTANYAAN : Bagaimana anomaly alert dibuat deterministic, deduplicated, dan tercatat tanpa diam-diam menjadi ACT atau capital action?
KLAUSE     : GRAND DESIGN V1#Bab 13, Bab 27, dan Bab 33; are/evidence.py
MENGAPA    : Alert tanpa audit trail dapat spam atau kehilangan kejadian penting; trigger ACT dapat melanggar firewall.
OPSI-JAWAB : (a) threshold/cooldown/dedup + audit log; (b) notification adapter; (c) automatic emergency-flat action.
USULAN     : (a)+(b) hanya sebagai observability; opsi (c) memerlukan authority dan kontrak terpisah, bukan keputusan IAQ.
```

## IAQ-013 - Performance & Resource Bounds

```text
PERTANYAAN : Batas memory, CPU, latency, replay size, dan what-if workload apa yang dibekukan sebelum implementasi?
KLAUSE     : GRAND DESIGN V1#Bab 13; CSK references; SC-06 finite budget
MENGAPA    : Resource tak terbatas dapat menyebabkan OOM, timeout, dan perilaku operasional yang tidak dapat direproduksi.
OPSI-JAWAB : (a) config-driven bounds; (b) streaming/chunking; (c) quota per component.
USULAN     : (a)+(c), dengan rejection fail-closed dan metrics terlog.
```

## IAQ-014 - Auditor Reproducibility

```text
PERTANYAAN : Artefak apa yang membuat setiap operasi ARE-2 dapat direproduksi auditor dari exact SHA, input hash, output hash, dan parameter hash?
KLAUSE     : AUDIT_COLLABORATION_CHARTER.md; ENGINEERING/RULES.md E-01/E-06/E-08; TOOLS specs
MENGAPA    : Tanpa audit trail deterministic, external auditor tidak dapat memverifikasi hasil.
OPSI-JAWAB : (a) structured JSONL audit log; (b) deterministic output and dual checks; (c) future manifest integration.
USULAN     : (a)+(b); manifest generation baru hanya melalui governance.
```

## IAQ-015 - Configuration & Version Management

```text
PERTANYAAN : Bagaimana konfigurasi ARE-2 di-version, di-hash, divalidasi, dan dibuat immutable selama runtime?
KLAUSE     : GRAND DESIGN V1#Bab 13 dan Bab 27; are/canonical.py; REGISTER V30
MENGAPA    : Config mutable merusak reproducibility, rollout safety, dan audit.
OPSI-JAWAB : (a) frozen typed config; (b) validated JSON/YAML; (c) environment variables untuk secret saja.
USULAN     : (a), dengan canonical hash dan load-once semantics.
```

## IAQ-016 - ARE-2 Slice Contract Prerequisites

```text
PERTANYAAN : Prasyarat apa yang harus selesai sebelum Slice-1 ARE-2 dapat ditulis dan diratifikasi?
KLAUSE     : ENGINEERING/SLICE_1_CONTRACT.md#P-1; IMPLEMENTATION_AUTHORITY_CHARTER.md#T2-T4; HASH_DOMAIN_TAGS V1
MENGAPA    : Coding tanpa tag, ledger, slice contract, dan charter yang jelas akan menghasilkan rework dan authority ambiguity.
OPSI-JAWAB : (a) appendix domain tags; (b) IAQ ledger sebagai QAO; (c) triase -> slice contract -> charter.
USULAN     : (a)+(b)+(c), seluruhnya harus selesai sebelum coding ARE-2.
```

## IAQ-017 - ARE-1 Deferred Residual Integration

```text
PERTANYAAN : Bagaimana ARE-2 memperlakukan IC-5 ROLLBACK_CAUSE, RES-03 var_ref hash, dan raw SQLite bypass yang masih deferred?
KLAUSE     : PROJECT_GOVERNANCE/ARE1/RESIDUAL_REGISTER.md; ARE1/DIARY/2026-08-27-ARE1-RESIDUAL-JURNAL.md
MENGAPA    : Mengabaikan residual dapat membuat ARE-2 bergantung pada fondasi yang belum lengkap.
OPSI-JAWAB : (a) dependency eksplisit pada Slice-2; (b) requirement feedback untuk ARE-1; (c) defensive mitigation tanpa mengklaim closure.
USULAN     : (a)+(b)+(c) secara terbatas; ARE-2 tidak boleh menyamarkan deferred menjadi fixed.
```

## Penutup

```text
JUMLAH ENTRI = 17
TRIASE       = SELESAI — 17/17 ANSWERED-WITH-CLAUSE
DISPOSISI    = 17 ANSWERED-WITH-CLAUSE, 0 NEEDS-NEW-GENERATION, 0 DEFERRED, 0 BLOCKER
STATUS       = ZERO AUTHORITY / READ-MODE / NON-NORMATIF / TRIASE SELESAI
NEXT         = Slice Contract ARE-2 → Charter T4 → DELEGASI_006 coding
LARANGAN     = Tidak coding, tidak mengubah dokumen normatif, tidak menjawab P001,
               tidak memilih strategi trading atau ACT behavior.
```

## Template Triase Lead Architect

| ID | DISPOSISI | KEPUTUSAN ARSITEK |
|---|---|---|
| IAQ-001 | [ ] | |
| IAQ-002 | [ ] | |
| IAQ-003 | [ ] | |
| IAQ-004 | [ ] | |
| IAQ-005 | [ ] | |
| IAQ-006 | [ ] | |
| IAQ-007 | [ ] | |
| IAQ-008 | [ ] | |
| IAQ-009 | [ ] | |
| IAQ-010 | [ ] | |
| IAQ-011 | [ ] | |
| IAQ-012 | [ ] | |
| IAQ-013 | [ ] | |
| IAQ-014 | [ ] | |
| IAQ-015 | [ ] | |
| IAQ-016 | [ ] | |
| IAQ-017 | [ ] | |
