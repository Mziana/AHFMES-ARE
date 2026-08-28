# DELEGASI 018 — Engineering AI: Coding MT5_BRIDGE (Live Feed Adapter, Safety-Gated Gateway & Demo Runner)

Status: **DELEGASI AKTIF / AUTHORIZED — CHARTER T4 RATIFIED**  
Diterbitkan: Lead Architect & Auditor · Baseline `@6a3763d` (281 tests pass)

> Cara pakai: Tempelkan SELURUH blok prompt di bawah ke sesi Engineering AI.

---

## 📋 PROMPT UNTUK ENGINEERING AI (salin dari sini)

```text
PERAN
Kamu adalah ENGINEERING AI (bukan arsitek).
GERBANG: DELEGASI_018 — CODING MT5_BRIDGE — AUTHORIZED
HANYA untuk lingkup di bawah. Luar lingkup = DILARANG.

BASELINE
HEAD saat delegasi = 6a3763d (P001 CLOSED, 281 tests pass, Manifest V41)
Kontrak rujukan = PROJECT_GOVERNANCE/MT5_BRIDGE/CONTRACTS/SLICE_1_CONTRACT_MT5.md

═══════════════════════════════════════════════════════
BAGIAN A — are/mt5_feed.py (METATRADER 5 MARKET FEED ADAPTER)
═══════════════════════════════════════════════════════
Buat `are/mt5_feed.py` (stdlib only: json, time, math, typing, dataclasses):
- Dataclass `MT5FeedConfig`:
  - `login: Optional[int] = None`
  - `server: Optional[str] = None`
  - `password: Optional[str] = None`
  - `path: Optional[str] = None`
  - `symbol: str = "BTCUSD"`
  - `timeframe: str = "M1"`
  - `use_mock: bool = True`
- Kelas `MT5MockFeed`:
  - Metode `initialize() -> bool`
  - Metode `get_latest_ticks(symbol: str, count: int = 10) -> List[Dict[str, Any]]`:
    Menghasilkan data tick pasar realistis berformat: `{"time": float, "bid": float, "ask": float, "last": float, "volume": float}`.
  - Metode `get_latest_bars(symbol: str, count: int = 20) -> List[Dict[str, Any]]`:
    Menghasilkan data candle bar: `{"time": float, "open": float, "high": float, "low": float, "close": float, "volume": float}`.
  - Metode `shutdown() -> None`
- Kelas `MT5MarketFeed`:
  - Mengelola koneksi ke MetaTrader5 (menggunakan dynamic import `import MetaTrader5 as mt5` jika tersedia, atau otomatis fallback ke `MT5MockFeed` jika tidak terinstal / `use_mock=True`).
  - Menyediakan API terpadu: `initialize()`, `get_latest_ticks()`, `get_latest_bars()`, `shutdown()`.

═══════════════════════════════════════════════════════
BAGIAN B — are/mt5_gateway.py (SAFETY-GATED EXECUTION GATEWAY)
═══════════════════════════════════════════════════════
Buat `are/mt5_gateway.py` (stdlib only):
- Dataclass `MT5OrderRequest`:
  - `symbol: str`
  - `action: str`  # "BUY" | "SELL"
  - `volume: float`
  - `price: Optional[float] = None`
  - `sl: Optional[float] = None`
  - `tp: Optional[float] = None`
  - `comment: str = "ARE_SIGNAL"`
  - `magic: int = 1001`
- Dataclass `MT5OrderResult`:
  - `success: bool`
  - `retcode: int`
  - `order_id: int`
  - `deal_id: int`
  - `volume: float`
  - `price: float`
  - `comment: str`
  - `timestamp: float`
- Kelas `MT5MockGateway`:
  - Mensimulasikan eksekusi order dan mencatat daftar open positions.
  - Metode `send_order(request: MT5OrderRequest) -> MT5OrderResult`
  - Metode `close_all_positions(symbol: Optional[str] = None) -> List[int]`
  - Metode `get_open_positions() -> List[Dict[str, Any]]`
- Kelas `MT5ExecutionGateway`:
  - Inisialisasi menerima `CapitalSafetyKernel`, `use_mock: bool = True`.
  - Metode `calculate_lot_size(account_equity: float, risk_pct: float = 0.01, stop_loss_points: float = 100.0) -> float`:
    Menghitung ukuran lot aman sesuai batas *position sizing clamping* CSK.
  - Metode `execute_order(request: MT5OrderRequest, current_risk_state: Dict[str, Any]) -> Tuple[bool, Optional[MT5OrderResult], str]`:
    1. Evaluasi batas risiko ke CSK: `safety_kernel.evaluate_order_intent(...)`.
    2. Jika `allowed == False`: tolak eksekusi dan kembalikan alasan penolakan.
    3. Jika `allowed == True`: kirim order ke terminal MT5 (atau `MT5MockGateway`).
  - Metode `emergency_flat() -> int`:
    Menutup seluruh posisi terbuka seketika (*Emergency Close All*).

═══════════════════════════════════════════════════════
BAGIAN C — are/mt5_runner.py (LIVE DEMO RUNNER ORCHESTRATOR)
═══════════════════════════════════════════════════════
Buat `are/mt5_runner.py` (stdlib only):
- Kelas `MT5LiveRunner`:
  - Inisialisasi: `MT5MarketFeed`, `MT5ExecutionGateway`, `OperationalBrain`, `EventStore`, `EvidenceLedger`, `MarketFeatureExtractor`.
  - Metode `step_live_tick(account_equity: float = 10000.0) -> Dict[str, Any]`:
    1. Ambil tick terbaru dari MT5 Feed.
    2. Ekstrak fitur pasar via `MarketFeatureExtractor`.
    3. Evaluasi keputusan sinyal lewat `OperationalBrain.process_tick()`.
    4. Jika sinyal `BUY`/`SELL`: hitung lot dan eksekusi via `MT5ExecutionGateway`.
    5. Jika sinyal `EMERGENCY_FLAT` atau CSK veto: trigger `emergency_flat()`.
    6. Kembalikan dict ringkasan tick.
  - Metode `run_live_loop(max_ticks: Optional[int] = 10, interval_sec: float = 0.1) -> int`.

═══════════════════════════════════════════════════════
BAGIAN D — PENGUJIAN UNIT & INTEGRASI (tests/are/)
═══════════════════════════════════════════════════════
Buat modul test:
1. `tests/are/test_mt5_feed.py`: Menguji feed initialization, polling tick/bar, dan integrasi feature extractor (ACC-601, ACC-602).
2. `tests/are/test_mt5_gateway.py`: Menguji veto CSK pada order, perhitungan lot, eksekusi order, dan emergency flat closure (ACC-603, ACC-604).
3. `tests/are/test_mt5_runner.py`: Menguji orkestrasi live loop end-to-end secara deterministik (ACC-605).

KRITERIA TERIMA (fail-closed, semuanya wajib)
  ACC-601 s/d ACC-610 terpenuhi 100%.
  `python -m pytest tests/ -q` $\rightarrow$ seluruh test PASS (281 baseline + test baru MT5_BRIDGE).
  Zero external hard-dependencies (stdlib-only fallback saat `MetaTrader5` tidak terpasang).
  Zero test regression (seluruh 281 test lama lulus 100%).
  Working tree clean.

LARANGAN
- Dilarang membypass CapitalSafetyKernel saat mengirim order.
- Dilarang membuat eksekusi modal riil tanpa mock simulator.

PROSES
1. Buat `are/mt5_feed.py`, `are/mt5_gateway.py`, `are/mt5_runner.py`.
2. Buat 3 test files di `tests/are/`.
3. Jalankan `python -m pytest tests/ -q` -> pastikan seluruh 281+ test PASS.
4. Commit di main: "feat(mt5): implement MT5 Market Feed, Safety-Gated Gateway & Live Demo Runner (DELEGASI_018)"
5. Laporkan hasilnya ke Lead Architect.
```
