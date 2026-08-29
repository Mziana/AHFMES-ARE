"""
Scientific Reality & Provenance Invariant Tests (DELEGASI_039 / RES-RED-07..09)
"""

import math
import os
import tempfile
import unittest

import polars as pl

from are.backtest import BacktestEngine, IsolatedBacktestEngine, calculate_sharpe_ratio
from are.evidence import EvidenceLedger
from are.storage import EventStore
from are.validation import ValidationReport, ValidationService


class TestScientificRealityInvariants(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "science_test.db")
        self.store = EventStore(self.db_path)
        self.ledger = EvidenceLedger(self.db_path)
        self.validation_service = ValidationService(self.ledger, self.store)
        self.engine = IsolatedBacktestEngine()

    def tearDown(self):
        self.store.close()
        if hasattr(self.ledger, "_store") and self.ledger._store:
            self.ledger._store.close()
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def test_sharpe_annualization_scales_with_bar_timeframe(self):
        """
        RES-RED-07: Verifies Sharpe ratio scaling dynamically scales with bar timeframe.
        1-minute data has factor sqrt(252 * 1440) ~= 602.39, while daily data has sqrt(252) ~= 15.87.
        """
        returns = [0.001 * (1 if i % 2 == 0 else -0.5) for i in range(100)]
        sharpe_1m = calculate_sharpe_ratio(returns, timeframe_seconds=60.0)
        sharpe_1d = calculate_sharpe_ratio(returns, timeframe_seconds=86400.0)

        # Scale factor check
        ratio = sharpe_1m / sharpe_1d
        expected_ratio = math.sqrt(1440.0)
        self.assertAlmostEqual(ratio, expected_ratio, places=4)

        # Annualization factor verification
        self.assertAlmostEqual(math.sqrt(252.0 * 1440.0), 602.3952, places=3)
        self.assertAlmostEqual(math.sqrt(252.0), 15.8745, places=3)

        # Backtest engine verification
        timestamps = [1700000000 + i * 60 for i in range(200)]
        prices = [100.0 + i * 0.1 for i in range(200)]
        df = pl.DataFrame({"timestamp": timestamps, "price": prices})

        res_1m = self.engine.run_backtest(historical_data=df, timeframe_seconds=60.0)
        res_1d = self.engine.run_backtest(historical_data=df, timeframe_seconds=86400.0)

        self.assertIn("annualization_factor", res_1m.metrics)
        self.assertAlmostEqual(res_1m.metrics["annualization_factor"], 602.3952, places=2)
        self.assertAlmostEqual(res_1d.metrics["annualization_factor"], 15.8745, places=2)

    def test_provenance_rejects_sentinel_zero_hash_as_verified(self):
        """
        RES-RED-08: ValidationService rejects sentinel zero-hash from claiming VERIFIED.
        Must set provenance_status to SENTINEL_UNPROVEN and is_provenance_verified to False.
        """
        dataset = [{"timestamp": 1700000000 + i * 60, "score": 0.8} for i in range(50)]
        report = self.validation_service.validate_candidate(
            candidate_id="CAND_SENTINEL_TEST",
            holdout_token="HT_001",
            as_of_ts=1700010000.0,
            dataset=dataset,
            source_manifest_hash="0" * 64,
            completeness_proof_hash="0" * 64,
        )
        self.assertEqual(report.provenance_status, "SENTINEL_UNPROVEN")
        self.assertNotEqual(report.provenance_status, "VERIFIED")
        self.assertFalse(report.is_provenance_verified)

    def test_provenance_allows_verified_only_on_valid_non_zero_hash(self):
        """
        RES-RED-08: ValidationService allows VERIFIED status only when valid non-zero
        cryptographic hashes are supplied.
        """
        dataset = [{"timestamp": 1700000000 + i * 60, "score": 0.8} for i in range(50)]
        valid_hash = "a" * 64
        valid_proof = "b" * 64
        report = self.validation_service.validate_candidate(
            candidate_id="CAND_VALID_PROV",
            holdout_token="HT_002",
            as_of_ts=1700010000.0,
            dataset=dataset,
            source_manifest_hash=valid_hash,
            completeness_proof_hash=valid_proof,
        )
        self.assertEqual(report.provenance_status, "VERIFIED")
        self.assertTrue(report.is_provenance_verified)

    def test_wfo_optimizes_in_sample_and_evaluates_out_of_sample(self):
        """
        RES-RED-09: True Walk-Forward Optimization (WFO) performs in-sample parameter fitting
        and evaluates the locked best parameter on independent out-of-sample slices.
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

        timestamps = [1700000000 + i * 60 for i in range(1200)]
        prices = [100.0 + (math.sin(i * 0.05) * 10.0) + (i * 0.02) for i in range(1200)]
        df = pl.DataFrame({"timestamp": timestamps, "price": prices})

        wfo_result = self.engine.run_walk_forward_optimization(
            strategy_factory=factory,
            param_grid=param_grid,
            historical_data=df,
            train_window_bars=400,
            test_window_bars=100,
            step_bars=100,
            optimization_metric="sharpe_ratio",
        )

        self.assertIn("folds", wfo_result)
        self.assertGreater(len(wfo_result["folds"]), 0)
        first_fold = wfo_result["folds"][0]
        self.assertIn("best_params", first_fold)
        self.assertIn("is_metrics", first_fold)
        self.assertIn("oos_metrics", first_fold)
        self.assertIn("wfe_ratio", first_fold)
        self.assertIn(first_fold["best_params"], param_grid)

    def test_wfo_detects_overfitting_parameter_decay(self):
        """
        RES-RED-09: WFO detects when in-sample optimized parameters decay out-of-sample (WFE < 0.5).
        """
        def factory(params: dict):
            bias = params["bias"]
            def strategy(df: pl.DataFrame) -> pl.DataFrame:
                sig = 1.0 if bias == "bull" else -1.0
                return df.with_columns(pl.lit(sig).alias("signal"))
            return strategy

        param_grid = [
            {"bias": "bull"},
            {"bias": "bear"},
        ]

        # First 400 bars: strong uptrend (+0.5 per bar) -> "bull" wins in Train
        # Next 100 bars: severe downtrend (-2.0 per bar) -> "bull" collapses in OOS
        prices = []
        p = 100.0
        for i in range(400):
            p += 0.5
            prices.append(p)
        for i in range(100):
            p -= 2.0
            prices.append(p)

        timestamps = [1700000000 + i * 60 for i in range(500)]
        df = pl.DataFrame({"timestamp": timestamps, "price": prices})

        wfo_result = self.engine.run_walk_forward_optimization(
            strategy_factory=factory,
            param_grid=param_grid,
            historical_data=df,
            train_window_bars=400,
            test_window_bars=100,
            step_bars=100,
            optimization_metric="sharpe_ratio",
        )

        self.assertEqual(len(wfo_result["folds"]), 1)
        fold_0 = wfo_result["folds"][0]
        self.assertEqual(fold_0["best_params"], {"bias": "bull"})
        self.assertGreater(fold_0["is_sharpe"], 0.0)
        self.assertLess(fold_0["wfe_ratio"], 0.5)


if __name__ == "__main__":
    unittest.main()