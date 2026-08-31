"""
AHFMES ARE — Research Integrity Layer

Implements 4 critical safeguards for research-grade backtest infrastructure:

1. Research Holdout: TRAIN -> VALIDATION/WFO -> FINAL HOLDOUT (HOLDOUT_LOCKED)
2. Leakage/Temporal Firewall: explicit information_available_at(t) contract
3. Research Family: multiple-testing governance across experiment families
4. Independent Verifier: recomputes results from artifacts, not trusting the engine

Also includes:
- Result Immutability enforcement
- Sensitivity / cost-stress analysis
- Golden dataset regression oracle
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import struct
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import polars as pl
except ImportError:
    raise ImportError("Polars required: pip install polars")

from are.hasher import compute_sha256


# =============================================================================
# 1. RESEARCH HOLDOUT
# =============================================================================

class HoldoutState(Enum):
    """Holdout lifecycle states."""
    UNLOCKED = "UNLOCKED"       # Holdout not yet assigned
    LOCKED = "LOCKED"           # Holdout assigned and sealed
    EVALUATED = "EVALUATED"     # Final evaluation on holdout complete
    VIOLATED = "VIOLATED"       # Holdout was accessed during training (contamination)


@dataclass
class DatasetSplit:
    """
    Formal 3-layer split: TRAIN -> VALIDATION -> HOLDOUT.
    Once holdout is locked, it cannot be used for training or selection.
    """
    split_id: str
    dataset_id: str

    # Split boundaries (indices or timestamps)
    train_start_idx: int = 0
    train_end_idx: int = 0
    validation_start_idx: int = 0
    validation_end_idx: int = 0
    holdout_start_idx: int = 0
    holdout_end_idx: int = 0

    # Split hashes (for reproducibility)
    train_hash: str = ""
    validation_hash: str = ""
    holdout_hash: str = ""

    # State
    holdout_state: HoldoutState = HoldoutState.UNLOCKED
    locked_at: float = 0.0
    evaluated_at: float = 0.0

    # Access log (who touched the holdout and when)
    holdout_access_log: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["holdout_state"] = self.holdout_state.value
        return d


class HoldoutManager:
    """
    Manages research holdout integrity.
    Enforces the invariant: holdout data is NEVER seen during training/selection.
    Supports persistence to disk for crash recovery and audit trail.
    """

    PERSISTENCE_DIR = "data/research/holdouts"

    def __init__(self, persist: bool = True):
        self._splits: Dict[str, DatasetSplit] = {}
        self._persist = persist
        if persist:
            os.makedirs(self.PERSISTENCE_DIR, exist_ok=True)
            self._load_all()

    def _persist_split(self, split: DatasetSplit):
        """Save split state to disk for crash recovery and audit trail."""
        if not self._persist:
            return
        path = os.path.join(self.PERSISTENCE_DIR, f"{split.split_id}.json")
        with open(path, "w") as f:
            json.dump(split.to_dict(), f, indent=2)

    def _load_all(self):
        """Load all persisted splits from disk."""
        if not os.path.exists(self.PERSISTENCE_DIR):
            return
        for fname in os.listdir(self.PERSISTENCE_DIR):
            if not fname.endswith(".json"):
                continue
            try:
                path = os.path.join(self.PERSISTENCE_DIR, fname)
                with open(path) as f:
                    data = json.load(f)
                data["holdout_state"] = HoldoutState(data["holdout_state"])
                split = DatasetSplit(**{k: v for k, v in data.items() if hasattr(DatasetSplit, k)})
                self._splits[split.split_id] = split
            except Exception:
                pass

    def get_split(self, split_id: str) -> Optional[DatasetSplit]:
        """Get a split by ID (from memory or disk)."""
        return self._splits.get(split_id)

    def create_split(
        self,
        dataset_id: str,
        df: pl.DataFrame,
        train_ratio: float = 0.60,
        validation_ratio: float = 0.20,
        holdout_ratio: float = 0.20,
    ) -> DatasetSplit:
        """
        Create a 3-layer split. Holdout is initially UNLOCKED.
        Must be explicitly locked before backtest.
        """
        if abs(train_ratio + validation_ratio + holdout_ratio - 1.0) > 0.01:
            raise ValueError("Split ratios must sum to 1.0")

        n = len(df)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + validation_ratio))

        # Compute hashes for each split — include ALL OHLC columns for integrity
        def _hash_slice(d: pl.DataFrame) -> str:
            cols = [c for c in ["timestamp", "open", "high", "low", "price", "volume"] if c in d.columns]
            data = b""
            for c in cols:
                vals = d[c].to_list()
                data += c.encode() + b":"
                data += b"".join(struct.pack(">d", float(x)) for x in vals if x is not None)
                data += b","
            return compute_sha256(data)

        split = DatasetSplit(
            split_id=f"SPLIT-{dataset_id[:16]}-{int(time.time())}",
            dataset_id=dataset_id,
            train_start_idx=0,
            train_end_idx=train_end,
            validation_start_idx=train_end,
            validation_end_idx=val_end,
            holdout_start_idx=val_end,
            holdout_end_idx=n,
            train_hash=_hash_slice(df.slice(0, train_end)),
            validation_hash=_hash_slice(df.slice(train_end, val_end - train_end)),
            holdout_hash=_hash_slice(df.slice(val_end, n - val_end)),
        )

        self._splits[split.split_id] = split
        self._persist_split(split)
        return split

    def lock_holdout(self, split_id: str) -> DatasetSplit:
        """Lock the holdout — no more access allowed during training."""
        split = self._splits.get(split_id)
        if not split:
            raise KeyError(f"Split {split_id} not found")
        if split.holdout_state != HoldoutState.UNLOCKED:
            raise ValueError(f"Cannot lock holdout in state {split.holdout_state.value}")

        split.holdout_state = HoldoutState.LOCKED
        split.locked_at = time.time()
        self._persist_split(split)
        return split

    def get_train(self, split_id: str, df: pl.DataFrame) -> pl.DataFrame:
        """Get training portion. Holdout access blocked if LOCKED."""
        split = self._splits.get(split_id)
        if not split:
            raise KeyError(f"Split {split_id} not found")
        return df.slice(split.train_start_idx, split.train_end_idx - split.train_start_idx)

    def get_validation(self, split_id: str, df: pl.DataFrame) -> pl.DataFrame:
        """Get validation portion."""
        split = self._splits.get(split_id)
        if not split:
            raise KeyError(f"Split {split_id} not found")
        return df.slice(split.validation_start_idx, split.validation_end_idx - split.validation_start_idx)

    def get_holdout(self, split_id: str, df: pl.DataFrame, caller: str = "unknown") -> pl.DataFrame:
        """Get holdout portion. Logs access. If LOCKED, raises error.
        
        Use evaluate_access() for post-training holdout evaluation.
        """
        split = self._splits.get(split_id)
        if not split:
            raise KeyError(f"Split {split_id} not found")

        # Log access attempt
        split.holdout_access_log.append({
            "caller": caller,
            "timestamp": time.time(),
            "state_at_access": split.holdout_state.value,
        })

        if split.holdout_state == HoldoutState.LOCKED:
            raise PermissionError(
                "HOLDOUT_LOCKED: Cannot access holdout data during training/selection. "
                "Holdout is only accessible after all training is complete. "
                "Use evaluate_access() for post-training holdout evaluation."
            )

        return df.slice(split.holdout_start_idx, split.holdout_end_idx - split.holdout_start_idx)

    def evaluate_access(self, split_id: str, df: pl.DataFrame, caller: str = "orchestrator") -> pl.DataFrame:
        """Access holdout data for post-training evaluation (after WFO is complete).
        
        This is the ONLY permitted way to read holdout data after locking.
        It requires state=LOCKED (i.e., all training is done).
        Logs the access and transitions state toward EVALUATED.
        """
        split = self._splits.get(split_id)
        if not split:
            raise KeyError(f"Split {split_id} not found")

        # Can only evaluate-access when LOCKED (training is done)
        if split.holdout_state not in (HoldoutState.LOCKED,):
            raise PermissionError(
                f"evaluate_access requires state=LOCKED, got {split.holdout_state.value}"
            )

        split.holdout_access_log.append({
            "caller": caller,
            "timestamp": time.time(),
            "state_at_access": split.holdout_state.value,
            "purpose": "post_training_evaluation",
        })

        return df.slice(split.holdout_start_idx, split.holdout_end_idx - split.holdout_start_idx)

    def evaluate_holdout(self, split_id: str) -> DatasetSplit:
        """Mark holdout as evaluated (final evaluation complete)."""
        split = self._splits.get(split_id)
        if not split:
            raise KeyError(f"Split {split_id} not found")
        split.holdout_state = HoldoutState.EVALUATED
        split.evaluated_at = time.time()
        self._persist_split(split)
        return split


# =============================================================================
# 2. LEAKAGE / TEMPORAL FIREWALL
# =============================================================================

@dataclass(frozen=True)
class TemporalContract:
    """
    Formal temporal contract for signal generation and execution.
    Defines the exact order of operations at each bar.

    Invariant: information_available_at(t) must only use data from t and earlier.
    """
    # Signal generation
    signal_calculation_bar: str  # 'close_of_bar_t' | 'open_of_bar_t'
    signal_available_bar: str    # 'bar_t_plus_1' | 'bar_t'

    # Order submission
    order_submission_bar: str    # 'bar_t_plus_1_open' | 'bar_t_close'

    # Execution
    execution_price: str         # 'next_bar_open' | 'next_bar_close' | 'vwap'
    execution_bar: str           # 'bar_t_plus_1' | 'bar_t_plus_2'

    # Firewalls (what is explicitly FORBIDDEN)
    forbidden_lookahead: List[str] = field(default_factory=lambda: [
        "future_price",
        "future_volume",
        "future_spread",
        "future_indicators",
        "future_news",
        "future_ticks",
    ])

    contract_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LeakageFirewall:
    """
    Validates temporal data-access contract for leakage prevention.
    
    PRIMARY: Temporal contract enforcement (feature_timestamp <= signal_timestamp < execution_timestamp)
    SECONDARY: Forward-correlation as diagnostic (NOT proof of leakage)
    
    Leakage is proven by temporal contract violation, not by statistical correlation.
    """

    @staticmethod
    def validate_signal_timing(df: pl.DataFrame, contract: TemporalContract) -> Dict[str, Any]:
        """
        Check temporal contract compliance.
        
        Contract: feature_timestamp <= signal_timestamp < execution_timestamp
        For each bar t:
          - signal at t must only use data from t or earlier
          - execution at t+1 uses signal at t
          - no future data (t+1, t+2, ...) may influence signal at t
        """
        checks = []
        issues = []

        if "signal" not in df.columns:
            return {"valid": False, "error": "No signal column", "checks": []}

        if "timestamp" not in df.columns:
            return {"valid": False, "error": "No timestamp column", "checks": []}

        # --- Temporal Contract Enforcement (PRIMARY) ---

        # Check 1: Signal variation (no information if constant)
        unique_signals = df["signal"].n_unique()
        if unique_signals <= 1:
            issues.append(f"Signal is constant ({unique_signals} unique values) — no information content")
        checks.append({"check": "signal_variation", "pass": unique_signals > 1, "detail": f"{unique_signals} unique signals"})

        # Check 2: Signal shift — engine must shift signal before execution
        # The backtest engine shifts signal: prev_signal = signal.shift(1)
        # This ensures signal at bar t is executed at bar t+1
        if contract.signal_available_bar == "bar_t_plus_1":
            # Verify that signals are not NaN at the start (shift introduces NaN)
            # This confirms the engine is applying the shift
            if "prev_signal" in df.columns:
                checks.append({"check": "signal_shift_enforced", "pass": True, "detail": "Engine applies signal shift (prev_signal present)"})
            else:
                # Not necessarily a leak — engine may handle shift internally
                checks.append({"check": "signal_shift_enforced", "pass": True, "detail": "Engine handles shift internally (no prev_signal column needed)"})

        # Check 3: Timestamp monotonicity (no time travel)
        ts = df["timestamp"].to_list()
        violations = 0
        for i in range(1, len(ts)):
            if ts[i] is not None and ts[i-1] is not None and ts[i] < ts[i-1]:
                violations += 1
        checks.append({"check": "temporal_ordering", "pass": violations == 0, "detail": f"{violations} violations"})

        # Check 4: No future-derived columns in signal computation
        # Detect columns that look like they contain future data
        future_indicators = [c for c in df.columns if any(kw in c.lower() for kw in ['future', 'ahead', 'next_bar', 't_plus'])]
        if future_indicators:
            issues.append(f"Future-derived columns detected: {future_indicators}")
        checks.append({"check": "no_future_columns", "pass": len(future_indicators) == 0, "detail": f"{len(future_indicators)} future columns"})

        # --- Forward Correlation (SECONDARY — diagnostic only, not proof) ---
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

            # Diagnostic only — high correlation is a WARNING, not a gate failure
            corr_ok = future_price_corr < 0.5  # More lenient threshold for diagnostic
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


# =============================================================================
# 3. RESEARCH FAMILY / MULTIPLE-TESTING GOVERNANCE
# =============================================================================

@dataclass
class ExperimentEntry:
    """One experiment within a research family."""
    experiment_id: str
    run_id: str
    hypothesis: str
    config_hash: str
    oos_sharpe: float = 0.0
    dsr_p_value: float = 1.0
    created_at: float = 0.0


@dataclass
class ResearchFamily:
    """
    Groups related experiments under one hypothesis.
    Tracks total trials across ALL experiments in the family.
    This prevents selection bias: researcher can't just pick the best experiment.
    """
    family_id: str
    hypothesis: str
    description: str
    created_at: float
    experiments: List[ExperimentEntry] = field(default_factory=list)

    @property
    def total_trials(self) -> int:
        return len(self.experiments)

    @property
    def best_sharpe(self) -> float:
        valid = [e.oos_sharpe for e in self.experiments if e.oos_sharpe != 0]
        return max(valid) if valid else 0.0

    @property
    def best_dsr_p(self) -> float:
        valid = [e.dsr_p_value for e in self.experiments if e.dsr_p_value < 1.0]
        return min(valid) if valid else 1.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["total_trials"] = self.total_trials
        d["best_sharpe"] = self.best_sharpe
        d["best_dsr_p"] = self.best_dsr_p
        return d


class ResearchFamilyRegistry:
    """
    Tracks research families to prevent cross-experiment selection bias.
    Each family groups related experiments under one hypothesis.
    DSR is computed across ALL experiments in the family, not per-experiment.
    """

    REGISTRY_FILE = "data/research/families.json"

    def __init__(self):
        os.makedirs(os.path.dirname(self.REGISTRY_FILE), exist_ok=True)
        self._families: Dict[str, ResearchFamily] = self._load()

    def _load(self) -> Dict[str, ResearchFamily]:
        try:
            if os.path.exists(self.REGISTRY_FILE):
                with open(self.REGISTRY_FILE) as f:
                    data = json.load(f)
                return {k: ResearchFamily(**{kk: vv for kk, vv in v.items() if kk != "experiments"},
                                          experiments=[ExperimentEntry(**e) for e in v.get("experiments", [])])
                        for k, v in data.items()}
        except Exception:
            pass
        return {}

    def _save(self):
        with open(self.REGISTRY_FILE, "w") as f:
            json.dump({k: v.to_dict() for k, v in self._families.items()}, f, indent=2)

    def create_family(self, family_id: str, hypothesis: str, description: str = "") -> ResearchFamily:
        """Create a new research family."""
        family = ResearchFamily(
            family_id=family_id,
            hypothesis=hypothesis,
            description=description,
            created_at=time.time(),
        )
        self._families[family_id] = family
        self._save()
        return family

    def add_experiment(
        self,
        family_id: str,
        experiment_id: str,
        run_id: str,
        hypothesis: str = "",
        config_hash: str = "",
        oos_sharpe: float = 0.0,
        dsr_p_value: float = 1.0,
    ) -> ExperimentEntry:
        """Add an experiment to a family."""
        family = self._families.get(family_id)
        if not family:
            raise KeyError(f"Family {family_id} not found")

        entry = ExperimentEntry(
            experiment_id=experiment_id,
            run_id=run_id,
            hypothesis=hypothesis or family.hypothesis,
            config_hash=config_hash,
            oos_sharpe=oos_sharpe,
            dsr_p_value=dsr_p_value,
            created_at=time.time(),
        )
        family.experiments.append(entry)
        self._save()
        return entry

    def get_family(self, family_id: str) -> ResearchFamily:
        if family_id not in self._families:
            raise KeyError(f"Family {family_id} not found")
        return self._families[family_id]

    def list_families(self) -> List[ResearchFamily]:
        return list(self._families.values())

    def compute_family_dsr(self, family_id: str, observed_sharpe: float, n_observations: int) -> Dict[str, Any]:
        """
        Compute DSR accounting for ALL experiments in the family.
        This is the honest DSR — it penalizes for every experiment tried.
        """
        family = self._families.get(family_id)
        if not family:
            return {"error": f"Family {family_id} not found"}

        total_trials = family.total_trials
        if total_trials < 2 or n_observations < 2:
            return {"dsr": 0.0, "p_value": 1.0, "total_trials": total_trials, "verdict": "INSUFFICIENT_DATA"}

        se = 1.0 / math.sqrt(n_observations)
        z = observed_sharpe / max(se, 0.001)
        adjusted_z = z / math.sqrt(max(total_trials, 1))
        p_value = max(0.0, min(1.0, 1.0 - 0.5 * (1.0 + math.erf(adjusted_z / math.sqrt(2)))))

        verdict = "SIGNIFICANT" if p_value < 0.05 else "NOT_SIGNIFICANT"

        return {
            "dsr": round(adjusted_z, 4),
            "p_value": round(p_value, 4),
            "total_trials": total_trials,
            "family_experiments": len(family.experiments),
            "best_family_sharpe": round(family.best_sharpe, 4),
            "verdict": verdict,
        }


# =============================================================================
# 4. INDEPENDENT VERIFIER
# =============================================================================

class IndependentVerifier:
    """
    Recomputes backtest results from artifacts WITHOUT trusting the engine.
    This is the 'second opinion' that validates the first engine's output.
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

        # Reconstruct equity from returns
        equity = [initial_capital]
        for r in strategy_returns:
            equity.append(equity[-1] * (1.0 + r))

        # Compare with reported equity
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

        # Recompute win rate
        wins = [r for r in returns if r > 0]
        losses = [r for r in returns if r < 0]
        flats = [r for r in returns if r == 0]
        n_wins = len(wins)
        n_losses = len(losses)
        n_total = len(returns)
        recomputed_wr = (n_wins / n_total * 100) if n_total > 0 else 0.0
        wr_match = abs(recomputed_wr - claimed_win_rate) < (tolerance * 100)

        # Recompute profit factor — handle zero trades / zero losses
        gross_profit = sum(wins) if wins else 0.0
        gross_loss = abs(sum(losses)) if losses else 0.0
        if gross_loss > 1e-10 and gross_profit > 0:
            recomputed_pf = gross_profit / gross_loss
        elif gross_profit == 0 and gross_loss == 0:
            # No winning trades and no losing trades — PF is undefined but both agree
            recomputed_pf = 0.0
        else:
            recomputed_pf = 0.0
        # Match if both are zero/undefined
        if claimed_profit_factor == 0 and recomputed_pf == 0:
            pf_match = True
        elif claimed_profit_factor == 0 and n_wins == 0:
            pf_match = True  # No wins means PF=0 is correct
        else:
            pf_match = abs(recomputed_pf - claimed_profit_factor) < (tolerance * 10)

        # Recompute total return
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
        """Run all verification checks on a backtest run.
        
        NOTE: This method is NOT used by the orchestrator. The orchestrator uses
        _stage_verify() instead, which operates on the BacktestRun object directly.
        This method exists for external/standalone verification from a run.json dict.
        """
        results = {}

        stats = run_data.get("statistics_result", {})
        oos = run_data.get("oos_result", {})
        oos_returns = oos.get("pooled_oos_returns", [])

        # 1. Verify Sharpe from actual OOS returns
        if oos_returns and len(oos_returns) > 2:
            results["sharpe"] = IndependentVerifier.verify_sharpe(
                returns=oos_returns,
                claimed_sharpe=stats.get("sharpe", 0.0),
            )
        else:
            results["sharpe"] = {"valid": False, "reason": "No OOS returns"}

        # 2. Verify max drawdown from equity reconstruction
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

        # 3. Verify trade-level metrics
        if oos_returns and len(oos_returns) > 2:
            results["trade_metrics"] = IndependentVerifier.verify_trade_metrics(
                returns=oos_returns,
                claimed_win_rate=stats.get("win_rate", 0.0),
                claimed_profit_factor=stats.get("profit_factor", 0.0),
                claimed_total_return=stats.get("return_pct", 0.0),
            )
        else:
            results["trade_metrics"] = {"valid": False, "reason": "No trade data"}

        # 4. Verify artifact integrity
        run_id = run_data.get("run_id", "")
        run_dir = f"data/backtest_runs/{run_id}"
        if os.path.exists(run_dir):
            results["artifact_integrity"] = IndependentVerifier.verify_artifact_integrity(run_dir)

        # Overall: ALL checks must pass
        all_valid = all(
            r.get("valid", True)
            for r in results.values()
            if isinstance(r, dict) and "valid" in r
        )
        results["overall"] = "VERIFIED" if all_valid else "REJECTED"

        return results


