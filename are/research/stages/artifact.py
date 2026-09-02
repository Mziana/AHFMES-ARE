"""
AHFMES ARE — Artifact Stage

Saves artifact with full directory structure and persists run manifest.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from are.research.types import RunStage, StageResult, ArtifactManifest, BacktestRun
from are.research.experiment_config import ExperimentConfig
from are.research.dataset_registry import DatasetManifest
from are.atomic_io import atomic_write_json
from are.hasher import compute_sha256


class ArtifactStage:
    """Save artifact with full directory structure."""

    RUNS_DIR = "data/backtest_runs"

    def run(self, run: BacktestRun, config: ExperimentConfig,
            manifest: DatasetManifest) -> StageResult:
        t0 = time.time()
        run_dir = os.path.join(self.RUNS_DIR, run.run_id)
        files_manifest = {}

        for subdir in ["dataset", "baseline", "wfo", "oos", "statistics", "crisis", "holdout", "final_gate"]:
            os.makedirs(os.path.join(run_dir, subdir), exist_ok=True)

        def _write_and_hash(rel_path: str, data: Any):
            full_path = os.path.join(run_dir, rel_path)
            atomic_write_json(full_path, data)
            with open(full_path, "rb") as f:
                files_manifest[rel_path] = compute_sha256(f.read())

        _write_and_hash("dataset/manifest.json", manifest.to_dict())
        if run.quality_report:
            _write_and_hash("dataset/quality_report.json", run.quality_report)
        if run.baseline_result:
            _write_and_hash("baseline/summary.json", run.baseline_result)
        if run.wfo_result:
            _write_and_hash("wfo/evidence.json", run.wfo_result)
        if run.oos_result:
            _write_and_hash("oos/summary.json", run.oos_result)
        if run.statistics_result:
            _write_and_hash("statistics/summary.json", run.statistics_result)
        if run.crisis_result:
            _write_and_hash("crisis/summary.json", run.crisis_result)
        if run.final_gate:
            _write_and_hash("final_gate/decision.json", run.final_gate)
        if run.holdout_evidence:
            _write_and_hash("holdout/evidence.json", run.holdout_evidence)
        _write_and_hash("config.json", config.to_dict())

        all_hashes = json.dumps(files_manifest, sort_keys=True)
        artifact_hash = compute_sha256(all_hashes.encode())

        artifact = ArtifactManifest(
            run_id=run.run_id,
            artifact_hash=artifact_hash,
            dataset_hash=run.dataset_hash,
            strategy_hash=config.strategy.source_hash,
            config_hash=config.config_hash,
            execution_model_hash=run.execution_model_hash,
            wfo_provenance_hash=run.provenance_hash,
            files=files_manifest,
            created_at=time.time(),
        )

        manifest_file = os.path.join(run_dir, "manifest.json")
        atomic_write_json(manifest_file, artifact.to_dict())

        run.artifact_manifest = artifact

        return StageResult(
            stage="artifact", status=RunStage.PASSED,
            started_at=t0, completed_at=time.time(),
            data={"artifact_hash": artifact_hash[:16], "run_dir": run_dir, "files": len(files_manifest)},
        )


def save_run(run: BacktestRun):
    """Save the completed run and patch run.json hash into manifest."""
    runs_dir = "data/backtest_runs"
    run_dir = os.path.join(runs_dir, run.run_id)
    os.makedirs(run_dir, exist_ok=True)
    run_file = os.path.join(run_dir, "run.json")
    atomic_write_json(run_file, run.to_dict())
    if run.artifact_manifest:
        with open(run_file, "rb") as f:
            run.artifact_manifest.files["run.json"] = compute_sha256(f.read())
        all_hashes = json.dumps(run.artifact_manifest.files, sort_keys=True)
        run.artifact_manifest.artifact_hash = compute_sha256(all_hashes.encode())
        manifest_file = os.path.join(run_dir, "manifest.json")
        atomic_write_json(manifest_file, run.artifact_manifest.to_dict())
