"""
Property-Based Governor & Critic Invariant Tests (DELEGASI_025, ACC-806..ACC-810)
"""

import copy
import hashlib
import json
import unittest
from hypothesis import given, settings
from hypothesis import strategies as st

from are.governor import CriticEngine, GovernorEngine, PromotionDisposition
from are.validation import ValidationReport


class TestGovernorInvariants(unittest.TestCase):

    @given(
        challenger=st.fixed_dictionaries({
            "candidate_id": st.text(min_size=1, max_size=10),
            "performance": st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
            "drawdown": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            "params": st.dictionaries(st.text(min_size=1, max_size=5), st.integers(min_value=1, max_value=100)),
        }),
        champion=st.fixed_dictionaries({
            "champion_id": st.text(min_size=1, max_size=10),
            "performance": st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
            "drawdown": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        }),
        stress_factor=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, deadline=None)
    def test_governor_and_critic_never_mutate_candidate_or_champion(
        self, challenger, champion, stress_factor
    ):
        """
        Invariant 1: Critic evaluation and Governor promotion evaluation MUST NOT mutate candidate inputs.
        """
        governor = GovernorEngine(secret_key="TEST_GOVERNOR_KEY_PROPERTY_025")
        critic = CriticEngine()

        challenger_clone = copy.deepcopy(challenger)
        champion_clone = copy.deepcopy(champion)

        hash_chal_before = hashlib.sha256(json.dumps(challenger, sort_keys=True).encode("utf-8")).hexdigest()
        hash_champ_before = hashlib.sha256(json.dumps(champion, sort_keys=True).encode("utf-8")).hexdigest()

        # 1. Critic evaluation
        critic_res = critic.evaluate_adversarial(
            challenger_metrics=challenger,
            champion_metrics=champion,
            stress_factor=stress_factor,
        )
        self.assertIsInstance(critic_res, bool)

        # 2. Governor evaluation
        report = ValidationReport(
            candidate_id=challenger["candidate_id"],
            status="VALIDATED" if critic_res else "REJECTED",
            sample_count=100,
            performance_metric=challenger["performance"],
            exposure_penalty=0.0,
            as_of_ts=1000.0,
        )

        disposition = governor.evaluate_promotion(
            candidate_id=challenger["candidate_id"],
            champion_id=champion["champion_id"],
            validation_report=report,
            critic_passed=critic_res,
            creator_principal="Discovery_Agent_1",
            validator_principal="Validation_Agent_2",
            promoter_principal="Governor_Agent_3",
            current_ts=1000.0,
        )
        self.assertIsInstance(disposition, PromotionDisposition)

        # Verify zero mutation
        hash_chal_after = hashlib.sha256(json.dumps(challenger, sort_keys=True).encode("utf-8")).hexdigest()
        hash_champ_after = hashlib.sha256(json.dumps(champion, sort_keys=True).encode("utf-8")).hexdigest()

        self.assertEqual(hash_chal_before, hash_chal_after, "Challenger data was mutated during evaluation")
        self.assertEqual(hash_champ_before, hash_champ_after, "Champion data was mutated during evaluation")
        self.assertEqual(challenger, challenger_clone)
        self.assertEqual(champion, champion_clone)

    @given(
        high_pnl=st.floats(min_value=10.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        critic_pass=st.booleans(),
    )
    @settings(max_examples=50, deadline=None)
    def test_rejection_on_high_pnl_but_failed_risk_validation(self, high_pnl, critic_pass):
        """
        Invariant 2: A candidate with spectacular PnL/score MUST be strictly rejected if out-of-sample
        validation is rejected or critic fails.
        """
        governor = GovernorEngine(secret_key="TEST_GOVERNOR_KEY_PROPERTY_025")
        failed_report = ValidationReport(
            candidate_id="CAND_HIGH_PNL_FAILED_RISK",
            status="REJECTED",
            sample_count=100,
            performance_metric=high_pnl,
            exposure_penalty=0.5,
            as_of_ts=1000.0,
        )

        disposition = governor.evaluate_promotion(
            candidate_id="CAND_HIGH_PNL_FAILED_RISK",
            champion_id="CHAMPION_BASELINE",
            validation_report=failed_report,
            critic_passed=critic_pass,
            creator_principal="Discovery_Agent",
            validator_principal="Validation_Agent",
            promoter_principal="Governor_Agent",
            current_ts=1000.0,
        )

        self.assertEqual(disposition.decision, "DISMISSED")
        self.assertIn("dismissed", disposition.rationale.lower())

    @given(
        principals=st.lists(st.sampled_from(["Agent_Alice", "Agent_Bob", "Agent_Charlie"]), min_size=3, max_size=3)
    )
    @settings(max_examples=30, deadline=None)
    def test_sod_invariant_never_allows_overlapping_principals(self, principals):
        """
        Invariant 3: Separation of Duties (SoD) MUST reject if creator, validator, or promoter overlap.
        """
        governor = GovernorEngine(secret_key="TEST_GOVERNOR_KEY_PROPERTY_025")
        creator, validator, promoter = principals
        has_overlap = len(set(principals)) < 3

        if has_overlap:
            with self.assertRaises(ValueError):
                governor.verify_sod(creator, validator, promoter)
        else:
            # Should pass cleanly
            governor.verify_sod(creator, validator, promoter)


if __name__ == "__main__":
    unittest.main()
