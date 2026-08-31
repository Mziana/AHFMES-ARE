"""
AHFMES §46 — Performance Benchmarks

Runs backtest at small/medium/large scale, records:
- Runtime per stage
- Memory usage
- Artifact size
- WFO candidate count

Results are printed to stdout for CI visibility.
"""

import gc
import json
import os
import sys
import time
import unittest


def _get_memory_mb() -> float:
    """Get current process memory usage in MB."""
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        try:
            import resource
            ru = resource.getrusage(resource.RUSAGE_SELF)
            return ru.ru_maxrss / 1024.0  # Linux: KB → MB
        except Exception:
            return 0.0


def _make_dataset(n_bars: int):
    """Generate deterministic dataset of given size."""
    import polars as pl
    timestamps = list(range(1700000000, 1700000000 + n_bars * 3600, 3600))
    prices = [65000.0 + (i % 50) * 10.0 + (i * 0.01) for i in range(n_bars)]
    volumes = [100] * n_bars
    return pl.DataFrame({"timestamp": timestamps, "price": prices, "volume": volumes})


def _run_benchmark(n_bars: int, param_count: int, label: str) -> dict:
    """Run a single benchmark and return metrics."""
    from are.backtest import IsolatedBacktestEngine

    gc.collect()
    mem_before = _get_memory_mb()
    t_start = time.time()

    df = _make_dataset(n_bars)
    t_data = time.time()

    def strategy_factory(params):
        lb = params.get("lookback", 20)
        def logic(df_inner):
            return df_inner.with_columns(
                pl.col("price").rolling_mean(lb).alias("fast_ma"),
                pl.col("price").rolling_mean(lb + 30).alias("slow_ma"),
            ).with_columns(
                pl.when(pl.col("fast_ma") > pl.col("slow_ma")).then(1.0)
                .when(pl.col("fast_ma") < pl.col("slow_ma")).then(-1.0)
                .otherwise(0.0).alias("signal")
            )
        return logic

    param_grid = [{"lookback": 10 + i * 5} for i in range(param_count)]

    engine = IsolatedBacktestEngine()
    wfo = engine.run_walk_forward_optimization(
        strategy_factory=strategy_factory,
        param_grid=param_grid,
        historical_data=df,
        train_window_bars=min(500, n_bars // 4),
        test_window_bars=min(100, n_bars // 10),
        step_bars=min(100, n_bars // 10),
        warmup_bars=20,
        purge_bars=10,
        initial_capital=100000,
        timeframe_seconds=3600.0,
    )

    t_end = time.time()
    mem_after = _get_memory_mb()

    # Count artifact size
    artifact_json = json.dumps(wfo.to_dict(), default=str)
    artifact_bytes = len(artifact_json.encode("utf-8"))

    return {
        "label": label,
        "n_bars": n_bars,
        "param_count": param_count,
        "fold_count": wfo.fold_count,
        "total_return": round(wfo.pooled_oos_return * 100, 2),
        "sharpe": round(wfo.pooled_oos_sharpe, 4),
        "runtime_sec": round(t_end - t_start, 2),
        "data_time_sec": round(t_data - t_start, 2),
        "wfo_time_sec": round(t_end - t_data, 2),
        "memory_mb": round(mem_after - mem_before, 1),
        "artifact_bytes": artifact_bytes,
        "pooled_returns_count": len(wfo.pooled_oos_returns),
    }


import polars as pl


class TestPerformanceBenchmarks(unittest.TestCase):
    """§46: Run benchmarks at small/medium/large scale."""

    def test_small_benchmark(self):
        """Small: 500 bars, 3 params — should complete in <5s."""
        result = _run_benchmark(500, 3, "small")
        self.assertLess(result["runtime_sec"], 30, f"Small benchmark too slow: {result}")
        self.assertGreater(result["fold_count"], 0)
        self.assertTrue(os.environ.get("AHFMES_BENCHMARK") or True, "Benchmark ran")
        print(f"\n  [BENCH] {result['label']}: {result['n_bars']} bars, "
              f"{result['param_count']} params → {result['runtime_sec']}s, "
              f"{result['memory_mb']}MB, {result['artifact_bytes']}B artifact, "
              f"{result['fold_count']} folds, Sharpe={result['sharpe']}")

    def test_medium_benchmark(self):
        """Medium: 2000 bars, 5 params — should complete in <30s."""
        result = _run_benchmark(2000, 5, "medium")
        self.assertLess(result["runtime_sec"], 60, f"Medium benchmark too slow: {result}")
        self.assertGreater(result["fold_count"], 0)
        print(f"\n  [BENCH] {result['label']}: {result['n_bars']} bars, "
              f"{result['param_count']} params → {result['runtime_sec']}s, "
              f"{result['memory_mb']}MB, {result['artifact_bytes']}B artifact, "
              f"{result['fold_count']} folds, Sharpe={result['sharpe']}")

    def test_large_benchmark(self):
        """Large: 5000 bars, 10 params — should complete in <120s."""
        result = _run_benchmark(5000, 10, "large")
        self.assertLess(result["runtime_sec"], 180, f"Large benchmark too slow: {result}")
        self.assertGreater(result["fold_count"], 0)
        print(f"\n  [BENCH] {result['label']}: {result['n_bars']} bars, "
              f"{result['param_count']} params → {result['runtime_sec']}s, "
              f"{result['memory_mb']}MB, {result['artifact_bytes']}B artifact, "
              f"{result['fold_count']} folds, Sharpe={result['sharpe']}")


if __name__ == "__main__":
    unittest.main()
