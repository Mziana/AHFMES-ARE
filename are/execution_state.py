"""
AHFMES ARE — Execution State Machine (P0-01 Fix)

Implements formal order lifecycle:
  INTENDED → DISPATCHED → ACKNOWLEDGED → FILLED / PARTIAL / REJECTED
  → POSITION_RECONCILED → FINALIZED

Plus persistent state for peak equity, order rate, and kill switch.
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path


class OrderState(str, Enum):
    INTENDED = "INTENDED"
    DISPATCHED = "DISPATCHED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"
    RECONCILED = "RECONCILED"
    FINALIZED = "FINALIZED"
    FAILED = "FAILED"


@dataclass
class OrderLifecycle:
    """Tracks the full lifecycle of a single order."""
    order_id: str
    symbol: str
    action: str
    intended_volume: float
    filled_volume: float = 0.0
    fill_price: float = 0.0
    state: OrderState = OrderState.INTENDED
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    broker_retcode: Optional[int] = None
    broker_comment: str = ""
    reconciliation_attempts: int = 0
    error_message: str = ""
    position_ticket: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "action": self.action,
            "intended_volume": self.intended_volume,
            "filled_volume": self.filled_volume,
            "fill_price": self.fill_price,
            "state": self.state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "broker_retcode": self.broker_retcode,
            "broker_comment": self.broker_comment,
            "reconciliation_attempts": self.reconciliation_attempts,
            "error_message": self.error_message,
            "position_ticket": self.position_ticket,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "OrderLifecycle":
        d["state"] = OrderState(d["state"])
        return cls(**d)


class ExecutionStateMachine:
    """
    Manages order lifecycle and persistent system state.

    Persistent state file stores:
    - peak_equity (survives restart)
    - order_timestamps (rate limiter survives restart)
    - kill_switch_active (survives restart)
    - recent_orders (for reconciliation)
    """

    STATE_FILE = "data/execution_state.json"

    def __init__(self, state_file: Optional[str] = None):
        self.state_file = state_file or self.STATE_FILE
        self._lock = threading.Lock()  # Thread-safe access from multiple threads
        self._active_orders: Dict[str, OrderLifecycle] = {}
        self._finalized_orders: List[OrderLifecycle] = []
        self._peak_equity: float = 0.0
        self._order_timestamps: List[float] = []
        self._kill_switch_active: bool = False
        self._persisted_positions: List[Dict] = []  # P0-3: Persist open positions
        self._load_state()

    def _load_state(self):
        """Load persistent state from disk."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                self._peak_equity = data.get("peak_equity", 0.0)
                self._order_timestamps = data.get("order_timestamps", [])
                self._kill_switch_active = data.get("kill_switch_active", False)
                self._persisted_positions = data.get("persisted_positions", [])
                # Load any unfinished orders for reconciliation
                for od in data.get("active_orders", []):
                    ol = OrderLifecycle.from_dict(od)
                    if ol.state not in (OrderState.FINALIZED, OrderState.FAILED):
                        self._active_orders[ol.order_id] = ol
            except (json.JSONDecodeError, KeyError) as e:
                # P0-2: Corrupt state must BLOCK startup, not reset silently
                # Save corrupted file for forensic analysis
                import shutil
                corrupt_backup = self.state_file + f".corrupt.{int(time.time())}"
                shutil.copy2(self.state_file, corrupt_backup)
                # Set UNKNOWN state — operator must investigate
                self._kill_switch_active = True  # Default to safe state
                self._peak_equity = 0.0
                self._order_timestamps = []
                self._save_state()  # Save the safe-default state
                print(f"[EXEC_STATE] WARNING: Corrupt state file detected. Backed up to {corrupt_backup}")
                print(f"[EXEC_STATE] Kill switch defaulted to ACTIVE for safety. Investigate and reset.")
                print(f"[EXEC_STATE] Error: {e}")

    def _save_state(self):
        """Persist state to disk atomically."""
        os.makedirs(os.path.dirname(self.state_file) or ".", exist_ok=True)
        data = {
            "peak_equity": self._peak_equity,
            "order_timestamps": self._order_timestamps[-100:],  # Keep last 100
            "kill_switch_active": self._kill_switch_active,
            "active_orders": [o.to_dict() for o in self._active_orders.values()],
            "persisted_positions": getattr(self, '_persisted_positions', []),
            "last_updated": time.time(),
        }
        tmp_file = self.state_file + ".tmp"
        try:
            with open(tmp_file, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_file, self.state_file)  # Atomic on most OS
        except (OSError, PermissionError):
            # Windows: file may be locked by another process
            # Fall back to direct write (non-atomic but functional)
            try:
                with open(self.state_file, "w") as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                print(f"[EXEC_STATE] Failed to persist state: {e}")

    # ─── Kill Switch (Persistent) ────────────────────────────────────────

    @property
    def kill_switch_active(self) -> bool:
        return self._kill_switch_active

    def set_kill_switch(self, active: bool) -> bool:
        """Set kill switch and persist to disk."""
        with self._lock:
            self._kill_switch_active = active
            self._save_state()
        return self._kill_switch_active

    # ─── Peak Equity (Persistent) ────────────────────────────────────────

    @property
    def peak_equity(self) -> float:
        return self._peak_equity

    def update_peak_equity(self, current_equity: float) -> float:
        """Update peak equity and persist. Returns current drawdown %."""
        with self._lock:
            if current_equity > self._peak_equity:
                self._peak_equity = current_equity
            dd_pct = 0.0
            if self._peak_equity > 0:
                dd_pct = max(0.0, (self._peak_equity - current_equity) / self._peak_equity * 100.0)
            self._save_state()
        return dd_pct

    # ─── Position Persistence (P0-3) ─────────────────────────────────────

    def persist_positions(self, positions: List[Dict]):
        """Persist open positions to disk for crash recovery."""
        with self._lock:
            self._persisted_positions = positions
            self._save_state()

    def get_persisted_positions(self) -> List[Dict]:
        """Get positions from last persist (survives restart)."""
        return getattr(self, '_persisted_positions', [])

    def clear_persisted_positions(self):
        """Clear persisted positions after successful reconciliation."""
        with self._lock:
            self._persisted_positions = []
            self._save_state()

    # ─── Order Rate Limiter (Persistent) ─────────────────────────────────

    def record_order(self):
        """Record an order timestamp and persist."""
        with self._lock:
            self._order_timestamps.append(time.time())
            # Prune old timestamps (keep last 5 minutes)
            cutoff = time.time() - 300
            self._order_timestamps = [t for t in self._order_timestamps if t > cutoff]
            self._save_state()

    def get_order_count(self, window_seconds: float = 60.0) -> int:
        """Get order count in window (from persistent state)."""
        cutoff = time.time() - window_seconds
        return sum(1 for t in self._order_timestamps if t > cutoff)

    # ─── Order Lifecycle Management ──────────────────────────────────────

    def create_order(self, order_id: str, symbol: str, action: str, volume: float) -> OrderLifecycle:
        """INTENDED → create lifecycle entry."""
        with self._lock:
            order = OrderLifecycle(
                order_id=order_id,
                symbol=symbol,
                action=action,
                intended_volume=volume,
                state=OrderState.INTENDED,
            )
            self._active_orders[order_id] = order
            self._save_state()
        return order

    def dispatch_order(self, order_id: str) -> OrderLifecycle:
        """INTENDED → DISPATCHED."""
        with self._lock:
            order = self._active_orders.get(order_id)
            if order and order.state == OrderState.INTENDED:
                order.state = OrderState.DISPATCHED
                order.updated_at = time.time()
                self._save_state()
        return order

    def acknowledge_order(self, order_id: str, retcode: int, comment: str = "") -> OrderLifecycle:
        """DISPATCHED → ACKNOWLEDGED (broker responded)."""
        with self._lock:
            order = self._active_orders.get(order_id)
            if order:
                order.state = OrderState.ACKNOWLEDGED
                order.broker_retcode = retcode
                order.broker_comment = comment
                order.updated_at = time.time()
                self._save_state()
        return order

    def fill_order(self, order_id: str, filled_volume: float, fill_price: float,
                   position_ticket: Optional[int] = None) -> OrderLifecycle:
        """ACKNOWLEDGED → FILLED or PARTIAL."""
        with self._lock:
            order = self._active_orders.get(order_id)
            if order:
                order.filled_volume = filled_volume
                order.fill_price = fill_price
                order.position_ticket = position_ticket
                if filled_volume >= order.intended_volume * 0.99:
                    order.state = OrderState.FILLED
                elif filled_volume > 0:
                    order.state = OrderState.PARTIAL
                else:
                    order.state = OrderState.REJECTED
                order.updated_at = time.time()
                self._save_state()
        return order

    def reconcile_order(self, order_id: str, actual_positions: List[Dict[str, Any]]) -> OrderLifecycle:
        """FILLED/PARTIAL → RECONCILED (verified against broker positions)."""
        with self._lock:
            order = self._active_orders.get(order_id)
            if order:
                order.reconciliation_attempts += 1
                # Find matching position
                matched = False
                for pos in actual_positions:
                    if (pos.get("symbol") == order.symbol and
                        pos.get("type", "").upper() == order.action.upper()):
                        matched = True
                        order.position_ticket = pos.get("ticket")
                        if order.state == OrderState.PARTIAL:
                            order.filled_volume = pos.get("volume", order.filled_volume)
                        break

                if matched:
                    order.state = OrderState.RECONCILED  # Only reconcile when broker position VERIFIED
                elif order.state == OrderState.FILLED and not matched:
                    # FILLED but position not found in broker — this is DANGEROUS
                    order.state = OrderState.AMBIGUOUS  # P0-3: Never assume FILLED = RECONCILED
                    order.error_message = f"Order FILLED but position NOT found in broker after {order.reconciliation_attempts} attempts"
                elif order.state == OrderState.PARTIAL and not matched:
                    # Partial fill not confirmed — stay in PARTIAL for retry
                    pass
                elif order.state == OrderState.AMBIGUOUS:
                    # Cannot reconcile — mark for emergency policy
                    pass

                order.updated_at = time.time()
                self._save_state()
        return order

    def finalize_order(self, order_id: str) -> OrderLifecycle:
        """RECONCILED → FINALIZED (closed/confirmed)."""
        with self._lock:
            order = self._active_orders.get(order_id)
            if order:
                order.state = OrderState.FINALIZED
                order.updated_at = time.time()
                self._finalized_orders.append(order)
                del self._active_orders[order_id]
                self._save_state()
        return order

    def mark_ambiguous(self, order_id: str, error: str = "") -> OrderLifecycle:
        """Mark order as ambiguous (broker returned None or unknown state)."""
        with self._lock:
            order = self._active_orders.get(order_id)
            if order:
                order.state = OrderState.AMBIGUOUS
                order.error_message = error
                order.updated_at = time.time()
                self._save_state()
        return order

    def mark_failed(self, order_id: str, error: str = "") -> OrderLifecycle:
        """Mark order as failed."""
        with self._lock:
            order = self._active_orders.get(order_id)
            if order:
                order.state = OrderState.FAILED
                order.error_message = error
                order.updated_at = time.time()
                self._active_orders.pop(order_id, None)
                self._save_state()
        return order

    def get_active_orders(self) -> List[OrderLifecycle]:
        """Get all non-finalized orders."""
        return list(self._active_orders.values())

    def get_stale_orders(self, max_age_seconds: float = 300) -> List[OrderLifecycle]:
        """Get orders older than max_age that haven't been finalized."""
        cutoff = time.time() - max_age_seconds
        return [o for o in self._active_orders.values()
                if o.created_at < cutoff and o.state not in (OrderState.FINALIZED, OrderState.FAILED)]

    def cleanup(self):
        """Remove old finalized orders (keep last 100)."""
        self._finalized_orders = self._finalized_orders[-100:]
        self._save_state()
