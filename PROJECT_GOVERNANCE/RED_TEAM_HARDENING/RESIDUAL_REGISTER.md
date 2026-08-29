# RED TEAM RESIDUAL REGISTER & ARCHITECTURAL DEBT LEDGER

Status: **ACTIVE TRACKER / GELOMBANG 3 TERBUKA (11 TEMUAN RANTAI WFO-01..11)**  
Baseline Inisiasi: **740873f on main**  
Baseline Gelombang 2: **1857269 on main**  
Baseline Gelombang 3: **6767cc9 on main**  
Otoritas: **Lead Architect & Red Team Advisory Council**

---

## 1. Register Temuan & Hutang Teknis Red Team

### Gelombang 1 (RED-01..12) — SELURUHNYA RESOLVED
... (lihat riwayat di bawah)

### Gelombang 2 (RED-13..23) — 9 RESOLVED, 2 DEFERRED
... (lihat riwayat di bawah)

---

### Gelombang 3 (WFO-01..11) — AUDIT INTEGRITAS RANTAI BUKTI WFO → DSR → FINAL GATE

> Ditemukan oleh Red Team Deep Targeted Audit pada 2026-08-29 setelah verifikasi commit `6767cc9`.
> Fokus audit: **Integritas Rantai Bukti Out-of-Sample, Pengendalian Multiple-Testing Selection Bias, dan Eliminasi Injeksi Parameter Manual pada Final Gate.**

| ID Residu | Kategori | Tingkat Keparahan | File : Baris Terkait | Deskripsi Masalah & Dampak Kegagalan | Target Remediasi | Status |
|---|---|:---:|---|---|---|:---:|
| **RES-WFO-01** | Final Gate / Wiring | 🚨 **P0 (CRITICAL)** | `are/preflight.py:251-256` | **Final Gate Not Wired to WFO (Manual Parameter Injection):** Pre-Flight Checkpoint 5 tidak memanggil `run_walk_forward_optimization()` melainkan menyuntikkan `wf_score=0.80` dan `num_trials=10` secara manual. Rantai bukti terputus. | DELEGASI_044 | ✅ RESOLVED @dd36c80 |
| **RES-WFO-02** | Statistics / Trials | 🚨 **P0 (CRITICAL)** | `are/backtest.py:589-591` | **Ill-defined Trial Count for DSR:** Terdapat kerancuan antara `parameter_family_size`, `evaluation_count`, dan `effective_trial_count`. DSR mengonsumsi trial count tanpa deklarasi metode aproksimasi dan model dependensi yang jelas. | DELEGASI_044 | ✅ RESOLVED @dd36c80 |
| **RES-WFO-03** | DSR / Coupling | 🚨 **P0 (CRITICAL)** | `are/validation.py:388-403`<br>`are/preflight.py:240-248` | **DSR Not Bound to Selected OOS Evidence:** DSR mengevaluasi Sharpe dari single backtest, bukan Sharpe deret return out-of-sample gabungan (*pooled OOS returns*) yang dipilih melalui proses seleksi parameter. | DELEGASI_044 | ✅ RESOLVED @dd36c80 |
| **RES-WFO-04** | Architecture / Object | 🚨 **P0 (CRITICAL)** | `are/backtest.py:575-595` | **No Canonical WFOEvidence Object:** WFO mengembalikan dictionary longgar tanpa tipe data kanonikal immutable yang menyatukan metadata fold, deret return OOS, hasil seleksi, dan hash pembuktian. | DELEGASI_044 | ✅ RESOLVED @dd36c80 |
| **RES-WFO-05** | Statistics / Aggregation | 📊 **P1 (HIGH)** | `are/backtest.py:582` | **Arithmetic Mean OOS Sharpe Distortion:** WFO menggunakan `mean_oos_sharpe = sum(oos_sharpes)/N` sebagai metrik ringkasan. Rata-rata Sharpe per fold secara matematis bukan Sharpe dari keseluruhan jalur ekuitas OOS gabungan (*pooled OOS Sharpe*). | DELEGASI_044 | ✅ RESOLVED @dd36c80 |
| **RES-WFO-06** | WFO / Leakage | 📊 **P1 (HIGH)** | `are/backtest.py:447, 513` | **Purge Unbound to Label Horizon:** Nilai `purge_bars` tidak memiliki kontrak invarian terhadap horizon label strategi (`assert purge_bars >= label_horizon_bars`), membuka risiko kontaminasi informasi jika strategi memiliki feature lookahead. | DELEGASI_044 | ✅ RESOLVED @dd36c80 |
| **RES-WFO-07** | WFO / Contract | 📊 **P1 (HIGH)** | `are/backtest.py:475-495` | **Fold Dependence & Overlap Undisclosed:** WFO rolling window tidak menghitung dan melaporkan rasio overlap data training dan OOS. OOS yang tumpang tindih tidak boleh diperlakukan sebagai observasi independen pada pooling. | DELEGASI_044 | ✅ RESOLVED @dd36c80 |
| **RES-WFO-08** | Provenance / Audit | 📊 **P1 (HIGH)** | `are/backtest.py:530-534` | **Incomplete Selection Provenance per Fold:** WFO tidak mencatat rincian pemilihan pemenang per fold (skor pemenang, runner-up, skor runner-up, tie count, batas data IS/Purge/OOS) untuk audit stabilitas seleksi. | DELEGASI_044 | ✅ RESOLVED @dd36c80 |
| **RES-WFO-09** | WFO / Degeneracy | 📋 **P2 (MEDIUM)** | `are/backtest.py:532` | **Undocumented Tie-Breaking in Grid Search:** Sorting kandidat pada Sharpe yang sama (*tie*) diserahkan ke urutan default list tanpa pencatatan `tie_count` dan aturan tie-break sekunder (misal: lower Max DD, lower Turnover). | DELEGASI_044 | ✅ RESOLVED @dd36c80 |
| **RES-WFO-10** | Safety / Fail-Closed | 🚨 **P0 (CRITICAL)** | `are/preflight.py:258, 360` | **Final Gate Not Fail-Closed on Missing WFO:** Jika `wfo_evidence` bernilai `None` atau bukti rusak, Final Gate tidak langsung mengeluarkan disposisi `INVALID` / `NO_GO`, melainkan berisiko menggunakan fallback. | DELEGASI_044 | ✅ RESOLVED @dd36c80 |
| **RES-WFO-11** | Test / End-to-End | 📊 **P1 (HIGH)** | `tests/are/` | **Lack of End-to-End Evidence Chain Tests:** Belum ada test suite invarian yang menguji ketahanan rantai penuh dari kebocoran (Selection Leakage, OOS Mutation, DSR Provenance, Missing WFO fail-closed, Warmup Contamination). | DELEGASI_044 | ✅ RESOLVED @dd36c80 |

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
| **RES-COG-03** | 2026-08-29 | DELEGASI_024 | GATED (Menunggu Validasi Stabilitas Bebas Infinite Loop) |