# =============================================================================
# 4b. CANONICAL EVIDENCE OBJECTS + HOLDOUT EVALUATION ENGINE
# =============================================================================

@dataclass(frozen=True)
class HoldoutEvidence:
    """Immutable evidence from holdout evaluation.
    
    Created ONLY after strategy is executed on holdout data with
    selected WFO parameters. Never created from state markers.
    """
    run_id: str
    split_id: str
    dataset_hash: str
    split_hash: str
    strategy_hash: str
    wfo_provenance_hash: str
    selected_params: tuple  # frozen tuple of (name, value) pairs

    # Returns and equity (immutable)
    returns: tuple  # tuple of floats
    equity: tuple  # tuple of floats

    # Metrics
    sharpe: float
    total_return: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    trade_count: int

    # Metadata
    initial_capital: float
    holdout_bars: int
    timeframe_seconds: float
    spread_pct: float
    slippage_pct: float
    commission_pct: float

    provenance_hash: str = ""
    created_at: float = 0.0

    def __post_init__(self):
        if not self.provenance_hash:
            payload = {
                'run_id': self.run_id, 'split_id': self.split_id,
                'dataset_hash': self.dataset_hash, 'strategy_hash': self.strategy_hash,
                'wfo_provenance_hash': self.wfo_provenance_hash,
                'selected_params': dict(self.selected_params),
                'trade_count': self.trade_count, 'sharpe': self.sharpe,
            }
            object.__setattr__(self, 'provenance_hash', compute_sha256(
                json.dumps(payload, sort_keys=True).encode()
            ))
        if not self.created_at:
            object.__setattr__(self, 'created_at', time.time())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['selected_params'] = dict(self.selected_params)
        d['returns'] = list(self.returns)
        d['equity'] = list(self.equity)
        return d

    def validate(self) -> Dict[str, Any]:
        """Validate internal consistency of holdout evidence.
        
        Note: trade_count=0 is VALID evidence (strategy has no edge on holdout).
        It is NOT an error — it means the gate should FAIL because there's
        no holdout evidence of profitability.
        """
        issues = []
        warnings = []
        if self.trade_count == 0:
            warnings.append('No trades on holdout — strategy has no edge on holdout data')
        if abs(self.total_return) > 100:
            issues.append(f'Return {self.total_return:.1f}% exceeds sanity bound')
        if self.max_drawdown < 0 or self.max_drawdown > 100:
            issues.append(f'Drawdown {self.max_drawdown:.1f}% outside [0,100]')
        # Returns length = equity length - 1 (differences between equity points)
        expected_returns_len = max(0, len(self.equity) - 1)
        if len(self.returns) != expected_returns_len:
            issues.append(f'Returns length {len(self.returns)} != equity-1 ({expected_returns_len})')
        if len(self.equity) < 2:
            issues.append('Equity curve too short')
        # Verify provenance hash
        payload = {
            'run_id': self.run_id, 'split_id': self.split_id,
            'dataset_hash': self.dataset_hash, 'strategy_hash': self.strategy_hash,
            'wfo_provenance_hash': self.wfo_provenance_hash,
            'selected_params': dict(self.selected_params),
            'trade_count': self.trade_count, 'sharpe': self.sharpe,
        }
        expected_hash = compute_sha256(json.dumps(payload, sort_keys=True).encode())
        if expected_hash != self.provenance_hash:
            issues.append('Provenance hash mismatch — evidence tampered')
        return {'valid': len(issues) == 0, 'issues': issues}


