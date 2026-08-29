"""
Historical Black Swan Crisis Replay & Bankruptcy Veto Invariant Tests (DELEGASI_035C)
100% Offline with Polars in-memory DataFrames. Zero SciPy, Zero Network.
"""

import unittest
import polars as pl

from are.backtest import IsolatedBacktestEngine
from are.governor import GovernorEngine
from are.validation import ValidationReport


class TestCrisisReplayInvariants(unittest.TestCase):
    def setUp(self):
        self.engine = IsolatedBacktestEngine()
        self.governor = GovernorEngine()

        # Deterministic severe crash dataset: 500 bars, plunges 60% (from 100.0 down to 40.0)
        n = 500
        timestamps = [1700000000 + i * 60 for i in range(n)]
        prices = [100.0 * (1.0 - (0.60 * (i / (n - 1)))) for i in range(n)]
        self.crash_df = pl.DataFrame({
            "timestamp": timestamps,
            "price": prices,
        })

    def test_crisis_replay_robust_strategy_survives(self):
        """
        Invariant 1: A defensive / risk-managed strategy preserves capital during a 60% market crash.
        """
        # Defensive strategy: Stay flat / do not blindly hold long during crash
        def defensive_strategy(df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns(pl.lit(0.0).alias("signal"))

        result = self.engine.run_crisis_replay(
            strategy_logic=defensive_strategy,
            crisis_df=self.crash_df,
            initial_capital=10000.0,
            survival_threshold_pct=0.50,
        )

        self.assertTrue(result["survival_bool"], f"Defensive strategy should survive, got {result}")
        self.assertFalse(result["bankruptcy_bool"])
        self.assertGreaterEqual(result["final_equity"], 5000.0)
        self.assertLessEqual(result["max_drawdown"], 0.50)

    def test_crisis_replay_fragile_strategy_bankrupts(self):
        """
        Invariant 2: A naive buy-and-hold strategy without risk control is wiped out during a 60% crash.
        """
        # Fragile strategy: Always long (1.0) with zero stop-loss
        def fragile_strategy(df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns(pl.lit(1.0).alias("signal"))

        result = self.engine.run_crisis_replay(
            strategy_logic=fragile_strategy,
            crisis_df=self.crash_df,
            initial_capital=10000.0,
            survival_threshold_pct=0.50,
        )

        self.assertFalse(result["survival_bool"], "Fragile strategy must fail Black Swan survival threshold")
        self.assertLess(result["final_equity"], 5000.0)
        self.assertGreater(result["max_drawdown"], 0.50)

    def test_governor_rejects_bankrupt_strategy_in_crisis(self):
        """
        Invariant 3: Governor Engine vetoes promotion if candidate failed Black Swan survival.
        """
        val_report = ValidationReport(
            candidate_id="CAND_FRAGILE_01",
            status="VALIDATED",
            sample_count=500,
            performance_metric=0.92,
            exposure_penalty=0.01,
            as_of_ts=1700000000.0,
        )

        disposition = self.governor.evaluate_promotion(
            candidate_id="CAND_FRAGILE_01",
            champion_id="CHAMPION_GENESIS",
            validation_report=val_report,
            critic_passed=True,
            creator_principal="RESEARCHER_ALICE",
            validator_principal="VALIDATOR_BOB",
            promoter_principal="GOVERNOR_CHARLIE",
            candidate_dsr_p_value=0.01,
            candidate_psr=0.98,
            crisis_survival=False,  # Failed crisis test
        )

        self.assertEqual(disposition.decision, "DISMISSED")
        self.assertIn("CRISIS_REPLAY_BANKRUPTCY", disposition.rationale)

    def test_governor_promotes_when_crisis_survived(self):
        """
        Invariant 4: Governor Engine promotes candidate when all gates pass including crisis survival.
        """
        val_report = ValidationReport(
            candidate_id="CAND_ROBUST_01",
            status="VALIDATED",
            sample_count=500,
            performance_metric=0.92,
            exposure_penalty=0.01,
            as_of_ts=1700000000.0,
        )

        disposition = self.governor.evaluate_promotion(
            candidate_id="CAND_ROBUST_01",
            champion_id="CHAMPION_GENESIS",
            validation_report=val_report,
            critic_passed=True,
            creator_principal="RESEARCHER_ALICE",
            validator_principal="VALIDATOR_BOB",
            promoter_principal="GOVERNOR_CHARLIE",
            candidate_dsr_p_value=0.01,
            candidate_psr=0.98,
            crisis_survival=True,  # Passed crisis test
        )

        self.assertEqual(disposition.decision, "PROMOTED")
        self.assertIn("passed out-of-sample validation", disposition.rationale)


if __name__ == "__main__":
    unittest.main()