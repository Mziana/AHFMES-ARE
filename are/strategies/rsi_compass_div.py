"""
RSI Compass + Divergence Scalper
Exact rules from user:
  1. RSI(14, Close)
  2. H1 RSI > 50 = Bullish, < 50 = Bearish
  3. M5 Buy: RSI crosses UP through 30
  4. M5 Sell: RSI crosses DOWN through 70
  5. Bullish divergence: price lower low + RSI higher low
  6. Bearish divergence: price higher high + RSI lower high
"""
from __future__ import annotations
import polars as pl


def compute_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower_bound=0.0)
    loss = (-delta).clip(lower_bound=0.0)
    avg_gain = gain.ewm_mean(span=period, adjust=False)
    avg_loss = loss.ewm_mean(span=period, adjust=False)
    rs = avg_gain / avg_loss.replace(0.0, 1e-10)
    return 100.0 - (100.0 / (1.0 + rs))


def detect_divergence(price, rsi, lookback=20, min_swing_pct=1.0):
    """Detect bullish/bearish divergence."""
    n = len(price)
    result = [0.0] * n
    pv = price.to_list()
    rv = rsi.to_list()
    for i in range(lookback, n):
        wp = pv[i-lookback:i+1]
        wr = rv[i-lookback:i+1]
        pc = [x for x in wp if x is not None]
        rc = [x for x in wr if x is not None]
        if len(pc) < 10 or len(rc) < 10:
            continue
        h = len(pc) // 2
        ppl, cpl = min(pc[:h]), min(pc[h:])
        prl, crl = min(rc[:h]), min(rc[h:])
        # Bullish divergence: price lower low, RSI higher low
        if cpl < ppl and crl > prl and abs(cpl - ppl) / ppl * 100 > min_swing_pct:
            result[i] = 1.0
        pph, cph = max(pc[:h]), max(pc[h:])
        prh, crh = max(rc[:h]), max(rc[h:])
        # Bearish divergence: price higher high, RSI lower high
        if cph > pph and crh < prh and abs(cph - pph) / pph * 100 > min_swing_pct:
            result[i] = -1.0
    return pl.Series("divergence", result)


