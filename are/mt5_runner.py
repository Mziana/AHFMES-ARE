"""
AHFMES MT5_BRIDGE — Live Demo Runner Orchestrator (ACC-605)

Integrates live/mock feed, feature extraction, operational brain signal generation,
and safety-gated execution gateway in a real-time event loop.
Zero external hard-dependencies (stdlib only: json, time, typing, dataclasses).
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, List, Optional

from are.evidence import EvidenceLedger
from are.features import MarketFeatureExtractor
from are.mt5_feed import MT5FeedConfig, MT5MarketFeed
from are.mt5_gateway import MT5ExecutionGateway, MT5OrderRequest, MT5OrderResult
from are.operational import OperationalBrain, OperationalSignal
from are.storage import EventStore


class MT5LiveRunner:
    """Orchestrates live market feed polling, signal generation, and gated execution with async support."""

    def __init__(
        self,
        feed: MT5MarketFeed,
        gateway: MT5ExecutionGateway,
        brain: OperationalBrain,
        event_store: EventStore,
        evidence_ledger: EvidenceLedger,
        feature_extractor: Optional[MarketFeatureExtractor] = None,
        symbol: str = "BTCUSD",
    ):
        self.feed = feed
        self.gateway = gateway
        self.brain = brain
        self.event_store = event_store
        self.evidence_ledger = evidence_ledger
        self.feature_extractor = feature_extractor or MarketFeatureExtractor()
        self.symbol = symbol
        self._running = False
        self.last_latency_ms: float = 0.0

    def step_live_tick(self, account_equity: float = 10000.0) -> Dict[str, Any]:
        """
        Executes a single live market tick cycle synchronously.
        """
        # 1. Fetch latest ticks from Feed
        ticks = self.feed.get_latest_ticks(self.symbol, count=15)
        if not ticks:
            return {"status": "NO_TICKS_AVAILABLE", "symbol": self.symbol}

        latest_tick = ticks[-1]
        now_ts = latest_tick.get("time", time.time())

        # 2. Extract Quantitative Features
        features = self.feature_extractor.extract_features(ticks)

        # 3. Dynamic Account Info & Risk State (RES-RED-05, RES-RED-01)
        acc_info = self.gateway.get_account_info(default_equity=account_equity)
        current_dd = acc_info.get("drawdown", 0.0)
        real_equity = acc_info.get("equity", account_equity)

        risk_state = {
            "drawdown": current_dd,
            "volatility": features.get("realized_volatility", 1.0) * 100.0,
            "order_count": self.gateway.get_recent_order_count(60.0),
        }

        signal: OperationalSignal = self.brain.process_tick(
            symbol=self.symbol,
            timestamp=now_ts,
            market_features=features,
            current_risk_state=risk_state,
            as_of_cutoff=now_ts + 100.0,
        )

        exec_status = "NO_ACTION"
        order_res: Optional[MT5OrderResult] = None

        # 4. Gated Execution
        if signal.safety_decision and not signal.safety_decision.allowed:
            exec_status = f"CSK_VETO: {signal.safety_decision.reason}"
        elif signal.final_action in ("BUY", "SELL"):
            lots = self.gateway.calculate_lot_size(account_equity=real_equity, risk_pct=0.01)
            req = MT5OrderRequest(
                symbol=self.symbol,
                action=signal.final_action,
                volume=lots,
                price=latest_tick.get("ask") if signal.final_action == "BUY" else latest_tick.get("bid"),
                comment=f"ARE_{signal.raw_decision.get('champion_id', 'CHAMP')[:8]}",
            )
            success, order_res, exec_status = self.gateway.execute_order(req, risk_state)

        elif signal.final_action == "EMERGENCY_FLAT":
            closed = self.gateway.emergency_flat()
            exec_status = f"EMERGENCY_FLAT_CLOSED_{closed}"

        return {
            "status": "PROCESSED",
            "symbol": self.symbol,
            "timestamp": now_ts,
            "price": latest_tick.get("last", latest_tick.get("bid", 0.0)),
            "signal": signal.final_action,
            "execution_status": exec_status,
            "order_result": order_res.__dict__ if order_res else None,
            "open_positions": len(self.gateway.get_open_positions()),
        }

    async def step_live_tick_async(self, account_equity: float = 10000.0) -> Dict[str, Any]:
        """
        Executes a single live market tick cycle asynchronously with heartbeat latency tracking (ACC-605).
        """
        t_start = time.time()
        ticks = await self.feed.get_latest_ticks_async(self.symbol, count=15)
        if not ticks:
            return {"status": "NO_TICKS_AVAILABLE", "symbol": self.symbol, "latency_ms": 0.0}

        latest_tick = ticks[-1]
        now_ts = latest_tick.get("time", time.time())

        # Extract Features & Dynamic Account Risk State (RES-RED-05, RES-RED-01)
        features = self.feature_extractor.extract_features(ticks)
        acc_info = self.gateway.get_account_info(default_equity=account_equity)
        current_dd = acc_info.get("drawdown", 0.0)
        real_equity = acc_info.get("equity", account_equity)

        risk_state = {
            "drawdown": current_dd,
            "volatility": features.get("realized_volatility", 1.0) * 100.0,
            "order_count": self.gateway.get_recent_order_count(60.0),
        }

        signal: OperationalSignal = self.brain.process_tick(
            symbol=self.symbol,
            timestamp=now_ts,
            market_features=features,
            current_risk_state=risk_state,
            as_of_cutoff=now_ts + 100.0,
        )

        exec_status = "NO_ACTION"
        order_res: Optional[MT5OrderResult] = None

        # Heartbeat & Latency Gate Check
        elapsed_so_far_ms = (time.time() - t_start) * 1000.0
        if elapsed_so_far_ms > 5000.0:
            # Latency violation circuit breaker
            await self.gateway.emergency_flat_async()
            return {
                "status": "CIRCUIT_BREAKER_LATENCY_VIOLATION",
                "symbol": self.symbol,
                "latency_ms": elapsed_so_far_ms,
                "signal": "EMERGENCY_FLAT",
            }

        # Gated Execution
        if signal.safety_decision and not signal.safety_decision.allowed:
            exec_status = f"CSK_VETO: {signal.safety_decision.reason}"
        elif signal.final_action in ("BUY", "SELL"):
            lots = self.gateway.calculate_lot_size(account_equity=real_equity, risk_pct=0.01)
            req = MT5OrderRequest(
                symbol=self.symbol,
                action=signal.final_action,
                volume=lots,
                price=latest_tick.get("ask") if signal.final_action == "BUY" else latest_tick.get("bid"),
                comment=f"ARE_{signal.raw_decision.get('champion_id', 'CHAMP')[:8]}",
            )
            success, order_res, exec_status = await self.gateway.execute_order_async(req, risk_state)

        elif signal.final_action == "EMERGENCY_FLAT":
            closed = await self.gateway.emergency_flat_async()
            exec_status = f"EMERGENCY_FLAT_CLOSED_{closed}"

        total_latency_ms = (time.time() - t_start) * 1000.0
        self.last_latency_ms = total_latency_ms

        return {
            "status": "PROCESSED",
            "symbol": self.symbol,
            "timestamp": now_ts,
            "price": latest_tick.get("last", latest_tick.get("bid", 0.0)),
            "signal": signal.final_action,
            "execution_status": exec_status,
            "order_result": order_res.__dict__ if order_res else None,
            "open_positions": len(self.gateway.get_open_positions()),
            "latency_ms": total_latency_ms,
        }

    def run_live_loop(self, max_ticks: Optional[int] = 10, interval_sec: float = 0.1) -> int:
        """
        Runs the live loop for a specified number of ticks synchronously.
        """
        self._running = True
        processed = 0

        self.feed.initialize()

        while self._running:
            if max_ticks is not None and processed >= max_ticks:
                break

            try:
                self.step_live_tick()
                processed += 1
                if interval_sec > 0.0:
                    time.sleep(interval_sec)
            except KeyboardInterrupt:
                break
            except Exception as exc:
                self._running = False
                if hasattr(self.evidence_ledger, "record_incident"):
                    try:
                        self.evidence_ledger.record_incident(f"RUNNER_FATAL_EXCEPTION: {str(exc)}")
                    except Exception:
                        pass
                try:
                    self.gateway.emergency_flat()
                except Exception:
                    pass
                raise RuntimeError(f"MT5LiveRunner loop crashed: {exc}") from exc

        self._running = False
        return processed

    async def run_tick_stream_async(self, max_ticks: int = 100, interval_seconds: float = 0.05) -> int:
        """
        Consumes tick stream asynchronously without blocking other coroutines or threads (ACC-605).
        """
        self._running = True
        processed = 0

        self.feed.initialize()

        while self._running and processed < max_ticks:
            try:
                await self.step_live_tick_async()
                processed += 1
                if interval_seconds > 0.0:
                    await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self._running = False
                if hasattr(self.evidence_ledger, "record_incident"):
                    try:
                        self.evidence_ledger.record_incident(f"RUNNER_FATAL_EXCEPTION: {str(exc)}")
                    except Exception:
                        pass
                try:
                    await self.gateway.emergency_flat_async()
                except Exception:
                    pass
                raise RuntimeError(f"MT5LiveRunner loop crashed: {exc}") from exc

        self._running = False
        return processed

    def close(self) -> None:
        """Gracefully closes all underlying feed and gateway threadpools."""
        self._running = False
        if hasattr(self.feed, "shutdown"):
            self.feed.shutdown()
        if hasattr(self.gateway, "close"):
            self.gateway.close()
