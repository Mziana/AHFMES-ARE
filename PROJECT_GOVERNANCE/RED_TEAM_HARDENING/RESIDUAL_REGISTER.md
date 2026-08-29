# RED TEAM RESIDUAL REGISTER & ARCHITECTURAL DEBT LEDGER

Status: **ACTIVE TRACKER / GELOMBANG 2 TERBUKA (11 TEMUAN BARU RED-13..23)**  
Baseline Inisiasi: **740873f on main**  
Baseline Gelombang 2: **1857269 on main**  
Otoritas: **Lead Architect & Red Team Advisory Council**

---

## 1. Register Temuan & Hutang Teknis Red Team

### Gelombang 1 (RED-01..12) — SELURUHNYA RESOLVED

| ID Residu | Kategori | Tingkat Keparahan | File : Baris Terkait | Deskripsi Masalah & Dampak Kegagalan | Target Remediasi | Status |
|---|---|:---:|---|---|---|:---:|
| **RES-RED-01** | Execution / CSK | 🚨 **P0 (CRITICAL)** | `are/mt5_runner.py:67`<br>`are/mt5_gateway.py:264` | **Semantic Inversion pada Rate Limiter:** Parameter `order_count` diisi `len(open_positions)` bukan frekuensi order per menit. Memblokir order baru jika posisi di-hold lama, dan meloloskan spam order jika posisi langsung tertutup. | DELEGASI_038 | ✅ RESOLVED @DELEGASI_038 |
| **RES-RED-02** | Gateway / Live | 🚨 **P0 (CRITICAL)** | `are/mt5_gateway.py:315-318` | **Live Gateway Open Positions Empty:** Pada mode non-mock, `get_open_positions()` mengembalikan `[]` statis tanpa memanggil `mt5.positions_get()`, melumpuhkan rate limiter di live mode. | DELEGASI_038 | ✅ RESOLVED @DELEGASI_038 |
| **RES-RED-03** | Safety / Mode | 🚨 **P0 (CRITICAL)** | `are/mt5_gateway.py:112-119` | **Silent Mock Fallback (Mode Confusion):** Jika user meminta `use_mock=False` namun library MT5 tidak ada, sistem diam-diam beralih ke Mock tanpa error, melanggar hukum Fail-Closed. | DELEGASI_038 | ✅ RESOLVED @DELEGASI_038 |
| **RES-RED-04** | Safety / Liquidation | 🚨 **P0 (CRITICAL)** | `are/mt5_gateway.py:277-308` | **Unverified Emergency Flat:** `emergency_flat()` hanya menghitung close order yang dikirim tanpa verifikasi *read-back* bahwa `positions_get() == 0`. Posisi liar yang gagal tertutup broker diabaikan. | DELEGASI_038 | ✅ RESOLVED @DELEGASI_038 |
| **RES-RED-05** | Runtime / Runner | 🚨 **P0 (CRITICAL)** | `are/mt5_runner.py:64` | **Hardcoded Risk State Stub:** Nilai drawdown di-hardcode statis `drawdown: 0.01` dan default `account_equity: 10000.0`. Sensor risiko tidak membaca data live account dari MT5 terminal. | DELEGASI_038 | ✅ RESOLVED @DELEGASI_038 |
| **RES-RED-06** | Watchdog / Loop | 🚨 **P0 (CRITICAL)** | `are/mt5_runner.py:177, 235` | **Silent Loop Termination:** Exception pada `run_live_loop()` hanya melakukan `break` tanpa memicu alert status `CRITICAL` ke `SystemHealthMonitor` dan tanpa mencatat insiden fatal. | DELEGASI_038 | ✅ RESOLVED @DELEGASI_038 |
| **RES-RED-07** | Statistics / Contract | 📊 **P1 (HIGH)** | `are/backtest.py:136` | **Sharpe Annualization Scale Mismatch:** Formula mengalikan `sqrt(252)` pada bar 1-menit (`+60s`). Faktor tahunan yang benar harus diskalakan terhadap frekuensi sampling bar. | DELEGASI_039 | ✅ RESOLVED @DELEGASI_039 |
| **RES-RED-08** | Provenance / Scientific | 📊 **P1 (HIGH)** | `are/validation.py:228-235` | **Semantic Verification Theater:** Placeholder hash `"0"*64` dilabeli `provenance_status = "VERIFIED"`. Wajib dilabeli `UNPROVEN` / `SENTINEL_UNVERIFIED`. | DELEGASI_039 | ✅ RESOLVED @DELEGASI_039 |
| **RES-RED-09** | Validation / WFA | 📊 **P1 (HIGH)** | `are/backtest.py:240-275` | **Static Logic Rolling Backtest:** WFA saat ini hanya evaluasi rolling pada fungsi statis, belum melakukan *True Walk-Forward Optimization* (`fit(train)` -> `test(oos)` parameter drift). | DELEGASI_039 | ✅ RESOLVED @DELEGASI_039 |
| **RES-RED-10** | Simulator / Backtest | 📊 **P1 (HIGH)** | `are/backtest.py:95-115` | **Frictionless P&L Assumption:** Backtest P&L murni `signal * price_return` tanpa model komisi, spread, slippage, latency, financing swap, dan partial fills. | DELEGASI_040 | ✅ RESOLVED @DELEGASI_040 |
| **RES-RED-11** | Stress Testing / MC | 📊 **P1 (HIGH)** | `are/validation.py:165-190` | **Shuffling Destroys Volatility Clustering:** Monte Carlo murni `random.shuffle()` mengabaikan dependensi serial dan pengelompokan volatilitas nyata pasar. | DELEGASI_040 | ✅ RESOLVED @DELEGASI_040 |
| **RES-RED-12** | Governance / Source | 📋 **P2 (MEDIUM)** | `README.md:14-17` | **Source of Truth Divergence:** Root `README.md` mencatat `ARE-2 AUTHORIZED`, berbeda dengan `CURRENT_AUTHORITY_INDEX.md` yang sudah menyelesaikan Fase 4. | DELEGASI_037b | ✅ RESOLVED @b80f413 |

