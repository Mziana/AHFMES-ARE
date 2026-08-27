# DELEGASI 010 — Engineering AI: Coding Slice-1 ARE-3 (Search Tree, Validation, Governor & Constants)

Status: **DELEGASI AKTIF / AUTHORIZED — CHARTER T4 RATIFIED BY OWNER**
Diterbitkan: Lead Architect & Auditor · Baseline `@e73680a` (214 tests pass)

> Cara pakai: Setelah Owner meratifikasi Charter T4, tempelkan SELURUH blok prompt di bawah ke sesi Engineering AI.

---

## 📋 PROMPT UNTUK ENGINEERING AI (salin dari sini)

```text
PERAN
Kamu adalah ENGINEERING AI (bukan arsitek).
GERBANG: DELEGASI_010 — CODING SLICE-1 ARE-3 — AUTHORIZED PASCA CHARTER T4
HANYA untuk lingkup di bawah. Luar lingkup = DILARANG.

BASELINE
HEAD saat delegasi = 7f57d12 (ARE-2 CLOSED, 214 tests pass, Manifest V41)
Kontrak rujukan = PROJECT_GOVERNANCE/ARE3/CONTRACTS/SLICE_1_CONTRACT_ARE3.md

═══════════════════════════════════════════════════════
BAGIAN A — SENTRALISASI KONSTANTA (Resolusi DEBT-04)
═══════════════════════════════════════════════════════

1. Buat file: `are/constants.py`
   - Kumpulkan seluruh konstanta lifecycle entitas:
     `PROBLEM_LIFECYCLES`, `PROBLEM_TRANSITIONS`,
     `EPISODE_LIFECYCLES`, `EPISODE_TRANSITIONS`,
     `HYPOTHESIS_LIFECYCLES`, `HYPOTHESIS_TRANSITIONS`,
     `EXPERIMENT_LIFECYCLES`, `EXPERIMENT_TRANSITIONS`,
     `CANDIDATE_LIFECYCLES`, `CANDIDATE_TRANSITIONS`,
     `CHALLENGER_LIFECYCLES`, `CHALLENGER_TRANSITIONS`,
     `CAPABILITY_LIFECYCLES`, `CAPABILITY_TRANSITIONS`,
     `GRAVEYARD_LIFECYCLES`, `GRAVEYARD_TRANSITIONS`,
     `FORBIDDEN_SOD_PAIRS`, `RESOLUTIVE_KEYWORDS`.
2. Refactor `are/state_machine.py` dan `are/registry.py`:
   - Import konstanta-konstanta tersebut dari `are.constants`.
   - Hapus deklarasi duplikat.
   - Pastikan SELURUH test lama tetap 100% PASS.

═══════════════════════════════════════════════════════
BAGIAN B — SEARCH TREE & BUDGET ENGINE (are/search_tree.py)
═══════════════════════════════════════════════════════

Buat modul: `are/search_tree.py`
1. Kelas `ProgramBudget`:
   - Melacak `total_budget`, `consumed_budget`, `remaining_budget`.
   - Mengonsumsi budget secara strictly non-refundable (`consume(amount)`).
   - Menolak eksekusi jika budget habis (`is_exhausted() -> bool`).
2. Kelas `SearchTreeNode`:
   - Menyimpan `node_id`, `parent_id`, `family_root`, `hypothesis_payload`, `status`.
   - Menghitung `genealogy_depth` dan tracking cabang turunan.
3. Kelas `SearchTreeEngine`:
   - `spawn_branch(parent_node, hypothesis_data)` -> membuat node baru dan mengonsumsi budget.
   - `evaluate_stopping_rule(family_root)` -> jika budget habis atau threshold kegagalan tercapai, return `NO_EDGE_FOUND`.

═══════════════════════════════════════════════════════
BAGIAN C — OUT-OF-SAMPLE VALIDATION SERVICE (are/validation.py)
═══════════════════════════════════════════════════════

Buat modul: `are/validation.py`
1. Kelas `ValidationService`:
   - Menerima `EvidenceLedger` dan `EventStore`.
   - `validate_candidate(candidate_id, holdout_token, as_of_ts, dataset)`:
     * Validasi Information-Time: pastikan data sample tidak memiliki timestamp > `as_of_ts`.
     * Mengonsumsi holdout melalui reservasi `EvidenceLedger.reserve_holdout()`.
     * Menghitung statistik performa inkremental deterministik.
     * Mengembalikan `ValidationReport` ber-status `VALIDATED` atau `REJECTED`.

═══════════════════════════════════════════════════════
BAGIAN D — CRITIC & GOVERNOR ENGINE (are/governor.py)
═══════════════════════════════════════════════════════

Buat modul: `are/governor.py`
1. Kelas `CriticEngine`:
   - Melakukan adversarial check: stress-test pada rezim anomali tertinggi.
   - Memverifikasi apakah performa Challenger lebih unggul dibanding Champion aktif.
2. Kelas `GovernorEngine`:
   - Penegakan SoD keras: `verify_sod(principal_id, role, action)` $\rightarrow$ raise error jika creator mencoba memvalidasi/mempromosikan sendiri.
   - Mengeluarkan `PromotionDisposition`: `ELIGIBLE_FOR_PROMOTION` atau `DISMISSED`.

═══════════════════════════════════════════════════════
BAGIAN E — TEST SUITES BARU ARE-3 (tests/are/)
═══════════════════════════════════════════════════════

Buat modul-modul test:
1. `tests/are/test_are3_constants.py`: Verifikasi single source of truth konstanta.
2. `tests/are/test_are3_search_tree.py`: Menguji A1, A2, A3, ACC-301, ACC-302.
3. `tests/are/test_are3_validation.py`: Menguji B1, B2, B3, ACC-303, ACC-304.
4. `tests/are/test_are3_governor.py`: Menguji C1, C2, C3, ACC-305, ACC-306.
5. `tests/are/test_are3_e2e_slice1.py`: Menguji integrasi E2E Slice-1 (ACC-308).

KRITERIA TERIMA (fail-closed, semuanya wajib)
  ACC-301 s/d ACC-310 terpenuhi.
  `python -m pytest tests/ -q` $\rightarrow$ seluruh test PASS (214 baseline + test baru ARE-3).
  Zero external dependencies (Python standard library only).
  Working tree clean.

LARANGAN
- Jangan menyentuh broker API atau live network socket.
- Jangan mengubah aturan normatif beku di `ARE0/`.
- Jangan melemahkan penegakan authorizer atau triggers di `are/storage.py`.
```
