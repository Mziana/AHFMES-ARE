# -*- coding: utf-8 -*-
"""Regression test P2-12: WFO memurifikasi data SEKALI, bukan per kandidat.

Akar: run_walk_forward_optimization memanggil run_backtest per kandidat per
fold; run_backtest selalu memanggil DataPurifier pada inputnya. Threshold
purifikasi (median-diff utk market-closed, rolling mean utk toxic spread)
dihitung per-slice, jadi flag berbeda antara fold vs dataset penuh — plus
kerja O(folds x params) yang berulang.

Perbaikan: run_backtest menerima pre_purified=True (skip purifier, tetap
fail-closed utk input tanpa price/bid-ask); WFO memurifikasi sekali dan
meneruskannya ke semua jalur IS & OOS.
"""
import math

import polars as pl
import pytest

from are.backtest import IsolatedBacktestEngine


def _synthetic(n=600):
    ts = [1700000000 + i * 3600 for i in range(n)]
    prices = [2000.0 + 40 * math.sin(i * 0.05) + i * 0.02 for i in range(n)]
    return pl.DataFrame({
        'timestamp': ts,
        'price': prices,
        'open': [p - 0.3 for p in prices],
        'high': [p + 0.8 for p in prices],
        'low': [p - 0.8 for p in prices],
        'close': prices,
        'volume': [5.0] * n,
    })


def _logic(d):
    return d.with_columns(pl.col('price').pct_change(15).alias('_m')).with_columns(
        pl.when(pl.col('_m') > 0.004).then(1.0)
        .when(pl.col('_m') < -0.004).then(-1.0).otherwise(0.0).alias('signal')
    ).drop('_m')


def test_wfo_produces_evidence_with_purify_once(monkeypatch):
    """WFO harus memanggil DataPurifier tepat SEKALI (bukan per kandidat x fold),
    dan hasilnya deterministik + lengkap."""
    calls = {'n': 0}
    from are import backtest as bt_mod

    real_purify = bt_mod.DataPurifier.purify_tick_data

    def counting_purify(self, df, *a, **k):
        calls['n'] += 1
        return real_purify(self, df, *a, **k)

    monkeypatch.setattr(bt_mod.DataPurifier, 'purify_tick_data', counting_purify)

    eng = IsolatedBacktestEngine()
    ev = eng.run_walk_forward_optimization(
        strategy_factory=lambda params: _logic,
        param_grid=[{'lookback': 10}, {'lookback': 20}],
        historical_data=_synthetic(600),
        train_window_bars=200,
        test_window_bars=60,
        step_bars=60,
        purge_bars=1,
        label_horizon_bars=1,
        timeframe_seconds=3600.0,
    )
    # 1x di WFO awal + 0x di dalam run_backtest (pre_purified)
    assert calls['n'] == 1, f"purifier harus dipanggil 1x, bukan {calls['n']}x"
    assert ev.fold_count >= 2
    assert ev.pooled_oos_returns is not None


def test_pre_purified_skips_purifier(monkeypatch):
    """pre_purified=True tidak memanggil DataPurifier sama sekali."""
    calls = {'n': 0}
    from are import backtest as bt_mod
    real_purify = bt_mod.DataPurifier.purify_tick_data

    def counting_purify(self, df, *a, **k):
        calls['n'] += 1
        return real_purify(self, df, *a, **k)

    monkeypatch.setattr(bt_mod.DataPurifier, 'purify_tick_data', counting_purify)

    eng = IsolatedBacktestEngine()
    res = eng.run_backtest(strategy_logic=_logic, historical_data=_synthetic(300),
                           initial_capital=10000.0, timeframe_seconds=3600.0,
                           pre_purified=True)
    assert calls['n'] == 0
    assert 'sharpe_ratio' in res.metrics
    # purified hash == raw hash (data sama, tidak dimodifikasi)
    assert res.metrics['raw_dataset_hash'] == res.metrics['purified_dataset_hash']


def test_pre_purified_fails_closed_without_price():
    """Kontrak: input pre-purified tanpa price/bid-ask harus ditolak."""
    eng = IsolatedBacktestEngine()
    bad = pl.DataFrame({'timestamp': [1.0, 2.0, 3.0]})
    with pytest.raises(ValueError, match='PRE_PURIFIED_CONTRACT_VIOLATION'):
        eng.run_backtest(strategy_logic=_logic, historical_data=bad,
                         initial_capital=10000.0, pre_purified=True)


def test_normal_path_still_purifies():
    """Perilaku default tidak berubah: tanpa pre_purified, purifier jalan."""
    from are import backtest as bt_mod
    eng = IsolatedBacktestEngine()
    res = eng.run_backtest(strategy_logic=_logic, historical_data=_synthetic(300),
                           initial_capital=10000.0, timeframe_seconds=3600.0)
    # purification_report terisi dari purifier (synthetic bid/ask rows > 0)
    pr = res.metrics.get('purification_report', {})
    assert pr.get('synthetic_bid_ask_rows', 0) > 0
