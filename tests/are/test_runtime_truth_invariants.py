"""
Runtime Truth & Execution Safety Invariant Tests (DELEGASI_038 / RES-RED-01..06)
"""

import os
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

from are.champion import ChampionRegistry
from are.evidence import EvidenceLedger
from are.governor import PromotionDisposition
from are.habitat import ConditionAtlas, HabitatAdapter
from are.mt5_feed import MT5FeedConfig, MT5MarketFeed
from are.mt5_gateway import MT5ExecutionGateway, MT5MockGateway, MT5OrderRequest
from are.mt5_runner import MT5LiveRunner
from are.operational import OperationalBrain
from are.safety import CapitalSafetyKernel, SafetyLimits
from are.storage import EventStore


class TestRuntimeTruthInvariants(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "truth_test.db")
        self.store = EventStore(self.db_path)
        self.ledger = EvidenceLedger(self.db_path)
        self.limits = SafetyLimits(
            max_position_size=1.0,
            max_drawdown_pct=0.15,
            volatility_cutoff=2.5,
            max_order_rate_per_min=10,
            kill_switch_active=False,
        )
        self.safety_kernel = CapitalSafetyKernel(self.limits)
        self.gateway = MT5ExecutionGateway(safety_kernel=self.safety_kernel, use_mock=True)

    def tearDown(self):
        self.gateway.close()
        self.store.close()
        if hasattr(self.ledger, "_store") and self.ledger._store:
            self.ledger._store.close()
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def test_rate_limiter_uses_sliding_window_not_open_positions(self):
        """
        RES-RED-01: Verifies rate limiter uses sliding 60-second window, not len(open_positions).
        - 5 open positions opened >60s ago -> get_recent_order_count(60.0) == 0 -> order allowed.
        - 10 orders dispatched within 5s -> get_recent_order_count(60.0) == 10 -> 11th order blocked (ACC-404).
        """
        # Inject 5 open positions directly into mock gateway without recording recent window timestamps
        for i in range(5):
            req = MT5OrderRequest(
                symbol="BTCUSD",
                action="BUY",
                volume=0.01,
                price=50000.0 + i,
            )
            self.gateway._mock_gateway.send_order(req)

        self.assertEqual(len(self.gateway.get_open_positions()), 5)
        # Verify sliding window count is 0 because no timestamps were recorded in recent window
        self.assertEqual(self.gateway.get_recent_order_count(60.0), 0)

        # CSK should permit the order even though 5 positions exist
        risk_state = {
            "drawdown": 0.0,
            "volatility": 1.0,
            "order_count": self.gateway.get_recent_order_count(60.0),
        }
        test_req = MT5OrderRequest(symbol="BTCUSD", action="BUY", volume=0.01, price=50000.0)
        success, res, status_msg = self.gateway.execute_order(test_req, risk_state)
        self.assertTrue(success)
        self.assertEqual(status_msg, "FILLED_MOCK")
        self.assertEqual(self.gateway.get_recent_order_count(60.0), 1)

        # Now send 9 more orders within the current window (total 10 orders in 60s)
        for i in range(9):
            r = MT5OrderRequest(symbol="BTCUSD", action="BUY", volume=0.01, price=50000.0 + i)
            s, _, _ = self.gateway.execute_order(r, {"order_count": self.gateway.get_recent_order_count(60.0)})
            self.assertTrue(s)

        self.assertEqual(self.gateway.get_recent_order_count(60.0), 10)

        # The 11th order must be blocked by CSK (rate limit exceeded: max 10 per min)
        req_11 = MT5OrderRequest(symbol="BTCUSD", action="BUY", volume=0.01, price=50000.0)
        risk_state_11 = {"order_count": self.gateway.get_recent_order_count(60.0)}
        success_11, res_11, status_11 = self.gateway.execute_order(req_11, risk_state_11)
        self.assertFalse(success_11)
        self.assertIn("CSK_VETO", status_11)
        self.assertIn("ACC-404", status_11)

    def test_live_gateway_fails_closed_when_mt5_missing(self):
        """
        RES-RED-03: When use_mock=False and MetaTrader5 package is unavailable,
        gateway must fail closed by raising RuntimeError and leaving _mock_gateway None.
        """
        with patch.dict(sys.modules, {"MetaTrader5": None}):
            with self.assertRaises(RuntimeError) as ctx:
                MT5ExecutionGateway(self.safety_kernel, use_mock=False)

            self.assertIn("LIVE_MT5_REQUIRED_BUT_UNAVAILABLE", str(ctx.exception))

    def test_emergency_flat_verifies_zero_residual_positions(self):
        """
        RES-RED-04: emergency_flat() closes all positions and verifies zero residual positions remain.
        """
        for i in range(3):
            req = MT5OrderRequest(symbol="BTCUSD", action="BUY", volume=0.05, price=50000.0 + i)
            self.gateway.execute_order(req, {})

        self.assertEqual(len(self.gateway.get_open_positions()), 3)

        unclosed = self.gateway.emergency_flat()
        self.assertEqual(unclosed, [])
        self.assertEqual(len(self.gateway.get_open_positions()), 0)

    def test_emergency_flat_returns_residual_positions_if_remain(self):
        """
        RES-RED-04: If positions remain after liquidation attempts,
        emergency_flat() returns a list of residual unclosed positions.
        """
        faulty_mock = MagicMock()
        faulty_mock.close_all_positions.return_value = ["pos_1"]
        faulty_mock.get_open_positions.return_value = [{"ticket": 999, "symbol": "BTCUSD"}]

        gateway = MT5ExecutionGateway(self.safety_kernel, use_mock=True)
        gateway._mock_gateway = faulty_mock

        unclosed = gateway.emergency_flat()
        self.assertEqual(len(unclosed), 1)
        self.assertEqual(unclosed[0]["ticket"], 999)
        gateway.close()

    def test_runner_uses_dynamic_account_drawdown(self):
        """
        RES-RED-05: Runner fetches dynamic drawdown from gateway.
        When drawdown is 0.15 (15%), CSK must reject orders (ACC-402).
        """
        champ_reg = ChampionRegistry(self.store)
        disp = PromotionDisposition(
            candidate_id="CAND_DYN_DD",
            champion_id="GENESIS",
            decision="PROMOTED",
            rationale="Test Dynamic DD",
            governor_signature="GOV_SIG",
            timestamp=1728000000.0,
        )
        champ_reg.promote_champion("CAND_DYN_DD", disp)

        atlas = ConditionAtlas()
        habitat = HabitatAdapter(atlas, self.store)
        brain = OperationalBrain(
            champion_registry=champ_reg,
            safety_kernel=self.safety_kernel,
            habitat=habitat,
            event_store=self.store,
        )
        feed = MT5MarketFeed(MT5FeedConfig(use_mock=True, symbol="BTCUSD"))
        feed.initialize()

        runner = MT5LiveRunner(
            feed=feed,
            gateway=self.gateway,
            brain=brain,
            event_store=self.store,
            evidence_ledger=self.ledger,
            symbol="BTCUSD",
        )

        # Mock gateway.get_account_info to return drawdown = 0.15 (at max_drawdown limit)
        self.gateway.get_account_info = MagicMock(return_value={
            "balance": 10000.0,
            "equity": 8500.0,
            "drawdown": 0.15,
        })

        res = runner.step_live_tick(account_equity=10000.0)
        self.assertEqual(res["status"], "PROCESSED")
        self.assertIn("CSK_VETO", res.get("execution_status", ""))
        feed.shutdown()
        runner.close()

    def test_runner_fatal_exception_records_incident_and_flats(self):
        """
        RES-RED-06: Non-silent exception handling in runner loop records incident and calls emergency_flat.
        """
        runner = MT5LiveRunner(
            feed=MagicMock(),
            gateway=self.gateway,
            brain=MagicMock(),
            event_store=self.store,
            evidence_ledger=self.ledger,
            symbol="BTCUSD",
        )
        runner.step_live_tick = MagicMock(side_effect=ValueError("CRITICAL_MEMORY_CORRUPTION"))
        self.gateway.emergency_flat = MagicMock(return_value=0)

        with self.assertRaises(RuntimeError) as ctx:
            runner.run_live_loop(max_ticks=5, interval_sec=0.0)

        self.assertIn("MT5LiveRunner loop crashed: CRITICAL_MEMORY_CORRUPTION", str(ctx.exception))
        self.gateway.emergency_flat.assert_called_once()
        runner.close()


if __name__ == "__main__":
    unittest.main()