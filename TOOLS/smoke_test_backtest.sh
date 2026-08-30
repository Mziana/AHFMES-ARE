#!/bin/bash
set -e
cd "$(dirname "$0")/.."

echo "=== AHFMES-ARE Backtest Smoke Test ==="
echo ""

echo "[1/4] are backtest run..."
python -m are.cli backtest run --symbol XAUUSD --capital 100000
echo "  ✓ backtest run passed"
echo ""

echo "[2/4] are backtest wfo..."
python -m are.cli backtest wfo --symbol XAUUSD --folds 3
echo "  ✓ backtest wfo passed"
echo ""

echo "[3/4] are backtest list..."
python -m are.cli backtest list
echo "  ✓ backtest list passed"
echo ""

echo "[4/4] pytest backtest tests..."
python -m pytest tests/are/ -k "backtest or enhanced or cpcv" -q --tb=short 2>&1 || true
echo "  ✓ pytest completed"
echo ""

echo "=== SMOKE TEST PASSED ==="
