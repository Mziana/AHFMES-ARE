"""
Statistical Rigor Invariants: Acklam Inverse CDF, FDR Control, PSR, DSR, and Governor Hardening (DELEGASI_035A)
100% Python Standard Library. Zero SciPy.
"""

import unittest

from are.governor import GovernorEngine
from are.validation import (
    ValidationReport,
    acklam_inverse_normal_cdf,
    apply_fdr_correction,
    calculate_deflated_sharpe_ratio,
    calculate_probabilistic_sharpe_ratio,
    standard_normal_cdf,
)


class TestFDRInvariants(unittest.TestCase):
    def setUp(self):
        self.governor = GovernorEngine()

    def test_acklam_inverse_normal_cdf_precision(self):
        """
        Invariant 1: Acklam inverse normal CDF precision vs known standard normal quantiles.
        Absolute error must be < 1e-4.
        """
        known_quantiles = [
            (0.5, 0.0),
            (0.975, 1.95996398454),
            (0.995, 2.57582930355),
            (0.025, -1.95996398454),
            (0.005, -2.57582930355),
        ]

        for p, expected_z in known_quantiles:
            computed_z = acklam_inverse_normal_cdf(p)
            self.assertAlmostEqual(
                computed_z,
                expected_z,
                places=4,
                msg=f"Failed for p={p}: got {computed_z}, expected {expected_z}",
            )

        # Boundary checks
        with self.assertRaises(ValueError):
            acklam_inverse_normal_cdf(0.0)
        with self.assertRaises(ValueError):
            acklam_inverse_normal_cdf(1.0)
        with self.assertRaises(ValueError):
            acklam_inverse_normal_cdf(-0.5)
        with self.assertRaises(ValueError):
            acklam_inverse_normal_cdf(1.5)

    def test_fdr_all_null_noise_rejected(self):
        """
        Invariant 2: 100 uniformly distributed high p-values (noise) are all rejected (False).
        """
        noise_p_values = [0.1 + (i * 0.008) for i in range(100)]
        survived = apply_fdr_correction(noise_p_values, alpha=0.05)

        self.assertEqual(len(survived), 100)
        self.assertEqual(sum(survived), 0, "No pure noise hypothesis should survive FDR control")
        self.assertTrue(all(not x for x in survived))

    def test_fdr_significant_signals_survive(self):
        """
        Invariant 3: Truly significant signals survive FDR multiple testing correction while noise is filtered.
        """
        significant_p = [0.0001] * 10
        noise_p = [0.8] * 90
        combined_p = significant_p + noise_p

        survived = apply_fdr_correction(combined_p, alpha=0.05)

        self.assertEqual(len(survived), 100)
        self.assertEqual(sum(survived), 10)
        self.assertTrue(all(survived[:10]))
        self.assertTrue(all(not x for x in survived[10:]))

    def test_dsr_high_trial_count_penalty(self):
        """
        Invariant 4: Multiple testing penalty in DSR inflates expected max Sharpe and increases p-value.
        """
        observed_sr = 1.5
        num_obs = 250

        # Trial 1: Single test (no multiple testing penalty)
        exp_sr_1, p_val_1 = calculate_deflated_sharpe_ratio(
            observed_sharpe=observed_sr,
            num_trials=1,
            num_observations=num_obs,
        )

        # Trial 500: 500 alpha seeds tested (severe selection bias penalty)
        exp_sr_500, p_val_500 = calculate_deflated_sharpe_ratio(
            observed_sharpe=observed_sr,
            num_trials=500,
            num_observations=num_obs,
        )

        self.assertEqual(exp_sr_1, 0.0)
        self.assertGreater(exp_sr_500, 1.5, "Expected max Sharpe must be high for 500 trials")
        self.assertLess(p_val_1, 0.01, "Single trial should be highly significant")
        self.assertGreater(p_val_500, 0.50, "500 trials must penalize Sharpe 1.5 to non-significance")

    def test_dsr_non_normality_penalty(self):
        """
        Invariant 5: Negative skewness and fat kurtosis increase standard error and penalize PSR/DSR.
        """
        observed_sr = 2.5
        num_obs = 150

        # Normal distribution (skew=0, kurtosis=3)
        _, p_val_normal = calculate_deflated_sharpe_ratio(
            observed_sharpe=observed_sr,
            num_trials=10,
            num_observations=num_obs,
            skewness=0.0,
            kurtosis=3.0,
        )

        # Negative skewness & fat tails (skew=-1.5, kurtosis=6.0)
        _, p_val_fat_tail = calculate_deflated_sharpe_ratio(
            observed_sharpe=observed_sr,
            num_trials=10,
            num_observations=num_obs,
            skewness=-1.5,
            kurtosis=6.0,
        )

        self.assertGreater(
            p_val_fat_tail,
            p_val_normal,
            "Fat tails and negative skewness must increase p-value (penalize strategy)",
        )

    def test_psr_robust_vs_noise(self):
        """
        Invariant 6: High Sharpe with large sample produces PSR > 0.95, weak Sharpe produces low PSR.
        """
        psr_high = calculate_probabilistic_sharpe_ratio(
            observed_sharpe=2.0,
            benchmark_sharpe=0.0,
            num_observations=250,
        )
        self.assertGreater(psr_high, 0.95, f"Expected PSR > 0.95, got {psr_high}")

        psr_low = calculate_probabilistic_sharpe_ratio(
            observed_sharpe=0.2,
            benchmark_sharpe=0.5,
            num_observations=50,
        )
        self.assertLess(psr_low, 0.50, f"Expected PSR < 0.50, got {psr_low}")

    def test_governor_rejects_insufficient_dsr(self):
        """
        Invariant 7: Governor Engine dismisses candidate if DSR p-value >= 0.05.
        """
        val_report = ValidationReport(
            candidate_id="CAND_DSR_FAIL_01",
            status="VALIDATED",
            sample_count=200,
            performance_metric=0.85,
            exposure_penalty=0.05,
            as_of_ts=1700000000.0,
        )

        disposition = self.governor.evaluate_promotion(
            candidate_id="CAND_DSR_FAIL_01",
            champion_id="CHAMPION_GENESIS",
            validation_report=val_report,
            critic_passed=True,
            creator_principal="RESEARCHER_ALICE",
            validator_principal="VALIDATOR_BOB",
            promoter_principal="GOVERNOR_CHARLIE",
            candidate_dsr_p_value=0.12,  # Insufficient (> 0.05)
            candidate_psr=0.98,
        )

        self.assertEqual(disposition.decision, "DISMISSED")
        self.assertIn("DEFLATED_SHARPE", disposition.rationale)

    def test_governor_rejects_insufficient_psr(self):
        """
        Invariant 8: Governor Engine dismisses candidate if PSR < 0.95.
        """
        val_report = ValidationReport(
            candidate_id="CAND_PSR_FAIL_01",
            status="VALIDATED",
            sample_count=200,
            performance_metric=0.85,
            exposure_penalty=0.05,
            as_of_ts=1700000000.0,
        )

        disposition = self.governor.evaluate_promotion(
            candidate_id="CAND_PSR_FAIL_01",
            champion_id="CHAMPION_GENESIS",
            validation_report=val_report,
            critic_passed=True,
            creator_principal="RESEARCHER_ALICE",
            validator_principal="VALIDATOR_BOB",
            promoter_principal="GOVERNOR_CHARLIE",
            candidate_dsr_p_value=0.02,  # Valid DSR
            candidate_psr=0.85,          # Insufficient PSR (< 0.95)
        )

        self.assertEqual(disposition.decision, "DISMISSED")
        self.assertIn("PROBABILISTIC_SHARPE", disposition.rationale)


if __name__ == "__main__":
    unittest.main()