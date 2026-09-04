"""
P0-2 regression tests: execution model WAJIB menentukan economics backtest.

Sebelum fix: run_backtest menghitung return close-to-close (prev_signal x pct_change)
dan friction konstanta, sementara ExecutionModel mendeklarasikan signal_timing=
'next_bar_open' (kontradiksi entry_price_type='close' -> hasil bisa terlihat bagus
padahal semantik eksekusi berbeda).

Setelah fix:
  (a) execution_model.signal_timing='next_bar_open' -> order di-fill di OPEN(t+1):
      bar entry r = (close/open - 1); bar lanjutan close-to-close.
  (b) spread/slippage/commission diambil DARI execution model.
  (c) execution_model=None -> jalur legacy close-to-close (label jujur), kompatibel.
  (d) data tanpa kolom open + model next_bar_open -> fail-closed ValueError.
"""
import math
from types import SimpleNamespace

import polars as pl
import pytest

from are.backtest import IsolatedBacktestEngine
from are.data_pipeline import DataPurifier


def _em(**over):
    base = dict(
        signal_timing="next_bar_open", entry_price_type="mid", exit_price_type="mid",
        position_model="continuous", order_type="market", fill_guarantee="guaranteed",
        spread_model="synthetic_fixed", slippage_model="fixed_pct", commission_model="fixed_pct",
        spread_pct=0.0, slippage_pct=0.0, commission_pct=0.0, initial_capital=1000.0,
        model_id="TEST-EM",
    )
    base.update(over)
    return SimpleNamespace(**base)


def _ohlc_df(opens, closes):
    n = len(opens)
    return pl.DataFrame({
        "timestamp": [1700000000 + i * 60 for i in range(n)],
        "open": opens, "high": [max(o, c) for o, c in zip(opens, closes)],
        "low": [min(o, c) for o, c in zip(opens, closes)],
        "close": closes, "price": closes, "volume": [1.0] * n,
    })


# ── (a) fill di open(t+1), bukan close(t) ────────────────────────────────────

def test_model_fills_at_open_next_bar_not_close():
    """Gap close(0)=100 -> open(1)=90. Sinyal BUY di close(0):
    model harus entri di 90 (r=110/90-1=+22.22%),
    legacy close-to-close entri di 100 (r=+10%)."""
    df = _ohlc_df([100.0, 90.0, 110.0, 110.0, 110.0],
                  [100.0, 110.0, 110.0, 110.0, 110.0])

    def strat(d):
        sig = [0.0, 0.0, 0.0, 0.0, 0.0]
        sig[0] = 1.0
        return d.with_columns(pl.Series("signal", sig))

    engine = IsolatedBacktestEngine()
    legacy = engine.run_backtest(strategy_logic=strat, historical_data=df, initial_capital=1000.0,
                                 spread_pct=0.0, slippage_pct=0.0, commission_pct=0.0)
    model = engine.run_backtest(strategy_logic=strat, historical_data=df, initial_capital=1000.0,
                                execution_model=_em())

    # Legacy: return close0->close1 = +10%
    assert abs(legacy.metrics["total_return"] - 0.10) < 5e-4
    # Model: fill di open(1)=90 -> 110/90-1 = +22.22%
    assert abs(model.metrics["total_return"] - (110.0 / 90.0 - 1.0)) < 5e-4
    assert model.metrics["total_return"] > legacy.metrics["total_return"] + 0.10
    # Trade log mencatat harga entri OPEN bar berikutnya (90), bukan close bar sinyal (100)
    assert float(model.trade_log["price"][0]) == 90.0
    assert model.metrics["filled_at_open_next_bar"] is True


# ── (b) P&L konsisten dgn model: replikasi manual ────────────────────────────

