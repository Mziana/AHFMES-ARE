#!/usr/bin/env python3
"""
Macroeconomic Data Fetcher
Fetches macro data from FRED (Federal Reserve Economic Data) API.
Free API key available at https://fred.stlouisfed.org/docs/api/api_key.html

Usage:
  python -m are.data_collectors.macro_fetcher --api-key YOUR_KEY
  python -m are.data_collectors.macro_fetcher --offline  # Use built-in historical data

Without API key, uses built-in historical data (limited to key dates).
"""
import argparse
import os
from datetime import datetime, timezone

import polars as pl

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# FRED Series IDs for key macro indicators
FRED_SERIES = {
    "DFF": "Federal Funds Effective Rate",
    "DGS10": "10-Year Treasury Rate",
    "DGS2": "2-Year Treasury Rate",
    "DGS30": "30-Year Treasury Rate",
    "CPIAUCSL": "Consumer Price Index (CPI)",
    "UNRATE": "Unemployment Rate",
    "GDP": "Gross Domestic Product",
    "T10Y2Y": "10Y-2Y Treasury Spread (recession indicator)",
    "DXY": "US Dollar Index (ICE)",
    "VIXCLS": "CBOE Volatility Index (VIX)",
    "GOLDAMGBD228NLBM": "Gold Price (London PM Fix)",
}


def fetch_fred_series(series_id: str, api_key: str, start: str = "2020-01-01", end: str = "2026-08-31") -> list[dict]:
    """Fetch a single series from FRED API."""
    if not HAS_REQUESTS:
        return []

    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
        "observation_end": end,
        "frequency": "m",  # Monthly
    }

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        observations = data.get("observations", [])

        records = []
        for obs in observations:
            if obs["value"] == ".":
                continue
            dt = datetime.strptime(obs["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            records.append({
                "timestamp": int(dt.timestamp()),
                "date": obs["date"],
                "series_id": series_id,
                "series_name": FRED_SERIES.get(series_id, series_id),
                "value": float(obs["value"]),
            })
        return records
    except Exception as e:
        print(f"  [WARN] Failed to fetch {series_id}: {e}")
        return []


