# RED TEAM RESIDUAL REGISTER & ARCHITECTURAL DEBT LEDGER

Status: **ACTIVE TRACKER / ZERO DEBT OMISSION PROTOCOL**  
Baseline Inisiasi: **740873f on main**  
Otoritas: **Lead Architect & Red Team Advisory Council**

---

## 1. Register Temuan & Hutang Teknis Red Team

| ID Residu | Kategori | Tingkat Keparahan | File : Baris Terkait | Deskripsi Masalah & Dampak Kegagalan | Target Remediasi | Status |
|---|---|:---:|---|---|---|:---:|
| **RES-RED-01** | Execution / CSK | 🚨 **P0 (CRITICAL)** | `are/mt5_runner.py:67`<br>`are/mt5_gateway.py:264` | **Semantic Inversion pada Rate Limiter:** Parameter `order_count` diisi `len(open_positions)` bukan frekuensi order per menit. Memblokir order baru jika posisi di-hold lama, dan meloloskan spam order jika posisi langsung tertutup. | DELEGASI_038 | ✅ RESOLVED @DELEGASI_038 |
| **RES-RED-02** | Gateway / Live | 🚨 **P0 (CRITICAL)** | `are/mt5_gateway.py:315-318` | **Live Gateway Open Positions Empty:** Pada mode non-mock, `get_open_positions()` mengembalikan `[]` statis tanpa memanggil `mt5.positions_get()`, melumpuhkan rate limiter di live mode. | DELEGASI_038 | ✅ RESOLVED @DELEGASI_038 |
| **RES-RED-03** | Safety / Mode | 🚨 **P0 (CRITICAL)** | `are/mt5_gateway.py:112-119` | **Silent Mock Fallback (Mode Confusion):** Jika user meminta `use_mock=False` namun library MT5 tidak ada, sistem diam-diam beralih ke Mock tanpa error, melanggar hukum Fail-Closed. | DELEGASI_038 | ✅ RESOLVED @DELEGASI_038 |
| **RES-RED-04** | Safety / Liquidation | 🚨 **P0 (CRITICAL)** | `are/mt5_gateway.py:277-308` | **Unverified Emergency Flat:** `emergency_flat()` hanya menghitung close order yang dikirim tanpa verifikasi *read-back* bahwa `positions_get() == 0`. Posisi liar yang gagal tertutup broker diabaikan. | DELEGASI_038 | ✅ RESOLVED @DELEGASI_038 |
| **RES-RED-05** | Runtime / Runner | 🚨 **P0 (CRITICAL)** | `are/mt5_runner.py:64` | **Hardcoded Risk State Stub:** Nilai drawdown di-hardcode statis `drawdown: 0.01` dan default `account_equity: 10000.0`. Sensor risiko tidak membaca data live account dari MT5 terminal. | DELEGASI_038 | ✅ RESOLVED @DELEGASI_038 |
| **RES-RED-06** | Watchdog / Loop | 🚨 **P0 (CRITICAL)** | `are/mt5_runner.py:177, 235` | **Silent Loop Termination:** Exception pada `run_live_loop()` hanya melakukan `break` tanpa memicu alert status `CRITICAL` ke `SystemHealthMonitor` dan tanpa mencatat insiden fatal. | DELEGASI_038 | ✅ RESOLVED @DELEGASI_038 |
| **RES-RED-07** | Statistics / Contract | 📊 **P1 (HIGH)** | `are/backtest.py:136` | **Sharpe Annualization Scale Mismatch:** Formula mengalikan `sqrt(252)` pada bar 1-menit (`+60s`). Faktor tahunan yang benar harus diskalakan terhadap frekuensi sampling bar. | DELEGASI_039 | 📋 QUEUED |
| **RES-RED-08** | Provenance / Scientific | 📊 **P1 (HIGH)** | `are/validation.py:228-235` | **Semantic Verification Theater:** Placeholder hash `"0"*64` dilabeli `provenance_status = "VERIFIED"`. Wajib dilabeli `UNPROVEN` / `SENTINEL_UNVERIFIED`. | DELEGASI_039 | 📋 QUEUED |
| **RES-RED-09** | Validation / WFA | 📊 **P1 (HIGH)** | `are/backtest.py:240-275` | **Static Logic Rolling Backtest:** WFA saat ini hanya evaluasi rolling pada fungsi statis, belum melakukan *True Walk-Forward Optimization* (`fit(train)` -> `test(oos)` parameter drift). | DELEGASI_039 | 📋 QUEUED |
| **RES-RED-10** | Simulator / Backtest | 📊 **P1 (HIGH)** | `are/backtest.py:95-115` | **Frictionless P&L Assumption:** Backtest P&L murni `signal * price_return` tanpa model komisi, spread, slippage, latency, financing swap, dan partial fills. | DELEGASI_040 | 📋 QUEUED |
| **RES-RED-11** | Stress Testing / MC | 📊 **P1 (HIGH)** | `are/validation.py:165-190` | **Shuffling Destroys Volatility Clustering:** Monte Carlo murni `random.shuffle()` mengabaikan dependensi serial dan pengelompokan volatilitas nyata pasar. | DELEGASI_040 | 📋 QUEUED |
| **RES-RED-12** | Governance / Source | 📋 **P2 (MEDIUM)** | `README.md:14-17` | **Source of Truth Divergence:** Root `README.md` mencatat `ARE-2 AUTHORIZED`, berbeda dengan `CURRENT_AUTHORITY_INDEX.md` yang sudah menyelesaikan Fase 4. | DELEGASI_037b | 📋 QUEUED |

