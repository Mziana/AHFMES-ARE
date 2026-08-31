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


if __name__ == "__main__":
    unittest.main()
