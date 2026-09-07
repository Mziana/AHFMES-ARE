# -*- coding: utf-8 -*-
"""Regression test P2-14: batas model portofolio terdeklarasi eksplisit.

Kontrak: kedua engine backtest wajib menandai metrics dgn
portfolio_model='return_compounding' dan
portfolio_model_limits='no_lot_no_margin_no_leverage' — mencegah PnL dolar
backtest dibaca sebagai proyeksi PnL akun (lot/margin/leverage tidak
dimodelkan; sizing nyata hidup di jalur eksekusi).
"""
import math

import polars as pl
import pytest

from are.backtest import IsolatedBacktestEngine
from are.backtest_enhanced import EnhancedBacktestEngine


def _synthetic(n=300):
    ts = [1700000000 + i * 3600 for i in range(n)]
    prices = [2000.0 + 30 * math.sin(i * 0.05) for i in range(n)]
    return pl.DataFrame({
        'timestamp': ts, 'price': prices,
        'open': prices, 'high': prices, 'low': prices, 'close': prices,
        'volume': [1.0] * n,
    })


def _logic(d):
    return d.with_columns(pl.col('price').pct_change(10).alias('_m')).with_columns(
        pl.when(pl.col('_m') > 0.004).then(1.0)
        .when(pl.col('_m') < -0.004).then(-1.0).otherwise(0.0).alias('signal')
    ).drop('_m')


def test_isolated_declares_portfolio_limits():
    res = IsolatedBacktestEngine().run_backtest(
        strategy_logic=_logic, historical_data=_synthetic(),
        initial_capital=10000.0, timeframe_seconds=3600.0)
    assert res.metrics['portfolio_model'] == 'return_compounding'
    assert res.metrics['portfolio_model_limits'] == 'no_lot_no_margin_no_leverage'


def test_enhanced_declares_portfolio_limits():
    res = EnhancedBacktestEngine().run_backtest(
        strategy_logic=_logic, historical_data=_synthetic(),
        initial_capital=10000.0, timeframe_seconds=3600.0)
    assert res.metrics['portfolio_model'] == 'return_compounding'
    assert res.metrics['portfolio_model_limits'] == 'no_lot_no_margin_no_leverage'
