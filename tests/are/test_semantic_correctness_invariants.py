"""
Semantic Correctness & Safety Invariant Tests (DELEGASI_041 / RES-RED-14, RES-RED-13)
"""

import unittest
from unittest.mock import MagicMock

from are.mt5_gateway import MT5ExecutionGateway
from are.safety import CapitalSafetyKernel


class TestSemanticCorrectnessInvariants(unittest.TestCase):
    def setUp(self):
        self.safety_kernel = CapitalSafetyKernel()

    def test_get_open_positions_raises_on_none_api_response(self):
        """
        RES-RED-14: Ketika MT5 API mengembalikan None (error/disconnect),
        get_open_positions() WAJIB raise RuntimeError, BUKAN return [].
        """
        gateway = MT5ExecutionGateway(self.safety_kernel, use_mock=False)
        mock_mt5 = MagicMock()
        mock_mt5.positions_get.return_value = None
        gateway._mt5_lib = mock_mt5
        gateway._mock_gateway = None

        with self.assertRaises(RuntimeError) as ctx:
            gateway.get_open_positions()
        self.assertIn("MT5_POSITIONS_GET_RETURNED_NONE", str(ctx.exception))

    def test_emergency_flat_retries_on_none_not_treats_as_flat(self):
        """
        RES-RED-14: emergency_flat() TIDAK BOLEH menganggap None sebagai "flat".
        Harus retry, dan jika tetap None setelah 4 attempt, raise RuntimeError.
        """
        gateway = MT5ExecutionGateway(self.safety_kernel, use_mock=False)
        mock_mt5 = MagicMock()
        mock_mt5.positions_get.return_value = None  # Always None = persistent error
        gateway._mt5_lib = mock_mt5
        gateway._mock_gateway = None

        with self.assertRaises(RuntimeError) as ctx:
            gateway.emergency_flat()
        self.assertIn("EMERGENCY_FLAT_VERIFICATION_FAILED", str(ctx.exception))
        # Verify mt5 was called multiple times (retried, not treated as flat on first None)
        self.assertGreaterEqual(mock_mt5.positions_get.call_count, 2)

    def test_drawdown_uses_peak_equity_not_balance(self):
        """
        RES-RED-13: Drawdown harus dihitung dari peak equity, bukan balance.
        Skenario: equity naik ke 15000, lalu turun ke 13000.
        Balance tetap 14000. DD seharusnya (15000-13000)/15000 = 13.33%, bukan 7.14%.
        """
        gateway = MT5ExecutionGateway(self.safety_kernel, use_mock=True)
        mock_mt5 = MagicMock()
        gateway._mt5_lib = mock_mt5
        gateway._mock_gateway = None  # Force live path

        # Equity naik ke 15000
        acc_peak = MagicMock()
        acc_peak.balance = 14000.0
        acc_peak.equity = 15000.0
        mock_mt5.account_info.return_value = acc_peak
        info1 = gateway.get_account_info()
        self.assertAlmostEqual(info1["peak_equity"], 15000.0)
        self.assertAlmostEqual(info1["drawdown"], 0.0)  # At peak, DD = 0

        # Equity turun ke 13000
        acc_dd = MagicMock()
        acc_dd.balance = 14000.0
        acc_dd.equity = 13000.0
        mock_mt5.account_info.return_value = acc_dd
        info2 = gateway.get_account_info()
        self.assertAlmostEqual(info2["peak_equity"], 15000.0)  # Peak tidak turun
        expected_dd = (15000.0 - 13000.0) / 15000.0  # = 0.1333
        self.assertAlmostEqual(info2["drawdown"], expected_dd, places=4)
        # Verifikasi bukan (14000 - 13000) / 14000 = 0.0714
        self.assertNotAlmostEqual(info2["drawdown"], 0.0714, places=3)

    def test_peak_equity_only_increases_never_decreases(self):
        """
        RES-RED-13: peak_equity adalah high water mark — hanya naik, tidak pernah turun.
        """
        gateway = MT5ExecutionGateway(self.safety_kernel, use_mock=True)
        mock_mt5 = MagicMock()
        gateway._mt5_lib = mock_mt5
        gateway._mock_gateway = None

        equities = [10000.0, 12000.0, 11000.0, 15000.0, 14000.0, 13000.0]
        expected_peaks = [10000.0, 12000.0, 12000.0, 15000.0, 15000.0, 15000.0]

        for eq, expected_peak in zip(equities, expected_peaks):
            acc = MagicMock()
            acc.balance = 10000.0
            acc.equity = float(eq)
            mock_mt5.account_info.return_value = acc
            info = gateway.get_account_info()
            self.assertAlmostEqual(info["peak_equity"], float(expected_peak))

    def test_mock_path_tracks_peak_equity(self):
        """
        RES-RED-13: Default mock path juga mencatat peak_equity dengan benar.
        """
        gateway = MT5ExecutionGateway(self.safety_kernel, use_mock=True)
        info1 = gateway.get_account_info(default_equity=12000.0)
        self.assertEqual(info1["peak_equity"], 12000.0)
        self.assertEqual(info1["drawdown"], 0.0)

        info2 = gateway.get_account_info(default_equity=9000.0)
        self.assertEqual(info2["peak_equity"], 12000.0)
        self.assertAlmostEqual(info2["drawdown"], (12000.0 - 9000.0) / 12000.0)


if __name__ == "__main__":
    unittest.main()