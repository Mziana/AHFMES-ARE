"""
P0 regression tests (audit 2026-09-04):

P0-3 — StatisticsStage harus bisa run tanpa NameError (`import time` hilang).
P0-1 — HoldoutEvaluationEngine WAJIB benar-benar mengevaluasi strategi DENGAN
       selected_params (injeksi `_param_<name>`, identik dengan WFO), dan
       resolve_holdout_selected_params TIDAK boleh mengembalikan parameter rekaan
       bila WFO tidak menghasilkan fold winner.
"""
from types import SimpleNamespace

import polars as pl
import pytest

from are.research.holdout import (
    HoldoutEvaluationEngine,
    resolve_holdout_selected_params,
)
from are.research.stages.gate import GateStage
from are.research.stages.statistics import StatisticsStage
from are.research.types import RunStage


# ── P0-3 ─────────────────────────────────────────────────────────────────────

def test_statistics_stage_runs_without_nameerror():
    """Regression: statistics.py memakai time.time() tanpa `import time`
    -> NameError. Setelah fix, stub run minimal harus selesai PASSED."""
    run = SimpleNamespace(
        oos_result={},
        wfo_result={},
        statistics_result=None,
        mc_simulations=100,
        initial_capital=10000.0,
    )
    result = StatisticsStage().run(run)
    assert result.status == RunStage.PASSED
    assert run.statistics_result is not None
    # Path tanpa returns -> metrics nol, bukan exception
    assert run.statistics_result["total_trades"] == 0
    assert "win_rate" in run.statistics_result


# ── P0-1: helper resolusi parameter ─────────────────────────────────────────

def test_resolve_params_from_last_fold_winner():
    wfo = {
        "folds": [
            {"fold_id": 0, "winner_params": {"lookback": 10}},
            {"fold_id": 1, "winner_params": {"lookback": 40}},
        ]
    }
    out = resolve_holdout_selected_params(wfo, has_params=True)
    assert out == {"lookback": 40}  # winner fold TERAKHIR


def test_resolve_params_no_fabrication_when_no_winner():
    # Parameter dideklarasikan tapi WFO kosong / tidak ada folds -> None (INVALID),
    # BUKAN {'lookback': 20} rekaan.
    assert resolve_holdout_selected_params(None, has_params=True) is None
    assert resolve_holdout_selected_params({}, has_params=True) is None
    assert resolve_holdout_selected_params({"folds": []}, has_params=True) is None
    assert resolve_holdout_selected_params(
        {"folds": [{"fold_id": 0, "winner_params": None}]}, has_params=True
    ) is None


def test_resolve_params_parameter_free_strategy_ok():
    # Strategi tanpa parameter: empty dict sah (bukan None).
    assert resolve_holdout_selected_params(None, has_params=False) == {}
    assert resolve_holdout_selected_params({"folds": []}, has_params=False) == {}
    assert resolve_holdout_selected_params(
        {"folds": [{"fold_id": 0, "winner_params": None}]}, has_params=False
    ) == {}


# ── P0-1: injeksi parameter ke strategi saat evaluasi holdout ───────────────

def _synthetic_uptrend_df(n=400):
    """Data sintetis uptrend lemah + noise deterministik (bukan synthetic engine)."""
    import random
    rng = random.Random(7)
    t0 = 1_700_000_000
    p = 100.0
    ts, px = [], []
    for i in range(n):
        ts.append(t0 + i * 60)
        p *= 1.0 + 0.0006 + rng.uniform(-0.0012, 0.0012)
        px.append(p)
    return pl.DataFrame({"timestamp": ts, "price": px})


def _dir_strategy(df: pl.DataFrame) -> pl.DataFrame:
    """Strategi yang MEMBUTUHKAN parameter `dir`:
    tanpanya langsung AssertionError -> membuktikan parameter disuntikkan."""
    if "_param_dir" not in df.columns:
        raise AssertionError("strategi dipanggil TANPA _param_dir — parameter tidak disuntikkan")
    val = float(df["_param_dir"][0])
    return df.with_columns(pl.Series("signal", [val] * df.height))


