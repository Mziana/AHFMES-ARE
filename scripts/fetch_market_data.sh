#!/bin/bash
# Fetch XAUUSD market data from MT5 (last 2 years)
# Usage: bash scripts/fetch_market_data.sh
# Requires: MT5 terminal running, MetaTrader5 Python package installed

set -e

SYMBOL="${1:-XAUUSD}"
START="${2:-2024-09-01}"
END="${3:-2026-09-01}"
TIMEFRAMES="M1,M5,M15,M30,H1,H4,D1"

echo "=== Fetching $SYMBOL data: $START to $END ==="
echo "Timeframes: $TIMEFRAMES"

python -m are.mt5_export \
    --symbol "$SYMBOL" \
    --timeframes "$TIMEFRAMES" \
    --start "$START" \
    --end "$END"

echo ""
echo "=== Done. Files in data/market_data/ ==="
ls -lh data/market_data/${SYMBOL}_*.parquet 2>/dev/null || echo "No files found"
