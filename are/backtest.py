"""
AHFMES ARE - Isolated High-Performance Vectorized Backtest Engine (DELEGASI_028, DELEGASI_029b, World 2: PROVE)

Provides ultra-fast vectorized backtesting using Polars with built-in data purification:
- Strict Architectural Firewall: Completely isolated from production execution modules.
- Anti-GIGO: Automatic DataPurifier integration (Toxic spread & macro gap filtering).
Zero external dependencies except Polars (stdlib + polars only).
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import polars as pl
except ImportError:
    raise ImportError("Pustaka 'polars' diperlukan untuk modul backtest. Install: pip install polars")

from are.data_pipeline import DataPurifier
from are.evidence import EvidenceLedger
from are.hasher import compute_sha256
from are.storage import EventStore


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
    signal_timing: str  # 'next_bar_open' | 'next_tick' | 'same_bar_close'
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
    return {
        "folds": [
            {
                "winner_params": f.winner_params,
                "oos_sharpe": f.oos_metrics.get("sharpe_ratio", 0.0)
            } for f in evidence.folds
        ],
        "pooled_oos_returns": evidence.pooled_oos_returns,
        "pooled_sharpe": evidence.pooled_oos_sharpe,
        "pooled_oos_return": evidence.pooled_oos_return,
        "pooled_oos_max_drawdown": evidence.pooled_oos_max_drawdown,
        "fold_count": evidence.fold_count,
        "parameter_family_size": evidence.parameter_family_size,
        "evaluation_count": evidence.evaluation_count,
        "effective_trial_count": evidence.effective_trial_count,
        "training_overlap_ratio": evidence.training_overlap_ratio,
        "oos_overlap_ratio": evidence.oos_overlap_ratio,
        "purge_bars": evidence.purge_bars,
        "label_horizon_bars": evidence.label_horizon_bars,
        "warmup_bars": evidence.warmup_bars,
        "mean_wfe": evidence.mean_wfe,
        "median_wfe": evidence.median_wfe,
        "worst_wfe": evidence.worst_wfe,
    }

def calculate_sharpe_ratio(
    returns: List[float],
    timeframe_seconds: float = 60.0,
) -> float:
    """
    Computes annualized Sharpe Ratio properly scaled to the bar timeframe (RES-RED-07).
    """
    if not returns or len(returns) < 2:
        return 0.0
    mean_ret = sum(returns) / len(returns)
    var_ret = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
    std_ret = math.sqrt(var_ret) if var_ret > 0 else 0.0
    if std_ret <= 1e-9:
        return 0.0
    bars_per_day = (86400.0 / timeframe_seconds) if timeframe_seconds > 0 else 1440.0
    annual_factor = math.sqrt(252.0 * bars_per_day)
    return float(mean_ret / std_ret * annual_factor)


class IsolatedBacktestEngine:
    """
    High-Performance Isolated Backtest Engine (World 2: PROVE).
    Executes vectorized strategy evaluations with zero live trading linkages.
    """

    def run_backtest(
        self,
        strategy_logic: Optional[Callable[[pl.DataFrame], pl.DataFrame]] = None,
        historical_data: Optional[pl.DataFrame] = None,
        initial_capital: float = 10000.0,
        timeframe_seconds: float = 60.0,
        spread_pct: float = 0.0001,      # 1 bps default spread cost (0.01%)
        slippage_pct: float = 0.00005,   # 0.5 bps default execution slippage (0.005%)
        commission_pct: float = 0.00005, # 0.5 bps default broker fee (0.005%)
        synthetic: bool = False,          # Explicit opt-in for synthetic test data
    ) -> BacktestResult:
        """
        Executes a vectorized backtest computation over historical market data.
        """
        # Input validation — fail-closed on nonsensical parameters (RES-RED-22)
        for param_name, param_val in [
            ("spread_pct", spread_pct),
            ("slippage_pct", slippage_pct),
            ("commission_pct", commission_pct),
        ]:
            if not isinstance(param_val, (int, float)):
                raise TypeError(f"INVALID_FRICTION_TYPE: {param_name} must be numeric, got {type(param_val).__name__}")
            if math.isnan(param_val) or math.isinf(param_val):
                raise ValueError(f"INVALID_FRICTION_VALUE: {param_name} = {param_val!r} (must be finite)")
            if param_val < 0.0:
                raise ValueError(f"NEGATIVE_FRICTION_REJECTED: {param_name} = {param_val} (friction cannot be negative)")

        if not isinstance(timeframe_seconds, (int, float)) or timeframe_seconds <= 0.0:
            raise ValueError(f"INVALID_TIMEFRAME: timeframe_seconds = {timeframe_seconds} (must be positive)")
        if math.isnan(timeframe_seconds) or math.isinf(timeframe_seconds):
            raise ValueError(f"INVALID_TIMEFRAME: timeframe_seconds = {timeframe_seconds} (must be finite)")

        if historical_data is None:
            if not synthetic:
                # FAIL-CLOSED: No synthetic fallback in research mode.
                raise ValueError(
                    "No historical data provided. Backtest requires real OHLC data.\n"
                    "Use data_loader.load_ohlc_data() or pass a DataFrame explicitly.\n"
                    "For testing only: pass synthetic=True to generate test data."
                )
            # Explicit synthetic opt-in for testing only
            timestamps = [1700000000 + i * 60 for i in range(1000)]
            prices = [65000.0 + (math.sin(i * 0.05) * 200.0) + (i * 0.1) for i in range(1000)]
            historical_data = pl.DataFrame({"timestamp": timestamps, "price": prices})

        # Compute raw dataset hash BEFORE purification (P0-4)
        import struct as _struct
        _ts = historical_data["timestamp"].to_list() if "timestamp" in historical_data.columns else []
        _pr = historical_data["price"].to_list() if "price" in historical_data.columns else []
        _vol = historical_data["volume"].to_list() if "volume" in historical_data.columns else [0.0] * len(_ts)
        _raw_bytes = b"V1" + b"".join(_struct.pack(">d", float(x)) for x in _ts) + b"".join(_struct.pack(">d", float(x)) for x in _pr) + b"".join(_struct.pack(">d", float(x)) for x in _vol)
        raw_dataset_hash = compute_sha256(_raw_bytes)

        # Purify raw tick / bar data via DataPurifier (Anti-GIGO, DELEGASI_029b)
        purifier = DataPurifier()
        purified_data = purifier.purify_tick_data(historical_data)
        purification_report = purifier.quality_report.to_dict() if purifier.quality_report else {}

        # Compute purified dataset hash AFTER purification
        _pts = purified_data["timestamp"].to_list() if "timestamp" in purified_data.columns else []
        _ppr = purified_data["price"].to_list() if "price" in purified_data.columns else []
        _pvol = purified_data["volume"].to_list() if "volume" in purified_data.columns else [0.0] * len(_pts)
        _purified_bytes = b"V1" + b"".join(_struct.pack(">d", float(x)) for x in _pts) + b"".join(_struct.pack(">d", float(x)) for x in _ppr) + b"".join(_struct.pack(">d", float(x)) for x in _pvol)
        purified_dataset_hash = compute_sha256(_purified_bytes)

        # 1. Apply Strategy Logic / Moving Average Crossover
        if strategy_logic is not None:
            df = strategy_logic(purified_data)
        else:
            # Default Vectorized Moving Average Crossover
            df = purified_data.with_columns([
                pl.col("price").rolling_mean(window_size=10).alias("fast_ma"),
                pl.col("price").rolling_mean(window_size=30).alias("slow_ma"),
            ]).with_columns(
                pl.when(pl.col("fast_ma") > pl.col("slow_ma"))
                .then(pl.lit(1.0))
                .when(pl.col("fast_ma") < pl.col("slow_ma"))
                .then(pl.lit(-1.0))
                .otherwise(pl.lit(0.0))
                .alias("signal")
            )

        if "signal" not in df.columns:
            # FAIL-CLOSED: Strategy MUST produce a 'signal' column.
            # Always-long fallback masks broken strategies — reject instead.
            raise ValueError(
                "Strategy did not produce 'signal' column.\n"
                "Every strategy_logic function must add a 'signal' column with values: -1.0, 0.0, or 1.0.\n"
                "Received columns: " + ", ".join(df.columns)
            )

        # Neutralize / block trade execution on toxic spreads or closed market periods (DELEGASI_029b)
        if "is_toxic_spread" in df.columns or "is_market_closed" in df.columns:
            toxic_cond = pl.col("is_toxic_spread") if "is_toxic_spread" in df.columns else pl.lit(False)
            closed_cond = pl.col("is_market_closed") if "is_market_closed" in df.columns else pl.lit(False)
            blocked_cond = toxic_cond | closed_cond
            df = df.with_columns(
                pl.when(blocked_cond).then(pl.lit(0.0)).otherwise(pl.col("signal")).alias("signal")
            )

        # 2. Vectorized P&L, Turnover, and Microstructure Friction (RES-RED-10)
        unit_friction = (0.5 * spread_pct) + slippage_pct + commission_pct

        df = df.with_columns([
            (pl.col("price").pct_change()).fill_null(0.0).alias("price_return"),
            pl.col("signal").shift(1).fill_null(0.0).alias("prev_signal"),
        ]).with_columns([
            (pl.col("signal") - pl.col("prev_signal")).abs().alias("turnover"),
            (pl.col("prev_signal") * pl.col("price_return")).alias("gross_strategy_return"),
        ]).with_columns([
            (pl.col("turnover") * pl.lit(unit_friction)).alias("friction_penalty"),
        ]).with_columns([
            (pl.col("gross_strategy_return") - pl.col("friction_penalty")).alias("strategy_return")
        ])

        # 3. Cumulative Equity Curve (Net of Frictions)
        df = df.with_columns([
            (pl.lit(initial_capital) * (1.0 + pl.col("strategy_return")).cum_prod()).alias("equity")
        ])

        # 4. Drawdown Calculation
        df = df.with_columns([
            pl.col("equity").cum_max().alias("peak_equity")
        ]).with_columns([
            ((pl.col("equity") - pl.col("peak_equity")) / pl.col("peak_equity")).alias("drawdown")
        ])

        # 5. Extract Trade Logs on Signal Changes
        trade_df = df.filter(
            (pl.col("signal") != pl.col("prev_signal")) & (pl.col("signal") != 0.0)
        ).select([
            pl.col("timestamp"),
            pl.when(pl.col("signal") > 0).then(pl.lit("BUY")).otherwise(pl.lit("SELL")).alias("action"),
            pl.col("price"),
            (pl.col("equity") - pl.col("equity").shift(1)).fill_null(0.0).alias("pnl"),
            pl.col("equity"),
        ])

        # 6. Quantitative Performance Metrics
        final_equity = float(df["equity"][-1])
        total_return = (final_equity - initial_capital) / initial_capital
        max_drawdown = float(df["drawdown"].min()) if len(df["drawdown"]) > 0 else 0.0
        max_drawdown_pct = abs(max_drawdown)

        returns_series = df["strategy_return"].to_list()
        mean_ret = sum(returns_series) / len(returns_series) if returns_series else 0.0
        var_ret = sum((r - mean_ret) ** 2 for r in returns_series) / len(returns_series) if returns_series else 0.0
        std_ret = math.sqrt(var_ret) if var_ret > 0 else 0.0

        bars_per_day = (86400.0 / timeframe_seconds) if timeframe_seconds > 0 else 1440.0
        annual_factor = math.sqrt(252.0 * bars_per_day)
        sharpe_ratio = (mean_ret / std_ret * annual_factor) if std_ret > 1e-9 else 0.0

        gains = [r for r in returns_series if r > 0]
        losses = [abs(r) for r in returns_series if r < 0]
        total_gains = sum(gains)
        total_losses = sum(losses)
        profit_factor = (total_gains / total_losses) if total_losses > 1e-9 else (100.0 if total_gains > 0 else 1.0)

        # Microstructure friction metrics
        total_turnover_count = int((df["turnover"] > 0).sum())
        total_friction_cost = float(df["friction_penalty"].sum())
        total_friction_cost_pct = round(total_friction_cost * 100.0, 4)

        gross_cum = (1.0 + df["gross_strategy_return"]).cum_prod()
        gross_final = float(gross_cum[-1]) if len(gross_cum) > 0 else 1.0
        gross_return = gross_final - 1.0
        gross_return_pct = round(gross_return * 100.0, 2)
        net_return_pct = round(total_return * 100.0, 2)

        metrics = {
            "initial_capital": initial_capital,
            "final_equity": round(final_equity, 2),
            "total_return": round(total_return, 4),
            "total_return_pct": round(total_return * 100.0, 2),
            "net_return_pct": net_return_pct,
            "gross_return_pct": gross_return_pct,
            "total_turnover_count": total_turnover_count,
            "total_friction_cost_pct": total_friction_cost_pct,
            "spread_pct": spread_pct,
            "slippage_pct": slippage_pct,
            "commission_pct": commission_pct,
            "max_drawdown": round(max_drawdown_pct, 4),
            "max_drawdown_pct": round(max_drawdown_pct * 100.0, 2),
            "sharpe_ratio": round(sharpe_ratio, 4),
            "profit_factor": round(profit_factor, 4),
            "total_bars": len(df),
            "total_trades": len(trade_df),
            "timeframe_seconds": timeframe_seconds,
            "annualization_factor": round(annual_factor, 4),
            # P0-4: Dataset identity hashes
            "raw_dataset_hash": raw_dataset_hash,
            "purified_dataset_hash": purified_dataset_hash,
            # P0-1: Purification audit trail
            "purification_report": purification_report,
            # P0-4: Execution semantics
            "signal_timing": "next_bar_open",
            "entry_price": "close",
            "position_model": "continuous",
            "fill_guarantee": "guaranteed",
        }

        equity_curve = df.select(["timestamp", "price", "signal", "equity", "drawdown", "strategy_return"])
        return BacktestResult(equity_curve=equity_curve, trade_log=trade_df, metrics=metrics)

    def save_artifact(self, result: BacktestResult, evidence_ledger: EvidenceLedger) -> str:
        """
        Serializes the backtest result into a canonical JSON artifact and records it into
        the Evidence Ledger as immutable RESEARCH_PROOF, returning its content-addressed proof hash (RES-RED-15).
        Separates deterministic scientific payload from execution timestamps to ensure reproducibility.
        """
        # Convert Polars DataFrames into native Python dicts/lists before JSON serialization
        equity_list = result.equity_curve.to_dicts()
        trade_list = result.trade_log.to_dicts()

        # DETERMINISTIC scientific payload — same inputs = same hash
        scientific_payload = {
            "equity_curve": equity_list,
            "trade_log": trade_list,
            "metrics": result.metrics,
            "artifact_type": "RESEARCH_PROOF",
        }

        scientific_json = json.dumps(scientific_payload, sort_keys=True, allow_nan=False)
        proof_hash = compute_sha256(scientific_json)

        # Record to Evidence Ledger storage stream
        if hasattr(evidence_ledger, "_store") and evidence_ledger._store is not None:
            head = evidence_ledger._store.get_head("research_proofs")
            rev = head[0] if head else 0
            prev_h = head[1] if head else "0" * 64
            evidence_ledger._store.append_event(
                stream_id="research_proofs",
                event_data=scientific_json.encode("utf-8"),
                expected_revision=rev,
                prev_event_hash=prev_h,
                var_ref=proof_hash,
            )

        return proof_hash

    def run_crisis_replay(
        self,
        strategy_logic: Optional[Callable[[pl.DataFrame], pl.DataFrame]] = None,
        crisis_dataset_path: Optional[str] = None,
        crisis_df: Optional[pl.DataFrame] = None,
        initial_capital: float = 10000.0,
        survival_threshold_pct: float = 0.50,
        crisis_name: str = "SYNTHETIC_CRISIS_CRASH",
        spread_pct: float = 0.0001,
        slippage_pct: float = 0.00005,
        commission_pct: float = 0.00005,
        timeframe_seconds: float = 60.0,
    ) -> Dict[str, Any]:
        """
        Runs strategy evaluation on historical or synthetic Black Swan crisis datasets.
        Evaluates strict capital survival threshold (>= 50% capital retained and <= 50% max DD)
        and bankruptcy barrier (< 10% capital).
        Propagates realistic microstructure friction parameters (RES-RED-16).
        """
        data: Optional[pl.DataFrame] = None
        if crisis_df is not None:
            data = crisis_df
        elif crisis_dataset_path is not None and os.path.exists(crisis_dataset_path):
            if crisis_dataset_path.endswith(".parquet"):
                data = pl.read_parquet(crisis_dataset_path)
            elif crisis_dataset_path.endswith(".jsonl") or crisis_dataset_path.endswith(".json"):
                data = pl.read_ndjson(crisis_dataset_path)
            else:
                data = pl.read_csv(crisis_dataset_path)
            if not crisis_name or crisis_name == "SYNTHETIC_CRISIS_CRASH":
                crisis_name = os.path.splitext(os.path.basename(crisis_dataset_path))[0]

        if data is None:
            # Generate deterministic synthetic severe crash data (-60% price plunge)
            timestamps = [1700000000 + i * 60 for i in range(500)]
            prices = [100.0 * (1.0 - (0.60 * (i / 499.0))) for i in range(500)]
            data = pl.DataFrame({
                "timestamp": timestamps,
                "price": prices,
            })

        bt_result = self.run_backtest(
            strategy_logic=strategy_logic,
            historical_data=data,
            initial_capital=initial_capital,
            timeframe_seconds=timeframe_seconds,
            spread_pct=spread_pct,
            slippage_pct=slippage_pct,
            commission_pct=commission_pct,
        )

        final_equity = bt_result.equity_curve["equity"][-1] if len(bt_result.equity_curve) > 0 else initial_capital
        raw_max_dd = abs(float(bt_result.metrics.get("max_drawdown", 0.0)))
        max_dd = raw_max_dd / 100.0 if raw_max_dd > 1.0 else raw_max_dd

        # Survival criteria
        survival_bool = bool((final_equity >= (initial_capital * survival_threshold_pct)) and (max_dd <= survival_threshold_pct))
        bankruptcy_bool = bool(final_equity < (initial_capital * 0.10))

        return {
            "crisis_name": crisis_name,
            "initial_capital": float(initial_capital),
            "final_equity": float(final_equity),
            "max_drawdown": float(max_dd),
            "survival_bool": survival_bool,
            "bankruptcy_bool": bankruptcy_bool,
            "metrics": bt_result.metrics,
        }

    def run_rolling_oos_evaluation(
        self,
        strategy_logic: Optional[Callable[[pl.DataFrame], pl.DataFrame]] = None,
        historical_data: Optional[pl.DataFrame] = None,
        train_window_bars: int = 252,
        test_window_bars: int = 63,
        step_bars: int = 63,
        initial_capital: float = 10000.0,
    ) -> Dict[str, Any]:
        """
        Executes rolling In-Sample (IS) vs Out-of-Sample (OOS) evaluation of a static strategy logic (RES-RED-17).
        NOTE: This is NOT Walk-Forward Optimization (which optimizes parameters per fold).
        For true Walk-Forward Optimization with parameter fitting, use run_walk_forward_optimization().
        """
        if historical_data is None:
            # Generate deterministic synthetic baseline
            timestamps = [1700000000 + i * 60 for i in range(1000)]
            prices = [100.0 + (math.sin(i * 0.05) * 5.0) + (i * 0.02) for i in range(1000)]
            historical_data = pl.DataFrame({
                "timestamp": timestamps,
                "price": prices,
            })

        n_rows = len(historical_data)
        folds: List[Dict[str, Any]] = []

        start = 0
        fold_idx = 0
        while (start + train_window_bars + test_window_bars) <= n_rows:
            train_slice = historical_data.slice(start, train_window_bars)
            test_slice = historical_data.slice(start + train_window_bars, test_window_bars)

            # In-Sample Backtest
            is_result = self.run_backtest(
                strategy_logic=strategy_logic,
                historical_data=train_slice,
                initial_capital=initial_capital,
            )

            # Out-of-Sample Backtest
            oos_result = self.run_backtest(
                strategy_logic=strategy_logic,
                historical_data=test_slice,
                initial_capital=initial_capital,
            )

            is_sharpe = float(is_result.metrics.get("sharpe_ratio", 0.0))
            oos_sharpe = float(oos_result.metrics.get("sharpe_ratio", 0.0))
            oos_return = float(oos_result.metrics.get("total_return", 0.0))
            raw_oos_dd = abs(float(oos_result.metrics.get("max_drawdown", 0.0)))
            oos_drawdown = raw_oos_dd / 100.0 if raw_oos_dd > 1.0 else raw_oos_dd

            folds.append({
                "fold_index": fold_idx,
                "train_start": start,
                "train_end": start + train_window_bars,
                "test_start": start + train_window_bars,
                "test_end": start + train_window_bars + test_window_bars,
                "is_sharpe": is_sharpe,
                "oos_sharpe": oos_sharpe,
                "oos_return": oos_return,
                "oos_drawdown": oos_drawdown,
            })

            fold_idx += 1
            start += step_bars

        n_folds = len(folds)
        if n_folds > 0:
            mean_train_sharpe = sum(f["is_sharpe"] for f in folds) / n_folds
            mean_test_sharpe = sum(f["oos_sharpe"] for f in folds) / n_folds
            wfa_efficiency_ratio = (mean_test_sharpe / mean_train_sharpe) if mean_train_sharpe > 0.0 else 0.0
            worst_fold_drawdown = max((f["oos_drawdown"] for f in folds), default=0.0)
            fold_consistency_ratio = sum(1 for f in folds if f["oos_return"] > 0.0) / n_folds
        else:
            mean_train_sharpe = 0.0
            mean_test_sharpe = 0.0
            wfa_efficiency_ratio = 0.0
            worst_fold_drawdown = 0.0
            fold_consistency_ratio = 0.0

        return {
            "n_folds": n_folds,
            "mean_train_sharpe": float(mean_train_sharpe),
            "mean_test_sharpe": float(mean_test_sharpe),
            "wfa_efficiency_ratio": float(wfa_efficiency_ratio),
            "worst_fold_drawdown": float(worst_fold_drawdown),
            "fold_consistency_ratio": float(fold_consistency_ratio),
            "folds": folds,
        }

    def run_walk_forward_analysis(self, *args, **kwargs) -> Dict[str, Any]:
        """DEPRECATED: Renamed to run_rolling_oos_evaluation(). NOT Walk-Forward Optimization (RES-RED-17)."""
        import warnings
        warnings.warn(
            "run_walk_forward_analysis() is deprecated and renamed to run_rolling_oos_evaluation(). "
            "For true Walk-Forward Optimization with parameter fitting, use run_walk_forward_optimization().",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.run_rolling_oos_evaluation(*args, **kwargs)

    def run_walk_forward_optimization(
        self,
        strategy_factory: Callable[[Dict[str, Any]], Callable[[pl.DataFrame], pl.DataFrame]],
        param_grid: List[Dict[str, Any]],
        historical_data: Optional[pl.DataFrame] = None,
        train_window_bars: int = 500,
        test_window_bars: int = 100,
        step_bars: int = 100,
        warmup_bars: int = 0,
        purge_bars: int = 0,
        label_horizon_bars: int = 0,
        optimization_metric: str = "sharpe_ratio",
        initial_capital: float = 10000.0,
        timeframe_seconds: float = 60.0,
        spread_pct: float = 0.0001,
        slippage_pct: float = 0.00005,
        commission_pct: float = 0.00005,
    ) -> WFOEvidence:
        """
        True Walk-Forward Optimization (WFO) with in-sample parameter fitting,
        warm-up indicator lookback, purge gap, and out-of-sample performance evaluation (RES-RED-09, RES-RED-18, RES-RED-19).
        """
        if purge_bars < label_horizon_bars:
            raise ValueError("PURGE_VIOLATION")

        if historical_data is None:
            # Generate deterministic dataset with sufficient bars
            timestamps = [1700000000 + i * int(timeframe_seconds) for i in range(1500)]
            prices = [65000.0 + (math.sin(i * 0.03) * 300.0) + (i * 0.2) for i in range(1500)]
            historical_data = pl.DataFrame({
                "timestamp": timestamps,
                "price": prices,
            })

        purifier = DataPurifier()
        purified_data = purifier.purify_tick_data(historical_data)

        total_bars = len(purified_data)
        min_required = train_window_bars + purge_bars + test_window_bars
        if total_bars < min_required:
            raise ValueError(
                f"Historical data length ({total_bars}) is less than minimum required bars ({min_required})"
            )

        folds = []
        start = 0
        fold_idx = 0
        
        pooled_returns = []
        pooled_equity = []
        
        def ts(idx):
            if idx < 0: return 0.0
            if idx >= total_bars: idx = total_bars - 1
            return float(purified_data["timestamp"][idx])

        while (start + train_window_bars + purge_bars + test_window_bars) <= total_bars:
            train_slice = purified_data.slice(start, train_window_bars)

            # In-Sample (Train) Phase: grid search over param_grid
            candidates = []
            
            for params in param_grid:
                strat_logic = strategy_factory(params)
                is_res = self.run_backtest(
                    strategy_logic=strat_logic,
                    historical_data=train_slice,
                    initial_capital=initial_capital,
                    timeframe_seconds=timeframe_seconds,
                    spread_pct=spread_pct,
                    slippage_pct=slippage_pct,
                    commission_pct=commission_pct,
                )
                
                is_sharpe = float(is_res.metrics.get("sharpe_ratio", 0.0))
                is_max_dd = float(is_res.metrics.get("max_drawdown", 0.0))
                is_turnover = float(is_res.metrics.get("total_turnover_count", 0.0))
                
                candidates.append({
                    "params": params,
                    "is_res": is_res,
                    "is_sharpe": is_sharpe,
                    "is_max_dd": is_max_dd,
                    "is_turnover": is_turnover,
                })
                
            def _wfo_selection_key(c):
                return (round(c["is_sharpe"], 6), -abs(c["is_max_dd"]), -c["is_turnover"])
                
            candidates.sort(key=_wfo_selection_key, reverse=True)
            best_cand = candidates[0]
            best_params = best_cand["params"]
            best_is_result = best_cand["is_res"]
            
            runner_up_cand = candidates[1] if len(candidates) > 1 else None
            
            best_sharpe_rounded = round(best_cand["is_sharpe"], 6)
            tie_count = sum(1 for c in candidates if round(c["is_sharpe"], 6) == best_sharpe_rounded)

            # Out-of-Sample (Test OOS) Phase with Purge and Warmup (RES-RED-18)
            oos_start_idx = start + train_window_bars + purge_bars
            warmup_start_idx = max(0, oos_start_idx - warmup_bars)
            actual_warmup = oos_start_idx - warmup_start_idx
            
            test_slice_with_warmup = purified_data.slice(warmup_start_idx, actual_warmup + test_window_bars)

            best_strat_logic = strategy_factory(best_params) if best_params is not None else None
            oos_res = self.run_backtest(
                strategy_logic=best_strat_logic,
                historical_data=test_slice_with_warmup,
                initial_capital=initial_capital,
                timeframe_seconds=timeframe_seconds,
                spread_pct=spread_pct,
                slippage_pct=slippage_pct,
                commission_pct=commission_pct,
            )

            # Score strict OOS portion only (excluding warmup bars)
            oos_returns = []
            if actual_warmup > 0 and len(oos_res.equity_curve) > actual_warmup:
                oos_equity_df = oos_res.equity_curve.slice(actual_warmup, test_window_bars)
                oos_returns = oos_equity_df["strategy_return"].to_list() if "strategy_return" in oos_equity_df.columns else []
                for r in oos_returns:
                    if r is None or not math.isfinite(r):
                        raise ValueError("Gagal-Tutup: Non-finite value detected in oos_returns")

                oos_sharpe = calculate_sharpe_ratio(oos_returns, timeframe_seconds=timeframe_seconds)
                oos_metrics = dict(oos_res.metrics)
                oos_metrics["sharpe_ratio"] = round(oos_sharpe, 4)
                if len(oos_equity_df) > 0 and "equity" in oos_equity_df.columns:
                    eq_init = float(oos_equity_df["equity"][0])
                    eq_final = float(oos_equity_df["equity"][-1])
                    oos_metrics["total_return"] = round((eq_final - eq_init) / eq_init, 4) if eq_init > 0 else 0.0
                    oos_metrics["total_return_pct"] = round(oos_metrics["total_return"] * 100.0, 2)
                    oos_metrics["net_return_pct"] = oos_metrics["total_return_pct"]
                    
                    pooled_returns.extend(oos_returns)
                    if not pooled_equity:
                        pooled_equity.extend(oos_equity_df["equity"].to_list())
                    else:
                        last_eq = pooled_equity[-1]
                        for r in oos_returns:
                            last_eq *= (1.0 + r)
                            pooled_equity.append(last_eq)
            else:
                oos_metrics = oos_res.metrics
                oos_sharpe = float(oos_res.metrics.get("sharpe_ratio", 0.0))
                if len(oos_res.equity_curve) > 0:
                    oos_returns = oos_res.equity_curve["strategy_return"].to_list() if "strategy_return" in oos_res.equity_curve.columns else []
                    for r in oos_returns:
                        if r is None or not math.isfinite(r):
                            raise ValueError("Gagal-Tutup: Non-finite value detected in oos_returns")

                    pooled_returns.extend(oos_returns)
                    if not pooled_equity:
                        pooled_equity.extend(oos_res.equity_curve["equity"].to_list() if "equity" in oos_res.equity_curve.columns else [])
                    else:
                        last_eq = pooled_equity[-1]
                        for r in oos_returns:
                            last_eq *= (1.0 + r)
                            pooled_equity.append(last_eq)

            is_sharpe = float(best_cand["is_sharpe"])
            wfe_ratio = (oos_sharpe / is_sharpe) if is_sharpe > 0.0 else 0.0
            
            fold_evidence = WFOFoldEvidence(
                fold_id=fold_idx,
                train_start_ts=ts(start),
                train_end_ts=ts(start + train_window_bars - 1),
                purge_start_ts=ts(start + train_window_bars),
                purge_end_ts=ts(oos_start_idx - 1),
                oos_start_ts=ts(oos_start_idx),
                oos_end_ts=ts(oos_start_idx + test_window_bars - 1),
                candidate_count=len(param_grid),
                selection_metric=optimization_metric,
                winner_params=best_params,
                winner_is_score=is_sharpe,
                runner_up_params=runner_up_cand["params"] if runner_up_cand else None,
                runner_up_is_score=runner_up_cand["is_sharpe"] if runner_up_cand else None,
                tie_count=tie_count,
                tie_break_rule="(round(is_sharpe, 6), -abs(is_max_dd), -is_turnover)",
                is_metrics=dict(best_is_result.metrics),
                oos_metrics=oos_metrics,
                oos_returns=tuple(oos_returns),
                wfe=wfe_ratio
            )
            folds.append(fold_evidence)

            fold_idx += 1
            start += step_bars

        pooled_oos_returns_tup = tuple(pooled_returns)
        pooled_oos_equity_tup = tuple(pooled_equity)
        pooled_oos_sharpe = calculate_sharpe_ratio(pooled_returns, timeframe_seconds=timeframe_seconds)
        
        pooled_total_return = 0.0
        pooled_max_dd = 0.0
        if pooled_equity:
            eq_init = pooled_equity[0]
            eq_final = pooled_equity[-1]
            if eq_init > 0:
                pooled_total_return = (eq_final - eq_init) / eq_init
                
            peak = pooled_equity[0]
            for eq in pooled_equity:
                if eq > peak:
                    peak = eq
                dd = (peak - eq) / peak if peak > 0 else 0.0
                if dd > pooled_max_dd:
                    pooled_max_dd = dd

        fold_oos_sharpes = [f.oos_metrics.get("sharpe_ratio", 0.0) for f in folds]
        fold_wfes = [f.wfe for f in folds]
        
        def _mean(vals): return sum(vals)/len(vals) if vals else 0.0
        def _median(vals):
            if not vals: return 0.0
            s = sorted(vals)
            n = len(s)
            if n % 2 == 1: return s[n//2]
            return (s[n//2 - 1] + s[n//2]) / 2.0
            
        def _worst(vals): return min(vals) if vals else 0.0
        def _std(vals):
            if not vals: return 0.0
            m = _mean(vals)
            var = sum((v - m)**2 for v in vals) / len(vals)
            return math.sqrt(var)

        fold_count = len(folds)
        parameter_family_size = len(param_grid)
        evaluation_count = fold_count * parameter_family_size
        
        training_overlap_ratio = 0.0
        oos_overlap_ratio = 0.0
        if fold_count > 1:
            training_overlap_ratio = max(0.0, (train_window_bars - step_bars) / train_window_bars)
            oos_overlap_ratio = max(0.0, (test_window_bars - step_bars) / test_window_bars)
            
        run_id = f"wfo_{int(time.time())}_{os.urandom(4).hex()}"
        
        import json
        import hashlib
        
        if historical_data is not None and len(historical_data) > 0:
            import struct
            ts_list = historical_data["timestamp"].to_list() if "timestamp" in historical_data.columns else []
            pr_list = historical_data["price"].to_list() if "price" in historical_data.columns else []
            vol_list = historical_data["volume"].to_list() if "volume" in historical_data.columns else [0.0]*len(ts_list)
            
            version = b"V1"
            symbol = b"UNKNOWN"
            tf_bytes = struct.pack(">d", float(timeframe_seconds))
            ts_bytes = b"".join(struct.pack(">d", float(x)) for x in ts_list)
            pr_bytes = b"".join(struct.pack(">d", float(x)) for x in pr_list)
            vol_bytes = b"".join(struct.pack(">d", float(x)) for x in vol_list)
            
            data_bytes = version + symbol + tf_bytes + ts_bytes + pr_bytes + vol_bytes
        else:
            data_bytes = b"0"

        evidence = WFOEvidence(
            run_id=run_id,
            dataset_hash=compute_sha256(data_bytes),
            timeframe_seconds=timeframe_seconds,
            data_start_ts=float(historical_data["timestamp"][0]) if len(historical_data) > 0 else 0.0,
            data_end_ts=float(historical_data["timestamp"][-1]) if len(historical_data) > 0 else 0.0,
            folds=tuple(folds),
            fold_count=fold_count,
            parameter_family_size=parameter_family_size,
            evaluation_count=evaluation_count,
            effective_trial_count=parameter_family_size,
            effective_trial_method="CONSERVATIVE_FAMILY_SIZE_PROXY",
            effective_trial_assumption="Independent hypotheses within grid",
            training_overlap_ratio=training_overlap_ratio,
            oos_overlap_ratio=oos_overlap_ratio,
            purge_bars=purge_bars,
            label_horizon_bars=label_horizon_bars,
            label_horizon_unit="BARS",
            warmup_bars=warmup_bars,
            pooled_oos_returns=pooled_oos_returns_tup,
            pooled_oos_equity=pooled_oos_equity_tup,
            pooled_oos_sharpe=pooled_oos_sharpe,
            pooled_oos_return=pooled_total_return,
            pooled_oos_max_drawdown=pooled_max_dd,
            mean_fold_oos_sharpe=_mean(fold_oos_sharpes),
            median_fold_oos_sharpe=_median(fold_oos_sharpes),
            worst_fold_oos_sharpe=_worst(fold_oos_sharpes),
            std_fold_oos_sharpe=_std(fold_oos_sharpes),
            mean_wfe=_mean(fold_wfes),
            median_wfe=_median(fold_wfes),
            worst_wfe=_worst(fold_wfes),
            provenance_hash=""
        )

        payload = build_wfo_provenance_payload(evidence)
        provenance_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()
        
        import dataclasses
        evidence = dataclasses.replace(evidence, provenance_hash=provenance_hash)

        # P1-3: Auto-save WFOEvidence to disk for reproducibility
        try:
            wfo_dir = "data/backtests"
            os.makedirs(wfo_dir, exist_ok=True)
            wfo_file = os.path.join(wfo_dir, f"wfo-{run_id}.json")
            wfo_payload = {
                "run_id": evidence.run_id,
                "dataset_hash": evidence.dataset_hash,
                "provenance_hash": evidence.provenance_hash,
                "fold_count": evidence.fold_count,
                "parameter_family_size": evidence.parameter_family_size,
                "pooled_oos_sharpe": evidence.pooled_oos_sharpe,
                "pooled_oos_return": evidence.pooled_oos_return,
                "pooled_oos_max_drawdown": evidence.pooled_oos_max_drawdown,
                "mean_wfe": evidence.mean_wfe,
                "purge_bars": evidence.purge_bars,
                "warmup_bars": evidence.warmup_bars,
                "fold_details": [
                    {
                        "fold_id": f.fold_id,
                        "winner_params": f.winner_params,
                        "oos_sharpe": f.oos_metrics.get("sharpe_ratio", 0.0),
                        "wfe": f.wfe,
                    } for f in evidence.folds
                ],
                "timestamp": time.time(),
            }
            with open(wfo_file, "w") as wf:
                json.dump(wfo_payload, wf, indent=2, default=str)
        except Exception:
            pass  # Non-critical — don't fail WFO if save fails

        return evidence


# =============================================================================
# BASELINE SUITE — Information Value Assessment (P1-1)
# =============================================================================

def baseline_buy_and_hold(df: pl.DataFrame) -> pl.DataFrame:
    """Always long from bar 0 — the simplest possible benchmark."""
    return df.with_columns(pl.lit(1.0).alias("signal"))


def baseline_always_flat(df: pl.DataFrame) -> pl.DataFrame:
    """Never trade — tests whether any alpha exists above zero."""
    return df.with_columns(pl.lit(0.0).alias("signal"))


def baseline_naive_long(df: pl.DataFrame) -> pl.DataFrame:
    """Long if previous return was positive (momentum 1-bar)."""
    return df.with_columns(
        pl.when(pl.col("price").pct_change().shift(1) > 0).then(1.0)
        .otherwise(0.0).alias("signal")
    )


def baseline_naive_short(df: pl.DataFrame) -> pl.DataFrame:
    """Short if previous return was negative (mean-reversion 1-bar)."""
    return df.with_columns(
        pl.when(pl.col("price").pct_change().shift(1) < 0).then(-1.0)
        .otherwise(0.0).alias("signal")
    )


def baseline_random_permutation(df: pl.DataFrame, seed: int = 42) -> pl.DataFrame:
    """Random signal — tests if strategy beats noise."""
    import random as _rng
    rng = _rng.Random(seed)
    n = len(df)
    signals = [rng.choice([-1.0, 0.0, 1.0]) for _ in range(n)]
    return df.with_columns(pl.Series("signal", signals))


BASELINE_STRATEGIES = {
    "buy_and_hold": baseline_buy_and_hold,
    "always_flat": baseline_always_flat,
    "naive_long": baseline_naive_long,
    "naive_short": baseline_naive_short,
    "random_permutation": baseline_random_permutation,
}


def run_baseline_comparison(
    engine: "IsolatedBacktestEngine",
    historical_data: pl.DataFrame,
    strategy_logic: Optional[Callable[[pl.DataFrame], pl.DataFrame]] = None,
    strategy_name: str = "strategy",
    initial_capital: float = 10000.0,
    timeframe_seconds: float = 3600.0,
    spread_pct: float = 0.0001,
    slippage_pct: float = 0.00005,
    commission_pct: float = 0.00005,
) -> Dict[str, Any]:
    """
    Runs strategy against all baselines. Returns comparison dict.
    Strategy has alpha if it beats all baselines on Sharpe AND return.
    """
    results = {}
    
    # Run baselines
    for name, bl_logic in BASELINE_STRATEGIES.items():
        try:
            r = engine.run_backtest(
                strategy_logic=bl_logic,
                historical_data=historical_data,
                initial_capital=initial_capital,
                timeframe_seconds=timeframe_seconds,
                spread_pct=spread_pct,
                slippage_pct=slippage_pct,
                commission_pct=commission_pct,
            )
            results[name] = {
                "sharpe": r.metrics.get("sharpe_ratio", 0.0),
                "return_pct": r.metrics.get("total_return_pct", 0.0),
                "max_dd_pct": r.metrics.get("max_drawdown_pct", 0.0),
                "trades": r.metrics.get("total_trades", 0),
            }
        except Exception as e:
            results[name] = {"error": str(e)}
    
    # Run actual strategy
    if strategy_logic is not None:
        try:
            r = engine.run_backtest(
                strategy_logic=strategy_logic,
                historical_data=historical_data,
                initial_capital=initial_capital,
                timeframe_seconds=timeframe_seconds,
                spread_pct=spread_pct,
                slippage_pct=slippage_pct,
                commission_pct=commission_pct,
            )
            results[strategy_name] = {
                "sharpe": r.metrics.get("sharpe_ratio", 0.0),
                "return_pct": r.metrics.get("total_return_pct", 0.0),
                "max_dd_pct": r.metrics.get("max_drawdown_pct", 0.0),
                "trades": r.metrics.get("total_trades", 0),
            }
        except Exception as e:
            results[strategy_name] = {"error": str(e)}
    
    # Assessment
    if strategy_name in results and "error" not in results[strategy_name]:
        strat = results[strategy_name]
        beats_all_sharpe = all(
            v.get("sharpe", -999) < strat["sharpe"]
            for k, v in results.items()
            if k != strategy_name and "error" not in v
        )
        beats_all_return = all(
            v.get("return_pct", -999) < strat["return_pct"]
            for k, v in results.items()
            if k != strategy_name and "error" not in v
        )
        results["_assessment"] = {
            "has_alpha": beats_all_sharpe and beats_all_return,
            "beats_all_sharpe": beats_all_sharpe,
            "beats_all_return": beats_all_return,
            "strategy_sharpe": strat["sharpe"],
            "best_baseline_sharpe": max(
                (v.get("sharpe", -999) for k, v in results.items()
                 if k != strategy_name and "error" not in v),
                default=0.0
            ),
        }
    
    return results


# =============================================================================
# PARAMETER STABILITY ANALYSIS (P1-2)
# =============================================================================

def parameter_stability_analysis(
    engine: "IsolatedBacktestEngine",
    historical_data: pl.DataFrame,
    base_strategy: Callable[[pl.DataFrame], pl.DataFrame],
    param_name: str,
    param_values: List[float],
    param_mutator: Callable[[pl.DataFrame, float], pl.DataFrame],
    initial_capital: float = 10000.0,
    timeframe_seconds: float = 3600.0,
) -> Dict[str, Any]:
    """
    Tests parameter stability: does performance degrade gracefully near the winner?
    
    param_mutator: function(df, param_value) -> df_with_signal
    Returns performance surface + stability assessment.
    """
    surface = []
    for val in param_values:
        try:
            r = engine.run_backtest(
                strategy_logic=lambda df, v=val: param_mutator(df, v),
                historical_data=historical_data,
                initial_capital=initial_capital,
                timeframe_seconds=timeframe_seconds,
            )
            surface.append({
                "param_value": val,
                "sharpe": r.metrics.get("sharpe_ratio", 0.0),
                "return_pct": r.metrics.get("total_return_pct", 0.0),
                "max_dd_pct": r.metrics.get("max_drawdown_pct", 0.0),
                "trades": r.metrics.get("total_trades", 0),
            })
        except Exception as e:
            surface.append({"param_value": val, "error": str(e)})
    
    valid = [s for s in surface if "error" not in s]
    if len(valid) < 3:
        return {"surface": surface, "stability": "INSUFFICIENT_DATA", "verdict": "NEED_MORE_POINTS"}
    
    sharpes = [s["sharpe"] for s in valid]
    best_idx = sharpes.index(max(sharpes))
    best_val = valid[best_idx]["param_value"]
    best_sharpe = max(sharpes)
    
    # Check neighborhood stability: ±1, ±2 indices from best
    neighbors_sharpes = []
    for offset in [-2, -1, 1, 2]:
        idx = best_idx + offset
        if 0 <= idx < len(valid):
            neighbors_sharpes.append(valid[idx]["sharpe"])
    
    if neighbors_sharpes:
        mean_neighbor = sum(neighbors_sharpes) / len(neighbors_sharpes)
        stability_ratio = mean_neighbor / best_sharpe if best_sharpe > 0 else 0.0
    else:
        stability_ratio = 0.0
    
    # Assessment
    if stability_ratio >= 0.7:
        stability = "ROBUST"
        verdict = "PARAMETER_IS_STABLE"
    elif stability_ratio >= 0.4:
        stability = "MARGINAL"
        verdict = "PARAMETER_SENSITIVE_BUT_USEABLE"
    else:
        stability = "FRAGILE"
        verdict = "PARAMETER_PEAK_IS_SUSPICIOUS"
    
    return {
        "param_name": param_name,
        "surface": surface,
        "best_param": best_val,
        "best_sharpe": round(best_sharpe, 4),
        "stability_ratio": round(stability_ratio, 4),
        "stability": stability,
        "verdict": verdict,
    }

