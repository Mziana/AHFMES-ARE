"""
Walk-Forward Analysis (WFA) Engine Invariant Tests (DELEGASI_036)
100% Python Standard Library + Polars.
"""

import time
import unittest
import polars as pl

from are.backtest import IsolatedBacktestEngine


class TestWalkForwardInvariants(unittest.TestCase):
    def setUp(self):
        self.engine = IsolatedBacktestEngine()

    def test_wfa_expanding_window_folds_execution(self):
        """
        Invariant 1: Slices data into rolling/expanding folds (at least 3 folds) with populated metrics.
        """
        n = 600
        timestamps = [1700000000 + i * 60 for i in range(n)]
        prices = [100.0 + (i * 0.05) for i in range(n)]
        df = pl.DataFrame({"timestamp": timestamps, "price": prices})

        res = self.engine.run_walk_forward_analysis(
            historical_data=df,
            train_window_bars=252,
            test_window_bars=63,
            step_bars=63,
        )

        self.assertGreaterEqual(res["n_folds"], 3)
        self.assertEqual(len(res["folds"]), res["n_folds"])
        for fold in res["folds"]:
            self.assertIn("is_sharpe", fold)
            self.assertIn("oos_sharpe", fold)
            self.assertIn("oos_return", fold)
            self.assertIn("oos_drawdown", fold)

    def test_wfa_detects_overfitting_decay(self):
        """
        Invariant 2: Detects severe overfitting when OOS performance collapses relative to IS.
        """
        n = 500
        timestamps = [1700000000 + i * 60 for i in range(n)]
        # Uptrend for first 300 bars (IS), severe crash for rest (OOS)
        prices = []
        for i in range(n):
            if i < 300:
                prices.append(100.0 + (i * 0.2))
            else:
                prices.append(160.0 - ((i - 300) * 0.5))
        df = pl.DataFrame({"timestamp": timestamps, "price": prices})

        # Naive strategy: Always long
        def always_long(data: pl.DataFrame) -> pl.DataFrame:
            return data.with_columns(pl.lit(1.0).alias("signal"))

        res = self.engine.run_walk_forward_analysis(
            strategy_logic=always_long,
            historical_data=df,
            train_window_bars=250,
            test_window_bars=63,
            step_bars=63,
        )

        self.assertLess(res["wfa_efficiency_ratio"], 0.50)

    def test_wfa_performance_benchmark(self):
        """
        Invariant 3: 1000 rows processed across multiple folds in under 3.0 seconds (Polars speed).
        """
        n = 1000
        timestamps = [1700000000 + i * 60 for i in range(n)]
        prices = [100.0 + (i * 0.01) for i in range(n)]
        df = pl.DataFrame({"timestamp": timestamps, "price": prices})

        t0 = time.perf_counter()
        res = self.engine.run_walk_forward_analysis(
            historical_data=df,
            train_window_bars=200,
            test_window_bars=50,
            step_bars=50,
        )
        elapsed = time.perf_counter() - t0

        self.assertGreaterEqual(res["n_folds"], 10)
        self.assertLess(elapsed, 3.0, f"WFA execution took {elapsed:.2f}s, exceeding 3.0s threshold")

    def test_wfa_consistency_calculation(self):
        """
        Invariant 4: Fold consistency ratio accurately computes the fraction of profitable OOS folds.
        """
        n = 600
        timestamps = [1700000000 + i * 60 for i in range(n)]
        # Pure uptrend -> all folds profitable
        prices = [100.0 + (i * 0.1) for i in range(n)]
        df = pl.DataFrame({"timestamp": timestamps, "price": prices})

        def always_long(data: pl.DataFrame) -> pl.DataFrame:
            return data.with_columns(pl.lit(1.0).alias("signal"))

        res = self.engine.run_walk_forward_analysis(
            strategy_logic=always_long,
            historical_data=df,
            train_window_bars=252,
            test_window_bars=63,
            step_bars=63,
        )

        self.assertEqual(res["fold_consistency_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()