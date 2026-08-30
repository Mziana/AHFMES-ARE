"""
AHFMES ARE — Real Data Loader
Loads OHLC data from MT5 or parquet files for backtest.
No synthetic fallback — real data or explicit failure.
"""
from __future__ import annotations
import os
import time
from typing import Optional
try:
    import polars as pl
except ImportError:
    raise ImportError("polars required: pip install polars")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "market_data")


def export_mt5_ohlc(symbol: str, timeframe: str = "H1", start: str = "2020-01-01",
                    end: str = "2026-12-31", output_dir: str = DATA_DIR) -> str:
    """Export OHLC data from MT5 to parquet file. Returns file path."""
    try:
        import MetaTrader5 as mt5
    except ImportError:
        raise RuntimeError("MetaTrader5 not installed. Install: pip install MetaTrader5")

    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialization failed: {mt5.last_error()}")

    tf_map = {
        "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30, "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1, "W1": mt5.TIMEFRAME_W1,
    }
    tf = tf_map.get(timeframe.upper(), mt5.TIMEFRAME_H1)

    from datetime import datetime
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")

    rates = mt5.copy_rates_range(symbol, tf, start_dt, end_dt)
    mt5.shutdown()

    if rates is None or len(rates) == 0:
        raise RuntimeError(f"MT5 returned no data for {symbol} {timeframe} {start}-{end}")

    df = pl.DataFrame({
        "timestamp": [r["time"] for r in rates],
        "open": [r["open"] for r in rates],
        "high": [r["high"] for r in rates],
        "low": [r["low"] for r in rates],
        "close": [r["close"] for r in rates],
        "volume": [r["tick_volume"] for r in rates],
    }).with_columns([
        pl.col("close").alias("price"),
        ((pl.col("high") + pl.col("low") + pl.col("close")) / 3).alias("typical_price"),
    ])

    os.makedirs(output_dir, exist_ok=True)
    filename = f"{symbol}_{timeframe}_{start}_{end}.parquet"
    filepath = os.path.join(output_dir, filename)
    df.write_parquet(filepath)
    print(f"Exported {len(df)} bars: {symbol} {timeframe} {start} to {end} -> {filepath}")
    return filepath


def load_ohlc_data(symbol: str, timeframe: str = "H1", start: Optional[str] = None,
                   end: Optional[str] = None) -> pl.DataFrame:
    """Load OHLC data from parquet files. Raises if no data found."""
    os.makedirs(DATA_DIR, exist_ok=True)

    # Try to find existing parquet file matching symbol/timeframe
    pattern = f"{symbol}_{timeframe}_"
    candidates = [f for f in os.listdir(DATA_DIR) if f.startswith(pattern) and f.endswith(".parquet")]

    if not candidates:
        raise FileNotFoundError(
            f"No OHLC data found for {symbol} {timeframe}. "
            f"First export from MT5: python -m are.cli data export --symbol {symbol} --timeframe {timeframe}"
        )

    # Load most recent file
    candidates.sort(reverse=True)
    filepath = os.path.join(DATA_DIR, candidates[0])
    df = pl.read_parquet(filepath)

    # Filter by date range if specified
    if start:
        start_ts = int(time.mktime(time.strptime(start, "%Y-%m-%d")))
        df = df.filter(pl.col("timestamp") >= start_ts)
    if end:
        end_ts = int(time.mktime(time.strptime(end, "%Y-%m-%d")))
        df = df.filter(pl.col("timestamp") <= end_ts)

    if df.height == 0:
        raise ValueError(f"No data in range {start}-{end} for {symbol}")

    print(f"Loaded {df.height} bars: {symbol} {timeframe} from {filepath}")
    return df


def list_available_data():
    """List all available OHLC data files."""
    os.makedirs(DATA_DIR, exist_ok=True)
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".parquet")]
    if not files:
        print("No OHLC data files found. Export from MT5 first.")
        return
    print(f"\n{'Symbol':<12} {'TF':<6} {'Start':<12} {'End':<12} {'Bars':<8} {'File'}")
    print("-" * 70)
    for f in sorted(files):
        parts = f.replace(".parquet", "").split("_")
        if len(parts) >= 4:
            sym, tf, start_d, end_d = parts[0], parts[1], parts[2], parts[3]
            try:
                df = pl.read_parquet(os.path.join(DATA_DIR, f))
                bars = df.height
            except:
                bars = "?"
            print(f"{sym:<12} {tf:<6} {start_d:<12} {end_d:<12} {bars:<8} {f}")
        else:
            print(f"{'?':<12} {'?':<6} {'?':<12} {'?':<12} {'?':<8} {f}")
