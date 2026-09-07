# -*- coding: utf-8 -*-
"""Regression test D1 (P1-05): konsistensi EnhancedBacktestEngine vs parent.

Akar bug (audit 2026-09-07, artifact bkt-1788783495102.json):
1. EnhancedBacktestEngine menghitung dataset hash format V1 (timestamp/price/
   volume saja) sementara IsolatedBacktestEngine memakai V2 (semua kolom
   market + rows/cols) -> identitas dataset tak bisa dibandingkan lintas jalur.
2. win_rate = % BAR dengan return positif (12 trade -> "Win Rate 0.9%") —
   seharusnya % trade menang dari PnL segmen.
3. slippage_pct/commission_pct diabaikan diam-diam padahal ada di signature.

Test ini mengeksekusi kedua engine pada data sintetis yang SAMA dan
membandingkan kontrak keluarannya.
"""
import math

import polars as pl
import pytest

from are.backtest import IsolatedBacktestEngine
from are.backtest_enhanced import EnhancedBacktestEngine


def _synthetic_ohlc(n=400):
    ts = [1700000000 + i * 3600 for i in range(n)]
    out = {"timestamp": ts}
    prices = []
    for i in range(n):
        prices.append(2000.0 + 50 * math.sin(i * 0.05) + i * 0.05)
    out["price"] = prices
    out["open"] = [p - 0.5 for p in prices]
    out["high"] = [p + 1.0 for p in prices]
    out["low"] = [p - 1.0 for p in prices]
    out["close"] = prices
    out["volume"] = [10.0] * n
    return pl.DataFrame(out)


def _momentum(d):
    return d.with_columns(pl.col("price").pct_change(20).alias("_m")).with_columns(
        pl.when(pl.col("_m") > 0.005).then(1.0)
        .when(pl.col("_m") < -0.005).then(-1.0).otherwise(0.0).alias("signal")
    ).drop("_m")


@pytest.fixture(scope="module")
def df():
    return _synthetic_ohlc()


def test_hash_format_consistent_between_engines(df):
    """Kedua engine harus menghasilkan raw_dataset_hash YANG SAMA untuk data
    yang sama (kontrak format V2)."""
    iso = IsolatedBacktestEngine().run_backtest(
        strategy_logic=_momentum, historical_data=df, initial_capital=100000.0,
        timeframe_seconds=3600.0)
    enh = EnhancedBacktestEngine().run_backtest(
        strategy_logic=_momentum, historical_data=df, initial_capital=100000.0,
        timeframe_seconds=3600.0)
    assert iso.metrics["raw_dataset_hash"] == enh.metrics["raw_dataset_hash"], \
        "raw hash harus identik lintas engine (V2)"
    assert iso.metrics["purified_dataset_hash"] == enh.metrics["purified_dataset_hash"], \
        "purified hash harus identik lintas engine (V2)"
    # dan hash purified != raw saat purifier menambah kolom sintetis
    assert enh.metrics["raw_dataset_hash"] != enh.metrics["purified_dataset_hash"]


def test_win_rate_is_per_trade(df):
    """win_rate = % trade menang (0-100), bukan % bar positif. Dengan sedikit
    trade pada 400 bar, % bar vs % trade berbeda jauh — kontrak: win_rate
    konsisten dengan total_trades & avg_win/avg_loss yang dihitung per-trade."""
    res = EnhancedBacktestEngine().run_backtest(
        strategy_logic=_momentum, historical_data=df, initial_capital=100000.0,
        timeframe_seconds=3600.0)
    m = res.metrics
    n_trades = m["total_trades"]
    if n_trades == 0:
        pytest.skip("no trades on synthetic data")
    assert 0.0 <= m["win_rate"] <= 100.0
    # jika semua pnl trade positif -> win_rate 100; kalau ada yang negatif -> <100
    pnls = [float(x) for x in res.trade_log["pnl"].to_list()]
    wins = sum(1 for p in pnls if p > 0)
    assert m["win_rate"] == pytest.approx(wins / len(pnls) * 100, abs=0.01)


def test_slippage_and_commission_applied(df):
    """Friction kini mencakup slippage+commission (tidak diabaikan)."""
    base = EnhancedBacktestEngine().run_backtest(
        strategy_logic=_momentum, historical_data=df, initial_capital=100000.0,
        timeframe_seconds=3600.0)
    heavy = EnhancedBacktestEngine().run_backtest(
        strategy_logic=_momentum, historical_data=df, initial_capital=100000.0,
        timeframe_seconds=3600.0, slippage_pct=0.001, commission_pct=0.001)
    assert heavy.metrics["final_equity"] <= base.metrics["final_equity"], \
        "friction lebih besar tidak boleh menghasilkan equity lebih tinggi"
    assert heavy.metrics["slippage_pct"] == 0.001
    assert heavy.metrics["commission_pct"] == 0.001
