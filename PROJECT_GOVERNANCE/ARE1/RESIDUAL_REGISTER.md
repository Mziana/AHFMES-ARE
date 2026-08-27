# ARE1 — Residual Register (FIX / DEFERRED / CATAT)

Status: **REGISTER EVIDENCE-CHRONOLOGY ARE-1 / ZERO AUTHORITY / APPEND-ONLY**  
Fase: **ARE-1 Scientific Kernel** — Slice-1 `83f73c0` (HEAD `d0d24af`)  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` §6 (diary dua tingkat) + prinsip `perbaiki yang bisa, tunda yang harus, catat biar tidak lupa`  
Lokasi: `PROJECT_GOVERNANCE/ARE1/RESIDUAL_REGISTER.md` (ledger terpusat) + `DIARY/` harian + `GLOBAL_PROGRESS_DIARY.md` mirror

> Ledger ini **bukan** dokumen normatif. Ia tidak memberi PASS/CLOSED. Hanya jejak by-data agar DEFERRED tidak jadi PR lupa (G07/G18).

---

## Ringkasan eksekutif — HEAD `d0d24af` (code `83f73c0`)

| # | Tindakan | Bukti `file:line` | Commit | Verifikasi |
|---|---|---|---:|---|
| **FIX** `RES-02` hygiene | `are/storage.py:92-93` dedup `receipts_no_replace` + hapus phantom `heads_no_update` | `9ca5289` | `1 file 1+2-` · `172 passed` |
| **FIX** `RES-01` authorizer | `are/storage.py:86-87` `if action==11 or 16: return DENY` (DENY ALL DROP TABLE/TRIGGER) | `83f73c0` | `1 file 2+10-` · `TRIGGER 10` · `60bc57` dual · `136/136` |
| **DEFERRED** `IC-5` `ROLLBACK_CAUSE` | `MACHINE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V30.md:23` + `REGISTER_V30` — scope `ENGINEERING/SLICE_1_CONTRACT.md:63` `are/` only → Slice-2 ACC wajib | `d0d24af` jurnal `:28` | Owner ratified, auditor 4 otak PASS→DEFERRED |
| **DEFERRED** `RES-03` `var_ref` | `are/storage.py:229-240` `_compute_event_hash` tanpa `var_ref` → breaking migration → generasi baru | `d0d24af` jurnal `:36` | Known gap `ARE1_SELF_AUDIT_REPORT.md:45` |
| **CATAT** harian | `ARE1/DIARY/2026-08-27-ARE1-RESIDUAL-JURNAL.md:1` (73 baris) + `PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md:2026-08-27` mirror (26 baris) + `ENGINEERING/DELEGASI_003/004` | `d0d24af` 3 file `158+` | Debt `G07` persist, `G18` tidak reset |

**Manfaat pencatatan:** semua `DEFERRED` punya ticket Slice-2, semua `FIX` punya `file:line + pytest`, tidak ada PR ngambang.

---

## 1. FIX — Perbaiki yang bisa (sebelum freeze)

### RES-02 — Hygiene allowlist (DONE `9ca5289`)

```text
ID       : RES-02
KATEGORI : FIX (hygiene editorial, zero semantic change)
FILE     : are/storage.py:89-93
SEBELUM  : allowlist 12 entries (dup "receipts_no_replace" ×2 + phantom "heads_no_update")
SESUDAH  : 10 entries ("events_no_update","events_no_delete","events_no_insert_replace",
           "nonce_ledger_no_update","nonce_ledger_no_delete","receipts_no_update",
           "receipts_no_delete","receipts_no_replace","heads_no_delete","stream_heads_no_replace")
BUKTI    : git show 9ca5289 --stat 1 file 1+2-
         : grep -c "receipts_no_replace" are/storage.py → 2 total (1 allowlist + 1 trigger) bukan 3
         : grep -n "CREATE TRIGGER" are/storage.py → 10
VERIF    : python -m pytest tests/are -q → 172 passed
         : python TOOLS/manifest_hash/IMPL_A/manifest_hash_a.py --manifest .../MANIFEST_V39.md → 60bc57...
         : python TOOLS/blob_verifier/... --manifest V39 --worktree . → 136/136
QAO      : 71e50b6 (SA-11+Impact+CP1/2+Regresi triage pada 9ca5289)
JURNAL   : ARE1/DIARY/2026-08-27-ARE1-RESIDUAL-JURNAL.md:14
```

### RES-01 — Authorizer DENY ALL DROP (DONE `83f73c0`)

```text
ID       : RES-01
KATEGORI : FIX (1-2 baris, 172 hijau → perbaiki sebelum freeze)
FILE     : are/storage.py:86-87
SEBELUM  : are/storage.py:83-97 (ea0c595) if action==11 or 16: if arg1 in allowlist → DENY (12 entries dup)
SESUDAH  : are/storage.py:86-87 (83f73c0) if action==11 or 16: return DENY ALL; if action==24: DENY ATTACH
BUKTI    : git diff 71e50b6..83f73c0 --stat 1 file 2+10-
         : are/storage.py:86-87 if action == 11 or 16: return 1 # SQLITE_DENY
