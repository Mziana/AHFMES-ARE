"""
Unit Tests for AHFMES ARE-4 Capital Safety Kernel (ACC-401..ACC-405)
"""

import unittest

from are.safety import CapitalSafetyKernel, SafetyDecision, SafetyLimits


class TestCapitalSafetyKernel(unittest.TestCase):
    def setUp(self):
        self.limits = SafetyLimits(
            max_position_size=1.5,
            max_drawdown_pct=0.15,
            volatility_cutoff=2.5,
            max_order_rate_per_min=5,
            kill_switch_active=False,
        )
        self.kernel = CapitalSafetyKernel(self.limits)

    def test_emergency_kill_switch_veto(self):
        # 1. Via parameter
        d1 = self.kernel.evaluate_action(
            intended_action={"size": 1.0},
            current_drawdown=0.05,
            current_volatility=1.0,
            recent_order_count=1,
            emergency_signal=True,
        )
        self.assertFalse(d1.allowed)
        self.assertEqual(d1.action, "EMERGENCY_FLAT")
        self.assertEqual(d1.clamped_size, 0.0)
        self.assertIn("kill switch", d1.reason)

        # 2. Via limit flag
        kernel_kill = CapitalSafetyKernel(SafetyLimits(kill_switch_active=True))
        d2 = kernel_kill.evaluate_action(
            intended_action={"size": 1.0},
            current_drawdown=0.01,
            current_volatility=0.5,
            recent_order_count=0,
        )
        self.assertFalse(d2.allowed)
        self.assertEqual(d2.action, "EMERGENCY_FLAT")

    def test_max_drawdown_veto(self):
        dec = self.kernel.evaluate_action(
            intended_action={"size": 1.0},
            current_drawdown=0.16,  # > 0.15 limit
            current_volatility=1.0,
            recent_order_count=1,
        )
        self.assertFalse(dec.allowed)
        self.assertEqual(dec.action, "ABSTAIN")
        self.assertIn("drawdown", dec.reason)

    def test_volatility_cutoff_veto(self):
        dec = self.kernel.evaluate_action(
            intended_action={"size": 1.0},
            current_drawdown=0.05,
            current_volatility=2.8,  # > 2.5 cutoff
            recent_order_count=1,
        )
        self.assertFalse(dec.allowed)
        self.assertEqual(dec.action, "ABSTAIN")
        self.assertIn("volatility", dec.reason)

    def test_order_rate_limit_veto(self):
        dec = self.kernel.evaluate_action(
            intended_action={"size": 1.0},
            current_drawdown=0.02,
            current_volatility=1.0,
            recent_order_count=5,  # >= 5 limit
        )
        self.assertFalse(dec.allowed)
        self.assertEqual(dec.action, "ABSTAIN")
        self.assertIn("rate limit", dec.reason)

    def test_position_sizing_clamping_and_allow(self):
        # Requesting 3.0 when max is 1.5
        dec = self.kernel.evaluate_action(
            intended_action={"size": 3.0},
            current_drawdown=0.05,
            current_volatility=1.2,
            recent_order_count=2,
        )
        self.assertTrue(dec.allowed)
        self.assertEqual(dec.action, "EXECUTE")
        self.assertEqual(dec.clamped_size, 1.5)
        self.assertTrue(len(dec.decision_hash) > 0)


if __name__ == "__main__":
    unittest.main()
