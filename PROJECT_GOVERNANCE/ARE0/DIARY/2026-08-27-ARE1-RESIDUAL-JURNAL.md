# 2026-08-27 — ARE-1 Residual Jurnal: Perbaiki yang Bisa, Tunda yang Harus (Harian)

Status: **JURNAL HARIAN ARE-1 / EVIDENCE-CHRONOLOGY / ZERO AUTHORITY**
Kategori: `ARE1 + ENGINEERING + GLOBAL`
Subjek: `71e50b6 → 83f73c0` (are/storage.py RES-01 fix)

---

## Keputusan Lead Architect (owner: perbaiki yang bisa, tunda yang harus, catat)

```text
TANGGAL  : 2026-08-27
SUBJEK   : 9ca5289 (hygiene RES-02) → 83f73c0 (fix RES-01)
DELEGASI : 003 hygiene RES-02 DONE (9ca5289), 004 fix RES-01 DONE (83f73c0)
AUDITOR  : Dewan 4 otak PASS (1 observasi wording IC-5 PASS→DEFERRED) — diambil
OWNER    : ratifikasi DEFERRED (IC-5, RES-01→FIXED, RES-03)
PRINSIP  : perbaiki yang bisa (1-2 baris, 172 tests hijau), tunda yang harus (breaking/generasi baru) + catat agar tidak jadi PR lupa (G07/G18 debt persist)
```

### Apa yang DIPERBAIKI sekarang (sebelum freeze)

```text
RES-01 raw file bypass — are/storage.py:83-88
  SEBELUM: if action==11 or 16: if arg1 in allowlist (12 entries dup+phantom) → DENY
  SESUDAH: if action==11 or 16: return DENY ALL (are/storage.py:86-87) + ATTACH DENY
  BUKTI  : git diff 83f73c0 --stat 1 file, 2+10-, pytest 172 passed, grep TRIGGER 10, manifest 60bc57 dual, blob 136/136
  DAMPAK : EventStore DROP via koneksi resmi kini 100% DENY; raw sqlite3 bypass masih heal via CREATE TRIGGER IF NOT EXISTS:104 (limit SQLite, bukan bug kode)
```

### Apa yang DITUNDA dengan alasan (DEFERRED justified) — tidak lupa, dicatat

```text
IC-5 ROLLBACK_CAUSE (MATRIX_V30:23, REGISTER_V30) — DEFERRED
  ALASAN: objek ROLLBACK_CAUSE_OBSERVATION belum di are/ (scope SLICE_1_CONTRACT:63 are/ only). SoD via principal_id are/registry.py:160 sudah PASS untuk Slice-1. Fix butuh tabel baru + generasi baru — bukan hygiene.
  CATAT : wajib ACC Slice-2 Contract (ARE-1 lanjutan) — tuntut implementasi objek + test G16/G17.
  JEJAK : GLOBAL_PROGRESS_DIARY.md 2026-08-27 + file ini + debt map family_debt

RES-03 var_ref tidak di-hash are/storage.py:229-240 — DEFERRED
  ALASAN: _compute_event_hash(stream_id+revision+event_data+prev_hash) tanpa var_ref. Ubah = ganti sidik jari semua event lama → breaking migration, butuh generasi baru hash domain. Sudah diakui ARE1_SELF_AUDIT_REPORT.md:45 sebagai known gap Slice-2.
  CATAT : wajib Slice-2/Generasi baru — ubah hash + re-derive chain, test deterministik.
  JEJAK : jurnal ini + GLOBAL_PROGRESS_DIARY.md + debt tidak hapus G07

RES-01 sisa raw bypass via raw sqlite3 file — DEFERRED sisa (OS-level)
  ALASAN: per-connection authorizer tidak bisa cegah proses lain buka file langsung (limit SQLite). Full fix = file chmod 600 + proses penjaga terpisah IAQ-003 — infra, bukan 1 baris.
  CATAT : production hardening checklist — file permission + keeper process
```

### Pencatatan (agar tidak PR lupa)

```text
JURNAL HARIAN : file ini (ARE0/DIARY/2026-08-27-ARE1-RESIDUAL-JURNAL.md)
GLOBAL DIARY  : PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md 2026-08-27 (mirror)
DELEGASI      : ENGINEERING/DELEGASI_003 + 004 (jejak by-data)
QAO           : 71e50b6 (SA-11+Impact+CP1/2+Regresi) → 83f73c0 (fix)
DEBT          : family_debt/G18 tidak reset, graveyard persist — G07 retention never erases debt
NEXT          : Final Consistency (IC-5 wording DEFERRED) → candidate freeze exact SHA 83f73c0 → binder → external audit
```

---

## Snapshot status saat entry ini

```text
ARE-0 CLOSED              = YES @03aec99 (ROOT 3affbbf0)
ARE-1 Scientific Kernel   = IN PROGRESS — Slice-1 done 83f73c0 (hygiene+RES-01), SA-11 PASS, Impact CLEAN (IC-5 DEFERRED), CP1/2 PASS, Regresi 369/369 (172 tests), QAO 71e50b6→83f73c0
ARE-2 Experience Intel    = LOCKED
ARE-3 Autonomous Science  = LOCKED
ARE-4 Governed Evolution  = LOCKED
IMPLEMENTATION(ARE-1)     = AUTHORIZED (22c585b)
P001                      = NOT AUTHORIZED
PRODUCTION                = CLOSED
EPHEMERAL AGENTS          = 5 file .opencode/agent/*-ephemeral.md (mode:subagent, 4/5 edit:deny) — hapus belakangan
```
