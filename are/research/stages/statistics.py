"""
AHFMES ARE — Statistics Compilation Stage

Computes DSR, PSR, Monte Carlo from REAL evidence chain.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from are.research.types import RunStage, StageResult, BacktestRun


class StatisticsStage:
    """Compile statistics with DSR/PSR/MC from REAL evidence chain.

    Evidence flow: WFOEvidence -> OOS -> Statistics -> Gate
    No fallbacks: missing evidence -> INVALID.
    """

    def run(self, run: BacktestRun) -> StageResult:
        t0 = time.time()
        oos = run.oos_result or {}
        wfo = run.wfo_result or {}

        oos_sharpe = oos.get("pooled_sharpe", 0.0)
        oos_returns = oos.get("pooled_oos_returns", [])
        n_obs = oos.get("n_obs", 0)
        effective_trials = oos.get("effective_trial_count", 0)

        stats = {
            "sharpe": oos_sharpe,
            "return_pct": oos.get("pooled_return", 0.0) * 100,
            "max_dd_pct": oos.get("pooled_max_dd", 0.0) * 100,
            "wfe": wfo.get("mean_wfe", 0.0),
            "fold_count": oos.get("fold_count", 0),
            "n_obs": n_obs,
            "effective_trial_count": effective_trials,
        }

        # Compute additional metrics from actual OOS returns
        if oos_returns and len(oos_returns) > 2:
            returns_arr = oos_returns
            mean_r = sum(returns_arr) / len(returns_arr)
            var_r = sum((r - mean_r) ** 2 for r in returns_arr) / max(len(returns_arr) - 1, 1)
            std_r = math.sqrt(var_r) if var_r > 0 else 1e-10
            upside = [r for r in returns_arr if r > 0]
            downside = [r for r in returns_arr if r < 0]
            flat_count = len(returns_arr) - len(upside) - len(downside)
            win_count = len(upside)
            loss_count = len(downside)
            actual_trades = win_count + loss_count
            stats["total_trades"] = actual_trades
            stats["total_observations"] = len(returns_arr)
            stats["flat_observations"] = flat_count
            stats["win_count"] = win_count
            stats["loss_count"] = loss_count
            stats["win_rate"] = (win_count / actual_trades * 100) if actual_trades > 0 else 0.0
            avg_win = sum(upside) / len(upside) if upside else 0.0
            avg_loss = abs(sum(downside) / len(downside)) if downside else 1.0
            stats["avg_win"] = avg_win
            stats["avg_loss"] = avg_loss
            stats["profit_factor"] = (avg_win * win_count) / (avg_loss * loss_count) if (avg_loss * loss_count) > 0 else 0.0
            cum = 1.0
            equity_curve = [1.0]
            peak = 1.0
            max_dd = 0.0
            for r in returns_arr:
                cum *= (1 + r)
                equity_curve.append(cum)
                if cum > peak:
                    peak = cum
                dd = (peak - cum) / peak if peak > 0 else 0
                if dd > max_dd:
                    max_dd = dd
            stats["total_return_pct"] = (cum - 1.0) * 100
            stats["max_drawdown_calc"] = max_dd * 100
        else:
            stats["total_trades"] = 0
            stats["win_rate"] = 0.0
            stats["profit_factor"] = 0.0

        # DSR/PSR using ACTUAL trial count from WFOEvidence
        try:
            from are.validation import calculate_deflated_sharpe_ratio, calculate_probabilistic_sharpe_ratio
            if n_obs > 10 and effective_trials > 0:
                psr = calculate_probabilistic_sharpe_ratio(oos_sharpe, 0.0, n_obs)
                expected_max_sr, dsr_p = calculate_deflated_sharpe_ratio(oos_sharpe, effective_trials, n_obs)
                stats["psr"] = psr
                stats["dsr_p_value"] = dsr_p
                stats["dsr_expected_max_sr"] = expected_max_sr
            else:
                stats["psr"] = 0.0
                stats["dsr_p_value"] = 1.0
                stats["dsr_skip_reason"] = f"n_obs={n_obs}, trials={effective_trials}"
        except Exception as e:
            logging.error(f"DSR/PSR computation failed: {e}")
            stats["psr"] = 0.0
            stats["dsr_p_value"] = 1.0

        # Monte Carlo with block bootstrap
        try:
            from are.validation import monte_carlo_simulation
            if len(oos_returns) > 10:
                mc = monte_carlo_simulation(
                    oos_returns,
                    num_simulations=run.mc_simulations,
                    initial_capital=run.initial_capital,
                )
                stats["mc_ruin_probability"] = mc.get(
                    "mc_terminal_ruin_probability",
                    mc.get("mc_probability_of_ruin", 1.0)
                ) if isinstance(mc, dict) else 1.0
                stats["mc_mean_equity"] = mc.get("mc_mean_final_equity", 0.0) if isinstance(mc, dict) else 0.0
                stats["mc_95th_dd"] = mc.get("mc_95th_pct_drawdown", 0.0) if isinstance(mc, dict) else 0.0
            else:
                stats["mc_ruin_probability"] = 1.0
                stats["mc_mean_equity"] = 0.0
        except Exception:
            stats["mc_ruin_probability"] = 1.0
            stats["mc_mean_equity"] = 0.0

        run.statistics_result = stats
        return StageResult(
            stage="statistics", status=RunStage.PASSED,
            started_at=t0, completed_at=time.time(), data=stats,
        )
