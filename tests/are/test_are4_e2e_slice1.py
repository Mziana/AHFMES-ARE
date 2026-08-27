"""
End-to-End Integration Tests for AHFMES ARE-4 Slice-1 (ACC-409)

Validates the full Operational Brain fast-loop execution:
1. Dynamic model inference based on active Champion in Champion Registry.
2. Non-bypassable Capital Safety Kernel gating (drawdown, volatility, kill-switch).
3. Append-only audit trail in EventStore stream "operational_signals".
"""

import os
import tempfile
import unittest

from are.champion import ChampionRegistry
from are.governor import PromotionDisposition
from are.habitat import ConditionAtlas, HabitatAdapter
from are.operational import OperationalBrain
from are.safety import CapitalSafetyKernel, SafetyLimits
from are.storage import EventStore


class TestARE4Slice1EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "slice1_e2e.db")
        self.store = EventStore(self.db_path)
        self.champion_registry = ChampionRegistry(self.store)
        self.limits = SafetyLimits(
            max_position_size=2.0,
            max_drawdown_pct=0.12,
            volatility_cutoff=2.0,
            max_order_rate_per_min=10,
        )
        self.safety_kernel = CapitalSafetyKernel(self.limits)
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

    def test_full_fast_loop_operational_lifecycle(self):
        as_of_cutoff = 1727000000.0

        # Step 1: Deploy Champion
        disp = PromotionDisposition(
            candidate_id="CAND_ARE4_CHAMPION_V1",
            champion_id="GENESIS",
            decision="PROMOTED",
            rationale="Pass validation and critic",
            governor_signature="GOV_SIG_VALID_123",
            timestamp=as_of_cutoff - 5000,
        )
        self.champion_registry.promote_champion("CAND_ARE4_CHAMPION_V1", disp)

        # Step 2: Tick 1 — Normal Condition -> BUY Signal
        sig1 = self.brain.process_tick(
            symbol="BTCUSDT",
            timestamp=as_of_cutoff - 4000,
            market_features={"volatility": 1.0, "trend_strength": 1.5},
            current_risk_state={"drawdown": 0.02, "volatility": 1.0, "order_count": 1},
            as_of_cutoff=as_of_cutoff,
        )
        self.assertEqual(sig1.final_action, "BUY")
        self.assertTrue(sig1.safety_decision.allowed)

        # Step 3: Tick 2 — High Volatility Spike -> CSK Veto ABSTAIN
        sig2 = self.brain.process_tick(
            symbol="BTCUSDT",
            timestamp=as_of_cutoff - 3000,
            market_features={"volatility": 2.6, "trend_strength": 1.8},
            current_risk_state={"drawdown": 0.03, "volatility": 2.6, "order_count": 2},
            as_of_cutoff=as_of_cutoff,
        )
        self.assertEqual(sig2.final_action, "ABSTAIN")
        self.assertFalse(sig2.safety_decision.allowed)
        self.assertIn("volatility", sig2.safety_decision.reason)

        # Step 4: Tick 3 — High Drawdown -> CSK Veto ABSTAIN
        sig3 = self.brain.process_tick(
            symbol="BTCUSDT",
            timestamp=as_of_cutoff - 2000,
            market_features={"volatility": 1.2, "trend_strength": 1.4},
            current_risk_state={"drawdown": 0.15, "volatility": 1.2, "order_count": 3},  # > 0.12 limit
            as_of_cutoff=as_of_cutoff,
        )
        self.assertEqual(sig3.final_action, "ABSTAIN")
        self.assertFalse(sig3.safety_decision.allowed)
        self.assertIn("drawdown", sig3.safety_decision.reason)

        # Step 5: Tick 4 — Emergency Kill Switch Triggered -> EMERGENCY_FLAT
        sig4 = self.brain.process_tick(
            symbol="BTCUSDT",
            timestamp=as_of_cutoff - 1000,
            market_features={"volatility": 1.0, "trend_strength": 1.2},
            current_risk_state={"drawdown": 0.01, "volatility": 1.0, "order_count": 0},
            as_of_cutoff=as_of_cutoff,
            emergency_signal=True,
        )
        self.assertEqual(sig4.final_action, "EMERGENCY_FLAT")
        self.assertFalse(sig4.safety_decision.allowed)
        self.assertEqual(sig4.safety_decision.clamped_size, 0.0)

        # Step 6: Verify EventStore Audit Trail on "operational_signals"
        head = self.store.get_head(OperationalBrain.STREAM_ID)
        self.assertIsNotNone(head)
        self.assertEqual(head[0], 4)  # 4 operational events recorded


if __name__ == "__main__":
    unittest.main()
