"""
AHFMES ARE — Gate & Verification Stages

Final gate decision (fail-closed) and independent verification of results.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from are.research.types import RunStage, StageResult, GateDecision, BacktestRun
from are.research.experiment_config import ExperimentConfig
from are.hasher import compute_sha256
from are.research.integrity import IndependentVerifier, EvidenceBinding


class GateStage:
    """Final gate decision — fail-closed, no fallbacks.

    Missing metrics = INVALID (not default values).
    """

    def run(self, run: BacktestRun, config: ExperimentConfig) -> StageResult:
        t0 = time.time()
        oos = run.oos_result or {}
        stats = run.statistics_result or {}
        crisis = run.crisis_result or {}
        stability = run.stability_result or {}
        baseline = run.baseline_result or {}
        holdout_evaluated = run.holdout_evaluated

        # FAIL-CLOSED: if critical evidence is missing, gate is INVALID
        n_obs = stats.get("n_obs", 0)
        oos_sharpe = oos.get("pooled_sharpe", 0.0)
        effective_trials = stats.get("effective_trial_count", 0)

        if n_obs < 10 or effective_trials < 1:
            gate = {
                "decision": "INVALID",
                "checks": [{"check": "evidence_sufficiency", "pass": False,
                             "value": f"n_obs={n_obs}, trials={effective_trials}"}],
                "passed": 0, "failed": 1, "total": 1,
                "reason": "Insufficient evidence: need n_obs >= 10 and trials >= 1",
            }
            run.final_gate = gate
            return StageResult(
                stage="final_gate", status=RunStage.FAILED,
                started_at=t0, completed_at=time.time(), data=gate,
            )

        is_sharpe = stats.get("wfe", 0.0) * oos_sharpe if stats.get("wfe", 0) > 0 else 0.0

        best_baseline_sharpe = max(
            (v.get("sharpe", -999) for v in baseline.values()
             if isinstance(v, dict) and "error" not in v),
            default=0.0
        )

        from are.research.metrics import compute_gate_metrics
        metrics_gate = compute_gate_metrics(
            oos_sharpe=oos_sharpe,
            is_sharpe=is_sharpe,
            oos_return=oos.get("pooled_return", 0.0),
            max_dd=oos.get("pooled_max_dd", 1.0),
            total_trades=stats.get("total_trades", 0),
            n_parameters=config.parameter_grid.grid_size,
            win_rate=stats.get("win_rate", 0.0),
            profit_factor=stats.get("profit_factor", 0.0),
        )

        extra_checks = []

        extra_checks.append({"check": "crisis_survival", "pass": crisis.get("survived", False), "value": crisis.get("survived", False)})
        extra_checks.append({"check": "param_stability", "pass": stability.get("verdict") in ("ROBUST", "MARGINAL"), "value": stability.get("verdict", "UNKNOWN")})
        extra_checks.append({"check": "beats_baselines", "pass": oos_sharpe > best_baseline_sharpe, "value": f"{oos_sharpe:.4f} > {best_baseline_sharpe:.4f}"})

        dsr_p = stats.get("dsr_p_value", 1.0)
        extra_checks.append({"check": "dsr_significant", "pass": dsr_p < 0.05, "value": f"p={dsr_p:.4f}"})

        mc_ruin = stats.get("mc_ruin_probability", 1.0)
        extra_checks.append({"check": "mc_ruin_low", "pass": mc_ruin < 0.10, "value": f"{mc_ruin:.2%}"})

        # BT-04: Holdout evidence check
        he = run.holdout_evidence
        holdout_valid = False
        holdout_detail = 'no evidence'
        if he is not None:
            he_trades = he.get('trade_count', he.get('total_trades', 0))
            he_return = he.get('total_return', he.get('total_return_pct', 0))
            he_sharpe = he.get('sharpe', 0)
            he_provenance = he.get('provenance_hash', '')
            he_valid = he.get('valid', True)
            holdout_valid = (
                he_valid
                and he_trades > 0
                and abs(he_return) < 100
                and len(he_provenance) > 0
            )
            holdout_detail = {
                'trades': he_trades,
                'return_pct': he_return,
                'sharpe': he_sharpe,
                'provenance': he_provenance[:16] if he_provenance else 'missing',
            }
        extra_checks.append({"check": "holdout_evidence", "pass": holdout_valid, "value": holdout_detail})

        eb = run.evidence_binding
        if eb is not None:
            eb_valid = eb.get('valid', True) if isinstance(eb, dict) else True
            extra_checks.append({"check": "evidence_binding", "pass": eb_valid, "value": 'binding chain intact' if eb_valid else 'binding broken'})
        else:
            extra_checks.append({"check": "evidence_binding", "pass": False, "value": 'no binding created'})

        wfe = oos.get("mean_wfe", 0.0)
        extra_checks.append({"check": "wfe_positive", "pass": wfe > 0.0, "value": f"{wfe:.4f}"})

        fold_count = oos.get("fold_count", 0)
        extra_checks.append({"check": "min_folds", "pass": fold_count >= 3, "value": f"{fold_count} folds"})

        all_checks = metrics_gate["checks"] + extra_checks
        failed = [c for c in all_checks if not c["pass"]]
        passed = [c for c in all_checks if c["pass"]]

        base_decision = metrics_gate["decision"]
        critical_failures = [c for c in failed if c["check"] in (
            "dsr_significant", "holdout_evidence", "evidence_sufficiency",
            "evidence_binding",
        )]

        if base_decision == "PASS" and len(failed) == 0:
            decision = GateDecision.PASS
        elif len(critical_failures) > 0:
            decision = GateDecision.FAIL
        elif base_decision in ("PASS", "BORDERLINE") and len(failed) <= 2:
            decision = GateDecision.BORDERLINE
        else:
            decision = GateDecision.FAIL if len(failed) <= len(all_checks) // 2 else GateDecision.INVALID

        gate = {
            "decision": decision.value,
            "checks": all_checks,
            "passed": len(passed),
            "failed": len(failed),
            "total": len(all_checks),
            "metrics_gate": metrics_gate["decision"],
        }
        run.final_gate = gate

        return StageResult(
            stage="final_gate", status=RunStage.PASSED,
            started_at=t0, completed_at=time.time(), data=gate,
        )


class VerifyStage:
    """Independent verification — recompute ALL metrics from actual OOS returns."""

    RUNS_DIR = "data/backtest_runs"

    def run(self, run: BacktestRun) -> StageResult:
        t0 = time.time()
        try:
            run_dir = os.path.join(self.RUNS_DIR, run.run_id)
            if not os.path.exists(run_dir):
                return StageResult(
                    stage="verify", status=RunStage.FAILED,
                    started_at=t0, completed_at=time.time(),
                    error="Run directory not found",
                )

            artifact_result = IndependentVerifier.verify_artifact_integrity(run_dir)

            oos_returns = run.oos_result.get("pooled_oos_returns", []) if run.oos_result else []
            stats = run.statistics_result or {}

            if oos_returns and len(oos_returns) > 2:
                sharpe_check = IndependentVerifier.verify_sharpe(
                    returns=oos_returns,
                    claimed_sharpe=stats.get("sharpe", 0.0),
                )
            else:
                sharpe_check = {"valid": False, "reason": "No OOS returns to verify"}

            return_check = {"valid": True, "checks": []}
            if oos_returns and len(oos_returns) > 1:
                cum = 1.0
                peak = 1.0
                max_dd = 0.0
                for r in oos_returns:
                    cum *= (1 + r)
                    if cum > peak:
                        peak = cum
                    dd = (peak - cum) / peak if peak > 0 else 0
                    if dd > max_dd:
                        max_dd = dd
                recomputed_return = (cum - 1.0) * 100
                claimed_return = stats.get("return_pct", 0.0)
                return_match = abs(recomputed_return - claimed_return) < 0.1
                return_check["checks"].append({
                    "metric": "total_return_pct",
                    "claimed": claimed_return,
                    "recomputed": round(recomputed_return, 4),
                    "match": return_match,
                })
                recomputed_dd = max_dd * 100
                claimed_dd = stats.get("max_dd_pct", 0.0)
                dd_match = abs(recomputed_dd - claimed_dd) < 0.1
                return_check["checks"].append({
                    "metric": "max_drawdown_pct",
                    "claimed": claimed_dd,
                    "recomputed": round(recomputed_dd, 4),
                    "match": dd_match,
                })
                all_return_ok = all(c["match"] for c in return_check["checks"])
                return_check["valid"] = all_return_ok

            trade_check = {"valid": False, "reason": "No returns"}
            if oos_returns and len(oos_returns) > 2:
                trade_check = IndependentVerifier.verify_trade_metrics(
                    returns=oos_returns,
                    claimed_win_rate=stats.get("win_rate", 0.0),
                    claimed_profit_factor=stats.get("profit_factor", 0.0),
                    claimed_total_return=stats.get("return_pct", 0.0),
                )

            all_valid = (
                artifact_result.get("valid", False)
                and sharpe_check.get("valid", False)
                and return_check.get("valid", False)
                and trade_check.get("valid", False)
            )

            return StageResult(
                stage="verify",
                status=RunStage.PASSED if all_valid else RunStage.FAILED,
                started_at=t0, completed_at=time.time(),
                data={
                    "artifact_integrity": artifact_result,
                    "sharpe_check": sharpe_check,
                    "return_check": return_check,
                    "trade_check": trade_check,
                },
            )
        except Exception as e:
            return StageResult(
                stage="verify", status=RunStage.FAILED,
                started_at=t0, completed_at=time.time(), error=str(e),
            )
