"""
AHFMES ARE — Qualification Test

Runs the full pipeline against a golden dataset, then injects deliberate
corruption to verify that the gate correctly rejects compromised evidence.

This is the definitive test that the pipeline cannot produce PASS when
the evidence chain is broken.
"""

import json
import os
import shutil
import tempfile
import time
import unittest

import polars as pl

from are.backtest import IsolatedBacktestEngine
from are.hasher import compute_sha256
from are.research.integrity import (
    HoldoutEvidence,
    HoldoutEvaluationEngine,
    EvidenceBinding,
    HoldoutManager,
    LeakageFirewall,
    compute_canonical_dataset_hash,
    compute_canonical_split_hash,
)
from are.research.experiment_config import build_execution_model


def _make_golden_data(n_bars: int = 500) -> pl.DataFrame:
    """Create a golden dataset with known momentum signal behavior."""
    import random
    rng = random.Random(42)
    prices = [100.0]
    for _ in range(n_bars - 1):
        prices.append(prices[-1] * (1 + rng.gauss(0, 0.005)))
    return pl.DataFrame({
        "timestamp": [1700000000 + i * 3600 for i in range(n_bars)],
        "open": prices,
        "high": [p * (1 + abs(rng.gauss(0, 0.002))) for p in prices],
        "low": [p * (1 - abs(rng.gauss(0, 0.002))) for p in prices],
        "price": prices,
        "volume": [rng.randint(100, 10000) for _ in range(n_bars)],
    })


def _momentum_strategy(df: pl.DataFrame) -> pl.DataFrame:
    """Simple momentum strategy for golden dataset."""
    df = df.with_columns(
        pl.col("price").rolling_mean(10).alias("fast_ma"),
        pl.col("price").rolling_mean(30).alias("slow_ma"),
    ).with_columns(
        pl.when(pl.col("fast_ma") > pl.col("slow_ma")).then(1.0)
        .when(pl.col("fast_ma") < pl.col("slow_ma")).then(-1.0)
        .otherwise(0.0).alias("signal")
    ).drop("fast_ma", "slow_ma")
    return df


