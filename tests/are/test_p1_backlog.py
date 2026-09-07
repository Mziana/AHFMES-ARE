"""
P1 backlog — test pembuktian per item (semua sudah terverifikasi di audit):
  P1-4  timeout orchestrator nyata (StageContext + cooperative cancellation di WFO)
  P1-5  synthetic bid/ask/volume -> research qualification INVALID (policy STRICT/BAR_APPROXIMATION)
  P1-6  duplicate timestamp ditolak tegas (purifier REJECT + gate FAIL)
  P1-8  WFO param binding diverifikasi terhadap SELURUH param_grid
  P1-9  trade metrics dari turnover-event log (pooled_trades), bukan bar-return
  P1-14 config_hash mengikat field yang mengubah hasil experiment
"""

import os
import shutil
import tempfile
import threading
import time

import polars as pl
import pytest

from are.backtest import IsolatedBacktestEngine, WFOEvidence
from are.data_pipeline import (
    DataPurifier,
    DataChronologyError,
    DuplicateTimestampError,
)
from are.research.dataset_registry import DataQualityGate
from are.research.experiment_config import (
    ExperimentConfig,
    ParameterGrid,
    StrategyIdentity,
    build_execution_model,
    build_experiment_config,
)
from are.research.orchestrator import StageContext
from are.research.stages.data import DataStage
from are.research.stages.statistics import StatisticsStage
from are.research.stages.wfo import WFOStage, OOSStage
from are.research.types import BacktestRun, RunStage
from are.research.verification import IndependentVerifier


def make_strategy_identity(strategy_id="p1-strat", source_hash="hash_p1") -> StrategyIdentity:
    return StrategyIdentity(
        strategy_id=strategy_id, strategy_name="P1 Strat",
        strategy_version="1.0.0", strategy_family="MOMENTUM",
        source_hash=source_hash, parameter_schema={"lookback": "int"},
        signal_contract="discrete_ternary", lookback_bars=10, warmup_bars=5,
        execution_assumption="next_bar_open",
    )


def make_grid(values=(5.0, 10.0)) -> ParameterGrid:
    return ParameterGrid(
        grid_id="pg1", param_names=("lookback",),
        param_values=(tuple(values),), grid_size=len(values), grid_hash="h1",
        constraints={},
    )


def make_df(n_bars: int = 300, dup: bool = False) -> pl.DataFrame:
    import random
    rng = random.Random(7)
    prices = [100.0]
    for _ in range(n_bars - 1):
        prices.append(prices[-1] * (1 + rng.gauss(0, 0.004)))
    ts = [1700000000 + i * 60 for i in range(n_bars)]
    if dup:
        ts[5] = ts[4]  # duplicate timestamp
    return pl.DataFrame({
        "timestamp": ts,
        "open": prices,
        "high": [p * 1.002 for p in prices],
        "low": [p * 0.998 for p in prices],
        "price": prices,
        "volume": [1000 + i for i in range(n_bars)],
    })


def momentum_strategy(df: pl.DataFrame) -> pl.DataFrame:
    df = df.with_columns(pl.col("price").rolling_mean(5).alias("ma5"))
    return df.with_columns(
        pl.when(pl.col("ma5") > pl.col("price").shift(1)).then(1.0)
        .otherwise(-1.0).alias("signal")
    ).drop("ma5")


def param_strategy(use_param: bool):
    """Strategi yang memakai _param_lookback hanya bila use_param."""
    def logic(df: pl.DataFrame) -> pl.DataFrame:
        if use_param and "_param_lookback" in df.columns:
            w = 3 + int(df["_param_lookback"][0])
        else:
            w = 3
        df = df.with_columns(pl.col("price").rolling_mean(w).alias("ma"))
        return df.with_columns(
            pl.when(pl.col("ma") > pl.col("price").shift(1)).then(1.0)
            .otherwise(-1.0).alias("signal")
        ).drop("ma")
    return logic


def partial_bind_strategy(df: pl.DataFrame) -> pl.DataFrame:
    """Hanya memakai parameter bila <= 5 (grid[0]=5 berefek, grid[1]=10 tidak)."""
    if "_param_lookback" in df.columns and int(df["_param_lookback"][0]) <= 5:
        w = 3 + int(df["_param_lookback"][0])
    else:
        w = 3
    df = df.with_columns(pl.col("price").rolling_mean(w).alias("ma"))
    return df.with_columns(
        pl.when(pl.col("ma") > pl.col("price").shift(1)).then(1.0)
        .otherwise(-1.0).alias("signal")
    ).drop("ma")