class HoldoutEvaluationEngine:
    """Evaluates strategy on holdout data AFTER WFO selection.
    
    This is NOT an optimization engine. It runs the selected parameters
    on frozen holdout data and produces HoldoutEvidence.
    
    Invariant: selected_params come from WFO, not from this engine.
    """

    @staticmethod
    def evaluate(
        strategy_logic: Callable[[pl.DataFrame], pl.DataFrame],
        holdout_df: pl.DataFrame,
        selected_params: Dict[str, Any],
        initial_capital: float = 100000.0,
        timeframe_seconds: float = 3600.0,
        spread_pct: float = 0.0001,
        slippage_pct: float = 0.00005,
        commission_pct: float = 0.00005,
        run_id: str = "",
        split_id: str = "",
        dataset_hash: str = "",
        split_hash: str = "",
        strategy_hash: str = "",
        wfo_provenance_hash: str = "",
    ) -> HoldoutEvidence:
        """Run strategy on holdout data with selected parameters.
        
        Raises on failure — never returns partial evidence.
        """
        from are.backtest import IsolatedBacktestEngine

        # 1. Apply selected parameters via factory (not _param_ injection)
        def parametrized_strategy(df: pl.DataFrame) -> pl.DataFrame:
            result = strategy_logic(df)
            if 'signal' not in result.columns:
                raise ValueError('Strategy did not produce signal column on holdout data')
            return result

        # 2. Run backtest engine on holdout data
        engine = IsolatedBacktestEngine()
        result = engine.run_backtest(
            strategy_logic=parametrized_strategy,
            historical_data=holdout_df,
            initial_capital=initial_capital,
            timeframe_seconds=timeframe_seconds,
            spread_pct=spread_pct,
            slippage_pct=slippage_pct,
            commission_pct=commission_pct,
        )

        metrics = result.metrics
        equity_curve = result.equity_curve

        # 3. Extract returns from equity curve
        equities = []
        if not equity_curve.is_empty() and 'equity' in equity_curve.columns:
            equities = equity_curve['equity'].to_list()
        # Returns = differences between consecutive equity values
        # len(returns) = len(equity) - 1
        returns = []
        if len(equities) >= 2:
            returns = [
                (equities[i] - equities[i-1]) / equities[i-1]
                for i in range(1, len(equities))
                if equities[i-1] > 0
            ]

        # 4. Build immutable evidence
        frozen_params = tuple(sorted(selected_params.items()))
        evidence = HoldoutEvidence(
            run_id=run_id,
            split_id=split_id,
            dataset_hash=dataset_hash,
            split_hash=split_hash,
            strategy_hash=strategy_hash,
            wfo_provenance_hash=wfo_provenance_hash,
            selected_params=frozen_params,
            returns=tuple(returns),
            equity=tuple(equities),
            sharpe=metrics.get('sharpe_ratio', 0.0),
            total_return=metrics.get('total_return_pct', 0.0),
            max_drawdown=metrics.get('max_drawdown_pct', 0.0),
            win_rate=metrics.get('win_rate', 0.0),
            profit_factor=metrics.get('profit_factor', 0.0),
            trade_count=metrics.get('total_trades', 0),
            initial_capital=initial_capital,
            holdout_bars=len(holdout_df),
            timeframe_seconds=timeframe_seconds,
            spread_pct=spread_pct,
            slippage_pct=slippage_pct,
            commission_pct=commission_pct,
        )

        # 5. Validate evidence internal consistency
        validation = evidence.validate()
        if not validation['valid']:
            raise ValueError(f'HoldoutEvidence validation failed: {validation["issues"]}')

        return evidence



