"""
Unit Tests for AHFMES MT5 Execution Gateway (ACC-603, ACC-604)
"""

import unittest

from are.mt5_gateway import MT5ExecutionGateway, MT5MockGateway, MT5OrderRequest
from are.safety import CapitalSafetyKernel, SafetyLimits


class TestMT5Gateway(unittest.TestCase):
    def setUp(self):
        self.limits = SafetyLimits(
            max_position_size=1.0,
            max_drawdown_pct=0.10,
            volatility_cutoff=2.5,
            kill_switch_active=False,
        )
        self.safety_kernel = CapitalSafetyKernel(self.limits)
        self.gateway = MT5ExecutionGateway(self.safety_kernel, use_mock=True)

    def test_calculate_lot_size_clamping(self):
        lots = self.gateway.calculate_lot_size(account_equity=10000.0, risk_pct=0.01, stop_loss_points=100.0)
        self.assertEqual(lots, 1.0)  # clamped at max_position_size 1.0

        # Small equity -> smaller lot
        lots_small = self.gateway.calculate_lot_size(account_equity=500.0, risk_pct=0.01, stop_loss_points=100.0)
        self.assertEqual(lots_small, 0.05)

    def test_execute_order_success(self):
        req = MT5OrderRequest(
            symbol="BTCUSD",
            action="BUY",
            volume=0.5,
            price=65000.0,
            sl=64500.0,
            tp=66000.0,
        )
        risk_state = {"drawdown": 0.01, "volatility": 1.0, "order_count": 0}

        success, result, status = self.gateway.execute_order(req, risk_state)
        self.assertTrue(success)
        self.assertIsNotNone(result)
        self.assertEqual(result.volume, 0.5)
        self.assertEqual(status, "FILLED_MOCK")

        positions = self.gateway.get_open_positions()
        self.assertEqual(len(positions), 1)

    def test_execute_order_csk_veto_drawdown(self):
        req = MT5OrderRequest(symbol="BTCUSD", action="BUY", volume=0.5)
        # Breached drawdown 12% > 10%
        risk_state = {"drawdown": 0.12, "volatility": 1.0, "order_count": 0}

        success, result, status = self.gateway.execute_order(req, risk_state)
        self.assertFalse(success)
        self.assertIsNone(result)
        self.assertIn("CSK_VETO", status)

    def test_emergency_flat(self):
        # Open 2 positions
        self.gateway.execute_order(MT5OrderRequest(symbol="BTCUSD", action="BUY", volume=0.2), {"drawdown": 0.01, "volatility": 1.0, "order_count": 0})
        self.gateway.execute_order(MT5OrderRequest(symbol="ETHUSD", action="BUY", volume=0.3), {"drawdown": 0.01, "volatility": 1.0, "order_count": 1})

        self.assertEqual(len(self.gateway.get_open_positions()), 2)

        # Trigger Emergency Flat
        closed = self.gateway.emergency_flat()
        self.assertEqual(closed, 2)
        self.assertEqual(len(self.gateway.get_open_positions()), 0)


if __name__ == "__main__":
    unittest.main()