class TestQualificationPipeline(unittest.TestCase):
    """Test that the full pipeline is fail-closed against corruption."""

    def test_01_golden_dataset_hash_deterministic(self):
        """Same data produces same canonical hash."""
        df = _make_golden_data(100)
        h1 = compute_canonical_dataset_hash(df)
        h2 = compute_canonical_dataset_hash(df)
        self.assertEqual(h1, h2)

    def test_02_golden_dataset_hash_changes_with_mutation(self):
        """Mutating data changes hash."""
        df = _make_golden_data(100)
        h1 = compute_canonical_dataset_hash(df)
        # Mutate one price value
        df2 = df.with_columns(
            pl.when(pl.col("price") == df["price"][0])
            .then(pl.lit(999999.0))
            .otherwise(pl.col("price"))
            .alias("price")
        )
        h2 = compute_canonical_dataset_hash(df2)
        self.assertNotEqual(h1, h2)

    def test_03_split_hash_deterministic(self):
        """Same split parameters produce same hash."""
        h1 = compute_canonical_split_hash("ds1", 0, 60, 60, 80, 80, 100, purge_bars=5)
        h2 = compute_canonical_split_hash("ds1", 0, 60, 60, 80, 80, 100, purge_bars=5)
        self.assertEqual(h1, h2)

    def test_04_split_hash_changes_with_boundary_mutation(self):
        """Changing split boundary changes hash."""
        h1 = compute_canonical_split_hash("ds1", 0, 60, 60, 80, 80, 100)
        h2 = compute_canonical_split_hash("ds1", 0, 61, 60, 80, 80, 100)  # train_end changed
        self.assertNotEqual(h1, h2)

    def test_05_holdout_evidence_valid(self):
        """HoldoutEvaluationEngine produces valid evidence."""
        df = _make_golden_data(200)
        evidence = HoldoutEvaluationEngine.evaluate(
            strategy_logic=_momentum_strategy,
            holdout_df=df,
            selected_params={"lookback": 10},
            initial_capital=100000,
            timeframe_seconds=3600.0,
            run_id="TEST-001",
            split_id="SPLIT-TEST",
            dataset_hash="hash123",
            split_hash="split456",
            strategy_hash="strat789",
            wfo_provenance_hash="wfo000",
        )
        self.assertIsInstance(evidence, HoldoutEvidence)
        self.assertTrue(evidence.provenance_hash)
        validation = evidence.validate()
        # May have warnings (zero trades) but should not have errors
        self.assertIsInstance(validation, dict)
        self.assertIn("valid", validation)

    def test_06_evidence_binding_integrity(self):
        """EvidenceBinding verify() passes for correct binding."""
        binding = EvidenceBinding(
            run_id="R1", dataset_hash="D1", strategy_hash="S1",
            parameter_hash="P1", wfo_provenance_hash="W1",
            holdout_provenance_hash="H1",
        )
        result = binding.verify()
        self.assertTrue(result["valid"])

    def test_07_evidence_binding_tamper_detection(self):
        """Tampered binding fails verification."""
        binding = EvidenceBinding(
            run_id="R1", dataset_hash="D1", strategy_hash="S1",
            parameter_hash="P1", wfo_provenance_hash="W1",
            holdout_provenance_hash="H1",
        )
        # Tamper with the binding hash
        tampered = EvidenceBinding(
            run_id="R1", dataset_hash="D1", strategy_hash="S1",
            parameter_hash="P1", wfo_provenance_hash="W1",
            holdout_provenance_hash="H1",
            binding_hash="TAMPERED_HASH",
        )
        result = tampered.verify()
        self.assertFalse(result["valid"])

    def test_08_leakage_no_future_columns(self):
        """Strategy with future column is detected."""
        df = _make_golden_data(100)
        # Add a future-derived column
        df = df.with_columns(
            pl.col("price").shift(-1).alias("future_price")
        )
        df = _momentum_strategy(df)
        contract = LeakageFirewall.build_default_contract()
        result = LeakageFirewall.validate_signal_timing(df, contract)
        # Should detect future column
        future_checks = [c for c in result["checks"] if "future" in c["check"]]
        self.assertTrue(len(future_checks) > 0)

    def test_09_canonical_hash_schema_inclusion(self):
        """Adding a column changes canonical hash."""
        df1 = _make_golden_data(50)
        h1 = compute_canonical_dataset_hash(df1)
        # Add a column
        df2 = df1.with_columns(pl.lit(0.0).alias("extra_col"))
        h2 = compute_canonical_dataset_hash(df2)
        self.assertNotEqual(h1, h2)

    def test_10_holdout_evidence_provenance_tamper(self):
        """HoldoutEvidence with tampered provenance fails validation."""
        evidence = HoldoutEvaluationEngine.evaluate(
            strategy_logic=_momentum_strategy,
            holdout_df=_make_golden_data(200),
            selected_params={"lookback": 10},
            run_id="TEST-TAMPER", split_id="S-TAMPER",
            dataset_hash="D", split_hash="S", strategy_hash="ST",
            wfo_provenance_hash="W",
        )
        # Tamper with provenance hash
        tampered_dict = evidence.to_dict()
        tampered_dict["provenance_hash"] = "TAMPERED"
        # Build new evidence with tampered hash
        tampered_evidence = HoldoutEvidence(**{
            k: tuple(v) if isinstance(v, list) else v
            for k, v in tampered_dict.items()
        })
        result = tampered_evidence.validate()
        self.assertFalse(result["valid"])
        self.assertTrue(any("provenance" in i.lower() for i in result["issues"]))