---

### Gelombang 2 (RED-13..23) — DEEP CORRECTION AUDIT (Stage 4 Red Team)

> Ditemukan oleh Lead Architect Deep Correction Audit pada 2026-08-29 setelah verifikasi fisik kode commit `1857269`. Temuan ini berada pada lapisan yang lebih dalam: **semantic correctness, statistical validity, dan evidence integrity** — bukan bug software biasa.

| ID Residu | Kategori | Tingkat Keparahan | File : Baris Terkait | Deskripsi Masalah & Dampak Kegagalan | Target Remediasi | Status |
|---|---|:---:|---|---|---|:---:|
| **RES-RED-13** | Safety / Drawdown | 📊 **P1 (HIGH)** | `are/mt5_gateway.py:142` | **Drawdown Semantics Mismatch:** `get_account_info()` menghitung drawdown sebagai `(balance - equity) / balance`, bukan peak-equity drawdown standar `(peak_equity - equity) / peak_equity`. Menyebabkan CSK gate bisa **underreport risiko** dan meloloskan order pada drawdown sebenarnya >15%. | DELEGASI_041 | 🔴 OPEN |
| **RES-RED-14** | Safety / Gateway | 🚨 **P0 (CRITICAL)** | `are/mt5_gateway.py:364-366` | **MT5 API None vs Empty Positions Ambiguity:** `get_open_positions()` menggunakan `if not positions: return []` yang menyamakan `None` (API error/unknown state) dengan `()` (benar-benar kosong). Emergency flat bisa menyatakan "FLAT" padahal state sebenarnya UNKNOWN. | DELEGASI_041 | 🔴 OPEN |
| **RES-RED-15** | Provenance / Artifact | 📋 **P2 (MEDIUM)** | `are/backtest.py:226` | **Non-deterministic Research Artifact Hash:** `save_artifact()` memasukkan `time.time()` ke dalam canonical JSON payload sebelum hashing. Komputasi identik menghasilkan `proof_hash` berbeda karena timestamp run berbeda, melanggar prinsip content-addressed proof. | DELEGASI_041 | 🔴 OPEN |
| **RES-RED-16** | Simulator / Crisis | 📊 **P1 (HIGH)** | `are/backtest.py:284-288` | **Crisis Replay Uses Static Default Friction:** `run_crisis_replay()` memanggil `run_backtest()` tanpa mempropagasikan `spread_pct`, `slippage_pct`, `commission_pct`. Crisis dataset (CHF, COVID, 2008) disimulasikan dengan spread 1 bps — tidak realistis. | DELEGASI_041 | 🔴 OPEN |
| **RES-RED-17** | API / Semantics | 📊 **P1 (HIGH)** | `are/backtest.py:308-396` | **Dual WFA Semantics Confusion:** `run_walk_forward_analysis()` (static logic rolling backtest) dan `run_walk_forward_optimization()` (true WFO with grid search) coexist sebagai API publik. Developer bisa salah memanggil yang pertama dan mengklaim "WFA" padahal bukan WFO. | DELEGASI_041 | 🔴 OPEN |
| **RES-RED-18** | WFO / Leakage | 📊 **P1 (HIGH)** | `are/backtest.py:441-442` | **WFO Boundary: No Warm-up, No Purge/Embargo:** OOS test slice dimulai tepat setelah train berakhir tanpa lookback context (strategy dengan `slow_MA=30` menghasilkan 30 bar NaN). Tidak ada purge/embargo window untuk mencegah label overlap information leakage. | DELEGASI_041 | 🔴 OPEN |
| **RES-RED-19** | Statistics / Bias | 📊 **P1 (HIGH)** | `are/backtest.py:449-464`<br>`are/validation.py:328-340` | **No Research-Family Accounting / Effective Trial Count:** WFO grid search `argmax(Sharpe)` per fold tidak mencatat `total_trials_count` atau `hypothesis_family_size`. DSR tidak bisa mengkoreksi selection bias karena jumlah hypothesis yang dicoba tidak diketahui. | DELEGASI_041 | 🔴 OPEN |
| **RES-RED-20** | Statistics / MC | 📊 **P1 (HIGH)** | `are/validation.py:282-295` | **Monte Carlo: No Uncertainty Interval:** Output `mc_probability_of_ruin` dan `mc_95th_pct_drawdown` adalah point estimate tanpa confidence interval. Gate `prob_ruin > 10%` bisa terlalu percaya diri. Percentile computation menggunakan `int(0.95 * N)` tanpa definisi kuantil eksplisit. | DELEGASI_041 | 🔴 OPEN |
| **RES-RED-21** | MC / Architecture | 📋 **P2 (MEDIUM)** | `are/validation.py:247-258` | **MC Does Not Preserve Execution-Cost Path Dependency:** Monte Carlo hanya resample `strategy_return` yang sudah jadi. Hubungan `market_path → signal → turnover → friction_cost` putus setelah resampling. | BACKLOG | 🟡 DEFERRED |
| **RES-RED-22** | Input / Validation | 📊 **P1 (HIGH)** | `are/backtest.py:63-71, 119` | **No Parameter Validation / Negative Friction Accepted:** `spread_pct`, `slippage_pct`, `commission_pct` tidak divalidasi. Nilai negatif menghasilkan "friction credit" yang secara semantik tidak masuk akal. Tidak ada guard untuk NaN, Inf, atau signal di luar [-1, 1]. | DELEGASI_041 | 🔴 OPEN |
| **RES-RED-23** | Safety / Rate | 📋 **P2 (MEDIUM)** | `are/mt5_gateway.py:111` | **Process-Local Order Rate State:** `_order_timestamps` adalah `deque` in-memory per-instance. Multi-process, restart, atau multiple gateway instances menyebabkan rate limit terfragmentasi. Singleton constraint belum dibuktikan. | BACKLOG | 🟡 DEFERRED |

