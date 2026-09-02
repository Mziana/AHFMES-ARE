"""
AHFMES ARE — Holdout Setup Stage

Creates 3-layer split and locks holdout for the experiment.
"""

from __future__ import annotations

from typing import Tuple

try:
    import polars as pl
except ImportError:
    raise ImportError("Polars required")

from are.research.types import BacktestRun
from are.research.dataset_registry import DatasetManifest
from are.research.integrity import HoldoutManager


class HoldoutSetupStage:
    """Create 3-layer split and lock holdout."""

    def run(self, run: BacktestRun, manifest: DatasetManifest,
            df: pl.DataFrame, mgr: HoldoutManager) -> Tuple[str, object]:
        split = mgr.create_split(manifest.dataset_id, df)
        split = mgr.lock_holdout(split.split_id)
        return split.split_id, split
