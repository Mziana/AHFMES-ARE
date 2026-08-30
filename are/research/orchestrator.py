"""
AHFMES ARE -- Backtest Orchestrator (Slice BT-04 + BT-05)

Orchestrates the complete research backtest lifecycle:
PRECHECK -> DATA -> STRATEGY -> BASELINE -> WFO -> OOS -> STATISTICS -> CRISIS -> GATE -> ARTIFACT

Produces BacktestRun -- one immutable research object per experiment.

Zero external dependencies except Polars + stdlib.
"""

from __future__ import annotations

import json
import os
import time
import dataclasses
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import polars as pl
except ImportError:
    raise ImportError("Polars required: pip install polars")

from are.backtest import (
    IsolatedBacktestEngine,
    BacktestResult,
    WFOEvidence,
    baseline_buy_and_hold,
    baseline_always_flat,
    baseline_naive_long,
    baseline_naive_short,
    baseline_random_permutation,
    run_baseline_comparison,
    parameter_stability_analysis,
)
from are.data_pipeline import DataPurifier
from are.hasher import compute_sha256
from are.research.dataset_registry import DatasetRegistry, DatasetManifest, DataQualityGate
from are.research.experiment_config import (
    ExperimentConfig,
    StrategyIdentity,
    ExecutionModel,
    ParameterGrid,
)


