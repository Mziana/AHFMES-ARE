"""
AHFMES ARE — Alpha Hypothesis Schema & Strict Parameter Validator (DELEGASI_031)

Defines the declarative data schema for parameterized alpha strategies (AlphaSeed).
Guarantees 100% fail-closed validation with zero dynamic Python code generation/execution.
100% Python Standard Library.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Set

VALID_ASSET_CLASSES: Set[str] = {
    "FOREX",
    "CRYPTO",
    "COMMODITY",
    "EQUITY",
    "INDICES",
}


class InvalidHypothesisError(Exception):
    """Dilempar saat parameter strategi melanggar batas validasi."""


@dataclass(frozen=True)
class AlphaSeed:
    strategy_id: str
    asset_class: str                  # "FOREX" | "CRYPTO" | "COMMODITY" | "EQUITY" | "INDICES"
    indicators: List[Dict[str, Any]]  # e.g., [{"name": "RSI", "period": 14}]
    entry_conditions: List[str]       # e.g., ["RSI < 30"]
    exit_conditions: List[str]        # e.g., ["RSI > 70"]
    risk_params: Dict[str, float]     # e.g., {"stop_loss_pips": 50.0, "take_profit_pips": 100.0}


def validate_alpha_seed(data: Dict[str, Any]) -> AlphaSeed:
    """
    Validates a raw dictionary payload against the strict AlphaSeed schema.
    Raises InvalidHypothesisError on any missing field, invalid type, or boundary violation.
    """
    if not isinstance(data, dict):
        raise InvalidHypothesisError("Payload must be a dictionary")

    # 1. Check all required top-level keys
    required_keys = {
        "strategy_id",
        "asset_class",
        "indicators",
        "entry_conditions",
        "exit_conditions",
        "risk_params",
    }
    missing_keys = required_keys - set(data.keys())
    if missing_keys:
        raise InvalidHypothesisError(f"Missing required fields: {sorted(list(missing_keys))}")

    # 2. Validate strategy_id
    strategy_id = data["strategy_id"]
    if not isinstance(strategy_id, str) or not strategy_id.strip():
        raise InvalidHypothesisError("strategy_id must be a non-empty string")
    strategy_id = strategy_id.strip()

    # 3. Validate asset_class
    asset_class = data["asset_class"]
    if not isinstance(asset_class, str) or asset_class != asset_class.upper() or asset_class not in VALID_ASSET_CLASSES:
        raise InvalidHypothesisError(
            f"Invalid asset_class '{asset_class}'. Must be uppercase and one of: {sorted(list(VALID_ASSET_CLASSES))}"
        )

    # 4. Validate indicators (non-empty list of dicts with valid name and period > 0)
    indicators = data["indicators"]
    if not isinstance(indicators, list) or len(indicators) == 0:
        raise InvalidHypothesisError("indicators must be a non-empty list of indicator definitions")

    validated_indicators: List[Dict[str, Any]] = []
    for idx, ind in enumerate(indicators):
        if not isinstance(ind, dict):
            raise InvalidHypothesisError(f"Indicator at index {idx} must be a dictionary")
        if "name" not in ind or "period" not in ind:
            raise InvalidHypothesisError(f"Indicator at index {idx} must contain 'name' and 'period'")

        ind_name = ind["name"]
        if not isinstance(ind_name, str) or not ind_name.strip():
            raise InvalidHypothesisError(f"Indicator name at index {idx} must be a non-empty string")

        try:
            period_val = float(ind["period"])
            if not math.isfinite(period_val) or period_val <= 0:
                raise InvalidHypothesisError(f"Indicator period at index {idx} must be > 0 (got {period_val})")
        except (ValueError, TypeError) as e:
            raise InvalidHypothesisError(f"Invalid indicator period at index {idx}: {e}")

        clean_ind = dict(ind)
        clean_ind["name"] = ind_name.strip()
        clean_ind["period"] = int(period_val) if period_val.is_integer() else period_val
        validated_indicators.append(clean_ind)

    # 5. Validate entry_conditions
    entry_conditions = data["entry_conditions"]
    if not isinstance(entry_conditions, list) or len(entry_conditions) == 0:
        raise InvalidHypothesisError("entry_conditions must be a non-empty list of condition strings")
    for idx, cond in enumerate(entry_conditions):
        if not isinstance(cond, str) or not cond.strip():
            raise InvalidHypothesisError(f"Entry condition at index {idx} must be a non-empty string")

    # 6. Validate exit_conditions
    exit_conditions = data["exit_conditions"]
    if not isinstance(exit_conditions, list) or len(exit_conditions) == 0:
        raise InvalidHypothesisError("exit_conditions must be a non-empty list of condition strings")
    for idx, cond in enumerate(exit_conditions):
        if not isinstance(cond, str) or not cond.strip():
            raise InvalidHypothesisError(f"Exit condition at index {idx} must be a non-empty string")

    # 7. Validate risk_params
    risk_params = data["risk_params"]
    if not isinstance(risk_params, dict):
        raise InvalidHypothesisError("risk_params must be a dictionary")
    if "stop_loss_pips" not in risk_params or "take_profit_pips" not in risk_params:
        raise InvalidHypothesisError("risk_params must contain 'stop_loss_pips' and 'take_profit_pips'")

    validated_risk_params: Dict[str, float] = {}
    for k, v in risk_params.items():
        try:
            v_float = float(v)
            if not math.isfinite(v_float) or v_float < 0.0:
                raise InvalidHypothesisError(f"Risk parameter '{k}' must be a non-negative finite number (got {v_float})")
            validated_risk_params[k] = v_float
        except (ValueError, TypeError) as e:
            raise InvalidHypothesisError(f"Invalid risk parameter value for '{k}': {e}")

    return AlphaSeed(
        strategy_id=strategy_id,
        asset_class=asset_class,
        indicators=validated_indicators,
        entry_conditions=[c.strip() for c in entry_conditions],
        exit_conditions=[c.strip() for c in exit_conditions],
        risk_params=validated_risk_params,
    )