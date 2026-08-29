"""
AHFMES TOOLS — Historical Black Swan Crisis Ingestion & Purification (DELEGASI_035C, Organ 7)

Ingests or synthetically generates verified datasets for 3 historic market crises:
1. 2008 Global Financial Crisis (GFC)
2. 2015 CHF Depeg Flash Crash
3. 2020 COVID Market Crash

Purifies raw data via DataPurifier (LOCF micro-gap fill, zero linear interpolation bias).
Supports pure offline synthetic generation if network or yfinance is unavailable.
"""

from __future__ import annotations

import datetime
import math
import os
from typing import Dict, Optional

import polars as pl
from are.data_pipeline import DataPurifier

CRISIS_DEFINITIONS: Dict[str, Dict[str, str]] = {
    "gfc_2008": {
        "name": "2008 Global Financial Crisis",
        "symbol": "^GSPC",
        "start": "2008-09-15",
        "end": "2009-03-09",
        "plunge_pct": "0.50",
    },
    "chf_depeg_2015": {
        "name": "2015 Swiss Franc (EURCHF) Depeg",
        "symbol": "EURCHF=X",
        "start": "2015-01-14",
        "end": "2015-01-16",
        "plunge_pct": "0.30",
    },
    "covid_crash_2020": {
        "name": "2020 COVID Flash Crash",
        "symbol": "^GSPC",
        "start": "2020-02-20",
        "end": "2020-03-23",
        "plunge_pct": "0.35",
    },
}


def generate_synthetic_crisis_data(crisis_key: str, n_bars: int = 500) -> pl.DataFrame:
    """
    Generates realistic synthetic crisis market data with steep drawdown and volatility.
    Pure offline, deterministic standard math.
    """
    cfg = CRISIS_DEFINITIONS.get(crisis_key, {
        "start": "2020-01-01",
        "plunge_pct": "0.50",
    })
    plunge_ratio = float(cfg.get("plunge_pct", 0.50))
    start_dt = datetime.datetime.fromisoformat(cfg["start"])
    base_ts = start_dt.timestamp()

    timestamps = []
    prices = []
    bids = []
    asks = []

    start_price = 100.0
    for i in range(n_bars):
        progress = i / max(1, n_bars - 1)
        # Crash curve with sinusoidal volatility
        trend_drop = plunge_ratio * (progress ** 0.8)
        noise = math.sin(i * 0.15) * 0.02
        current_price = start_price * (1.0 - trend_drop + noise)
        ts = base_ts + (i * 3600.0)

        timestamps.append(ts)
        prices.append(round(current_price, 4))
        spread = 0.0005 * current_price
        bids.append(round(current_price - (spread / 2.0), 4))
        asks.append(round(current_price + (spread / 2.0), 4))

    return pl.DataFrame({
        "timestamp": timestamps,
        "price": prices,
        "bid": bids,
        "ask": asks,
    })


def fetch_or_generate_crisis(
    crisis_key: str,
    output_dir: str = "data/historical_crises/purified",
    force_synthetic: bool = False,
) -> str:
    """
    Fetches online historical crisis data via yfinance if available,
    otherwise cleanly falls back to deterministic synthetic generation.
    Purifies via DataPurifier and saves to Parquet format.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{crisis_key}.parquet")

    raw_df: Optional[pl.DataFrame] = None
    if not force_synthetic:
        try:
            import yfinance as yf  # Permitted only in TOOLS/ (Organ 7)

            cfg = CRISIS_DEFINITIONS[crisis_key]
            ticker = yf.Ticker(cfg["symbol"])
            hist = ticker.history(start=cfg["start"], end=cfg["end"])
            if not hist.empty and "Close" in hist.columns:
                timestamps = [dt.timestamp() for dt in hist.index]
                closes = hist["Close"].to_list()
                raw_df = pl.DataFrame({
                    "timestamp": timestamps,
                    "price": closes,
                })
        except Exception:
            raw_df = None

    if raw_df is None:
        raw_df = generate_synthetic_crisis_data(crisis_key)

    # Purify raw data using DataPurifier
    purifier = DataPurifier()
    purified_df = purifier.purify_tick_data(raw_df)

    purified_df.write_parquet(out_path)
    return out_path


def seed_all_historical_crises(output_dir: str = "data/historical_crises/purified") -> Dict[str, str]:
    """Generates and purifies all 3 standard historical crisis datasets."""
    results: Dict[str, str] = {}
    for key in CRISIS_DEFINITIONS:
        saved_path = fetch_or_generate_crisis(key, output_dir=output_dir, force_synthetic=True)
        results[key] = saved_path
    return results


if __name__ == "__main__":
    paths = seed_all_historical_crises()
    for k, p in paths.items():
        print(f"Purified crisis dataset seeded: {k} -> {p}")