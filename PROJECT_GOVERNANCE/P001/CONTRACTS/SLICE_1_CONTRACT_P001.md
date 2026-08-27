# SLICE 1 CONTRACT — PROGRAM P001 & RUNNER SUITE (Operational CLI, Runner Daemon & Dashboard)

Status: **FROZEN T3 — RATIFIED FOR IMPLEMENTATION / AUTHORIZED**  
Fase: **P001 Slice-1 (Operational Tooling & Runner)**  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` & `ENGINEERING/RULES.md`  
Baseline: `@c2db321` (260 tests pass, Manifest V41)

---

## 1. Lingkup Komponen P001 Slice-1

### A. Unified CLI Command Center (`are/cli.py`)
- Menggunakan `argparse` standar (zero external dependencies).
- Perintah yang didukung:
  1. `are status`: Menampilkan ringkasan status sistem (Active Champion ID, CSK risk limits, Drawdown saat ini, total event di streams `champion_registry`, `operational_signals`, `research_telemetry`).
  2. `are run-cycle`: Menjalankan 1 siklus riset otonom terpandu (`ResearchCoordinator.run_autonomous_cycle()`) dan menampilkan hasil promosi/rejeksi.
  3. `are run-daemon`: Memulai runner service berkelanjutan (background / foreground loop).
  4. `are champion`: Subkomando untuk `history` (melihat riwayat suksesi champion) dan `rollback` (mengembalikan champion ke record sebelumnya via `ChampionRegistry.rollback_champion()`).
  5. `are safety-kill`: Mengaktifkan *emergency kill switch* pada `CapitalSafetyKernel` (ACC-501).
  6. `are dashboard`: Meluncurkan interactive terminal dashboard mode.

### B. Continuous Operational Runner Daemon (`are/runner.py`)
- Mengoordinasikan *Fast Loop* (`OperationalBrain`) dan *Slow Loop* (`EvolutionaryLoop`):
  1. `RunnerConfig`: dataclass konfigurasi frekuensi tick, symbol target, database path, batch sizes.
  2. `OperationalRunner`: Menjalankan tick data simulasi/pasar, mencatat telemetri, dan jika rasio penyesalan (*regret threshold*) terlampaui, otomatis memanggil `EvolutionaryLoop.evaluate_and_evolve()` untuk adaptasi champion tanpa downtime (ACC-502).

### C. Rich Terminal ANSI Dashboard (`are/dashboard.py`)
- Render visual ANSI / ASCII text formatting yang interaktif & informatif (ACC-503):
  1. Header: Status Node, Waktu Sistem, Mode Operasional (SIMULATED / SANDBOXED).
  2. Panel Champion: Active Champion ID, Candidate Hash, Status, Activation Time.
  3. Panel Risk Firewall (CSK): Kill Switch (ACTIVE / OFF), Max Drawdown %, Volatility Cutoff, Order Rate Limit.
  4. Panel Streams & Ledger: Total Operational Ticks, Total Research Cycles, Hash Chain Integrity (VALID / COMPROMISED).

---

## 2. Kriteria Penerimaan Formal (ACC-501 s/d ACC-510)

| ID | Deskripsi Kriteria Penerimaan | Verifikasi |
|---|---|---|
| **ACC-501** | `are/cli.py` menyediakan subperintah `status`, `run-cycle`, `run-daemon`, `champion`, `safety-kill`, `dashboard` | Unit test CLI |
| **ACC-502** | `are/runner.py` mengoordinasikan loop cepat dan loop lambat secara thread-safe dan non-blocking | `test_are_runner.py` |
| **ACC-503** | `are/dashboard.py` merender visual status terminal yang lengkap dan bebas error | `test_are_dashboard.py` |
| **ACC-504** | Subperintah `safety-kill` langsung mengaktifkan kill-switch CSK dan memverifikasi veto `EMERGENCY_FLAT` | E2E CLI test |
| **ACC-505** | Zero external dependencies (murni Python Standard Library: `argparse`, `time`, `json`, `sqlite3`, dll.) | Code audit |
| **ACC-506** | Seluruh test suite (260 baseline + test suite baru P001 Slice-1) 100% PASS | `python -m pytest tests/` |
| **ACC-507** | Repositori bersih tanpa file sementara (`working tree clean`) | `git status` |
| **ACC-508** | Dual-implementation `manifest_hash` & `blob_verifier` 100% PASS | `TOOLS/` verification |
| **ACC-509** | Zero regressions pada seluruh test historis ARE-1 s/d ARE-4 | Full pytest pass |
| **ACC-510** | Dilarang menyentuh broker API riil / transmisi modal live | Strict firewall audit |

---

## 3. Batasan & Larangan Keras
- **DILARANG** menambahkan dependensi eksternal seperti `click`, `rich`, `textual` (WAJIB stdlib-only).
- **DILARANG** membuka eksekusi order modal live.
