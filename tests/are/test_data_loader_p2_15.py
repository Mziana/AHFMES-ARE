# -*- coding: utf-8 -*-
"""Regression test P2-15: data_loader — UTC parsing + pemilihan file by coverage.

Akar bug: (1) filter tanggal memakai time.mktime (waktu LOKAL) — hasil load
berbeda antar mesin/zona waktu; (2) file dipilih leksikografis "terbaru"
(suffix nama file), bukan berdasarkan cakupan rentang yang diminta — dua file
dengan rentang berbeda bisa membuat backtest senyap memakai data salah.
"""
import time

import polars as pl
import pytest

import are.data_loader as dl


def _mk_parquet(tmp_path, name, start_ts, end_ts, bars=10):
    ts = [start_ts + (end_ts - start_ts) * i / max(bars - 1, 1) for i in range(bars)]
    df = pl.DataFrame({
        'timestamp': ts,
        'open': [1.0] * bars, 'high': [1.1] * bars, 'low': [0.9] * bars,
        'close': [1.05] * bars, 'volume': [1.0] * bars,
        'price': [1.05] * bars,
    })
    df.write_parquet(tmp_path / name)


def _utc(y, m, d):
    return time.mktime((y, m, d, 0, 0, 0, 0, 0, -1)) - time.timezone if False else (
        __import__('calendar').timegm((y, m, d, 0, 0, 0)))


def test_utc_parsing_not_local(tmp_path, monkeypatch):
    """Filter tanggal harus UTC: jumlah bar yang terpilih identik di zona
    waktu mana pun (dihitung dari calendar.timegm, bukan mktime)."""
    # rentang file: 2025-01-10 .. 2025-03-01 UTC
    lo, hi = _utc(2025, 1, 10), _utc(2025, 3, 1)
    _mk_parquet(tmp_path, 'XAUUSD_H1_x.parquet', lo, hi, bars=2000)
    monkeypatch.setattr(dl, 'DATA_DIR', str(tmp_path))

    df = dl.load_ohlc_data('XAUUSD', 'H1', '2025-01-15', '2025-02-15')
    req_lo, req_hi = _utc(2025, 1, 15), _utc(2025, 2, 15) + 86399
    assert df['timestamp'].min() >= req_lo
    assert df['timestamp'].max() <= req_hi


def test_picks_file_with_best_coverage(tmp_path, monkeypatch):
    """Dua file: yang lama (nama lebih kecil) mencakup rentang diminta, yang
    'terbaru' (nama lebih besar) tidak — loader harus memilih yang mencakup."""
    _mk_parquet(tmp_path, 'XAUUSD_H1_2025-01-01_2025-06-01.parquet',
                _utc(2025, 1, 1), _utc(2025, 6, 1), bars=3000)
    _mk_parquet(tmp_path, 'XAUUSD_H1_2025-07-01_2025-12-31.parquet',
                _utc(2025, 7, 1), _utc(2025, 12, 31), bars=3000)
    monkeypatch.setattr(dl, 'DATA_DIR', str(tmp_path))

    df = dl.load_ohlc_data('XAUUSD', 'H1', '2025-02-01', '2025-04-01')
    assert df['timestamp'].min() >= _utc(2025, 2, 1)


def test_out_of_range_request_fails_honest(tmp_path, monkeypatch):
    """Rentang yang tidak dicakup file mana pun harus GAGAL, bukan senyap
    mengembalikan file salah."""
    _mk_parquet(tmp_path, 'XAUUSD_H1_a.parquet', _utc(2025, 1, 1), _utc(2025, 3, 1), 500)
    monkeypatch.setattr(dl, 'DATA_DIR', str(tmp_path))
    with pytest.raises(ValueError, match='mencakup rentang'):
        dl.load_ohlc_data('XAUUSD', 'H1', '2025-10-01', '2025-11-01')


def test_partial_coverage_warns(tmp_path, monkeypatch, capsys):
    _mk_parquet(tmp_path, 'XAUUSD_H1_b.parquet', _utc(2025, 1, 1), _utc(2025, 2, 1), 800)
    monkeypatch.setattr(dl, 'DATA_DIR', str(tmp_path))
    df = dl.load_ohlc_data('XAUUSD', 'H1', '2025-01-01', '2025-06-01')
    out = capsys.readouterr().out
    assert 'WARN' in out and '%' in out
