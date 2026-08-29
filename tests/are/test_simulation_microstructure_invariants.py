"""
Realistic Simulation Microstructure & Path-Dependency Invariant Tests (DELEGASI_040 / RES-RED-10..11)
"""

import math
import os
import tempfile
import unittest

import polars as pl

from are.backtest import BacktestEngine, IsolatedBacktestEngine
from are.validation import monte_carlo_simulation


class TestSimulationMicrostructureInvariants(unittest.TestCase):
    def setUp(self):
        self.engine = IsolatedBacktestEngine()

    def test_friction_model_penalizes_high_turnover_strategy(self):
        """
        RES-RED-10: Verifies that microstructure frictions penalize high-churn turnover strategies
        even when asset price is completely flat.
        """
        n_bars = 100
        timestamps = [1700000000 + i * 60 for i in range(n_bars)]
        prices = [100.0] * n_bars
        df = pl.DataFrame({"timestamp": timestamps, "price": prices})

        # Aggressive alternating BUY/SELL strategy
        def churn_strategy(data: pl.DataFrame) -> pl.DataFrame:
            signals = [1.0 if i % 2 == 0 else -1.0 for i in range(len(data))]
            return data.with_columns(pl.Series("signal", signals))

        # Run with friction
        spread = 0.0002
        comm = 0.0001
        res = self.engine.run_backtest(
            strategy_logic=churn_strategy,
            historical_data=df,
            initial_capital=10000.0,
            spread_pct=spread,
            slippage_pct=0.0,
            commission_pct=comm,
        )

        metrics = res.metrics
        self.assertGreater(metrics["total_turnover_count"], 50)
        self.assertGreater(metrics["total_friction_cost_pct"], 0.0)
        self.assertLess(metrics["total_return"], 0.0)
        self.assertEqual(metrics["gross_return_pct"], 0.0)
        self.assertLess(metrics["net_return_pct"], 0.0)

    def test_zero_friction_matches_legacy_gross_returns(self):
        """
        RES-RED-10: Verifies zero friction maintains 100% backward compatibility
        where net_return equals gross_return.
        """
        n_bars = 100
        timestamps = [1700000000 + i * 60 for i in range(n_bars)]
        prices = [100.0 + (i * 0.5) for i in range(n_bars)]
        df = pl.DataFrame({"timestamp": timestamps, "price": prices})

        res = self.engine.run_backtest(
            historical_data=df,
            spread_pct=0.0,
            slippage_pct=0.0,
            commission_pct=0.0,
        )

        metrics = res.metrics
        self.assertEqual(metrics["total_friction_cost_pct"], 0.0)
        self.assertEqual(metrics["gross_return_pct"], metrics["net_return_pct"])
        self.assertEqual(metrics["total_return_pct"], metrics["net_return_pct"])

    def test_block_bootstrap_preserves_streak_clustering(self):
        """
        RES-RED-11: Circular Block Bootstrap preserves streak dependencies,
        detecting higher/more conservative 95th-percentile drawdown than IID shuffle.
        """
        # Cluster of severe losses followed by mild gains
        returns = [-0.05, -0.05, -0.05, -0.05] + [0.015] * 20
        trade_log = pl.DataFrame({"strategy_return": returns})

        mc_block = monte_carlo_simulation(
            trade_log_df=trade_log,
            num_simulations=500,
            initial_capital=10000.0,
            method="BLOCK_BOOTSTRAP",
            block_size=4,
        )

        mc_iid = monte_carlo_simulation(
            trade_log_df=trade_log,
            num_simulations=500,
            initial_capital=10000.0,
            method="IID_SHUFFLE",
            block_size=1,
        )

        self.assertEqual(mc_block["mc_simulation_method"], "BLOCK_BOOTSTRAP")
        self.assertEqual(mc_block["mc_block_size"], 4)
        self.assertEqual(mc_iid["mc_simulation_method"], "IID_SHUFFLE")

        # Block bootstrap keeps the 4 consecutive -5% losses together (drawdown >= 18.5%)
        # while IID shuffle disperses them across gains
        self.assertGreater(
            mc_block["mc_95th_pct_drawdown"],
            mc_iid["mc_95th_pct_drawdown"],
            f"Expected Block Bootstrap 95th DD ({mc_block['mc_95th_pct_drawdown']}) > IID ({mc_iid['mc_95th_pct_drawdown']})",
        )

    def test_circular_block_bootstrap_handles_boundary_wrap(self):
        """
        RES-RED-11: Circular block bootstrap successfully samples blocks that wrap
        across the array boundaries without raising IndexError and preserving exact length.
        """
        returns = [0.01, -0.02, 0.03, -0.01, 0.05, -0.04, 0.02]
        trade_log = pl.DataFrame({"strategy_return": returns})

        # Run with block_size close to length
        mc_res = monte_carlo_simulation(
            trade_log_df=trade_log,
            num_simulations=100,
            initial_capital=10000.0,
            method="BLOCK_BOOTSTRAP",
            block_size=5,
        )

        self.assertIn("mc_95th_pct_drawdown", mc_res)
        self.assertIn("mc_probability_of_ruin", mc_res)
        self.assertIn("mc_mean_final_equity", mc_res)
        self.assertGreater(mc_res["mc_mean_final_equity"], 0.0)

    def test_wfo_integration_with_friction_model(self):
        """
        RES-RED-10 & RES-RED-09: WFO evaluates in-sample and out-of-sample slices
        incorporating realistic microstructure frictions.
        """
        def factory(params: dict):
            fast = params["fast"]
            slow = params["slow"]
            def strategy(df: pl.DataFrame) -> pl.DataFrame:
                return df.with_columns([
                    pl.col("price").rolling_mean(window_size=fast).alias("f_ma"),
                    pl.col("price").rolling_mean(window_size=slow).alias("s_ma"),
                ]).with_columns(
                    pl.when(pl.col("f_ma") > pl.col("s_ma"))
                    .then(pl.lit(1.0))
                    .otherwise(pl.lit(-1.0))
                    .alias("signal")
                )
            return strategy

        param_grid = [
            {"fast": 5, "slow": 15},
            {"fast": 10, "slow": 30},
        ]

        timestamps = [1700000000 + i * 60 for i in range(800)]
        prices = [100.0 + (math.sin(i * 0.04) * 15.0) + (i * 0.03) for i in range(800)]
        df = pl.DataFrame({"timestamp": timestamps, "price": prices})

        wfo_result = self.engine.run_walk_forward_optimization(
            strategy_factory=factory,
            param_grid=param_grid,
            historical_data=df,
            train_window_bars=300,
            test_window_bars=100,
            step_bars=100,
            optimization_metric="sharpe_ratio",
            spread_pct=0.0002,
            slippage_pct=0.0001,
            commission_pct=0.0001,
        )

        self.assertIn("folds", wfo_result)
        self.assertGreater(len(wfo_result["folds"]), 0)
        for fold in wfo_result["folds"]:
            # Assert both IS and OOS metrics have friction metadata
            self.assertIn("total_friction_cost_pct", fold["is_metrics"])
            self.assertIn("total_friction_cost_pct", fold["oos_metrics"])
            self.assertIn("net_return_pct", fold["oos_metrics"])
            self.assertIn("gross_return_pct", fold["oos_metrics"])


if __name__ == "__main__":
    unittest.main()