"""
AHFMES ARE -- Research Experiment Plane (Slice BT-02)

StrategyRegistry: Track strategy identity, source hash, parameter schema.
ExperimentConfig: Frozen experiment configuration with all hashes.

Zero external dependencies except stdlib.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

from are.hasher import compute_sha256


@dataclass(frozen=True)
class StrategyIdentity:
    """Immutable identity card for a strategy."""
    strategy_id: str
    strategy_name: str
    strategy_version: str
    strategy_family: str  # MOMENTUM, MEAN_REVERSION, ORDERBOOK_IMBALANCE, CUSTOM
    source_hash: str  # hash of the strategy code
    parameter_schema: Dict[str, Any]  # {param_name: {type, min, max, default}}
    signal_contract: str  # 'discrete_ternary' | 'continuous'
    lookback_bars: int
    warmup_bars: int
    execution_assumption: str  # 'next_bar_open', 'same_bar_close'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ParameterGrid:
    """Immutable parameter grid for WFO."""
    grid_id: str
    param_names: Tuple[str, ...]
    param_values: Tuple[Tuple[float, ...], ...]  # list of value lists
    grid_size: int
    grid_hash: str
    constraints: Dict[str, Any]  # e.g. {"fast < slow": True}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExecutionModel:
    """
    First-class execution simulation model.
    All backtest results must reference the exact execution model used.
    """
    model_id: str
    signal_timing: str  # 'next_bar_open', 'same_bar_close', 'next_tick'
    entry_price_type: str  # 'bid', 'ask', 'mid', 'close'
    exit_price_type: str  # 'bid', 'ask', 'mid', 'close'
    position_model: str  # 'continuous', 'discrete'
    order_type: str  # 'market', 'limit'
    fill_guarantee: str  # 'guaranteed', 'partial_possible'
    spread_model: str  # 'historical', 'synthetic_fixed', 'instrument_aware'
    slippage_model: str  # 'fixed_pct', 'volatility_dependent'
    commission_model: str  # 'fixed_pct', 'proportional', 'per_lot'
    spread_pct: float
    slippage_pct: float
    commission_pct: float
    initial_capital: float
    model_hash: str  # hash of all above fields

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExperimentConfig:
    """
    Frozen experiment configuration. Once created, cannot be modified.
    This is the single source of truth for one backtest experiment.
    """
    experiment_id: str
    created_at: float

    # Identity
    strategy: StrategyIdentity
    execution_model: ExecutionModel
    parameter_grid: ParameterGrid

    # WFO Configuration
    wfo_train_window_bars: int
    wfo_test_window_bars: int
    wfo_step_bars: int
    wfo_purge_bars: int
    wfo_warmup_bars: int
    wfo_n_folds: int
    wfo_selection_metric: str  # 'sharpe_ratio'
    wfo_tie_breaker: str  # '(sharpe, -max_dd, -turnover)'

    # Statistics Policy
    dsr_enabled: bool = True
    psr_enabled: bool = True
    mc_enabled: bool = True
    mc_simulations: int = 1000
    crisis_enabled: bool = True

    # Hashes
    config_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StrategyRegistry:
    """
    Registry for strategy identities.
    Ensures every backtest references a versioned, hashed strategy.
    """

    REGISTRY_FILE = "data/strategies/strategy_registry.json"

    def __init__(self):
        os.makedirs(os.path.dirname(self.REGISTRY_FILE), exist_ok=True)
        self._strategies: Dict[str, StrategyIdentity] = self._load()

    def _load(self) -> Dict[str, StrategyIdentity]:
        try:
            if os.path.exists(self.REGISTRY_FILE):
                with open(self.REGISTRY_FILE) as f:
                    data = json.load(f)
                return {k: StrategyIdentity(**v) for k, v in data.items()}
        except Exception:
            pass
        return {}

    def _save(self):
        with open(self.REGISTRY_FILE, "w") as f:
            json.dump({k: v.to_dict() for k, v in self._strategies.items()}, f, indent=2)

    def register_strategy(
        self,
        strategy_id: str,
        strategy_name: str,
        strategy_family: str,
        strategy_func: Callable,
        parameter_schema: Dict[str, Any],
        signal_contract: str = "discrete_ternary",
        lookback_bars: int = 50,
        warmup_bars: int = 50,
        execution_assumption: str = "next_bar_open",
        strategy_version: str = "1.0.0",
    ) -> StrategyIdentity:
        """Register a strategy with source hash and identity."""
        # Hash the strategy source code
        try:
            source = inspect.getsource(strategy_func)
            source_hash = compute_sha256(source.encode())
        except (TypeError, OSError):
            source_hash = compute_sha256(strategy_func.__name__.encode())

        identity = StrategyIdentity(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            strategy_version=strategy_version,
            strategy_family=strategy_family,
            source_hash=source_hash,
            parameter_schema=parameter_schema,
            signal_contract=signal_contract,
            lookback_bars=lookback_bars,
            warmup_bars=warmup_bars,
            execution_assumption=execution_assumption,
        )

        self._strategies[strategy_id] = identity
        self._save()
        return identity

    def get_strategy(self, strategy_id: str) -> StrategyIdentity:
        if strategy_id not in self._strategies:
            raise KeyError(f"Strategy {strategy_id} not registered")
        return self._strategies[strategy_id]

    def list_strategies(self) -> List[StrategyIdentity]:
        return list(self._strategies.values())


def build_execution_model(
    spread_pct: float = 0.0001,
    slippage_pct: float = 0.00005,
    commission_pct: float = 0.00005,
    initial_capital: float = 100000.0,
    signal_timing: str = "next_bar_open",
    entry_price_type: str = "close",
    spread_model: str = "historical",
    slippage_model: str = "fixed_pct",
) -> ExecutionModel:
    """Build and hash an execution model."""
    model_id = f"EX-{int(time.time())}"

    fields = {
        "signal_timing": signal_timing,
        "entry_price_type": entry_price_type,
        "spread_model": spread_model,
        "slippage_model": slippage_model,
        "spread_pct": spread_pct,
        "slippage_pct": slippage_pct,
        "commission_pct": commission_pct,
        "initial_capital": initial_capital,
    }
    model_hash = compute_sha256(json.dumps(fields, sort_keys=True).encode())

    return ExecutionModel(
        model_id=model_id,
        signal_timing=signal_timing,
        entry_price_type=entry_price_type,
        exit_price_type=entry_price_type,
        position_model="continuous",
        order_type="market",
        fill_guarantee="guaranteed",
        spread_model=spread_model,
        slippage_model=slippage_model,
        commission_model="fixed_pct",
        spread_pct=spread_pct,
        slippage_pct=slippage_pct,
        commission_pct=commission_pct,
        initial_capital=initial_capital,
        model_hash=model_hash,
    )


def build_parameter_grid(
    param_name: str,
    values: List[float],
    constraints: Optional[Dict[str, Any]] = None,
) -> ParameterGrid:
    """Build and hash a parameter grid."""
    grid_hash = compute_sha256(json.dumps({"name": param_name, "values": values}, sort_keys=True).encode())
    return ParameterGrid(
        grid_id=f"PG-{grid_hash[:12]}",
        param_names=(param_name,),
        param_values=(tuple(values),),
        grid_size=len(values),
        grid_hash=grid_hash,
        constraints=constraints or {},
    )


def build_experiment_config(
    strategy: StrategyIdentity,
    execution_model: ExecutionModel,
    parameter_grid: ParameterGrid,
    wfo_train_window_bars: int = 500,
    wfo_test_window_bars: int = 100,
    wfo_step_bars: int = 100,
    wfo_purge_bars: int = 10,
    wfo_warmup_bars: int = 50,
    wfo_n_folds: int = 5,
    dsr_enabled: bool = True,
    mc_simulations: int = 1000,
) -> ExperimentConfig:
    """Build and hash a frozen experiment configuration."""
    experiment_id = f"EXP-{strategy.strategy_id}-{parameter_grid.grid_hash[:8]}"

    config_fields = {
        "strategy_id": strategy.strategy_id,
        "strategy_hash": strategy.source_hash,
        "execution_hash": execution_model.model_hash,
        "param_grid_hash": parameter_grid.grid_hash,
        "wfo_train": wfo_train_window_bars,
        "wfo_test": wfo_test_window_bars,
        "wfo_step": wfo_step_bars,
        "wfo_purge": wfo_purge_bars,
        "wfo_warmup": wfo_warmup_bars,
        "wfo_folds": wfo_n_folds,
        "dsr": dsr_enabled,
        "mc_sims": mc_simulations,
    }
    config_hash = compute_sha256(json.dumps(config_fields, sort_keys=True).encode())

    return ExperimentConfig(
        experiment_id=experiment_id,
        created_at=time.time(),
        strategy=strategy,
        execution_model=execution_model,
        parameter_grid=parameter_grid,
        wfo_train_window_bars=wfo_train_window_bars,
        wfo_test_window_bars=wfo_test_window_bars,
        wfo_step_bars=wfo_step_bars,
        wfo_purge_bars=wfo_purge_bars,
        wfo_warmup_bars=wfo_warmup_bars,
        wfo_n_folds=wfo_n_folds,
        wfo_selection_metric="sharpe_ratio",
        wfo_tie_breaker="(sharpe, -max_dd, -turnover)",
        dsr_enabled=dsr_enabled,
        mc_enabled=True,
        mc_simulations=mc_simulations,
        crisis_enabled=True,
        config_hash=config_hash,
    )
