"""
Runtime Drawdown Sizing Throttling Invariant Tests (DELEGASI_036)
100% Python Standard Library.
"""

import unittest

from are.safety import CapitalSafetyKernel, RiskLimits


class TestSafetyDrawdownSizingInvariants(unittest.TestCase):
    def setUp(self):
        # max_drawdown_pct = 0.15, max_position_size = 5.0
        self.limits = RiskLimits(
            max_drawdown_pct=0.15,
            volatility_cutoff=2.5,
            max_order_rate_per_min=10,
            max_position_size=5.0,
        )
        self.kernel = CapitalSafetyKernel(limits=self.limits)

    def test_safety_reduces_size_at_80pct_drawdown(self):
        """
        Invariant 1: When current drawdown reaches >= 80% of limit (0.12 of 0.15), size is throttled by 50%.
        """
        action = {"action": "BUY", "size": 1.0, "price": 100.0}
        risk_metrics = {
            "current_drawdown": 0.12,  # Exactly 80% of 0.15 limit
            "current_volatility": 1.0,
            "order_rate_1m": 1,
        }

        decision = self.kernel.evaluate_action(action, risk_metrics)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.clamped_size, 0.50)
        self.assertIn("size throttled 50%", decision.reason)

    def test_safety_normal_size_below_80pct_drawdown(self):
        """
        Invariant 2: When current drawdown is below 80% of limit (0.05 < 0.12), size remains unthrottled.
        """
        action = {"action": "BUY", "size": 1.0, "price": 100.0}
        risk_metrics = {
            "current_drawdown": 0.05,
            "current_volatility": 1.0,
            "order_rate_1m": 1,
        }

        decision = self.kernel.evaluate_action(action, risk_metrics)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.clamped_size, 1.0)
        self.assertNotIn("size throttled", decision.reason)

    def test_safety_zero_size_at_max_drawdown(self):
        """
        Invariant 3: When current drawdown breaches the limit (0.15 >= 0.15), order is rejected (size 0.0).
        """
        action = {"action": "BUY", "size": 1.0, "price": 100.0}
        risk_metrics = {
            "current_drawdown": 0.15,
            "current_volatility": 1.0,
            "order_rate_1m": 1,
        }

        decision = self.kernel.evaluate_action(action, risk_metrics)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.clamped_size, 0.0)
        self.assertEqual(decision.action, "ABSTAIN")
        self.assertIn("Max drawdown threshold exceeded", decision.reason)


if __name__ == "__main__":
    unittest.main()