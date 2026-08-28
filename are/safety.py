"""
AHFMES ARE-4 — Capital Safety Kernel (Slice-1 Part A)

Implements:
- SafetyLimits: hard boundary parameters for risk and exposure.
- SafetyDecision: content-addressed, cryptographic safety decision container.
- CapitalSafetyKernel: independent, non-bypassable veto gate enforcing kill-switch (ACC-401),
  max drawdown (ACC-402), volatility cutoff (ACC-403), order rate limits (ACC-404),
  and position size clamping (ACC-405).

Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class SafetyLimits:
    max_position_size: float = 1.0
    max_drawdown_pct: float = 0.15
    volatility_cutoff: float = 2.5
    max_order_rate_per_min: int = 10
    kill_switch_active: bool = False


@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    action: str  # "EXECUTE" | "ABSTAIN" | "EMERGENCY_FLAT"
    clamped_size: float
    reason: str
    decision_hash: str = ""

    def __post_init__(self):
        if not self.decision_hash:
            canonical_repr = {
                "allowed": self.allowed,
                "action": self.action,
                "clamped_size": self.clamped_size,
                "reason": self.reason,
            }
            raw = json.dumps(canonical_repr, sort_keys=True).encode("utf-8")
            digest = hashlib.sha256(raw).hexdigest()
            object.__setattr__(self, "decision_hash", digest)


class CapitalSafetyKernel:
    """
    Capital Safety Kernel (CSK) — hard risk firewall gating all operational actions.
    """

    def __init__(self, limits: Optional[SafetyLimits] = None):
        self.limits = limits if limits is not None else SafetyLimits()

    def evaluate_action(
        self,
        intended_action: Dict[str, Any],
        current_drawdown: float,
        current_volatility: float,
        recent_order_count: int,
        emergency_signal: bool = False,
    ) -> SafetyDecision:
        """
        Evaluates proposed action against absolute safety limits (ACC-401..ACC-405).
        Fails-closed on any corrupt, ambiguous, NaN, Inf, or out-of-bound inputs.
        """
        # 1. Emergency Kill Switch Check (ACC-401)
        if emergency_signal or self.limits.kill_switch_active:
            return SafetyDecision(
                allowed=False,
                action="EMERGENCY_FLAT",
                clamped_size=0.0,
                reason="Emergency kill switch triggered (ACC-401)",
            )

        # 2. Input Integrity & Corrupt / Ambiguous Data Fail-Closed Check
        if not isinstance(intended_action, dict) or intended_action.get("is_ambiguous", False) or intended_action.get("is_corrupt", False):
            return SafetyDecision(
                allowed=False,
                action="ABSTAIN",
                clamped_size=0.0,
                reason="Corrupt or ambiguous action payload received",
            )

        # Validate numeric health of drawdown and volatility metrics
        try:
            dd = float(current_drawdown)
            vol = float(current_volatility)
            orders = int(recent_order_count)
            if not math.isfinite(dd) or dd < 0.0 or not math.isfinite(vol) or vol < 0.0 or orders < 0:
                return SafetyDecision(
                    allowed=False,
                    action="ABSTAIN",
                    clamped_size=0.0,
                    reason="Corrupt or non-finite risk metrics (NaN/Inf/Negative detected)",
                )
        except (ValueError, TypeError):
            return SafetyDecision(
                allowed=False,
                action="ABSTAIN",
                clamped_size=0.0,
                reason="Invalid metric types for risk evaluation",
            )

        # Validate intended price and execution latency / slippage if provided
        price = intended_action.get("price")
        if price is not None:
            try:
                p = float(price)
                if not math.isfinite(p) or p <= 0.0 or p > 1e12:
                    return SafetyDecision(
                        allowed=False,
                        action="ABSTAIN",
                        clamped_size=0.0,
                        reason="Corrupt or non-finite market price in action payload",
                    )
            except (ValueError, TypeError):
                return SafetyDecision(
                    allowed=False,
                    action="ABSTAIN",
                    clamped_size=0.0,
                    reason="Invalid price type in action payload",
                )

        try:
            slippage_pips = float(intended_action.get("slippage_pips", 0.0))
            latency_ms = float(intended_action.get("latency_ms", 0.0))
            if not math.isfinite(slippage_pips) or not math.isfinite(latency_ms) or slippage_pips > 500.0 or latency_ms > 5000.0:
                return SafetyDecision(
                    allowed=False,
                    action="ABSTAIN",
                    clamped_size=0.0,
                    reason="Extreme slippage (>500 pips) or latency (>5000 ms) circuit breaker triggered",
                )
        except (ValueError, TypeError):
            return SafetyDecision(
                allowed=False,
                action="ABSTAIN",
                clamped_size=0.0,
                reason="Invalid slippage or latency metrics",
            )

        # 3. Maximum Drawdown Check (ACC-402)
        if dd >= self.limits.max_drawdown_pct:
            return SafetyDecision(
                allowed=False,
                action="ABSTAIN",
                clamped_size=0.0,
                reason=f"Max drawdown threshold exceeded: {dd:.4f} >= {self.limits.max_drawdown_pct:.4f} (ACC-402)",
            )

        # 4. Volatility Cutoff Check (ACC-403)
        if vol >= self.limits.volatility_cutoff:
            return SafetyDecision(
                allowed=False,
                action="ABSTAIN",
                clamped_size=0.0,
                reason=f"Market volatility cutoff breached: {vol:.4f} >= {self.limits.volatility_cutoff:.4f} (ACC-403)",
            )

        # 5. Order Rate Limit Check (ACC-404)
        if orders >= self.limits.max_order_rate_per_min:
            return SafetyDecision(
                allowed=False,
                action="ABSTAIN",
                clamped_size=0.0,
                reason=f"Order frequency rate limit reached: {orders} >= {self.limits.max_order_rate_per_min} (ACC-404)",
            )

        # 6. Position Sizing Clamping (ACC-405)
        try:
            raw_size = float(intended_action.get("size", 1.0))
            if not math.isfinite(raw_size) or raw_size < 0.0:
                return SafetyDecision(
                    allowed=False,
                    action="ABSTAIN",
                    clamped_size=0.0,
                    reason="Invalid or non-finite position size in action payload",
                )
            clamped_size = min(max(0.0, raw_size), self.limits.max_position_size)
        except (ValueError, TypeError):
            return SafetyDecision(
                allowed=False,
                action="ABSTAIN",
                clamped_size=0.0,
                reason="Invalid size type in action payload",
            )

        return SafetyDecision(
            allowed=True,
            action="EXECUTE",
            clamped_size=clamped_size,
            reason="Action passed Capital Safety Kernel verification",
        )