def rsi_compass_divergence_strategy(
    rsi_period=14,
    rsi_oversold=30,
    rsi_overbought=70,
    tp_pips=400.0,
    sl_pips=300.0,
    max_hold_bars=36,
    divergence_lookback=20,
    divergence_min_swing=1.0,
):
    def strategy(df):
        result = df.clone()
        price_col = "price" if "price" in result.columns else "close"

        # Step 1: Compute M5 RSI
        result = result.with_columns(compute_rsi(pl.col(price_col), rsi_period).alias("rsi_m5"))
        result = result.with_columns(pl.col("rsi_m5").shift(1).alias("rsi_m5_prev"))

        # Step 2: Compute H1 RSI from M5 data (resample)
        # Group every 12 M5 bars = 1 H1 bar, compute RSI on H1 close
        # Then map H1 RSI back to each M5 bar
        result = result.with_columns(pl.col("timestamp").alias("ts"))
        # Create H1 group: timestamp // 3600
        result = result.with_columns((pl.col("ts") // 3600).alias("h1_group"))

        # Compute H1 close as the last M5 close in each H1 group
        h1_close = result.group_by("h1_group").agg(
            pl.col(price_col).last().alias("h1_close"),
        ).sort("h1_group")

        # Compute RSI on H1 closes
        h1_close = h1_close.with_columns(compute_rsi(pl.col("h1_close"), rsi_period).alias("rsi_h1"))
        h1_close = h1_close.with_columns(pl.col("rsi_h1").shift(1).alias("rsi_h1_prev"))

        # Map H1 RSI back to M5 bars
        result = result.join(h1_close.select(["h1_group", "rsi_h1"]), on="h1_group", how="left")

        # Step 3: H1 Trend Direction
        result = result.with_columns(
            pl.when(pl.col("rsi_h1") > 50).then(1.0)
            .when(pl.col("rsi_h1") < 50).then(-1.0)
            .otherwise(0.0).alias("h1_trend")
        )

        # Step 4: M5 Entry Signals
        # Buy: RSI M5 crosses UP through 30 (was below 30, now above 30)
        result = result.with_columns(
            pl.when(
                (pl.col("rsi_m5_prev") < rsi_oversold) &
                (pl.col("rsi_m5") >= rsi_oversold)
            ).then(1.0).otherwise(0.0).alias("cross_up_30")
        )

        # Sell: RSI M5 crosses DOWN through 70 (was above 70, now below 70)
        result = result.with_columns(
            pl.when(
                (pl.col("rsi_m5_prev") > rsi_overbought) &
                (pl.col("rsi_m5") <= rsi_overbought)
            ).then(-1.0).otherwise(0.0).alias("cross_down_70")
        )

        # Step 5: Divergence Detection
        result = result.with_columns(
            detect_divergence(result[price_col], result["rsi_m5"], divergence_lookback, divergence_min_swing).alias("divergence")
        )

        # Step 6: Combine Entry Signals
        # Buy: cross_up_30 AND H1 bullish AND (divergence bullish OR no divergence needed)
        result = result.with_columns(
            pl.when(
                (pl.col("cross_up_30") > 0) &
                (pl.col("h1_trend") > 0)
            ).then(1.0)
            .when(
                (pl.col("divergence") > 0) &
                (pl.col("h1_trend") > 0)
            ).then(1.0)
            .otherwise(0.0).alias("raw_buy")
        )

        # Sell: cross_down_70 AND H1 bearish AND (divergence bearish OR no divergence needed)
        result = result.with_columns(
            pl.when(
                (pl.col("cross_down_70") < 0) &
                (pl.col("h1_trend") < 0)
            ).then(-1.0)
            .when(
                (pl.col("divergence") < 0) &
                (pl.col("h1_trend") < 0)
            ).then(-1.0)
            .otherwise(0.0).alias("raw_sell")
        )

        # Final signal
        result = result.with_columns(
            pl.when(pl.col("raw_buy") > 0).then(1.0)
            .when(pl.col("raw_sell") < 0).then(-1.0)
            .otherwise(0.0).alias("entry_signal")
        )

        # Step 7: Position Tracking
        prices = result[price_col].to_list()
        entry_sigs = result["entry_signal"].to_list()
        n = len(result)
        pip_val = 0.01
        pos = [0.0] * n
        ep = [0.0] * n
        bh = [0] * n

        for i in range(1, n):
            p = prices[i]
            if p is None:
                pos[i] = pos[i-1]
                ep[i] = ep[i-1]
                bh[i] = bh[i-1] + 1 if pos[i-1] != 0 else 0
                continue

            if pos[i-1] == 0.0:  # Flat
                if entry_sigs[i] > 0:
                    pos[i] = 1.0; ep[i] = p; bh[i] = 0
                elif entry_sigs[i] < 0:
                    pos[i] = -1.0; ep[i] = p; bh[i] = 0
                else:
                    pos[i] = 0.0; ep[i] = 0.0; bh[i] = 0
            else:  # In position
                bh[i] = bh[i-1] + 1
                e = ep[i-1]
                if pos[i-1] > 0:  # Long
                    pnl = (p - e) / pip_val
                    if pnl >= tp_pips or pnl <= -sl_pips or bh[i] >= max_hold_bars:
                        pos[i] = 0.0; ep[i] = 0.0
                    else:
                        pos[i] = 1.0; ep[i] = e
                else:  # Short
                    pnl = (e - p) / pip_val
                    if pnl >= tp_pips or pnl <= -sl_pips or bh[i] >= max_hold_bars:
                        pos[i] = 0.0; ep[i] = 0.0
                    else:
                        pos[i] = -1.0; ep[i] = e

        result = result.with_columns(pl.Series("signal", pos))
        return result

    return strategy

