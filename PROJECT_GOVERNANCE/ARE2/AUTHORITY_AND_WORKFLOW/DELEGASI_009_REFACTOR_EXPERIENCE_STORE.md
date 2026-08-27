# DELEGASI 009 — Engineering AI: Refactor ExperienceStore Reuse EventStore (ACC-9/ACC-18 Fix)

Status: **DELEGASI AKTIF / AUTHORIZED — LEAD ARCHITECT AUDIT DIRECTIVE**
Diterbitkan: Lead Architect & Auditor · Audit ARE-2 2026-08-27 · Baseline `357b42e`

> Cara pakai: tempelkan SELURUH blok prompt di bawah ke sesi Engineering AI.
> Delegasi ini mengatasi temuan audit ARE-2 FINDING-01: ExperienceStore
> menduplikasi EventStore alih-alih reuse. ACC-9 dan ACC-18 FAIL.

---

## 📋 PROMPT UNTUK ENGINEERING AI (salin dari sini)

```text
PERAN
Kamu adalah ENGINEERING AI (bukan arsitek).
GERBANG: DELEGASI_009 — REFACTOR EXPERIENCE STORE — AUTHORIZED
HANYA untuk lingkup di bawah. Luar lingkup = DILARANG.

BASELINE
HEAD saat delegasi = 357b42e (ARE-2 Slice-1+2)
Audit finding = ACC-9 dan ACC-18 FAIL (raw SQLite mutation di ExperienceStore)

KONTEKS MASALAH
File: are/experience.py
Kelas: ExperienceStore (sekitar baris 555-710)

ExperienceStore saat ini:
  - Membuat tabel sendiri: experience_events, experience_heads
  - Menjalankan raw SQL: INSERT INTO experience_events (baris ~676)
  - Menjalankan raw SQL: UPDATE experience_heads (baris ~692)
  - TIDAK menginstansiasi EventStore dari are/storage.py
  - TIDAK menggunakan EventStore.append_event() API
  - TIDAK memiliki trigger append-only yang dimiliki EventStore

Kontrak menyatakan (SLICE_1_CONTRACT_ARE2.md §1 A1):
  "Experience Store append-only di SQLite (WAL, reuse are/storage.py)"
  "CAS per stream via WHERE last_revision=? (reuse are/storage.py)"

═══════════════════════════════════════════════════════
TUGAS: REFACTOR ExperienceStore → Reuse EventStore
═══════════════════════════════════════════════════════

LANGKAH 1: Ubah ExperienceStore.__init__
  - Buang inisialisasi tabel experience_events dan experience_heads
  - Instansiasi EventStore dari are/storage.py sebagai self._event_store
  - Gunakan db_path yang sama (atau db_path terpisah jika perlu isolasi)
  - ExperienceStore menggunakan 3 stream_id: "decision_memory", "regret_memory", "anomaly_detection"
  - EventStore sudah support multi-stream via stream_id parameter

LANGKAH 2: Ubah ExperienceStore.append()
  - Ganti raw SQL INSERT/UPDATE dengan self._event_store.append_event()
  - Map ExperienceRecord fields ke EventStore event_data format
  - Gunakan EventStore CAS (revision matching) yang sudah ada
  - Setiap stream punya head terpisah (sudah didukung EventStore)

LANGKAH 3: Ubah ExperienceStore.replay()
  - Ganti raw SQL SELECT dengan self._event_store.get_event() atau query yang sesuai
  - Maintain pure function semantics (input → output, zero side effects)

LANGKAH 4: Ubah ExperienceStore.fork_what_if()
  - Pastikan fork snapshot tetap menggunakan :memory: database (sudah ada)
  - Fork harus membuat EventStore baru di memory

LANGKAH 5: Preserve Public API
  - ExperienceStore.append(stream_type, record) → TETAP sama
  - ExperienceStore.replay(stream_type, initial_state, reducer) → TETAP sama
  - ExperienceStore.fork_what_if(...) → TETAP sama
  - ExperienceStore.get_head(stream_type) → TETAP sama
  - Semua kelas lain yang menggunakan ExperienceStore TIDAK BOLEH berubah

LANGKAH 6: Update imports
  - Tambahkan: from are.storage import EventStore (jika belum ada)

LANGKAH 7: Hapus dead code
  - Hapus CREATE TABLE experience_events dan experience_heads SQL
  - Hapus raw INSERT INTO dan UPDATE SQL di ExperienceStore
  - JANGAN hapus ExperienceStore class — hanya refactor internal

PENTING:
  - ExperienceStore sekarang menjadi WRAPPER di atas EventStore
  - EventStore menyediakan: append-only triggers, CAS, verify_chain, WAL
  - ExperienceStore menambahkan: stream routing, record mapping, replay semantics
  - Ini BUKAN penggantian ExperienceStore — ini refactor internal

KRITERIA TERIMA (fail-closed, semuanya wajib)
  ACC-D9-01 python -m pytest tests/ -q → semua test PASS (minimal 214)
  ACC-D9-02 grep "INSERT INTO experience_events" are/experience.py → 0 match
  ACC-D9-03 grep "UPDATE experience_heads" are/experience.py → 0 match
  ACC-D9-04 grep "CREATE TABLE experience_" are/experience.py → 0 match
  ACC-D9-05 grep "EventStore" are/experience.py → minimal 1 match (import/usage)
  ACC-D9-06 Replay deterministik: test_experience.py replay tests PASS
  ACC-D9-07 What-if isolation: fork_what_if tests PASS (original immutable)
  ACC-D9-08 Zero new dependency (masih stdlib only)

LARANGAN
- Jangan ubah are/storage.py (EventStore API sudah cukup)
- Jangan ubah are/canonical.py, are/evidence.py, are/registry.py, are/state_machine.py
- Jangan ubah public API ExperienceStore (hanya refactor internal)
- Jangan buat branch baru
- Jangan ubah dokumen normatif beku
- Jangan tambah dependency eksternal

PROSES
1. Baca ExperienceStore saat ini (experience.py:555-710) sepenuhnya
2. Baca EventStore API (storage.py) — pahami append_event, get_head, get_event
3. Refactor ExperienceStore → gunakan EventStore sebagai backend
4. Jalankan ALL tests → pastikan 214+ PASS
5. Verifikasi ACC-D9-01..08
6. Commit: "refactor(are2): ExperienceStore reuse EventStore — ACC-9/ACC-18 fix"
7. Report ke arsitek

DELIVERABLE
Commit di main: "refactor(are2): ExperienceStore reuse EventStore — ACC-9/ACC-18 fix (DELEGASI_009)"
Report: file berubah, test results, grep verification ACC-D9-01..08
STOP bila: API EventStore tidak cukup, test gagal, atau ragu scope → tanya arsitek.
```

---

## Catatan arsitek (di luar prompt)

- FINDING-01 dari audit ARE-2: ExperienceStore duplikasi EventStore pattern
- ACC-9 FAIL: "zero raw SQLite mutation" dilanggar oleh raw INSERT/UPDATE
- ACC-18 FAIL: sama (Slice-2 scope)
- Refactor ini seharusnya straightforward — EventStore sudah mendukung multi-stream
- Jika EventStore API tidak cukup (misal butuh query custom), Engineer boleh
  menambahkan method PUBLIC baru di EventStore — tapi itu harus dilaporkan dulu
- ExperienceStore.replay() mungkin butuh EventStore.get_events_by_stream() —
  cek apakah method ini sudah ada, jika tidak, STOP dan lapor
- DELEGASI_008 (hygiene/security) bisa dieksekusi paralel — scope tidak overlap