---

## 2. Kebijakan Anti-Penghilangan Residu (Zero Debt Omission)

1. Tidak ada satu pun residu di atas yang boleh dihapus dari register ini kecuali telah disertai bukti commit perbaikan, tes invarian verifikasi, dan audit Lead Architect.
2. Setiap kali residu diselesaikan, status diubah menjadi `RESOLVED @<commit>` dan dicatat di Riwayat Penyelesaian di bawah.

---

## 3. Riwayat Penyelesaian Residu

| ID Residu | Tanggal Tutup | Delegasi / Commit | Deskripsi Solusi Teknis |
| :--- | :---: | :---: | :--- |
| **RES-RED-01** | 2026-08-29 | DELEGASI_038 | Mengimplementasikan sliding 60-second window tracker `_order_timestamps` via `deque` dan method `get_recent_order_count(60.0)` pada `MT5ExecutionGateway`, menggantikan `len(open_positions)`. |
| **RES-RED-02** | 2026-08-29 | DELEGASI_038 | Mengikat `get_open_positions()` pada live MT5 ke `self._mt5_lib.positions_get()` dengan ekstraksi kamus tiket, volume, symbol, dan type. |
| **RES-RED-03** | 2026-08-29 | DELEGASI_038 | Menerapkan strict Fail-Closed pada `use_mock=False`: melempar `RuntimeError("LIVE_MT5_REQUIRED_BUT_UNAVAILABLE")` jika package `MetaTrader5` tidak terpasang/gagal diimpor. |
| **RES-RED-04** | 2026-08-29 | DELEGASI_038 | Menerapkan loop verifikasi *read-back* maksimal 3 retry pada `emergency_flat()` dan melempar `RuntimeError("EMERGENCY_FLAT_VERIFICATION_FAILED")` jika posisi sisa $> 0$. |
| **RES-RED-05** | 2026-08-29 | DELEGASI_038 | Menambahkan `get_account_info()` pada `MT5ExecutionGateway` dan mengikat `drawdown` dinamis real-time serta real equity pada `MT5LiveRunner.step_live_tick()` dan `step_live_tick_async()`. |
| **RES-RED-06** | 2026-08-29 | DELEGASI_038 | Mengeliminasi silent break: mencatat `RUNNER_FATAL_EXCEPTION` ke `evidence_ledger`, memicu `emergency_flat()`, dan melempar `RuntimeError` saat loop runner crash. |