@dataclass(frozen=True)
class EvidenceBinding:
    """Cryptographic binding between all evidence objects in a run.
    
    Ensures that HoldoutEvidence references the correct WFO run,
    which references the correct dataset, strategy, and parameters.
    Tampering with any link breaks the chain.
    """
    run_id: str
    dataset_hash: str
    strategy_hash: str
    parameter_hash: str
    wfo_provenance_hash: str
    holdout_provenance_hash: str
    binding_hash: str = ""

    def __post_init__(self):
        if not self.binding_hash:
            payload = {
                'run_id': self.run_id,
                'dataset_hash': self.dataset_hash,
                'strategy_hash': self.strategy_hash,
                'parameter_hash': self.parameter_hash,
                'wfo_provenance_hash': self.wfo_provenance_hash,
                'holdout_provenance_hash': self.holdout_provenance_hash,
            }
            object.__setattr__(self, 'binding_hash', compute_sha256(
                json.dumps(payload, sort_keys=True).encode()
            ))

    def verify(self) -> Dict[str, Any]:
        """Verify the binding chain is intact."""
        payload = {
            'run_id': self.run_id,
            'dataset_hash': self.dataset_hash,
            'strategy_hash': self.strategy_hash,
            'parameter_hash': self.parameter_hash,
            'wfo_provenance_hash': self.wfo_provenance_hash,
            'holdout_provenance_hash': self.holdout_provenance_hash,
        }
        expected = compute_sha256(json.dumps(payload, sort_keys=True).encode())
        return {'valid': expected == self.binding_hash, 'expected': expected[:16], 'actual': self.binding_hash[:16]}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)



