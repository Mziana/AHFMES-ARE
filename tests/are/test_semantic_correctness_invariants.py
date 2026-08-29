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


if __name__ == "__main__":
    unittest.main()