VERIF    : python -m pytest tests/are -q → 172 passed (28 storage +42 canonical +19 hasher +20 registry +28 evidence +22 state +13 tools)
         : grep -n "CREATE TRIGGER" are/storage.py → 10
         : EventStore DROP TRIGGER → "not authorized" (by-data)
         : raw sqlite3 DROP TRIGGER → masih bisa (heal via CREATE TRIGGER IF NOT EXISTS:104, limit SQLite)
         : manifest 60bc57 dual, blob 136/136 unchanged
QAO      : 71e50b6 → 83f73c0
JURNAL   : ARE1/DIARY/2026-08-27-ARE1-RESIDUAL-JURNAL.md:23-27
DELEGASI : ENGINEERING/DELEGASI_004_FIX_RES01_AUTHORIZER_DENY_ALL.md:29-32
STATUS   : FIXED — sisa raw bypass OS-level dicatat sebagai DEFERRED infra (di bawah)
```

---

## 2. DEFERRED — Tunda yang harus (justified, ticket Slice-2)

### IC-5 — ROLLBACK_CAUSE_OBSERVATION

```text
ID       : IC-5
KATEGORI : DEFERRED (bukan hygiene, butuh tabel baru)
SUMBER   : MACHINE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V30.md:23
           + REGISTER_V30 ROLLBACK_CAUSE_OBSERVATION
DESKRIPSI: Objek ROLLBACK_CAUSE belum ada di are/ . SoD via principal_id are/registry.py:160 sudah PASS untuk Slice-1.
ALASAN TUNDA: Scope SLICE_1_CONTRACT.md:63 are/ only. Fix butuh tabel baru + generasi hash domain baru → bukan 1 baris.
TICKET   : Slice-2 ACC wajib — implementasi ROLLBACK_CAUSE table + test G16/G17 (critic cannot rescue, research cannot self-validate)
BUKTI    : ARE1/DIARY/2026-08-27-ARE1-RESIDUAL-JURNAL.md:33-36
         : GLOBAL_PROGRESS_DIARY.md 2026-08-27 mirror
         : Debt family_debt/G18 tidak reset
AUDITOR  : Dewan 4 otak PASS observasi wording → diambil menjadi DEFERRED (1 baris)
OWNER    : ratifikasi 2026-08-27
NEXT     : Final Consistency (IC-5 wording DEFERRED) → candidate 83f73c0
```

### RES-03 — var_ref tidak di-hash

```text
ID       : RES-03
KATEGORI : DEFERRED (breaking migration → generasi baru)
FILE     : are/storage.py:229-240 _compute_event_hash(stream_id+revision+event_data+prev_hash) TANPA var_ref
DESKRIPSI: var_ref disimpan di events.var_ref tapi tidak masuk event_hash → chain tidak bind var_ref
ALASAN TUNDA: Ubah hash = ganti sidik jari semua event lama → butuh re-derive chain, migrasi DB, generasi baru HASH_DOMAIN_TAGS
TICKET   : Generasi baru / Slice-2 — ubah _compute_event_hash + re-derive chain + test deterministik + amend HASH_DOMAIN_TAGS_V1
BUKTI    : ARE1/DIARY/2026-08-27-ARE1-RESIDUAL-JURNAL.md:38-41
         : ENGINEERING/ARE1_SELF_AUDIT_REPORT.md:45 known gap
         : debt G07 retention never erases, G18 tidak hapus
STATUS   : DEFERRED — dicatat, tidak lupa
```

### RES-01 sisa — Raw sqlite3 bypass (OS-level)

```text
ID       : RES-01-sisa
KATEGORI : DEFERRED sisa (infra, bukan kode)
DESKRIPSI: per-connection authorizer (are/storage.py:83) tidak cegah proses lain buka file DB langsung via sqlite3.connect()
           then DROP TRIGGER + UPDATE events (repro verify_authorizer.py: RAW UPDATE events SUCCEEDED - bypass!)
           Heal via EventStore._init_schema CREATE TRIGGER IF NOT EXISTS:104 tapi window ada.
ALASAN TUNDA: Full fix = OS-level: chmod 600 + keeper process terpisah (IAQ-003) — infra, bukan 1 baris kode.
TICKET   : Production hardening checklist — file permission + keeper IAQ-003
BUKTI    : ARE1/DIARY/2026-08-27-ARE1-RESIDUAL-JURNAL.md:43-45
         : verify_authorizer.py log: RAW DROP TRIGGER SUCCEEDED, RAW UPDATE SUCCEEDED
