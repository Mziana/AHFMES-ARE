# -*- coding: utf-8 -*-
"""Regression test P1-09: skema artifact bkt-* terpadu (are/artifacts.py).

Akar bug: tiga penulis (cli.py, web_ui.py, UI backtest route) memakai tiga
skema berbeda -> `are backtest list` menampilkan `? 0 bars` utk artifact UI,
dan endpoint equity-curve web_ui gagal utk artifact CLI.

Kontrak skema union yang diuji: artifact yang dihasilkan helper memuaskan
SEMUA pembaca yang ada.
"""
import json
import os

import polars as pl
import pytest

from are.artifacts import build_backtest_artifact, save_backtest_artifact


def _fake_metrics():
    return {
        'initial_capital': 100000.0,
        'final_equity': 102281.27,
        'total_return_pct': 2.28,
        'total_trades': 12,
        'win_rate': 50.0,
        'sharpe_ratio': 0.1755,
        'sortino_ratio': 0.2,
        'calmar_ratio': 0.21,
        'cvar_5pct': -0.004,
        'profit_factor': 1.05,
        'max_drawdown_pct': 10.87,
        'avg_win': 0.01,
        'avg_loss': 0.008,
        'max_consecutive_losses': 3,
        'exposure_pct': 42.0,
        'total_bars': 9345,
        'raw_dataset_hash': 'a' * 64,
        'purified_dataset_hash': 'b' * 64,
        'signal_timing': 'same_bar_close (close-to-close legacy)',
        'execution_model_id': 'legacy_close_to_close',
    }


def _fake_equity_curve(n=500):
    ts = [1700000000 + i * 3600 for i in range(n)]
    eq = [100000.0 + i * 4.5 for i in range(n)]
    return pl.DataFrame({'timestamp': ts, 'equity': eq})


def test_artifact_satisfies_cli_list_reader(tmp_path):
    """CLI list membaca: id, strategy_id, metrics.total_trades/win_rate/sharpe."""
    art = build_backtest_artifact(
        metrics=_fake_metrics(), equity_curve=_fake_equity_curve(),
        symbol='XAUUSD', timeframe='H1', start='2025-01-01', end='2026-08-01',
        initial_capital=100000.0, strategy_id='dsr-momentum-breakout')
    path = save_backtest_artifact(art, bt_dir=str(tmp_path))
    disk = json.load(open(path, encoding='utf-8'))
    m = disk.get('metrics', {})
    assert disk.get('id') == art['id']
    assert disk.get('strategy_id') == 'dsr-momentum-breakout'
    assert m.get('total_trades') == 12
    assert m.get('win_rate') == 50.0
    assert m.get('sharpe_ratio') == 0.1755


def test_artifact_satisfies_webui_and_page_readers(tmp_path):
    """web_ui + UI page membaca: strategyName, config{...}, results{camelCase},
    equityCurve[]."""
    art = build_backtest_artifact(
        metrics=_fake_metrics(), equity_curve=_fake_equity_curve(),
        symbol='XAUUSD', timeframe='H1', start='2025-01-01', end='2026-08-01',
        initial_capital=100000.0, strategy_id='s1', strategy_name='DSR Momentum Breakout')
    path = save_backtest_artifact(art, bt_dir=str(tmp_path))
    disk = json.load(open(path, encoding='utf-8'))
    assert disk['strategyName'] == 'DSR Momentum Breakout'
    assert disk['config']['symbol'] == 'XAUUSD'
    assert disk['config']['initialBalance'] == 100000.0
    r = disk['results']
    assert r['totalTrades'] == 12 and r['winRate'] == 50.0 and r['sharpe'] == 0.1755
    assert r['netPnl'] == 2281.27
    ec = disk['equityCurve']
    assert 0 < len(ec) <= 260  # sampling range(0,n,step) utk n=500, step=2 -> 250
    assert set(ec[0]) == {'timestamp', 'equity'}
    # equity-curve endpoint shape (id + equity_curve list)
    assert disk['id'] == art['id']


def test_artifact_has_provenance():
    art = build_backtest_artifact(metrics=_fake_metrics(), equity_curve=None,
                                  strategy_id='s1')
    r = art['results']
    assert r['rawDatasetHash'] == 'a' * 64
    assert art['schema_version'] == 2
    assert art['strategyId'] == 's1'  # UI page key


def test_atomic_write_no_tmp_left(tmp_path):
    art = build_backtest_artifact(metrics=_fake_metrics(), strategy_id='s1')
    path = save_backtest_artifact(art, bt_dir=str(tmp_path))
    assert os.path.exists(path)
    assert not os.path.exists(path + '.tmp')
