# DELEGASI 008 — Engineering AI: Hygiene, Security Fixes & Architecture Remediation

Status: **DELEGASI AKTIF / AUTHORIZED — LEAD ARCHITECT AUDIT DIRECTIVE**
Diterbitkan: Lead Architect · Deep Analysis 2026-08-27 · Baseline `357b42e`

> Cara pakai: tempelkan SELURUH blok prompt di bawah ke sesi Engineering AI.
> Delegasi ini sah di bawah authority Lead Architect & Auditor.
> Tidak mengubah dokumen normatif beku. Fokus: code hygiene, security fixes, structure.

---

## 📋 PROMPT UNTUK ENGINEERING AI (salin dari sini)

```text
PERAN
Kamu adalah ENGINEERING AI (bukan arsitek).
GERBANG: DELEGASI_008 — HYGIENE & SECURITY FIXES — AUTHORIZED
HANYA untuk lingkup di bawah. Luar lingkup = DILARANG.

BASELINE
HEAD saat delegasi = 357b42e (ARE-2 Slice-1 complete, 199+ tests)
Deep Analysis Report = 2026-08-27 (5 P0, 5 P1 ditemukan)

═══════════════════════════════════════════════════════
BAGIAN A — P0 CRITICAL SECURITY FIXES (wajib semua)
═══════════════════════════════════════════════════════

FIX-01  Authorizer Silent Failure
  File: are/storage.py:93-103
  Masalah: except Exception: pass — jika set_authorizer gagal, DB tanpa proteksi
  Perbaikan:
    - Hapus try/except yang menelan error
    - Biarkan set_authorizer dipanggil langsung (tanpa try/except)
    - Jika harus handle, minimal log warning ke stderr, JANGAN pass diam-diam
    - Lakukan hal yang sama di are/experience.py:584-588

FIX-02  Dead Code guard_G16
  File: are/state_machine.py (cari guard_G16_research_cannot_self_validate)
  Masalah: mengandung `if False else False: pass` — dead code, guard tidak berfungsi
  Perbaikan:
    - Implementasikan guard sesungguhnya yang menegakkan G16
    - G16 = Research TIDAK BOLEH self-validate — jika role == RESEARCH dan
      action == VALIDATE_OWN_WORK, RAISE IllegalTransition
    - Pastikan test test_state_machine.py tetap PASS

FIX-03  Dead Code guard_G12
  File: are/state_machine.py (cari guard_G12_labels_descriptive_only)
  Masalah: variabel dibaca tapi diabaikan `_ = fields.get("caller_label")`
  Perbaikan:
    - Implementasikan validasi label sesungguhnya
    - G12 = labels harus deskriptif saja, tidak boleh mengandung status resolutif
    - Jika label mengandung kata resolutif (APPROVED, REJECTED, FINAL, CONFIRMED),
      RAISE IllegalTransition
    - Pastikan test tetap PASS

FIX-04  CapabilityToken Tanpa Secret
  File: are/storage.py:816-853
  Masalah: "signature" hanya SHA-256 data publik, bisa di-forge
  Perbaikan:
    - Tambahkan parameter `secret_key: str` ke `issue_capability_token()` dan
      `CapabilityToken.is_valid()`
    - Gunakan HMAC-SHA256 dengan secret_key, bukan plain SHA-256
    - Default secret_key = "" untuk backward compat di test
    - Update test_slice2_e_residual.py jika perlu (pastikan tetap PASS)

FIX-05  Migration Tanpa Backup
  File: are/storage.py:733-801 (migrate_event_store_var_ref)
  Masalah: DELETE FROM events tanpa backup — jika crash = data hilang
  Perbaikan:
    - Sebelum migrasi, buat backup: shutil.copy2(db_path, db_path + ".backup")
    - Jika migrasi gagal (exception), restore dari backup
    - Jika migrasi sukses, hapus backup
    - Import shutil di atas file

═══════════════════════════════════════════════════════
BAGIAN B — P1 ARCHITECTURE IMPROVEMENTS
═══════════════════════════════════════════════════════

ARCH-01  Tambahkan __init__.py (package markers)
  Buat file kosong (hanya komentar "# ARE package"):
    - are/__init__.py
    - tests/__init__.py
    - tests/are/__init__.py

ARCH-02  Perkuat .gitignore
  File: .gitignore (root)
  Tambahkan baris berikut (jangan hapus yang sudah ada):
    tmp/
    .opencode/
    *.db
    *.db-wal
    *.db-shm
    *.sqlite
    .venv/
    venv/
    *.egg-info/
    dist/
    build/

ARCH-03  Path Traversal Mitigation di TOOLS
  File: SEMUA 6 file Python di TOOLS/ (IMPL_A dan IMPL_B untuk blob_verifier,
        manifest_hash, path_router)
  Perbaikan:
    - Setelah `full = os.path.join(worktree, *path.split("/"))`, tambahkan:
      ```python
      full = os.path.abspath(full)
      if not full.startswith(os.path.abspath(worktree) + os.sep):
          # path traversal attempt
          [handle as FAIL/error per tool behavior]
      ```
    - Pastikan test_tools.py tetap PASS

ARCH-04  Authorizer Magic Numbers → Named Constants
  File: are/storage.py dan are/experience.py
  Perbaikan:
    - Di atas file, tambahkan:
      ```python
      SQLITE_DROP_TABLE = 11
      SQLITE_DROP_TRIGGER = 16
      SQLITE_ATTACH = 24
      ```
    - Ganti magic number 11, 16, 24 dengan named constants

═══════════════════════════════════════════════════════
BAGIAN C — HYGIENE CLEANUP
═══════════════════════════════════════════════════════

HYG-01  Hapus branch temp-accept
  Jalankan: git branch -d temp-accept

HYG-02  Pindahkan fix scripts ke tmp/
  Pindahkan:
    - fix_manifest_residual.py → tmp/fix_manifest_residual.py
    - fix_manifest_self.py → tmp/fix_manifest_self.py
  (Atau hapus jika sudah tidak diperlukan — tanya arsitek jika ragu)

HYG-03  Update TOOLS/README.md status
  File: TOOLS/README.md
  Ganti baris yang menyatakan "BELUM ADA IMPLEMENTASI" dengan:
    MANIFEST_HASH = TERSEDIA (IMPL_A, IMPL_B) — LULUS UJI DUAL-IMPL
    BLOB_VERIFIER = TERSEDIA (IMPL_A, IMPL_B) — LULUS UJI DUAL-IMPL
    PATH_ROUTER   = TERSEDIA (IMPL_A, IMPL_B) — LULUS UJI DUAL-IMPL

HYG-04  Commit uncommitted work
  Stage dan commit semua perubahan yang sudah selesai sebelum FIX dimulai:
    git add -A
    git commit -m "chore(hygiene): commit outstanding ARE-2 Slice-2 work before DELEGASI_008 fixes"

HYG-05  Clean __pycache__
  Hapus semua __pycache__ directories yang ter-track:
    git rm -r --cached are/__pycache__/ tests/are/__pycache__/ 2>/dev/null
  (Sudah ter-gitignore, tapi mungkin ter-track di git)

KRITERIA TERIMA (fail-closed, semuanya wajib)
  ACC-D8-01 python -m pytest tests/ -q → semua test PASS (minimal 214)
  ACC-D8-02 git branch → hanya main
  ACC-D8-03 find -name "__init__.py" di are/ dan tests/ → 3 file
  ACC-D8-04 git status → clean working tree
  ACC-D8-05 grep "BELUM ADA" TOOLS/README.md → 0 match
  ACC-D8-06 grep "except Exception" are/storage.py → 0 match di authorizer
  ACC-D8-07 tidak ada fix_*.py di root directory

LARANGAN
- Jangan ubah dokumen normatif beku (MANIFEST, CONTRACTS, MACHINE, CONSTITUTION)
- Jangan ubah are/evidence.py atau are/registry.py (di luar scope)
- Jangan buat branch baru
- Jangan ubah test behavior — hanya fix source code
- Jangan tambah dependency eksternal

PROSES
Urutan: HYG-04 (commit dulu) → Bagian A → Bagian B → Bagian C (sisanya)
→ verifikasi ACC-D8-01..07 → commit → report ke arsitek

DELIVERABLE
Commit di main: "fix(delegasi-008): hygiene + security fixes + architecture remediation"
Report: daftar file berubah, test results, issues jika ada
STOP bila: ragu scope, butuh ubah normatif, atau test gagal.
```

---

## Catatan arsitek (di luar prompt)

- Deep analysis 2026-08-27 menemukan 5 P0, 5 P1, 7 P2 issues
- Items DEFERRED (tidak masuk delegasi ini):
  - God Class Registry (~700 baris) → perlu refactor besar, generasi baru
  - God File experience.py (43 class) → perlu refactor besar, generasi baru
  - DB encapsulation bypass via _get_conn() → breaking change, perlu migration plan
  - Duplikasi konstanta state_machine.py ↔ registry.py → perlu shared module
  - Rename GRAND DESIGN → GRAND_DESIGN → akan pecah referensi dokumen beku
- Items DEFERRED dicatat di ENGINEERING/ARCH_DEBT_REGISTER.md
- Delegasi ini TIDAK memerlukan Charter baru — ini hygiene/fix, bukan fitur baru
- FIX-04 (HMAC) backward compatible via default empty secret