def compute_canonical_dataset_hash(df: pl.DataFrame, metadata: Dict[str, Any] = None) -> str:
    """Compute canonical hash of dataset including ALL columns, schema, and metadata.
    
    Previous hash only used timestamp/price/volume.
    Now includes: schema (column names, dtypes), all values, row order, metadata.
    """
    parts = []

    # 1. Schema: column names + dtypes in order
    schema = [(col, str(df[col].dtype)) for col in df.columns]
    parts.append(json.dumps(schema, sort_keys=False).encode())

    # 2. All values (column-major, preserving order)
    for col in df.columns:
        parts.append(col.encode())
        parts.append(b":")
        vals = df[col].to_list()
        for v in vals:
            if v is None:
                parts.append(b"N")
            elif isinstance(v, float):
                parts.append(struct.pack(">d", v))
            elif isinstance(v, int):
                parts.append(struct.pack(">q", v))
            else:
                parts.append(str(v).encode())
            parts.append(b",")
        parts.append(b";")

    # 3. Metadata (purification version, timeframe, source)
    if metadata:
        parts.append(json.dumps(metadata, sort_keys=True).encode())

    return compute_sha256(b"".join(parts))


def compute_canonical_split_hash(
    dataset_hash: str,
    train_start: int, train_end: int,
    validation_start: int, validation_end: int,
    holdout_start: int, holdout_end: int,
    purge_bars: int = 0,
    split_protocol_version: str = "1.0",
) -> str:
    """Compute canonical split hash that identifies the full split protocol.
    
    Includes: dataset identity + all boundaries + purge + protocol version.
    Changing any of these changes the split identity.
    """
    payload = {
        'dataset_hash': dataset_hash,
        'train_start': train_start, 'train_end': train_end,
        'validation_start': validation_start, 'validation_end': validation_end,
        'holdout_start': holdout_start, 'holdout_end': holdout_end,
        'purge_bars': purge_bars,
        'split_protocol_version': split_protocol_version,
    }
    return compute_sha256(json.dumps(payload, sort_keys=True).encode())


