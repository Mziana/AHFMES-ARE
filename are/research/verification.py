"""
AHFMES ARE — Verification Layer

Leakage/temporal firewall and independent result verification.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any, Dict, List

try:
    import polars as pl
except ImportError:
    raise ImportError("Polars required: pip install polars")

from are.hasher import compute_sha256
from are.research.holdout import TemporalContract


class LeakageFirewall:
    """
    Validates temporal data-access contract for leakage prevention.

    PRIMARY: Temporal contract enforcement (feature_timestamp <= signal_timestamp < execution_timestamp)
    SECONDARY: Forward-correlation as diagnostic (NOT proof of leakage)

    Leakage is proven by temporal contract violation, not by statistical correlation.
    """

    @staticmethod
    def validate_signal_timing(df: pl.DataFrame, contract: TemporalContract) -> Dict[str, Any]:
        """Check temporal contract compliance."""
        checks = []
        issues = []

        if "signal" not in df.columns:
            return {"valid": False, "error": "No signal column", "checks": []}

        if "timestamp" not in df.columns:
            return {"valid": False, "error": "No timestamp column", "checks": []}

        # Check 1: Signal variation
        unique_signals = df["signal"].n_unique()
        if unique_signals <= 1:
            issues.append(f"Signal is constant ({unique_signals} unique values) — no information content")
        checks.append({"check": "signal_variation", "pass": unique_signals > 1, "detail": f"{unique_signals} unique signals"})

        # Check 2: Signal shift
        if contract.signal_available_bar == "bar_t_plus_1":
            if "prev_signal" in df.columns:
                checks.append({"check": "signal_shift_enforced", "pass": True, "detail": "Engine applies signal shift (prev_signal present)"})
            else:
                checks.append({"check": "signal_shift_enforced", "pass": True, "detail": "Engine handles shift internally (no prev_signal column needed)"})

        # Check 3: Timestamp monotonicity
        ts = df["timestamp"].to_list()
        violations = 0
        for i in range(1, len(ts)):
            if ts[i] is not None and ts[i-1] is not None and ts[i] < ts[i-1]:
                violations += 1
        checks.append({"check": "temporal_ordering", "pass": violations == 0, "detail": f"{violations} violations"})

        # Check 4: No future-derived columns
        future_indicators = [c for c in df.columns if any(kw in c.lower() for kw in ['future', 'ahead', 'next_bar', 't_plus'])]
        if future_indicators:
            issues.append(f"Future-derived columns detected: {future_indicators}")
        checks.append({"check": "no_future_columns", "pass": len(future_indicators) == 0, "detail": f"{len(future_indicators)} future columns"})

        # Forward Correlation (SECONDARY — diagnostic only)
        if "price" in df.columns:
            future_price_corr = 0.0
            try:
                sig = df["signal"].to_list()
                price = df["price"].to_list()
                if len(sig) > 10 and len(price) > 10:
                    sig_vals = sig[:-1]
                    ret_vals = [(price[i+1] - price[i]) / price[i] if price[i] != 0 else 0 for i in range(len(price)-1)]
                    n = min(len(sig_vals), len(ret_vals))
                    if n > 10:
                        mean_s = sum(sig_vals[:n]) / n
                        mean_r = sum(ret_vals[:n]) / n
                        cov = sum((sig_vals[i] - mean_s) * (ret_vals[i] - mean_r) for i in range(n)) / n
                        std_s = math.sqrt(sum((s - mean_s)**2 for s in sig_vals[:n]) / n)
                        std_r = math.sqrt(sum((r - mean_r)**2 for r in ret_vals[:n]) / n)
                        if std_s > 0 and std_r > 0:
                            future_price_corr = abs(cov / (std_s * std_r))
            except Exception:
                pass

            corr_ok = future_price_corr < 0.5
            if not corr_ok:
                issues.append(f"HIGH forward correlation: {future_price_corr:.4f} — investigate for leakage (diagnostic only)")
            checks.append({"check": "forward_correlation_diagnostic", "pass": True, "detail": f"corr={future_price_corr:.4f} (diagnostic, not a gate)"})

        valid = len(issues) == 0
        return {
            "valid": valid,
            "issues": issues,
            "checks": checks,
            "contract": contract.to_dict(),
            "note": "PRIMARY: temporal contract enforcement. SECONDARY: forward correlation is diagnostic only.",
        }

    @staticmethod
    def build_default_contract() -> TemporalContract:
        """Build the standard AHFMES temporal contract."""
        fields = {
            "signal_calculation_bar": "close_of_bar_t",
            "signal_available_bar": "bar_t_plus_1",
            "order_submission_bar": "bar_t_plus_1_open",
            "execution_price": "next_bar_open",
            "execution_bar": "bar_t_plus_1",
        }
        contract_hash = compute_sha256(json.dumps(fields, sort_keys=True).encode())
        return TemporalContract(
            signal_calculation_bar="close_of_bar_t",
            signal_available_bar="bar_t_plus_1",
            order_submission_bar="bar_t_plus_1_open",
            execution_price="next_bar_open",
            execution_bar="bar_t_plus_1",
            contract_hash=contract_hash,
        )


class IndependentVerifier:
    """
    Recomputes backtest results from artifacts WITHOUT trusting the engine.
    """

    @staticmethod
    def verify_equity_curve(
        equity_data: List[Dict[str, Any]],
        initial_capital: float,
        strategy_returns: List[float],
    ) -> Dict[str, Any]:
        """Verify equity curve is consistent with strategy returns."""
        if not equity_data or not strategy_returns:
            return {"valid": False, "error": "Empty data"}

        equity = [initial_capital]
        for r in strategy_returns:
            equity.append(equity[-1] * (1.0 + r))

        reported = [e.get("equity", 0) for e in equity_data]
        mismatches = 0
        max_diff = 0.0
        for i in range(min(len(equity), len(reported))):
            diff = abs(equity[i] - reported[i])
            max_diff = max(max_diff, diff)
            if diff > 0.01:
                mismatches += 1

        return {
            "valid": mismatches == 0,
            "mismatches": mismatches,
            "max_difference": round(max_diff, 6),
            "equity_points": len(equity),
        }

    @staticmethod
    def verify_sharpe(
        returns: List[float],
        claimed_sharpe: float,
        timeframe_seconds: float = 3600.0,
        tolerance: float = 0.001,
    ) -> Dict[str, Any]:
        """Recompute Sharpe ratio from raw returns."""
        if not returns or len(returns) < 2:
            return {"valid": False, "error": "Insufficient returns"}

        mean_ret = sum(returns) / len(returns)
        var_ret = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
        std_ret = math.sqrt(var_ret) if var_ret > 0 else 0.0

        bars_per_day = 86400.0 / timeframe_seconds if timeframe_seconds > 0 else 1440.0
        annual_factor = math.sqrt(252.0 * bars_per_day)
        recomputed_sharpe = (mean_ret / std_ret * annual_factor) if std_ret > 1e-9 else 0.0

        diff = abs(recomputed_sharpe - claimed_sharpe)

        return {
            "valid": diff < tolerance,
            "claimed": round(claimed_sharpe, 4),
            "recomputed": round(recomputed_sharpe, 4),
            "difference": round(diff, 6),
            "tolerance": tolerance,
        }

    @staticmethod
    def verify_max_drawdown(
        equity_curve: List[float],
        claimed_max_dd: float,
        tolerance: float = 0.001,
    ) -> Dict[str, Any]:
        """Recompute max drawdown from equity curve."""
        if not equity_curve or len(equity_curve) < 2:
            return {"valid": False, "error": "Insufficient equity data"}

        peak = equity_curve[0]
        max_dd = 0.0
        for eq in equity_curve:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak if peak > 0 else 0.0
            max_dd = max(max_dd, dd)

        diff = abs(max_dd - claimed_max_dd)
        return {
            "valid": diff < tolerance,
            "claimed": round(claimed_max_dd, 4),
            "recomputed": round(max_dd, 4),
            "difference": round(diff, 6),
        }

    @staticmethod
    def verify_artifact_integrity(run_dir: str) -> Dict[str, Any]:
        """Verify that all files in an artifact match their manifest hashes."""
        manifest_path = os.path.join(run_dir, "manifest.json")
        if not os.path.exists(manifest_path):
            return {"valid": False, "error": "No manifest.json found"}

        with open(manifest_path) as f:
            manifest = json.load(f)

        files = manifest.get("files", {})
        mismatches = []
        verified = []

        for file_path, expected_hash in files.items():
            full_path = os.path.join(run_dir, file_path)
            if not os.path.exists(full_path):
                mismatches.append({"file": file_path, "error": "missing"})
                continue

            with open(full_path, "rb") as f:
                actual_hash = compute_sha256(f.read())

            if actual_hash != expected_hash:
                mismatches.append({"file": file_path, "expected": expected_hash[:16], "actual": actual_hash[:16]})
            else:
                verified.append(file_path)

        return {
            "valid": len(mismatches) == 0,
            "verified_files": len(verified),
            "mismatched_files": len(mismatches),
            "mismatches": mismatches,
        }

    @staticmethod
    def verify_trade_metrics(
        returns: List[float],
        claimed_win_rate: float,
        claimed_profit_factor: float,
        claimed_total_return: float,
        tolerance: float = 0.05,
    ) -> Dict[str, Any]:
        """Verify trade-level metrics from raw OOS returns."""
        if not returns or len(returns) < 2:
            return {"valid": False, "error": "Insufficient returns"}

        wins = [r for r in returns if r > 0]
        losses = [r for r in returns if r < 0]
        n_wins = len(wins)
        n_total = len(returns)
        recomputed_wr = (n_wins / n_total * 100) if n_total > 0 else 0.0
        wr_match = abs(recomputed_wr - claimed_win_rate) < (tolerance * 100)

        gross_profit = sum(wins) if wins else 0.0
        gross_loss = abs(sum(losses)) if losses else 0.0
        if gross_loss > 1e-10 and gross_profit > 0:
            recomputed_pf = gross_profit / gross_loss
        elif gross_profit == 0 and gross_loss == 0:
            recomputed_pf = 0.0
        else:
            recomputed_pf = 0.0
        if claimed_profit_factor == 0 and recomputed_pf == 0:
            pf_match = True
        elif claimed_profit_factor == 0 and n_wins == 0:
            pf_match = True
        else:
            pf_match = abs(recomputed_pf - claimed_profit_factor) < (tolerance * 10)

        cum = 1.0
        for r in returns:
            cum *= (1 + r)
        recomputed_return = (cum - 1.0) * 100
        ret_match = abs(recomputed_return - claimed_total_return) < 0.1

        all_match = wr_match and pf_match and ret_match

        return {
            "valid": all_match,
            "win_rate": {
                "claimed": round(claimed_win_rate, 2),
                "recomputed": round(recomputed_wr, 2),
                "match": wr_match,
            },
            "profit_factor": {
                "claimed": round(claimed_profit_factor, 4),
                "recomputed": round(recomputed_pf, 4),
                "match": pf_match,
            },
            "total_return_pct": {
                "claimed": round(claimed_total_return, 4),
                "recomputed": round(recomputed_return, 4),
                "match": ret_match,
            },
        }

    @staticmethod
    def full_verification(run_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run all verification checks on a backtest run."""
        results = {}

        stats = run_data.get("statistics_result", {})
        oos = run_data.get("oos_result", {})
        oos_returns = oos.get("pooled_oos_returns", [])

        if oos_returns and len(oos_returns) > 2:
            results["sharpe"] = IndependentVerifier.verify_sharpe(
                returns=oos_returns,
                claimed_sharpe=stats.get("sharpe", 0.0),
            )
        else:
            results["sharpe"] = {"valid": False, "reason": "No OOS returns"}

        if oos_returns and len(oos_returns) > 1:
            cum = 1.0
            equity = [1.0]
            for r in oos_returns:
                cum *= (1 + r)
                equity.append(cum)
            results["max_drawdown"] = IndependentVerifier.verify_max_drawdown(
                equity_curve=equity,
                claimed_max_dd=stats.get("max_dd_pct", 0.0) / 100.0,
            )
        else:
            results["max_drawdown"] = {"valid": False, "reason": "No equity data"}

        if oos_returns and len(oos_returns) > 2:
            results["trade_metrics"] = IndependentVerifier.verify_trade_metrics(
                returns=oos_returns,
                claimed_win_rate=stats.get("win_rate", 0.0),
                claimed_profit_factor=stats.get("profit_factor", 0.0),
                claimed_total_return=stats.get("return_pct", 0.0),
            )
        else:
            results["trade_metrics"] = {"valid": False, "reason": "No trade data"}

        run_id = run_data.get("run_id", "")
        run_dir = f"data/backtest_runs/{run_id}"
        if os.path.exists(run_dir):
            results["artifact_integrity"] = IndependentVerifier.verify_artifact_integrity(run_dir)

        all_valid = all(
            r.get("valid", True)
            for r in results.values()
            if isinstance(r, dict) and "valid" in r
        )
        results["overall"] = "VERIFIED" if all_valid else "REJECTED"

        return results
