"""
Walk-Forward & Monte Carlo Validation Engine Invariant Tests (DELEGASI_031b)
"""

import unittest
import polars as pl

from are.governor import GovernorEngine
from are.validation import (
    ValidationReport,
    monte_carlo_simulation,
    validate_statistical_robustness,
    walk_forward_consistency,
)


class TestValidationInvariants(unittest.TestCase):
    def setUp(self):
        self.governor = GovernorEngine()

    def test_monte_carlo_detects_lucky_sequence(self):
        """
        Invariant 1: Monte Carlo permutation test detects lucky trade sequence ordering
        and flags high probability of ruin (> 10%).
        """
        # 95 trades with -1% return, followed by 1 lucky trade with +200% return
        returns = [-0.01] * 95 + [2.00]
        trade_log = pl.DataFrame({
            "strategy_return": returns,
        })

        mc_res = monte_carlo_simulation(trade_log, num_simulations=300, initial_capital=10000.0)

        # Under random shuffling, the 95 losses often occur before the big win, causing ruin probability > 10%
        self.assertGreater(
            mc_res["mc_probability_of_ruin"],
            0.10,
            f"Expected ruin probability > 0.10, got {mc_res['mc_probability_of_ruin']}",
        )

        passed, reason = validate_statistical_robustness(
            backtest_metrics={"max_drawdown": 0.15},
            mc_metrics=mc_res,
            wf_score=0.85,
        )

        self.assertFalse(passed)
        self.assertIn("MC_RUIN_PROBABILITY_HIGH", reason)

    def test_walk_forward_detects_regime_decay(self):
        """
        Invariant 2: Walk-Forward Analysis detects out-of-sample regime decay and retention < 50%.
        """
        # First half (50 trades): 85% win rate (+2% gain, -1% loss)
        is_trades = ([0.02] * 85 + [-0.01] * 15)[:50]
        # Second half (50 trades): 10% win rate (+2% gain, -1% loss)
        oos_trades = ([0.02] * 10 + [-0.01] * 90)[:50]

        all_trades = is_trades + oos_trades
        trade_log = pl.DataFrame({
            "strategy_return": all_trades,
        })

        wf_score = walk_forward_consistency(trade_log)

        self.assertLess(wf_score, 0.50, f"Expected WFA score < 0.50, got {wf_score}")

        passed, reason = validate_statistical_robustness(
            backtest_metrics={"max_drawdown": 0.10},
            mc_metrics={"mc_probability_of_ruin": 0.0, "mc_95th_pct_drawdown": 0.12},
            wf_score=wf_score,
        )

        self.assertFalse(passed)
        self.assertIn("WFA_REGIME_DECAY", reason)

    def test_governor_rejects_statistically_flawed_candidate(self):
        """
        Invariant 3: Governor Engine refuses promotion if candidate fails statistical robustness validation.
        """
        val_report = ValidationReport(
            candidate_id="CAND_OVERFIT_01",
            status="VALIDATED",
            sample_count=200,
            performance_metric=0.85,
            exposure_penalty=0.05,
            as_of_ts=1700000000.0,
        )

        stat_rob = (False, "MC_RUIN_PROBABILITY_HIGH: Probability of ruin > 10% under permutation.")

        disposition = self.governor.evaluate_promotion(
            candidate_id="CAND_OVERFIT_01",
            champion_id="CHAMPION_GENESIS",
            validation_report=val_report,
            critic_passed=True,
            creator_principal="RESEARCHER_ALICE",
            validator_principal="VALIDATOR_BOB",
            promoter_principal="GOVERNOR_CHARLIE",
            statistical_robustness=stat_rob,
        )

        self.assertEqual(disposition.decision, "DISMISSED")
        self.assertIn("statistical robustness validation failed", disposition.rationale)
        self.assertIn("MC_RUIN_PROBABILITY_HIGH", disposition.rationale)


if __name__ == "__main__":
    unittest.main()