# RED TEAM REMEDIATION PLAN: 3-STAGE EXECUTION ROADMAP

Status: **RATIFIED REMEDIATION ROADMAP**  
Baseline Inisiasi: **740873f on main**  
Otoritas: **Lead Architect & Red Team Advisory Council**

---

## 🎯 Peta Jalan Remediasi 3-Tahap

Untuk menyelesaikan seluruh 12 residu teknis tanpa merusak stabilitas repositori, perbaikan dibagi secara atomik ke dalam 3 gelombang delegasi pengerasan:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🗺️ ROADMAP EKSEKUSI REMEDIASI RED TEAM                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 🚨 TAHAP 1: RUNTIME TRUTH & EXECUTION SAFETY (DELEGASI_038) ─── [P0 BLOCKER]│
│    • Target: RES-RED-01 s/d RES-RED-06 + RES-RED-12                         │
│    • 1. Sliding 60-Second Window Order Timestamp Ledger di Runner/CSK       │
│    • 2. Live MT5 Gateway `get_open_positions()` via `mt5.positions_get()`   │
│    • 3. Fail-Closed MT5: Exception jika `use_mock=False` & library missing  │
│    • 4. Guaranteed Flat Verification Loop (`len(positions_get()) == 0`)     │
│    • 5. Real-Time Account Balance & Dynamic Drawdown Polling                │
│    • 6. Non-Silent Exception Handling & Transition to State HALTED          │
│    • 7. Sinkronisasi Root README.md terhadap CURRENT_AUTHORITY_INDEX.md     │
│                                                                             │
│ 📊 TAHAP 2: SCIENTIFIC PROVENANCE & WFO REALITY (DELEGASI_039) ── [P1 RIGOR]│
│    • Target: RES-RED-07, RES-RED-08, RES-RED-09                             │
│    • 1. Bar-Timeframe Scaled Sharpe Ratio Annualization Formula             │
│    • 2. Provenance Label: Ganti `"0"*64` VERIFIED menjadi UNPROVEN          │
│    • 3. True Walk-Forward Optimization (WFO): Separasi Parameter Fitting    │
│                                                                             │
│ 🌪️ TAHAP 3: REALISTIC SIMULATION & PATH-DEPENDENCY (DELEGASI_040) ─ [P1 SIM]│
│    • Target: RES-RED-10, RES-RED-11                                         │
│    • 1. Realistic Backtest Friction Model (Spread, Slippage, Fee, Swap)     │
│    • 2. Block/Regime Bootstrap Monte Carlo (Preserve Volatility Clustering) │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Detail Rencana per Delegasi

### 1. DELEGASI_038: Runtime Truth & Execution Safety (P0)
- **Komponen Terdampak:** `are/mt5_gateway.py`, `are/mt5_runner.py`, `are/safety.py`, `README.md`.
- **Spesifikasi Teknis:**
  - `OrderRateTracker`: Menyimpan deque timestamp order yang dikirim dalam 60 detik terakhir.
  - `MT5ExecutionGateway`: Melempar `RuntimeError` jika `use_mock=False` gagal impor `MetaTrader5`.
  - `emergency_flat()`: Mengirim close request lalu memanggil `positions_get()` sampai terkonfirmasi 0. Jika dalam 3 retry masih ada sisa, melempar alert status `CRITICAL`.
  - `MT5LiveRunner`: Membaca `account_info().equity` dan `balance` langsung dari MT5 terminal untuk menghitung `drawdown = (balance - equity) / balance`.

### 2. DELEGASI_039: Scientific Provenance & True WFO (P1)
- **Komponen Terdampak:** `are/backtest.py`, `are/validation.py`.
- **Spesifikasi Teknis:**
  - `calculate_sharpe_ratio()`: Menerima parameter `timeframe_seconds` (default 60s -> multiplier $\sqrt{252 \times 1440}$).
  - `ValidationService`: Status provenance `"VERIFIED"` hanya diberikan jika hash tidak nol dan lolos verifikasi kriptografis. Hash nol dilabeli `"SENTINEL_UNPROVEN"`.
  - `run_walk_forward_optimization()`: Menerima `strategy_factory(params)` dan `param_grid`, melakukan fitting di `train_slice`, membekukan parameter terbaik, lalu menguji di `test_slice`.

### 3. DELEGASI_040: Realistic Microstructure Simulation (P1)
- **Komponen Terdampak:** `are/backtest.py`, `are/validation.py`.
- **Spesifikasi Teknis:**
  - `BacktestEngine`: Menghitung P&L berbasis $P_{\text{execution}}$ (termasuk half-spread bid/ask, komisi per lot, slippage acak berbasis volatilitas).
  - `monte_carlo_simulation()`: Menambahkan mode `Block Bootstrap` untuk mempertahankan autokorelasi dan clustering volatilitas.