STATUS   : DEFERRED infra — dicatat
```

---

## 3. CATAT — Sistem pencatatan (agar tidak PR lupa)

### Arsip dua tingkat (GOVERNANCE_FOLDER_STRUCTURE_RULES.md §6)

| Tingkat | Lokasi | Isi | Format |
|---|---|---|---|
| **Lokal ARE1** | `PROJECT_GOVERNANCE/ARE1/DIARY/` | Detail harian teknis ARE-1 | `YYYY-MM-DD-<SUBJEK>.md` |
| **Lokal ARE0** | `PROJECT_GOVERNANCE/ARE0/DIARY/` | Arsip fase 0 (9 files, tidak diubah) | — |
| **Global** | `PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md` | Indeks lintas fase, merujuk diary lokal | `## YYYY-MM-DD — <judul>` |
| **Ledger terpusat** | `PROJECT_GOVERNANCE/ARE1/RESIDUAL_REGISTER.md` | File ini — FIX/DEFERRED/CATAT dengan ticket | Tabel + text block |

### File pencatatan HEAD `d0d24af`

```text
JURNAL HARIAN : ARE1/DIARY/2026-08-27-ARE1-RESIDUAL-JURNAL.md (73 baris) — canonical
                + copy byte-identical di ARE0/DIARY/2026-08-27-ARE1-RESIDUAL-JURNAL.md (jejak S2)
GLOBAL MIRROR : PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md ## 2026-08-27 — Jurnal Harian ARE-1 (26 baris)
DELEGASI      : ENGINEERING/DELEGASI_003_HYGIENE_EA0C595_RES02.md (53 baris)
                ENGINEERING/DELEGASI_004_FIX_RES01_AUTHORIZER_DENY_ALL.md (59 baris)
LEDGER        : file ini (RESIDUAL_REGISTER.md)
QAO           : 71e50b6 (SA-11 PASS 60bc57/136 + Impact CLEAN IC-5 DEFERRED + CP1/2 PASS + Regresi 369/369)
              → 83f73c0 (fix RES-01) → d0d24af (jurnal)
```

### Template harian (untuk entri berikutnya)

```markdown
# YYYY-MM-DD — <JUDUL>
Status: **JURNAL HARIAN ARE-1 / EVIDENCE-CHRONOLOGY / ZERO AUTHORITY**
Kategori: `ARE1`
Subjek: `<commit range>` (<file:line>)

## Keputusan
TANGGAL  : YYYY-MM-DD
SUBJEK   : <commit>
DELEGASI : <nomor> <status>
PRINSIP  : perbaiki yang bisa / tunda yang harus / catat

## FIX (jika ada)
RES-XX — file:line — bukti pytest/TRIGGER/manifest

## DEFERRED (jika ada)
ID — alasan — ticket Slice-X — jejak GLOBAL_DIARY

## Snapshot
ARE-1 = ...
NEXT = ...
```

### Debt yang persist (G07/G18)

```text
G07 retention never erases debt — family_debt persist meski archival
G18 new IDs cannot reset debt — graveyard persist
→ RES-03 dan IC-5 debt tetap meski FIX RES-01, tidak hilang.
→ Ledger ini jamin DEFERRED tidak hapus debt, hanya tunda implementasi.
```

---

## 4. Verifikasi by-data HEAD

```text
HEAD     : d0d24afcdebb342d72c5ff96fa4b4181d9e6136b (code 83f73c0)
are/storage.py:86-87 DENY ALL — 1 file 2+10-
TRIGGER  : grep -n "CREATE TRIGGER" are/storage.py → 10
PYTEST   : python -m pytest tests/are -q → 172 passed
MANIFEST : python TOOLS/manifest_hash/IMPL_A/manifest_hash_a.py --manifest .../MANIFEST_V39.md → 60bc57...
BLOB     : python TOOLS/blob_verifier/... --manifest V39 --worktree . → 136/136
QAO      : 71e50b6 triage (SA-11 PASS + Impact CLEAN DEFERRED + CP1/2 PASS + Regresi 369/369)
NEXT     : Final Consistency (IC-5 wording) → candidate freeze exact SHA 83f73c0 → binder → external audit
```

---

## 5. Next — Candidate freeze

```text
SUBJEK FREEZE : 83f73c0 (HEAD d0d24af dengan jurnal)
PIPELINE      : Final Consistency → candidate exact SHA → binder → external audit
TIDAK ADA PR ngambang — semua DEFERRED punya ticket, semua FIX punya file:line
```

*Ledger ini append-only. Entri baru ditambah di bawah, histori tidak rewrite.*