### Gelombang 2 (Diselesaikan di DELEGASI_041)

| ID Residu | Tanggal Tutup | Delegasi / Commit | Deskripsi Solusi Teknis |
| :--- | :--- | :---: | :--- |
| **RES-RED-13** | 2026-08-29 | DELEGASI_041 | Menambahkan tracking state high-water-mark `_peak_equity` pada `MT5ExecutionGateway` dan menghitung standard quantitative peak-equity drawdown `(peak_equity - equity) / peak_equity` pada `get_account_info()`. |
| **RES-RED-14** | 2026-08-29 | DELEGASI_041 | Membedakan secara ketat antara MT5 API error/disconnect (`None`) dan verifikasi flat (`()`). `get_open_positions()` melempar `RuntimeError` pada `None`, dan `emergency_flat()` melanjutkan retry hingga verifikasi selesai. |
| **RES-RED-15** | 2026-08-29 | DELEGASI_041 | Memisahkan canonical scientific payload deterministik dari execution timestamp pada `save_artifact()`. Komputasi identik menghasilkan proof hash SHA-256 identik (content-addressed proof). |
| **RES-RED-16** | 2026-08-29 | DELEGASI_041 | Menambahkan dan mempropagasikan parameter friksi mikrostruktur (`spread_pct`, `slippage_pct`, `commission_pct`) dan `timeframe_seconds` dari `run_crisis_replay()` ke `run_backtest()`. |
| **RES-RED-17** | 2026-08-29 | DELEGASI_041 | Mengganti nama fungsi `run_walk_forward_analysis()` menjadi `run_rolling_oos_evaluation()` untuk menghindari kebingungan semantik, serta menyediakan wrapper deprecated yang memicu `DeprecationWarning`. |
| **RES-RED-18** | 2026-08-29 | DELEGASI_041 | Menambahkan parameter `warmup_bars` (lookback context untuk inisialisasi indikator OOS) dan `purge_bars` (gap pemisah train-test untuk mencegah label leakage) pada `run_walk_forward_optimization()`. |
| **RES-RED-19** | 2026-08-29 | DELEGASI_041 | Menambahkan pelaporan riset-keluarga (`total_trials_per_fold`, `total_trials_all_folds`, `hypothesis_family_size`, `selection_method`) pada output WFO untuk memungkinkan koreksi selection bias pada DSR. |
| **RES-RED-20** | 2026-08-29 | DELEGASI_041 | Mengimplementasikan Wilson score confidence interval 95% untuk estimasi probabilitas ruin, pemisahan path ruin vs terminal ruin, nearest-rank percentile (NIST), dan pelaporan varians ekuitas pada `monte_carlo_simulation()`. |
| **RES-RED-22** | 2026-08-29 | DELEGASI_041 | Menerapkan guard clause fail-closed pada `run_backtest()`: menolak nilai friksi negatif (friction credit), NaN, Inf, tipe non-numerik, serta timeframe nol atau negatif. |