def make_config(values=(5.0, 10.0), **kw) -> ExperimentConfig:
    return build_experiment_config(
        strategy=make_strategy_identity(),
        execution_model=build_execution_model(),
        parameter_grid=make_grid(values),
        wfo_train_window_bars=60, wfo_test_window_bars=50,
        wfo_step_bars=50, wfo_purge_bars=5, wfo_warmup_bars=5,
        wfo_n_folds=2, **kw,
    )


def make_run() -> BacktestRun:
    return BacktestRun(run_id="p1-test", experiment_id="p1", created_at=time.time())


# ---------------------------------------------------------------------------
# P1-4: timeout nyata
# ---------------------------------------------------------------------------

class TestP14Timeout:

    def test_stage_context_cancel_event(self):
        ev = threading.Event()
        ctx = StageContext("wfo", time.time() + 1000, ev)
        ev.set()
        with pytest.raises(TimeoutError, match="STAGE_TIMEOUT"):
            ctx.check_cancelled()

    def test_stage_context_deadline_passed(self):
        ctx = StageContext("wfo", time.time() - 1.0, threading.Event())
        with pytest.raises(TimeoutError, match="STAGE_TIMEOUT"):
            ctx.check_cancelled()

    def test_stage_context_ok(self):
        ctx = StageContext("wfo", time.time() + 1000, threading.Event())
        ctx.check_cancelled()  # tidak melempar

    def test_engine_cancel_check_propagates(self):
        engine = IsolatedBacktestEngine()
        df = make_df(200)
        def cancel():
            raise TimeoutError("STAGE_TIMEOUT: test cancel")
        with pytest.raises(TimeoutError, match="STAGE_TIMEOUT"):
            engine.run_walk_forward_optimization(
                strategy_factory=lambda params: momentum_strategy,
                param_grid=[{"lookback": 5.0}],
                historical_data=df,
                train_window_bars=60, test_window_bars=50, step_bars=50,
                purge_bars=5, warmup_bars=5,
                cancel_check=cancel,
            )

    def test_wfo_stage_cooperative_cancellation_fails_fast(self):
        """stage_ctx diteruskan ke engine; event pre-set -> FAILED cepat (bukan post-hoc)."""
        tmp = tempfile.mkdtemp()
        try:
            WFOStage.RUNS_DIR = tmp
            run = make_run()
            df = make_df(300)
            ev = threading.Event()
            ev.set()
            ctx = StageContext("wfo", time.time() + 0.5, ev)
            t0 = time.time()
            res = WFOStage().run(
                run, make_config(), df, momentum_strategy,
                build_execution_model(), stage_ctx=ctx,
            )
            elapsed = time.time() - t0
            assert res.status == RunStage.FAILED
            assert "STAGE_TIMEOUT" in (res.error or "")
            assert elapsed < 5.0, f"cancellation lambat: {elapsed:.2f}s"
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            WFOStage.RUNS_DIR = "data/backtest_runs"


# ---------------------------------------------------------------------------
# P1-5: synthetic microstructure -> INVALID kecuali opt-in eksplisit
# ---------------------------------------------------------------------------

class TestP15Qualification:

    def _df_synthetic(self):
        return make_df(150).drop("open", "high", "low", "volume")

    def _df_real_bidask(self):
        df = make_df(150)
        return df.with_columns([
            (pl.col("price") - 0.0001).alias("bid"),
            (pl.col("price") + 0.0001).alias("ask"),
        ])

    def test_strict_rejects_synthetic(self):
        res = DataStage().run(make_run(), self._df_synthetic(), None, qualification_policy="STRICT")
        assert res.status == RunStage.FAILED
        assert "DATA_QUALIFICATION_INVALID" in (res.error or "")

    def test_bar_approximation_explicit_optin_allowed(self):
        res = DataStage().run(make_run(), self._df_synthetic(), None, qualification_policy="BAR_APPROXIMATION")
        assert res.status == RunStage.PASSED
        assert "BAR_APPROXIMATION" in (res.data or {}).get("qualification_note", "")

    def test_strict_passes_real_bidask(self):
   
        res = DataStage().run(make_run(), self._df_real_bidask(), None, qualification_policy="STRICT")
        assert res.status == RunStage.PASSED

    def test_config_policy_bound_in_hash(self):
        c1 = make_config(qualification_policy="STRICT")
        c2 = make_config(qualification_policy="BAR_APPROXIMATION")
        assert c1.qualification_policy == "STRICT"
        assert c2.qualification_policy == "BAR_APPROXIMATION"
        assert c1.config_hash != c2.config_hash


# ---------------------------------------------------------------------------
# P1-6: duplicate timestamp ditolak tegas
# ---------------------------------------------------------------------------

