#!/usr/bin/env python3
"""
AHFMES-ARE MT5 Data Exporter
Exports OHLCV, tick data, and validates data integrity.
Usage: python -m are.mt5_export [--symbol XAUUSD] [--timeframes H1,H4,D1] [--start 2020-01-01] [--end 2026-08-31]
"""
import argparse
import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path

import MetaTrader5 as mt5
import polars as pl
import numpy as np


# ─── MT5 Connection ──────────────────────────────────────────────────────────

def connect_mt5() -> bool:
    """Initialize and verify MT5 connection."""
    if not mt5.initialize():
        print(f"[ERROR] MT5 initialize failed: {mt5.last_error()}")
        return False
    info = mt5.terminal_info()
    if info is None:
        print("[ERROR] Cannot get MT5 terminal info")
        return False
    print(f"[OK] MT5 connected: {info.name}, build {info.build}")
    account = mt5.account_info()
    if account:
        print(f"[OK] Account: {account.login}, Balance: ${account.balance:.2f}")
    return True


# ─── Export OHLCV ────────────────────────────────────────────────────────────

def export_ohlcv(symbol: str, timeframe: int, start: str, end: str, output_dir: str) -> bool:
    """Export OHLCV data from MT5 to parquet."""
    tf_names = {
        mt5.TIMEFRAME_M1: "M1", mt5.TIMEFRAME_M5: "M5", mt5.TIMEFRAME_M15: "M15",
        mt5.TIMEFRAME_M30: "M30", mt5.TIMEFRAME_H1: "H1", mt5.TIMEFRAME_H4: "H4",
        mt5.TIMEFRAME_D1: "D1", mt5.TIMEFRAME_W1: "W1", mt5.TIMEFRAME_MN1: "MN1",
    }
    tf_name = tf_names.get(timeframe, f"TF{timeframe}")

    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")

    print(f"  Exporting {symbol} {tf_name} ({start} to {end})...")

    rates = mt5.copy_rates_range(symbol, timeframe, start_dt, end_dt)
    if rates is None or len(rates) == 0:
        print(f"  [WARN] No data returned for {symbol} {tf_name}")
        return False

    df = pl.DataFrame({
        "timestamp": [int(r["time"]) for r in rates],
        "open": [float(r["open"]) for r in rates],
        "high": [float(r["high"]) for r in rates],
        "low": [float(r["low"]) for r in rates],
        "close": [float(r["close"]) for r in rates],
        "volume": [float(r["tick_volume"]) for r in rates],
        "price": [float(r["close"]) for r in rates],  # backward compat
    })

    # Add typical_price
    df = df.with_columns(
        ((pl.col("high") + pl.col("low") + pl.col("close")) / 3.0).alias("typical_price")
    )

    # Add derived columns
    df = df.with_columns([
        pl.col("close").pct_change().alias("returns"),
        (pl.col("high") - pl.col("low")).alias("range"),
        ((pl.col("high") - pl.col("low")) / pl.col("close")).alias("range_pct"),
    ])

    os.makedirs(output_dir, exist_ok=True)
    filename = f"{symbol}_{tf_name}_{start}_{end}.parquet"
    filepath = os.path.join(output_dir, filename)
    df.write_parquet(filepath)

    min_ts = df["timestamp"].min()
    max_ts = df["timestamp"].max()
    min_dt = datetime.fromtimestamp(min_ts, tz=timezone.utc).strftime("%Y-%m-%d") if min_ts else "?"
    max_dt = datetime.fromtimestamp(max_ts, tz=timezone.utc).strftime("%Y-%m-%d") if max_ts else "?"

    print(f"  [OK] {filename}: {len(df)} bars, {min_dt} to {max_dt}, {Path(filepath).stat().st_size/1024:.1f} KB")
    return True


# ─── Export Tick Data ────────────────────────────────────────────────────────

