"""
AHFMES ARE — Evidence Binding & Sensitivity Analysis

Cryptographic binding between evidence objects and sensitivity/cost-stress analysis.
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List

try:
    import polars as pl
except ImportError:
    raise ImportError("Polars required: pip install polars")

from are.hasher import compute_sha256


@dataclass(frozen=True)
class EvidenceBinding:
    """Cryptographic binding between all evidence objects in a run."""
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


class SensitivityAnalyzer:
    """Tests strategy robustness under parameter and cost perturbation."""

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


def compute_canonical_dataset_hash(df: pl.DataFrame, metadata: Dict[str, Any] = None) -> str:
    """Compute canonical hash of dataset including ALL columns, schema, and metadata."""
    parts = []

    schema = [(col, str(df[col].dtype)) for col in df.columns]
    parts.append(json.dumps(schema, sort_keys=False).encode())

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
    """Compute canonical split hash that identifies the full split protocol."""
    payload = {
        'dataset_hash': dataset_hash,
        'train_start': train_start, 'train_end': train_end,
        'validation_start': validation_start, 'validation_end': validation_end,
        'holdout_start': holdout_start, 'holdout_end': holdout_end,
        'purge_bars': purge_bars,
        'split_protocol_version': split_protocol_version,
    }
    return compute_sha256(json.dumps(payload, sort_keys=True).encode())
