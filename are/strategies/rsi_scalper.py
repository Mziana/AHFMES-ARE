"""
RSI Scalper Strategy — Match Manual Trading Behavior

Target: 6-10 trades/day on M5 (matches manual RSI 25/75 scalping)
Rules:
1. RSI(14, Close) with levels 25/75 (tighter than standard 30/70)
2. Buy: RSI crosses above 25 (recovery from oversold)
3. Sell: RSI crosses below 75 (recovery from overbought)
4. Exit: Fixed TP/SL in pips (scalping targets)
5. No cooldown — let the market decide
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


def rsi_scalper_strategy(
    rsi_period: int = 14,
    rsi_oversold: float = 25.0,
    rsi_overbought: float = 75.0,
    tp_pips: float = 30.0,        # Take profit: 30 pips ($3 for XAUUSD)
    sl_pips: float = 15.0,        # Stop loss: 15 pips ($1.5 for XAUUSD)
    max_hold_bars: int = 12,      # Max hold: 1 hour (12 x 5min)
    compass_filter: bool = True,   # Use RSI 50 as trend filter
) -> pl.DataFrame:
    """RSI Scalper — match manual 6-10 trades/day behavior."""
    def strategy(df: pl.DataFrame) -> pl.DataFrame:
        result = df.clone()
        price_col = "price" if "price" in result.columns else "close"
        
        # Compute RSI
        result = result.with_columns(
            compute_rsi(pl.col(price_col), rsi_period).alias("rsi")
        )
        
        # Previous RSI for crossover
        result = result.with_columns(pl.col("rsi").shift(1).alias("rsi_prev"))
        
        # Compass: RSI > 50 = bullish bias, < 50 = bearish bias
        result = result.with_columns(
            pl.when(pl.col("rsi") > 50.0).then(1.0)
            .when(pl.col("rsi") < 50.0).then(-1.0)
            .otherwise(0.0).alias("compass")
        )
        
        # Raw entry signals
        result = result.with_columns([
            # Buy: RSI crosses UP through oversold
            pl.when(
                (pl.col("rsi_prev") < rsi_oversold) &
                (pl.col("rsi") >= rsi_oversold)
            ).then(1.0).otherwise(0.0).alias("raw_buy"),
            
            # Sell: RSI crosses DOWN through overbought
            pl.when(
                (pl.col("rsi_prev") > rsi_overbought) &
                (pl.col("rsi") <= rsi_overbought)
            ).then(-1.0).otherwise(0.0).alias("raw_sell"),
        ])
        
        # Position tracking with TP/SL
        prices = result[price_col].to_list()
        raw_buys = result["raw_buy"].to_list()
        raw_sells = result["raw_sell"].to_list()
        compass_vals = result["compass"].to_list()
        n = len(result)
        
        position = [0.0] * n
        entry_price = [0.0] * n
        bars_held = [0] * n
        
        # pip value for XAUUSD: 1 pip = $0.01 price move
        pip_value = 0.01
        
        for i in range(1, n):
            price = prices[i]
            if price is None:
                position[i] = position[i-1]
                entry_price[i] = entry_price[i-1]
                bars_held[i] = bars_held[i-1] + 1 if position[i-1] != 0 else 0
                continue
            
            if position[i-1] == 0.0:  # Flat — look for entry
                if raw_buys[i] > 0.0:
                    # Check compass filter
                    if not compass_filter or compass_vals[i] > 0.0:
                        position[i] = 1.0
                        entry_price[i] = price
                        bars_held[i] = 0
                    else:
                        position[i] = 0.0
                        entry_price[i] = 0.0
                        bars_held[i] = 0
                elif raw_sells[i] < 0.0:
                    if not compass_filter or compass_vals[i] < 0.0:
                        position[i] = -1.0
                        entry_price[i] = price
                        bars_held[i] = 0
                    else:
                        position[i] = 0.0
                        entry_price[i] = 0.0
                        bars_held[i] = 0
                else:
                    position[i] = 0.0
                    entry_price[i] = 0.0
                    bars_held[i] = 0
            
            else:  # In position — check exit
                bars_held[i] = bars_held[i-1] + 1
                ep = entry_price[i-1]
                
                if position[i-1] > 0:  # Long
                    pnl_pips = (price - ep) / pip_value
                    if (pnl_pips >= tp_pips or          # TP hit
                        pnl_pips <= -sl_pips or         # SL hit
                        bars_held[i] >= max_hold_bars): # Time exit
                        position[i] = 0.0
                        entry_price[i] = 0.0
                    else:
                        position[i] = 1.0
                        entry_price[i] = ep
                
                else:  # Short
                    pnl_pips = (ep - price) / pip_value
                    if (pnl_pips >= tp_pips or
                        pnl_pips <= -sl_pips or
                        bars_held[i] >= max_hold_bars):
                        position[i] = 0.0
                        entry_price[i] = 0.0
                    else:
                        position[i] = -1.0
                        entry_price[i] = ep
        
        result = result.with_columns(pl.Series("signal", position))
        return result
    
    return strategy
