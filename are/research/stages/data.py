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
from are.data_pipeline import DataPurifier


class DataStage:
    """Validate data quality and freeze."""

    def run(self, run: BacktestRun, df: pl.DataFrame, manifest: DatasetManifest,
            qualification_policy: str = "STRICT") -> StageResult:
        t0 = time.time()
        gate = DataQualityGate.validate(df)
        run.quality_report = gate

        if gate["gate"] == "FAIL":
            return StageResult(
                stage="data", status=RunStage.FAILED,
                started_at=t0, completed_at=time.time(),
                data=gate, error=f"Data quality gate FAILED: {gate['failed_count']} failures",
            )

        # P1-5: research qualification — synthetic bid/ask/volume membuat experiment
        # INVALID kecuali eksperimen eksplisit memilih BAR_APPROXIMATION.
        # Jangan biarkan microstructure sintetis masuk jalur yang sama dengan execution
        # historical tanpa pengakuan eksplisit.
        try:
            purifier = DataPurifier()
            purifier.purify_tick_data(df)
            report = purifier.quality_report
        except Exception:
            report = None
        synthetic_rows = 0
        if report is not None:
            synthetic_rows = int(
                (report.synthetic_bid_ask_rows or 0)
                + (report.synthetic_volume_rows or 0)
                + (report.synthetic_price_rows or 0)
            )
        if synthetic_rows > 0 and qualification_policy != "BAR_APPROXIMATION":
            return StageResult(
                stage="data", status=RunStage.FAILED,
                started_at=t0, completed_at=time.time(),
                data={"gate": gate["gate"], "synthetic_rows": synthetic_rows},
                error=(
                    f"DATA_QUALIFICATION_INVALID: {synthetic_rows} bar dengan bid/ask/volume "
                    f"SINTETIS (bukan data market asli). Policy STRICT menolak microstructure "
                    f"sintetis untuk research qualification. Bila eksperimen memang berbasis "
                    f"bar-approximation, set qualification_policy='BAR_APPROXIMATION' secara "
                    f"eksplisit di ExperimentConfig."
                ),
            )

        note = ""
        if synthetic_rows > 0:
            note = f"BAR_APPROXIMATION: {synthetic_rows} bar microstructure sintetis dilabeli (bukan historical)"

        return StageResult(
            stage="data", status=RunStage.PASSED,
            started_at=t0, completed_at=time.time(),
            data={"rows": len(df), "gate": gate["gate"], "warnings": gate["warn_count"], "qualification_note": note},
        )
