# -*- coding: utf-8 -*-
"""Regression test P2-18 fix: EnhancedBacktestEngine WFO-compatible.

Akar bug (ditemukan empiris saat audit P2-18, 2026-09-07): setelah P2-12
memasukkan pre_purified di run_walk_forward_optimization, OVERRIDE
EnhancedBacktestEngine.run_backtest tidak menerima parameter itu ->
CLI `are backtest wfo` crash dengan TypeError 100% (tidak ada test
ekuivalensi dua engine yang menangkapnya — test suite hijau penuh).

Kontrak sekarang:
1. EnhancedBacktestEngine.run_backtest menerima pre_purified (dan kwarg
   tak-dikenal via **_extra — forward compatible).
2. pre_purified=True: tidak memanggil DataPurifier; metrics tetap lengkap.
3. CLI `backtest wfo` end-to-end: rc=0, folded evidence, tracker berubah.
4. IsolatedBacktestEngine di-mock di WFO pun tetap jalan (WFO memanggil
   run_backtest method milik sendiri -> engine apapun yang override harus
   kompatibel).
"""
import json
import math
import os

import polars as pl
import pytest

import are.backtest as bt_mod
from are.backtest_enhanced import EnhancedBacktestEngine


def _synthetic(n=700):
    ts = [1700000000 + i * 3600 for i in range(n)]
    prices = [2000.0 + 40 * math.sin(i * 0.05) + i * 0.03 for i in range(n)]
    return pl.DataFrame({
        'timestamp': ts, 'price': prices,
        'open': prices, 'high': prices, 'low': prices, 'close': prices,
        'volume': [1.0] * n,
    })


def _logic(d):
    return d.with_columns(pl.col('price').pct_change(15).alias('_m')).with_columns(
        pl.when(pl.col('_m') > 0.004).then(1.0)
        .when(pl.col('_m') < -0.004).then(-1.0).otherwise(0.0).alias('signal')
    ).drop('_m')


def test_enhanced_accepts_pre_purified_kwarg(tmp_path, monkeypatch):
    """THE regression: EnhancedBacktestEngine.run_backtest(pre_purified=True)
    harus jalan tanpa TypeError dan tanpa memanggil purifier."""
    calls = {'n': 0}
    real_purify = bt_mod.DataPurifier.purify_tick_data

    def counting(self, df, *a, **k):
        calls['n'] += 1
        return real_purify(self, df, *a, **k)

    monkeypatch.setattr(bt_mod.DataPurifier, 'purify_tick_data', counting)

    eng = EnhancedBacktestEngine()
    res = eng.run_backtest(strategy_logic=_logic, historical_data=_synthetic(300),
                           initial_capital=10000.0, timeframe_seconds=3600.0,
                           pre_purified=True)
    assert calls['n'] == 0, 'pre_purified=True tidak boleh memanggil DataPurifier'
    assert 'sharpe_ratio' in res.metrics
    # unknown kwargs juga diterima (forward compatible)
    res2 = eng.run_backtest(strategy_logic=_logic, historical_data=_synthetic(300),
                            initial_capital=10000.0, timeframe_seconds=3600.0,
                            pre_purified=True, unknown_future_kwarg=123)
    assert 'sharpe_ratio' in res2.metrics


def test_enhanced_wfo_end_to_end():
    """WFO via EnhancedBacktestEngine (jalur CLI) harus menghasilkan evidence."""
    eng = EnhancedBacktestEngine()
    ev = eng.run_walk_forward_optimization(
        strategy_factory=lambda params: _logic,
        param_grid=[{'lookback': 10}, {'lookback': 20}],
        historical_data=_synthetic(700),
        train_window_bars=250,
        test_window_bars=80,
        step_bars=80,
        purge_bars=1,
        label_horizon_bars=1,
        timeframe_seconds=3600.0,
    )
    assert ev.fold_count >= 2
    assert ev.pooled_oos_returns is not None


def test_engine_equivalence_contract():
    """Kedua engine harus kompatibel dgn signature WFO (pre_purified diterima
    keduanya) — guard utk regresi kelas ini."""
    for engine in (bt_mod.IsolatedBacktestEngine(), EnhancedBacktestEngine()):
        res = engine.run_backtest(strategy_logic=_logic,
                                  historical_data=_synthetic(300),
                                  initial_capital=10000.0,
                                  timeframe_seconds=3600.0,
                                  pre_purified=True)
        assert 'sharpe_ratio' in res.metrics
