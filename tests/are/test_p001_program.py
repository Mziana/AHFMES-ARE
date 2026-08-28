"""
End-to-End Tests for AHFMES P001 Autonomous Research Program (ACC-514, ACC-515)
"""

import os
import tempfile
import unittest

from are.coordinator import AgentAssignment
from are.p001_program import P001ProgramRunner


class TestP001Program(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "p001_prog_test.db")
        self.runner = P001ProgramRunner(self.db_path)
        self.assignment = AgentAssignment(
            discovery_agent="P001_Discovery_Agent",
            validation_agent="P001_Validation_Agent",
            governor_agent="P001_Governor_Agent",
        )

    def tearDown(self):
        self.runner.close()
        self.tmp_dir.cleanup()

    def test_full_p001_program_discovery_and_champion_promotion(self):
        # 1. Prepare raw market ticks
        raw_ticks = [
            {
                "symbol": "BTCUSDT",
                "timestamp": 1728000000.0 + (i * 10),
                "price": 60000.0 + (i * 25.0),
                "volume": 2.0,
                "side": "BUY",
                "bid": 59999.0 + (i * 25.0),
                "ask": 60001.0 + (i * 25.0),
                "bid_size": 3.0,
                "ask_size": 2.0,
                "bids": [(59999.0 + (i * 25.0), 3.0)],
                "asks": [(60001.0 + (i * 25.0), 2.0)],
            }
            for i in range(25)
        ]

        holdout_ticks = [
            {
                "symbol": "BTCUSDT",
                "timestamp": 1728000300.0 + (i * 10),
                "price": 60625.0 + (i * 10.0),
                "volume": 1.5,
            }
            for i in range(10)
        ]

        # 2. Run Program
        res = self.runner.run_program(
            symbol="BTCUSDT",
            raw_market_ticks=raw_ticks,
            holdout_ticks=holdout_ticks,
            assignment=self.assignment,
        )

        self.assertEqual(res["symbol"], "BTCUSDT")
        self.assertEqual(res["program_status"], "SUCCESS")
        self.assertIsNotNone(res["promoted_champion"])

        # 3. Verify Active Champion in Registry
        active_champ = self.runner.champion_registry.get_active_champion()
        self.assertIsNotNone(active_champ)
        self.assertEqual(active_champ.champion_id, res["promoted_champion"]["champion_id"])
        self.assertEqual(active_champ.status, "ACTIVE")


if __name__ == "__main__":
    unittest.main()