def get_offline_macro_data() -> list[dict]:
    """
    Built-in macro data for key dates (no API key needed).
    Source: FRED, BLS, Federal Reserve historical publications.
    """
    # Key macro events with approximate values
    data = [
        # Fed Funds Rate (monthly averages)
        ("2020-01-01", "DFF", "Federal Funds Effective Rate", 1.55),
        ("2020-03-01", "DFF", "Federal Funds Effective Rate", 0.65),
        ("2020-04-01", "DFF", "Federal Funds Effective Rate", 0.05),
        ("2020-06-01", "DFF", "Federal Funds Effective Rate", 0.08),
        ("2020-12-01", "DFF", "Federal Funds Effective Rate", 0.09),
        ("2021-06-01", "DFF", "Federal Funds Effective Rate", 0.08),
        ("2021-12-01", "DFF", "Federal Funds Effective Rate", 0.08),
        ("2022-03-01", "DFF", "Federal Funds Effective Rate", 0.20),
        ("2022-05-01", "DFF", "Federal Funds Effective Rate", 0.77),
        ("2022-06-01", "DFF", "Federal Funds Effective Rate", 1.58),
        ("2022-07-01", "DFF", "Federal Funds Effective Rate", 2.33),
        ("2022-09-01", "DFF", "Federal Funds Effective Rate", 3.08),
        ("2022-11-01", "DFF", "Federal Funds Effective Rate", 3.83),
        ("2022-12-01", "DFF", "Federal Funds Effective Rate", 4.33),
        ("2023-02-01", "DFF", "Federal Funds Effective Rate", 4.57),
        ("2023-03-01", "DFF", "Federal Funds Effective Rate", 4.65),
        ("2023-05-01", "DFF", "Federal Funds Effective Rate", 5.06),
        ("2023-07-01", "DFF", "Federal Funds Effective Rate", 5.12),
        ("2023-09-01", "DFF", "Federal Funds Effective Rate", 5.33),
        ("2023-12-01", "DFF", "Federal Funds Effective Rate", 5.33),
        ("2024-03-01", "DFF", "Federal Funds Effective Rate", 5.33),
        ("2024-06-01", "DFF", "Federal Funds Effective Rate", 5.33),
        ("2024-09-01", "DFF", "Federal Funds Effective Rate", 5.33),
        ("2024-10-01", "DFF", "Federal Funds Effective Rate", 4.83),
        ("2024-12-01", "DFF", "Federal Funds Effective Rate", 4.33),
        ("2025-01-01", "DFF", "Federal Funds Effective Rate", 4.33),
        ("2025-06-01", "DFF", "Federal Funds Effective Rate", 4.33),
        ("2025-08-01", "DFF", "Federal Funds Effective Rate", 4.33),

        # US CPI (Year-over-Year %)
        ("2020-01-01", "CPIAUCSL", "Consumer Price Index (CPI) YoY%", 2.5),
        ("2020-05-01", "CPIAUCSL", "Consumer Price Index (CPI) YoY%", 0.1),
        ("2020-12-01", "CPIAUCSL", "Consumer Price Index (CPI) YoY%", 1.4),
        ("2021-06-01", "CPIAUCSL", "Consumer Price Index (CPI) YoY%", 5.4),
        ("2021-12-01", "CPIAUCSL", "Consumer Price Index (CPI) YoY%", 7.0),
        ("2022-03-01", "CPIAUCSL", "Consumer Price Index (CPI) YoY%", 8.5),
        ("2022-06-01", "CPIAUCSL", "Consumer Price Index (CPI) YoY%", 9.1),
        ("2022-09-01", "CPIAUCSL", "Consumer Price Index (CPI) YoY%", 8.2),
        ("2022-12-01", "CPIAUCSL", "Consumer Price Index (CPI) YoY%", 6.5),
        ("2023-06-01", "CPIAUCSL", "Consumer Price Index (CPI) YoY%", 3.0),
        ("2023-12-01", "CPIAUCSL", "Consumer Price Index (CPI) YoY%", 3.4),
        ("2024-06-01", "CPIAUCSL", "Consumer Price Index (CPI) YoY%", 3.0),
        ("2024-12-01", "CPIAUCSL", "Consumer Price Index (CPI) YoY%", 2.9),
        ("2025-06-01", "CPIAUCSL", "Consumer Price Index (CPI) YoY%", 2.6),

        # US Unemployment Rate
        ("2020-01-01", "UNRATE", "Unemployment Rate", 3.5),
        ("2020-04-01", "UNRATE", "Unemployment Rate", 14.7),
        ("2020-12-01", "UNRATE", "Unemployment Rate", 6.7),
        ("2021-06-01", "UNRATE", "Unemployment Rate", 5.9),
        ("2021-12-01", "UNRATE", "Unemployment Rate", 3.9),
        ("2022-06-01", "UNRATE", "Unemployment Rate", 3.6),
        ("2022-12-01", "UNRATE", "Unemployment Rate", 3.5),
        ("2023-06-01", "UNRATE", "Unemployment Rate", 3.6),
        ("2023-12-01", "UNRATE", "Unemployment Rate", 3.7),
        ("2024-06-01", "UNRATE", "Unemployment Rate", 4.1),
        ("2024-12-01", "UNRATE", "Unemployment Rate", 4.1),
        ("2025-06-01", "UNRATE", "Unemployment Rate", 4.2),

        # 10Y-2Y Treasury Spread (recession indicator)
        ("2020-01-01", "T10Y2Y", "10Y-2Y Treasury Spread", 0.31),
        ("2020-03-01", "T10Y2Y", "10Y-2Y Treasury Spread", -0.01),
        ("2020-08-01", "T10Y2Y", "10Y-2Y Treasury Spread", 0.58),
        ("2021-03-01", "T10Y2Y", "10Y-2Y Treasury Spread", 1.56),
        ("2021-12-01", "T10Y2Y", "10Y-2Y Treasury Spread", 0.78),
        ("2022-03-01", "T10Y2Y", "10Y-2Y Treasury Spread", 0.25),
        ("2022-07-01", "T10Y2Y", "10Y-2Y Treasury Spread", -0.20),
        ("2022-10-01", "T10Y2Y", "10Y-2Y Treasury Spread", -0.42),
        ("2023-03-01", "T10Y2Y", "10Y-2Y Treasury Spread", -0.38),
        ("2023-07-01", "T10Y2Y", "10Y-2Y Treasury Spread", -0.73),
        ("2023-10-01", "T10Y2Y", "10Y-2Y Treasury Spread", -0.30),
        ("2024-01-01", "T10Y2Y", "10Y-2Y Treasury Spread", -0.24),
        ("2024-06-01", "T10Y2Y", "10Y-2Y Treasury Spread", -0.08),
        ("2024-09-01", "T10Y2Y", "10Y-2Y Treasury Spread", 0.08),
        ("2024-12-01", "T10Y2Y", "10Y-2Y Treasury Spread", 0.25),
        ("2025-06-01", "T10Y2Y", "10Y-2Y Treasury Spread", 0.15),

        # VIX (Monthly close approximations)
        ("2020-01-01", "VIXCLS", "CBOE Volatility Index (VIX)", 14.0),
        ("2020-03-01", "VIXCLS", "CBOE Volatility Index (VIX)", 66.0),
        ("2020-06-01", "VIXCLS", "CBOE Volatility Index (VIX)", 31.0),
        ("2020-12-01", "VIXCLS", "CBOE Volatility Index (VIX)", 23.0),
        ("2021-03-01", "VIXCLS", "CBOE Volatility Index (VIX)", 19.0),
        ("2021-12-01", "VIXCLS", "CBOE Volatility Index (VIX)", 29.0),
        ("2022-01-01", "VIXCLS", "CBOE Volatility Index (VIX)", 30.0),
        ("2022-06-01", "VIXCLS", "CBOE Volatility Index (VIX)", 29.0),
        ("2022-10-01", "VIXCLS", "CBOE Volatility Index (VIX)", 32.0),
        ("2023-03-01", "VIXCLS", "CBOE Volatility Index (VIX)", 20.0),
        ("2023-10-01", "VIXCLS", "CBOE Volatility Index (VIX)", 23.0),
        ("2024-03-01", "VIXCLS", "CBOE Volatility Index (VIX)", 13.0),
        ("2024-08-01", "VIXCLS", "CBOE Volatility Index (VIX)", 21.0),
        ("2024-12-01", "VIXCLS", "CBOE Volatility Index (VIX)", 17.0),
        ("2025-03-01", "VIXCLS", "CBOE Volatility Index (VIX)", 22.0),
        ("2025-06-01", "VIXCLS", "CBOE Volatility Index (VIX)", 18.0),
    ]

    records = []
    for date_str, series_id, name, value in data:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        records.append({
            "timestamp": int(dt.timestamp()),
            "date": date_str,
            "series_id": series_id,
            "series_name": name,
            "value": value,
        })
    return records


