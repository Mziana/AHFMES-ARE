"""
Unit & Integration Tests for AHFMES P001 Operational Runner Daemon (ACC-502, ACC-505)
"""

import os
import tempfile
import unittest

from are.coordinator import AgentAssignment
from are.governor import PromotionDisposition
from are.runner import OperationalRunner, RunnerConfig


class TestP001Runner(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "runner_test.db")
        self.config = RunnerConfig(
            db_path=self.db_path,
            symbol="BTCUSDT",
            tick_interval_sec=0.0,
            lookback_events=5,
            regret_threshold=0.30,
            auto_evolve=True,
        )
        self.runner = OperationalRunner(self.config)
        self.assignment = AgentAssignment(
            discovery_agent="Runner_Agent_1",
            validation_agent="Runner_Agent_2",
            governor_agent="Runner_Agent_3",
        )

    def tearDown(self):
        self.runner.close()
        self.tmp_dir.cleanup()

    def test_runner_step_tick_execution(self):
        # 1. Promote baseline champion
        disp = PromotionDisposition(
            candidate_id="CAND_RUNNER_01",
            champion_id="GENESIS",
            decision="PROMOTED",
            rationale="Initial baseline",
            governor_signature="GOV_SIG_R1",
            timestamp=1728000000.0,
        )
        self.runner.champion_registry.promote_champion("CAND_RUNNER_01", disp)

        # 2. Step 1 tick
        sig = self.runner.step_tick(
            market_features={"volatility": 1.0, "trend_strength": 1.5},
            current_risk_state={"drawdown": 0.01, "volatility": 1.0, "order_count": 0},
            timestamp=1728000100.0,
        )
        self.assertIsNotNone(sig)
        self.assertEqual(sig.final_action, "BUY")
        self.assertEqual(sig.symbol, "BTCUSDT")

    def test_runner_run_loop_and_adaptation(self):
        # 1. Promote baseline champion
        disp = PromotionDisposition(
            candidate_id="CAND_RUNNER_BASE",
            champion_id="GENESIS",
            decision="PROMOTED",
            rationale="Initial baseline",
            governor_signature="GOV_SIG_RBASE",
            timestamp=1728000000.0,
        )
        c_base = self.runner.champion_registry.promote_champion("CAND_RUNNER_BASE", disp)

        # 2. Tick generator with volatility shocks to breach regret
        tick_count = 0
        def tick_gen():
            nonlocal tick_count
            tick_count += 1
            # First 3 normal, next 7 shocks
            vol = 1.0 if tick_count <= 3 else 3.5
            return {"volatility": vol, "trend_strength": 0.5}, {"drawdown": 0.02, "volatility": vol, "order_count": tick_count}

        holdout = [{"timestamp": 1728000500.0, "score": 0.93}]
        processed = self.runner.run_loop(
            tick_generator_fn=tick_gen,
            max_ticks=10,
            assignment=self.assignment,
            holdout_dataset=holdout,
            evaluation_func=lambda f: {"performance": 0.93, "score": 0.93},
        )
        self.assertEqual(processed, 10)

        # Verify new champion emerged from slow loop
        active_champ = self.runner.champion_registry.get_active_champion()
        self.assertIsNotNone(active_champ)
        self.assertNotEqual(active_champ.champion_id, c_base.champion_id)


if __name__ == "__main__":
    unittest.main()
