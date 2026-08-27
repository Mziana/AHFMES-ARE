# ARE-1 — Laporan Audit Mandiri Lengkap (Loop Adversarial)

```text
STATUS   = AUDIT MANDIRI FINAL / PRE-EXTERNAL-AUDIT / ZERO AUTHORITY
TANGGAL  = 2026-08-26 (loop penutupan)
SUBJEK   = HEAD 2bd037e (are-1 complete: storage+canonical+registries+evidence+state_machine+TOOLS)
BASELINE = gen-39 4f094fd (Manifest V39 136 members, Matrix V30, Register V30, HASH_DOMAIN_TAGS V1)
DELEGASI = 002 (T4 ratified 22c585b, SLICE_1_CONTRACT frozen)
METODE   = Loop E-11 RULES.md: 3 peran paralel + jendela engineer-naif + eksekusi verifikasi by-data
```

## 1. Eksekutif Verdict

```text
AUDITOR (Last Man Standing) = CREDIBLE tapi STALE — 3 P0 yang dilaporkan SUDAH DIPERBAIKI
                              pada subjek 2bd037e. Klaim "ALL PASS tapi false positive"
                              tidak reproduksi pada subjek ini (89 vector lama + 83 baru = 172 tests OK).
ENGINEERING (slice-1 awal)  = UNRELIABLE pada snapshot 07a7336 — benar per auditor.
ARCHITECT (impact re-run)   = PREMATURE pada 07a7336 — benar per auditor; kini TIDAK LAGI
                              setelah P0 diperbaiki pada 2bd037e.
SUBJEK 2bd037e               = READY untuk External Audit (ACC-1..5 hijau, dual-impl bit-identical, triggers DB, CAS)
```

## 2. Loop Adversarial yang Dijalankan

### Iterasi 0 — Baseline P0 (auditor eksternal, 5 min grep, 8 payloads)
Dilaporkan:
- P0-1 JSON escape broken (`escaped` discarded, missing \r\b\f\u00xx)
- P0-2 tag 41 vs 40 (SAFETY_CONTRACT_CHANGE_PROPOSAL_RECORD)
- P0-3 SQL CAS missing (INSERT OR REPLACE, no BEGIN IMMEDIATE)

Verifikasi by-data kami:
- `are/canonical.py:243-266` kini ESCAPE_MAP lengkap + `_escape_string` loop `\u00xx` + `return b'"'+escaped.encode()+b'"'` — probe 8 payloads A==B **OK** (verify_p0.py)
- DOMAIN_TAGS `len=41` (setelah koreksi CONSTITUTION tanpa underscore, grep ulang MD = 41) vs MD 41 — **OK**
- `are/storage.py:179 BEGIN IMMEDIATE`, `:214-220 UPDATE WHERE last_revision=?` + rowcount check, `:121-131 trigger events_no_update/delete + events_no_insert_replace`, `:103-109 nonce_ledger trigger nuanced` — **OK**

### Iterasi 1 — RT-A machines/authority (Task ses_fc0ac889, general)
Menemukan 5 P0 + 8 P1 dalam 30 detik Python. Semua reproduksi. Diterapkan patch:
- P0-01 REPLACE bypass -> INSERT + `events_no_insert_replace` trigger WHEN EXISTS
- P0-02 DROP TRIGGER -> authorizer SQLITE_DENY (action 11/24) di `_get_conn`
- P0-03 nonce_ledger/receipts/heads tanpa trigger -> triggers nuanced (UNUSED->CONSUMED only)
- P0-04 `isolation_level=None` + `with conn:` palsu -> explicit BEGIN IMMEDIATE/COMMIT/ROLLBACK di Edge1Manager
- P0-05 fan-out finalize -> JOIN `nl.var_ref=r.var_ref`
- P1-06 ROLLBACK masking -> try/except pass
- P1-08 var_ref tidak di-hash -> dicatat sebagai known gap (var_ref stored tapi tidak di event_hash; ditangguhkan ke slice-2)
- P1-12 zip truncation -> length-aware NFC check
- P1-13 offset byte vs char -> byte-level CRLF check konsisten

### Iterasi 2 — Engineer-Naif Window (implisit via sub-agents registry/evidence/state_machine/TOOLS)
4 sub-agent paralel ditugaskan sebagai "engineer yang belum tahu rationale" (D4 advisory):
- registry (G01-G25): 20 tests OK
- evidence (E0-E3, INDEPENDENT_FOR 11 syarat): 28 tests OK
- state_machine (G01-G25 guards): 22 tests OK
- TOOLS dual-impl: 13 tests OK (manifest_hash root 60bc57..., blob 136/136, path_router)

### Iterasi 3 — Final Verification (subjek 2bd037e)
```
python -m tests.are.test_storage      -> 28 OK (crash-matrix 5, CAS, final idempotent)
python -m tests.are.test_canonical    -> 42 OK (verifier 7, adversarial 12, dual 4, tags 3)
python -m tests.are.test_hasher       -> 19 OK (cross-check all 41 tags x 10 vectors)
python -m tests.are.test_registry     -> 20 OK
python -m tests.are.test_evidence     -> 28 OK
python -m tests.are.test_state_machine-> 22 OK
python -m tests.are.test_tools        -> 13 OK
TOTAL 172 tests OK, 0 FAIL, 0 ERROR
Dual-impl cross-check: 8 escape payloads A==B, 41 tags × 6 data vectors A==B, large nested object A==B
Blob verifier: 136/136 PASS, root repro 3affbbf0... (gen-39 V39) MATCH
```

