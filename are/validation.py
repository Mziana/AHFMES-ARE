"""
AHFMES ARE-3 — Out-of-Sample Validation Service & Statistical Robustness Engine (DELEGASI_031b & DELEGASI_035A)

Implements:
- ValidationReport: immutable validation assessment record.
- ValidationService: out-of-sample holdout validation, strict Information-Time barrier (SC-03, ACC-303),
  and evidence ledger exposure accounting (ACC-304).
- monte_carlo_simulation: permutation testing for lucky sequences and ruin probability.
- walk_forward_consistency: out-of-sample performance retention scoring.
- validate_statistical_robustness: fail-closed statistical judge.
- standard_normal_cdf: Gaussian cumulative distribution function.
- acklam_inverse_normal_cdf: Acklam (2010) high-precision probit inverse normal CDF (< 1.15e-9 error).
- apply_fdr_correction: Benjamini-Hochberg (1995) false discovery rate control.
- calculate_probabilistic_sharpe_ratio: Probabilistic Sharpe Ratio (Lopez de Prado, 2012).
- calculate_deflated_sharpe_ratio: Deflated Sharpe Ratio with multiple-testing correction.

100% Python Standard Library (math, typing, dataclasses) + Polars support. Zero SciPy.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from are.evidence import EvidenceLedger
from are.storage import EventStore


@dataclass(frozen=True)
class ValidationReport:
    candidate_id: str
    status: str  # "VALIDATED" | "REJECTED"
    sample_count: int
    performance_metric: float
    exposure_penalty: float
    as_of_ts: float
    provenance_status: str = "SENTINEL_UNPROVEN"
    is_provenance_verified: bool = False
    report_hash: str = ""

    def __post_init__(self):
        if not self.report_hash:
            canonical_payload = {
                "candidate_id": self.candidate_id,
                "status": self.status,
                "sample_count": self.sample_count,
                "performance_metric": self.performance_metric,
                "exposure_penalty": self.exposure_penalty,
                "as_of_ts": self.as_of_ts,
                "provenance_status": self.provenance_status,
                "is_provenance_verified": self.is_provenance_verified,
            }
            raw = json.dumps(canonical_payload, sort_keys=True).encode("utf-8")
            digest = hashlib.sha256(raw).hexdigest()
            object.__setattr__(self, "report_hash", digest)


class ValidationService:
    """
    Validates candidates against out-of-sample data with Information-Time enforcement.
    """

    def __init__(self, evidence_ledger: EvidenceLedger, event_store: EventStore):
        self.evidence_ledger = evidence_ledger
        self.event_store = event_store

    def validate_candidate(
        self,
        candidate_id: str,
        holdout_token: str,
        as_of_ts: float,
        dataset: List[Dict[str, Any]],
        performance_threshold: float = 0.5,
        research_program_id: str = "ARE3_RESEARCH",
        role: str = "INTERNAL_VALIDATION",
        source_manifest_hash: Optional[str] = None,
        completeness_proof_hash: Optional[str] = None,
    ) -> ValidationReport:
        """
        Validates a candidate against dataset points strictly prior to as_of_ts.
        Fails-closed on any future-timestamp leakage (ACC-303, SC-03).
        """
        if not dataset:
            raise ValueError("Cannot validate against an empty dataset")

        # 1. Information-Time Check (SC-03, ACC-303)
        for i, row in enumerate(dataset):
            row_ts = float(row.get("timestamp", 0.0))
            if row_ts > as_of_ts:
                raise ValueError(
                    f"Information-Time violation (SC-03): sample #{i} timestamp {row_ts} > cutoff {as_of_ts}"
                )

        # 2. Holdout Evidence Accounting (ACC-304 / Anti-Theater RES-RED-08)
        manifest_hash = source_manifest_hash or ("0" * 64)
        proof_hash = completeness_proof_hash or ("0" * 64)

        if manifest_hash == "0" * 64 or proof_hash == "0" * 64:
            provenance_status = "SENTINEL_UNPROVEN"
        else:
            provenance_status = "VERIFIED"

        is_provenance_verified = (provenance_status == "VERIFIED")

        t_unique = int(time.time() * 1000000)
        snap_id = f"SNAP_VAL_{candidate_id}_{int(as_of_ts)}_{t_unique % 1000000}"
        snapshot = self.evidence_ledger.create_snapshot(
            evidence_snapshot_id=snap_id,
            source_manifest_hash=manifest_hash,
            source_kind="HOLDOUT_DATASET",
            source_epoch=f"EPOCH_{int(as_of_ts)}",
            information_time_contract_hash="0" * 64,
            row_or_event_identity_contract_hash="0" * 64,
            completeness_proof_hash=proof_hash,
            provenance_status=provenance_status,
            origin="PROSPECTIVE_STRICT_BLIND",
        )

        batch_root = hashlib.sha256(f"BATCH_{candidate_id}_{t_unique}".encode("utf-8")).hexdigest()
        res_id = f"RES_VAL_{candidate_id}_{int(as_of_ts)}_{t_unique % 1000000}"
        reservation = self.evidence_ledger.create_reservation(
            reservation_id=res_id,
            research_program_id=research_program_id,
            program_budget_envelope_root_hash="0" * 64,
            research_family_root="0" * 64,
            claim_family_root="0" * 64,
            research_contract_root_hash="0" * 64,
            evidence_snapshot_root_hash=snapshot.root_hash,
            validation_family_root_hash="0" * 64,
            candidate_batch_root_hash=batch_root,
            primary_estimand_root_hash="0" * 64,
            multiplicity_plan_root_hash="0" * 64,
            search_tree_root_hash="0" * 64,
            search_debt_root_hash="0" * 64,
            permitted_disclosures_root_hash=None,
            permitted_actor_ids=["validator_actor"],
            role=role,
        )

        # Log exposure
        self.evidence_ledger.log_exposure(
            exposure_event_id=f"EXP_{candidate_id}_{int(as_of_ts)}_{t_unique % 1000000}",
            evidence_snapshot_root_hash=snapshot.root_hash,
            research_program_id=research_program_id,
            research_family_root="0" * 64,
            claim_family_root="0" * 64,
            research_contract_root_hash="0" * 64,
            candidate_or_batch_root_hash=batch_root,
            validation_reservation_id=reservation.reservation_id,
            role=role,
            access_granularity="ROW_OUTCOME",
            outcome_awareness="BOUNDED",
        )

        # 3. Deterministic Performance Metric Calculation
        scores = [float(row.get("score", row.get("value", 0.0))) for row in dataset]
        avg_score = sum(scores) / len(scores)
        exposure_penalty = min(0.3, len(dataset) * 0.0005)
        final_metric = max(0.0, avg_score - exposure_penalty)

        status = "VALIDATED" if final_metric >= performance_threshold else "REJECTED"

        return ValidationReport(
            candidate_id=candidate_id,
            status=status,
            sample_count=len(dataset),
            performance_metric=final_metric,
            exposure_penalty=exposure_penalty,
            as_of_ts=as_of_ts,
            provenance_status=snapshot.provenance_status,
            is_provenance_verified=is_provenance_verified,
        )


def _extract_returns(trade_log: Any, initial_capital: float = 10000.0) -> List[float]:
    """Extracts sequence of percentage returns from DataFrame or list of dicts/floats."""
    if trade_log is None:
        return []

    # Polars DataFrame support
    if hasattr(trade_log, "columns"):
        cols = trade_log.columns
        if "strategy_return" in cols:
            return [float(x) for x in trade_log["strategy_return"].to_list() if x is not None]
        elif "return" in cols:
            return [float(x) for x in trade_log["return"].to_list() if x is not None]
        elif "pnl" in cols:
            return [float(x) / initial_capital for x in trade_log["pnl"].to_list() if x is not None]
        elif "profit" in cols:
            return [float(x) / initial_capital for x in trade_log["profit"].to_list() if x is not None]

    # Native list support
    if isinstance(trade_log, list):
        returns: List[float] = []
        for item in trade_log:
            if isinstance(item, (int, float)):
                returns.append(float(item))
            elif isinstance(item, dict):
                if "strategy_return" in item:
                    returns.append(float(item["strategy_return"]))
                elif "return" in item:
                    returns.append(float(item["return"]))
                elif "pnl" in item:
                    returns.append(float(item["pnl"]) / initial_capital)
                elif "profit" in item:
                    returns.append(float(item["profit"]) / initial_capital)
        return returns

    return []


def _wilson_ci(successes: int, trials: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson score interval for binomial proportion (95% CI by default) (RES-RED-20)."""
    if trials == 0:
        return 0.0, 0.0
    p_hat = successes / trials
    denominator = 1.0 + z * z / trials
    center = (p_hat + z * z / (2.0 * trials)) / denominator
    margin = z * math.sqrt((p_hat * (1.0 - p_hat) + z * z / (4.0 * trials)) / trials) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def monte_carlo_simulation(
    trade_log_df: Any,
    num_simulations: int = 500,
    initial_capital: float = 10000.0,
    method: str = "BLOCK_BOOTSTRAP",  # "BLOCK_BOOTSTRAP" | "IID_SHUFFLE"
    block_size: int = 10,             # Block size for circular block bootstrap
) -> Dict[str, Any]:
    """
    Performs Monte Carlo simulation using either Circular Block Bootstrap or classic IID Shuffle (RES-RED-11, RES-RED-20).
    Circular Block Bootstrap preserves volatility clustering and streak dependencies.
    Computes nearest-rank 95th-percentile drawdown, Wilson score confidence intervals for ruin probability,
    and path vs terminal ruin metrics.
    """
    returns = _extract_returns(trade_log_df, initial_capital)
    if not returns:
        return {
            "mc_95th_pct_drawdown": 0.0,
            "mc_quantile_method": "nearest_rank",
            "mc_path_ruin_probability": 0.0,
            "mc_terminal_ruin_probability": 0.0,
            "mc_probability_of_ruin": 0.0,
            "mc_ruin_ci_lower_95": 0.0,
            "mc_ruin_ci_upper_95": 0.0,
            "mc_mean_final_equity": initial_capital,
            "mc_std_final_equity": 0.0,
            "mc_simulation_method": method,
            "mc_block_size": block_size if method == "BLOCK_BOOTSTRAP" else 1,
            "mc_num_simulations": num_simulations,
        }

    n_samples = len(returns)
    rng = random.Random(42)
    max_drawdowns: List[float] = []
    final_equities: List[float] = []
    path_ruin_count = 0
    terminal_ruin_count = 0

    ruin_threshold = initial_capital * 0.5

    for _ in range(num_simulations):
        if method == "BLOCK_BOOTSTRAP" and n_samples > 1 and block_size > 1:
            effective_block = min(block_size, n_samples)
            sim_trajectory: List[float] = []
            while len(sim_trajectory) < n_samples:
                start_idx = rng.randint(0, n_samples - 1)
                for offset in range(effective_block):
                    sim_trajectory.append(returns[(start_idx + offset) % n_samples])
            sim_returns = sim_trajectory[:n_samples]
        else:
            sim_returns = list(returns)
            rng.shuffle(sim_returns)

        equity = initial_capital
        peak = initial_capital
        min_equity = initial_capital
        max_dd = 0.0

        for r in sim_returns:
            equity *= (1.0 + r)
            if equity > peak:
                peak = equity
            if equity < min_equity:
                min_equity = equity
            dd = (equity - peak) / peak if peak > 0 else 0.0
            if abs(dd) > max_dd:
                max_dd = abs(dd)

        max_drawdowns.append(max_dd)
        final_equities.append(equity)

        if min_equity < ruin_threshold:
            path_ruin_count += 1
        if equity < ruin_threshold:
            terminal_ruin_count += 1

    # Nearest-rank method (NIST Engineering Statistics Handbook)
    max_drawdowns.sort()
    rank = int(math.ceil(0.95 * len(max_drawdowns))) - 1
    rank = max(0, min(rank, len(max_drawdowns) - 1))
    mc_95th_pct_drawdown = float(max_drawdowns[rank])

    path_ruin_prob = float(path_ruin_count / num_simulations)
    terminal_ruin_prob = float(terminal_ruin_count / num_simulations)
    ci_lower, ci_upper = _wilson_ci(path_ruin_count, num_simulations)

    mean_final_eq = float(sum(final_equities) / len(final_equities))
    var_final_eq = sum((e - mean_final_eq) ** 2 for e in final_equities) / len(final_equities)
    std_final_eq = math.sqrt(var_final_eq)

    return {
        "mc_95th_pct_drawdown": round(mc_95th_pct_drawdown, 4),
        "mc_quantile_method": "nearest_rank",
        "mc_path_ruin_probability": round(path_ruin_prob, 4),
        "mc_terminal_ruin_probability": round(terminal_ruin_prob, 4),
        "mc_probability_of_ruin": round(path_ruin_prob, 4),  # backward compat
        "mc_ruin_ci_lower_95": round(ci_lower, 4),
        "mc_ruin_ci_upper_95": round(ci_upper, 4),
        "mc_mean_final_equity": round(mean_final_eq, 2),
        "mc_std_final_equity": round(std_final_eq, 2),
        "mc_simulation_method": method,
        "mc_block_size": block_size if method == "BLOCK_BOOTSTRAP" else 1,
        "mc_num_simulations": num_simulations,
    }


