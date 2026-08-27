# Architecture Debt Register — AHFMES-ARE

```text
STATUS   = ENGINEERING RECORD / LEAD ARCHITECT / NON-NORMATIVE
DIBUAT   = 2026-08-27
SUMBER   = Deep Analysis Report 2026-08-27 (Lead Architect & Auditor)
ATURAN   = ENGINEERING/RULES.md
```

> Register ini mencatat hutang arsitektur yang diidentifikasi selama deep analysis
> tetapi **tidak dapat diperbaiki** dalam satu delegasi karena merupakan breaking
> changes atau memerlukan redesign fundamental. Setiap entri memiliki severity,
> justifikasi deferral, dan syarat penyelesaian.

---

## Ringkasan

| ID | Severity | Judul | Status | Target |
|----|----------|-------|--------|--------|
| DEBT-01 | HIGH | God Class: Registry | DEFERRED | Generasi baru |
| DEBT-02 | HIGH | God File: experience.py (43 class) | DEFERRED | Generasi baru |
| DEBT-03 | CRITICAL | DB Encapsulation Bypass via `_get_conn()` | DEFERRED | Generasi baru |
| DEBT-04 | MEDIUM | Duplikasi Konstanta state_machine ↔ registry | DEFERRED | DELEGASI_009+ |
| DEBT-05 | LOW | Folder GRAND DESIGN (spasi) | DEFERRED | Generasi baru |
| DEBT-06 | MEDIUM | Over-engineering Governance Docs | ACKNOWLEDGED | Ongoing |
| DEBT-07 | LOW | Missing pytest/coverage configuration | DEFERRED | DELEGASI_009+ |
| DEBT-08 | LOW | Missing conftest.py & fixture dedup | DEFERRED | DELEGASI_009+ |

---

## DEBT-01 — God Class: Registry (~700 baris, 8 entity types)

```text
SEVERITY     : HIGH
FILE         : are/registry.py
MASALAH      : Kelas Registry menangani seluruh lifecycle Problem, Episode,
               Hypothesis, Experiment, Candidate, Challenger, Capability, dan
               Graveyard dalam satu kelas. Textbook God Class anti-pattern.
DAMPAK       : Maintainability collapse; setiap perubahan di satu entity
               berisiko memengaruhi entity lain.
SOLUSI IDEAL : Pecah menggunakan Strategy Pattern atau module per-entity
               (registry_problem.py, registry_hypothesis.py, dst.)
ALASAN DEFER : Breaking change — semua import dan test harus diubah.
               Memerlukan generasi baru dengan slice contract terpisah.
SYARAT CLOSE : Refactor Registry ke module terpisah per entity, test coverage
               dipertahankan, zero regression.
```

## DEBT-02 — God File: experience.py (43 class dalam 1254 baris)

```text
SEVERITY     : HIGH
FILE         : are/experience.py
MASALAH      : 43 class dan dataclass dalam satu file:
               - 5 exception, 4 enum, 12 dataclass
               - ExperienceStore, AnomalyDetector, QualityGate, AuditLogger
               - KnowledgeSynthesizer, EvidenceExperienceBridge
               - CapabilityGapEngine, ScientificMemory, BatchReplayEngine, dll.
DAMPAK       : File terlalu besar untuk review efektif; coupling tinggi
               antar concern yang seharusnya terpisah.
SOLUSI IDEAL : Pecah minimal 5-7 modul:
               experience_store.py, anomaly.py, quality_gate.py,
               audit.py, capability_gap.py, replay.py, bridge.py
ALASAN DEFER : Breaking change — semua import di test dan modul lain berubah.
               Memerlukan generasi baru.
SYARAT CLOSE : Pecah file, pertahankan API publik, zero regression.
```

## DEBT-03 — DB Encapsulation Bypass via `_get_conn()`

```text
SEVERITY     : CRITICAL
FILE         : are/evidence.py, are/registry.py, are/experience.py
MASALAH      : Modul-modul ini menembus internal EventStore melalui
               self._store._get_conn() untuk menjalankan raw SQL langsung.
               EventStore gagal sebagai abstraksi — setiap consumer bisa
               bypass trigger, CAS, dan append-only enforcement.
DAMPAK       : Refactoring storage backend mustahil tanpa rewrite massal.
               Melanggar SRP dan Information Hiding.
               Security: raw SQL bisa bypass append-only trigger.
SOLUSI IDEAL : Tambahkan public API di EventStore untuk setiap operasi
               yang sekarang dilakukan via raw SQL. Hapus akses ke
               _get_conn() dari modul luar.
ALASAN DEFER : Paling invasif dari semua debt — memengaruhi 3 modul besar.
               Setiap raw SQL query harus dianalisis dan dimigrasikan.
               Memerlukan generasi baru dengan migration plan.
SYARAT CLOSE : Zero _get_conn() calls dari luar storage.py; semua operasi
               melalui public API EventStore.
```

