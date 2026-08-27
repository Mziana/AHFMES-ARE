# DELEGASI 003 — Engineering AI: Hygiene Patch RES-02 (ea0c595 → ea0c595')

Status: **DELEGASI AKTIF / HYGIENE ONLY / ZERO-NORMATIVE-CHANGE**
Diterbitkan: Lead Architect · Subjek `ea0c59581e2f193c06d2b645b9b78d703fd847ee` (HEAD)
Baseline: `ea0c595` · Charter `22c585b RATIFIED=YES` · Slice `1d567fa` frozen
Scope: `are/` + `tests/are/` saja (`SLICE_1_CONTRACT.md:63`)

> Cara pakai: tempelkan SELURUH blok prompt di bawah ke sesi Engineering AI.
> Delegasi ini sah HANYA untuk hygiene kosmetik RES-02. DILARANG ubah semantik lain.

---

## 📋 PROMPT UNTUK ENGINEERING AI (salin dari sini)

```text
PERAN
Kamu adalah ENGINEERING AI (bukan arsitek). GERBANG: IMPLEMENTATION(ARE-1)=AUTHORIZED (22c585b) — boleh coding HANYA hygiene di bawah.

SUBJEK
HEAD = ea0c59581e2f193c06d2b645b9b78d703fd847ee (are/storage.py:84 authorizer 11 or 16, 10 triggers)
TUGAS HYGIENE RES-02 (C editorial, tidak ubah semantik):
  File: are/storage.py:83-97
  - Hapus duplikat "receipts_no_replace" kedua di are/storage.py:93 (baris allowlist kedua)
  - Hapus phantom "heads_no_update" dari allowlist are/storage.py:92 (trigger riil = heads_no_delete:190; tidak ada heads_no_update; allowlist salah)
  - Hasil allowlist harus: ("events_no_update","events_no_delete","events_no_insert_replace","nonce_ledger_no_update","nonce_ledger_no_delete","receipts_no_update","receipts_no_delete","receipts_no_replace","heads_no_delete","stream_heads_no_replace")
  - JANGAN ubah logika DENY (if arg1 in allowlist → SQLITE_DENY untuk action 11/16), JANGAN tambah DENY all, JANGAN ubah trigger.

LARANGAN
- DILARANG sentuh are/canonical.py, are/registry.py, are/evidence.py, tests/ lain, dokumen normatif PROJECT_GOVERNANCE/*, atau branch baru (README.md:17 main only)
- DILARANG klaim closure, sentuh P001/broker/produksi

VERIFIKASI WAJIB (by-data, sebelum commit)
  1. git diff --stat (harus 1 file, 2 deletions atau 1 insertion 1 deletion)
  2. python -m pytest tests/are -q → 172 passed (28 storage +42 canonical +19 hasher +20 registry +28 evidence +22 state_machine +13 tools)
  3. python TOOLS/manifest_hash/IMPL_A/manifest_hash_a.py --manifest PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V39.md → 60bc57... + TOOLS/blob_verifier/... --manifest V39 --worktree . → 136/136 (jika disentuh, buk bukti tidak ubah blob)
  4. grep -n CREATE TRIGGER are/storage.py → tetap 10
  5. grep -n receipts_no_replace are/storage.py → 1 kemunculan di allowlist + 1 trigger = 2 total (bukan 3)

DELIVERABLE
Commit hygiene di main: message "hygiene(p1): storage.py allowlist dedup + phantom heads_no_update (RES-02, ea0c595')"
Isi commit: are/storage.py saja
Laporan singkat: file:line yang diubah + output 5 verifikasi di atas
STOP bila ragu scope → tanya arsitek.
```

---

## Catatan arsitek (di luar prompt)

- RES-01 raw file bypass + RES-03 var_ref not in hash = DEFERRED (ratifikasi owner, bukan coding sekarang) — jangan sentuh.
- Setelah commit hygiene, arsitek verifikasi by-data exact SHA baru (ea0c595') → langsung SA-11→Impact→CP1/CP2→Regresi 369 (tanpa re-mint gelombang, QUARANTINE_POLICY_V9:10).
- Re-mint cap AUDIT_COLLABORATION_CHARTER.md:32 ≤2/gelombang — hygiene ini bukan re-mint normatif, tidak hitung.
```
