# AHFMES-ARE Data Inventory

> **Catatan:** File data parquet (OHLCV, tick) tidak di-commit ke GitHub karena ukurannya besar (~217 MB).
> Data hanya tersedia di lokal dan harus di-export ulang dari MT5 jika clone ke mesin baru.

## Export Command

```bash
# Export semua data dari MT5 (butuh MT5 terminal yang running)
python -m are.mt5_export

# Export spesifik
python -m are.mt5_export --symbols XAUUSD,EURUSD --timeframes M15,H1,H4,D1 --start 2020-01-01 --end 2026-08-31

# Export tick data (terbatas ~2 bulan terakhir)
python -m are.mt5_export --ticks --tick-start 2026-07-01 --end 2026-08-31

# Validate existing data
python -m are.mt5_export --validate-only
```

## Data yang Tersedia (Lokal)

### OHLCV Bar Data — `data/market_data/`

| Symbol | TF | Period | Bars | Size | File |
|--------|-----|--------|------|------|------|
| XAUUSD | M15 | 2020-01-01 → 2026-08-28 | 157,433 | 5.9 MB | `XAUUSD_M15_2020-01-01_2026-08-31.parquet` |
| XAUUSD | H1 | 2020-01-01 → 2026-08-28 | 39,381 | 1.5 MB | `XAUUSD_H1_2020-01-01_2026-08-31.parquet` |
| XAUUSD | H4 | 2020-01-01 → 2026-08-28 | 10,298 | 422 KB | `XAUUSD_H4_2020-01-01_2026-08-31.parquet` |
| XAUUSD | D1 | 2020-01-02 → 2026-08-28 | 1,719 | 81 KB | `XAUUSD_D1_2020-01-01_2026-08-31.parquet` |
| EURUSD | M15 | 2020-01-01 → 2026-08-28 | 162,509 | 6.2 MB | `EURUSD_M15_2020-01-01_2026-08-31.parquet` |
| EURUSD | H1 | 2020-01-01 → 2026-08-28 | 40,629 | 1.7 MB | `EURUSD_H1_2020-01-01_2026-08-31.parquet` |
| EURUSD | H4 | 2020-01-01 → 2026-08-28 | 10,369 | 542 KB | `EURUSD_H4_2020-01-01_2026-08-31.parquet` |
| EURUSD | D1 | 2020-01-02 → 2026-08-28 | 1,728 | 110 KB | `EURUSD_D1_2020-01-01_2026-08-31.parquet` |
| GBPUSD | M15 | 2020-01-01 → 2026-08-28 | 162,498 | 6.4 MB | `GBPUSD_M15_2020-01-01_2026-08-31.parquet` |
| GBPUSD | H1 | 2020-01-01 → 2026-08-28 | 40,628 | 1.8 MB | `GBPUSD_H1_2020-01-01_2026-08-31.parquet` |
| GBPUSD | H4 | 2020-01-01 → 2026-08-28 | 10,369 | 548 KB | `GBPUSD_H4_2020-01-01_2026-08-31.parquet` |
| GBPUSD | D1 | 2020-01-02 → 2026-08-28 | 1,728 | 111 KB | `GBPUSD_D1_2020-01-01_2026-08-31.parquet` |
| USDJPY | M15 | 2020-01-01 → 2026-08-28 | 162,506 | 5.7 MB | `USDJPY_M15_2020-01-01_2026-08-31.parquet` |
| USDJPY | H1 | 2020-01-01 → 2026-08-28 | 40,631 | 1.5 MB | `USDJPY_H1_2020-01-01_2026-08-31.parquet` |
| USDJPY | H4 | 2020-01-01 → 2026-08-28 | 10,369 | 422 KB | `USDJPY_H4_2020-01-01_2026-08-31.parquet` |
| USDJPY | D1 | 2020-01-02 → 2026-08-28 | 1,728 | 84 KB | `USDJPY_D1_2020-01-01_2026-08-31.parquet` |

### Tick Data — `data/market_data/`

| Symbol | Period | Ticks | Size |
|--------|--------|-------|------|
| XAUUSD | 2026-08-25 → 2026-08-31 | 1,734,133 | 11.3 MB |
| XAUUSD | 2026-07-01 → 2026-08-31 | 16,437,767 | 106 MB |
| EURUSD | 2026-07-01 → 2026-08-31 | 8,278,036 | 22 MB |
| GBPUSD | 2026-07-01 → 2026-08-31 | 6,521,247 | 23 MB |
| USDJPY | 2026-07-01 → 2026-08-31 | 5,504,547 | 22 MB |

### Kolom

**OHLCV:** `timestamp`, `open`, `high`, `low`, `close`, `volume`, `price`, `typical_price`, `returns`, `range`, `range_pct`

**Ticks:** `timestamp`, `bid`, `ask`, `volume`, `mid`, `spread`

## Data yang Belum Tersedia

| Tipe | Catatan |
|------|---------|
| Order Book (Level 2) | Hanya real-time snapshot di MT5, tidak ada historical |
| Market Sentiment | Tidak tersedia di MT5 — perlu sumber eksternal (Fear & Greed, VIX, dll) |
| News/Calendar | Tidak tersedia di MT5 — perlu integrasi Kalender Ekonomi |
| Macro Data (CPI, GDP, Rate) | Tidak tersedia di MT5 — perlu integrasi FRED/BIS |

## Data Validation

Parquet files sudah divalidasi dengan gap check:
- Gaps yang terdeteksi adalah weekend/holiday (normal untuk forex)
- Tidak ada null values signifikan (kecuali 1 bar pertama dari returns computation)
- Semua file memiliki kolom yang konsisten
