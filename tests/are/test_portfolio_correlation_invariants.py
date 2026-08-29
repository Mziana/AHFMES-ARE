"""
Portfolio Correlation & Risk Analytics Invariant Tests (DELEGASI_036)
100% Python Standard Library.
"""

import unittest

from are.governor import GovernorEngine
from are.portfolio import calculate_annualized_volatility, calculate_pearson_correlation
from are.validation import ValidationReport


class TestPortfolioCorrelationInvariants(unittest.TestCase):
    def setUp(self):
        self.governor = GovernorEngine()

    def test_correlation_calculation_accuracy_and_zero_variance(self):
        """
        Invariant 1: Validates exact math on identical (1.0), inverse (-1.0), and flat/zero variance (0.0).
        """
        a = [0.01, 0.02, -0.01, 0.03, 0.00]
        # Identical
        self.assertAlmostEqual(calculate_pearson_correlation(a, a), 1.0, places=5)

        # Inverted
        b = [-x for x in a]
        self.assertAlmostEqual(calculate_pearson_correlation(a, b), -1.0, places=5)

        # Constant / Zero Variance
        flat = [0.01, 0.01, 0.01, 0.01, 0.01]
        self.assertEqual(calculate_pearson_correlation(a, flat), 0.0)
        self.assertEqual(calculate_pearson_correlation(flat, flat), 0.0)

        # Volatility check
        vol = calculate_annualized_volatility(a, periods_per_year=252)
        self.assertGreater(vol, 0.0)
        self.assertEqual(calculate_annualized_volatility(flat), 0.0)

    def test_governor_rejects_highly_correlated_candidate(self):
        """
        Invariant 2: Governor vetoes promotion if candidate return correlation with champion exceeds 0.85.
        """
        val_report = ValidationReport(
            candidate_id="CAND_CORRELATED_01",
            status="VALIDATED",
            sample_count=500,
            performance_metric=0.95,
            exposure_penalty=0.01,
            as_of_ts=1700000000.0,
        )

        champ_returns = [0.01, 0.02, -0.01, 0.03, 0.01, -0.02, 0.04]
        # Highly correlated returns (~0.99)
        cand_returns = [r * 1.05 + 0.001 for r in champ_returns]

        disposition = self.governor.evaluate_promotion(
            candidate_id="CAND_CORRELATED_01",
            champion_id="CHAMPION_ALPHA",
            validation_report=val_report,
            critic_passed=True,
            creator_principal="RESEARCHER_ALICE",
            validator_principal="VALIDATOR_BOB",
            promoter_principal="GOVERNOR_CHARLIE",
            candidate_dsr_p_value=0.01,
            candidate_psr=0.98,
            crisis_survival=True,
            candidate_returns=cand_returns,
            existing_champions_returns={"CHAMPION_ALPHA": champ_returns},
        )

        self.assertEqual(disposition.decision, "DISMISSED")
        self.assertIn("PORTFOLIO_CORRELATION_EXCESSIVE", disposition.rationale)

    def test_governor_promotes_uncorrelated_candidate(self):
        """
        Invariant 3: Governor promotes candidate when correlation is low (< 0.85).
        """
        val_report = ValidationReport(
            candidate_id="CAND_DIVERSE_01",
            status="VALIDATED",
            sample_count=500,
            performance_metric=0.95,
            exposure_penalty=0.01,
            as_of_ts=1700000000.0,
        )

        champ_returns = [0.01, 0.02, -0.01, 0.03, 0.01, -0.02, 0.04]
        # Uncorrelated / different returns pattern
        cand_returns = [-0.02, 0.01, 0.03, -0.01, 0.02, 0.01, -0.03]

        disposition = self.governor.evaluate_promotion(
            candidate_id="CAND_DIVERSE_01",
            champion_id="CHAMPION_ALPHA",
            validation_report=val_report,
            critic_passed=True,
            creator_principal="RESEARCHER_ALICE",
            validator_principal="VALIDATOR_BOB",
            promoter_principal="GOVERNOR_CHARLIE",
            candidate_dsr_p_value=0.01,
            candidate_psr=0.98,
            crisis_survival=True,
            candidate_returns=cand_returns,
            existing_champions_returns={"CHAMPION_ALPHA": champ_returns},
        )

        self.assertEqual(disposition.decision, "PROMOTED")
        self.assertIn("passed out-of-sample validation", disposition.rationale)


if __name__ == "__main__":
    unittest.main()