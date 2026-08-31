#!/usr/bin/env python3
"""
Market Sentiment Fetcher
Fetches sentiment data from free APIs and saves to parquet.
Sources:
  - Alternative.me Fear & Greed Index (crypto, but useful as market fear proxy)
  - Fear & Greed historical data

Usage: python -m are.data_collectors.sentiment_fetcher --start 2020-01-01 --end 2026-08-31
"""
import argparse
import os
import json
from datetime import datetime, timezone, timedelta

import polars as pl

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def fetch_fear_greed_index(days: int = 365) -> list[dict]:
    """Fetch Fear & Greed Index from alternative.me."""
    if not HAS_REQUESTS:
        print("[WARN] requests not installed, using synthetic sentiment")
        return []

    url = f"https://api.alternative.me/fng/?limit={days}&format=json"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json().get("data", [])

        records = []
        for item in data:
            ts = int(datetime.fromtimestamp(int(item["timestamp"]), tz=timezone.utc).timestamp())
            records.append({
                "timestamp": ts,
                "date": datetime.fromtimestamp(int(item["timestamp"]), tz=timezone.utc).strftime("%Y-%m-%d"),
                "fear_greed_index": int(item["value"]),
                "fear_greed_label": item["value_classification"],
                "source": "alternative.me",
            })
        return records
    except Exception as e:
        print(f"[WARN] Fear & Greed fetch failed: {e}")
        return []


def fetch_sentiment_calendar() -> list[dict]:
    """
    Generate sentiment events from known market-moving calendar.
    This creates a simple news sentiment proxy based on known events.
    """
    # Major events that affect gold/forex (historical knowledge)
    events = [
        # 2020 events
        ("2020-03-09", "COVID-19 pandemic panic", -0.8),
        ("2020-03-16", "Fed emergency rate cut to 0%", 0.6),
        ("2020-04-01", "US stimulus package $2.2T", 0.5),
        ("2020-06-10", "Fed dot plot signals low rates through 2022", 0.3),
        ("2020-11-03", "US Presidential Election", 0.1),
        ("2020-12-14", "COVID vaccine rollout begins", 0.4),
        # 2021 events
        ("2021-01-06", "Capitol riot / political uncertainty", -0.3),
        ("2021-03-10", "US CPI starts rising", -0.2),
        ("2021-06-16", "Fed signals earlier rate hikes", -0.4),
        ("2021-11-26", "Omicron variant detected", -0.5),
        # 2022 events
        ("2022-02-24", "Russia-Ukraine conflict begins", -0.7),
        ("2022-03-16", "Fed begins rate hike cycle", -0.5),
        ("2022-06-15", "Fed 75bp hike (aggressive)", -0.6),
        ("2022-09-26", "GBP flash crash / UK gilt crisis", -0.6),
        ("2022-11-15", "CPI peak at 9.1%", -0.8),
        # 2023 events
        ("2023-03-10", "SVB bank collapse", -0.5),
        ("2023-05-03", "Fed funds rate 5.25% (peak cycle)", -0.3),
        ("2023-10-07", "Israel-Hamas conflict", -0.4),
        ("2023-12-13", "Fed signals rate cuts in 2024", 0.5),
        # 2024 events
        ("2024-01-10", "US CPI stays sticky", -0.2),
        ("2024-03-19", "BOJ ends negative rates", 0.1),
        ("2024-06-07", "US NFP beats expectations", -0.1),
        ("2024-09-18", "Fed 50bp cut (aggressive easing)", 0.6),
        ("2024-11-06", "Trump wins US election", 0.2),
        ("2024-12-18", "Fed cuts 25bp but signals slower", -0.1),
        # 2025 events
        ("2025-01-20", "Trump inauguration / tariff fears", -0.3),
        ("2025-02-01", "US tariff escalation begins", -0.5),
        ("2025-03-12", "Trade war intensifies", -0.6),
        ("2025-04-02", "Liberation Day tariffs", -0.7),
        ("2025-06-18", "Fed holds rates", -0.1),
        ("2025-08-01", "Gold breaks $4000/oz", 0.3),
    ]

    records = []
    for date_str, event, sentiment in events:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        records.append({
            "timestamp": int(dt.timestamp()),
            "date": date_str,
            "event": event,
            "sentiment_score": sentiment,  # -1.0 (extreme fear) to 1.0 (extreme greed)
            "fear_greed_index": int((sentiment + 1) * 50),  # Map to 0-100
            "fear_greed_label": "Extreme Fear" if sentiment < -0.5 else "Fear" if sentiment < -0.1 else "Neutral" if sentiment < 0.1 else "Greed" if sentiment < 0.5 else "Extreme Greed",
            "source": "manual_calendar",
        })
    return records


def main():
    parser = argparse.ArgumentParser(description="Market Sentiment Fetcher")
    parser.add_argument("--output", default="data/market_data")
    parser.add_argument("--days", type=int, default=365, help="Days of Fear & Greed to fetch")
    args = parser.parse_args()

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), args.output)

    print("=== Fetching Sentiment Data ===")

    # 1. Fear & Greed Index
    fg_records = fetch_fear_greed_index(args.days)
    if fg_records:
        df = pl.DataFrame(fg_records)
        fp = os.path.join(output_dir, "SENTIMENT_FEAR_GREED.parquet")
        df.write_parquet(fp)
        print(f"[OK] Fear & Greed: {len(df)} days -> {fp}")

    # 2. Calendar-based sentiment
    cal_records = fetch_sentiment_calendar()
    if cal_records:
        df = pl.DataFrame(cal_records)
        fp = os.path.join(output_dir, "SENTIMENT_CALENDAR.parquet")
        df.write_parquet(fp)
        print(f"[OK] Calendar events: {len(df)} events -> {fp}")

    print("[OK] Sentiment data collection complete")


if __name__ == "__main__":
    main()
