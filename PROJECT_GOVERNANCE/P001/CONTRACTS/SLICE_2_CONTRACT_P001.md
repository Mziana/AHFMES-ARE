# SLICE 2 CONTRACT — PROGRAM P001 (Autonomous Alpha Discovery Engine & Ingestion Pipeline)

Status: **FROZEN T3 — RATIFIED FOR IMPLEMENTATION / AUTHORIZED**  
Fase: **P001 Slice-2 (Quantitative Features, Alpha Generator & Ingestion)**  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` & `ENGINEERING/RULES.md`  
Baseline: `@4fe32f0` (269 tests pass, Manifest V41)

---

## 1. Lingkup Komponen P001 Slice-2

### A. Quantitative Feature Library (`are/features.py`)
- Ekstraksi fitur pasar kuantitatif matematis murni (stdlib only: `math`, `typing`, `dataclasses`):
  1. `OrderbookImbalance`: rasio kedalaman bid/ask, micro-price, dan order book skew.
  2. `VolatilityFeatures`: rolling realized volatility, Parkinson volatility proxy, dan true range metrics.
  3. `MomentumFeatures`: directional momentum indicator, fast/slow exponential moving averages crossover, velocity.
  4. `MeanReversionFeatures`: price z-score divergence terhadap moving mean, Bollinger band quantile.
  5. `MarketFeatureExtractor`: fungsi terpadu `extract_features(market_data: List[Dict[str, Any]]) -> Dict[str, float]` yang deterministik.

### B. Alpha Hypothesis Generator (`are/alpha_generator.py`)
- Generator hipotesis kuantitatif berbasis parameter space terstruktur untuk `SearchTreeEngine`:
  1. `AlphaTemplate`: definisi formula matematis (misal: `MOMENTUM_BREAKOUT`, `MEAN_REVERSION_Z`, `IMBALANCE_FLOW`).
  2. `AlphaGenerator`: membangkitkan kombinasi hipotesis dan parameter evaluasi secara terstruktur.

### C. Market Data Ingestion Pipeline (`are/ingestion.py`)
- Pipeline pencatatan data pasar ke dalam bukti kriptografis:
  1. `MarketTick` / `MarketBar`: dataclass representasi tick atau candle.
  2. `MarketIngestionService`: mem-parsing data pasar (CSV / JSON / dict list), membuat `EvidenceSnapshot` di `EvidenceLedger`, dan menginjeksi record ke `ExperienceStore` dengan hash provenance terverifikasi.

### D. P001 Autonomous Research Program Runner (`are/p001_program.py`)
- `P001ProgramRunner`: mengorkestrasikan seluruh alur riset P001 secara otomatis:
  1. Ingestion dataset historis pasar.
  2. Eksplorasi Search Tree alpha hipotesis.
  3. Validasi holdout out-of-sample via `ValidationService`.
  4. Komparasi adversarial via `CriticEngine`.
  5. Promosi governance via `GovernorEngine` & aktivasi di `ChampionRegistry` menghasilkan **P001 Champion Strategy v1**.

---

## 2. Kriteria Penerimaan Formal (ACC-511 s/d ACC-520)

| ID | Deskripsi Kriteria Penerimaan | Verifikasi |
|---|---|---|
| **ACC-511** | `are/features.py` mengekstrak fitur kuantitatif (imbalance, volatility, momentum, mean-reversion) secara matematis | `test_p001_features.py` |
| **ACC-512** | `are/alpha_generator.py` membangkitkan formula alpha kuantitatif yang kompatibel dengan `SearchTreeEngine` | `test_p001_alpha_gen.py` |
| **ACC-513** | `are/ingestion.py` mencatat dataset pasar ke `EvidenceLedger` dan `ExperienceStore` secara kriptografis | `test_p001_ingestion.py` |
| **ACC-514** | `are/p001_program.py` mengorkestrasikan siklus riset P001 penuh dan mempromosikan Champion v1 | `test_p001_program.py` |
| **ACC-515** | Integrasi E2E Penuh: Ingestion $\rightarrow$ Alpha Generation $\rightarrow$ Holdout Validation $\rightarrow$ Champion Succession | E2E test |
| **ACC-516** | Zero external dependencies (murni Python Standard Library: `math`, `json`, `csv`, `sqlite3`, dll.) | Code audit |
| **ACC-517** | Seluruh test suite (269 baseline + test baru P001 Slice-2) 100% PASS | `python -m pytest tests/` |
| **ACC-518** | Repositori bersih tanpa file sementara (`working tree clean`) | `git status` |
| **ACC-519** | Dual-implementation `manifest_hash` & `blob_verifier` 100% PASS | `TOOLS/` verification |
| **ACC-520** | Dilarang menyentuh broker API / live market execution | Strict firewall audit |

---

## 3. Batasan & Larangan Keras
- **DILARANG** menambahkan dependensi eksternal seperti `pandas`, `numpy`, `scipy` (WAJIB stdlib-only).
- **DILARANG** membuka akses eksekusi live ke broker.
