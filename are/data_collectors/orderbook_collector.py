#!/usr/bin/env python3
"""
MT5 Orderbook Snapshot Collector
Takes periodic snapshots of Level 2 depth and saves to parquet.
Usage: python -m are.data_collectors.orderbook_collector --symbol XAUUSD --interval 60 --duration 3600
"""
import argparse
import time
import os
import json
from datetime import datetime, timezone

import MetaTrader5 as mt5
import polars as pl


def snapshot_orderbook(symbol: str) -> dict | None:
    """Take a single orderbook snapshot from MT5."""
    if not mt5.symbol_select(symbol, True):
        return None

    book = mt5.market_book_get(symbol)
    if book is None:
        return None

    bids = []
    asks = []

    for item in book:
        if item.type == mt5.BOOK_TYPE_BUY or item.type == mt5.BOOK_TYPE_BUY_MARKET:
            bids.append({"price": item.price, "volume": item.volume, "orders": item.order})
        elif item.type == mt5.BOOK_TYPE_SELL or item.type == mt5.BOOK_TYPE_SELL_MARKET:
            asks.append({"price": item.price, "volume": item.volume, "orders": item.order})

    if not bids and not asks:
        return None

    bid_total = sum(b["volume"] for b in bids)
    ask_total = sum(a["volume"] for a in asks)
    imbalance = (bid_total - ask_total) / (bid_total + ask_total) if (bid_total + ask_total) > 0 else 0.0

    return {
        "timestamp": int(time.time()),
        "symbol": symbol,
        "bid_depth": bid_total,
        "ask_depth": ask_total,
        "imbalance": imbalance,
        "bid_levels": len(bids),
        "ask_levels": len(asks),
        "best_bid": bids[0]["price"] if bids else 0.0,
        "best_ask": asks[0]["price"] if asks else 0.0,
        "spread": (asks[0]["price"] - bids[0]["price"]) if (bids and asks) else 0.0,
        "bids_json": json.dumps(bids[:20]),  # Top 20 levels
        "asks_json": json.dumps(asks[:20]),
    }


def collect(symbol: str, interval: int, duration: int, output_dir: str):
    """Collect orderbook snapshots over a duration."""
    if not mt5.initialize():
        print(f"[ERROR] MT5 init failed: {mt5.last_error()}")
        return

    print(f"[OK] Collecting orderbook for {symbol} every {interval}s for {duration}s")

    snapshots = []
    start_time = time.time()
    count = 0

    while time.time() - start_time < duration:
        snap = snapshot_orderbook(symbol)
        if snap:
            snapshots.append(snap)
            count += 1
            if count % 10 == 0:
                print(f"  [{count}] bid_depth={snap['bid_depth']:.0f} ask_depth={snap['ask_depth']:.0f} imbalance={snap['imbalance']:.3f}")
        time.sleep(interval)

    mt5.shutdown()

    if not snapshots:
        print("[WARN] No snapshots collected")
        return

    # Save to parquet
    df = pl.DataFrame(snapshots)
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    fp = os.path.join(output_dir, f"{symbol}_ORDERBOOK_{ts}.parquet")
    df.write_parquet(fp)
    print(f"[OK] Saved {len(snapshots)} snapshots to {fp}")


def main():
    parser = argparse.ArgumentParser(description="MT5 Orderbook Collector")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between snapshots")
    parser.add_argument("--duration", type=int, default=3600, help="Total collection time in seconds")
    parser.add_argument("--output", default="data/market_data")
    args = parser.parse_args()

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), args.output)
    collect(args.symbol, args.interval, args.duration, output_dir)


if __name__ == "__main__":
    main()