---

## 2. Kebijakan Anti-Penghilangan Residu (Zero Debt Omission)

1. Tidak ada satu pun residu di atas yang boleh dihapus dari register ini kecuali telah disertai bukti commit perbaikan, tes invarian verifikasi, dan audit Lead Architect.
2. Setiap kali residu diselesaikan, status diubah menjadi `RESOLVED @<commit>` dan dicatat di Riwayat Penyelesaian di bawah.
3. **Klaim "Zero Debt" HANYA sah jika seluruh residu berstatus RESOLVED.** Selama ada residu OPEN atau DEFERRED, klaim "zero debt" dilarang.

---

## 3. Riwayat Penyelesaian Residu

### Gelombang 1 (Diselesaikan 2026-08-29)

| ID Residu | Tanggal Tutup | Delegasi / Commit | Deskripsi Solusi Teknis |
| :--- | :---: | :---: | :--- |
| **RES-RED-01** | 2026-08-29 | DELEGASI_038 | Mengimplementasikan sliding 60-second window tracker `_order_timestamps` via `deque` dan method `get_recent_order_count(60.0)` pada `MT5ExecutionGateway`, menggantikan `len(open_positions)`. |
| **RES-RED-02** | 2026-08-29 | DELEGASI_038 | Mengikat `get_open_positions()` pada live MT5 ke `self._mt5_lib.positions_get()` dengan ekstraksi kamus tiket, volume, symbol, dan type. |
| **RES-RED-03** | 2026-08-29 | DELEGASI_038 | Menerapkan strict Fail-Closed pada `use_mock=False`: melempar `RuntimeError("LIVE_MT5_REQUIRED_BUT_UNAVAILABLE")` jika package `MetaTrader5` tidak terpasang/gagal diimpor. |
| **RES-RED-04** | 2026-08-29 | DELEGASI_038 | Menerapkan loop verifikasi *read-back* maksimal 3 retry pada `emergency_flat()` dan melempar `RuntimeError("EMERGENCY_FLAT_VERIFICATION_FAILED")` jika posisi sisa > 0. |
| **RES-RED-05** | 2026-08-29 | DELEGASI_038 | Menambahkan `get_account_info()` pada `MT5ExecutionGateway` dan mengikat `drawdown` dinamis real-time serta real equity pada `MT5LiveRunner.step_live_tick()` dan `step_live_tick_async()`. |
| **RES-RED-06** | 2026-08-29 | DELEGASI_038 | Mengeliminasi silent break: mencatat `RUNNER_FATAL_EXCEPTION` ke `evidence_ledger`, memicu `emergency_flat()`, dan melempar `RuntimeError` saat loop runner crash. |
| **RES-RED-07** | 2026-08-29 | DELEGASI_039 | Menambahkan parameter `timeframe_seconds` (default 60s) dan fungsi `calculate_sharpe_ratio()`, serta menghitung annualization factor dinamis `sqrt(252 * bars_per_day)` pada `are/backtest.py`. |
| **RES-RED-08** | 2026-08-29 | DELEGASI_039 | Menghilangkan verification theater pada `ValidationService.validate_candidate()`: sentinel zero-hash wajib dilabeli `SENTINEL_UNPROVEN` dan `is_provenance_verified = False`, status `VERIFIED` hanya sah pada hash kriptografis non-zero. |
| **RES-RED-09** | 2026-08-29 | DELEGASI_039 | Mengimplementasikan `run_walk_forward_optimization()` pada `BacktestEngine`: optimasi parameter in-sample (train) dan evaluasi out-of-sample (test) independen, kalkulasi WFE ratio, serta deteksi degradasi overfitting. |
| **RES-RED-10** | 2026-08-29 | DELEGASI_040 | Mengimplementasikan model friksi mikrostruktur proporsional baseline v1 (`spread_pct`, `slippage_pct`, `commission_pct`) pada `BacktestEngine`, menghitung turnover posisi per bar dan rincian biaya transaksi. |
| **RES-RED-11** | 2026-08-29 | DELEGASI_040 | Mengimplementasikan metode Circular Block Bootstrap Monte Carlo pada `monte_carlo_simulation()`, mempertahankan dependensi lokal serial dalam window `block_size`. |
| **RES-RED-12** | 2026-08-29 | DELEGASI_037b (`b80f413`) | Menyelaraskan penuh root `README.md` dengan `CURRENT_AUTHORITY_INDEX.md`, mengeliminasi divergensi status sistem. |

### Gelombang 2 (Dalam Proses)

| ID Residu | Tanggal Tutup | Delegasi / Commit | Deskripsi Solusi Teknis |
| :--- | :---: | :---: | :--- |
| *Belum ada penyelesaian* | — | — | — |
