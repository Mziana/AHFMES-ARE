"""
AHFMES ARE — Data Models

Immutable data containers for backtest results, WFO evidence, and research contracts.
Extracted from backtest.py for single-responsibility separation.

Zero external dependencies except Polars (stdlib + polars only).
"""

from __future__ import annotations

import dataclasses as _dc
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    import polars as pl
except ImportError:
    raise ImportError("Pustaka 'polars' diperlukan untuk modul models. Install: pip install polars")


@dataclass(frozen=True)
class BacktestResult:
    """Immutable container for vectorized backtest outputs and performance metrics."""
    equity_curve: pl.DataFrame
    trade_log: pl.DataFrame
    metrics: Dict[str, Any]


@dataclass(frozen=True)
class WFOFoldEvidence:
    fold_id: int
    train_start_ts: float
    train_end_ts: float
    purge_start_ts: float
    purge_end_ts: float
    oos_start_ts: float
    oos_end_ts: float
    candidate_count: int
    selection_metric: str
    winner_params: Dict[str, Any]
    winner_is_score: float
    runner_up_params: Optional[Dict[str, Any]]
    runner_up_is_score: Optional[float]
    tie_count: int
    tie_break_rule: str
    is_metrics: Dict[str, float]
    oos_metrics: Dict[str, float]
    oos_returns: Tuple[float, ...]
    wfe: float


@dataclass(frozen=True)
class WFOEvidence:
    run_id: str
    dataset_hash: str
    timeframe_seconds: float
    data_start_ts: float
    data_end_ts: float
    folds: Tuple[WFOFoldEvidence, ...]

    # Trial Accounting (RES-WFO-02)
    fold_count: int
    parameter_family_size: int
    evaluation_count: int
    effective_trial_count: int
    effective_trial_method: str
    effective_trial_assumption: str

    # Overlap Disclosure (RES-WFO-07)
    training_overlap_ratio: float
    oos_overlap_ratio: float

    # Parameter Kontrak (RES-WFO-06)
    purge_bars: int
    label_horizon_bars: int
    label_horizon_unit: str
    warmup_bars: int

    # Strict Pooled OOS Evidence (RES-WFO-05)
    pooled_oos_returns: Tuple[float, ...]
    pooled_oos_equity: Tuple[float, ...]
    pooled_oos_sharpe: float
    pooled_oos_return: float
    pooled_oos_max_drawdown: float

    # Fold Distribution Metrics
    mean_fold_oos_sharpe: float
    median_fold_oos_sharpe: float
    worst_fold_oos_sharpe: float
    std_fold_oos_sharpe: float
    mean_wfe: float
    median_wfe: float
    worst_wfe: float

    provenance_hash: str

    def to_dict(self) -> dict:
        """Canonical serialization of ALL WFO evidence fields."""
        d = {}
        for f in _dc.fields(self):
            val = getattr(self, f.name)
            if isinstance(val, tuple):
                # Handle Tuple[WFOFoldEvidence, ...]
                d[f.name] = [
                    _dc.asdict(item) if hasattr(item, '__dataclass_fields__') else item
                    for item in val
                ]
            else:
                d[f.name] = val
        return d


@dataclass(frozen=True)
class BacktestResearchContract:
    """
    Frozen research contract that locks all semantic decisions before a backtest run.
    Every backtest must be associated with a contract to ensure reproducibility.
    """
    # Dataset Identity
    instrument: str
    venue: str
    timezone: str
    timeframe_seconds: float
    data_source: str  # e.g. 'mt5_parquet', 'csv', 'synthetic_test'
    data_start_ts: float
    data_end_ts: float
    raw_dataset_hash: str
    purified_dataset_hash: str
    purification_report: Dict[str, Any]  # from DataQualityReport.to_dict()

    # Execution Semantics
    signal_timing: str  # 'next_bar_close' | 'next_tick' | 'same_bar_open' | 'same_bar_close'
    entry_price_type: str  # 'bid' | 'ask' | 'mid'
    exit_price_type: str  # 'bid' | 'ask' | 'mid'
    position_model: str  # 'continuous' | 'discrete'
    order_type: str  # 'market' | 'limit'
    fill_guarantee: str  # 'guaranteed' | 'partial_possible'
    slippage_model: str  # 'fixed_pct' | 'volatility_dependent'
    spread_model: str  # 'historical' | 'synthetic_fixed'
    commission_model: str  # 'fixed_pct' | 'proportional'

    # Strategy Identity
    strategy_id: str
    strategy_version: str
    strategy_family: str
    parameter_space_hash: str
    parameter_constraints: Dict[str, Any]
    signal_domain: str  # 'discrete_ternary' | 'continuous'
    lookback_bars: int
    warmup_bars: int

    # WFO Configuration
    wfo_train_window_bars: int
    wfo_test_window_bars: int
    wfo_step_bars: int
    wfo_purge_bars: int
    wfo_warmup_bars: int
    wfo_n_folds: int
    wfo_selection_metric: str
    wfo_tie_breaker: str

    # Reproducibility
    engine_version: str
    configuration_hash: str
    random_seed: Optional[int]
    contract_hash: str  # hash of all above fields


def build_wfo_provenance_payload(evidence: WFOEvidence) -> Dict[str, Any]:
    """P1-02: Hash ALL evidence fields — canonical payload for provenance.

    Missing any field here means evidence can be mutated without breaking the hash.
    """
    # Serialize ALL fields from WFOEvidence
    payload = {}
    for f in _dc.fields(evidence):
        val = getattr(evidence, f.name)
        if f.name == 'provenance_hash':
            continue  # Don't include the hash itself
        if isinstance(val, tuple):
            payload[f.name] = [
                _dc.asdict(item) if hasattr(item, '__dataclass_fields__') else item
                for item in val
            ]
        else:
            payload[f.name] = val

    return payload