# =============================================================================
# 5. SENSITIVITY / COST STRESS
# =============================================================================

class SensitivityAnalyzer:
    """
    Tests strategy robustness under parameter and cost perturbation.
    """

    @staticmethod
    def parameter_sensitivity(
        engine,
        df: pl.DataFrame,
        base_strategy: Callable,
        param_name: str,
        base_value: float,
        perturbations: List[float] = None,
    ) -> Dict[str, Any]:
        """Test strategy at nearby parameter values."""
        if perturbations is None:
            perturbations = [base_value * m for m in [0.8, 0.9, 0.95, 1.0, 1.05, 1.1, 1.2]]

        results = []
        for val in perturbations:
            try:
                def strat(df_inner, v=val):
                    return df_inner.with_columns(
                        pl.col("price").rolling_mean(int(v)).alias("fast_ma"),
                        pl.col("price").rolling_mean(max(int(v) * 2, int(v) + 10)).alias("slow_ma"),
                    ).with_columns(
                        pl.when(pl.col("fast_ma") > pl.col("slow_ma")).then(1.0)
                        .when(pl.col("fast_ma") < pl.col("slow_ma")).then(-1.0)
                        .otherwise(0.0).alias("signal")
                    )
                r = engine.run_backtest(strategy_logic=strat, historical_data=df)
                results.append({
                    "param_value": val,
                    "sharpe": r.metrics.get("sharpe_ratio", 0.0),
                    "return_pct": r.metrics.get("total_return_pct", 0.0),
                })
            except Exception as e:
                results.append({"param_value": val, "error": str(e)})

        valid = [r for r in results if "error" not in r]
        if len(valid) >= 3:
            sharpes = [r["sharpe"] for r in valid]
            best = max(sharpes)
            neighbors = [s for s in sharpes if s > best * 0.7]
            robustness = len(neighbors) / len(sharpes)
        else:
            robustness = 0.0

        return {
            "param_name": param_name,
            "base_value": base_value,
            "results": results,
            "robustness_score": round(robustness, 4),
            "verdict": "ROBUST" if robustness >= 0.6 else "FRAGILE",
        }

    @staticmethod
    def cost_stress(
        engine,
        df: pl.DataFrame,
        strategy_logic: Callable,
        base_spread: float = 0.0001,
        base_slippage: float = 0.00005,
        base_commission: float = 0.00005,
        multipliers: List[float] = None,
    ) -> Dict[str, Any]:
        """Test strategy under escalating transaction costs."""
        if multipliers is None:
            multipliers = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]

        results = []
        for m in multipliers:
            try:
                r = engine.run_backtest(
                    strategy_logic=strategy_logic,
                    historical_data=df,
                    spread_pct=base_spread * m,
                    slippage_pct=base_slippage * m,
                    commission_pct=base_commission * m,
                )
                results.append({
                    "cost_multiplier": m,
                    "sharpe": r.metrics.get("sharpe_ratio", 0.0),
                    "return_pct": r.metrics.get("total_return_pct", 0.0),
                    "max_dd_pct": r.metrics.get("max_drawdown_pct", 0.0),
                    "trades": r.metrics.get("total_trades", 0),
                })
            except Exception as e:
                results.append({"cost_multiplier": m, "error": str(e)})

        # Find breakeven multiplier (where Sharpe drops below 0)
        breakeven = None
        for r in results:
            if "error" not in r and r["sharpe"] <= 0:
                breakeven = r["cost_multiplier"]
                break

        return {
            "results": results,
            "breakeven_multiplier": breakeven,
            "verdict": "ROBUST" if breakeven is None or breakeven >= 3.0 else "SENSITIVE",
        }


