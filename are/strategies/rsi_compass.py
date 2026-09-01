"""
RSI Compass Strategy v2 — Optimized for Low Trade Frequency

Key optimization: Reduce trades from ~23K to ~100-300 per 2 years.
Rules:
1. RSI(14, Close) compass — level 50 = trend direction
2. Entry: RSI crosses back from oversold/overbought (recovery, not knife-catching)
3. Divergence: Strongest signal — price vs RSI divergence
4. Cooldown: Minimum bars between entries to prevent overtrading
5. Exit: RSI crosses compass level (50) in opposite direction

Signal output: 1.0 (buy), -1.0 (sell), 0.0 (flat)
"""
from __future__ import annotations
import polars as pl


def compute_rsi(close: pl.Series, period: int = 14) -> pl.Series:
    """Compute RSI using Wilder's smoothing method."""
    delta = close.diff()
    gain = delta.clip(lower_bound=0.0)
    loss = (-delta).clip(lower_bound=0.0)
    avg_gain = gain.ewm_mean(span=period, adjust=False)
    avg_loss = loss.ewm_mean(span=period, adjust=False)
    rs = avg_gain / avg_loss.replace(0.0, 1e-10)
    return 100.0 - (100.0 / (1.0 + rs))


def detect_divergence(
    price: pl.Series,
    rsi: pl.Series,
    lookback: int = 30,
    min_swing_pct: float = 1.0,
) -> pl.Series:
    """Detect bullish/bearish divergence with wider lookback."""
    n = len(price)
    result = [0.0] * n
    price_vals = price.to_list()
    rsi_vals = rsi.to_list()
    
    for i in range(lookback, n):
        wp = price_vals[i-lookback:i+1]
        wr = rsi_vals[i-lookback:i+1]
        pc = [x for x in wp if x is not None]
        rc = [x for x in wr if x is not None]
        if len(pc) < 10 or len(rc) < 10:
            continue
        
        h = len(pc) // 2
        ppl, cpl = min(pc[:h]), min(pc[h:])
        prl, crl = min(rc[:h]), min(rc[h:])
        
        # Bullish divergence
        if cpl < ppl and crl > prl and abs(cpl - ppl) / ppl * 100 > min_swing_pct:
            result[i] = 1.0
        
        pph, cph = max(pc[:h]), max(pc[h:])
        prh, crh = max(rc[:h]), max(rc[h:])
        
        # Bearish divergence
        if cph > pph and crh < prh and abs(cph - pph) / pph * 100 > min_swing_pct:
            result[i] = -1.0
    
    return pl.Series("divergence", result)


def rsi_compass_strategy(
    rsi_period: int = 14,
    rsi_oversold: float = 30.0,
    rsi_overbought: float = 70.0,
    rsi_compass_level: float = 50.0,
    cooldown_bars: int = 12,        # Minimum 1 hour between entries (12 x 5min)
    min_hold_bars: int = 6,          # Hold position at least 30 min
    divergence_lookback: int = 30,
    divergence_min_swing: float = 1.0,
) -> pl.DataFrame:
    """Returns a strategy function with optimized trade frequency."""
    def strategy(df: pl.DataFrame) -> pl.DataFrame:
        result = df.clone()
        price_col = "price" if "price" in result.columns else "close"
        
        # 1. Compute RSI
        result = result.with_columns(
            compute_rsi(pl.col(price_col), rsi_period).alias("rsi")
        )
        
        # 2. RSI compass direction
        result = result.with_columns(
            pl.when(pl.col("rsi") > rsi_compass_level).then(1.0)
            .when(pl.col("rsi") < rsi_compass_level).then(-1.0)
            .otherwise(0.0).alias("compass")
        )
        
        # 3. Previous RSI for crossover detection
        result = result.with_columns(
            pl.col("rsi").shift(1).alias("rsi_prev")
        )
        
        # 4. Divergence detection
        price_s = result[price_col]
        rsi_s = result["rsi"]
        result = result.with_columns(
            detect_divergence(price_s, rsi_s, divergence_lookback, divergence_min_swing).alias("divergence")
        )
        
        # 5. Entry signals (only on specific conditions, not every bar)
        # Buy: RSI recovering from oversold zone
        # Sell: RSI recovering from overbought zone
        result = result.with_columns([
            # Buy signal: RSI crosses UP through oversold (recovery)
            pl.when(
                (pl.col("rsi_prev") < rsi_oversold) &    # Was oversold
                (pl.col("rsi") >= rsi_oversold) &         # Now recovered
                (pl.col("compass") > 0.0)                  # Compass confirms uptrend
            ).then(1.0)
            # Also: Strong divergence bullish
            .when(pl.col("divergence") == 1.0).then(1.0)
            .otherwise(0.0).alias("raw_buy"),
            
            # Sell signal: RSI crosses DOWN through overbought (recovery)
            pl.when(
                (pl.col("rsi_prev") > rsi_overbought) &   # Was overbought
                (pl.col("rsi") <= rsi_overbought) &        # Now recovered
                (pl.col("compass") < 0.0)                   # Compass confirms downtrend
            ).then(-1.0)
            # Also: Strong divergence bearish
            .when(pl.col("divergence") == -1.0).then(-1.0)
            .otherwise(0.0).alias("raw_sell"),
        ])
        
        # 6. Exit signal: RSI crosses compass level in opposite direction
        result = result.with_columns(
            pl.when(
                (pl.col("rsi_prev") > rsi_compass_level) &
                (pl.col("rsi") <= rsi_compass_level)
            ).then(-1.0)  # Exit long
            .when(
                (pl.col("rsi_prev") < rsi_compass_level) &
                (pl.col("rsi") >= rsi_compass_level)
            ).then(1.0)   # Exit short (go flat or reverse)
            .otherwise(0.0).alias("exit_signal")
        )
        
        # 7. Combine: entry + exit logic with position tracking
        # Use position column to track current state
        position = [0.0] * len(result)
        last_entry_bar = [-cooldown_bars - 1] * len(result)
        raw_buy = result["raw_buy"].to_list()
        raw_sell = result["raw_sell"].to_list()
        exit_sig = result["exit_signal"].to_list()
        
        for i in range(1, len(position)):
            bars_since_entry = i - last_entry_bar[i-1]
            
            if position[i-1] == 0.0:  # Flat — look for entry
                if bars_since_entry >= cooldown_bars:
                    if raw_buy[i] > 0.0:
                        position[i] = 1.0
                        last_entry_bar[i] = i
                    elif raw_sell[i] < 0.0:
                        position[i] = -1.0
                        last_entry_bar[i] = i
                    else:
                        position[i] = 0.0
                else:
                    position[i] = 0.0
            else:  # In position — look for exit
                if bars_since_entry >= min_hold_bars:
                    if (position[i-1] > 0 and exit_sig[i] < 0):
                        position[i] = 0.0  # Exit long
                    elif (position[i-1] < 0 and exit_sig[i] > 0):
                        position[i] = 0.0  # Exit short
                    else:
                        position[i] = position[i-1]
                else:
                    position[i] = position[i-1]  # Hold through min_hold
                last_entry_bar[i] = last_entry_bar[i-1]
        
        result = result.with_columns(
            pl.Series("signal", position)
        )
        
        return result
    
    return strategy