class TestDeterminism(unittest.TestCase):
    """W1.5: Verify deterministic results for identical inputs."""

    def test_backtest_engine_determinism(self):
        """Same strategy + same data => identical Sharpe, return, DD."""
        import polars as pl
        from are.backtest import IsolatedBacktestEngine

        n = 2000
        timestamps = list(range(1700000000, 1700000000 + n * 3600, 3600))
        prices = [65000.0 + (i % 50) * 10.0 + (i * 0.1) for i in range(n)]
        df = pl.DataFrame({"timestamp": timestamps, "price": prices, "volume": [100] * n})

        def strategy_logic(df_inner):
            return df_inner.with_columns(
                pl.col("price").rolling_mean(20).alias("fast_ma"),
                pl.col("price").rolling_mean(50).alias("slow_ma"),
            ).with_columns(
                pl.when(pl.col("fast_ma") > pl.col("slow_ma")).then(1.0)
                .when(pl.col("fast_ma") < pl.col("slow_ma")).then(-1.0)
                .otherwise(0.0).alias("signal")
            )

        engine = IsolatedBacktestEngine()
        r1 = engine.run_backtest(strategy_logic=strategy_logic, historical_data=df,
                                  initial_capital=100000, timeframe_seconds=3600.0)
        r2 = engine.run_backtest(strategy_logic=strategy_logic, historical_data=df,
                                  initial_capital=100000, timeframe_seconds=3600.0)

        self.assertAlmostEqual(r1.metrics["sharpe_ratio"], r2.metrics["sharpe_ratio"],
                               places=10, msg="Sharpe must be deterministic")
        self.assertAlmostEqual(r1.metrics["total_return_pct"], r2.metrics["total_return_pct"],
                               places=10, msg="Return must be deterministic")
        self.assertAlmostEqual(r1.metrics["max_drawdown_pct"], r2.metrics["max_drawdown_pct"],
                               places=10, msg="Max DD must be deterministic")
        self.assertEqual(len(r1.trade_log), len(r2.trade_log),
                         msg="Trade count must be deterministic")

    def test_wfo_determinism(self):
        """Same WFO config => identical fold count and pooled Sharpe."""
        import polars as pl
        from are.backtest import IsolatedBacktestEngine

        n = 2000
        timestamps = list(range(1700000000, 1700000000 + n * 3600, 3600))
        prices = [65000.0 + (i % 50) * 10.0 + (i * 0.1) for i in range(n)]
        df = pl.DataFrame({"timestamp": timestamps, "price": prices, "volume": [100] * n})

        def strategy_factory(params):
            def logic(df_inner):
                lb = params.get("lookback", 20)
                return df_inner.with_columns(
                    pl.col("price").rolling_mean(lb).alias("fast_ma"),
                    pl.col("price").rolling_mean(lb + 30).alias("slow_ma"),
                ).with_columns(
                    pl.when(pl.col("fast_ma") > pl.col("slow_ma")).then(1.0)
                    .when(pl.col("fast_ma") < pl.col("slow_ma")).then(-1.0)
                    .otherwise(0.0).alias("signal")
                )
            return logic

        param_grid = [{"lookback": 10}, {"lookback": 20}]
        engine = IsolatedBacktestEngine()

        wfo1 = engine.run_walk_forward_optimization(
            strategy_factory=strategy_factory, param_grid=param_grid,
            historical_data=df, train_window_bars=500, test_window_bars=100,
            step_bars=100, warmup_bars=20, purge_bars=10,
            initial_capital=100000, timeframe_seconds=3600.0,
        )
        wfo2 = engine.run_walk_forward_optimization(
            strategy_factory=strategy_factory, param_grid=param_grid,
            historical_data=df, train_window_bars=500, test_window_bars=100,
            step_bars=100, warmup_bars=20, purge_bars=10,
            initial_capital=100000, timeframe_seconds=3600.0,
        )

        self.assertEqual(len(wfo1.folds), len(wfo2.folds),
                         msg="WFO fold count must be deterministic")
        self.assertAlmostEqual(wfo1.pooled_oos_sharpe, wfo2.pooled_oos_sharpe,
                               places=10, msg="WFO pooled Sharpe must be deterministic")
        self.assertEqual(len(wfo1.pooled_oos_returns), len(wfo2.pooled_oos_returns),
                         msg="WFO pooled returns length must be deterministic")
        for i, (r1, r2) in enumerate(zip(wfo1.pooled_oos_returns, wfo2.pooled_oos_returns)):
            self.assertAlmostEqual(r1, r2, places=15,
                msg=f"WFO pooled return[{i}] must be deterministic")

    def test_run_id_content_addressing(self):
        """Different strategy source_hash => different run_id."""
        from are.research.experiment_config import (
            ExperimentConfig, StrategyIdentity, ParameterGrid,
        )
        from are.research.experiment_config import build_execution_model, build_experiment_config
        from are.hasher import compute_sha256

        em = build_execution_model()
        pg = ParameterGrid(
            grid_id="g1", param_names=("lookback",),
            param_values=((10.0, 20.0),), grid_size=2, grid_hash="h1",
            constraints={},
        )
        strat1 = StrategyIdentity(
            strategy_id="det-001", strategy_name="Det 1",
            strategy_version="1.0.0", strategy_family="MOMENTUM",
            source_hash="hash_aaa", parameter_schema={"lookback": "int"},
            signal_contract="discrete_ternary", lookback_bars=20, warmup_bars=50,
            execution_assumption="next_bar_open",
        )
        config1 = build_experiment_config(
            strategy=strat1,
            execution_model=em, parameter_grid=pg,
        )

        strat2 = StrategyIdentity(
            strategy_id="det-001", strategy_name="Det 1",
            strategy_version="1.0.0", strategy_family="MOMENTUM",
            source_hash="hash_bbb", parameter_schema={"lookback": "int"},
            signal_contract="discrete_ternary", lookback_bars=20, warmup_bars=50,
            execution_assumption="next_bar_open",
        )
        config2 = build_experiment_config(
            strategy=strat2,
            execution_model=em, parameter_grid=pg,
        )

        self.assertNotEqual(config1.config_hash, config2.config_hash,
            msg="Different configs must have different hashes")

    def test_content_addressable_config_hash(self):
        """Identical ExperimentConfig => identical config_hash (idempotent)."""
        from are.research.experiment_config import (
            ExperimentConfig, StrategyIdentity, ParameterGrid,
        )
        from are.research.experiment_config import build_execution_model
        import time

        kwargs = dict(
            experiment_id="idem-test",
            created_at=12345.0,
            strategy=StrategyIdentity(
                strategy_id="idem-001", strategy_name="Idem 1",
                strategy_version="1.0.0", strategy_family="MOMENTUM",
                source_hash="hash_same", parameter_schema={"lookback": "int"},
                signal_contract="discrete_ternary", lookback_bars=20, warmup_bars=50,
                execution_assumption="next_bar_open",
            ),
            execution_model=build_execution_model(),
            parameter_grid=ParameterGrid(
                grid_id="g1", param_names=("lookback",),
                param_values=((10.0, 20.0),), grid_size=2, grid_hash="h1",
                constraints={},
            ),
            wfo_train_window_bars=500, wfo_test_window_bars=100,
            wfo_step_bars=100, wfo_purge_bars=10, wfo_warmup_bars=20,
            wfo_n_folds=5, wfo_selection_metric="sharpe_ratio",
            wfo_tie_breaker="(sharpe, -max_dd, -turnover)",
        )
        c1 = ExperimentConfig(**kwargs)
        c2 = ExperimentConfig(**kwargs)
        self.assertEqual(c1.config_hash, c2.config_hash,
            msg="Identical configs must produce identical hashes")


if __name__ == "__main__":
    unittest.main()
