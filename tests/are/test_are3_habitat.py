"""
Unit Tests for AHFMES ARE-3 Habitat Adapter & Condition Atlas (ACC-315, ACC-316)
"""

import os
import tempfile
import unittest

from are.habitat import ConditionAtlas, HabitatAdapter, MarketStateObservation
from are.storage import EventStore


class TestHabitatAdapter(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "habitat_test.db")
        self.store = EventStore(self.db_path)
        self.atlas = ConditionAtlas()
        self.adapter = HabitatAdapter(self.atlas, self.store)

    def tearDown(self):
        self.store.close()
        self.tmp_dir.cleanup()

    def test_condition_atlas_regime_classification(self):
        # Volatility Expansion
        r1 = self.atlas.classify_regime({"volatility": 2.0, "trend_strength": 0.5})
        self.assertEqual(r1, "VOLATILITY_EXPANSION")

        # Trending Expansion
        r2 = self.atlas.classify_regime({"volatility": 1.0, "trend_strength": 1.5})
        self.assertEqual(r2, "TRENDING_EXPANSION")

        # Range Compression
        r3 = self.atlas.classify_regime({"volatility": 0.8, "trend_strength": 0.2, "range_span": 0.3})
        self.assertEqual(r3, "RANGE_COMPRESSION")

        # Regime Transition
        r4 = self.atlas.classify_regime({"volatility": 1.0, "trend_strength": 0.5, "range_span": 0.8})
        self.assertEqual(r4, "REGIME_TRANSITION")

    def test_information_time_violation_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.adapter.ingest_market_state(
                symbol="BTCUSDT",
                timestamp=1050.0,
                features={"volatility": 1.2},
                as_of_cutoff=1000.0,  # 1050 > 1000 => leak
            )
        self.assertIn("Information-Time violation", str(ctx.exception))

    def test_valid_market_state_ingestion(self):
        obs = self.adapter.ingest_market_state(
            symbol="ETHUSDT",
            timestamp=950.0,
            features={"volatility": 1.8, "trend_strength": 0.4},
            as_of_cutoff=1000.0,
        )
        self.assertIsInstance(obs, MarketStateObservation)
        self.assertEqual(obs.symbol, "ETHUSDT")
        self.assertEqual(obs.regime, "VOLATILITY_EXPANSION")
        self.assertTrue(len(obs.observation_hash) > 0)

        # Verify persisted in EventStore stream
        head = self.store.get_head("market_state:ETHUSDT")
        self.assertIsNotNone(head)
        self.assertEqual(head[0], 1)


if __name__ == "__main__":
    unittest.main()
