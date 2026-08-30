"""
AHFMES ARE — Independent Backtest Metrics Validator

Recomputes all backtest metrics from raw returns using a SEPARATE implementation
from the backtest engine. This is the "independent verifier" that catches bugs
in the main engine — if both implementations agree, confidence is high.

Based on institutional standards:
- Sharpe, Sortino, Calmar, CVaR (from backtrex.com, quantconnect.com)
- Profit factor, win rate, expectancy (from quantifiedstrategies.com)
- Minimum 30 trades per parameter (from Lopez de Prado AFML)
- IS/OOS correlation check (from paperswithbacktest.com)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

try:
    import polars as pl
except ImportError:
    raise ImportError("Polars required: pip install polars")


def compute_all_metrics(
    returns: List[float],
    equity_curve: Optional[List[float]] = None,
    initial_capital: float = 100000.0,
    timeframe_seconds: float = 3600.0,
    n_parameters: int = 1,
) -> Dict[str, Any]:
    """
    Compute ALL backtest metrics from raw returns.
    This is an INDEPENDENT implementation — does not use any function
    from are/backtest.py or are/backtest_enhanced.py.
    """
    if not returns or len(returns) < 2:
        return {"error": "Insufficient returns", "valid": False}

    n = len(returns)
    mean_r = sum(returns) / n
    var_r = sum((r - mean_r) ** 2 for r in returns) / n
    std_r = math.sqrt(var_r) if var_r > 0 else 0.0

    # Annualization
    bars_per_day = 86400.0 / timeframe_seconds if timeframe_seconds > 0 else 1440.0
    annual_factor = math.sqrt(252.0 * bars_per_day)

    # --- Core Metrics ---
    sharpe = (mean_r / std_r * annual_factor) if std_r > 1e-9 else 0.0

    # Sortino (downside deviation)
    neg_returns = [r for r in returns if r < 0]
    downside_var = sum(r ** 2 for r in neg_returns) / n if neg_returns else 0.0
    downside_std = math.sqrt(downside_var) if downside_var > 0 else 0.0
    sortino = (mean_r / downside_std * annual_factor) if downside_std > 1e-9 else 0.0

    # Profit factor
    gains = [r for r in returns if r > 0]
    losses = [abs(r) for r in returns if r < 0]
    gross_profit = sum(gains)
    gross_loss = sum(losses)
    profit_factor = (gross_profit / gross_loss) if gross_loss > 1e-9 else (100.0 if gross_profit > 0 else 1.0)

    # Win rate
    win_rate = (len(gains) / n * 100) if n > 0 else 0.0

    # Expectancy (average win * win_rate - average loss * loss_rate)
    avg_win = (gross_profit / len(gains)) if gains else 0.0
    avg_loss = (gross_loss / len(losses)) if losses else 0.0
    expectancy = avg_win * (len(gains) / n) - avg_loss * (len(losses) / n) if n > 0 else 0.0

    # Max consecutive losses
    max_consec = 0
    curr_consec = 0
    for r in returns:
        if r < 0:
            curr_consec += 1
            max_consec = max(max_consec, curr_consec)
        else:
            curr_consec = 0

    # --- Drawdown (from equity curve or reconstruct) ---
    if equity_curve and len(equity_curve) > 1:
        eq = equity_curve
    else:
        eq = [initial_capital]
        for r in returns:
            eq.append(eq[-1] * (1.0 + r))

    peak = eq[0]
    max_dd = 0.0
    for e in eq:
        if e > peak:
            peak = e
        dd = (peak - e) / peak if peak > 0 else 0.0
        max_dd = max(max_dd, dd)

    # Calmar
    total_return = (eq[-1] - initial_capital) / initial_capital if initial_capital > 0 else 0.0
    annual_return = total_return * (252.0 * bars_per_day / n) if n > 0 else 0.0
    calmar = (annual_return / max_dd) if max_dd > 1e-9 else 0.0

    # CVaR (5%)
    sorted_returns = sorted(returns)
    cvar_idx = max(1, int(len(sorted_returns) * 0.05))
    cvar = abs(sum(sorted_returns[:cvar_idx]) / cvar_idx) if cvar_idx > 0 else 0.0

    # Exposure
    time_in_market = sum(1 for r in returns if r != 0) / n * 100 if n > 0 else 0.0

    # --- Overfitting Diagnostics ---
    # Minimum trades per parameter (Lopez de Prado: >= 30)
    total_trades = len(gains) + len(losses)
    trades_per_param = total_trades / max(n_parameters, 1)
    min_trades_sufficient = trades_per_param >= 30

    # Return distribution normality (Jarque-Bera approximate)
    skew = sum((r - mean_r) ** 3 for r in returns) / (n * std_r ** 3) if std_r > 1e-9 else 0.0
    kurt = sum((r - mean_r) ** 4 for r in returns) / (n * std_r ** 4) if std_r > 1e-9 else 0.0
    jb_stat = n / 6 * (skew ** 2 + (kurt - 3) ** 2 / 4) if n > 10 else 0.0

    return {
        "valid": True,
        "n_observations": n,
        "initial_capital": initial_capital,
        "final_equity": round(eq[-1], 2),
        "total_return_pct": round(total_return * 100, 2),
        "annual_return_pct": round(annual_return * 100, 2),
        "sharpe_ratio": round(sharpe, 4),
        "sortino_ratio": round(sortino, 4),
        "calmar_ratio": round(calmar, 4),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "profit_factor": round(profit_factor, 4),
        "win_rate_pct": round(win_rate, 2),
        "expectancy": round(expectancy, 6),
        "cvar_5pct": round(cvar, 6),
        "total_trades": total_trades,
        "avg_win": round(avg_win, 6),
        "avg_loss": round(avg_loss, 6),
        "max_consecutive_losses": max_consec,
        "exposure_pct": round(time_in_market, 2),
        "trades_per_parameter": round(trades_per_param, 1),
        "min_trades_sufficient": min_trades_sufficient,
        "skewness": round(skew, 4),
        "kurtosis": round(kurt, 4),
        "jarque_bera_stat": round(jb_stat, 4),
        "annualization_factor": round(annual_factor, 4),
    }


def validate_backtest_result(
    claimed_metrics: Dict[str, Any],
    returns: List[float],
    equity_curve: Optional[List[float]] = None,
    initial_capital: float = 100000.0,
    timeframe_seconds: float = 3600.0,
    n_parameters: int = 1,
    tolerance: float = 0.01,
) -> Dict[str, Any]:
    """
    Validate a backtest result by recomputing all metrics independently.
    Returns validation report with pass/fail for each metric.
    """
    recomputed = compute_all_metrics(
        returns=returns,
        equity_curve=equity_curve,
        initial_capital=initial_capital,
        timeframe_seconds=timeframe_seconds,
        n_parameters=n_parameters,
    )

    if not recomputed.get("valid", False):
        return {"valid": False, "error": recomputed.get("error", "Recomputation failed")}

    checks = []
    key_metrics = [
        ("sharpe_ratio", "sharpe_ratio"),
        ("sortino_ratio", "sortino_ratio"),
        ("calmar_ratio", "calmar_ratio"),
        ("max_drawdown_pct", "max_drawdown_pct"),
        ("profit_factor", "profit_factor"),
        ("win_rate_pct", "win_rate_pct"),
        ("total_return_pct", "total_return_pct"),
        ("cvar_5pct", "cvar_5pct"),
    ]

    for claimed_key, recomputed_key in key_metrics:
        claimed_val = claimed_metrics.get(claimed_key, 0.0)
        recomputed_val = recomputed.get(recomputed_key, 0.0)
        if abs(claimed_val) > 1e-9:
            diff_pct = abs(claimed_val - recomputed_val) / abs(claimed_val)
        else:
            diff_pct = abs(claimed_val - recomputed_val)
        passed = diff_pct < tolerance
        checks.append({
            "metric": claimed_key,
            "claimed": round(claimed_val, 6),
            "recomputed": round(recomputed_val, 6),
            "diff_pct": round(diff_pct * 100, 4),
            "pass": passed,
        })

    # Minimum trades check
    checks.append({
        "metric": "min_trades_per_parameter",
        "claimed": claimed_metrics.get("total_trades", 0),
        "recomputed": recomputed["total_trades"],
        "trades_per_param": recomputed["trades_per_parameter"],
        "pass": recomputed["min_trades_sufficient"],
    })

    all_pass = all(c["pass"] for c in checks)
    failed_count = sum(1 for c in checks if not c["pass"])

    return {
        "valid": True,
        "overall": "VERIFIED" if all_pass else "MISMATCH",
        "checks": checks,
        "passed_count": len(checks) - failed_count,
        "failed_count": failed_count,
        "total_count": len(checks),
        "recomputed": recomputed,
    }


def cross_validate_engines(
    base_result_metrics: Dict[str, Any],
    enhanced_result_metrics: Dict[str, Any],
    tolerance: float = 0.02,
) -> Dict[str, Any]:
    """
    Cross-validate base engine vs enhanced engine results.
    Both should produce similar metrics on the same data.
    """
    checks = []
    key_metrics = ["sharpe_ratio", "max_drawdown_pct", "profit_factor", "total_return_pct"]

    for metric in key_metrics:
        base_val = base_result_metrics.get(metric, 0.0)
        enh_val = enhanced_result_metrics.get(metric, 0.0)
        if abs(base_val) > 1e-9:
            diff_pct = abs(base_val - enh_val) / abs(base_val)
        else:
            diff_pct = abs(base_val - enh_val)
        checks.append({
            "metric": metric,
            "base_engine": round(base_val, 6),
            "enhanced_engine": round(enh_val, 6),
            "diff_pct": round(diff_pct * 100, 4),
            "pass": diff_pct < tolerance,
        })

    all_pass = all(c["pass"] for c in checks)
    return {
        "overall": "CONSISTENT" if all_pass else "DIVERGENT",
        "checks": checks,
        "all_pass": all_pass,
    }


def compute_gate_metrics(
    oos_sharpe: float = 0.0,
    is_sharpe: float = 0.0,
    oos_return: float = 0.0,
    max_dd: float = 0.0,
    total_trades: int = 0,
    n_parameters: int = 1,
    win_rate: float = 0.0,
    profit_factor: float = 0.0,
) -> Dict[str, Any]:
    """
    Compute all gate-worthy metrics for the final gate decision.
    Based on institutional thresholds from research.
    """
    checks = []

    # 1. OOS Sharpe > 0
    checks.append({
        "check": "oos_sharpe_positive",
        "value": round(oos_sharpe, 4),
        "pass": oos_sharpe > 0,
        "threshold": "> 0",
        "source": "Basic alpha existence",
    })

    # 2. OOS Sharpe > 1.0 (institutional quality)
    checks.append({
        "check": "oos_sharpe_institutional",
        "value": round(oos_sharpe, 4),
        "pass": oos_sharpe > 1.0,
        "threshold": "> 1.0",
        "source": "QuantConnect / Backtrex standard",
    })

    # 3. Max DD < 25% (conservative) or < 50% (aggressive)
    checks.append({
        "check": "max_dd_conservative",
        "value": round(max_dd * 100, 2),
        "pass": max_dd < 0.25,
        "threshold": "< 25%",
        "source": "Institutional risk limit",
    })

    # 4. Profit factor > 1.3
    checks.append({
        "check": "profit_factor_minimum",
        "value": round(profit_factor, 4),
        "pass": profit_factor > 1.3,
        "threshold": "> 1.3",
        "source": "Minimum viable edge",
    })

    # 5. Win rate > 40% (for trend strategies)
    checks.append({
        "check": "win_rate_floor",
        "value": round(win_rate, 2),
        "pass": win_rate > 40.0,
        "threshold": "> 40%",
        "source": "Minimum viable win rate",
    })

    # 6. Minimum trades: >= 30 per parameter
    trades_per_param = total_trades / max(n_parameters, 1)
    checks.append({
        "check": "min_trades_per_parameter",
        "value": round(trades_per_param, 1),
        "pass": trades_per_param >= 30,
        "threshold": ">= 30",
        "source": "Lopez de Prado AFML",
    })

    # 7. IS/OOS consistency (WFE > 0)
    if is_sharpe > 0:
        wfe = oos_sharpe / is_sharpe
    else:
        wfe = 0.0
    checks.append({
        "check": "is_oos_consistency",
        "value": round(wfe, 4),
        "pass": wfe > 0,
        "threshold": "> 0",
        "source": "Walk-forward efficiency",
    })

    # 8. Expectancy > 0
    checks.append({
        "check": "positive_expectancy",
        "value": round(win_rate / 100 * profit_factor - (1 - win_rate / 100), 4),
        "pass": win_rate / 100 * profit_factor > (1 - win_rate / 100),
        "threshold": "win_rate * PF > loss_rate",
        "source": "Mathematical expectancy",
    })

    failed = [c for c in checks if not c["pass"]]
    passed = [c for c in checks if c["pass"]]

    if len(failed) == 0:
        decision = "PASS"
    elif len(failed) <= 2 and len(passed) >= 5:
        decision = "BORDERLINE"
    else:
        decision = "FAIL"

    return {
        "decision": decision,
        "checks": checks,
        "passed": len(passed),
        "failed": len(failed),
        "total": len(checks),
    }