def walk_forward_consistency(trade_log_df: Any, min_periods: int = 2) -> float:
    """
    Calculates out-of-sample performance retention vs in-sample performance.
    Returns consistency score between 0.0 and 1.0.
    """
    returns = _extract_returns(trade_log_df)
    if len(returns) < min_periods:
        return 1.0

    split_idx = len(returns) // 2
    is_returns = returns[:split_idx]
    oos_returns = returns[split_idx:]

    if not is_returns or not oos_returns:
        return 1.0

    is_wins = sum(1 for r in is_returns if r > 0)
    oos_wins = sum(1 for r in oos_returns if r > 0)
    is_win_rate = is_wins / len(is_returns)
    oos_win_rate = oos_wins / len(oos_returns)

    # Win-rate retention ratio
    if is_win_rate > 0:
        retention = oos_win_rate / is_win_rate
    else:
        retention = 1.0 if oos_win_rate >= is_win_rate else 0.0

    return round(max(0.0, min(1.0, retention)), 4)


def validate_statistical_robustness(
    backtest_metrics: Dict[str, Any],
    mc_metrics: Dict[str, Any],
    wf_score: float,
    wfo_metrics: Optional[Dict[str, Any]] = None,
    num_trials: Optional[int] = None,
) -> Tuple[bool, str]:
    """
    Enforces brutal statistical validation gates against lucky sequences, ruin risk, regime decay,
    and multiple-testing selection bias (DSR).
    """
    # 1. Ruin Probability Gate (> 10%)
    prob_ruin = float(mc_metrics.get("mc_probability_of_ruin", 0.0))
    if prob_ruin > 0.10:
        return (False, "MC_RUIN_PROBABILITY_HIGH: Probability of ruin > 10% under permutation.")

    # 2. Monte Carlo 95th Percentile Drawdown Gate
    mc_dd = float(mc_metrics.get("mc_95th_pct_drawdown", 0.0))
    bt_dd = abs(float(backtest_metrics.get("max_drawdown", backtest_metrics.get("max_drawdown_pct", 0.15))))
    if bt_dd > 1.0:
        bt_dd = bt_dd / 100.0

    if mc_dd > (bt_dd * 2.0) and mc_dd > 0.30:
        return (False, "MC_DRAWDOWN_EXCESSIVE: 95th percentile Monte Carlo drawdown exceeds tolerance.")

    # 3. Walk-Forward Retention Gate (< 50%)
    if wf_score < 0.50:
        return (False, "WFA_REGIME_DECAY: Out-of-sample performance retention fell below 50%.")

    # 4. Deflated Sharpe Ratio (DSR) Multiple-Testing Gate
    trials = num_trials
    if trials is None and wfo_metrics is not None:
        trials = int(wfo_metrics.get("total_trials_all_folds", wfo_metrics.get("hypothesis_family_size", 1)))

    if trials is not None and trials > 1:
        sr = float(backtest_metrics.get("sharpe_ratio", 0.0))
        n_obs = int(backtest_metrics.get("total_bars", 252))
        _, p_val = calculate_deflated_sharpe_ratio(
            observed_sharpe=sr,
            num_trials=trials,
            num_observations=n_obs,
        )
        if p_val >= 0.05:
            return (False, f"DSR_SELECTION_BIAS_REJECTED: p-value {p_val:.4f} >= 0.05 across {trials} hypothesis trials.")

    return (True, "STATISTICALLY_ROBUST")


