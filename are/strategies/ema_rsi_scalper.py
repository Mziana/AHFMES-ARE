"""EMA + RSI Scalper based on real manual trading rules."""
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

def compute_ema(series, span):
    return series.ewm_mean(span=span, adjust=False)

def ema_rsi_scalper_strategy(
    ema_fast_period=6, ema_slow_period=30,
    rsi_period=14,
    rsi_bull_pullback_low=45.0, rsi_bull_pullback_high=60.0,
    rsi_bear_pullback_low=40.0, rsi_bear_pullback_high=55.0,
    tp_pips=400.0, sl_pips=300.0, max_hold_bars=36,
    use_volume_filter=True, use_session_filter=True,
):
    def strategy(df):
        result = df.clone()
        # Engine provides: timestamp, bid, ask, price, volume, spread
        # price = close price

        # 1. EMA TREND (use price = close)
        result = result.with_columns([
            compute_ema(pl.col("price"), ema_fast_period).alias("ema_fast"),
            compute_ema(pl.col("price"), ema_slow_period).alias("ema_slow"),
        ])
        result = result.with_columns(pl.when(pl.col("ema_fast") > pl.col("ema_slow")).then(1.0).when(pl.col("ema_fast") < pl.col("ema_slow")).then(-1.0).otherwise(0.0).alias("trend"))

        # 2. RSI
        result = result.with_columns(compute_rsi(pl.col("price"), rsi_period).alias("rsi"))
        result = result.with_columns(pl.col("rsi").shift(1).alias("rsi_prev"))

        # Bull entry: RSI pullback to zone in uptrend
        result = result.with_columns(pl.when((pl.col("trend") > 0) & (pl.col("rsi_prev") < rsi_bull_pullback_low) & (pl.col("rsi") >= rsi_bull_pullback_low) & (pl.col("rsi") <= rsi_bull_pullback_high)).then(1.0).when((pl.col("trend") > 0) & (pl.col("rsi_prev") < 50) & (pl.col("rsi") >= 50) & (pl.col("rsi") <= 60)).then(1.0).otherwise(0.0).alias("raw_buy"))

        # Bear entry: RSI pullback to zone in downtrend
        result = result.with_columns(pl.when((pl.col("trend") < 0) & (pl.col("rsi_prev") > rsi_bear_pullback_high) & (pl.col("rsi") <= rsi_bear_pullback_high) & (pl.col("rsi") >= rsi_bear_pullback_low)).then(-1.0).when((pl.col("trend") < 0) & (pl.col("rsi_prev") > 50) & (pl.col("rsi") <= 50) & (pl.col("rsi") >= 40)).then(-1.0).otherwise(0.0).alias("raw_sell"))

        # 3. VOLATILITY FILTER (use price rolling std as proxy for ATR)
        result = result.with_columns(pl.col("price").rolling_std(window_size=20).alias("vol"))
        result = result.with_columns((pl.col("vol") / pl.col("price") * 10000).alias("vol_bps"))
        vol_median = result["vol_bps"].median()
        result = result.with_columns(pl.when(pl.col("vol_bps") > vol_median * 0.5).then(1.0).otherwise(0.0).alias("vol_ok"))

        # 4. SESSION FILTER
        if use_session_filter:
            result = result.with_columns(((pl.col("timestamp") % 86400) // 3600).alias("hour_utc"))
            result = result.with_columns(pl.when(((pl.col("hour_utc") >= 7) & (pl.col("hour_utc") <= 16)) | ((pl.col("hour_utc") >= 13) & (pl.col("hour_utc") <= 22))).then(1.0).otherwise(0.0).alias("session_ok"))
        else:
            result = result.with_columns(pl.lit(1.0).alias("session_ok"))

        # 5. VOLUME FILTER
        if use_volume_filter and "volume" in result.columns:
            result = result.with_columns(pl.col("volume").rolling_mean(window_size=20).alias("vol_avg"))
            result = result.with_columns(pl.when(pl.col("volume") > pl.col("vol_avg") * 0.8).then(1.0).otherwise(0.0).alias("vol_confirm"))
        else:
            result = result.with_columns(pl.lit(1.0).alias("vol_confirm"))

        # 6. COMBINE
        result = result.with_columns((pl.col("vol_ok") + pl.col("session_ok") + pl.col("vol_confirm")).alias("filter_score"))
        result = result.with_columns(pl.when((pl.col("raw_buy") > 0) & (pl.col("filter_score") >= 2)).then(1.0).when((pl.col("raw_sell") < 0) & (pl.col("filter_score") >= 2)).then(-1.0).otherwise(0.0).alias("filtered_signal"))

        # 7. POSITION TRACKING
        prices = result["price"].to_list()
        sigs = result["filtered_signal"].to_list()
        trends = result["trend"].to_list()
        n = len(result)
        pip_val = 0.01
        pos = [0.0]*n; ep = [0.0]*n; bh = [0]*n
        for i in range(1, n):
            p = prices[i]
            if p is None:
                pos[i]=pos[i-1]; ep[i]=ep[i-1]; bh[i]=bh[i-1]+1 if pos[i-1]!=0 else 0; continue
            if pos[i-1] == 0:
                if sigs[i]>0: pos[i]=1.0; ep[i]=p; bh[i]=0
                elif sigs[i]<0: pos[i]=-1.0; ep[i]=p; bh[i]=0
                else: pos[i]=0; ep[i]=0; bh[i]=0
            else:
                bh[i]=bh[i-1]+1; e=ep[i-1]
                if pos[i-1]>0:
                    pnl=(p-e)/pip_val
                    if pnl>=tp_pips or pnl<=-sl_pips or bh[i]>=max_hold_bars or trends[i]<0: pos[i]=0; ep[i]=0
                    else: pos[i]=1.0; ep[i]=e
                else:
                    pnl=(e-p)/pip_val
                    if pnl>=tp_pips or pnl<=-sl_pips or bh[i]>=max_hold_bars or trends[i]>0: pos[i]=0; ep[i]=0
                    else: pos[i]=-1.0; ep[i]=e
        result = result.with_columns(pl.Series("signal", pos))
        return result
    return strategy

