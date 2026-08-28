"""
Property-Based Safety Invariant Tests for Capital Safety Kernel (DELEGASI_025, ACC-801..ACC-805)
"""

import math
import unittest
from hypothesis import given, settings
from hypothesis import strategies as st

from are.safety import CapitalSafetyKernel, SafetyDecision, SafetyLimits
from tests.are.strategies import (
    ambiguous_market_state_strategy,
    corrupt_price_strategy,
    extreme_slippage_latency_strategy,
)


class TestSafetyInvariants(unittest.TestCase):

    @given(
        corrupt_action=ambiguous_market_state_strategy(),
        drawdown=st.floats(min_value=-10.0, max_value=10.0),
        volatility=st.floats(min_value=-10.0, max_value=10.0),
        order_count=st.integers(min_value=-10, max_value=100),
    )
    @settings(max_examples=100, deadline=None)
    def test_fail_closed_on_corrupt_or_ambiguous_data(
        self, corrupt_action, drawdown, volatility, order_count
    ):
        """
        Invariant 1: Any corrupt, ambiguous, negative, or non-finite inputs MUST fail closed (allowed=False).
        """
        # Fresh kernel instantiation per hypothesis example to prevent state leakage (Bagian E.1)
        limits = SafetyLimits(
            max_position_size=1.0,
            max_drawdown_pct=0.15,
            volatility_cutoff=2.5,
            max_order_rate_per_min=10,
            kill_switch_active=False,
        )
        kernel = CapitalSafetyKernel(limits)

        # Determine if input is valid
        is_action_valid = (
            isinstance(corrupt_action, dict)
            and not corrupt_action.get("is_ambiguous", False)
            and not corrupt_action.get("is_corrupt", False)
        )
        price = corrupt_action.get("price") if isinstance(corrupt_action, dict) else None
        if price is not None:
            try:
                p = float(price)
                if not math.isfinite(p) or p <= 0.0 or p > 1e12:
                    is_action_valid = False
            except (ValueError, TypeError):
                is_action_valid = False

        is_risk_valid = (
            math.isfinite(drawdown)
            and drawdown >= 0.0
            and math.isfinite(volatility)
            and volatility >= 0.0
            and order_count >= 0
        )

        decision = kernel.evaluate_action(
            intended_action=corrupt_action,
            current_drawdown=drawdown,
            current_volatility=volatility,
            recent_order_count=order_count,
        )

        self.assertIsInstance(decision, SafetyDecision)
        self.assertTrue(len(decision.reason) > 0, "Rejection reason must be provided")

        if not is_action_valid or not is_risk_valid:
            self.assertFalse(
                decision.allowed,
                f"Kernel allowed a corrupt/ambiguous state: action={corrupt_action}, dd={drawdown}, vol={volatility}",
            )
            self.assertNotEqual(decision.action, "EXECUTE")

    @given(extreme_action=extreme_slippage_latency_strategy())
    @settings(max_examples=50, deadline=None)
    def test_circuit_breaker_triggers_on_extreme_slippage_and_latency(self, extreme_action):
        """
        Invariant 2: Extreme slippage (>500 pips) or execution latency (>5000 ms) MUST trigger VETO.
        """
        kernel = CapitalSafetyKernel(SafetyLimits())
        decision = kernel.evaluate_action(
            intended_action=extreme_action,
            current_drawdown=0.05,
            current_volatility=1.0,
            recent_order_count=1,
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action, "ABSTAIN")
        self.assertEqual(decision.clamped_size, 0.0)
        self.assertIn("circuit breaker", decision.reason.lower())

    @given(
        drawdown=st.floats(min_value=0.15001, max_value=1.0, allow_nan=False, allow_infinity=False),
        volatility=st.floats(min_value=2.5001, max_value=50.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, deadline=None)
    def test_circuit_breaker_triggers_on_excessive_drawdown_and_volatility(self, drawdown, volatility):
        """
        Invariant 3: Drawdown >= 15% or Volatility >= 2.5 sigma MUST be strictly vetoed.
        """
        kernel = CapitalSafetyKernel(SafetyLimits())
        valid_action = {"symbol": "BTCUSD", "price": 65000.0, "size": 0.5}

        # Test Drawdown Breach
        decision_dd = kernel.evaluate_action(
            intended_action=valid_action,
            current_drawdown=drawdown,
            current_volatility=1.0,
            recent_order_count=1,
        )
        self.assertFalse(decision_dd.allowed)
        self.assertEqual(decision_dd.action, "ABSTAIN")

        # Test Volatility Breach
        decision_vol = kernel.evaluate_action(
            intended_action=valid_action,
            current_drawdown=0.05,
            current_volatility=volatility,
            recent_order_count=1,
        )
        self.assertFalse(decision_vol.allowed)
        self.assertEqual(decision_vol.action, "ABSTAIN")

    @given(
        action=st.fixed_dictionaries({
            "symbol": st.sampled_from(["BTCUSD", "XAUUSD"]),
            "price": st.floats(min_value=100.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
            "size": st.floats(min_value=0.1, max_value=1.0, allow_nan=False, allow_infinity=False),
        }),
        emergency_signal=st.booleans(),
        kill_switch_config=st.booleans(),
    )
    @settings(max_examples=50, deadline=None)
    def test_kill_switch_invariant(self, action, emergency_signal, kill_switch_config):
        """
        Invariant 4: If kill_switch_active=True OR emergency_signal=True, 100% of signals are immediately rejected with EMERGENCY_FLAT.
        """
        limits = SafetyLimits(kill_switch_active=kill_switch_config)
        kernel = CapitalSafetyKernel(limits)

        decision = kernel.evaluate_action(
            intended_action=action,
            current_drawdown=0.01,
            current_volatility=0.5,
            recent_order_count=0,
            emergency_signal=emergency_signal,
        )

        if emergency_signal or kill_switch_config:
            self.assertFalse(decision.allowed)
            self.assertEqual(decision.action, "EMERGENCY_FLAT")
            self.assertEqual(decision.clamped_size, 0.0)
            self.assertIn("kill switch", decision.reason.lower())


if __name__ == "__main__":
    unittest.main()
