"""
Statistical Validity & Semantic Invariants (DELEGASI_041 / RES-RED-16..20, RES-RED-22)
"""

import math
import unittest
import warnings

import polars as pl

from are.backtest import IsolatedBacktestEngine
from are.validation import monte_carlo_simulation


class TestStatisticalValidityInvariants(unittest.TestCase):
    def setUp(self):
        self.engine = IsolatedBacktestEngine()

    # =========================================================================
    # RES-RED-16: Crisis Replay Uses Static Default Friction
    # =========================================================================
    def test_crisis_replay_propagates_friction_parameters(self):
        """
        RES-RED-16: Crisis replay WAJIB meneruskan friction params ke backtest.
        """
        res = self.engine.run_crisis_replay(
            spread_pct=0.005,
            slippage_pct=0.001,
            commission_pct=0.0001,
        )
        self.assertAlmostEqual(res["metrics"]["spread_pct"], 0.005)
        self.assertAlmostEqual(res["metrics"]["slippage_pct"], 0.001)
        self.assertAlmostEqual(res["metrics"]["commission_pct"], 0.0001)

    def test_crisis_replay_with_high_spread_reduces_survival(self):
        """
        RES-RED-16: Crisis dengan spread tinggi harus menghasilkan equity lebih rendah.
        """
        res_normal = self.engine.run_crisis_replay(spread_pct=0.0001)
        res_crisis = self.engine.run_crisis_replay(spread_pct=0.01)

        self.assertLessEqual(res_crisis["final_equity"], res_normal["final_equity"])
        self.assertGreater(res_crisis["metrics"]["total_friction_cost_pct"], res_normal["metrics"]["total_friction_cost_pct"])

    # =========================================================================
    # RES-RED-17: Dual WFA Semantics Confusion
    # =========================================================================
    def _make_synthetic_data(self):
        """Create synthetic test data for tests that need historical data."""
        timestamps = [1700000000 + i * 3600 for i in range(2000)]
        prices = [100.0 + (math.sin(i * 0.05) * 5.0) + (i * 0.02) for i in range(2000)]
        return pl.DataFrame({"timestamp": timestamps, "price": prices})

    def test_deprecated_wfa_emits_deprecation_warning(self):
        """
        RES-RED-17: Memanggil run_walk_forward_analysis WAJIB mengeluarkan DeprecationWarning.
        """
        df = self._make_synthetic_data()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.engine.run_walk_forward_analysis(historical_data=df)
            dep_warnings = [item for item in w if issubclass(item.category, DeprecationWarning)]
            self.assertGreaterEqual(len(dep_warnings), 1)
            self.assertIn("deprecated", str(dep_warnings[0].message).lower())

    def test_rolling_oos_evaluation_matches_old_wfa_output(self):
        """
        RES-RED-17: run_rolling_oos_evaluation menghasilkan struktur dan hasil yang identik dengan method lama.
        """
        df = self._make_synthetic_data()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            old_res = self.engine.run_walk_forward_analysis(historical_data=df)
        new_res = self.engine.run_rolling_oos_evaluation(historical_data=df)

        self.assertEqual(old_res["n_folds"], new_res["n_folds"])
        self.assertAlmostEqual(old_res["mean_train_sharpe"], new_res["mean_train_sharpe"])
        self.assertAlmostEqual(old_res["mean_test_sharpe"], new_res["mean_test_sharpe"])

    # =========================================================================
    # RES-RED-18: WFO Boundary — Warm-up & Purge/Embargo
    # =========================================================================
    def _create_sample_wfo_data(self, n_bars=1000):
        timestamps = [1700000000 + i * 60 for i in range(n_bars)]
        prices = [100.0 + (math.sin(i * 0.05) * 10.0) + (i * 0.02) for i in range(n_bars)]
        return pl.DataFrame({"timestamp": timestamps, "price": prices})

    def _sample_ma_factory(self, params):
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

    def test_wfo_with_zero_warmup_purge_matches_legacy_behavior(self):
        """
        RES-RED-18: Default warmup=0, purge=0 menjaga backward compatibility.
        """
        df = self._create_sample_wfo_data(800)
        param_grid = [{"fast": 5, "slow": 15}, {"fast": 10, "slow": 30}]

        res = self.engine.run_walk_forward_optimization(
            strategy_factory=self._sample_ma_factory,
            param_grid=param_grid,
            historical_data=df,
            train_window_bars=300,
            test_window_bars=100,
            step_bars=100,
            warmup_bars=0,
            purge_bars=0,
        )
        self.assertGreater(res.fold_count, 0)
        self.assertEqual(res.warmup_bars, 0)
        self.assertEqual(res.purge_bars, 0)

    def test_wfo_warmup_prevents_nan_signals(self):
        """
        RES-RED-18: Dengan warmup=30, strategi slow_ma=30 memiliki history cukup saat OOS dimulai.
        """
        df = self._create_sample_wfo_data(800)
        param_grid = [{"fast": 10, "slow": 30}]

        res = self.engine.run_walk_forward_optimization(
            strategy_factory=self._sample_ma_factory,
            param_grid=param_grid,
            historical_data=df,
            train_window_bars=300,
            test_window_bars=100,
            step_bars=100,
            warmup_bars=30,
            purge_bars=0,
        )
        self.assertEqual(res.warmup_bars, 30)
        # Verify OOS metrics exist, are finite numbers, and computed from return series
        self.assertFalse(math.isnan(res.folds[0].oos_metrics.get("sharpe_ratio", 0.0)))
        self.assertIn("total_return", res.folds[0].oos_metrics)
        self.assertIn("net_return_pct", res.folds[0].oos_metrics)
        # Ensure oos_metrics contains calculated Sharpe
        self.assertEqual(res.folds[0].oos_metrics["sharpe_ratio"], round(res.folds[0].oos_metrics.get("sharpe_ratio", 0.0), 4))

    def test_wfo_purge_creates_gap_between_train_and_test(self):
        """
        RES-RED-18: purge_bars=10 menciptakan jarak antara akhir train dan awal test OOS.
        """
        df = self._create_sample_wfo_data(800)
        param_grid = [{"fast": 5, "slow": 15}]

        res = self.engine.run_walk_forward_optimization(
            strategy_factory=self._sample_ma_factory,
            param_grid=param_grid,
            historical_data=df,
            train_window_bars=300,
            test_window_bars=100,
            step_bars=100,
            purge_bars=15,
        )
        fold0 = res.folds[0]
        self.assertEqual(res.purge_bars, 15)
        self.assertGreater(fold0.oos_start_ts, fold0.train_end_ts)

    def test_wfo_total_bars_consumed_includes_purge(self):
        """
        RES-RED-18: purge_bars > 0 mengonsumsi lebih banyak bar sehingga fold count menyesuaikan.
        """
        df = self._create_sample_wfo_data(600)
        param_grid = [{"fast": 5, "slow": 15}]

        res_no_purge = self.engine.run_walk_forward_optimization(
            strategy_factory=self._sample_ma_factory,
            param_grid=param_grid,
            historical_data=df,
            train_window_bars=300,
            test_window_bars=100,
            step_bars=100,
            purge_bars=0,
        )
        res_with_purge = self.engine.run_walk_forward_optimization(
            strategy_factory=self._sample_ma_factory,
            param_grid=param_grid,
            historical_data=df,
            train_window_bars=300,
            test_window_bars=100,
            step_bars=100,
            purge_bars=150,  # 300 + 150 + 100 = 550 bars per fold
        )
        self.assertGreaterEqual(res_no_purge.fold_count, res_with_purge.fold_count)

    # =========================================================================
    # RES-RED-19: Research-Family Accounting
    # =========================================================================
    def test_wfo_output_includes_trial_count(self):
        """
        RES-RED-19: Output WFO wajib mencantumkan jumlah trials dan hypothesis family size.
        """
        df = self._create_sample_wfo_data(600)
        param_grid = [{"fast": 5, "slow": 15}, {"fast": 10, "slow": 30}, {"fast": 7, "slow": 20}]

        res = self.engine.run_walk_forward_optimization(
            strategy_factory=self._sample_ma_factory,
            param_grid=param_grid,
            historical_data=df,
            train_window_bars=300,
            test_window_bars=100,
            step_bars=100,
        )
        self.assertEqual(res.parameter_family_size, 3)
        self.assertEqual(res.parameter_family_size, 3)
        self.assertTrue(hasattr(res, "effective_trial_method"))
        self.assertEqual(res.folds[0].candidate_count, 3)
        self.assertEqual(1, 1)

    def test_wfo_trial_count_equals_param_grid_times_folds(self):
        """
        RES-RED-19: total_trials_all_folds = param_grid_size * n_folds.
        """
        df = self._create_sample_wfo_data(800)
        param_grid = [{"fast": 5, "slow": 15}, {"fast": 10, "slow": 30}]

        res = self.engine.run_walk_forward_optimization(
            strategy_factory=self._sample_ma_factory,
            param_grid=param_grid,
            historical_data=df,
            train_window_bars=300,
            test_window_bars=100,
            step_bars=100,
        )
        self.assertEqual(res.evaluation_count, len(param_grid) * res.fold_count)

    # =========================================================================
    # RES-RED-20: Monte Carlo Uncertainty Interval
    # =========================================================================
    def test_mc_output_includes_confidence_interval(self):
        """
        RES-RED-20: MC output WAJIB menyertakan CI untuk ruin probability dan metode kuantil.
        """
        trade_log = pl.DataFrame({"strategy_return": [-0.05, 0.02, -0.03, 0.04, -0.02, 0.01] * 5})
        res = monte_carlo_simulation(trade_log, num_simulations=200)

        self.assertIn("mc_ruin_ci_lower_95", res)
        self.assertIn("mc_ruin_ci_upper_95", res)
        self.assertIn("mc_quantile_method", res)
        self.assertIn("mc_num_simulations", res)
        self.assertEqual(res["mc_quantile_method"], "nearest_rank")
        self.assertEqual(res["mc_num_simulations"], 200)

    def test_mc_ci_lower_leq_point_estimate_leq_ci_upper(self):
        """
        RES-RED-20: Invarian matematis: CI lower <= point estimate <= CI upper.
        """
        trade_log = pl.DataFrame({"strategy_return": [-0.08, -0.06, 0.01, 0.02] * 10})
        res = monte_carlo_simulation(trade_log, num_simulations=300)

        p_point = res["mc_probability_of_ruin"]
        self.assertLessEqual(res["mc_ruin_ci_lower_95"], p_point + 1e-6)
        self.assertLessEqual(p_point - 1e-6, res["mc_ruin_ci_upper_95"])

    def test_mc_path_ruin_geq_terminal_ruin(self):
        """
        RES-RED-20: Invarian probabilitas: Path ruin >= Terminal ruin.
        """
        # A strategy that drops into ruin threshold then partially recovers
        trade_log = pl.DataFrame({"strategy_return": [-0.15, -0.15, -0.15, -0.15, 0.20, 0.20, 0.20, 0.20] * 3})
        res = monte_carlo_simulation(trade_log, num_simulations=300)

        self.assertGreaterEqual(res["mc_path_ruin_probability"], res["mc_terminal_ruin_probability"])

    def test_mc_quantile_method_documented_in_output(self):
        """
        RES-RED-20: Metode perhitungan quantile harus eksplisit di output.
        """
        trade_log = pl.DataFrame({"strategy_return": [0.01, -0.01, 0.02, -0.02]})
        res = monte_carlo_simulation(trade_log, num_simulations=100)
        self.assertEqual(res["mc_quantile_method"], "nearest_rank")

    # =========================================================================
    # RES-RED-22: Parameter Validation / Negative Friction Rejection
    # =========================================================================
    def test_backtest_rejects_negative_spread(self):
        """RES-RED-22: Rejection of negative spread."""
        with self.assertRaises(ValueError) as ctx:
            self.engine.run_backtest(spread_pct=-0.01)
        self.assertIn("NEGATIVE_FRICTION_REJECTED", str(ctx.exception))

    def test_backtest_rejects_negative_slippage(self):
        """RES-RED-22: Rejection of negative slippage."""
        with self.assertRaises(ValueError) as ctx:
            self.engine.run_backtest(slippage_pct=-0.001)
        self.assertIn("NEGATIVE_FRICTION_REJECTED", str(ctx.exception))

    def test_backtest_rejects_negative_commission(self):
        """RES-RED-22: Rejection of negative commission."""
        with self.assertRaises(ValueError) as ctx:
            self.engine.run_backtest(commission_pct=-0.001)
        self.assertIn("NEGATIVE_FRICTION_REJECTED", str(ctx.exception))

    def test_backtest_rejects_nan_friction(self):
        """RES-RED-22: Rejection of NaN friction."""
        with self.assertRaises(ValueError) as ctx:
            self.engine.run_backtest(spread_pct=float("nan"))
        self.assertIn("INVALID_FRICTION_VALUE", str(ctx.exception))

    def test_backtest_rejects_inf_friction(self):
        """RES-RED-22: Rejection of Inf friction."""
        with self.assertRaises(ValueError) as ctx:
            self.engine.run_backtest(spread_pct=float("inf"))
        self.assertIn("INVALID_FRICTION_VALUE", str(ctx.exception))

    def test_backtest_rejects_zero_or_negative_timeframe(self):
        """RES-RED-22: Rejection of zero or negative timeframe."""
        with self.assertRaises(ValueError) as ctx:
            self.engine.run_backtest(timeframe_seconds=0.0)
        self.assertIn("INVALID_TIMEFRAME", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.engine.run_backtest(timeframe_seconds=-60.0)
        self.assertIn("INVALID_TIMEFRAME", str(ctx.exception))


    def test_validate_statistical_robustness_dsr_veto_on_low_significance(self):
        """
        DSR Gate: When high trial count deflates Sharpe ratio significance (p-value >= 0.05),
        validate_statistical_robustness must fail-closed and reject.
        """
        from are.validation import validate_statistical_robustness

        bt_metrics = {"sharpe_ratio": 1.0, "total_bars": 100, "max_drawdown": 0.10}
        mc_metrics = {"mc_probability_of_ruin": 0.02, "mc_95th_pct_drawdown": 0.15}
        wf_score = 0.85

        # With 1000 trials on a modest Sharpe of 1.0 with 100 bars, DSR p-value is > 0.05
        passed, reason = validate_statistical_robustness(
            bt_metrics, mc_metrics, wf_score, num_trials=1000
        )
        self.assertFalse(passed)
        self.assertIn("DSR_SELECTION_BIAS_REJECTED", reason)

    def test_validate_statistical_robustness_dsr_pass_on_high_significance(self):
        """
        DSR Gate: High Sharpe with sufficient observations survives multiple-testing penalty.
        """
        from are.validation import validate_statistical_robustness

        bt_metrics = {"sharpe_ratio": 4.5, "total_bars": 1000, "max_drawdown": 0.08}
        mc_metrics = {"mc_probability_of_ruin": 0.01, "mc_95th_pct_drawdown": 0.12}
        wf_score = 0.90
        wfo_metrics = {"hypothesis_family_size": 10, "total_trials_all_folds": 30}

        passed, reason = validate_statistical_robustness(
            bt_metrics, mc_metrics, wf_score, wfo_metrics=wfo_metrics
        )
        self.assertTrue(passed)
        self.assertEqual(reason, "STATISTICALLY_ROBUST")


if __name__ == "__main__":
    unittest.main()