"""
AHFMES ARE — WFO Stages

Walk-Forward Optimization, OOS extraction, parameter stability, and sensitivity analysis.
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
from typing import Any, Callable

try:
    import polars as pl
except ImportError:
    raise ImportError("Polars required")

from are.research.types import RunStage, StageResult, BacktestRun
from are.research.experiment_config import ExperimentConfig, ExecutionModel
from are.backtest import IsolatedBacktestEngine, parameter_stability_analysis


class WFOStage:
    """Run Walk-Forward Optimization using the ACTUAL registered strategy."""

    RUNS_DIR = "data/backtest_runs"

    def run(self, run: BacktestRun, config: ExperimentConfig,
            df: pl.DataFrame, strategy_logic: Callable,
            em: ExecutionModel) -> StageResult:
        t0 = time.time()
        engine = IsolatedBacktestEngine()

        pg = config.parameter_grid
        param_names = pg.param_names or ["lookback"]
        param_values = list(pg.param_values[0]) if pg.param_values else [20]

        # Build param_grid as list of dicts [{param_name: val, ...}, ...]
        param_grid = []
        for vals in (pg.param_values if pg.param_values else [[20]]):
            param_dict = {name: val for name, val in zip(param_names, vals)}
            param_grid.append(param_dict)

        # FIX P0-3: Validate parameter binding before running WFO
        param_binding_valid = False
        if param_grid and len(param_grid) > 1:
            try:
                signals_base = strategy_logic(df)
                signals_vary = None
                test_param = param_grid[0]
                df_test = df
                for k, v in test_param.items():
                    df_test = df_test.with_columns(pl.lit(v).alias(f"_param_{k}"))
                try:
                    signals_vary = strategy_logic(df_test)
                except Exception:
                    pass
                if signals_vary is not None and "signal" in signals_vary.columns:
                    base_sigs = signals_base["signal"].to_list()
                    vary_sigs = signals_vary["signal"].to_list()
                    n_different = sum(1 for a, b in zip(base_sigs, vary_sigs) if a != b)
                    if n_different > 0:
                        param_binding_valid = True
            except Exception:
                pass
        else:
            param_binding_valid = True

        def wfo_strategy_factory(params):
            def logic(df_inner):
                df_with_params = df_inner
                for k, v in params.items():
                    df_with_params = df_with_params.with_columns(
                        pl.lit(v).alias(f"_param_{k}")
                    )
                result = strategy_logic(df_with_params)
                if 'signal' not in result.columns:
                    raise ValueError(f'Strategy did not produce signal column with params {params}')
                return result
            return logic

        try:
            wfo_evidence = engine.run_walk_forward_optimization(
                strategy_factory=wfo_strategy_factory,
                historical_data=df,
                param_grid=param_grid,
                initial_capital=em.initial_capital,
                timeframe_seconds=3600.0,
                spread_pct=em.spread_pct,
                slippage_pct=em.slippage_pct,
                commission_pct=em.commission_pct,
                train_window_bars=config.wfo_train_window_bars,
                test_window_bars=config.wfo_test_window_bars,
                step_bars=config.wfo_step_bars,
                purge_bars=config.wfo_purge_bars,
                warmup_bars=config.wfo_warmup_bars,
            )

            run.wfo_result = wfo_evidence.to_dict()
            run.provenance_hash = wfo_evidence.provenance_hash

            # BT-03+BT-03b: Canonical WFOEvidence persistence + fail-closed + read-back
            wfo_dir = os.path.join(self.RUNS_DIR, run.run_id)
            os.makedirs(wfo_dir, exist_ok=True)
            wfo_file = os.path.join(wfo_dir, "wfo_evidence.json")

            canonical_payload = wfo_evidence.to_dict()
            wfo_file_tmp = wfo_file + ".tmp"
            with open(wfo_file_tmp, "w") as wf:
                json.dump(canonical_payload, wf, indent=2, default=str)
            os.replace(wfo_file_tmp, wfo_file)

            with open(wfo_file) as rf:
                loaded = json.load(rf)
            loaded_hash = loaded.get('provenance_hash', '')
            if loaded_hash != wfo_evidence.provenance_hash:
                raise RuntimeError(
                    f"WFOEvidence persistence FAILED: read-back hash mismatch. "
                    f"Expected {wfo_evidence.provenance_hash[:16]}, got {loaded_hash[:16]}. "
                    f"Run INVALID."
                )

            wfo_artifact = os.path.join(wfo_dir, "wfo", "evidence.json")
            os.makedirs(os.path.dirname(wfo_artifact), exist_ok=True)
            with open(wfo_artifact, "w") as wf:
                json.dump(canonical_payload, wf, indent=2, default=str)

            return StageResult(
                stage="wfo", status=RunStage.PASSED,
                started_at=t0, completed_at=time.time(),
                data={
                    "fold_count": wfo_evidence.fold_count,
                    "provenance": wfo_evidence.provenance_hash[:16],
                    "param_binding_valid": param_binding_valid,
                    "param_binding_note": "Parameters affect strategy output" if param_binding_valid else "WARNING: Parameters may not affect strategy",
                },
            )
        except Exception as e:
            return StageResult(
                stage="wfo", status=RunStage.FAILED,
                started_at=t0, completed_at=time.time(), error=str(e),
            )


class OOSStage:
    """Extract OOS results from WFO — preserves full evidence chain."""

    def run(self, run: BacktestRun) -> StageResult:
        t0 = time.time()
        if not run.wfo_result:
            return StageResult(stage="oos", status=RunStage.SKIPPED, started_at=t0, completed_at=time.time())

        run.oos_result = {
            "pooled_sharpe": run.wfo_result.get("pooled_oos_sharpe", 0.0),
            "pooled_return": run.wfo_result.get("pooled_oos_return", 0.0),
            "pooled_max_dd": run.wfo_result.get("pooled_oos_max_drawdown", 0.0),
            "fold_count": run.wfo_result.get("fold_count", 0),
            "pooled_oos_returns": run.wfo_result.get("pooled_oos_returns", []),
            "effective_trial_count": run.wfo_result.get("effective_trial_count", 1),
            "parameter_family_size": run.wfo_result.get("parameter_family_size", 1),
            "n_obs": run.wfo_result.get("n_obs", 0),
        }
        return StageResult(
            stage="oos", status=RunStage.PASSED,
            started_at=t0, completed_at=time.time(),
            data={"n_obs": run.oos_result["n_obs"], "sharpe": run.oos_result["pooled_sharpe"]},
        )


class StabilityStage:
    """Parameter stability analysis using the ACTUAL registered strategy."""

    def run(self, run: BacktestRun, config: ExperimentConfig,
            df: pl.DataFrame, strategy_logic: Callable) -> StageResult:
        t0 = time.time()
        try:
            engine = IsolatedBacktestEngine()
            pg = config.parameter_grid
            param_names = pg.param_names or ["lookback"]
            values = list(pg.param_values[0]) if pg.param_values else [10, 20, 30]

            if len(values) >= 2:
                step = values[1] - values[0] if len(values) > 1 else 5
                extended = [values[0] - step] + values + [values[-1] + step]
            else:
                extended = [values[0] - 5, values[0], values[0] + 5]

            def mutator(df_inner, val):
                param_name = param_names[0]
                df_with_param = df_inner.with_columns(pl.lit(val).alias(f"_param_{param_name}"))
                try:
                    result = strategy_logic(df_with_param)
                    if "signal" in result.columns:
                        return result
                except Exception as e:
                    logging.warning(f"Stability analysis: param {val} failed: {e}")
                return strategy_logic(df_inner)

            stability = parameter_stability_analysis(
                engine=engine, historical_data=df,
                base_strategy=strategy_logic,
                param_name=param_names[0],
                param_values=extended,
                param_mutator=mutator,
            )
            run.stability_result = stability
            return StageResult(
                stage="stability", status=RunStage.PASSED,
                started_at=t0, completed_at=time.time(),
                data={"verdict": stability.get("verdict", "UNKNOWN")},
            )
        except Exception as e:
            return StageResult(
                stage="stability", status=RunStage.FAILED,
                started_at=t0, completed_at=time.time(), error=str(e),
            )


class SensitivityStage:
    """Run sensitivity and cost stress analysis."""

    def run(self, run: BacktestRun, config: ExperimentConfig,
            df: pl.DataFrame, strategy_logic: Callable) -> StageResult:
        t0 = time.time()
        try:
            from are.research.integrity import SensitivityAnalyzer
            engine = IsolatedBacktestEngine()

            pg = config.parameter_grid
            base_val = list(pg.param_values[0])[len(pg.param_values[0]) // 2] if pg.param_values else 20.0
            param_result = SensitivityAnalyzer.parameter_sensitivity(
                engine, df, strategy_logic, "lookback", base_val
            )

            em = config.execution_model
            cost_result = SensitivityAnalyzer.cost_stress(
                engine, df, strategy_logic,
                base_spread=em.spread_pct, base_slippage=em.slippage_pct,
                base_commission=em.commission_pct,
            )

            return StageResult(
                stage="sensitivity", status=RunStage.PASSED,
                started_at=t0, completed_at=time.time(),
                data={
                    "param_robustness": param_result.get("verdict", "UNKNOWN"),
                    "cost_breakeven": cost_result.get("breakeven_multiplier"),
                    "cost_verdict": cost_result.get("verdict", "UNKNOWN"),
                },
            )
        except Exception as e:
            return StageResult(
                stage="sensitivity", status=RunStage.FAILED,
                started_at=t0, completed_at=time.time(), error=str(e),
            )
