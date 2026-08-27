# DELEGASI 017 — Engineering AI: Coding Slice-2 P001 (Alpha Discovery Engine, Feature Library, Ingestion & P001 Program Runner)

Status: **DELEGASI AKTIF / AUTHORIZED — CHARTER T4 RATIFIED**  
Diterbitkan: Lead Architect & Auditor · Baseline `@4fe32f0` (269 tests pass)

> Cara pakai: Tempelkan SELURUH blok prompt di bawah ke sesi Engineering AI.

---

## 📋 PROMPT UNTUK ENGINEERING AI (salin dari sini)

```text
PERAN
Kamu adalah ENGINEERING AI (bukan arsitek).
GERBANG: DELEGASI_017 — CODING SLICE-2 P001 (ALPHA ENGINE & INGESTION) — AUTHORIZED
HANYA untuk lingkup di bawah. Luar lingkup = DILARANG.

BASELINE
HEAD saat delegasi = 4fe32f0 (P001 Slice-1 CLOSED, 269 tests pass, Manifest V41)
Kontrak rujukan = PROJECT_GOVERNANCE/P001/CONTRACTS/SLICE_2_CONTRACT_P001.md

═══════════════════════════════════════════════════════
BAGIAN A — are/features.py (QUANTITATIVE FEATURE LIBRARY)
═══════════════════════════════════════════════════════
Buat `are/features.py` (stdlib only: math, statistics, typing, dataclasses):
- Fungsi dan kelas ekstraksi fitur matematis:
  1. `calculate_orderbook_imbalance(bids: List[Tuple[float, float]], asks: List[Tuple[float, float]], depth: int = 5) -> Dict[str, float]`:
     Menghitung `imbalance_ratio` (-1.0 s/d 1.0), `micro_price`, `spread`.
  2. `calculate_realized_volatility(prices: List[float], window: int = 20) -> float`:
     Menghitung standard deviation log returns.
  3. `calculate_momentum_indicators(prices: List[float], fast_period: int = 5, slow_period: int = 20) -> Dict[str, float]`:
     Menghitung `ema_fast`, `ema_slow`, `crossover_diff`, `price_velocity`.
  4. `calculate_mean_reversion_zscore(prices: List[float], window: int = 20) -> float`:
     Menghitung z-score harga relatif terhadap rata-rata bergerak window.
  5. Kelas `MarketFeatureExtractor`:
     Metode `extract_features(market_snapshots: List[Dict[str, Any]]) -> Dict[str, float]`.

═══════════════════════════════════════════════════════
BAGIAN B — are/alpha_generator.py (ALPHA HYPOTHESIS GENERATOR)
═══════════════════════════════════════════════════════
Buat `are/alpha_generator.py` (stdlib only: json, hashlib, typing, dataclasses):
- Dataclass `AlphaHypothesisSpec`:
  - `hypothesis_id: str`
  - `family: str` # "MOMENTUM" | "MEAN_REVERSION" | "ORDERBOOK_IMBALANCE"
  - `parameters: Dict[str, Any]`
  - `signal_threshold: float`
  - `stop_loss_pct: float`
  - `take_profit_pct: float`
- Kelas `AlphaGenerator`:
  - Metode `generate_hypotheses(symbol: str, family: Optional[str] = None, count: int = 5) -> List[AlphaHypothesisSpec]`:
    Membangkitkan daftar hipotesis alpha deterministik yang siap disuntikkan ke SearchTreeEngine.
  - Metode `evaluate_alpha_signal(hypothesis: AlphaHypothesisSpec, features: Dict[str, float]) -> Dict[str, Any]`:
    Mengevaluasi fitur pasar dan menghasilkan sinyal `BUY`, `SELL`, atau `HOLD` dengan keyakinan (*confidence*).

═══════════════════════════════════════════════════════
BAGIAN C — are/ingestion.py (MARKET DATA INGESTION PIPELINE)
═══════════════════════════════════════════════════════
Buat `are/ingestion.py` (stdlib only: json, csv, hashlib, time, typing, dataclasses):
- Dataclass `MarketTick`:
  - `symbol: str`, `timestamp: float`, `price: float`, `volume: float`, `side: str`, `bid: float`, `ask: float`, `bid_size: float`, `ask_size: float`
- Kelas `MarketIngestionService`:
  - Inisialisasi: `EvidenceLedger`, `ExperienceStore`
  - Metode `ingest_ticks(symbol: str, ticks: List[Dict[str, Any]], snapshot_id: str) -> EvidenceSnapshot`:
    Mencatat data ke EvidenceLedger sebagai snapshot kriptografis dan menyimpan baris ke ExperienceStore (`market` stream).
  - Metode `ingest_from_csv(symbol: str, csv_content: str, snapshot_id: str) -> EvidenceSnapshot`.

═══════════════════════════════════════════════════════
BAGIAN D — are/p001_program.py (P001 AUTONOMOUS RESEARCH RUNNER)
═══════════════════════════════════════════════════════
Buat `are/p001_program.py` (stdlib only):
- Kelas `P001ProgramRunner`:
  - Mengorkestrasikan seluruh siklus program P001:
    1. Ingestion dataset pasar historis via `MarketIngestionService`.
    2. Pembangkitan kandidat alpha via `AlphaGenerator`.
    3. Eksekusi siklus riset otonom via `ResearchCoordinator`.
    4. Evaluasi performa pada holdout dataset out-of-sample.
    5. Promosi Champion pertama program P001 (`P001_CHAMPION_V1`).

═══════════════════════════════════════════════════════
BAGIAN E — PENGUJIAN UNIT & E2E (tests/are/)
═══════════════════════════════════════════════════════
Buat modul test:
1. `tests/are/test_p001_features.py`: Menguji fungsi matematis ekstraksi fitur (ACC-511).
2. `tests/are/test_p001_alpha_gen.py`: Menguji pembangkitan hipotesis dan evaluasi sinyal (ACC-512).
3. `tests/are/test_p001_ingestion.py`: Menguji ingestion ticks/CSV ke EvidenceLedger & ExperienceStore (ACC-513).
4. `tests/are/test_p001_program.py`: Menguji end-to-end P001 research run & promosi Champion v1 (ACC-514, ACC-515).

KRITERIA TERIMA (fail-closed, semuanya wajib)
  ACC-511 s/d ACC-520 terpenuhi 100%.
  `python -m pytest tests/ -q` $\rightarrow$ seluruh test PASS (269 baseline + test baru P001 Slice-2).
  Zero external dependencies (Python Standard Library only: math, statistics, json, csv, sqlite3, typing).
  Zero test regression (seluruh 269 test lama lulus 100%).
  Working tree clean.

LARANGAN
- Dilarang menambahkan dependensi pihak ketiga (pandas, numpy, scipy, dll.).
- Dilarang menyentuh broker API / live market execution.

PROSES
1. Buat `are/features.py`, `are/alpha_generator.py`, `are/ingestion.py`, `are/p001_program.py`.
2. Buat 4 test files di `tests/are/`.
3. Jalankan `python -m pytest tests/ -q` -> pastikan seluruh 269+ test PASS.
4. Commit di main: "feat(p001): implement Slice-2 Alpha Discovery Engine, Feature Library & Ingestion Pipeline (DELEGASI_017)"
5. Laporkan hasilnya ke Lead Architect.
```
