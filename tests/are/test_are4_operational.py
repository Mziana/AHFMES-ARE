"""
Unit Tests for AHFMES ARE-4 Operational Brain & Fast Loop (ACC-406..ACC-408)
"""

import os
import tempfile
import unittest

from are.champion import ChampionRegistry
from are.governor import PromotionDisposition
from are.habitat import ConditionAtlas, HabitatAdapter
from are.operational import OperationalBrain, OperationalSignal
from are.safety import CapitalSafetyKernel, SafetyLimits
from are.storage import EventStore


class TestOperationalBrain(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "op_test.db")
        self.store = EventStore(self.db_path)
        self.champion_registry = ChampionRegistry(self.store)
        self.safety_kernel = CapitalSafetyKernel(SafetyLimits(max_drawdown_pct=0.10, volatility_cutoff=2.0))
        self.atlas = ConditionAtlas()
        self.habitat = HabitatAdapter(self.atlas, self.store)
        self.brain = OperationalBrain(
            champion_registry=self.champion_registry,
            safety_kernel=self.safety_kernel,
            habitat=self.habitat,
            event_store=self.store,
        )

    def tearDown(self):
        self.store.close()
        self.tmp_dir.cleanup()

    def test_information_time_violation_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.brain.process_tick(
                symbol="BTCUSDT",
                timestamp=1050.0,
                market_features={"volatility": 1.0},
                current_risk_state={},
                as_of_cutoff=1000.0,  # 1050 > 1000
            )
        self.assertIn("Information-time barrier violated", str(ctx.exception))

    def test_abstain_when_no_active_champion(self):
        sig = self.brain.process_tick(
            symbol="BTCUSDT",
            timestamp=950.0,
            market_features={"volatility": 1.0, "trend_strength": 0.5},
            current_risk_state={"drawdown": 0.02, "volatility": 1.0, "order_count": 0},
            as_of_cutoff=1000.0,
        )
        self.assertIsInstance(sig, OperationalSignal)
        self.assertEqual(sig.final_action, "ABSTAIN")
        self.assertEqual(sig.raw_decision["action"], "ABSTAIN")

    def test_execute_signal_with_active_champion_and_persistence(self):
        # Deploy active champion
        disp = PromotionDisposition(
            candidate_id="CAND_MOMENTUM_01",
            champion_id="GENESIS",
            decision="PROMOTED",
            rationale="Verified pass",
            governor_signature="SIG_VALID",
            timestamp=900.0,
        )
        self.champion_registry.promote_champion("CAND_MOMENTUM_01", disp)

        sig = self.brain.process_tick(
            symbol="BTCUSDT",
            timestamp=950.0,
            market_features={"volatility": 1.1, "trend_strength": 1.5},
            current_risk_state={"drawdown": 0.02, "volatility": 1.1, "order_count": 0},
            as_of_cutoff=1000.0,
        )

        self.assertEqual(sig.final_action, "BUY")
        self.assertTrue(sig.safety_decision.allowed)
        self.assertEqual(sig.raw_decision["champion_id"], "CHAMP_CAND_MOMENTUM_01_900")
        self.assertTrue(len(sig.signal_hash) > 0)

        # Verify recorded to EventStore stream
        head = self.store.get_head(OperationalBrain.STREAM_ID)
        self.assertIsNotNone(head)
        self.assertEqual(head[0], 1)

    def test_safety_kernel_vetoes_champion_signal(self):
        disp = PromotionDisposition(
            candidate_id="CAND_02",
            champion_id="GENESIS",
            decision="PROMOTED",
            rationale="Pass",
            governor_signature="SIG_V",
            timestamp=900.0,
        )
        self.champion_registry.promote_champion("CAND_02", disp)

        # Volatility cutoff breach
        sig = self.brain.process_tick(
            symbol="ETHUSDT",
            timestamp=960.0,
            market_features={"volatility": 2.5, "trend_strength": 2.0},
            current_risk_state={"drawdown": 0.01, "volatility": 2.5, "order_count": 0},
            as_of_cutoff=1000.0,
        )
        self.assertEqual(sig.final_action, "ABSTAIN")
        self.assertFalse(sig.safety_decision.allowed)


if __name__ == "__main__":
    unittest.main()
