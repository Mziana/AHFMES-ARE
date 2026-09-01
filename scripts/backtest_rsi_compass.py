#!/usr/bin/env python3
"""Run RSI Compass Strategy Backtest on XAUUSD M5 data."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import polars as pl
from are.backtest import IsolatedBacktestEngine, baseline_buy_and_hold
from are.strategies.rsi_compass import rsi_compass_strategy

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "market_data")
m5_file = os.path.join(DATA_DIR, "XAUUSD_M5_2024-09-01_2026-09-01.parquet")

print("=== Loading Data ===")
m5_df = pl.read_parquet(m5_file).with_columns(pl.col("close").alias("price"))
print(f"M5 data: {len(m5_df):,} bars")

print("\n=== Running RSI Compass Strategy v2 (M5) ===")
strategy = rsi_compass_strategy(
    rsi_period=14,
    rsi_oversold=30.0,
    rsi_overbought=70.0,
    rsi_compass_level=50.0,
    cooldown_bars=12,
    min_hold_bars=6,
)

engine = IsolatedBacktestEngine()
result = engine.run_backtest(
    strategy_logic=strategy,
    historical_data=m5_df,
    initial_capital=100000.0,
    timeframe_seconds=300.0,
    spread_pct=0.0002,
    slippage_pct=0.0001,
    commission_pct=0.00005,
)

m = result.metrics
print(f"\n=== Results ===")
print(f"Total Trades: {m['total_trades']}")
print(f"Net PnL: ${m['net_pnl']:,.2f}")
print(f"Final Equity: ${m['final_equity']:,.2f}")
print(f"Total Return: {m['total_return_pct']:.2f}%")
print(f"Sharpe Ratio: {m['sharpe_ratio']:.4f}")
print(f"Max Drawdown: {m['max_drawdown_pct']:.2f}%")
print(f"Profit Factor: {m['profit_factor']:.4f}")
print(f"Friction Cost: {m['total_friction_cost_pct']:.2f}%")
print(f"Turnover: {m['total_turnover_count']}")

# Baseline
print("\n=== Baseline: Buy & Hold ===")
bh = engine.run_backtest(
    strategy_logic=baseline_buy_and_hold,
    historical_data=m5_df,
    initial_capital=100000.0,
    timeframe_seconds=300.0,
)
bm = bh.metrics
print(f"Total Return: {bm['total_return_pct']:.2f}%")
print(f"Sharpe: {bm['sharpe_ratio']:.4f}")
print(f"Max DD: {bm['max_drawdown_pct']:.2f}%")

output = {"strategy": "rsi_compass_m5_v2", "results": m, "baseline": bm}
output_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "backtest_runs", "rsi_compass_m5_v2.json")
os.makedirs(os.path.dirname(output_file), exist_ok=True)
with open(output_file, "w") as f:
    json.dump(output, f, indent=2, default=str)
print(f"\nSaved to: {output_file}")