class RunStage(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class RunStatus(Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class GateDecision(Enum):
    PASS = "PASS"
    BORDERLINE = "BORDERLINE"
    FAIL = "FAIL"
    INVALID = "INVALID"


@dataclass
class StageResult:
    stage: str
    status: RunStage
    started_at: float = 0.0
    completed_at: float = 0.0
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ArtifactManifest:
    """Complete artifact manifest for a backtest run."""
    run_id: str
    artifact_hash: str
    dataset_hash: str
    strategy_hash: str
    config_hash: str
    execution_model_hash: str
    wfo_provenance_hash: str
    files: Dict[str, str] = field(default_factory=dict)  # path -> hash
    created_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BacktestRun:
    """
    Primary research object. One run = one immutable experiment.
    Contains the full lifecycle of a backtest from data to artifact.
    """
    run_id: str
    experiment_id: str
    created_at: float
    engine_version: str = "4.0.0"

    # Identity
    strategy_id: str = ""
    strategy_version: str = ""
    dataset_id: str = ""
    dataset_hash: str = ""
    purified_hash: str = ""
    config_hash: str = ""
    execution_model_hash: str = ""

    # Status
    status: RunStatus = RunStatus.CREATED
    stages: Dict[str, StageResult] = field(default_factory=dict)

    # Results
    baseline_result: Optional[Dict[str, Any]] = None
    wfo_result: Optional[Dict[str, Any]] = None
    oos_result: Optional[Dict[str, Any]] = None
    statistics_result: Optional[Dict[str, Any]] = None
    crisis_result: Optional[Dict[str, Any]] = None
    stability_result: Optional[Dict[str, Any]] = None
    final_gate: Optional[Dict[str, Any]] = None
    quality_report: Optional[Dict[str, Any]] = None

    # Artifact
    artifact_manifest: Optional[ArtifactManifest] = None
    provenance_hash: str = ""

    # Timestamps
    started_at: float = 0.0
    completed_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = {}
        for f in dataclasses.fields(self):
            val = getattr(self, f.name)
            if isinstance(val, Enum):
                d[f.name] = val.value
            elif f.name == "stages":
                d[f.name] = {}
                for sk, sv in val.items():
                    if isinstance(sv, StageResult):
                        sd = {kk: vv.value if isinstance(vv, Enum) else vv for kk, vv in asdict(sv).items()}
                        d[f.name][sk] = sd
                    else:
                        d[f.name][sk] = sv
            elif isinstance(val, list):
                d[f.name] = [item.to_dict() if hasattr(item, "to_dict") else item for item in val]
            elif hasattr(val, "to_dict"):
                d[f.name] = val.to_dict()
            else:
                d[f.name] = val
        return d


class BacktestOrchestrator:
    """
    Full research backtest orchestrator.
    Controls the lifecycle: DATA -> STRATEGY -> BASELINE -> WFO -> OOS -> STATISTICS -> CRISIS -> GATE -> ARTIFACT
    """

    RUNS_DIR = "data/backtest_runs"

    def __init__(self):
        os.makedirs(self.RUNS_DIR, exist_ok=True)

    def run_experiment(
        self,
        config: ExperimentConfig,
        dataset_manifest: DatasetManifest,
        df: pl.DataFrame,
        strategy_logic: Callable[[pl.DataFrame], pl.DataFrame],
        callback: Optional[Callable[[str, StageResult], None]] = None,
    ) -> BacktestRun:
        """
        Execute a full backtest experiment through all stages.
        callback(stage_name, stage_result) is called after each stage.
        """
        run_id = f"BT-{int(time.time())}-{os.urandom(3).hex()}"
        run = BacktestRun(
            run_id=run_id,
            experiment_id=config.experiment_id,
            created_at=time.time(),
            strategy_id=config.strategy.strategy_id,
            strategy_version=config.strategy.strategy_version,
            dataset_id=dataset_manifest.dataset_id,
            dataset_hash=dataset_manifest.raw_hash,
            purified_hash=dataset_manifest.purified_hash,
            config_hash=config.config_hash,
            execution_model_hash=config.execution_model.model_hash,
        )

        run.started_at = time.time()
        run.status = RunStatus.RUNNING
        em = config.execution_model

        try:
            # -- Stage 1: DATA --
            run.stages["data"] = self._stage_data(run, df, dataset_manifest)
            if callback:
                callback("data", run.stages["data"])
            if run.stages["data"].status == RunStage.FAILED:
                run.status = RunStatus.FAILED
                return run

            # -- Stage 2: STRATEGY --
            run.stages["strategy"] = self._stage_strategy(run, config, strategy_logic, df)
            if callback:
                callback("strategy", run.stages["strategy"])
            if run.stages["strategy"].status == RunStage.FAILED:
                run.status = RunStatus.FAILED
                return run

            # -- Stage 3: BASELINE --
            run.stages["baseline"] = self._stage_baseline(run, df, em)
            if callback:
                callback("baseline", run.stages["baseline"])

            # -- Stage 4: WFO --
            run.stages["wfo"] = self._stage_wfo(run, config, df, strategy_logic, em)
            if callback:
                callback("wfo", run.stages["wfo"])
            if run.stages["wfo"].status == RunStage.FAILED:
                run.status = RunStatus.FAILED
                return run

            # -- Stage 5: OOS --
            run.stages["oos"] = self._stage_oos(run)
            if callback:
                callback("oos", run.stages["oos"])

            # -- Stage 6: STATISTICS --
            run.stages["statistics"] = self._stage_statistics(run)
            if callback:
                callback("statistics", run.stages["statistics"])

            # -- Stage 7: CRISIS --
            run.stages["crisis"] = self._stage_crisis(run, config, df, strategy_logic, em)
            if callback:
                callback("crisis", run.stages["crisis"])

            # -- Stage 8: STABILITY --
            run.stages["stability"] = self._stage_stability(run, config, df, strategy_logic)
            if callback:
                callback("stability", run.stages["stability"])

            # -- Stage 9: FINAL GATE --
            run.stages["final_gate"] = self._stage_gate(run, config)
            if callback:
                callback("final_gate", run.stages["final_gate"])

            # -- Stage 10: ARTIFACT --
            run.stages["artifact"] = self._stage_artifact(run, config, dataset_manifest)
            if callback:
                callback("artifact", run.stages["artifact"])

            run.status = RunStatus.COMPLETED

        except Exception as e:
            run.status = RunStatus.FAILED
            run.stages["_error"] = StageResult(
                stage="_error", status=RunStage.FAILED, error=str(e)
            )

        run.completed_at = time.time()

        # Save run manifest
        self._save_run(run)
        return run

    def _stage_data(self, run: BacktestRun, df: pl.DataFrame, manifest: DatasetManifest) -> StageResult:
        """Validate data quality and freeze."""
        t0 = time.time()
        gate = DataQualityGate.validate(df)
        run.quality_report = gate

        if gate["gate"] == "FAIL":
            return StageResult(
                stage="data", status=RunStage.FAILED,
                started_at=t0, completed_at=time.time(),
                data=gate, error=f"Data quality gate FAILED: {gate['failed_count']} failures",
            )

        return StageResult(
            stage="data", status=RunStage.PASSED,
            started_at=t0, completed_at=time.time(),
            data={"rows": len(df), "gate": gate["gate"], "warnings": gate["warn_count"]},
        )

    def _stage_strategy(self, run: BacktestRun, config: ExperimentConfig,
                        strategy_logic: Callable, df: pl.DataFrame) -> StageResult:
        """Validate strategy produces valid signal output."""
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

    def _stage_baseline(self, run: BacktestRun, df: pl.DataFrame, em: ExecutionModel) -> StageResult:
        """Run baseline comparisons."""
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

    def _stage_wfo(self, run: BacktestRun, config: ExperimentConfig,
                   df: pl.DataFrame, strategy_logic: Callable,
                   em: ExecutionModel) -> StageResult:
        """Run Walk-Forward Optimization."""
        t0 = time.time()
        engine = IsolatedBacktestEngine()

        # Build param grid values
        pg = config.parameter_grid
        param_values = list(pg.param_values[0]) if pg.param_values else [20]

        def strategy_factory(params):
            def logic(df_inner):
                lb = int(params.get("lookback", params.get("emaFast", 20)))
                return df_inner.with_columns(
                    pl.col("price").rolling_mean(lb).alias("fast_ma"),
                    pl.col("price").rolling_mean(max(lb * 2, lb + 10)).alias("slow_ma"),
                ).with_columns(
                    pl.when(pl.col("fast_ma") > pl.col("slow_ma")).then(1.0)
                    .when(pl.col("fast_ma") < pl.col("slow_ma")).then(-1.0)
                    .otherwise(0.0).alias("signal")
                )
            return logic

        param_grid = [{"lookback": v} for v in param_values]

        try:
            wfo_evidence = engine.run_walk_forward_optimization(
                strategy_factory=strategy_factory,
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

            run.wfo_result = {
                "run_id": wfo_evidence.run_id,
                "fold_count": wfo_evidence.fold_count,
                "pooled_oos_sharpe": wfo_evidence.pooled_oos_sharpe,
                "pooled_oos_return": wfo_evidence.pooled_oos_return,
                "pooled_oos_max_drawdown": wfo_evidence.pooled_oos_max_drawdown,
                "mean_wfe": wfo_evidence.mean_wfe,
                "provenance_hash": wfo_evidence.provenance_hash,
            }
            run.provenance_hash = wfo_evidence.provenance_hash

            return StageResult(
                stage="wfo", status=RunStage.PASSED,
                started_at=t0, completed_at=time.time(),
                data=run.wfo_result,
            )
        except Exception as e:
            return StageResult(
                stage="wfo", status=RunStage.FAILED,
                started_at=t0, completed_at=time.time(), error=str(e),
            )

    def _stage_oos(self, run: BacktestRun) -> StageResult:
        """Extract OOS results from WFO."""
        t0 = time.time()
        if not run.wfo_result:
            return StageResult(stage="oos", status=RunStage.SKIPPED, started_at=t0, completed_at=time.time())

        run.oos_result = {
            "pooled_sharpe": run.wfo_result.get("pooled_oos_sharpe", 0.0),
            "pooled_return": run.wfo_result.get("pooled_oos_return", 0.0),
            "pooled_max_dd": run.wfo_result.get("pooled_oos_max_drawdown", 0.0),
            "fold_count": run.wfo_result.get("fold_count", 0),
        }
        return StageResult(
            stage="oos", status=RunStage.PASSED,
            started_at=t0, completed_at=time.time(), data=run.oos_result,
        )

    def _stage_statistics(self, run: BacktestRun) -> StageResult:
        """Compile statistics summary."""
        t0 = time.time()
        oos = run.oos_result or {}
        wfo = run.wfo_result or {}

        run.statistics_result = {
            "sharpe": oos.get("pooled_sharpe", 0.0),
            "return_pct": oos.get("pooled_return", 0.0) * 100,
            "max_dd_pct": oos.get("pooled_max_dd", 0.0) * 100,
            "wfe": wfo.get("mean_wfe", 0.0),
            "fold_count": oos.get("fold_count", 0),
        }
        return StageResult(
            stage="statistics", status=RunStage.PASSED,
            started_at=t0, completed_at=time.time(), data=run.statistics_result,
        )

    def _stage_crisis(self, run: BacktestRun, config: ExperimentConfig,
                      df: pl.DataFrame, strategy_logic: Callable,
                      em: ExecutionModel) -> StageResult:
        """Run crisis replay."""
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

    def _stage_stability(self, run: BacktestRun, config: ExperimentConfig,
                         df: pl.DataFrame, strategy_logic: Callable) -> StageResult:
        """Parameter stability analysis."""
        t0 = time.time()
        try:
            engine = IsolatedBacktestEngine()
            pg = config.parameter_grid
            values = list(pg.param_values[0]) if pg.param_values else [10, 20, 30]

            # Extend range around values
            if len(values) >= 2:
                step = values[1] - values[0] if len(values) > 1 else 5
                extended = [values[0] - step] + values + [values[-1] + step]
            else:
                extended = [values[0] - 5, values[0], values[0] + 5]

            def mutator(df_inner, val):
                return df_inner.with_columns(
                    pl.col("price").rolling_mean(int(val)).alias("fast_ma"),
                    pl.col("price").rolling_mean(max(int(val) * 2, int(val) + 10)).alias("slow_ma"),
                ).with_columns(
                    pl.when(pl.col("fast_ma") > pl.col("slow_ma")).then(1.0)
                    .when(pl.col("fast_ma") < pl.col("slow_ma")).then(-1.0)
                    .otherwise(0.0).alias("signal")
                )

            stability = parameter_stability_analysis(
                engine=engine, historical_data=df,
                base_strategy=strategy_logic,
                param_name=pg.param_names[0] if pg.param_names else "lookback",
                param_values=extended,
                param_mutator=mutator,
            )
            run.stability_result = stability
            return StageResult(
                stage="stability", status=RunStage.PASSED,
                started_at=t0, completed_at=time.time(), data={"verdict": stability.get("verdict", "UNKNOWN")},
            )
        except Exception as e:
            return StageResult(
                stage="stability", status=RunStage.FAILED,
                started_at=t0, completed_at=time.time(), error=str(e),
            )

    def _stage_gate(self, run: BacktestRun, config: ExperimentConfig) -> StageResult:
        """Final gate decision."""
        t0 = time.time()
        oos = run.oos_result or {}
        stats = run.statistics_result or {}
        crisis = run.crisis_result or {}
        stability = run.stability_result or {}

        checks = []

        # OOS Sharpe > 0
        oos_sharpe = oos.get("pooled_sharpe", 0.0)
        checks.append({"check": "oos_sharpe_positive", "pass": oos_sharpe > 0, "value": oos_sharpe})

        # WFE > 0 (OOS > 0 relative to IS)
        wfe = stats.get("wfe", 0.0)
        checks.append({"check": "wfe_positive", "pass": wfe > 0, "value": wfe})

        # Max DD < 50%
        max_dd = oos.get("pooled_max_dd", 1.0)
        checks.append({"check": "max_dd_acceptable", "pass": max_dd < 0.50, "value": max_dd})

        # Crisis survival
        checks.append({"check": "crisis_survival", "pass": crisis.get("survived", False), "value": crisis.get("survived", False)})

        # Parameter stability
        checks.append({"check": "param_stability", "pass": stability.get("verdict") in ("ROBUST", "MARGINAL"), "value": stability.get("verdict", "UNKNOWN")})

        # Baseline beat
        baseline = run.baseline_result or {}
        best_baseline_sharpe = max((v.get("sharpe", -999) for v in baseline.values() if isinstance(v, dict) and "error" not in v), default=0.0)
        checks.append({"check": "beats_baselines", "pass": oos_sharpe > best_baseline_sharpe, "value": f"{oos_sharpe:.4f} > {best_baseline_sharpe:.4f}"})

        failed = [c for c in checks if not c["pass"]]
        passed = [c for c in checks if c["pass"]]

        if len(failed) == 0:
            decision = GateDecision.PASS
        elif len(failed) <= 2 and len(passed) >= 3:
            decision = GateDecision.BORDERLINE
        elif len(failed) <= len(checks) // 2:
            decision = GateDecision.FAIL
        else:
            decision = GateDecision.INVALID

        gate = {
            "decision": decision.value,
            "checks": checks,
            "passed": len(passed),
            "failed": len(failed),
            "total": len(checks),
        }
        run.final_gate = gate

        return StageResult(
            stage="final_gate", status=RunStage.PASSED,
            started_at=t0, completed_at=time.time(), data=gate,
        )

    def _stage_artifact(self, run: BacktestRun, config: ExperimentConfig,
                        manifest: DatasetManifest) -> StageResult:
        """Save artifact manifest."""
        t0 = time.time()
        run_dir = os.path.join(self.RUNS_DIR, run.run_id)
        os.makedirs(run_dir, exist_ok=True)

        # Save run as JSON
        run_file = os.path.join(run_dir, "run.json")
        with open(run_file, "w") as f:
            json.dump(run.to_dict(), f, indent=2, default=str)

        # Compute artifact hash
        with open(run_file) as f:
            artifact_hash = compute_sha256(f.read().encode())

        artifact = ArtifactManifest(
            run_id=run.run_id,
            artifact_hash=artifact_hash,
            dataset_hash=run.dataset_hash,
            strategy_hash=config.strategy.source_hash,
            config_hash=config.config_hash,
            execution_model_hash=run.execution_model_hash,
            wfo_provenance_hash=run.provenance_hash,
            files={"run.json": artifact_hash},
            created_at=time.time(),
        )

        # Save manifest
        manifest_file = os.path.join(run_dir, "manifest.json")
        with open(manifest_file, "w") as f:
            json.dump(artifact.to_dict(), f, indent=2)

        run.artifact_manifest = artifact

        return StageResult(
            stage="artifact", status=RunStage.PASSED,
            started_at=t0, completed_at=time.time(),
            data={"artifact_hash": artifact_hash[:16], "run_dir": run_dir},
        )

    def _save_run(self, run: BacktestRun):
        """Save the completed run."""
        run_dir = os.path.join(self.RUNS_DIR, run.run_id)
        os.makedirs(run_dir, exist_ok=True)
        with open(os.path.join(run_dir, "run.json"), "w") as f:
            json.dump(run.to_dict(), f, indent=2, default=str)

    def load_run(self, run_id: str) -> BacktestRun:
        """Load a completed run."""
        run_file = os.path.join(self.RUNS_DIR, run_id, "run.json")
        if not os.path.exists(run_file):
            raise FileNotFoundError(f"Run {run_id} not found")
        with open(run_file) as f:
            data = json.load(f)
        # Reconstruct BacktestRun
        data["status"] = RunStatus(data["status"])
        data["stages"] = {k: StageResult(**v) for k, v in data.get("stages", {}).items()}
        return BacktestRun(**data)

    def list_runs(self) -> List[Dict[str, Any]]:
        """List all runs with summary."""
        runs = []
        if not os.path.exists(self.RUNS_DIR):
            return runs
        for name in os.listdir(self.RUNS_DIR):
            rf = os.path.join(self.RUNS_DIR, name, "run.json")
            if os.path.exists(rf):
                with open(rf) as f:
                    data = json.load(f)
                runs.append({
                    "run_id": data.get("run_id", name),
                    "strategy_id": data.get("strategy_id", ""),
                    "status": data.get("status", ""),
                    "created_at": data.get("created_at", 0),
                    "gate": data.get("final_gate", {}).get("decision", "UNKNOWN"),
                })
        return sorted(runs, key=lambda x: x["created_at"], reverse=True)
