"""
AHFMES ARE -- Backtest Orchestrator (Slice BT-04 + BT-05)

Orchestrates the complete research backtest lifecycle:
PRECHECK -> DATA -> STRATEGY -> BASELINE -> WFO -> OOS -> STATISTICS -> CRISIS -> GATE -> ARTIFACT

Produces BacktestRun -- one immutable research object per experiment.

This is a thin coordinator. Stage logic lives in are.research.stages.*.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Callable, Dict, List, Optional

from are.atomic_io import atomic_write_json
from are.run_state import RunStateManager, RunPhase
from are.input_guard import validate_param_grid, validate_numeric

try:
    import polars as pl
except ImportError:
    raise ImportError("Polars required: pip install polars")

from are.hasher import compute_sha256
from are.research.dataset_registry import DatasetRegistry, DatasetManifest
from are.research.experiment_config import (
    ExperimentConfig,
    ExecutionModel,
)
from are.research.integrity import (
    LeakageFirewall,
    HoldoutManager,
    HoldoutEvaluationEngine,
    resolve_holdout_selected_params,
    EvidenceBinding,
    compute_canonical_dataset_hash,
)

# -- Shared types (re-exported for backward compatibility) --
from are.research.types import (  # noqa: F401
    RunStage,
    RunStatus,
    GateDecision,
    StageResult,
    ArtifactManifest,
    BacktestRun,
)

# -- Stage imports --
from are.research.stages.data import DataStage
from are.research.stages.strategy import StrategyStage, LeakageStage, BaselineStage
from are.research.stages.precheck import HoldoutSetupStage
from are.research.stages.wfo import WFOStage, OOSStage, StabilityStage, SensitivityStage
from are.research.stages.statistics import StatisticsStage
from are.research.stages.crisis import CrisisStage
from are.research.stages.gate import GateStage, VerifyStage
from are.research.stages.artifact import ArtifactStage, save_run


class BacktestOrchestrator:
    """
    Full research backtest orchestrator.
    Controls the lifecycle: DATA -> STRATEGY -> BASELINE -> WFO -> OOS -> STATISTICS -> CRISIS -> GATE -> ARTIFACT
    """

    RUNS_DIR = "data/backtest_runs"
    DEFAULT_STAGE_TIMEOUT = 300  # 5 minutes per stage

    STAGE_TIMEOUTS = {
        "data": 30,
        "strategy": 30,
        "leakage": 30,
        "holdout_setup": 10,
        "baseline": 60,
        "wfo": 300,
        "oos": 10,
        "statistics": 30,
        "crisis": 60,
        "stability": 120,
        "sensitivity": 120,
        "final_gate": 10,
        "artifact": 30,
        "verify": 30,
    }

    def __init__(self):
        os.makedirs(self.RUNS_DIR, exist_ok=True)
        # Stage instances
        self._data_stage = DataStage()
        self._strategy_stage = StrategyStage()
        self._leakage_stage = LeakageStage()
        self._holdout_stage = HoldoutSetupStage()
        self._baseline_stage = BaselineStage()
        self._wfo_stage = WFOStage()
        self._oos_stage = OOSStage()
        self._statistics_stage = StatisticsStage()
        self._crisis_stage = CrisisStage()
        self._stability_stage = StabilityStage()
        self._sensitivity_stage = SensitivityStage()
        self._gate_stage = GateStage()
        self._verify_stage = VerifyStage()
        self._artifact_stage = ArtifactStage()

    def run_experiment(
        self,
        config: ExperimentConfig,
        dataset_manifest: DatasetManifest,
        df: pl.DataFrame,
        strategy_logic: Callable[[pl.DataFrame], pl.DataFrame],
        callback: Optional[Callable[[str, StageResult], None]] = None,
    ) -> BacktestRun:
        """Execute a full backtest experiment through all stages."""
        # Content-addressed run ID
        run_hash = compute_sha256(
            (dataset_manifest.raw_hash + config.strategy.source_hash +
             config.config_hash + config.execution_model.model_hash).encode()
        )
        run_id = f"BT-{run_hash[:16]}"

        existing_dir = os.path.join(self.RUNS_DIR, run_id)
        if os.path.exists(os.path.join(existing_dir, "run.json")):
            return self.load_run(run_id)

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

        # Input validation
        validate_numeric(config.execution_model.initial_capital, "initial_capital", min_val=1, max_val=1e12)
        if config.parameter_grid.grid_size > 0:
            validate_param_grid(
                [{k: v for k, v in zip(config.parameter_grid.param_names or ['x'], combo)}
                 for combo in (config.parameter_grid.param_values or [])],
                max_combos=10000,
            )

        run.started_at = time.time()
        run.status = RunStatus.RUNNING
        em = config.execution_model
        run.random_seed = 42
        run.mc_simulations = config.mc_simulations
        run.initial_capital = config.execution_model.initial_capital

        run_state_mgr = RunStateManager(os.path.join(self.RUNS_DIR, run.run_id))
        run_state_mgr.transition(RunPhase.RUNNING)

        # Complexity guard
        grid_size = config.parameter_grid.grid_size
        estimated_folds = max(1, (len(df) if df is not None else 10000) // 500)
        estimated_work = grid_size * estimated_folds
        MAX_WORK_BUDGET = 50000
        if estimated_work > MAX_WORK_BUDGET:
            raise ValueError(
                f"Work budget exceeded: {grid_size} params x ~{estimated_folds} folds = {estimated_work} > {MAX_WORK_BUDGET}. "
                f"Reduce grid size or increase window size."
            )

        deadline = run.started_at + 600

        contract = LeakageFirewall.build_default_contract()
        run.temporal_contract_hash = contract.contract_hash

        holdout_mgr = HoldoutManager()
        split_id = None

        def _run_stage(name, stage_func, *args, **kwargs):
            """Run a stage with timeout enforcement via cooperative abort."""
            import threading
            timeout = self.STAGE_TIMEOUTS.get(name, self.DEFAULT_STAGE_TIMEOUT)
            stage_deadline = time.time() + timeout
            if time.time() > deadline:
                raise TimeoutError(f"EXPERIMENT_TIMEOUT: Total budget exceeded")

            abort_flag = threading.Event()
            def _abort_if_overdue():
                if time.time() > stage_deadline:
                    abort_flag.set()
            timer = threading.Timer(timeout, _abort_if_overdue)
            timer.daemon = True
            timer.start()
            try:
                result = stage_func(*args, **kwargs)
            finally:
                timer.cancel()

            if isinstance(result, StageResult):
                if time.time() > stage_deadline:
                    result.status = RunStage.FAILED
                    result.error = f"STAGE_TIMEOUT: {name} exceeded {timeout}s limit (hard)"
                if result.status == RunStage.PASSED:
                    run_state_mgr.mark_stage_completed(name)
            else:
                run_state_mgr.mark_stage_completed(name)
            return result

        try:
            # Stage 1: DATA
            run.stages["data"] = _run_stage("data", self._data_stage.run, run, df, dataset_manifest)
            if callback: callback("data", run.stages["data"])
            if run.stages["data"].status == RunStage.FAILED:
                run.status = RunStatus.FAILED
                return run

            # Stage 2: STRATEGY
            run.stages["strategy"] = _run_stage("strategy", self._strategy_stage.run, run, config, strategy_logic, df)
            if callback: callback("strategy", run.stages["strategy"])
            if run.stages["strategy"].status == RunStage.FAILED:
                run.status = RunStatus.FAILED
                return run

            # Stage 2b: LEAKAGE FIREWALL
            run.stages["leakage"] = _run_stage("leakage", self._leakage_stage.run, run, config, strategy_logic, df, contract)
            if callback: callback("leakage", run.stages["leakage"])
            run.leakage_check_passed = run.stages["leakage"].status in (RunStage.PASSED, RunStage.FAILED)

            # Stage 2c: HOLDOUT SPLIT + LOCK
            split_id, holdout_split = _run_stage("holdout_setup", self._holdout_stage.run, run, dataset_manifest, df, holdout_mgr)
            run.holdout_locked = True
            if callback: callback("holdout_setup", StageResult(stage="holdout_setup", status=RunStage.PASSED))

            # Stage 3: BASELINE
            run.stages["baseline"] = _run_stage("baseline", self._baseline_stage.run, run, df, em)
            if callback: callback("baseline", run.stages["baseline"])

            # Stage 4: WFO (on TRAIN portion only)
            train_df = holdout_mgr.get_train(split_id, df)
            run.stages["wfo"] = _run_stage("wfo", self._wfo_stage.run, run, config, train_df, strategy_logic, em)
            if callback: callback("wfo", run.stages["wfo"])
            if run.stages["wfo"].status == RunStage.FAILED:
                run.status = RunStatus.FAILED
                return run

            # Stage 5: OOS
            run.stages["oos"] = _run_stage("oos", self._oos_stage.run, run)
            if callback: callback("oos", run.stages["oos"])

            # Stage 6: STATISTICS
            run.stages["statistics"] = _run_stage("statistics", self._statistics_stage.run, run)
            if callback: callback("statistics", run.stages["statistics"])

            # Stage 7: CRISIS
            run.stages["crisis"] = _run_stage("crisis", self._crisis_stage.run, run, config, df, strategy_logic, em)
            if callback: callback("crisis", run.stages["crisis"])

            # Stage 8: STABILITY
            run.stages["stability"] = _run_stage("stability", self._stability_stage.run, run, config, df, strategy_logic)
            if callback: callback("stability", run.stages["stability"])

            # Stage 8b: SENSITIVITY
            run.stages["sensitivity"] = _run_stage("sensitivity", self._sensitivity_stage.run, run, config, df, strategy_logic)
            if callback: callback("sensitivity", run.stages["sensitivity"])

            # Stage 9b: HOLDOUT EVALUATION (before gate)
            holdout_evidence = None
            if split_id:
                # P0-1: parameter holdout = winner WFO (fold terakhir). TIDAK ada
                # fallback rekaan. Bila parameter dideklarasikan tapi WFO tidak
                # menghasilkan winner, holdout TIDAK dievaluasi -> INVALID.
                has_params = bool(
                    config.parameter_grid
                    and config.parameter_grid.param_names
                )
                selected_params = resolve_holdout_selected_params(run.wfo_result, has_params)

                if selected_params is None:
                    run.holdout_evaluated = False
                    run.holdout_evidence = None
                    run.holdout_invalid_reason = (
                        "HOLDOUT_INVALID: WFO tidak menghasilkan fold winner "
                        "(wfo_result kosong / winner_params hilang) padahal parameter "
                        "dideklarasikan -- holdout TIDAK dievaluasi dengan parameter rekaan."
                    )
                else:
                    holdout_df = holdout_mgr.evaluate_access(split_id, df, caller="orchestrator")
                    holdout_split_obj = holdout_mgr.get_split(split_id)
                    split_hash_val = holdout_split_obj.holdout_hash if holdout_split_obj else ""

                    holdout_evidence = HoldoutEvaluationEngine.evaluate(
                        strategy_logic=strategy_logic,
                        holdout_df=holdout_df,
                        selected_params=selected_params,
                        initial_capital=em.initial_capital,
                        timeframe_seconds=3600.0,
                        spread_pct=em.spread_pct,
                        slippage_pct=em.slippage_pct,
                        commission_pct=em.commission_pct,
                        execution_model=em,
                        run_id=run.run_id,
                        split_id=split_id,
                        dataset_hash=run.dataset_hash,
                        split_hash=split_hash_val,
                        strategy_hash=config.strategy.source_hash,
                        wfo_provenance_hash=run.provenance_hash,
                    )

                    run.holdout_evaluated = True
                    holdout_mgr.evaluate_holdout(split_id)

                    param_hash = compute_sha256(json.dumps(sorted(selected_params.items())).encode())
                    run.evidence_binding = EvidenceBinding(
                        run_id=run.run_id,
                        dataset_hash=run.dataset_hash,
                        strategy_hash=config.strategy.source_hash,
                        parameter_hash=param_hash,
                        wfo_provenance_hash=run.provenance_hash,
                        holdout_provenance_hash=holdout_evidence.provenance_hash,
                    )

            run.holdout_evidence = holdout_evidence.to_dict() if holdout_evidence is not None else None

            # Stage 9: FINAL GATE (after holdout)
            run.stages["final_gate"] = _run_stage("final_gate", self._gate_stage.run, run, config)
            if callback: callback("final_gate", run.stages["final_gate"])

            # Stage 10: ARTIFACT
            run.stages["artifact"] = _run_stage("artifact", self._artifact_stage.run, run, config, dataset_manifest)
            if callback: callback("artifact", run.stages["artifact"])

            # Stage 11: INDEPENDENT VERIFICATION
            run.stages["verify"] = _run_stage("verify", self._verify_stage.run, run)
            if callback: callback("verify", run.stages["verify"])
            run.verification_status = "VERIFIED" if run.stages["verify"].status == RunStage.PASSED else "REJECTED"

            run.status = RunStatus.COMPLETED

        except Exception as e:
            run.status = RunStatus.FAILED
            run.stages["_error"] = StageResult(
                stage="_error", status=RunStage.FAILED, error=str(e)
            )
            run.verification_status = "INVALID"

        run.completed_at = time.time()

        save_run(run)
        return run

    def load_run(self, run_id: str) -> BacktestRun:
        """Load a completed run."""
        run_file = os.path.join(self.RUNS_DIR, run_id, "run.json")
        if not os.path.exists(run_file):
            raise FileNotFoundError(f"Run {run_id} not found")
        with open(run_file) as f:
            data = json.load(f)
        data["status"] = RunStatus(data["status"])
        data["stages"] = {k: StageResult(**v) for k, v in data.get("stages", {}).items()}
        am = data.get("artifact_manifest")
        if isinstance(am, dict):
            data["artifact_manifest"] = ArtifactManifest(**am)
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