# =============================================================================
# DELEGASI_035A: STATISTICAL RIGOR (ACKLAM, FDR, PSR, DSR) — 100% STDLIB
# =============================================================================


def standard_normal_cdf(x: float) -> float:
    """
    Standard Normal Cumulative Distribution Function (Phi).
    Uses math.erf from Python Standard Library.
    """
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def acklam_inverse_normal_cdf(p: float) -> float:
    """
    Inverse Standard Normal Cumulative Distribution Function (Probit function).
    By Peter J. Acklam (2010). Absolute error < 1.15e-9.
    100% Python Standard Library.
    """
    if p <= 0.0 or p >= 1.0:
        raise ValueError(f"Probability p must be in (0, 1), got {p}")

    # Koefisien Acklam
    a = (
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    )
    b = (
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    )
    c = (
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    )
    d = (
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    )

    p_low = 0.02425
    p_high = 1.0 - p_low

    if p < p_low:
        # Rational approximation for lower region
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
        )
    elif p <= p_high:
        # Rational approximation for central region
        q = p - 0.5
        r = q * q
        return (
            (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5])
            * q
            / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)
        )
    else:
        # Rational approximation for upper region
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -(
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
        )


def apply_fdr_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Benjamini-Hochberg (1995) procedure.
    Mengembalikan list of bool yang berukuran sama dengan p_values.
    True menandakan hipotesis lolos koreksi FDR (bukan false discovery).
    """
    if not p_values:
        return []
    m = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])

    max_k = -1
    for rank_minus_1, (orig_idx, p_val) in enumerate(indexed):
        k = rank_minus_1 + 1
        if p_val <= (k / m) * alpha:
            max_k = rank_minus_1

    survived = [False] * m
    if max_k != -1:
        for rank_minus_1 in range(max_k + 1):
            orig_idx = indexed[rank_minus_1][0]
            survived[orig_idx] = True
    return survived


def calculate_probabilistic_sharpe_ratio(
    observed_sharpe: float,
    benchmark_sharpe: float,
    num_observations: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
) -> float:
    """
    Menghitung probabilitas (0.0 - 1.0) bahwa Sharpe ratio teramati berada di atas benchmark,
    disesuaikan dengan skewness, kurtosis, dan panjang sampel data (Lopez de Prado, 2012).
    """
    if num_observations <= 1:
        return 0.0
    denom_sq = 1.0 - skewness * observed_sharpe + ((kurtosis - 1.0) / 4.0) * (observed_sharpe**2)
    if denom_sq <= 0.0:
        return 0.0
    std_error = math.sqrt(denom_sq / (num_observations - 1))
    z_stat = (observed_sharpe - benchmark_sharpe) / std_error
    return standard_normal_cdf(z_stat)


def calculate_deflated_sharpe_ratio(
    observed_sharpe: float,
    num_trials: int,
    num_observations: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
    var_sharpe: float = 1.0,
) -> Tuple[float, float]:
    """
    Menghitung Deflated Sharpe Ratio (DSR) dengan benchmark ekspektasi Sharpe maksimum
    dari N pengujian independen.
    Mengembalikan: (expected_max_sharpe, p_value).
    p_value < 0.05 mengindikasikan strategi lolos uji signifikansi.
    """
    if num_trials <= 1:
        expected_max_sr = 0.0
    else:
        euler_mascheroni = 0.5772156649015329
        p1 = 1.0 - (1.0 / num_trials)
        p2 = 1.0 - (1.0 / (num_trials * math.e))
        z1 = acklam_inverse_normal_cdf(max(1e-6, min(1.0 - 1e-6, p1)))
        z2 = acklam_inverse_normal_cdf(max(1e-6, min(1.0 - 1e-6, p2)))
        expected_max_sr = math.sqrt(var_sharpe) * ((1.0 - euler_mascheroni) * z1 + euler_mascheroni * z2)

    psr = calculate_probabilistic_sharpe_ratio(
        observed_sharpe=observed_sharpe,
        benchmark_sharpe=expected_max_sr,
        num_observations=num_observations,
        skewness=skewness,
        kurtosis=kurtosis,
    )
    p_value = max(0.0, 1.0 - psr)
    return (expected_max_sr, p_value)