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
from typing import Any, Callable, Dict, List, Optional

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
    ) -> BacktestResult:
        """
        Executes a vectorized backtest computation over historical market data.
        """
        if historical_data is None:
            # Generate deterministic synthetic data for default evaluations
            timestamps = [1700000000 + i * 60 for i in range(1000)]
            prices = [65000.0 + (math.sin(i * 0.05) * 200.0) + (i * 0.1) for i in range(1000)]
            historical_data = pl.DataFrame({
                "timestamp": timestamps,
                "price": prices,
            })

        # Purify raw tick / bar data via DataPurifier (Anti-GIGO, DELEGASI_029b)
        purifier = DataPurifier()
        purified_data = purifier.purify_tick_data(historical_data)

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
            df = df.with_columns(pl.lit(1.0).alias("signal"))

        # Neutralize / block trade execution on toxic spreads or closed market periods (DELEGASI_029b)
        if "is_toxic_spread" in df.columns or "is_market_closed" in df.columns:
            toxic_cond = pl.col("is_toxic_spread") if "is_toxic_spread" in df.columns else pl.lit(False)
            closed_cond = pl.col("is_market_closed") if "is_market_closed" in df.columns else pl.lit(False)
            blocked_cond = toxic_cond | closed_cond
            df = df.with_columns(
                pl.when(blocked_cond).then(pl.lit(0.0)).otherwise(pl.col("signal")).alias("signal")
            )

        # 2. Vectorized P&L and Returns Computation
        df = df.with_columns([
            (pl.col("price").pct_change()).fill_null(0.0).alias("price_return"),
            pl.col("signal").shift(1).fill_null(0.0).alias("prev_signal"),
        ]).with_columns([
            (pl.col("prev_signal") * pl.col("price_return")).alias("strategy_return")
        ])

        # 3. Cumulative Equity Curve
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

        sharpe_ratio = (mean_ret / std_ret * math.sqrt(252.0)) if std_ret > 1e-9 else 0.0

        gains = [r for r in returns_series if r > 0]
        losses = [abs(r) for r in returns_series if r < 0]
        total_gains = sum(gains)
        total_losses = sum(losses)
        profit_factor = (total_gains / total_losses) if total_losses > 1e-9 else (100.0 if total_gains > 0 else 1.0)

        metrics = {
            "initial_capital": initial_capital,
            "final_equity": round(final_equity, 2),
            "total_return": round(total_return, 4),
            "total_return_pct": round(total_return * 100.0, 2),
            "max_drawdown": round(max_drawdown_pct, 4),
            "max_drawdown_pct": round(max_drawdown_pct * 100.0, 2),
            "sharpe_ratio": round(sharpe_ratio, 4),
            "profit_factor": round(profit_factor, 4),
            "total_bars": len(df),
            "total_trades": len(trade_df),
        }

        equity_curve = df.select(["timestamp", "price", "signal", "equity", "drawdown"])
        return BacktestResult(equity_curve=equity_curve, trade_log=trade_df, metrics=metrics)

    def save_artifact(self, result: BacktestResult, evidence_ledger: EvidenceLedger) -> str:
        """
        Serializes the backtest result into a canonical JSON artifact and records it into
        the Evidence Ledger as immutable RESEARCH_PROOF, returning its content-addressed proof hash.
        """
        # Convert Polars DataFrames into native Python dicts/lists before JSON serialization
        equity_list = result.equity_curve.to_dicts()
        trade_list = result.trade_log.to_dicts()

        payload = {
            "equity_curve": equity_list,
            "trade_log": trade_list,
            "metrics": result.metrics,
            "timestamp": time.time(),
            "artifact_type": "RESEARCH_PROOF",
        }

        json_str = json.dumps(payload, sort_keys=True)
        proof_hash = compute_sha256(json_str)

        # Record to Evidence Ledger storage stream
        if hasattr(evidence_ledger, "_store") and evidence_ledger._store is not None:
            head = evidence_ledger._store.get_head("research_proofs")
            rev = head[0] if head else 0
            prev_h = head[1] if head else "0" * 64
            evidence_ledger._store.append_event(
                stream_id="research_proofs",
                event_data=json_str.encode("utf-8"),
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
    ) -> Dict[str, Any]:
        """
        Runs strategy evaluation on historical or synthetic Black Swan crisis datasets.
        Evaluates strict capital survival threshold (>= 50% capital retained and <= 50% max DD)
        and bankruptcy barrier (< 10% capital).
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

    def run_walk_forward_analysis(
        self,
        strategy_logic: Optional[Callable[[pl.DataFrame], pl.DataFrame]] = None,
        historical_data: Optional[pl.DataFrame] = None,
        train_window_bars: int = 252,
        test_window_bars: int = 63,
        step_bars: int = 63,
        initial_capital: float = 10000.0,
    ) -> Dict[str, Any]:
        """
        Executes multi-fold Walk-Forward Analysis (WFA) using rolling/expanding window slicing.
        Evaluates In-Sample (IS) training vs Out-of-Sample (OOS) testing degradation.
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

    # Alias for explicit API naming
    run_vectorized_backtest = run_backtest