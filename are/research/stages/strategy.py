"""
AHFMES ARE — Strategy Stages

Strategy validation, leakage firewall, and baseline comparison.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict

try:
    import polars as pl
except ImportError:
    raise ImportError("Polars required")

from are.research.types import RunStage, StageResult, BacktestRun
from are.research.experiment_config import ExperimentConfig, ExecutionModel
from are.research.integrity import LeakageFirewall, TemporalContract
from are.backtest import (
    IsolatedBacktestEngine,
    baseline_buy_and_hold,
    baseline_always_flat,
    baseline_naive_long,
    baseline_naive_short,
    baseline_random_permutation,
)


class StrategyStage:
    """Validate strategy produces valid signal output."""

    def run(self, run: BacktestRun, config: ExperimentConfig,
            strategy_logic: Callable, df: pl.DataFrame) -> StageResult:
        t0 = time.time()
        try:
            result = strategy_logic(df)
            if "signal" not in result.columns:
                return StageResult(
                    stage="strategy", status=RunStage.FAILED,
                    started_at=t0, completed_at=time.time(),
                    error="Strategy did not produce 'signal' column",
                )

            signals = result["signal"]
            valid_signals = signals.is_in([-1.0, 0.0, 1.0]).all()
            has_nulls = signals.is_null().any()
            has_nan = signals.is_nan().any() if hasattr(signals, 'is_nan') else False

            issues = []
            if has_nulls:
                issues.append("null signals")
            if has_nan:
                issues.append("NaN signals")

            if issues:
                return StageResult(
                    stage="strategy", status=RunStage.FAILED,
                    started_at=t0, completed_at=time.time(),
                    error=f"Invalid signals: {', '.join(issues)}",
                )

            return StageResult(
                stage="strategy", status=RunStage.PASSED,
                started_at=t0, completed_at=time.time(),
                data={
                    "strategy_id": config.strategy.strategy_id,
                    "source_hash": config.strategy.source_hash[:16],
                    "total_bars": len(df),
                    "signal_distribution": {
                        "long": int((signals == 1.0).sum()),
                        "short": int((signals == -1.0).sum()),
                        "flat": int((signals == 0.0).sum()),
                    },
                },
            )
        except Exception as e:
            return StageResult(
                stage="strategy", status=RunStage.FAILED,
                started_at=t0, completed_at=time.time(), error=str(e),
            )


class LeakageStage:
    """Run leakage / temporal firewall check. WARNING only — engine handles shift."""

    def run(self, run: BacktestRun, config: ExperimentConfig,
            strategy_logic: Callable, df: pl.DataFrame,
            contract: TemporalContract) -> StageResult:
        t0 = time.time()
        try:
            result = strategy_logic(df)
            validation = LeakageFirewall.validate_signal_timing(result, contract)
            validation["note"] = "WARNING: Engine handles signal shift internally. Strategy output is pre-shift."
            return StageResult(
                stage="leakage", status=RunStage.PASSED,
                started_at=t0, completed_at=time.time(), data=validation,
            )
        except Exception as e:
            return StageResult(
                stage="leakage", status=RunStage.FAILED,
                started_at=t0, completed_at=time.time(), error=str(e),
            )


class BaselineStage:
    """Run baseline comparisons."""

    def run(self, run: BacktestRun, df: pl.DataFrame, em: ExecutionModel) -> StageResult:
        t0 = time.time()
        engine = IsolatedBacktestEngine()

        results = {}
        baselines = {
            "buy_and_hold": baseline_buy_and_hold,
            "always_flat": baseline_always_flat,
            "naive_long": baseline_naive_long,
            "naive_short": baseline_naive_short,
            "random": baseline_random_permutation,
        }

        for name, logic in baselines.items():
            try:
                r = engine.run_backtest(
                    strategy_logic=logic, historical_data=df,
                    initial_capital=em.initial_capital,
                    timeframe_seconds=3600.0,
                    spread_pct=em.spread_pct, slippage_pct=em.slippage_pct,
                    commission_pct=em.commission_pct,
                    execution_model=em,
                )
                results[name] = {
                    "sharpe": r.metrics.get("sharpe_ratio", 0.0),
                    "return_pct": r.metrics.get("total_return_pct", 0.0),
                    "max_dd_pct": r.metrics.get("max_drawdown_pct", 0.0),
                }
            except Exception:
                results[name] = {"error": True}

        run.baseline_result = results
        return StageResult(
            stage="baseline", status=RunStage.PASSED,
            started_at=t0, completed_at=time.time(),
            data={"baseline_count": len(results)},
        )
