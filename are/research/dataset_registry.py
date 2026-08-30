"""
AHFMES ARE -- Research Data Plane (Slice BT-01)

DatasetRegistry: Freeze, track, and verify datasets for reproducible research.
Raw data and purified data are both immutable once frozen.
Each dataset gets a unique ID, manifest, and quality report.

Zero external dependencies except Polars + stdlib.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

try:
    import polars as pl
except ImportError:
    raise ImportError("Polars required: pip install polars")

from are.data_pipeline import DataPurifier, DataQualityReport
from are.hasher import compute_sha256


@dataclass(frozen=True)
class DatasetManifest:
    """Immutable identity card for a frozen dataset."""
    dataset_id: str
    symbol: str
    venue: str
    timezone: str
    timeframe_seconds: float
    data_source: str  # 'mt5_parquet', 'csv', 'api'
    start_ts: float
    end_ts: float
    raw_rows: int
    purified_rows: int
    raw_hash: str
    purified_hash: str
    quality_report: Dict[str, Any]
    created_at: float
    frozen: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DatasetRegistry:
    """
    Central registry for research datasets.
    Ensures every backtest uses a frozen, reproducible dataset.
    """

    REGISTRY_DIR = "data/datasets"

    def __init__(self):
        os.makedirs(self.REGISTRY_DIR, exist_ok=True)

    def register_dataset(
        self,
        symbol: str,
        df: pl.DataFrame,
        venue: str = "MT5",
        timezone: str = "UTC",
        timeframe_seconds: float = 3600.0,
        data_source: str = "mt5_parquet",
    ) -> DatasetManifest:
        """
        Register and freeze a dataset. Returns immutable manifest.
        Raw hash computed before purification, purified hash after.
        """
        if df.is_empty():
            raise ValueError("Cannot register empty dataset")

        # Generate deterministic dataset ID
        ts_list = df["timestamp"].to_list() if "timestamp" in df.columns else []
        pr_list = df["price"].to_list() if "price" in df.columns else []
        vol_list = df["volume"].to_list() if "volume" in df.columns else [0.0] * len(ts_list)

        # Compute raw hash
        raw_bytes = (
            b"V1"
            + symbol.encode()
            + struct.pack(">d", timeframe_seconds)
            + b"".join(struct.pack(">d", float(x)) for x in ts_list)
            + b"".join(struct.pack(">d", float(x)) for x in pr_list)
            + b"".join(struct.pack(">d", float(x)) for x in vol_list)
        )
        raw_hash = compute_sha256(raw_bytes)

        # Purify and compute purified hash
        purifier = DataPurifier()
        purified_df = purifier.purify_tick_data(df, symbol=symbol, timeframe_seconds=timeframe_seconds)
        quality = purifier.quality_report.to_dict() if purifier.quality_report else {}

        pts = purified_df["timestamp"].to_list() if "timestamp" in purified_df.columns else []
        ppr = purified_df["price"].to_list() if "price" in purified_df.columns else []
        pvol = purified_df["volume"].to_list() if "volume" in purified_df.columns else [0.0] * len(pts)
        purified_bytes = (
            b"V1"
            + b"".join(struct.pack(">d", float(x)) for x in pts)
            + b"".join(struct.pack(">d", float(x)) for x in ppr)
            + b"".join(struct.pack(">d", float(x)) for x in pvol)
        )
        purified_hash = compute_sha256(purified_bytes)

        dataset_id = f"DS-{symbol}-{int(timeframe_seconds)}-{raw_hash[:12]}"
        start_ts = float(ts_list[0]) if ts_list else 0.0
        end_ts = float(ts_list[-1]) if ts_list else 0.0

        manifest = DatasetManifest(
            dataset_id=dataset_id,
            symbol=symbol,
            venue=venue,
            timezone=timezone,
            timeframe_seconds=timeframe_seconds,
            data_source=data_source,
            start_ts=start_ts,
            end_ts=end_ts,
            raw_rows=len(df),
            purified_rows=len(purified_df),
            raw_hash=raw_hash,
            purified_hash=purified_hash,
            quality_report=quality,
            created_at=time.time(),
            frozen=True,
        )

        # Save manifest + raw + purified parquet
        ds_dir = os.path.join(self.REGISTRY_DIR, dataset_id)
        os.makedirs(ds_dir, exist_ok=True)
        with open(os.path.join(ds_dir, "manifest.json"), "w") as f:
            json.dump(manifest.to_dict(), f, indent=2)
        with open(os.path.join(ds_dir, "quality_report.json"), "w") as f:
            json.dump(quality, f, indent=2)
        df.write_parquet(os.path.join(ds_dir, "raw.parquet"))
        purified_df.write_parquet(os.path.join(ds_dir, "purified.parquet"))

        return manifest

    def load_dataset(self, dataset_id: str) -> Tuple[pl.DataFrame, DatasetManifest]:
        """Load a frozen dataset and its manifest."""
        ds_dir = os.path.join(self.REGISTRY_DIR, dataset_id)
        manifest_path = os.path.join(ds_dir, "manifest.json")
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Dataset {dataset_id} not found")

        with open(manifest_path) as f:
            data = json.load(f)
        manifest = DatasetManifest(**data)

        purified_path = os.path.join(ds_dir, "purified.parquet")
        if not os.path.exists(purified_path):
            raise FileNotFoundError(f"Purified data not found for {dataset_id}")

        df = pl.read_parquet(purified_path)
        return df, manifest

    def load_raw(self, dataset_id: str) -> pl.DataFrame:
        """Load raw (pre-purification) data for inspection."""
        raw_path = os.path.join(self.REGISTRY_DIR, dataset_id, "raw.parquet")
        if not os.path.exists(raw_path):
            raise FileNotFoundError(f"Raw data not found for {dataset_id}")
        return pl.read_parquet(raw_path)

    def list_datasets(self) -> List[DatasetManifest]:
        """List all registered datasets."""
        manifests = []
        if not os.path.exists(self.REGISTRY_DIR):
            return manifests
        for name in os.listdir(self.REGISTRY_DIR):
            mp = os.path.join(self.REGISTRY_DIR, name, "manifest.json")
            if os.path.exists(mp):
                with open(mp) as f:
                    data = json.load(f)
                manifests.append(DatasetManifest(**data))
        return manifests

    def verify_integrity(self, dataset_id: str) -> Dict[str, Any]:
        """Verify a dataset hasn't been tampered with."""
        ds_dir = os.path.join(self.REGISTRY_DIR, dataset_id)
        manifest_path = os.path.join(ds_dir, "manifest.json")
        with open(manifest_path) as f:
            data = json.load(f)
        manifest = DatasetManifest(**data)

        # Recompute purified hash
        df = pl.read_parquet(os.path.join(ds_dir, "purified.parquet"))
        pts = df["timestamp"].to_list()
        ppr = df["price"].to_list()
        pvol = df["volume"].to_list() if "volume" in df.columns else [0.0] * len(pts)
        purified_bytes = (
            b"V1"
            + b"".join(struct.pack(">d", float(x)) for x in pts)
            + b"".join(struct.pack(">d", float(x)) for x in ppr)
            + b"".join(struct.pack(">d", float(x)) for x in pvol)
        )
        current_hash = compute_sha256(purified_bytes)

        return {
            "dataset_id": dataset_id,
            "manifest_hash": manifest.purified_hash,
            "current_hash": current_hash,
            "matches": manifest.purified_hash == current_hash,
            "frozen": manifest.frozen,
        }