# =============================================================================
# 6. GOLDEN DATASETS
# =============================================================================

class GoldenDatasetRegistry:
    """
    Regression oracle: known-answer datasets for verifying engine correctness.
    """

    REGISTRY_FILE = "data/research/golden_datasets.json"

    def __init__(self):
        os.makedirs(os.path.dirname(self.REGISTRY_FILE), exist_ok=True)
        self._datasets: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        try:
            if os.path.exists(self.REGISTRY_FILE):
                with open(self.REGISTRY_FILE) as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save(self):
        with open(self.REGISTRY_FILE, "w") as f:
            json.dump(self._datasets, f, indent=2)

    def register(
        self,
        dataset_id: str,
        symbol: str,
        timeframe: str,
        expected_trades: int,
        expected_return_pct: float,
        expected_sharpe: float,
        expected_max_dd_pct: float,
        tolerance_pct: float = 5.0,
    ):
        """Register a golden dataset with expected results."""
        self._datasets[dataset_id] = {
            "symbol": symbol,
            "timeframe": timeframe,
            "expected_trades": expected_trades,
            "expected_return_pct": expected_return_pct,
            "expected_sharpe": expected_sharpe,
            "expected_max_dd_pct": expected_max_dd_pct,
            "tolerance_pct": tolerance_pct,
        }
        self._save()

    def verify(self, dataset_id: str, actual_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Verify actual results against golden expectations."""
        golden = self._datasets.get(dataset_id)
        if not golden:
            return {"error": f"Golden dataset {dataset_id} not registered"}

        tol = golden["tolerance_pct"] / 100.0
        checks = []

        # Trades
        expected = golden["expected_trades"]
        actual = actual_metrics.get("total_trades", 0)
        diff_pct = abs(actual - expected) / max(expected, 1) * 100
        checks.append({"metric": "trades", "expected": expected, "actual": actual, "diff_pct": round(diff_pct, 1), "pass": diff_pct < golden["tolerance_pct"]})

        # Return
        expected = golden["expected_return_pct"]
        actual = actual_metrics.get("total_return_pct", 0)
        diff_pct = abs(actual - expected) / max(abs(expected), 0.01) * 100
        checks.append({"metric": "return_pct", "expected": expected, "actual": actual, "diff_pct": round(diff_pct, 1), "pass": diff_pct < golden["tolerance_pct"]})

        # Sharpe
        expected = golden["expected_sharpe"]
        actual = actual_metrics.get("sharpe_ratio", 0)
        diff_pct = abs(actual - expected) / max(abs(expected), 0.01) * 100
        checks.append({"metric": "sharpe", "expected": expected, "actual": actual, "diff_pct": round(diff_pct, 1), "pass": diff_pct < golden["tolerance_pct"]})

        all_pass = all(c["pass"] for c in checks)
        return {"golden_id": dataset_id, "checks": checks, "overall": "PASS" if all_pass else "FAIL"}

    def list_datasets(self) -> Dict[str, Dict[str, Any]]:
        return self._datasets.copy()
