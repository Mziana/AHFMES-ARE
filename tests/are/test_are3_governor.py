"""
Unit Tests for AHFMES ARE-3 Critic & Governor Engine (ACC-305, ACC-306)
"""

import unittest
from are.governor import CriticEngine, GovernorEngine, PromotionDisposition
from are.validation import ValidationReport


class TestGovernorAndCritic(unittest.TestCase):
    def setUp(self):
        self.critic = CriticEngine()
        self.governor = GovernorEngine(secret_key="TEST_GOV_KEY")

    def test_sod_violation_raises(self):
        # Creator == Validator
        with self.assertRaises(ValueError) as ctx1:
            self.governor.verify_sod(creator_principal="Alice", validator_principal="Alice", promoter_principal="Bob")
        self.assertIn("Separation of Duties", str(ctx1.exception))

        # Creator == Promoter
        with self.assertRaises(ValueError) as ctx2:
            self.governor.verify_sod(creator_principal="Alice", validator_principal="Bob", promoter_principal="Alice")
        self.assertIn("Separation of Duties", str(ctx2.exception))

        # Validator == Promoter
        with self.assertRaises(ValueError) as ctx3:
            self.governor.verify_sod(creator_principal="Alice", validator_principal="Bob", promoter_principal="Bob")
        self.assertIn("Separation of Duties", str(ctx3.exception))

    def test_adversarial_critic_comparison(self):
        # Challenger clearly wins
        challenger_good = {"performance": 1.2, "drawdown": 0.05}
        champion_base = {"performance": 0.8, "drawdown": 0.10}
        self.assertTrue(self.critic.evaluate_adversarial(challenger_good, champion_base, stress_factor=1.1))

        # Challenger loses due to excessive drawdown under stress
        challenger_fragile = {"performance": 1.0, "drawdown": 0.8}
        self.assertFalse(self.critic.evaluate_adversarial(challenger_fragile, champion_base, stress_factor=1.5))

    def test_governor_promotion_evaluation(self):
        val_report_pass = ValidationReport(
            candidate_id="CAND_ALPHA",
            status="VALIDATED",
            sample_count=100,
            performance_metric=0.85,
            exposure_penalty=0.02,
            as_of_ts=1000.0,
        )

        disp = self.governor.evaluate_promotion(
            candidate_id="CAND_ALPHA",
            champion_id="CHAMP_V1",
            validation_report=val_report_pass,
            critic_passed=True,
            creator_principal="Researcher_A",
            validator_principal="Validator_B",
            promoter_principal="Governor_C",
            current_ts=1000.0,
        )

        self.assertIsInstance(disp, PromotionDisposition)
        self.assertEqual(disp.decision, "PROMOTED")
        self.assertTrue(len(disp.governor_signature) > 0)
        self.assertIsNotNone(disp.disposition_hash)

        # Failure case: validation rejected
        val_report_fail = ValidationReport(
            candidate_id="CAND_BETA",
            status="REJECTED",
            sample_count=50,
            performance_metric=0.30,
            exposure_penalty=0.05,
            as_of_ts=1000.0,
        )

        disp_fail = self.governor.evaluate_promotion(
            candidate_id="CAND_BETA",
            champion_id="CHAMP_V1",
            validation_report=val_report_fail,
            critic_passed=True,
            creator_principal="Researcher_A",
            validator_principal="Validator_B",
            promoter_principal="Governor_C",
            current_ts=1000.0,
        )
        self.assertEqual(disp_fail.decision, "DISMISSED")


if __name__ == "__main__":
    unittest.main()
