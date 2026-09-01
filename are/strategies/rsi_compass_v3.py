"""
RSI Compass Strategy v3 — With TP/SL and Better Exit Logic

Improvements over v2:
1. ATR-based TP/SL (adaptive to volatility)
2. Trailing stop to lock profits
3. RSI exit at opposite extreme (not just compass cross)
4. Volume confirmation (optional)
"""
from __future__ import annotations
import polars as pl


def compute_rsi(close: pl.Series, period: int = 14) -> pl.Series:
    delta = close.diff()
    gain = delta.clip(lower_bound=0.0)
    loss = (-delta).clip(lower_bound=0.0)
    avg_gain = gain.ewm_mean(span=period, adjust=False)
    avg_loss = loss.ewm_mean(span=period, adjust=False)
    rs = avg_gain / avg_loss.replace(0.0, 1e-10)
    return 100.0 - (100.0 / (1.0 + rs))


def compute_atr(high: pl.Series, low: pl.Series, close: pl.Series, period: int = 14) -> pl.Series:
    """Average True Range for volatility-adaptive TP/SL."""
    prev_close = close.shift(1)
    tr = pl.max([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ])
    return tr.rolling_mean(window_size=period)


def detect_divergence(
    price: pl.Series, rsi: pl.Series,
    lookback: int = 30, min_swing_pct: float = 1.0,
) -> pl.Series:
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
        if cpl < ppl and crl > prl and abs(cpl - ppl) / ppl * 100 > min_swing_pct:
            result[i] = 1.0
        pph, cph = max(pc[:h]), max(pc[h:])
        prh, crh = max(rc[:h]), max(rc[h:])
        if cph > pph and crh < prh and abs(cph - pph) / pph * 100 > min_swing_pct:
            result[i] = -1.0
    return pl.Series("divergence", result)


def rsi_compass_strategy(
    rsi_period: int = 14,
    rsi_oversold: float = 30.0,
    rsi_overbought: float = 70.0,
    rsi_compass_level: float = 50.0,
    cooldown_bars: int = 12,
    min_hold_bars: int = 6,
    atr_period: int = 14,
    atr_sl_mult: float = 1.5,     # Stop loss = 1.5x ATR
    atr_tp_mult: float = 3.0,     # Take profit = 3.0x ATR (2:1 RR)
    trailing_atr_mult: float = 2.0,  # Trailing stop = 2x ATR
) -> pl.DataFrame:
    def strategy(df: pl.DataFrame) -> pl.DataFrame:
        result = df.clone()
        price_col = "price" if "price" in result.columns else "close"
        
        # Compute indicators
        result = result.with_columns([
            compute_rsi(pl.col(price_col), rsi_period).alias("rsi"),
            compute_atr(pl.col("high"), pl.col("low"), pl.col(price_col), atr_period).alias("atr"),
        ])
        
        # Compass
        result = result.with_columns(
            pl.when(pl.col("rsi") > rsi_compass_level).then(1.0)
            .when(pl.col("rsi") < rsi_compass_level).then(-1.0)
            .otherwise(0.0).alias("compass")
        )
        
        result = result.with_columns(pl.col("rsi").shift(1).alias("rsi_prev"))
        
        # Divergence
        result = result.with_columns(
            detect_divergence(result[price_col], result["rsi"], 30, 1.0).alias("divergence")
        )
        
        # Entry signals
        result = result.with_columns([
            pl.when(
                (pl.col("rsi_prev") < rsi_oversold) &
                (pl.col("rsi") >= rsi_oversold) &
                (pl.col("compass") > 0.0)
            ).then(1.0)
            .when(pl.col("divergence") == 1.0).then(1.0)
            .otherwise(0.0).alias("raw_buy"),
            
            pl.when(
                (pl.col("rsi_prev") > rsi_overbought) &
                (pl.col("rsi") <= rsi_overbought) &
                (pl.col("compass") < 0.0)
            ).then(-1.0)
            .when(pl.col("divergence") == -1.0).then(-1.0)
            .otherwise(0.0).alias("raw_sell"),
        ])
        
        # Position tracking with TP/SL
        prices = result[price_col].to_list()
        atrs = result["atr"].to_list()
        raw_buys = result["raw_buy"].to_list()
        raw_sells = result["raw_sell"].to_list()
        n = len(result)
        
        position = [0.0] * n
        entry_price = [0.0] * n
        stop_loss = [0.0] * n
        take_profit = [0.0] * n
        trailing_stop = [0.0] * n
        last_entry_bar = [-cooldown_bars - 1] * n
        
        for i in range(1, n):
            bars_since = i - last_entry_bar[i-1]
            atr_val = atrs[i] if atrs[i] is not None else 0.0
            
            if position[i-1] == 0.0:  # Flat
                if bars_since >= cooldown_bars and atr_val > 0:
                    if raw_buys[i] > 0.0:
                        position[i] = 1.0
                        entry_price[i] = prices[i]
                        stop_loss[i] = prices[i] - atr_val * atr_sl_mult
                        take_profit[i] = prices[i] + atr_val * atr_tp_mult
                        trailing_stop[i] = prices[i] - atr_val * trailing_atr_mult
                        last_entry_bar[i] = i
                    elif raw_sells[i] < 0.0:
                        position[i] = -1.0
                        entry_price[i] = prices[i]
                        stop_loss[i] = prices[i] + atr_val * atr_sl_mult
                        take_profit[i] = prices[i] - atr_val * atr_tp_mult
                        trailing_stop[i] = prices[i] + atr_val * trailing_atr_mult
                        last_entry_bar[i] = i
                    else:
                        position[i] = 0.0
                        last_entry_bar[i] = last_entry_bar[i-1]
                else:
                    position[i] = 0.0
                    last_entry_bar[i] = last_entry_bar[i-1]
            else:  # In position
                if bars_since >= min_hold_bars:
                    price = prices[i]
                    
                    if position[i-1] > 0:  # Long
                        # Update trailing stop
                        new_trail = price - atr_val * trailing_atr_mult
                        if new_trail > trailing_stop[i-1]:
                            trailing_stop[i] = new_trail
                        else:
                            trailing_stop[i] = trailing_stop[i-1]
                        
                        # Check exits: TP, SL, trailing, or RSI exit
                        rsi_exit = (result["rsi"].to_list()[i] > rsi_overbought)
                        if (price >= take_profit[i-1] or 
                            price <= stop_loss[i-1] or 
                            price <= trailing_stop[i] or
                            rsi_exit):
                            position[i] = 0.0
                        else:
                            position[i] = 1.0
                    else:  # Short
                        new_trail = price + atr_val * trailing_atr_mult
                        if new_trail < trailing_stop[i-1]:
                            trailing_stop[i] = new_trail
                        else:
                            trailing_stop[i] = trailing_stop[i-1]
                        
                        rsi_exit = (result["rsi"].to_list()[i] < rsi_oversold)
                        if (price <= take_profit[i-1] or 
                            price >= stop_loss[i-1] or 
                            price >= trailing_stop[i] or
                            rsi_exit):
                            position[i] = 0.0
                        else:
                            position[i] = -1.0
                    
                    entry_price[i] = entry_price[i-1]
                    stop_loss[i] = stop_loss[i-1]
                    take_profit[i] = take_profit[i-1]
                    last_entry_bar[i] = last_entry_bar[i-1]
                else:
                    position[i] = position[i-1]
                    entry_price[i] = entry_price[i-1]
                    stop_loss[i] = stop_loss[i-1]
                    t
