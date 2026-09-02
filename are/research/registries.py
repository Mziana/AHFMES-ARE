"""
AHFMES ARE — Research Registries

Golden dataset regression oracle and research family governance.
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


# =============================================================================
# RESEARCH FAMILY / MULTIPLE-TESTING GOVERNANCE
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
    """Tracks research families to prevent cross-experiment selection bias."""

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
        """Compute DSR accounting for ALL experiments in the family."""
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
# GOLDEN DATASETS
# =============================================================================

class GoldenDatasetRegistry:
    """Regression oracle: known-answer datasets for verifying engine correctness."""

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
        golden = self._datasets.get(dataset_id)
        if not golden:
            return {"error": f"Golden dataset {dataset_id} not registered"}

        tol = golden["tolerance_pct"] / 100.0
        checks = []

        expected = golden["expected_trades"]
        actual = actual_metrics.get("total_trades", 0)
        diff_pct = abs(actual - expected) / max(expected, 1) * 100
        checks.append({"metric": "trades", "expected": expected, "actual": actual, "diff_pct": round(diff_pct, 1), "pass": diff_pct < golden["tolerance_pct"]})

        expected = golden["expected_return_pct"]
        actual = actual_metrics.get("total_return_pct", 0)
        diff_pct = abs(actual - expected) / max(abs(expected), 0.01) * 100
        checks.append({"metric": "return_pct", "expected": expected, "actual": actual, "diff_pct": round(diff_pct, 1), "pass": diff_pct < golden["tolerance_pct"]})

        expected = golden["expected_sharpe"]
        actual = actual_metrics.get("sharpe_ratio", 0)
        diff_pct = abs(actual - expected) / max(abs(expected), 0.01) * 100
        checks.append({"metric": "sharpe", "expected": expected, "actual": actual, "diff_pct": round(diff_pct, 1), "pass": diff_pct < golden["tolerance_pct"]})

        all_pass = all(c["pass"] for c in checks)
        return {"golden_id": dataset_id, "checks": checks, "overall": "PASS" if all_pass else "FAIL"}

    def list_datasets(self) -> Dict[str, Dict[str, Any]]:
        return self._datasets.copy()
