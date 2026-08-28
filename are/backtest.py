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