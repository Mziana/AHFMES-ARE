"""
AHFMES ARE — Portfolio Correlation & Risk Analytics (DELEGASI_036, Organ 2 & 6)

Provides mathematical utilities for portfolio risk analysis:
1. Annualized volatility calculation.
2. Sample Pearson correlation coefficient calculation with zero-variance protection.
100% Python Standard Library + Polars. Zero SciPy, Zero External Network.
"""

from __future__ import annotations

import math
from typing import List


def calculate_annualized_volatility(
    returns_series: List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Computes annualized sample volatility from a series of periodic returns.
    Returns 0.0 if sample size < 2.
    """
    n = len(returns_series)
    if n < 2:
        return 0.0

    mean_ret = sum(returns_series) / n
    variance = sum((r - mean_ret) ** 2 for r in returns_series) / (n - 1)
    if variance <= 0.0:
        return 0.0

    sample_std = math.sqrt(variance)
    return float(sample_std * math.sqrt(periods_per_year))


def calculate_pearson_correlation(
    returns_a: List[float],
    returns_b: List[float],
) -> float:
    """
    Calculates Pearson correlation coefficient between two return series.
    Truncates series to equal minimum length.
    Fail-closed: Returns 0.0 if either series has zero variance or n < 2 (prevents ZeroDivisionError).
    """
    n = min(len(returns_a), len(returns_b))
    if n < 2:
        return 0.0

    a = returns_a[:n]
    b = returns_b[:n]

    mean_a = sum(a) / n
    mean_b = sum(b) / n

    cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    var_a = sum((x - mean_a) ** 2 for x in a)
    var_b = sum((y - mean_b) ** 2 for y in b)

    if var_a <= 1e-12 or var_b <= 1e-12:
        return 0.0

    corr = cov / math.sqrt(var_a * var_b)
    # Clip numerical precision drift to [-1.0, 1.0]
    return float(max(-1.0, min(1.0, corr)))