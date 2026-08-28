"""
Unit Tests for AHFMES P001 Alpha Hypothesis Generator (ACC-512)
"""

import unittest

from are.alpha_generator import AlphaGenerator, AlphaHypothesisSpec


class TestP001AlphaGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = AlphaGenerator()

    def test_generate_hypotheses_structure(self):
        hyps = self.generator.generate_hypotheses("BTCUSDT", count=6)
        self.assertEqual(len(hyps), 6)

        families = set(h.family for h in hyps)
        self.assertTrue("MOMENTUM" in families)
        self.assertTrue("MEAN_REVERSION" in families)
        self.assertTrue("ORDERBOOK_IMBALANCE" in families)

        for h in hyps:
            self.assertTrue(len(h.spec_hash) > 0)
            self.assertIn("BTCUSDT", h.hypothesis_id)

    def test_evaluate_momentum_signal(self):
        hyps = self.generator.generate_hypotheses("BTCUSDT", family="MOMENTUM", count=1)
        hyp = hyps[0]

        # Strong upward crossover
        feats = {"crossover_diff": 0.05, "price_velocity": 0.02}
        sig = self.generator.evaluate_alpha_signal(hyp, feats)
        self.assertEqual(sig["action"], "BUY")
        self.assertTrue(sig["confidence"] > 0.6)

    def test_evaluate_mean_reversion_signal(self):
        hyps = self.generator.generate_hypotheses("ETHUSDT", family="MEAN_REVERSION", count=1)
        hyp = hyps[0]

        # Extreme high zscore -> SELL signal
        feats = {"zscore": 2.5}
        sig = self.generator.evaluate_alpha_signal(hyp, feats)
        self.assertEqual(sig["action"], "SELL")
        self.assertTrue(sig["confidence"] > 0.6)

    def test_evaluate_orderbook_imbalance_signal(self):
        hyps = self.generator.generate_hypotheses("SOLUSDT", family="ORDERBOOK_IMBALANCE", count=1)
        hyp = hyps[0]

        # Extreme positive imbalance -> BUY signal
        feats = {"imbalance_ratio": 0.6}
        sig = self.generator.evaluate_alpha_signal(hyp, feats)
        self.assertEqual(sig["action"], "BUY")
        self.assertTrue(sig["confidence"] > 0.6)


if __name__ == "__main__":
    unittest.main()
