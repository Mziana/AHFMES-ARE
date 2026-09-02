"""
AHFMES ARE — Data Quality Validation Stage

Validates data quality and freezes dataset for the experiment.
"""

from __future__ import annotations

import time
from typing import Any

try:
    import polars as pl
except ImportError:
    raise ImportError("Polars required")

from are.research.types import RunStage, StageResult, BacktestRun
from are.research.dataset_registry import DatasetManifest, DataQualityGate


class DataStage:
    """Validate data quality and freeze."""

    def run(self, run: BacktestRun, df: pl.DataFrame, manifest: DatasetManifest) -> StageResult:
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
