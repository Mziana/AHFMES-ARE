# DELEGASI 016 — Engineering AI: Coding Slice-1 P001 (Operational Tooling, CLI, Runner Daemon & Terminal Dashboard)

Status: **DELEGASI AKTIF / AUTHORIZED — CHARTER T4 RATIFIED**  
Diterbitkan: Lead Architect & Auditor · Baseline `@c2db321` (260 tests pass)

> Cara pakai: Tempelkan SELURUH blok prompt di bawah ke sesi Engineering AI.

---

## 📋 PROMPT UNTUK ENGINEERING AI (salin dari sini)

```text
PERAN
Kamu adalah ENGINEERING AI (bukan arsitek).
GERBANG: DELEGASI_016 — CODING SLICE-1 P001 & RUNNER SUITE — AUTHORIZED
HANYA untuk lingkup di bawah. Luar lingkup = DILARANG.

BASELINE
HEAD saat delegasi = c2db321 (ARE-4 CLOSED, 260 tests pass, Manifest V41)
Kontrak rujukan = PROJECT_GOVERNANCE/P001/CONTRACTS/SLICE_1_CONTRACT_P001.md

═══════════════════════════════════════════════════════
BAGIAN A — are/dashboard.py (RICH TERMINAL ANSI/ASCII DASHBOARD)
═══════════════════════════════════════════════════════
Buat `are/dashboard.py` (stdlib only: sys, os, time, json):
- Fungsi `format_dashboard(champion_info: dict, safety_info: dict, stream_stats: dict, is_live_mode: bool = False) -> str`:
  Menghasilkan layout teks berbingkai ASCII/ANSI yang memvisualisasikan:
  1. Header Node & Time (UTC / System).
  2. Panel Champion: Active ID, Candidate Hash, Status, Activation Time.
  3. Panel Capital Safety Kernel: Kill Switch (ACTIVE/OFF), Max Drawdown %, Volatility Cutoff, Order Rate Limit.
  4. Panel Streams & Ledger: Total Operational Ticks, Veto Ratio, Chain Health (VERIFIED / OK).
- Kelas `TerminalDashboard`:
  - Metode `render(champion_registry, safety_kernel, event_store, stream_id="operational_signals") -> str`
  - Metode `print_dashboard(champion_registry, safety_kernel, event_store)`

═══════════════════════════════════════════════════════
BAGIAN B — are/runner.py (OPERATIONAL RUNNER DAEMON)
═══════════════════════════════════════════════════════
Buat `are/runner.py` (stdlib only: time, threading, json, typing, dataclasses):
- Dataclass `RunnerConfig`:
  - `db_path: str = "ahfmes_are.db"`
  - `symbol: str = "BTCUSDT"`
  - `tick_interval_sec: float = 1.0`
  - `lookback_events: int = 50`
  - `regret_threshold: float = 0.40`
  - `auto_evolve: bool = True`
- Kelas `OperationalRunner`:
  - Inisialisasi: `OperationalBrain`, `EvolutionaryLoop`, `ResearchCoordinator`, `EventStore`, dll.
  - Metode `step_tick(market_features: dict, current_risk_state: dict, timestamp: Optional[float] = None) -> OperationalSignal`:
    Memproses 1 tick lewat OperationalBrain.
  - Metode `check_and_adapt(current_features: dict, holdout_dataset: list, assignment: AgentAssignment) -> Optional[ResearchCycleResult]`:
    Memanggil EvolutionaryLoop jika terjadi pelanggaran batas penyesalan (*regret breach*).
  - Metode `run_loop(tick_generator_fn, max_ticks: Optional[int] = None)`:
    Menjalankan loop berkelanjutan secara terkendali dan fail-safe.

═══════════════════════════════════════════════════════
BAGIAN C — are/cli.py (UNIFIED CLI COMMAND CENTER)
═══════════════════════════════════════════════════════
Buat `are/cli.py` (stdlib only: argparse, sys, json, os, time):
- Main CLI function `main(argv=None) -> int` dan parser subperintah:
  1. `status [--db-path] [--json]`: Menampilkan ringkasan status node, active champion, CSK limits, dan stream counts.
  2. `run-cycle [--db-path] [--symbol SYMBOL]`: Menjalankan 1 siklus riset otonom terpandu dan mencetak hasil promosi.
  3. `run-daemon [--db-path] [--symbol SYMBOL] [--ticks N] [--interval SEC]`: Menjalankan OperationalRunner.
  4. `champion history [--db-path]` / `champion rollback [--db-path]`: Melihat riwayat atau melakukan rollback champion.
  5. `safety-kill [--db-path]`: Mengaktifkan kill-switch CSK secara instan.
  6. `dashboard [--db-path]`: Merender visual dashboard ke stdout.

═══════════════════════════════════════════════════════
BAGIAN D — PENGUJIAN UNIT & E2E (tests/are/)
═══════════════════════════════════════════════════════
Buat modul test:
1. `tests/are/test_p001_dashboard.py`: Menguji format teks dan rendering dashboard.
2. `tests/are/test_p001_runner.py`: Menguji eksekusi `OperationalRunner` dan adaptasi otomatis.
3. `tests/are/test_p001_cli.py`: Menguji subperintah `status`, `run-cycle`, `champion`, `safety-kill`, `dashboard` lewat CLI.

KRITERIA TERIMA (fail-closed, semuanya wajib)
  ACC-501 s/d ACC-510 terpenuhi 100%.
  `python -m pytest tests/ -q` $\rightarrow$ seluruh test PASS (260 baseline + test baru P001 Slice-1).
  Zero external dependencies (Python Standard Library only: argparse, json, sys, os, time, sqlite3, threading).
  Zero test regression (seluruh 260 test lama lulus 100%).
  Working tree clean.

LARANGAN
- Dilarang menambahkan dependensi pihak ketiga (click, rich, dll.).
- Dilarang menyentuh broker API / live market execution.

PROSES
1. Buat `are/dashboard.py`, `are/runner.py`, `are/cli.py`.
2. Buat `tests/are/test_p001_dashboard.py`, `tests/are/test_p001_runner.py`, `tests/are/test_p001_cli.py`.
3. Jalankan `python -m pytest tests/ -q` -> pastikan seluruh 260+ test PASS.
4. Commit di main: "feat(p001): implement Slice-1 Operational CLI, Runner Daemon & Dashboard (DELEGASI_016)"
5. Laporkan hasilnya ke Lead Architect.
```
