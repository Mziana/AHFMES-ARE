"""
Integration Tests for AHFMES MT5 Live Runner (ACC-605)
"""

import os
import tempfile
import unittest

from are.champion import ChampionRegistry
from are.evidence import EvidenceLedger
from are.governor import PromotionDisposition
from are.habitat import ConditionAtlas, HabitatAdapter
from are.mt5_feed import MT5FeedConfig, MT5MarketFeed
from are.mt5_gateway import MT5ExecutionGateway
from are.mt5_runner import MT5LiveRunner
from are.operational import OperationalBrain
from are.safety import CapitalSafetyKernel, SafetyLimits
from are.storage import EventStore


class TestMT5Runner(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "mt5_runner_test.db")
        self.store = EventStore(self.db_path)
        self.ledger = EvidenceLedger(self.db_path)

        self.champ_reg = ChampionRegistry(self.store)
        self.limits = SafetyLimits(max_drawdown_pct=0.15, volatility_cutoff=2.5)
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
        self.gateway = MT5ExecutionGateway(self.safety_kernel, use_mock=True)

        self.runner = MT5LiveRunner(
            feed=self.feed,
            gateway=self.gateway,
            brain=self.brain,
            event_store=self.store,
            evidence_ledger=self.ledger,
            symbol="BTCUSD",
        )

    def tearDown(self):
        self.feed.shutdown()
        self.store.close()
        self.ledger.close()
        self.tmp_dir.cleanup()

    def test_live_runner_step_tick_and_execution(self):
        # 1. Promote Champion
        disp = PromotionDisposition(
            candidate_id="CAND_MT5_01",
            champion_id="GENESIS",
            decision="PROMOTED",
            rationale="Initial baseline",
            governor_signature="GOV_SIG_MT5",
            timestamp=1728000000.0,
        )
        self.champ_reg.promote_champion("CAND_MT5_01", disp)

        # 2. Step live tick
        self.feed.initialize()
        res = self.runner.step_live_tick(account_equity=10000.0)

        self.assertEqual(res["status"], "PROCESSED")
        self.assertEqual(res["symbol"], "BTCUSD")
        self.assertIn("signal", res)
        self.assertIn("execution_status", res)

    def test_live_runner_run_loop(self):
        # 1. Promote Champion
        disp = PromotionDisposition(
            candidate_id="CAND_MT5_BASE",
            champion_id="GENESIS",
            decision="PROMOTED",
            rationale="Baseline",
            governor_signature="GOV_SIG_MT5_BASE",
            timestamp=1728000000.0,
        )
        self.champ_reg.promote_champion("CAND_MT5_BASE", disp)

        # 2. Run 5 ticks loop
        processed = self.runner.run_live_loop(max_ticks=5, interval_sec=0.0)
        self.assertEqual(processed, 5)


if __name__ == "__main__":
    unittest.main()
