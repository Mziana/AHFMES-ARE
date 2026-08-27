"""
Unit Tests for AHFMES ARE-3 Constants Centralization (ACC-307)
"""

import unittest
from are import constants
from are import state_machine
from are import registry


class TestARE3Constants(unittest.TestCase):
    def test_constants_importable_and_non_empty(self):
        self.assertTrue(len(constants.PROBLEM_LIFECYCLES) > 0)
        self.assertTrue(len(constants.HYPOTHESIS_LIFECYCLES) > 0)
        self.assertTrue(len(constants.CANDIDATE_LIFECYCLES) > 0)
        self.assertTrue(len(constants.EXPERIMENT_LIFECYCLES) > 0)
        self.assertTrue(len(constants.CAPABILITY_LIFECYCLES) > 0)
        self.assertTrue(len(constants.FORBIDDEN_SOD_PAIRS) > 0)
        self.assertTrue(len(constants.RESOLUTIVE_KEYWORDS) > 0)

    def test_single_source_of_truth_consistency(self):
        # Verify state_machine uses the exact same constant sets
        self.assertIs(state_machine.PROBLEM_LIFECYCLES, constants.PROBLEM_LIFECYCLES)
        self.assertIs(state_machine.HYPOTHESIS_LIFECYCLES, constants.HYPOTHESIS_LIFECYCLES)
        self.assertIs(state_machine.CANDIDATE_LIFECYCLES, constants.CANDIDATE_LIFECYCLES)
        self.assertIs(state_machine.FORBIDDEN_SOD_PAIRS, constants.FORBIDDEN_SOD_PAIRS)
        self.assertIs(state_machine.RESOLUTIVE_KEYWORDS, constants.RESOLUTIVE_KEYWORDS)

        # Verify registry uses the exact same constant sets
        self.assertIs(registry.PROBLEM_LIFECYCLES, constants.PROBLEM_LIFECYCLES)
        self.assertIs(registry.HYPOTHESIS_LIFECYCLES, constants.HYPOTHESIS_LIFECYCLES)
        self.assertIs(registry.CANDIDATE_LIFECYCLES, constants.CANDIDATE_LIFECYCLES)
        self.assertIs(registry.FORBIDDEN_SOD_PAIRS, constants.FORBIDDEN_SOD_PAIRS)


if __name__ == "__main__":
    unittest.main()
