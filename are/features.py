"""
AHFMES P001 — Quantitative Feature Library (ACC-511)

Deterministic market feature calculation engine.
Zero external dependencies (stdlib only: math, statistics, typing, dataclasses).
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def calculate_orderbook_imbalance(
    bids: List[Tuple[float, float]],
    asks: List[Tuple[float, float]],
    depth: int = 5,
) -> Dict[str, float]:
    """
    Calculates orderbook volume imbalance ratio (-1.0 to 1.0), micro-price, and spread.
    bids: list of (price, size) sorted descending by price
    asks: list of (price, size) sorted ascending by price
    """
    if not bids or not asks:
        return {
            "imbalance_ratio": 0.0,
            "micro_price": 0.0,
            "spread": 0.0,
            "mid_price": 0.0,
            "bid_volume": 0.0,
            "ask_volume": 0.0,
        }

    bids_slice = bids[:depth]
    asks_slice = asks[:depth]

    bid_vol = sum(size for _, size in bids_slice)
    ask_vol = sum(size for _, size in asks_slice)
    total_vol = bid_vol + ask_vol

    imbalance_ratio = ((bid_vol - ask_vol) / total_vol) if total_vol > 0.0 else 0.0

    best_bid, best_bid_size = bids[0]
    best_ask, best_ask_size = asks[0]
    spread = max(0.0, best_ask - best_bid)
    mid_price = (best_bid + best_ask) / 2.0

    top_vol = best_bid_size + best_ask_size
    if top_vol > 0.0:
        micro_price = (best_bid * best_ask_size + best_ask * best_bid_size) / top_vol
    else:
        micro_price = mid_price

    return {
        "imbalance_ratio": imbalance_ratio,
        "micro_price": micro_price,
        "spread": spread,
        "mid_price": mid_price,
        "bid_volume": bid_vol,
        "ask_volume": ask_vol,
    }


def calculate_realized_volatility(prices: List[float], window: int = 20) -> float:
    """
    Calculates realized volatility from log returns over a rolling window.
    """
    if len(prices) < 2:
        return 0.0

    recent_prices = prices[-window:] if len(prices) > window else prices
    if len(recent_prices) < 2:
        return 0.0

    log_returns = []
    for i in range(1, len(recent_prices)):
        p_prev = recent_prices[i - 1]
        p_curr = recent_prices[i]
        if p_prev > 0.0 and p_curr > 0.0:
            log_returns.append(math.log(p_curr / p_prev))
        else:
            log_returns.append(0.0)

    if len(log_returns) < 2:
        return 0.0

    mean_ret = sum(log_returns) / len(log_returns)
    variance = sum((r - mean_ret) ** 2 for r in log_returns) / (len(log_returns) - 1)
    return math.sqrt(variance)


def calculate_momentum_indicators(
    prices: List[float],
    fast_period: int = 5,
    slow_period: int = 20,
) -> Dict[str, float]:
    """
    Calculates fast and slow exponential moving averages (EMA), crossover diff, and price velocity.
    """
    if not prices:
        return {
            "ema_fast": 0.0,
            "ema_slow": 0.0,
            "crossover_diff": 0.0,
            "price_velocity": 0.0,
        }

    def compute_ema(data: List[float], period: int) -> float:
        if not data:
            return 0.0
        alpha = 2.0 / (period + 1.0)
        ema = data[0]
        for val in data[1:]:
            ema = alpha * val + (1.0 - alpha) * ema
        return ema

    ema_fast = compute_ema(prices[-fast_period * 3:] if len(prices) > fast_period * 3 else prices, fast_period)
    ema_slow = compute_ema(prices[-slow_period * 3:] if len(prices) > slow_period * 3 else prices, slow_period)
    crossover_diff = ema_fast - ema_slow

    # Velocity: percentage change over fast_period
    if len(prices) >= fast_period and prices[-fast_period] > 0.0:
        price_velocity = (prices[-1] - prices[-fast_period]) / prices[-fast_period]
    else:
        price_velocity = 0.0

    return {
        "ema_fast": ema_fast,
        "ema_slow": ema_slow,
        "crossover_diff": crossover_diff,
        "price_velocity": price_velocity,
    }


def calculate_mean_reversion_zscore(prices: List[float], window: int = 20) -> float:
    """
    Calculates the z-score of current price relative to a moving window mean and standard deviation.
    """
    if not prices:
        return 0.0

    recent = prices[-window:] if len(prices) > window else prices
    if len(recent) < 2:
        return 0.0

    mean_val = sum(recent) / len(recent)
    variance = sum((x - mean_val) ** 2 for x in recent) / (len(recent) - 1)
    std_dev = math.sqrt(variance)

    if std_dev == 0.0:
        return 0.0

    current_price = prices[-1]
    return (current_price - mean_val) / std_dev


class MarketFeatureExtractor:
    """Extracts unified quantitative features from chronological market snapshots."""

    def extract_features(self, market_snapshots: List[Dict[str, Any]]) -> Dict[str, float]:
        if not market_snapshots:
            return {
                "imbalance_ratio": 0.0,
                "spread": 0.0,
                "micro_price": 0.0,
                "realized_volatility": 0.0,
                "crossover_diff": 0.0,
                "price_velocity": 0.0,
                "zscore": 0.0,
                "trend_strength": 0.0,
                "volatility": 0.0,
            }

        prices = [float(s.get("price", s.get("mid_price", 0.0))) for s in market_snapshots if s.get("price") or s.get("mid_price")]
        latest = market_snapshots[-1]

        bids = latest.get("bids", [])
        asks = latest.get("asks", [])
        ob_res = calculate_orderbook_imbalance(bids, asks)

        vol = calculate_realized_volatility(prices)
        mom = calculate_momentum_indicators(prices)
        zscore = calculate_mean_reversion_zscore(prices)

        trend_strength = abs(mom["crossover_diff"]) / (latest.get("price", 1.0) or 1.0) * 1000.0

        return {
            "imbalance_ratio": ob_res["imbalance_ratio"],
            "spread": ob_res["spread"],
            "micro_price": ob_res["micro_price"],
            "realized_volatility": vol,
            "crossover_diff": mom["crossover_diff"],
            "price_velocity": mom["price_velocity"],
            "zscore": zscore,
            "trend_strength": trend_strength,
            "volatility": vol * 100.0,
        }
