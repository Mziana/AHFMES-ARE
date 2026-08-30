"""
AHFMES ARE — Strategy Engine
Converts AlphaHypothesisSpec into strategy_logic callable for backtest.
Uses AlphaGenerator's real logic, not simplified momentum.
"""
from __future__ import annotations
from typing import Callable, Dict, Any
try:
    import polars as pl
except ImportError:
    raise ImportError("polars required: pip install polars")


def spec_to_strategy_logic(spec) -> Callable[[pl.DataFrame], pl.DataFrame]:
    """Convert AlphaHypothesisSpec to a strategy_logic function for backtest engine.

    The returned function takes a DataFrame with OHLC columns and adds a 'signal' column:
      1 = BUY, -1 = SELL, 0 = HOLD
    """
    family = spec.family
    params = spec.parameters
    threshold = spec.signal_threshold

    if family == "MOMENTUM":
        fast = params.get("fast_period", 10)
        slow = params.get("slow_period", 30)
        vel_weight = params.get("velocity_weight", 0.5)

        def momentum_strategy(df: pl.DataFrame) -> pl.DataFrame:
            df = df.with_columns([
                pl.col("price").rolling_mean(fast).alias("_fast_ma"),
                pl.col("price").rolling_mean(slow).alias("_slow_ma"),
                pl.col("price").pct_change(1).alias("_velocity"),
            ])
            df = df.with_columns([
                ((pl.col("_fast_ma") - pl.col("_slow_ma")) / pl.col("_slow_ma")).alias("_crossover"),
            ])
            df = df.with_columns([
                (pl.col("_crossover") + vel_weight * pl.col("_velocity")).alias("_signal_raw"),
            ])
            df = df.with_columns([
                pl.when(pl.col("_signal_raw") > threshold).then(1.0)
                .when(pl.col("_signal_raw") < -threshold).then(-1.0)
                .otherwise(0.0).alias("signal")
            ])
            return df.drop(["_fast_ma", "_slow_ma", "_velocity", "_crossover", "_signal_raw"])

        return momentum_strategy

    elif family == "MEAN_REVERSION":
        zscore_entry = params.get("zscore_entry", 2.0)
        zscore_exit = params.get("zscore_exit", 0.5)
        window = params.get("window", 20)

        def mean_reversion_strategy(df: pl.DataFrame) -> pl.DataFrame:
            df = df.with_columns([
                pl.col("price").rolling_mean(window).alias("_mean"),
                pl.col("price").rolling_std(window).alias("_std"),
            ])
            df = df.with_columns([
                ((pl.col("price") - pl.col("_mean")) / pl.col("_std").clip(lower_bound=0.0001)).alias("_zscore"),
            ])
            df = df.with_columns([
                pl.when(pl.col("_zscore") < -zscore_entry).then(1.0)
                .when(pl.col("_zscore") > zscore_entry).then(-1.0)
                .when(pl.col("_zscore").abs() < zscore_exit).then(0.0)
                .otherwise(pl.col("signal").shift(1).fill_null(0.0)).alias("signal"),
            ])
            return df.drop(["_mean", "_std", "_zscore"])

        return mean_reversion_strategy

    elif family == "ORDERBOOK_IMBALANCE":
        imb_thresh = params.get("imbalance_threshold", 0.3)

        def orderbook_strategy(df: pl.DataFrame) -> pl.DataFrame:
            # Approximate imbalance from OHLC (real orderbook needs L2 data)
            df = df.with_columns([
                ((pl.col("close") - pl.col("low")) / (pl.col("high") - pl.col("low") + 0.0001)).alias("_buy_pressure"),
            ])
            df = df.with_columns([
                (2 * pl.col("_buy_pressure") - 1).alias("_imbalance"),
                pl.col("volume").rolling_mean(10).alias("_avg_vol"),
            ])
            df = df.with_columns([
                pl.when(pl.col("_imbalance") > imb_thresh).then(1.0)
                .when(pl.col("_imbalance") < -imb_thresh).then(-1.0)
                .otherwise(0.0).alias("signal")
            ])
            return df.drop(["_buy_pressure", "_imbalance", "_avg_vol"])

        return orderbook_strategy

    else:
        # Fallback: simple momentum from price
        def fallback_strategy(df: pl.DataFrame) -> pl.DataFrame:
            df = df.with_columns([
                pl.col("price").pct_change(20).alias("_mom"),
            ]).with_columns([
                pl.when(pl.col("_mom") > threshold).then(1.0)
                .when(pl.col("_mom") < -threshold).then(-1.0)
                .otherwise(0.0).alias("signal")
            ])
            return df.drop(["_mom"])
        return fallback_strategy
