# DELEGASI 004 — Engineering AI: Fix RES-01 authorizer DENY ALL DROP (9ca5289→)

Status: **DELEGASI AKTIF / FIX-BEFORE-FREEZE / 1 BARIS**
Diterbitkan: Lead Architect · Subjek `71e50b6` (code `9ca5289`) · Charter `22c585b RATIFIED=YES`
Scope: `are/storage.py:83-97` saja

> Cara pakai: tempelkan SELURUH blok prompt di bawah ke sesi Engineering AI.

---

## 📋 PROMPT UNTUK ENGINEERING AI (salin dari sini)

```text
PERAN
Kamu adalah ENGINEERING AI. GERBANG: IMPLEMENTATION(ARE-1)=AUTHORIZED (22c585b) — boleh coding HANYA fix di bawah.

SUBJEK
HEAD = 71e50b6 (code subject 9ca5289 hygiene RES-02)

TUGAS FIX RES-01 (bisa diperbaiki, jangan DEFERRED lagi):
  File: are/storage.py:83-97
  Sebelum:
    if action == 11 or action == 16:
        if arg1 in ("events_no_update", ... "stream_heads_no_replace"):
            return 1  # SQLITE_DENY
    if action == 24:
        return 1
  Sesudah (DENY ALL DROP):
    if action == 11 or action == 16:  # SQLITE_DROP_TABLE (11) / SQLITE_DROP_TRIGGER (16) — DENY ALL
        return 1  # SQLITE_DENY
    if action == 24:  # SQLITE_ATTACH
        return 1
  Hapus allowlist check untuk DROP — DENY semua DROP TABLE/TRIGGER. ATTACH tetap DENY. Jangan ubah trigger lain, jangan ubah BEGIN IMMEDIATE/CAS.

LARANGAN
- DILARANG sentuh are/canonical.py, registry, evidence, PROJECT_GOVERNANCE/*, branch baru (README.md:17 main only), P001/broker
- DILARANG ubah RES-03 var_ref hash atau IC-5 (DEFERRED, dicatat di jurnal — bukan scope ini)

VERIFIKASI WAJIB (by-data, sebelum commit)
  1. git diff --stat → 1 file (are/storage.py)
  2. python -m pytest tests/are -q → 172 passed
  3. grep -n "CREATE TRIGGER" are/storage.py → 10
  4. python -c "import sqlite3; dari are.storage import EventStore; test DROP TRIGGER via EventStore → not authorized; raw sqlite3 masih bisa DROP (heal via CREATE IF NOT EXISTS) — catat"
  5. python TOOLS/manifest_hash/IMPL_A/manifest_hash_a.py --manifest PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V39.md → 60bc57

DELIVERABLE
Commit di main: message "fix(p1): storage.py authorizer DENY all DROP TABLE/TRIGGER (RES-01, 9ca5289) — perbaiki yang bisa, tunda yang harus"
Isi: are/storage.py saja
STOP bila ragu → tanya arsitek.
```

---

## Catatan arsitek (di luar prompt)

- RES-03 var_ref hash + IC-5 ROLLBACK_CAUSE = DEFERRED (harus ditunda) → dicatat di jurnal GLOBAL_PROGRESS_DIARY.md + ARE0/DIARY/2026-08-27-ARE1-RESIDUAL-DEFERRED.md (bukan PR lupa).
- RES-01 ini FIX-BEFORE-FREEZE — Owner perintahkan "perbaiki yang bisa, tunda yang harus, catat di harian" — jadi RES-01 dikerjakan sekarang, tidak ditunda.
- Re-mint cap CHARTER:32 ≤2 — hygiene+fix ini bukan re-mint normatif, tidak hitung.
```
