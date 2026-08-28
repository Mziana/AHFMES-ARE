"""
Unit Tests for AHFMES P001 Quantitative Feature Library (ACC-511)
"""

import math
import unittest

from are.features import (
    MarketFeatureExtractor,
    calculate_mean_reversion_zscore,
    calculate_momentum_indicators,
    calculate_orderbook_imbalance,
    calculate_realized_volatility,
)


class TestP001Features(unittest.TestCase):
    def test_orderbook_imbalance_calculation(self):
        # Balanced book
        bids = [(100.0, 10.0), (99.5, 5.0)]
        asks = [(100.5, 10.0), (101.0, 5.0)]
        res = calculate_orderbook_imbalance(bids, asks)
        self.assertEqual(res["imbalance_ratio"], 0.0)
        self.assertEqual(res["spread"], 0.5)
        self.assertEqual(res["mid_price"], 100.25)

        # Heavy bid side
        bids_heavy = [(100.0, 30.0)]
        asks_light = [(100.5, 10.0)]
        res_heavy = calculate_orderbook_imbalance(bids_heavy, asks_light)
        self.assertAlmostEqual(res_heavy["imbalance_ratio"], 0.5)

    def test_realized_volatility_calculation(self):
        # Constant prices -> 0 vol
        const_prices = [100.0] * 25
        self.assertEqual(calculate_realized_volatility(const_prices), 0.0)

        # Oscillating prices -> positive vol
        osc_prices = [100.0, 105.0, 95.0, 102.0, 98.0, 104.0, 96.0]
        vol = calculate_realized_volatility(osc_prices)
        self.assertTrue(vol > 0.0)

    def test_momentum_indicators(self):
        # Upward trend
        up_prices = [100.0 + i for i in range(30)]
        mom = calculate_momentum_indicators(up_prices)
        self.assertTrue(mom["crossover_diff"] > 0.0)
        self.assertTrue(mom["price_velocity"] > 0.0)

    def test_mean_reversion_zscore(self):
        prices = [100.0] * 20 + [110.0]  # Sudden spike
        zscore = calculate_mean_reversion_zscore(prices)
        self.assertTrue(zscore > 2.0)

    def test_market_feature_extractor_pipeline(self):
        extractor = MarketFeatureExtractor()
        snapshots = [
            {
                "price": 100.0 + (i * 0.5),
                "bids": [(100.0 + (i * 0.5) - 0.1, 10.0)],
                "asks": [(100.0 + (i * 0.5) + 0.1, 8.0)],
            }
            for i in range(25)
        ]
        feats = extractor.extract_features(snapshots)
        self.assertIn("imbalance_ratio", feats)
        self.assertIn("realized_volatility", feats)
        self.assertIn("trend_strength", feats)
        self.assertIn("zscore", feats)


if __name__ == "__main__":
    unittest.main()