class TestP16DuplicateTimestamps:

    def test_purifier_rejects_duplicates(self):
        with pytest.raises(DuplicateTimestampError, match="Duplicate timestamps"):
            DataPurifier().purify_tick_data(make_df(150, dup=True))

    def test_quality_gate_fails_on_duplicates(self):
        gate = DataQualityGate.validate(make_df(150, dup=True))
        dup_check = next(c for c in gate["checks"] if c["check"] == "duplicate_timestamps")
        assert dup_check["status"] == "FAIL"
        assert gate["gate"] == "FAIL"

    def test_chronology_still_rejects_reordered(self):
        df = make_df(150)
        ts = df["timestamp"].to_list()
        ts[10], ts[11] = ts[11], ts[10]  # reorder
        df = df.with_columns(pl.Series("timestamp", ts))
        with pytest.raises(DataChronologyError):
            DataPurifier().purify_tick_data(df)


# ---------------------------------------------------------------------------
# P1-8: param binding vs SELURUH grid
# ---------------------------------------------------------------------------

class TestP18ParamBinding:

    def _run_wfo(self, strategy, values=(5.0, 10.0)):
        tmp = tempfile.mkdtemp()
        try:
            WFOStage.RUNS_DIR = tmp
            run = make_run()
            res = WFOStage().run(run, make_config(values), make_df(300), strategy, build_execution_model())
            return res
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            WFOStage.RUNS_DIR = "data/backtest_runs"

    def test_all_grid_combos_bind(self):
        res = self._run_wfo(param_strategy(use_param=True))
        assert res.status == RunStage.PASSED
        assert res.data["param_binding_valid"] is True
        assert "Semua 2 kombinasi" in res.data["param_binding_note"]

    def test_dead_combo_in_grid_detected(self):
        """grid[0] (5) berefek, grid[1] (10) tidak -> check lama (grid[0] saja) lolos,
        check baru vs SELURUH grid harus GAGAL."""
        res = self._run_wfo(partial_bind_strategy)
        assert res.data["param_binding_valid"] is False
        assert "BINDING GAGAL" in res.data["param_binding_note"]

    def test_all_combos_dead_detected(self):
        res = self._run_wfo(param_strategy(use_param=False))
        assert res.data["param_binding_valid"] is False

# ---------------------------------------------------------------------------
# P1-9: trade metrics dari pooled_trades (event log), bukan bar-return
# ---------------------------------------------------------------------------

