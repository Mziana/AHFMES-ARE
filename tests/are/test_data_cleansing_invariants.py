"""
Data Cleansing & Gap-Alignment Invariant Tests (DELEGASI_029b, Anti-GIGO)
"""

import unittest
import polars as pl

from are.backtest import IsolatedBacktestEngine
from are.data_pipeline import (
    CrossedMarketError,
    DataChronologyError,
    DataPurifier,
)


class TestDataCleansingInvariants(unittest.TestCase):
    def setUp(self):
        self.purifier = DataPurifier()
        self.engine = IsolatedBacktestEngine()

    def test_no_linear_interpolation_bias(self):
        """
        Invariant 1: Micro-gaps (<1h) MUST use Forward Fill (LOCF), NEVER linear interpolation.
        """
        # Price at t=1000 is 100.0, price at t=1010 jumps to 110.0
        df = pl.DataFrame({
            "timestamp": [1000.0, 1001.0, 1002.0, 1010.0],
            "bid": [99.5, 99.5, None, 109.5],
            "ask": [100.5, 100.5, None, 110.5],
            "price": [100.0, 100.0, None, 110.0],
            "volume": [1.0, 1.0, 1.0, 1.0],
        })

        purified = self.purifier.purify_tick_data(df)

        # Row 2 (t=1002) should have price 100.0 (LOCF), NOT 103.33 (linear interpolation)
        self.assertEqual(purified["price"][2], 100.0)
        self.assertEqual(purified["bid"][2], 99.5)
        self.assertEqual(purified["ask"][2], 100.5)

    def test_macro_gap_preservation(self):
        """
        Invariant 2: Macro-gaps (>= 1 hour, e.g. 48h weekend) MUST be flagged as is_market_closed=True
        without generating fictitious prices.
        """
        # Friday close (t=0) to Sunday open (t=172800, 48 hours later)
        df = pl.DataFrame({
            "timestamp": [0.0, 60.0, 120.0, 172800.0, 172860.0],
            "bid": [100.0, 100.1, 100.2, 105.0, 105.1],
            "ask": [101.0, 101.1, 101.2, 106.0, 106.1],
            "volume": [10.0, 12.0, 11.0, 50.0, 45.0],
        })

        purified = self.purifier.purify_tick_data(df)

        # Row 3 (t=172800.0) is the start of post-gap bar
        self.assertTrue(purified["is_market_closed"][3])
        self.assertFalse(purified["is_market_closed"][0])
        self.assertFalse(purified["is_market_closed"][1])
        self.assertFalse(purified["is_market_closed"][4])

    def test_toxic_spread_neutralization(self):
        """
        Invariant 3: Spreads exceeding 3x MA MUST be tagged as is_toxic_spread=True,
        and IsolatedBacktestEngine MUST NOT execute trades on toxic ticks.
        """
        n = 120
        timestamps = [1000.0 + i * 60 for i in range(n)]
        bids = [100.0] * n
        asks = [101.0] * n  # Normal spread = 1.0

        # Inject toxic spread spike at index 105
        asks[105] = 110.0  # Spread = 10.0 (10x normal spread)

        df = pl.DataFrame({
            "timestamp": timestamps,
            "bid": bids,
            "ask": asks,
            "volume": [1.0] * n,
        })

        purified = self.purifier.purify_tick_data(df)

        # Index 105 must be toxic
        self.assertTrue(purified["is_toxic_spread"][105])
        self.assertFalse(purified["is_toxic_spread"][10])

        # Run backtest with custom strategy triggering Buy on index 105
        def toxic_trigger_strategy(data: pl.DataFrame) -> pl.DataFrame:
            return data.with_columns(
                pl.when(pl.col("timestamp") == timestamps[105])
                .then(pl.lit(1.0))
                .otherwise(pl.lit(0.0))
                .alias("signal")
            )

        result = self.engine.run_backtest(
            strategy_logic=toxic_trigger_strategy,
            historical_data=df,
        )

        # The toxic signal should have been suppressed to 0.0 (neutralized)
        trades = result.trade_log
        self.assertEqual(len(trades), 0, "Trade was erroneously executed on a toxic spread tick")

    def test_chronology_invariant(self):
        """
        Invariant 4: Decreasing timestamps (time-travel data feed anomaly) MUST raise DataChronologyError.
        """
        df = pl.DataFrame({
            "timestamp": [100.0, 101.0, 102.0, 103.0, 99.0, 105.0],  # 99.0 is backward
            "bid": [10.0, 10.0, 10.0, 10.0, 10.0, 10.0],
            "ask": [11.0, 11.0, 11.0, 11.0, 11.0, 11.0],
            "volume": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        })

        with self.assertRaises(DataChronologyError):
            self.purifier.purify_tick_data(df)

    def test_crossed_market_invariant(self):
        """
        Invariant 5: Crossed market feed (bid > ask) MUST raise CrossedMarketError.
        """
        df = pl.DataFrame({
            "timestamp": [100.0, 101.0, 102.0],
            "bid": [10.0, 12.0, 10.0],  # 12.0 > 11.0 is crossed
            "ask": [11.0, 11.0, 11.0],
            "volume": [1.0, 1.0, 1.0],
        })

        with self.assertRaises(CrossedMarketError):
            self.purifier.purify_tick_data(df)


if __name__ == "__main__":
    unittest.main()