"""
Unit Tests for AHFMES MT5 Market Feed (ACC-601, ACC-602)
"""

import unittest

from are.features import MarketFeatureExtractor
from are.mt5_feed import MT5FeedConfig, MT5MarketFeed, MT5MockFeed


class TestMT5Feed(unittest.TestCase):
    def test_mock_feed_generation(self):
        feed = MT5MockFeed(base_price=60000.0)
        self.assertTrue(feed.initialize())

        ticks = feed.get_latest_ticks("BTCUSD", count=10)
        self.assertEqual(len(ticks), 10)
        for t in ticks:
            self.assertIn("bid", t)
            self.assertIn("ask", t)
            self.assertIn("volume", t)
            self.assertTrue(t["ask"] >= t["bid"])

        bars = feed.get_latest_bars("BTCUSD", count=15)
        self.assertEqual(len(bars), 15)
        for b in bars:
            self.assertIn("open", b)
            self.assertIn("high", b)
            self.assertIn("low", b)
            self.assertIn("close", b)
            self.assertTrue(b["high"] >= b["low"])

        feed.shutdown()

    def test_market_feed_integration_with_feature_extractor(self):
        feed = MT5MarketFeed(MT5FeedConfig(use_mock=True, symbol="ETHUSD"))
        self.assertTrue(feed.initialize())

        ticks = feed.get_latest_ticks("ETHUSD", count=25)
        self.assertEqual(len(ticks), 25)

        extractor = MarketFeatureExtractor()
        features = extractor.extract_features(ticks)

        self.assertIn("realized_volatility", features)
        self.assertIn("imbalance_ratio", features)
        self.assertIn("trend_strength", features)

        feed.shutdown()


if __name__ == "__main__":
    unittest.main()