def test_holdout_injects_selected_params_into_strategy():
    df = _synthetic_uptrend_df()
    seen_cols = {}

    def spy_strategy(d: pl.DataFrame) -> pl.DataFrame:
        seen_cols["cols"] = list(d.columns)
        return _dir_strategy(d)

    ev = HoldoutEvaluationEngine.evaluate(
        strategy_logic=spy_strategy,
        holdout_df=df,
        selected_params={"dir": 1},
        initial_capital=100000.0,
    )
    # Parameter benar-benar diterima strategi sebagai kolom _param_dir
    assert "_param_dir" in seen_cols["cols"]
    # Terbawa ke evidence (bukan sekadar metadata: dipakai di hash/provenance)
    assert dict(ev.selected_params) == {"dir": 1}


def test_selected_params_change_holdout_evaluation_result():
    df = _synthetic_uptrend_df()

    ev_buy = HoldoutEvaluationEngine.evaluate(
        strategy_logic=_dir_strategy, holdout_df=df,
        selected_params={"dir": 1}, initial_capital=100000.0,
    )
    ev_sell = HoldoutEvaluationEngine.evaluate(
        strategy_logic=_dir_strategy, holdout_df=df,
        selected_params={"dir": -1}, initial_capital=100000.0,
    )
    # Parameter mengubah evaluasi secara NYATA: arah berlawanan -> hasil berlawanan
    assert ev_buy.total_return > 0, f"dir=+1 pada uptrend harus profit, dapat {ev_buy.total_return}"
    assert ev_sell.total_return < 0, f"dir=-1 pada uptrend harus rugi, dapat {ev_sell.total_return}"
    assert dict(ev_buy.selected_params) == {"dir": 1}
    assert dict(ev_sell.selected_params) == {"dir": -1}


def test_holdout_no_params_strategy_runs_without_fabricated_columns():
    """Strategi tanpa parameter: selected_params={} -> TIDAK boleh ada kolom rekaan
    (_param_lookback) yang disuntikkan diam-diam."""
    df = _synthetic_uptrend_df()

    def no_param_strategy(d: pl.DataFrame) -> pl.DataFrame:
        for c in d.columns:
            if c.startswith("_param_"):
                raise AssertionError(f"kolom rekaan disuntikkan: {c}")
        return d.with_columns(pl.Series("signal", [1.0] * d.height))

    ev = HoldoutEvaluationEngine.evaluate(
        strategy_logic=no_param_strategy, holdout_df=df,
        selected_params={}, initial_capital=100000.0,
    )
    assert ev.total_return > 0


# ── P0-1: gate menolak holdout yang dilewati (INVALID, bukan PASS/FAIL) ──────

def test_gate_invalid_when_holdout_skipped_for_missing_wfo_winner():
    """Ketika orchestrator menandai holdout_invalid_reason (WFO tanpa winner),
    Final Gate harus INVALID — jangan pernah PASS/BORDERLINE dengan evidence palsu."""
    run = SimpleNamespace(
        oos_result={"pooled_sharpe": 0.3, "pooled_return": 0.01, "pooled_max_dd": 0.1},
        statistics_result={
            "n_obs": 100, "effective_trial_count": 5, "wfe": 0.2,
            "dsr_p_value": 0.001, "mc_ruin_probability": 0.02,
            "total_trades": 50, "win_rate": 55.0, "profit_factor": 1.3,
        },
        crisis_result={}, stability_result={}, baseline_result={},
        holdout_evaluated=False, holdout_evidence=None,
        holdout_invalid_reason="HOLDOUT_INVALID: WFO tidak menghasilkan fold winner",
        final_gate=None,
    )
    res = GateStage().run(run, config=None)
    assert res.data["decision"] == "INVALID"
    assert res.data["reason"].startswith("HOLDOUT_INVALID")
    assert res.status == RunStage.FAILED
