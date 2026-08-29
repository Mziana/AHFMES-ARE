import asyncio
import math
import time
import unittest
from typing import Any, Dict, List

from are.evidence import EvidenceLedger
from are.health_monitor import SystemHealthMonitor
from are.champion import ChampionRegistry
from are.habitat import HabitatAdapter, ConditionAtlas
from are.mt5_feed import MT5MarketFeed
from are.mt5_gateway import MT5ExecutionGateway, MT5OrderRequest
from are.mt5_runner import MT5LiveRunner
from are.operational import OperationalBrain
from are.safety import CapitalSafetyKernel, SafetyLimits
from are.stability_harness import HourlyStabilityHarness
from are.storage import EventStore


class MockFeed(MT5MarketFeed):
    def __init__(self):
        super().__init__()
        self.fail_mode = False
        self.nan_mode = False

    def get_latest_ticks(self, symbol: str, count: int) -> List[Dict[str, Any]]:
        if self.fail_mode:
            from are.mt5_gateway import ARETransientError
            raise ARETransientError("Network down")
        
        t = time.time()
        if self.nan_mode:
            return [{"time": t, "bid": float("inf"), "ask": float("nan"), "last": float("nan")}]
        return [{"time": t, "bid": 50000.0, "ask": 50001.0, "last": 50000.5}]

    async def get_latest_ticks_async(self, symbol: str, count: int) -> List[Dict[str, Any]]:
        return self.get_latest_ticks(symbol, count)


class MockGateway(MT5ExecutionGateway):
    def __init__(self, kernel):
        super().__init__(safety_kernel=kernel)
        self.flat = False
    
    def emergency_flat(self) -> int:
        self.flat = True
        return 1

    async def emergency_flat_async(self) -> int:
        self.flat = True
        return 1
        
    def get_account_info(self, default_equity: float = 10000.0) -> Dict[str, float]:
        return {"equity": default_equity, "margin": 0.0, "drawdown": 0.0, "balance": default_equity}


class TestOperationalResilienceInvariants(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.feed = MockFeed()
        self.safety_kernel = CapitalSafetyKernel(SafetyLimits())
        self.gateway = MockGateway(self.safety_kernel)
        self.event_store = EventStore(":memory:")
        self.registry = ChampionRegistry(self.event_store)
        self.condition_atlas = ConditionAtlas()
        self.habitat = HabitatAdapter(self.condition_atlas, self.event_store)
        
        # Mock habitat run_inference to prevent needing actual model logic for simple tests
        self.habitat.run_inference = lambda cid, ctx: {"action": "NO_ACTION", "confidence": 0.0}
        
        self.brain = OperationalBrain(self.registry, self.safety_kernel, self.habitat, self.event_store)
        self.ledger = EvidenceLedger(":memory:")
        self.runner = MT5LiveRunner(
            feed=self.feed,
            gateway=self.gateway,
            brain=self.brain,
            event_store=self.event_store,
            evidence_ledger=self.ledger,
        )

    def test_runner_survives_network_disconnection_and_reconnects(self):
        """L1 RESILIENCE: mt5_runner must catch disconnects and recover automatically."""
        self.feed.fail_mode = True
        res = self.runner.step_live_tick()
        self.assertEqual(res["status"], "RETRY_TRANSIENT")
        
        self.feed.fail_mode = False
        res2 = self.runner.step_live_tick()
        self.assertNotEqual(res2["status"], "FEED_ERROR")
        self.assertIn("status", res2)

    def test_runner_handles_nan_and_infinity_in_market_feed(self):
        """L1 RESILIENCE: Corrupted data (NaN/Inf) must not crash the loop and must be filtered."""
        self.feed.nan_mode = True
        res = self.runner.step_live_tick()
        self.assertEqual(res["status"], "DATA_CORRUPTION_NAN_INF")

    async def test_circuit_breaker_trips_on_extreme_latency_jitter(self):
        """L1 RESILIENCE: Circuit breaker must trip when loop latency exceeds limits."""
        original_time = time.time
        def slow_time():
            if not hasattr(slow_time, "called"):
                slow_time.called = True
                return original_time()
            return original_time() + 6.0
        
        import builtins
        import are.mt5_runner
        
        original_time_runner = are.mt5_runner.time.time
        are.mt5_runner.time.time = slow_time
        
        try:
            res = await self.runner.step_live_tick_async()
            self.assertEqual(res["status"], "CIRCUIT_BREAKER_LATENCY_VIOLATION")
            self.assertEqual(res["signal"], "EMERGENCY_FLAT")
        finally:
            are.mt5_runner.time.time = original_time_runner

    def test_hourly_stability_harness_evaluates_stable_condition(self):
        """L1 RESILIENCE: Stability Harness must complete and verify STABLE conditions."""
        health_mon = SystemHealthMonitor()
        harness = HourlyStabilityHarness(
            safety_kernel=self.safety_kernel,
            gateway=self.gateway,
            health_monitor=health_mon,
            evidence_ledger=self.ledger,
            event_store=self.event_store
        )
        
        for i in range(24):
            harness.run_simulated_hour_block(hour_index=i, ticks_per_hour=10)
            
        summary = harness.get_stability_summary()
        self.assertEqual(summary["stability_status"], "STABLE")


if __name__ == "__main__":
    unittest.main()