"""
Unit Tests for AHFMES P001 Terminal Dashboard (ACC-501, ACC-504)
"""

import json
import os
import tempfile
import unittest

from are.champion import ChampionRegistry
from are.dashboard import TerminalDashboard, format_dashboard
from are.governor import PromotionDisposition
from are.safety import CapitalSafetyKernel, SafetyLimits
from are.storage import EventStore


class TestP001Dashboard(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "dashboard_test.db")
        self.store = EventStore(self.db_path)
        self.champ_reg = ChampionRegistry(self.store)
        self.limits = SafetyLimits(max_drawdown_pct=0.12, volatility_cutoff=2.2, kill_switch_active=False)
        self.safety_kernel = CapitalSafetyKernel(self.limits)
        self.dashboard = TerminalDashboard()

    def tearDown(self):
        self.store.close()
        self.tmp_dir.cleanup()

    def test_format_dashboard_text_structure(self):
        champ_info = {
            "champion_id": "CHAMP_TEST_001",
            "candidate_id": "CAND_TEST_001",
            "status": "ACTIVE",
            "activated_at": 1728000000.0,
        }
        safety_info = {
            "kill_switch_active": False,
            "max_drawdown_pct": 0.15,
            "volatility_cutoff": 2.5,
            "max_order_rate_per_min": 10,
        }
        stream_stats = {
            "total_ticks": 100,
            "veto_count": 5,
            "chain_health": "VERIFIED (OK)",
        }

        rendered = format_dashboard(champ_info, safety_info, stream_stats, is_live_mode=True)
        self.assertIn("AHFMES-ARE RECURSIVE AUTONOMOUS ENGINE", rendered)
        self.assertIn("CHAMP_TEST_001", rendered)
        self.assertIn("CAND_TEST_001", rendered)
        self.assertIn("15.0%", rendered)
        self.assertIn("100", rendered)
        self.assertIn("5.0%", rendered)

    def test_terminal_dashboard_render_with_live_store(self):
        # 1. Promote a champion
        disp = PromotionDisposition(
            candidate_id="CAND_DASH_01",
            champion_id="GENESIS",
            decision="PROMOTED",
            rationale="Dashboard Test",
            governor_signature="GOV_SIG_DASH",
            timestamp=1728000000.0,
        )
        self.champ_reg.promote_champion("CAND_DASH_01", disp)

        # 2. Add some operational events
        for i in range(10):
            ev = {
                "symbol": "BTCUSDT",
                "final_action": "BUY" if i % 3 != 0 else "ABSTAIN",
                "safety_decision": {"allowed": i % 3 != 0},
                "timestamp": 1728000000.0 + i,
            }
            head = self.store.get_head("operational_signals")
            exp_rev = 0 if head is None else head[0]
            prev_h = "0" * 64 if head is None else head[1]
            self.store.append_event("operational_signals", json.dumps(ev).encode("utf-8"), exp_rev, prev_h)

        rendered = self.dashboard.render(self.champ_reg, self.safety_kernel, self.store)
        self.assertIn("CAND_DASH_01", rendered)
        self.assertIn("Operational Ticks: 10", rendered)
        self.assertIn("VERIFIED (OK)", rendered)


if __name__ == "__main__":
    unittest.main()
