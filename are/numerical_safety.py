"""
AHFMES Numerical Robustness (§29)

Safe metric computation with explicit handling for:
NaN, Inf, -Inf, None, empty series, single observation,
zero variance, zero denominator, negative equity, 100% loss.
"""

import math
from typing import List, Optional, Tuple


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division: returns default if denominator is zero or result is non-finite."""
    if denominator == 0 or not math.isfinite(denominator):
        return default
    result = numerator / denominator
    return result if math.isfinite(result) else default


def safe_sqrt(value: float, default: float = 0.0) -> float:
    """Safe sqrt: returns default for negative input."""
    if not math.isfinite(value) or value < 0:
        return default
    return math.sqrt(value)


def clean_returns(returns: List[float]) -> List[float]:
    """Remove None/NaN/Inf from returns. Returns clean list."""
    return [r for r in returns if r is not None and math.isfinite(r)]


def compute_returns_safe(equity_curve: List[float]) -> List[float]:
    """Compute percentage returns from equity curve with full edge case handling."""
    clean = clean_returns(equity_curve)
    if len(clean) < 2:
        return []
    returns = []
    for i in range(1, len(clean)):
        if clean[i - 1] != 0 and math.isfinite(clean[i - 1]):
            r = (clean[i] - clean[i - 1]) / abs(clean[i - 1])
            if math.isfinite(r):
                returns.append(r)
            else:
                returns.append(0.0)
        else:
            returns.append(0.0)
    return returns


def compute_max_drawdown(equity_curve: List[float]) -> Tuple[float, float]:
    """Compute max drawdown and its duration from equity curve.
    Returns (max_drawdown_pct, max_drawdown_duration).
    Full edge case handling per §29.
    """
    clean = clean_returns(equity_curve)
    if len(clean) < 2:
        return 0.0, 0

    peak = clean[0]
    max_dd = 0.0
    current_dd_duration = 0
    max_dd_duration = 0

    for eq in clean:
        if eq > peak:
            peak = eq
            current_dd_duration = 0
        if peak > 0 and math.isfinite(peak):
            dd = (peak - eq) / peak
            if dd > max_dd:
                max_dd = dd
            if dd > 0:
                current_dd_duration += 1
                if current_dd_duration > max_dd_duration:
                    max_dd_duration = current_dd_duration
            else:
                current_dd_duration = 0

    return min(max_dd, 1.0), max_dd_duration  # Cap at 100%


def compute_sortino_ratio(
    returns: List[float],
    risk_free_rate: float = 0.0,
    timeframe_seconds: float = 3600.0,
) -> float:
    """Compute Sortino ratio using downside deviation only."""
    clean = clean_returns(returns)
    if len(clean) < 2:
        return 0.0

    mean_ret = sum(clean) / len(clean)
    downside = [r for r in clean if r < risk_free_rate]
    if not downside:
        return 0.0

    downside_var = sum((r - risk_free_rate) ** 2 for r in downside) / len(downside)
    downside_std = safe_sqrt(downside_var)
    if downside_std <= 1e-9:
        return 0.0

    bars_per_day = (86400.0 / timeframe_seconds) if timeframe_seconds > 0 else 1440.0
    annual_factor = safe_sqrt(252.0 * bars_per_day)
    result = (mean_ret - risk_free_rate) / downside_std * annual_factor
    return 0.0 if not math.isfinite(result) else float(result)


def compute_calmar_ratio(
    total_return_pct: float,
    max_drawdown_pct: float,
) -> float:
    """Compute Calmar ratio: annualized return / max drawdown."""
    if max_drawdown_pct <= 0 or not math.isfinite(max_drawdown_pct):
        return 0.0
    result = total_return_pct / max_drawdown_pct
    return 0.0 if not math.isfinite(result) else float(result)


def compute_cvar(returns: List[float], confidence: float = 0.05) -> float:
    """Compute Conditional Value at Risk (Expected Shortfall) at given confidence level."""
    clean = sorted(clean_returns(returns))
    if not clean:
        return 0.0
    idx = int(len(clean) * confidence)
    idx = max(0, min(idx, len(clean) - 1))
    return clean[idx]


def validate_metric(metric_name: str, value: float) -> bool:
    """Check that a metric value is finite and sensible."""
    if not math.isfinite(value):
        return False
    if metric_name in ("sharpe_ratio", "sortino_ratio", "calmar_ratio"):
        # Sharpe can legitimately be negative, but not infinite
        return True
    if metric_name == "max_drawdown":
        return 0.0 <= value <= 1.0
    if metric_name == "win_rate":
        return 0.0 <= value <= 1.0
    if metric_name == "total_return":
        return value >= -1.0  # Can't lose more than 100%
    return True