class TestP19TradeMetrics:

    def _stats_with(self, oos_result):
        run = make_run()
        run.oos_result = oos_result
        StatisticsStage().run(run)
        return run.statistics_result

    def test_event_log_basis_used_when_pooled_trades(self):
        trades = [
            {"timestamp": 1.0, "action": "BUY", "price": 100.0, "pnl": 0.5},
            {"timestamp": 2.0, "action": "SELL", "price": 101.0, "pnl": -0.25},
            {"timestamp": 3.0, "action": "BUY", "price": 100.5, "pnl": 0.25},
            {"timestamp": 4.0, "action": "SELL", "price": 99.5, "pnl": 0.0},
        ]
        stats = self._stats_with({
            "pooled_sharpe": 0.5, "pooled_oos_returns": [0.01, -0.005, 0.01, 0.0],
            "n_obs": 4, "effective_trial_count": 2, "pooled_trades": trades,
        })
        assert stats["total_trades"] == 4
        assert stats["win_count"] == 2
        assert stats["loss_count"] == 1
        assert stats["win_rate"] == pytest.approx(50.0)
        assert stats["trade_metrics_basis"].startswith("turnover_event_log")
        assert stats["pooled_trades_count"] == 4

    def test_bar_return_fallback_labeled_honestly(self):
        stats = self._stats_with({
            "pooled_sharpe": 0.5,
            "pooled_oos_returns": [0.01, -0.005, 0.01, 0.005],
            "n_obs": 4, "effective_trial_count": 2,
        })
        assert stats["trade_metrics_basis"] == "bar_return_observations (FALLBACK: tanpa pooled_trades; bukan ledger trade)"

    def test_verifier_recomputes_from_pooled_trades(self):
        trades = [
            {"timestamp": 1.0, "pnl": 0.5},
            {"timestamp": 2.0, "pnl": -0.25},
            {"timestamp": 3.0, "pnl": 0.25},
        ]
        run = make_run()
        run.statistics_result = {
            "win_rate": 66.67, "profit_factor": 3.0, "return_pct": 1.5,
            "sharpe": 0.5, "max_dd_pct": 1.0, "total_trades": 3,
        }
        run.oos_result = {
            "pooled_oos_returns": [0.01, -0.005, 0.01],
            "pooled_trades": trades,
        }
        res = IndependentVerifier.full_verification(run.to_dict())
        assert res["trade_metrics"]["basis"] == "turnover_event_log (pooled_trades)"
        assert res["trade_metrics"]["valid"] is True

    def test_wfo_evidence_pools_trades_integration(self):
        """Rantai penuh: engine -> WFOEvidence.pooled_trades -> OOSStage -> StatisticsStage."""
        engine = IsolatedBacktestEngine()
        df = make_df(500)
        param_grid = [{"lookback": v} for v in (5.0, 10.0)]

        def factory(params):
            def logic(df_inner):
                d = df_inner.with_columns(pl.lit(float(params["lookback"])).alias("_param_lookback"))
                return param_strategy(use_param=True)(d)
            return logic

        ev = engine.run_walk_forward_optimization(
            strategy_factory=factory,
            param_grid=param_grid,
            historical_data=df,
            train_window_bars=100, test_window_bars=80, step_bars=80,
            purge_bars=10, warmup_bars=5,
            execution_model=build_execution_model(),
        )
        assert len(ev.pooled_trades) > 0, "pooled_trades harus terisi dari OOS trade log"

        run = make_run()
        run.wfo_result = ev.to_dict()
        oos_res = OOSStage().run(run)
        assert oos_res.status == RunStage.PASSED
        assert len(run.oos_result["pooled_trades"]) > 0

        stats = StatisticsStage().run(run)
        assert stats.status == RunStage.PASSED
        assert run.statistics_result["trade_metrics_basis"].startswith("turnover_event_log")
        assert run.statistics_result["total_trades"] == len(run.oos_result["pooled_trades"])

    def test_wfo_evidence_default_pooled_trades(self):
        ev = WFOEvidence(
            run_id="x", dataset_hash="h", timeframe_seconds=60.0,
            data_start_ts=0.0, data_end_ts=1.0, folds=(),
            fold_count=0, parameter_family_size=1, evaluation_count=0,
            effective_trial_count=1, effective_trial_method="M",
            effective_trial_assumption="A", training_overlap_ratio=0.0,
            oos_overlap_ratio=0.0, purge_bars=0, label_horizon_bars=0,
            label_horizon_unit="BARS", warmup_bars=0,
            pooled_oos_returns=(), pooled_oos_equity=(),
            pooled_oos_sharpe=0.0, pooled_oos_return=0.0,
            pooled_oos_max_drawdown=0.0, mean_fold_oos_sharpe=0.0,
            median_fold_oos_sharpe=0.0, worst_fold_oos_sharpe=0.0,
            std_fold_oos_sharpe=0.0, mean_wfe=0.0, median_wfe=0.0,
            worst_wfe=0.0, provenance_hash="",
        )
        assert ev.to_dict()["pooled_trades"] == []


# ---------------------------------------------------------------------------
# P1-14: config_hash mengikat semua field yang mengubah hasil
# ---------------------------------------------------------------------------

class TestP114ConfigHash:

    def test_identical_configs_same_hash(self):
        assert make_config().config_hash == make_config().config_hash

    def test_selection_metric_bound(self):
        assert make_config(wfo_selection_metric="sortino_ratio").config_hash != make_config().config_hash

    def test_tie_breaker_bound(self):
        assert make_config(wfo_tie_breaker="(sortino, -max_dd)").config_hash != make_config().config_hash

    def test_mc_crisis_psr_bound(self):
        base = make_config().config_hash
        assert make_config(mc_enabled=False).config_hash != base
        assert make_config(crisis_enabled=False).config_hash != base
        assert make_config(psr_enabled=False).config_hash != base

    def test_oos_nobs_fed_from_pooled_returns(self):
        """n_obs di OOSStage harus = len(pooled_oos_returns), bukan 0 (bug lama:
        WFOEvidence tanpa field n_obs -> Final Gate INVALID permanen)."""
        run = make_run()
        run.wfo_result = {
            "pooled_oos_sharpe": 0.5, "pooled_oos_return": 0.01,
            "pooled_oos_max_drawdown": 0.05, "fold_count": 2,
            "pooled_oos_returns": list(range(12)), "pooled_trades": [],
            "effective_trial_count": 2, "parameter_family_size": 2,
        }
        res = OOSStage().run(run)
        assert res.status == RunStage.PASSED
        assert run.oos_result["n_obs"] == 12
        from are.research.stages.gate import GateStage
        stats = StatisticsStage().run(run)
        assert run.statistics_result["n_obs"] == 12
        gate_res = GateStage().run(run, make_config())
        # n_obs >= 10 & trials >= 1 -> early INVALID evidence_sufficiency tidak boleh fire
        assert not (
            (gate_res.data or {}).get("decision") == "INVALID"
            and any(c.get("check") == "evidence_sufficiency" for c in (gate_res.data or {}).get("checks", []))
        )
