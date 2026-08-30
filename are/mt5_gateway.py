"""
AHFMES MT5_BRIDGE — Safety-Gated Execution Gateway (ACC-603, ACC-604)

Strictly routes all order requests through the CapitalSafetyKernel firewall before execution.
Zero external hard-dependencies (stdlib only: json, time, math, typing, dataclasses).
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from are.operational import OperationalSignal
from are.safety import CapitalSafetyKernel, SafetyDecision, SafetyLimits
from are.execution_state import ExecutionStateMachine, OrderState


class ARETransientError(Exception):
    """Exception for transient errors (e.g., timeout, stale data)."""
    pass

class AREFatalError(Exception):
    """Exception for fatal errors (e.g., account query fail)."""
    pass

class AREAmbiguousExecutionError(Exception):
    """Exception for ambiguous states (e.g., order sent but confirmation lost)."""
    pass


@dataclass(frozen=True)
class MT5OrderRequest:
    symbol: str
    action: str  # "BUY" | "SELL"
    volume: float
    price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    comment: str = "ARE_SIGNAL"
    magic: int = 1001


@dataclass(frozen=True)
class MT5OrderResult:
    success: bool
    retcode: int
    order_id: int
    deal_id: int
    volume: float
    price: float
    comment: str
    timestamp: float


class MT5MockGateway:
    """Simulated MT5 trade server recording positions and fills."""

    def __init__(self):
        self._order_counter = 10000
        self._positions: Dict[int, Dict[str, Any]] = {}

    def send_order(self, request: MT5OrderRequest) -> MT5OrderResult:
        self._order_counter += 1
        order_id = self._order_counter
        deal_id = order_id + 50000
        fill_price = request.price or (65000.0 if request.action == "BUY" else 64998.0)
        ts = time.time()

        pos = {
            "ticket": order_id,
            "symbol": request.symbol,
            "type": request.action,
            "volume": request.volume,
            "open_price": fill_price,
            "sl": request.sl,
            "tp": request.tp,
            "magic": request.magic,
            "comment": request.comment,
            "open_time": ts,
        }
        self._positions[order_id] = pos

        return MT5OrderResult(
            success=True,
            retcode=10009,  # TRADE_RETCODE_DONE
            order_id=order_id,
            deal_id=deal_id,
            volume=request.volume,
            price=fill_price,
            comment=f"MOCK_FILLED_{request.comment}",
            timestamp=ts,
        )

    def close_all_positions(self, symbol: Optional[str] = None) -> List[int]:
        closed_tickets: List[int] = []
        tickets = list(self._positions.keys())
        for t in tickets:
            pos = self._positions[t]
            if symbol is None or pos["symbol"] == symbol:
                closed_tickets.append(t)
                del self._positions[t]
        return closed_tickets

    def get_open_positions(self) -> List[Dict[str, Any]]:
        return list(self._positions.values())


class MT5ExecutionGateway:
    """Safety-Gated Execution Gateway enforcing CapitalSafetyKernel limits before MT5 delivery."""

    def __init__(
        self,
        safety_kernel: CapitalSafetyKernel,
        use_mock: bool = True,
        state_file: Optional[str] = None,
    ):
        self.safety_kernel = safety_kernel
        self.use_mock = use_mock
        self._mock_gateway = MT5MockGateway() if use_mock else None
        self._mt5_lib: Optional[Any] = None
        self._exec_state = ExecutionStateMachine(state_file)
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="MT5GatewayWorker")

        if not use_mock:
            try:
                import MetaTrader5 as mt5
                self._mt5_lib = mt5
            except ImportError:
                self._mt5_lib = None
                self._mock_gateway = None
                raise RuntimeError("LIVE_MT5_REQUIRED_BUT_UNAVAILABLE: MetaTrader5 package is not installed or unavailable.")

    def get_recent_order_count(self, window_seconds: float = 60.0) -> int:
        """Counts orders filled within the sliding window (persistent, survives restart)."""
        return self._exec_state.get_order_count(window_seconds)

    def record_order_timestamp(self, ts: Optional[float] = None) -> None:
        """Records the timestamp of a successfully dispatched/filled order (persistent)."""
        self._exec_state.record_order()

    def get_account_info(self, default_equity: float = 10000.0) -> Dict[str, float]:
        """Polls live account balance, equity, and computes peak-equity drawdown (persistent, survives restart)."""
        if self._mt5_lib is not None:
            acc = self._mt5_lib.account_info()
            if acc is not None:
                bal = float(getattr(acc, "balance", default_equity))
                eq = float(getattr(acc, "equity", default_equity))
                dd = self._exec_state.update_peak_equity(eq)
                return {
                    "balance": bal,
                    "equity": eq,
                    "peak_equity": self._exec_state.peak_equity,
                    "drawdown": dd / 100.0,
                }
            else:
                raise AREFatalError("Failed to fetch account info from MT5.")

        # Mock/default path — also track peak (persistent)
        dd = self._exec_state.update_peak_equity(default_equity)
        return {
            "balance": default_equity,
            "equity": default_equity,
            "peak_equity": self._exec_state.peak_equity,
            "drawdown": dd / 100.0,
        }

    def calculate_lot_size(
        self,
        account_equity: float,
        risk_pct: float = 0.01,
        stop_loss_points: float = 100.0,
    ) -> float:
        """
        Calculates safe lot size and clamps against CSK max_position_size (ACC-405).
        """
        if account_equity <= 0.0 or stop_loss_points <= 0.0:
            return 0.01

        risk_capital = account_equity * risk_pct
        raw_lots = risk_capital / (stop_loss_points * 1.0)
        clamped_lots = min(self.safety_kernel.limits.max_position_size, max(0.01, raw_lots))
        return round(clamped_lots, 2)

    def execute_order(
        self,
        request: MT5OrderRequest,
        current_risk_state: Dict[str, Any],
    ) -> Tuple[bool, Optional[MT5OrderResult], str]:
        """
        Gated order execution with strict CSK firewall validation (ACC-603).
        """
        drawdown = current_risk_state.get("drawdown", 0.0)
        volatility = current_risk_state.get("volatility", 1.0)
        # ─── P0-02: Persistent Kill Switch (first check, before anything else) ───
        if self._exec_state.kill_switch_active:
            return False, None, "CSK_VETO: PERSISTENT_KILL_SWITCH_ACTIVE (P0-02)"

        order_count = current_risk_state.get("order_count", self.get_recent_order_count(60.0))

        # ─── P0-01: Create order lifecycle entry ───
        order_id = f"ord-{int(time.time()*1000)}-{request.symbol}"
        lifecycle = self._exec_state.create_order(
            order_id=order_id,
            symbol=request.symbol,
            action=request.action,
            volume=request.volume,
        )

        intended_action = {
            "action": request.action,
            "position_size": request.volume,
            "symbol": request.symbol,
            "price": request.price,
        }

        # 1. Capital Safety Kernel Firewall Evaluation (MANDATORY — P0-02)
        decision = self.safety_kernel.evaluate_action(
            intended_action=intended_action,
            current_drawdown=drawdown,
            current_volatility=volatility,
            recent_order_count=order_count,
        )

        if not decision.allowed:
            self._exec_state.mark_failed(order_id, f"CSK_VETO: {decision.reason}")
            return False, None, f"CSK_VETO: {decision.reason} (Action: {decision.action})"

        # 2. Adjust volume to clamped size if clamped
        target_volume = min(request.volume, decision.clamped_size)
        adjusted_request = MT5OrderRequest(
            symbol=request.symbol,
            action=request.action,
            volume=target_volume,
            price=request.price,
            sl=request.sl,
            tp=request.tp,
            comment=request.comment,
            magic=request.magic,
        )

        # 3. Dispatch → Acknowledged → Filled lifecycle
        self._exec_state.dispatch_order(order_id)

        if self._mock_gateway is not None:
            res = self._mock_gateway.send_order(adjusted_request)
            self._exec_state.acknowledge_order(order_id, res.retcode, res.comment)
            self._exec_state.fill_order(order_id, res.volume, res.price, res.order_id)
            self._exec_state.reconcile_order(order_id, self._mock_gateway.get_open_positions())
            self._exec_state.finalize_order(order_id)
            self.record_order_timestamp()
            return True, res, "FILLED_MOCK"

        if self._mt5_lib is not None:
            order_type = self._mt5_lib.ORDER_TYPE_BUY if request.action == "BUY" else self._mt5_lib.ORDER_TYPE_SELL
            req_dict = {
                "action": self._mt5_lib.TRADE_ACTION_DEAL,
                "symbol": adjusted_request.symbol,
                "volume": adjusted_request.volume,
                "type": order_type,
                "price": adjusted_request.price or self._mt5_lib.symbol_info_tick(adjusted_request.symbol).ask,
                "sl": adjusted_request.sl or 0.0,
                "tp": adjusted_request.tp or 0.0,
                "magic": adjusted_request.magic,
                "comment": adjusted_request.comment,
                "type_time": self._mt5_lib.ORDER_TIME_GTC,
                "type_filling": self._mt5_lib.ORDER_FILLING_IOC,
            }

            try:
                res_mt5 = self._mt5_lib.order_send(req_dict)
            except Exception as e:
                self._exec_state.mark_ambiguous(order_id, f"EXCEPTION: {e}")
                raise AREAmbiguousExecutionError(f"Order dispatched but exception: {e}. State ambiguous.")

            if res_mt5 is None:
                self._exec_state.mark_ambiguous(order_id, "MT5 returned None")
                raise AREAmbiguousExecutionError("Order dispatched but MT5 returned None. State ambiguous.")

            self._exec_state.acknowledge_order(order_id, res_mt5.retcode, getattr(res_mt5, 'comment', ''))

            if res_mt5.retcode != self._mt5_lib.TRADE_RETCODE_DONE:
                ret = res_mt5.retcode if res_mt5 else -1
                self._exec_state.mark_failed(order_id, f"MT5_ERROR_{ret}")
                return False, None, f"MT5_ERROR_{ret}"

            # Partial fill check
            filled_vol = getattr(res_mt5, 'volume', adjusted_request.volume)
            self._exec_state.fill_order(order_id, filled_vol, res_mt5.price, res_mt5.deal)

            # Reconcile against actual positions
            try:
                positions = self.get_open_positions()
                self._exec_state.reconcile_order(order_id, positions)
                self._exec_state.finalize_order(order_id)
            except Exception:
                pass  # Best-effort reconciliation

            self.record_order_timestamp()
            return True, MT5OrderResult(
                success=True,
                retcode=res_mt5.retcode,
                order_id=res_mt5.order,
                deal_id=res_mt5.deal,
                volume=res_mt5.volume,
                price=res_mt5.price,
                comment=res_mt5.comment,
                timestamp=time.time(),
            ), "FILLED_LIVE"

        self._exec_state.mark_failed(order_id, "NO_GATEWAY_AVAILABLE")
        return False, None, "NO_GATEWAY_AVAILABLE"

    async def execute_order_async(
        self,
        request: MT5OrderRequest,
        current_risk_state: Dict[str, Any],
    ) -> Tuple[bool, Optional[MT5OrderResult], str]:
        """Non-blocking asynchronous order execution via threadpool worker (ACC-603)."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            self.execute_order,
            request,
            current_risk_state,
        )

    async def send_order_async(
        self,
        signal: OperationalSignal,
        market_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """High-level async operational order dispatcher with latency monitoring (ACC-603)."""
        t_start = time.time()
        if signal.final_action not in ("BUY", "SELL", "EMERGENCY_FLAT"):
            return {"status": "ABSTAIN", "reason": "Signal is ABSTAIN / neutral", "latency_ms": 0.0}

        if signal.final_action == "EMERGENCY_FLAT":
            unclosed_positions = await self.emergency_flat_async()
            latency_ms = (time.time() - t_start) * 1000.0
            return {"status": "EMERGENCY_FLAT", "unclosed_positions": unclosed_positions, "latency_ms": latency_ms}

        symbol = market_state.get("symbol", "BTCUSD")
        price = market_state.get("price")
        lot_size = self.calculate_lot_size(
            account_equity=market_state.get("account_equity", 10000.0),
            risk_pct=0.01,
        )
        req = MT5OrderRequest(
            symbol=symbol,
            action=signal.final_action,
            volume=lot_size,
            price=price,
            comment=f"ASYNC_{signal.final_action}",
        )

        risk_state = {
            "drawdown": market_state.get("drawdown", 0.0),
            "volatility": market_state.get("volatility", 1.0),
            "order_count": self.get_recent_order_count(60.0),
        }

        success, result, status_msg = await self.execute_order_async(req, risk_state)
        latency_ms = (time.time() - t_start) * 1000.0

        return {
            "success": success,
            "status": status_msg,
            "order_result": result.__dict__ if result else None,
            "latency_ms": latency_ms,
        }

    def emergency_flat(self) -> List[Dict[str, Any]]:
        """
        Immediate emergency liquidation of all positions across all symbols (ACC-604).
        Performs verified read-back loop ensuring zero residual positions (RES-RED-04, RES-RED-14).
        Returns a list of positions that failed to close.
        """
        closed_count = 0

        # Attempt liquidation with up to 3 retries (4 total attempts)
        for attempt in range(4):
            if self._mock_gateway is not None:
                tickets = self._mock_gateway.close_all_positions()
                closed_count += len(tickets)
            elif self._mt5_lib is not None:
                positions = self._mt5_lib.positions_get()

                # CRITICAL: None = unknown, NOT flat. Continue retry (RES-RED-14).
                if positions is None:
                    time.sleep(0.1)
                    continue

                if positions:
                    for pos in positions:
                        tick = self._mt5_lib.symbol_info_tick(pos.symbol)
                        if tick is None:
                            continue
                        price = tick.bid if pos.type == self._mt5_lib.ORDER_TYPE_BUY else tick.ask
                        close_type = self._mt5_lib.ORDER_TYPE_SELL if pos.type == self._mt5_lib.ORDER_TYPE_BUY else self._mt5_lib.ORDER_TYPE_BUY
                        close_req = {
                            "action": self._mt5_lib.TRADE_ACTION_DEAL,
                            "position": pos.ticket,
                            "symbol": pos.symbol,
                            "volume": pos.volume,
                            "type": close_type,
                            "price": price,
                            "magic": pos.magic,
                            "comment": "ARE_EMERGENCY_FLAT",
                            "type_time": self._mt5_lib.ORDER_TIME_GTC,
                            "type_filling": self._mt5_lib.ORDER_FILLING_IOC,
                        }
                        res = self._mt5_lib.order_send(close_req)
                        if res and res.retcode == self._mt5_lib.TRADE_RETCODE_DONE:
                            closed_count += 1

            # Read-back verification
            try:
                open_pos = self.get_open_positions()
            except ARETransientError:
                time.sleep(0.1)
                continue
            except RuntimeError:
                # State unknown — continue retry, do NOT treat as flat (RES-RED-14)
                time.sleep(0.1)
                continue

            if len(open_pos) == 0:
                return []

            time.sleep(0.05)

        # Final check — may raise exception if still None
        try:
            residual_positions = self.get_open_positions()
        except Exception as e:
            raise ARETransientError(
                f"EMERGENCY_FLAT_VERIFICATION_FAILED: Position state UNKNOWN after 4 attempts. "
                f"Original: {e}"
            )

        return residual_positions

    async def emergency_flat_async(self) -> List[Dict[str, Any]]:
        """Non-blocking emergency liquidation via threadpool worker (ACC-604)."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self.emergency_flat)

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Returns open positions from Mock or Live MT5 terminal (RES-RED-02, RES-RED-14)."""
        if self._mock_gateway is not None:
            return self._mock_gateway.get_open_positions()

        if self._mt5_lib is not None:
            positions = self._mt5_lib.positions_get()

            # CRITICAL: Distinguish None (API error) from () (verified empty) (RES-RED-14)
            if positions is None:
                raise ARETransientError(
                    "MT5_POSITIONS_GET_RETURNED_NONE: "
                    "API error or connection lost. Position state is UNKNOWN. "
                    "Cannot safely assume flat."
                )

            if len(positions) == 0:
                return []

            pos_list = []
            for p in positions:
                pos_list.append({
                    "ticket": getattr(p, "ticket", 0),
                    "symbol": getattr(p, "symbol", ""),
                    "type": "BUY" if getattr(p, "type", 0) == 0 else "SELL",
                    "volume": getattr(p, "volume", 0.0),
                    "open_price": getattr(p, "price_open", 0.0),
                    "sl": getattr(p, "sl", 0.0),
                    "tp": getattr(p, "tp", 0.0),
                    "magic": getattr(p, "magic", 0),
                    "comment": getattr(p, "comment", ""),
                    "open_time": getattr(p, "time", 0),
                })
            return pos_list

        return []

    def close(self) -> None:
        if hasattr(self, '_executor') and self._executor:
            self._executor.shutdown(wait=False)