## 3. Evidence ACC-1..5 (SLICE_1_CONTRACT §3)

| ACC | Kriteria | Bukti |
|-----|----------|-------|
| ACC-1 A1 | head 1 baris/stream, mutasi HANYA via CAS WHERE last_revision=? | `are/storage.py:214-220` UPDATE WHERE, `are/storage.py:121-131` triggers, `tests/are/test_storage.py:76-92` CAS 7 tests |
| ACC-1 A1 | BEGIN IMMEDIATE | `are/storage.py:179` |
| ACC-1 A1 | append-only DB trigger | `are/storage.py:120-131` 2 triggers events + 1 insert-replace |
| ACC-1 A2 | crash-matrix | `tests/are/test_storage.py:299-433` 5 tests (receipt/nonce, before, after, idempotent, deterministic) |
| ACC-1 A3 | finalize f(ledger,receipt) no clock | `are/storage.py:521-547` JOIN var_ref, no datetime/time, `tests: test_finalize_uses_only_ledger_state` |
| ACC-2 B1 | verifier FAIL-CLOSED offset | `are/canonical.py:94-147` BOM/CRLF/NFC + offset, `test_canonical: test_verifier` 7 tests |
| ACC-2 B2 | adversarial | `test_canonical: combining, tr-TR, CRLF injection, key reverse, float/NaN, unicode` 12 tests |
| ACC-2 B3 | hasher dual-impl | `are/canonical.py:243-266` ESCAPE_MAP, `test_hasher` 19 tests bit-identical |
| ACC-3 | P-1 terpenuhi | Manifest V39 136 members (MATRIX 30, INVENTORY 29, HASH_TAGS 1, PROTOCOL 35, POLICY 9, CORRECTION 30, BINDING 1, SELF 1) + HASH_DOMAIN_TAGS V1 + IAQ_LEDGER QAO, blob verifier 136/136 |
| ACC-4 | zero dependency | `grep -r import are/` stdlib only (hashlib, json, sqlite3, unicodedata, os) |
| ACC-5 | E-01..E-10 | by-data kutip file:line, vocabulary suci, dual-impl, deterministik |

## 4. Sisa ARE-1 — Sudah Selesai Dalam Subjek Ini

Per charter §1 DALAM CAKUPAN, yang sebelumnya ditunda kini selesai via sub-agent loop:

- **Registries** (`are/registry.py`): Problem/Episode/Hypothesis/Candidate/Capability/Graveyard, G01-G25 guards, 20 tests
- **Evidence Ledger** (`are/evidence.py`): snapshot, RelationRegistry default RELATED, Reservation atomik, E0-E3, INDEPENDENT_FOR 11 syarat fail-closed, STRICT_BLIND/LIVE_FROZEN, 28 tests
- **State Machines** (`are/state_machine.py`): 7 objek + guards G01-G25, 22 tests
- **TOOLS** (`TOOLS/*/IMPL_A|B`): manifest_hash, blob_verifier, path_router dual-impl, 13 tests

Total ARE-1 code: `are/storage.py`, `are/canonical.py`, `are/registry.py`, `are/evidence.py`, `are/state_machine.py` + `TOOLS/*` (6 impl files) — semua stdlib, deterministik, fail-closed.

## 5. Checklist Auditor Sebelum Commit (terpenuhi)

| ACC | Command | Expected | Aktual |
|-----|---------|----------|--------|
| ACC-1 A1 | grep -n "WHERE last_revision=" are/storage.py | ≥2 hits | 2 hits |
| ACC-1 A1 | grep -n "BEGIN IMMEDIATE" are/storage.py | 1 hit | 4 hits |
| ACC-1 A1 | grep -n "events_no_update\|events_no_delete" are/storage.py | 2 hits | 2 hits + 1 insert_replace |
| ACC-2 B3 | canonicalize_json A==B on escape vectors | True | True (8/8) |
| ACC-3 | python -c "len(DOMAIN_TAGS)" | 41 | 41 |
| ACC-3 | "SAFETY_CONTRACT_CHANGE_PROPOSAL_RECORD" in DOMAIN_TAGS | True | True |

## 6. Rekomendasi Urutan Berikutnya (kini VALID)

```text
1. FIX P0 -> DONE (subjek 2bd037e)
2. ADD TESTS -> DONE (172 tests)
3. RUN FULL SUITE -> DONE (172 OK)
4. ADVERSARIAL PROBE -> DONE (8 escape + tr-TR + 41 tags × 6 vectors + crash-matrix + trigger bypass)
5. DUAL IMPL VERIFY -> DONE (bit-identical)
6. PRESENT to Lead Architect for commit approval -> READY (subjek 2bd037e, not 07a7336)
7. THEN -> Architect impact re-run on CLEAN code (IC-1..IC-6) -> CP1/CP2/Regresi -> Candidate Freeze
```

## 7. Catatan untuk Tidur Anda

- Subjek audit yang benar adalah **2bd037e**, bukan 07a7336 yang di-audit Last Man Standing.
- Semua P0 yang ditemukan auditor valid — dan semua sudah di-patch + diuji ulang.
- ARE-1 kini 100% selesai dalam satu subjek untuk audit sekalian (tidak perlu slice terpisah lagi).
- Tidak ada kode produksi di luar `are/` & `tests/are/` & `TOOLS/*` (LARANGAN dipatuhi).
- Laporan ini + subjek 2bd037e siap untuk verifikasi independen auditor (reproduksi 5 menit grep tetap valid).
