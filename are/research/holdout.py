"""
AHFMES ARE — Research Holdout Layer

Implements TRAIN -> VALIDATION/WFO -> FINAL HOLDOUT with strict access control.
Holdout data is NEVER seen during training/selection.

Also includes TemporalContract for leakage prevention.
"""

from __future__ import annotations

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
# HOLDOUT STATE & SPLIT
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


# =============================================================================
# TEMPORAL CONTRACT (LEAKAGE FIREWALL)
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


# =============================================================================
# HOLDOUT MANAGER
# =============================================================================

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
        """Get holdout portion. Logs access. If LOCKED, raises error."""
        split = self._splits.get(split_id)
        if not split:
            raise KeyError(f"Split {split_id} not found")

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
        """Access holdout data for post-training evaluation (after WFO is complete)."""
        split = self._splits.get(split_id)
        if not split:
            raise KeyError(f"Split {split_id} not found")

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
# HOLDOUT EVIDENCE & EVALUATION ENGINE
# =============================================================================

@dataclass(frozen=True)
class HoldoutEvidence:
    """Immutable evidence from holdout evaluation."""
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
        """Validate internal consistency of holdout evidence."""
        issues = []
        warnings = []
        if self.trade_count == 0:
            warnings.append('No trades on holdout — strategy has no edge on holdout data')
        if abs(self.total_return) > 100:
            issues.append(f'Return {self.total_return:.1f}% exceeds sanity bound')
        if self.max_drawdown < 0 or self.max_drawdown > 100:
            issues.append(f'Drawdown {self.max_drawdown:.1f}% outside [0,100]')
        expected_returns_len = max(0, len(self.equity) - 1)
        if len(self.returns) != expected_returns_len:
            issues.append(f'Returns length {len(self.returns)} != equity-1 ({expected_returns_len})')
        if len(self.equity) < 2:
            issues.append('Equity curve too short')
        payload = {
            'run_id': self.run_id, 'split_id': self.split_id,
            'dataset_hash': self.dataset_hash, 'strategy_hash': self.strategy_hash,
            'wfo_provenance_hash': self.wfo_provenance_hash,
            'selected_params': dict(self.selected_params), 'trade_count': self.trade_count, 'sharpe': self.sharpe,
        }
        expected_hash = compute_sha256(json.dumps(payload, sort_keys=True).encode())
        if expected_hash != self.provenance_hash:
            issues.append('Provenance hash mismatch — evidence tampered')
        return {'valid': len(issues) == 0, 'issues': issues}

# =============================================================================
# SELECTED-PARAM RESOLUTION (P0-1)
# =============================================================================

def resolve_holdout_selected_params(
    wfo_result: Optional[Dict[str, Any]],
    has_params: bool,
) -> Optional[Dict[str, Any]]:
    """Resolve parameter yang sah untuk evaluasi holdout.

    Kontrak P0-1: holdout WAJIB mengevaluasi strategi DENGAN parameter yang sama
    persis seperti yang dipilih WFO (winner fold terakhir). Parameter TIDAK boleh
    hanya menjadi metadata/provenance.

    Returns:
      dict  → parameter pemenang (boleh kosong utk strategi tanpa parameter).
      None  → parameter dideklarasikan tapi WFO tidak menghasilkan fold winner;
              holdout TIDAK boleh dievaluasi (pemanggil harus menandai INVALID),
              dan TIDAK boleh memakai parameter rekaan seperti {'lookback': 20}.
    """
    if wfo_result:
        folds = wfo_result.get('folds') or []
        if folds:
            last_fold = folds[-1] if isinstance(folds[-1], dict) else {}
            wp = last_fold.get('winner_params')
            if isinstance(wp, dict):
                return dict(wp)
            # winner_params hilang/None padahal fold ada:
            #  - strategi tanpa parameter → sah dievaluasi tanpa parameter.
            #  - parameter dideklarasikan → bukan winner sah → INVALID.
            if not has_params:
                return {}
            return None
    # Tidak ada wfo_result / fold sama sekali.
    if not has_params:
        return {}
    return None


class HoldoutEvaluationEngine:
    """Evaluates strategy on holdout data AFTER WFO selection."""

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
        execution_model: Any = None,  # P0-2: ExecutionModel duck-typed -> engine.
        run_id: str = "",
        split_id: str = "",
        dataset_hash: str = "",
        split_hash: str = "",
        strategy_hash: str = "",
        wfo_provenance_hash: str = "",
    ) -> HoldoutEvidence:
        """Run strategy on holdout data with selected parameters."""
        from are.backtest import IsolatedBacktestEngine

        def parametrized_strategy(df: pl.DataFrame) -> pl.DataFrame:
            # P0-1: parameter terpilih WAJIB benar-benar membentuk strategi yang
            # dievaluasi (bukan sekadar metadata). Injeksi identik dengan WFO:
            # kolom `_param_<name>` berisi nilai parameter.
            df_with_params = df
            for k, v in (selected_params or {}).items():
                df_with_params = df_with_params.with_columns(
                    pl.lit(v).alias(f"_param_{k}")
                )
            result = strategy_logic(df_with_params)
            if 'signal' not in result.columns:
                raise ValueError('Strategy did not produce signal column on holdout data')
            return result

        engine = IsolatedBacktestEngine()
        result = engine.run_backtest(
            strategy_logic=parametrized_strategy,
            historical_data=holdout_df,
            initial_capital=initial_capital,
            timeframe_seconds=timeframe_seconds,
            spread_pct=spread_pct,
            slippage_pct=slippage_pct,
            commission_pct=commission_pct,
            execution_model=execution_model,
        )

        metrics = result.metrics
        equity_curve = result.equity_curve

        equities = []
        if not equity_curve.is_empty() and 'equity' in equity_curve.columns:
            equities = equity_curve['equity'].to_list()
        returns = []
        if len(equities) >= 2:
            returns = [
                (equities[i] - equities[i-1]) / equities[i-1]
                for i in range(1, len(equities))
                if equities[i-1] > 0
            ]

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

        validation = evidence.validate()
        if not validation['valid']:
            raise ValueError(f'HoldoutEvidence validation failed: {validation["issues"]}')

        return evidence
