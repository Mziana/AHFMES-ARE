"""
AHFMES ARE — Baseline Strategies & Parameter Stability Analysis

Benchmark strategies for Information Value Assessment (P1-1) and
parameter sensitivity analysis (P1-2).
Extracted from backtest.py for single-responsibility separation.

Zero external dependencies except Polars (stdlib + polars only).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

try:
    import polars as pl
except ImportError:
    raise ImportError("Pustaka 'polars' diperlukan untuk modul baselines. Install: pip install polars")

if TYPE_CHECKING:
    from are.backtest import IsolatedBacktestEngine


# =============================================================================
# BASELINE SUITE — Information Value Assessment (P1-1)
# =============================================================================

def baseline_buy_and_hold(df: pl.DataFrame) -> pl.DataFrame:
    """Always long from bar 0 — the simplest possible benchmark."""
    return df.with_columns(pl.lit(1.0).alias("signal"))


def baseline_always_flat(df: pl.DataFrame) -> pl.DataFrame:
    """Never trade — tests whether any alpha exists above zero."""
    return df.with_columns(pl.lit(0.0).alias("signal"))


def baseline_naive_long(df: pl.DataFrame) -> pl.DataFrame:
    """Long if previous return was positive (momentum 1-bar)."""
    return df.with_columns(
        pl.when(pl.col("price").pct_change().shift(1) > 0).then(1.0)
        .otherwise(0.0).alias("signal")
    )


def baseline_naive_short(df: pl.DataFrame) -> pl.DataFrame:
    """Short if previous return was negative (mean-reversion 1-bar)."""
    return df.with_columns(
        pl.when(pl.col("price").pct_change().shift(1) < 0).then(-1.0)
        .otherwise(0.0).alias("signal")
    )


def baseline_random_permutation(df: pl.DataFrame, seed: int = 42) -> pl.DataFrame:
    """Random signal — tests if strategy beats noise."""
    import random as _rng
    rng = _rng.Random(seed)
    n = len(df)
    signals = [rng.choice([-1.0, 0.0, 1.0]) for _ in range(n)]
    return df.with_columns(pl.Series("signal", signals))


BASELINE_STRATEGIES = {
    "buy_and_hold": baseline_buy_and_hold,
    "always_flat": baseline_always_flat,
    "naive_long": baseline_naive_long,
    "naive_short": baseline_naive_short,
    "random_permutation": baseline_random_permutation,
}


def run_baseline_comparison(
    engine: "IsolatedBacktestEngine",
    historical_data: pl.DataFrame,
    strategy_logic: Optional[Callable[[pl.DataFrame], pl.DataFrame]] = None,
    strategy_name: str = "strategy",
    initial_capital: float = 10000.0,
    timeframe_seconds: float = 3600.0,
    spread_pct: float = 0.0001,
    slippage_pct: float = 0.00005,
    commission_pct: float = 0.00005,
) -> Dict[str, Any]:
    """
    Runs strategy against all baselines. Returns comparison dict.
    Strategy has alpha if it beats all baselines on Sharpe AND return.
    """
    results = {}

    # Run baselines
    for name, bl_logic in BASELINE_STRATEGIES.items():
        try:
            r = engine.run_backtest(
                strategy_logic=bl_logic,
                historical_data=historical_data,
                initial_capital=initial_capital,
                timeframe_seconds=timeframe_seconds,
                spread_pct=spread_pct,
                slippage_pct=slippage_pct,
                commission_pct=commission_pct,
            )
            results[name] = {
                "sharpe": r.metrics.get("sharpe_ratio", 0.0),
                "return_pct": r.metrics.get("total_return_pct", 0.0),
                "max_dd_pct": r.metrics.get("max_drawdown_pct", 0.0),
                "trades": r.metrics.get("total_trades", 0),
            }
        except Exception as e:
            results[name] = {"error": str(e)}

    # Run actual strategy
    if strategy_logic is not None:
        try:
            r = engine.run_backtest(
                strategy_logic=strategy_logic,
                historical_data=historical_data,
                initial_capital=initial_capital,
                timeframe_seconds=timeframe_seconds,
                spread_pct=spread_pct,
                slippage_pct=slippage_pct,
                commission_pct=commission_pct,
            )
            results[strategy_name] = {
                "sharpe": r.metrics.get("sharpe_ratio", 0.0),
                "return_pct": r.metrics.get("total_return_pct", 0.0),
                "max_dd_pct": r.metrics.get("max_drawdown_pct", 0.0),
                "trades": r.metrics.get("total_trades", 0),
            }
        except Exception as e:
            results[strategy_name] = {"error": str(e)}

    # Assessment
    if strategy_name in results and "error" not in results[strategy_name]:
        strat = results[strategy_name]
        beats_all_sharpe = all(
            v.get("sharpe", -999) < strat["sharpe"]
            for k, v in results.items()
            if k != strategy_name and "error" not in v
        )
        beats_all_return = all(
            v.get("return_pct", -999) < strat["return_pct"]
            for k, v in results.items()
            if k != strategy_name and "error" not in v
        )
        results["_assessment"] = {
            "has_alpha": beats_all_sharpe and beats_all_return,
            "beats_all_sharpe": beats_all_sharpe,
            "beats_all_return": beats_all_return,
            "strategy_sharpe": strat["sharpe"],
            "best_baseline_sharpe": max(
                (v.get("sharpe", -999) for k, v in results.items()
                 if k != strategy_name and "error" not in v),
                default=0.0
            ),
        }

    return results


# =============================================================================
# PARAMETER STABILITY ANALYSIS (P1-2)
# =============================================================================

def parameter_stability_analysis(
    engine: "IsolatedBacktestEngine",
    historical_data: pl.DataFrame,
    base_strategy: Callable[[pl.DataFrame], pl.DataFrame],
    param_name: str,
    param_values: List[float],
    param_mutator: Callable[[pl.DataFrame, float], pl.DataFrame],
    initial_capital: float = 10000.0,
    timeframe_seconds: float = 3600.0,
) -> Dict[str, Any]:
    """
    Tests parameter stability: does performance degrade gracefully near the winner?

    param_mutator: function(df, param_value) -> df_with_signal
    Returns performance surface + stability assessment.
    """
    surface = []
    for val in param_values:
        try:
            r = engine.run_backtest(
                strategy_logic=lambda df, v=val: param_mutator(df, v),
                historical_data=historical_data,
                initial_capital=initial_capital,
                timeframe_seconds=timeframe_seconds,
            )
            surface.append({
                "param_value": val,
                "sharpe": r.metrics.get("sharpe_ratio", 0.0),
                "return_pct": r.metrics.get("total_return_pct", 0.0),
                "max_dd_pct": r.metrics.get("max_drawdown_pct", 0.0),
                "trades": r.metrics.get("total_trades", 0),
            })
        except Exception as e:
            surface.append({"param_value": val, "error": str(e)})

    valid = [s for s in surface if "error" not in s]
    if len(valid) < 3:
        return {"surface": surface, "stability": "INSUFFICIENT_DATA", "verdict": "NEED_MORE_POINTS"}

    sharpes = [s["sharpe"] for s in valid]
    best_idx = sharpes.index(max(sharpes))
    best_val = valid[best_idx]["param_value"]
    best_sharpe = max(sharpes)

    # Check neighborhood stability: ±1, ±2 indices from best
    neighbors_sharpes = []
    for offset in [-2, -1, 1, 2]:
        idx = best_idx + offset
        if 0 <= idx < len(valid):
            neighbors_sharpes.append(valid[idx]["sharpe"])

    if neighbors_sharpes:
        mean_neighbor = sum(neighbors_sharpes) / len(neighbors_sharpes)
        stability_ratio = mean_neighbor / best_sharpe if best_sharpe > 0 else 0.0
    else:
        stability_ratio = 0.0

    # Assessment
    if stability_ratio >= 0.7:
        stability = "ROBUST"
        verdict = "PARAMETER_IS_STABLE"
    elif stability_ratio >= 0.4:
        stability = "MARGINAL"
        verdict = "PARAMETER_SENSITIVE_BUT_USEABLE"
    else:
        stability = "FRAGILE"
        verdict = "PARAMETER_PEAK_IS_SUSPICIOUS"

    return {
        "param_name": param_name,
        "surface": surface,
        "best_param": best_val,
        "best_sharpe": round(best_sharpe, 4),
        "stability_ratio": round(stability_ratio, 4),
        "stability": stability,
        "verdict": verdict,
    }
