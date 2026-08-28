"""
MT5 Async Bridge & Non-Blocking Isolation Invariant Tests (DELEGASI_026, ACC-601..ACC-605)
"""

import asyncio
import os
import tempfile
import time
import unittest

from are.champion import ChampionRegistry
from are.evidence import EvidenceLedger
from are.habitat import ConditionAtlas, HabitatAdapter
from are.mt5_feed import MT5FeedConfig, MT5MarketFeed
from are.mt5_gateway import MT5ExecutionGateway, MT5OrderRequest
from are.mt5_runner import MT5LiveRunner
from are.operational import OperationalBrain, OperationalSignal
from are.safety import CapitalSafetyKernel, SafetyLimits
from are.storage import EventStore


class TestMT5AsyncInvariants(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "mt5_async_test.db")
        self.store = EventStore(self.db_path)
        self.ledger = EvidenceLedger(self.db_path)

        self.champ_reg = ChampionRegistry(self.store)
        self.limits = SafetyLimits(
            max_position_size=1.0,
            max_drawdown_pct=0.15,
            volatility_cutoff=2.5,
            max_order_rate_per_min=10,
            kill_switch_active=False,
        )
        self.safety_kernel = CapitalSafetyKernel(self.limits)
        self.atlas = ConditionAtlas()
        self.habitat = HabitatAdapter(self.atlas, self.store)

        self.brain = OperationalBrain(
            champion_registry=self.champ_reg,
            safety_kernel=self.safety_kernel,
            habitat=self.habitat,
            event_store=self.store,
        )

        self.feed = MT5MarketFeed(MT5FeedConfig(use_mock=True, symbol="BTCUSD"))
        self.feed.initialize()
        self.gateway = MT5ExecutionGateway(safety_kernel=self.safety_kernel, use_mock=True)

        self.runner = MT5LiveRunner(
            feed=self.feed,
            gateway=self.gateway,
            brain=self.brain,
            event_store=self.store,
            evidence_ledger=self.ledger,
            symbol="BTCUSD",
        )

    def tearDown(self):
        self.runner.close()
        self.gateway.close()
        self.feed.shutdown()
        if hasattr(self, 'store'):
            self.store.close()
        if hasattr(self, 'ledger') and hasattr(self.ledger, '_store'):
            self.ledger._store.close()
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    async def test_non_blocking_tick_concurrency(self):
        """
        Invariant 1: Concurrently retrieving 50+ ticks via get_next_tick_async()
        runs smoothly without deadlock or blocking the event loop.
        """
        tasks = [self.feed.get_next_tick_async("BTCUSD") for _ in range(60)]
        results = await asyncio.gather(*tasks)

        self.assertEqual(len(results), 60)
        for tick in results:
            self.assertIsNotNone(tick)
            self.assertIn("bid", tick)
            self.assertIn("ask", tick)
            self.assertIn("last", tick)
            self.assertGreater(tick["bid"], 0.0)

    async def test_async_order_safety_gating(self):
        """
        Invariant 2: Async order execution strictly enforces CapitalSafetyKernel firewall limits.
        """
        normal_signal = OperationalSignal(
            signal_id="SIG_ASYNC_001",
            symbol="BTCUSD",
            raw_decision={"action": "BUY", "champion_id": "CHAMP_001"},
            safety_decision=None,  # Handled safely by send_order_async
            final_action="BUY",
            timestamp=time.time(),
        )

        # 1. Normal risk state -> Should succeed
        res_normal = await self.gateway.send_order_async(
            signal=normal_signal,
            market_state={"symbol": "BTCUSD", "price": 65000.0, "drawdown": 0.02, "volatility": 1.0},
        )
        self.assertTrue(res_normal["success"])
        self.assertEqual(res_normal["status"], "FILLED_MOCK")
        self.assertGreater(res_normal["latency_ms"], 0.0)

        # 2. Breached risk state (Drawdown >= 15%) -> CSK MUST VETO
        res_veto = await self.gateway.send_order_async(
            signal=normal_signal,
            market_state={"symbol": "BTCUSD", "price": 65000.0, "drawdown": 0.20, "volatility": 1.0},
        )
        self.assertFalse(res_veto["success"])
        self.assertIn("CSK_VETO", res_veto["status"])

        # 3. Kill switch active -> CSK MUST VETO
        strict_kernel = CapitalSafetyKernel(SafetyLimits(kill_switch_active=True))
        strict_gateway = MT5ExecutionGateway(safety_kernel=strict_kernel, use_mock=True)
        res_kill = await strict_gateway.send_order_async(
            signal=normal_signal,
            market_state={"symbol": "BTCUSD", "price": 65000.0, "drawdown": 0.01, "volatility": 1.0},
        )
        self.assertFalse(res_kill["success"])
        self.assertIn("CSK_VETO", res_kill["status"])
        strict_gateway.close()

    async def test_non_blocking_main_thread_coexistence(self):
        """
        Invariant 3: Heavy/slow gateway I/O in worker thread does NOT freeze concurrent
        event loop tasks or math computations in the main thread.
        """
        start_time = time.time()

        # Launch async tick ingestion tasks
        tick_task = asyncio.create_task(self.feed.get_latest_ticks_async("BTCUSD", count=20))

        # Simultaneously run fast calculations on the event loop
        computed_sum = 0
        for i in range(1000):
            computed_sum += i
            if i % 100 == 0:
                await asyncio.sleep(0.001)

        ticks = await tick_task
        elapsed = time.time() - start_time

        self.assertEqual(computed_sum, 499500)
        self.assertEqual(len(ticks), 20)
        self.assertLess(elapsed, 2.0, "Concurrent execution took unexpectedly long")

    async def test_async_runner_tick_stream(self):
        """
        Invariant 4: Async live runner streams ticks and records latency without blocking.
        """
        ticks_processed = await self.runner.run_tick_stream_async(max_ticks=5, interval_seconds=0.01)
        self.assertEqual(ticks_processed, 5)
        self.assertGreater(self.runner.last_latency_ms, 0.0)


if __name__ == "__main__":
    unittest.main()