## DEBT-04 — Duplikasi Konstanta state_machine.py ↔ registry.py

```text
SEVERITY     : MEDIUM
FILE         : are/state_machine.py, are/registry.py
MASALAH      : Kedua modul mendefinisikan set konstanta identik secara terpisah:
               PROBLEM_LIFECYCLES, PROBLEM_TRANSITIONS,
               EPISODE_LIFECYCLES, HYPOTHESIS_LIFECYCLES, dll.
DAMPAK       : Jika satu diubah tanpa yang lain, invarian sistem pecah
               secara diam-diam. Single source of truth tidak terjaga.
SOLUSI IDEAL : Buat shared constants module (are/constants.py) dan import
               dari kedua modul.
ALASAN DEFER : Tidak breaking tapi memerlukan koordinasi — cocok untuk
               DELEGASI_009 atau batch berikutnya.
SYARAT CLOSE : Satu sumber kebenaran untuk konstanta lifecycle; kedua modul
               mengimpor dari tempat yang sama.
```

## DEBT-05 — Folder GRAND DESIGN (Spasi dalam Nama)

```text
SEVERITY     : LOW
FILE         : GRAND DESIGN/ (root)
MASALAH      : Folder menggunakan spasi sementara semua folder lain
               menggunakan underscore. Menyebabkan masalah di CLI dan scripts.
DAMPAK       : Minor — path harus di-quote di shell commands.
SOLUSI IDEAL : Rename ke GRAND_DESIGN/.
ALASAN DEFER : Akan memecah referensi di dokumen beku yang menyebut
               "GRAND DESIGN/..." sebagai path. Migrasi path memerlukan
               routing table update.
SYARAT CLOSE : Rename + update semua referensi non-beku + path routing.
```

## DEBT-06 — Over-engineering Governance Documentation

```text
SEVERITY     : MEDIUM
FILE         : Seluruh PROJECT_GOVERNANCE/, ENGINEERING/
MASALAH      : Ribuan baris Markdown "hukum" (Constitution, Charter, IAQ
               Ledger, Council Protocol, dst.) tidak proporsional dengan
               ~289KB kode fungsional. Jargon tanpa kamus sentral.
DAMPAK       : Barrier masuk tinggi; Developer experience buruk.
SOLUSI IDEAL : Buat GLOSSARY.md dan ringkasan arsitektur 1 halaman.
ALASAN DEFER : Keputusan governance ini milik Owner, bukan arsitek.
               Dicatat sebagai observasi, bukan directive.
SYARAT CLOSE : Owner decision — simplifikasi atau pertahankan.
```

## DEBT-07 — Missing Pytest/Coverage Configuration

```text
SEVERITY     : LOW
FILE         : (tidak ada) — perlu pyproject.toml atau pytest.ini + .coveragerc
MASALAH      : Tidak ada konfigurasi test runner atau coverage measurement.
               214 test berjalan tapi coverage aktual tidak terukur.
DAMPAK       : Blind spots tidak terdeteksi; CI/CD tidak bisa enforce coverage.
SOLUSI IDEAL : Buat pyproject.toml dengan [tool.pytest] dan [tool.coverage].
ALASAN DEFER : Tidak urgent — test berjalan tanpa config. Cocok untuk batch.
SYARAT CLOSE : pyproject.toml ada; coverage terukur; baseline coverage tercatat.
```

## DEBT-08 — Missing conftest.py & Test Fixture Dedup

```text
SEVERITY     : LOW
FILE         : tests/are/ — perlu conftest.py
MASALAH      : Duplikasi fungsi _clean() dan _cleanup_db() di beberapa
               test files. Tidak ada shared fixtures.
DAMPAK       : Minor — maintenance overhead saat setup/teardown berubah.
SOLUSI IDEAL : Buat conftest.py dengan shared fixtures (tmp_db, cleanup, etc.)
ALASAN DEFER : Tidak urgent — test berjalan. Cocok untuk batch.
SYARAT CLOSE : conftest.py ada; duplikasi setup/teardown dieliminasi.
```

---

## Changelog

| Tanggal | Aksi | Oleh |
|---------|------|------|
| 2026-08-27 | Register dibuat, 8 entri awal dari deep analysis | Lead Architect |
