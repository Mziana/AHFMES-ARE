"""
AHFMES ARE — Data Cleansing & Gap-Alignment Engine (DELEGASI_029b, Anti-GIGO)

Provides statistical purification of raw financial market ticks:
- Strict Monotonic Chronology Verification (Anti-Time-Travel)
- Crossed Market Detection (Bid <= Ask)
- Anti-Linear-Interpolation Gap Alignment (Micro-gaps via LOCF, Macro-gaps as Closed Market)
- Toxic Spread & Rollover Spike Neutralization (> 3x MA Spread)
- Data Quality Report for full purification auditability
Zero external dependencies except Polars (stdlib + polars only).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

try:
    import polars as pl
except ImportError:
    raise ImportError("Pustaka 'polars' diperlukan untuk data pipeline. Install: pip install polars")


class DataChronologyError(Exception):
    """Dilempar saat data timestamp tidak monotonik naik (waktu mundur)."""


class CrossedMarketError(Exception):
    """Dilempar saat bid > ask terdeteksi (data feed cacat)."""


@dataclass(frozen=True)
class DataQualityReport:
    """
    Immutable audit trail for data purification process.
    Answers: how many bars raw, modified, removed, synthetic, flagged.
    """
    raw_rows: int
    final_rows: int
    removed_rows: int = 0
    forward_filled_rows: int = 0
    synthetic_bid_ask_rows: int = 0
    synthetic_volume_rows: int = 0
    synthetic_price_rows: int = 0
    toxic_spread_rows: int = 0
    market_closed_rows: int = 0
    duplicate_timestamp_rows: int = 0
    crossed_market_rows: int = 0
    symbol: str = "UNKNOWN"
    timeframe_seconds: float = 0.0
    data_start_ts: float = 0.0
    data_end_ts: float = 0.0

    def to_dict(self) -> dict:
        return {
            "raw_rows": self.raw_rows,
            "final_rows": self.final_rows,
            "removed_rows": self.removed_rows,
            "forward_filled_rows": self.forward_filled_rows,
            "synthetic_bid_ask_rows": self.synthetic_bid_ask_rows,
            "synthetic_volume_rows": self.synthetic_volume_rows,
            "synthetic_price_rows": self.synthetic_price_rows,
            "toxic_spread_rows": self.toxic_spread_rows,
            "market_closed_rows": self.market_closed_rows,
            "duplicate_timestamp_rows": self.duplicate_timestamp_rows,
            "crossed_market_rows": self.crossed_market_rows,
            "symbol": self.symbol,
            "timeframe_seconds": self.timeframe_seconds,
            "data_start_ts": self.data_start_ts,
            "data_end_ts": self.data_end_ts,
        }


class DataPurifier:
    """
    Purifies raw market tick data without statistical bias or fictitious interpolation.
    After each purify_tick_data() call, access quality_report for the purification audit trail.
    """

    def __init__(self):
        self.quality_report: Optional[DataQualityReport] = None

    def purify_tick_data(self, df: pl.DataFrame, symbol: str = "UNKNOWN", timeframe_seconds: float = 0.0) -> pl.DataFrame:
        """
        Purifies tick dataset, validating invariants and tagging toxic spreads / market closures.
        Populates self.quality_report after purification.
        """
        if df.is_empty():
            self.quality_report = DataQualityReport(raw_rows=0, final_rows=0)
            return df

        raw_rows = len(df)
        synthetic_bid_ask = 0
        synthetic_volume = 0
        synthetic_price = 0
        forward_filled = 0
        removed = 0

        # 1. Normalize Column Names & Ensure Minimum Required Fields
        cols = df.columns
        if "timestamp" not in cols:
            raise ValueError("Dataset must contain a 'timestamp' column")

        # Synthesize bid/ask from price if only price is provided
        if "bid" not in cols or "ask" not in cols:
            if "price" in cols:
                synthetic_bid_ask = len(df)
                df = df.with_columns([
                    (pl.col("price") - 0.5).alias("bid"),
                    (pl.col("price") + 0.5).alias("ask"),
                ])
            else:
                raise ValueError("Dataset must contain 'bid'/'ask' or 'price' columns")

        if "volume" not in cols:
            synthetic_volume = len(df)
            df = df.with_columns(pl.lit(1.0).alias("volume"))

        if "price" not in cols:
            synthetic_price = len(df)
            df = df.with_columns(((pl.col("bid") + pl.col("ask")) / 2.0).alias("price"))

        # Count forward fills (micro-gaps) before applying
        bid_list = df["bid"].to_list()
        ask_list = df["ask"].to_list()
        price_list = df["price"].to_list()
        for i in range(1, len(bid_list)):
            if bid_list[i] is None or ask_list[i] is None or price_list[i] is None:
                forward_filled += 1

        # Count duplicate timestamps
        ts_list = df["timestamp"].to_list()
        duplicate_timestamps = 0
        seen_ts = set()
        for ts in ts_list:
            if ts in seen_ts:
                duplicate_timestamps += 1
            seen_ts.add(ts)

        # 2. Strict Monotonic Chronology Validation
        time_diffs = df["timestamp"].diff().to_list()
        for i, diff in enumerate(time_diffs[1:], start=1):
            if diff is not None and diff < 0:
                raise DataChronologyError(
                    f"Timestamp chronology violation at index {i}: "
                    f"timestamp[{i}]={df['timestamp'][i]} < timestamp[{i-1}]={df['timestamp'][i-1]}"
                )

        # 3. Crossed Market Validation (Bid <= Ask)
        crossed_mask = df["bid"] > df["ask"]
        crossed_count = int(crossed_mask.sum()) if crossed_mask.any() else 0
        if crossed_count > 0:
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

        toxic_count = int(df["is_toxic_spread"].sum())

        # 5. Gap Detection & Market Closed Tagging (Macro-gaps >= 1 hour = 3600 seconds)
        df = df.with_columns([
            pl.col("timestamp").diff().fill_null(0.0).alias("time_diff")
        ]).with_columns([
            (pl.col("time_diff") >= 3600.0).alias("is_market_closed")
        ])

        closed_count = int(df["is_market_closed"].sum())

        # 6. Micro-gaps Forward Fill (LOCF / Last Observation Carried Forward)
        df = df.with_columns([
            pl.col("bid").forward_fill(),
            pl.col("ask").forward_fill(),
            pl.col("price").forward_fill(),
        ])

        # Build quality report
        ts_arr = df["timestamp"].to_list()
        self.quality_report = DataQualityReport(
            raw_rows=raw_rows,
            final_rows=len(df),
            removed_rows=removed,
            forward_filled_rows=forward_filled,
            synthetic_bid_ask_rows=synthetic_bid_ask,
            synthetic_volume_rows=synthetic_volume,
            synthetic_price_rows=synthetic_price,
            toxic_spread_rows=toxic_count,
            market_closed_rows=closed_count,
            duplicate_timestamp_rows=duplicate_timestamps,
            crossed_market_rows=crossed_count,
            symbol=symbol,
            timeframe_seconds=timeframe_seconds,
            data_start_ts=float(ts_arr[0]) if ts_arr else 0.0,
            data_end_ts=float(ts_arr[-1]) if ts_arr else 0.0,
        )

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