class DataQualityGate:
    """
    Pre-backtest data validation gate.
    PASS = data is valid for research.
    FAIL = data has issues that must be resolved.
    """

    @staticmethod
    def validate(df: pl.DataFrame, manifest: Optional[DatasetManifest] = None) -> Dict[str, Any]:
        """Run all validation checks. Returns gate result."""
        checks = []

        # Structural checks
        if "timestamp" not in df.columns:
            checks.append({"check": "timestamp_column", "status": "FAIL", "detail": "Missing timestamp"})
        elif df["timestamp"].is_null().any():
            null_count = int(df["timestamp"].is_null().sum())
            checks.append({"check": "timestamp_null", "status": "FAIL", "detail": f"{null_count} null timestamps"})
        else:
            checks.append({"check": "timestamp_column", "status": "PASS", "detail": "OK"})

        # Price checks
        if "price" in df.columns:
            neg = int((df["price"] < 0).sum())
            zero = int((df["price"] == 0).sum())
            if neg > 0:
                checks.append({"check": "negative_price", "status": "FAIL", "detail": f"{neg} negative prices"})
            elif zero > 0:
                checks.append({"check": "zero_price", "status": "FAIL", "detail": f"{zero} zero prices"})
            else:
                checks.append({"check": "price_sanity", "status": "PASS", "detail": "OK"})

            # Extreme returns
            returns = df["price"].pct_change().drop_nulls()
            if len(returns) > 0:
                extreme = int((returns.abs() > 0.50).sum())
                if extreme > 0:
                    checks.append({"check": "extreme_returns", "status": "WARN", "detail": f"{extreme} bars with >50% return"})
                else:
                    checks.append({"check": "extreme_returns", "status": "PASS", "detail": "OK"})
        else:
            checks.append({"check": "price_column", "status": "FAIL", "detail": "Missing price"})

        # Duplicate timestamps
        if "timestamp" in df.columns:
            dupes = int(df["timestamp"].is_duplicated().sum())
            if dupes > 0:
                checks.append({"check": "duplicate_timestamps", "status": "WARN", "detail": f"{dupes} duplicates"})
            else:
                checks.append({"check": "duplicate_timestamps", "status": "PASS", "detail": "OK"})

        # Minimum rows
        if len(df) < 100:
            checks.append({"check": "minimum_rows", "status": "FAIL", "detail": f"Only {len(df)} rows (need ≥100)"})
        else:
            checks.append({"check": "minimum_rows", "status": "PASS", "detail": f"{len(df)} rows"})

        # Toxic spread / market closed
        if "is_toxic_spread" in df.columns:
            toxic_pct = float(df["is_toxic_spread"].mean()) * 100
            if toxic_pct > 20:
                checks.append({"check": "toxic_spread", "status": "WARN", "detail": f"{toxic_pct:.1f}% toxic"})
            else:
                checks.append({"check": "toxic_spread", "status": "PASS", "detail": f"{toxic_pct:.1f}%"})

        if "is_market_closed" in df.columns:
            closed_pct = float(df["is_market_closed"].mean()) * 100
            if closed_pct > 50:
                checks.append({"check": "market_closed", "status": "WARN", "detail": f"{closed_pct:.1f}% closed"})
            else:
                checks.append({"check": "market_closed", "status": "PASS", "detail": f"{closed_pct:.1f}%"})

        failed = [c for c in checks if c["status"] == "FAIL"]
        warned = [c for c in checks if c["status"] == "WARN"]

        gate = "PASS" if not failed else "FAIL"
        if not failed and warned:
            gate = "PASS_WITH_WARNINGS"

        return {
            "gate": gate,
            "checks": checks,
            "failed_count": len(failed),
            "warn_count": len(warned),
        }