def test_model_pnl_matches_manual_next_bar_open_replication():
    opens = [100.0, 101.0, 102.0, 101.0, 103.0]
    closes = [100.0, 102.0, 101.0, 103.0, 105.0]
    df = _ohlc_df(opens, closes)
    n = len(closes)

    def long_strat(d):
        return d.with_columns(pl.Series("signal", [1.0] * n))

    engine = IsolatedBacktestEngine()
    model = engine.run_backtest(strategy_logic=long_strat, historical_data=df,
                                initial_capital=1000.0, execution_model=_em())

    # Replikasi manual kontrak: sinyal konstan long mulai close(0).
    # r_bar1 = close1/open1 - 1 (entry), r_bar_j = close_j/close_{j-1} - 1 (lanjutan)
    exp_equity = 1000.0
    for j in range(1, n):
        base = opens[j] if j == 1 else closes[j - 1]
        exp_equity *= (closes[j] / base)
    exp_return = exp_equity / 1000.0 - 1.0
    assert abs(model.metrics["total_return"] - exp_return) < 5e-4
    final = float(model.equity_curve["equity"][-1])
    assert abs(final - exp_equity) < 1.0


# ── (b2) friction & label dari model, bukan konstanta argumen ────────────────

def test_friction_taken_from_execution_model():
    df = _ohlc_df([100.0] * 4, [100.0, 101.0, 102.0, 103.0])

    def strat(d):
        return d.with_columns(pl.Series("signal", [1.0] * 4))

    engine = IsolatedBacktestEngine()
    model = engine.run_backtest(
        strategy_logic=strat, historical_data=df, initial_capital=1000.0,
        spread_pct=0.0001,  # argumen dgn nilai beda; model harus MENANG
        execution_model=_em(spread_pct=0.02, slippage_pct=0.001, commission_pct=0.001),
    )
    assert model.metrics["spread_pct"] == 0.02
    assert model.metrics["slippage_pct"] == 0.001
    assert model.metrics["commission_pct"] == 0.001
    # friction dari model (0.5*0.02+0.001+0.001 = 0.012 per turnover)
    # lebih kecil return daripada friction argumen 0.0001 -> pastikan efeknya tampak
    assert model.metrics["execution_model_id"] == "TEST-EM"


# ── (c) legacy default: perilaku close-to-close dipertahankan ────────────────

def test_legacy_default_close_to_close_unchanged_and_labeled():
    df = _ohlc_df([100.0] * 5, [100.0, 101.0, 100.5, 102.0, 101.0])

    def strat(d):
        return d.with_columns(pl.Series("signal", [1.0] * 5))

    engine = IsolatedBacktestEngine()
    r = engine.run_backtest(strategy_logic=strat, historical_data=df, initial_capital=1000.0,
                            spread_pct=0.0, slippage_pct=0.0, commission_pct=0.0)
    # total_return = product(close_j/close_{j-1}) - 1 (close-to-close penuh)
    exp = (101.0 / 100.0) * (100.5 / 101.0) * (102.0 / 100.5) * (101.0 / 102.0) - 1.0
    assert abs(r.metrics["total_return"] - exp) < 5e-4
    # label jujur utk jalur legacy
    assert r.metrics["signal_timing"] == "same_bar_close (close-to-close legacy)"
    assert r.metrics["filled_at_open_next_bar"] is False


# ── (d) fail-closed: next_bar_open tanpa kolom open ──────────────────────────

def test_next_bar_open_without_open_column_fails_closed():
    df = pl.DataFrame({
        "timestamp": [1700000000 + i * 60 for i in range(5)],
        "price": [100.0 + i for i in range(5)],
    })

    def strat(d):
        return d.with_columns(pl.Series("signal", [0.0, 1.0, 1.0, 1.0, 0.0]))

    engine = IsolatedBacktestEngine()
    with pytest.raises(ValueError, match="EXECUTION_CONTRACT_VIOLATION"):
        engine.run_backtest(strategy_logic=strat, historical_data=df,
                            execution_model=_em())


# ── purifier: OHLC dipertahankan (prasyarat next_bar_open) ──────────────────

def test_purifier_keeps_ohlc_columns():
    df = _ohlc_df([100.0, 101.0], [101.0, 102.0])
    out = DataPurifier().purify_tick_data(df)
    assert "open" in out.columns
    assert "close" in out.columns
    assert "high" in out.columns
    assert "low" in out.columns
    assert out["open"].to_list() == [100.0, 101.0]