def main():
    parser = argparse.ArgumentParser(description="Macro Data Fetcher")
    parser.add_argument("--api-key", default=os.environ.get("FRED_API_KEY", ""), help="FRED API key")
    parser.add_argument("--start", default="2020-01-01")
    parser.add_argument("--end", default="2026-08-31")
    parser.add_argument("--output", default="data/market_data")
    parser.add_argument("--offline", action="store_true", help="Use built-in historical data only")
    args = parser.parse_args()

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), args.output)
    os.makedirs(output_dir, exist_ok=True)

    all_records = []

    if args.api_key and not args.offline:
        print("=== Fetching Macro Data from FRED ===")
        for series_id, name in FRED_SERIES.items():
            print(f"  Fetching {series_id} ({name})...")
            records = fetch_fred_series(series_id, args.api_key, args.start, args.end)
            all_records.extend(records)
            print(f"    -> {len(records)} observations")
    else:
        print("=== Using Offline Macro Data ===")
        all_records = get_offline_macro_data()
        print(f"  -> {len(all_records)} observations (built-in historical)")

    if all_records:
        df = pl.DataFrame(all_records).sort("timestamp")
        fp = os.path.join(output_dir, "MACRO_DATA.parquet")
        df.write_parquet(fp)
        print(f"[OK] Macro data: {len(df)} observations -> {fp}")

        # Summary per series
        for sid in df["series_id"].unique():
            subset = df.filter(pl.col("series_id") == sid)
            print(f"  {sid}: {len(subset)} points, {subset['value'].min():.2f} to {subset['value'].max():.2f}")


if __name__ == "__main__":
    main()