def export_ticks(symbol: str, start: str, end: str, output_dir: str) -> bool:
    """Export tick data from MT5 (limited to recent data)."""
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")

    print(f"  Exporting {symbol} ticks ({start} to {end})...")

    ticks = mt5.copy_ticks_range(symbol, start_dt, end_dt, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        print(f"  [WARN] No tick data returned for {symbol}")
        return False

    df = pl.DataFrame({
        "timestamp": [int(t["time"]) for t in ticks],
        "bid": [float(t["bid"]) for t in ticks],
        "ask": [float(t["ask"]) for t in ticks],
        "last": [float(t["last"]) for t in ticks],
        "volume": [float(t["volume"]) for t in ticks],
        "flags": [int(t["flags"]) for t in ticks],
    })

    df = df.with_columns([
        ((pl.col("bid") + pl.col("ask")) / 2.0).alias("mid"),
        (pl.col("ask") - pl.col("bid")).alias("spread"),
        ((pl.col("ask") - pl.col("bid")) / pl.col("mid") * 100).alias("spread_bps"),
    ])

    os.makedirs(output_dir, exist_ok=True)
    filename = f"{symbol}_TICKS_{start}_{end}.parquet"
    filepath = os.path.join(output_dir, filename)
    df.write_parquet(filepath)

    print(f"  [OK] {filename}: {len(df)} ticks, {Path(filepath).stat().st_size/1024:.1f} KB")
    return True


# ─── Data Validation ─────────────────────────────────────────────────────────

def validate_data(filepath: str) -> dict:
    """Validate parquet data integrity."""
    df = pl.read_parquet(filepath)
    report = {
        "file": os.path.basename(filepath),
        "rows": len(df),
        "columns": df.columns,
        "issues": [],
    }

    if "timestamp" in df.columns:
        ts = df["timestamp"]
        min_ts = ts.min()
        max_ts = ts.max()
        if min_ts and max_ts:
            start_dt = datetime.fromtimestamp(min_ts, tz=timezone.utc)
            end_dt = datetime.fromtimestamp(max_ts, tz=timezone.utc)
            report["start"] = start_dt.strftime("%Y-%m-%d %H:%M")
            report["end"] = end_dt.strftime("%Y-%m-%d %H:%M")

            # Check for gaps
            diffs = ts.diff().drop_nulls()
            if len(diffs) > 0:
                median_diff = diffs.median()
                gaps = diffs.filter(diffs > median_diff * 2.5)
                if len(gaps) > 0:
                    report["issues"].append(f"GAP detected: {len(gaps)} large gaps (>{median_diff*2.5:.0f}s)")

                # Check for duplicate timestamps
                duplicates = ts.filter(ts.is_duplicated())
                if len(duplicates) > 0:
                    report["issues"].append(f"Duplicate timestamps: {len(duplicates)}")

    # Check for null values
    null_counts = df.null_count()
    for col in df.columns:
        nc = null_counts[col][0]
        if nc > 0:
            report["issues"].append(f"NULL in {col}: {nc}/{len(df)} ({nc/len(df)*100:.1f}%)")

    # Check for infinite values in numeric columns
    for col in df.columns:
        if df[col].dtype in [pl.Float32, pl.Float64]:
            inf_count = df[col].filter(df[col].is_infinite()).len()
            if inf_count > 0:
                report["issues"].append(f"INF in {col}: {inf_count}")

    report["valid"] = len(report["issues"]) == 0
    return report


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MT5 Data Exporter for AHFMES-ARE")
    parser.add_argument("--symbol", default="XAUUSD", help="Symbol to export (default: XAUUSD)")
    parser.add_argument("--symbols", default="XAUUSD,EURUSD,GBPUSD,USDJPY", help="Multiple symbols (comma-separated)")
    parser.add_argument("--timeframes", default="M15,H1,H4,D1", help="Timeframes (comma-separated)")
    parser.add_argument("--start", default="2020-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2026-08-31", help="End date (YYYY-MM-DD)")
    parser.add_argument("--ticks", action="store_true", help="Also export tick data")
    parser.add_argument("--tick-start", default="2026-07-01", help="Tick data start (limited by MT5)")
    parser.add_argument("--output", default="data/market_data", help="Output directory")
    parser.add_argument("--validate-only", action="store_true", help="Only validate existing files")
    args = parser.parse_args()

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), args.output)

    # Validate only mode
    if args.validate_only:
        print("\n=== Data Validation ===")
        for f in sorted(os.listdir(output_dir)):
            if f.endswith(".parquet"):
                filepath = os.path.join(output_dir, f)
                report = validate_data(filepath)
                status = "[OK]" if report["valid"] else "[WARN]"
                print(f"  {status} {report['file']}: {report['rows']} rows, {report.get('start','?')} to {report.get('end','?')}")
                for issue in report["issues"]:
                    print(f"       -> {issue}")
        return

    # Export mode
    if not connect_mt5():
        sys.exit(1)

    tf_map = {
        "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30, "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1, "W1": mt5.TIMEFRAME_W1, "MN1": mt5.TIMEFRAME_MN1,
    }

    symbols = [s.strip() for s in args.symbols.split(",")]
    timeframes = [t.strip() for t in args.timeframes.split(",")]

    print(f"\n=== Exporting OHLCV Data ===")
    print(f"  Symbols: {symbols}")
    print(f"  Timeframes: {timeframes}")
    print(f"  Period: {args.start} to {args.end}")

    exported = 0
    for symbol in symbols:
        info = mt5.symbol_info(symbol)
        if info is None:
            print(f"\n  [SKIP] {symbol} not found in MT5")
            continue
        print(f"\n--- {symbol} (point={info.point}, digits={info.digits}) ---")
        for tf_str in timeframes:
            tf = tf_map.get(tf_str)
            if tf is None:
                print(f"  [SKIP] Unknown timeframe: {tf_str}")
                continue
            if export_ohlcv(symbol, tf, args.start, args.end, output_dir):
                exported += 1

    # Export tick data
    if args.ticks:
        print(f"\n=== Exporting Tick Data ===")
        for symbol in symbols:
            info = mt5.symbol_info(symbol)
            if info is None:
                continue
            export_ticks(symbol, args.tick_start, args.end, output_dir)

    mt5.shutdown()
    print(f"\n=== Export Complete: {exported} files ===")

    # Validate all exported data
    print(f"\n=== Data Validation ===")
    for f in sorted(os.listdir(output_dir)):
        if f.endswith(".parquet"):
            filepath = os.path.join(output_dir, f)
            report = validate_data(filepath)
            status = "[OK]" if report["valid"] else "[WARN]"
            print(f"  {status} {report['file']}: {report['rows']} rows, {report.get('start','?')} to {report.get('end','?')}")
            for issue in report["issues"]:
                print(f"       -> {issue}")


if __name__ == "__main__":
    main()
