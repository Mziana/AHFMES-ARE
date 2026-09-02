"""
AHFMES ARE — Crisis Replay Stage

Runs strategy evaluation on historical or synthetic Black Swan crisis datasets.
"""

from __future__ import annotations

import time
from typing import Callable

try:
    import polars as pl
except ImportError:
    raise ImportError("Polars required")

from are.research.types import RunStage, StageResult, BacktestRun
from are.research.experiment_config import ExperimentConfig, ExecutionModel
from are.backtest import IsolatedBacktestEngine


class CrisisStage:
    """Run crisis replay."""

    def run(self, run: BacktestRun, config: ExperimentConfig,
            df: pl.DataFrame, strategy_logic: Callable,
            em: ExecutionModel) -> StageResult:
        t0 = time.time()
        try:
            engine = IsolatedBacktestEngine()
            crisis = engine.run_crisis_replay(
                strategy_logic=strategy_logic,
                initial_capital=em.initial_capital,
                timeframe_seconds=3600.0,
                spread_pct=em.spread_pct,
                slippage_pct=em.slippage_pct,
                commission_pct=em.commission_pct,
            )
            run.crisis_result = {
                "survived": crisis.get("survived", False),
                "final_equity": crisis.get("final_equity", 0.0),
                "max_drawdown_pct": crisis.get("max_drawdown_pct", 0.0),
            }
            return StageResult(
                stage="crisis", status=RunStage.PASSED,
                started_at=t0, completed_at=time.time(), data=run.crisis_result,
            )
        except Exception as e:
            return StageResult(
                stage="crisis", status=RunStage.FAILED,
                started_at=t0, completed_at=time.time(), error=str(e),
            )
