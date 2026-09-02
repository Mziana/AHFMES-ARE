"""
AHFMES ARE — Quantitative Metrics

Standalone metric functions for backtest performance evaluation.
Extracted from backtest.py for single-responsibility separation.

Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import math
from typing import List


def calculate_sharpe_ratio(
    returns: List[float],
    timeframe_seconds: float = 60.0,
) -> float:
    """
    Computes annualized Sharpe Ratio properly scaled to the bar timeframe (RES-RED-07).
    Handles NaN/Inf/empty/zero-var/100% loss edge cases.
    """
    if not returns or len(returns) < 2:
        return 0.0
    # Filter non-finite values
    clean = [r for r in returns if r is not None and math.isfinite(r)]
    if len(clean) < 2:
        return 0.0
    mean_ret = sum(clean) / len(clean)
    var_ret = sum((r - mean_ret) ** 2 for r in clean) / len(clean)
    std_ret = math.sqrt(var_ret) if var_ret > 0 else 0.0
    if std_ret <= 1e-9:
        return 0.0
    bars_per_day = (86400.0 / timeframe_seconds) if timeframe_seconds > 0 else 1440.0
    annual_factor = math.sqrt(252.0 * bars_per_day)
    result = mean_ret / std_ret * annual_factor
    return 0.0 if not math.isfinite(result) else float(result)
