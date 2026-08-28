"""
AHFMES ARE — Data Cleansing & Gap-Alignment Engine (DELEGASI_029b, Anti-GIGO)

Provides statistical purification of raw financial market ticks:
- Strict Monotonic Chronology Verification (Anti-Time-Travel)
- Crossed Market Detection (Bid <= Ask)
- Anti-Linear-Interpolation Gap Alignment (Micro-gaps via LOCF, Macro-gaps as Closed Market)
- Toxic Spread & Rollover Spike Neutralization (> 3x MA Spread)
Zero external dependencies except Polars (stdlib + polars only).
"""

from __future__ import annotations

import math
from typing import Optional

try:
    import polars as pl
except ImportError:
    raise ImportError("Pustaka 'polars' diperlukan untuk data pipeline. Install: pip install polars")


class DataChronologyError(Exception):
    """Dilempar saat data timestamp tidak monotonik naik (waktu mundur)."""


class CrossedMarketError(Exception):
    """Dilempar saat bid > ask terdeteksi (data feed cacat)."""


class DataPurifier:
    """
    Purifies raw market tick data without statistical bias or fictitious interpolation.
    """

    def purify_tick_data(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Purifies tick dataset, validating invariants and tagging toxic spreads / market closures.
        """
        if df.is_empty():
            return df

        # 1. Normalize Column Names & Ensure Minimum Required Fields
        cols = df.columns
        if "timestamp" not in cols:
            raise ValueError("Dataset must contain a 'timestamp' column")

        # Synthesize bid/ask from price if only price is provided
        if "bid" not in cols or "ask" not in cols:
            if "price" in cols:
                df = df.with_columns([
                    (pl.col("price") - 0.5).alias("bid"),
                    (pl.col("price") + 0.5).alias("ask"),
                ])
            else:
                raise ValueError("Dataset must contain 'bid'/'ask' or 'price' columns")

        if "volume" not in cols:
            df = df.with_columns(pl.lit(1.0).alias("volume"))

        if "price" not in cols:
            df = df.with_columns(((pl.col("bid") + pl.col("ask")) / 2.0).alias("price"))

        # 2. Strict Monotonic Chronology Validation
        time_diffs = df["timestamp"].diff().to_list()
        # First diff is None; all subsequent must be >= 0
        for i, diff in enumerate(time_diffs[1:], start=1):
            if diff is not None and diff < 0:
                raise DataChronologyError(
                    f"Timestamp chronology violation at index {i}: "
                    f"timestamp[{i}]={df['timestamp'][i]} < timestamp[{i-1}]={df['timestamp'][i-1]}"
                )

        # 3. Crossed Market Validation (Bid <= Ask)
        crossed_mask = df["bid"] > df["ask"]
        if crossed_mask.any():
            crossed_idx = crossed_mask.to_list().index(True)
            raise CrossedMarketError(
                f"Crossed market anomaly detected at index {crossed_idx}: "
                f"bid ({df['bid'][crossed_idx]}) > ask ({df['ask'][crossed_idx]})"
            )

        # 4. Spread & Toxic Spread Calculation
        df = df.with_columns([
            (pl.col("ask") - pl.col("bid")).alias("spread")
        ])

        try:
            spread_ma_expr = pl.col("spread").rolling_mean(window_size=100, min_samples=1).alias("spread_ma")
        except TypeError:
            spread_ma_expr = pl.col("spread").rolling_mean(window_size=100, min_periods=1).alias("spread_ma")

        df = df.with_columns([spread_ma_expr])

        # Toxic spread if spread > 3.0 * spread_ma
        df = df.with_columns([
            (pl.col("spread") > (3.0 * pl.col("spread_ma"))).alias("is_toxic_spread")
        ])

        # 5. Gap Detection & Market Closed Tagging (Macro-gaps >= 1 hour = 3600 seconds)
        df = df.with_columns([
            pl.col("timestamp").diff().fill_null(0.0).alias("time_diff")
        ]).with_columns([
            (pl.col("time_diff") >= 3600.0).alias("is_market_closed")
        ])

        # 6. Micro-gaps Forward Fill (LOCF / Last Observation Carried Forward)
        # Note: Polars forward fill on bid/ask preserves last known market price without linear bias
        df = df.with_columns([
            pl.col("bid").forward_fill(),
            pl.col("ask").forward_fill(),
            pl.col("price").forward_fill(),
        ])

        return df.select([
            "timestamp",
            "bid",
            "ask",
            "price",
            "volume",
            "spread",
            "is_toxic_spread",
            "is_market_closed",
        ])