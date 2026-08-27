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
        """
        # 1. Emergency Kill Switch Check (ACC-401)
        if emergency_signal or self.limits.kill_switch_active:
            return SafetyDecision(
                allowed=False,
                action="EMERGENCY_FLAT",
                clamped_size=0.0,
                reason="Emergency kill switch triggered (ACC-401)",
            )

        # 2. Maximum Drawdown Check (ACC-402)
        if current_drawdown >= self.limits.max_drawdown_pct:
            return SafetyDecision(
                allowed=False,
                action="ABSTAIN",
                clamped_size=0.0,
                reason=f"Max drawdown threshold exceeded: {current_drawdown:.4f} >= {self.limits.max_drawdown_pct:.4f} (ACC-402)",
            )

        # 3. Volatility Cutoff Check (ACC-403)
        if current_volatility >= self.limits.volatility_cutoff:
            return SafetyDecision(
                allowed=False,
                action="ABSTAIN",
                clamped_size=0.0,
                reason=f"Market volatility cutoff breached: {current_volatility:.4f} >= {self.limits.volatility_cutoff:.4f} (ACC-403)",
            )

        # 4. Order Rate Limit Check (ACC-404)
        if recent_order_count >= self.limits.max_order_rate_per_min:
            return SafetyDecision(
                allowed=False,
                action="ABSTAIN",
                clamped_size=0.0,
                reason=f"Order frequency rate limit reached: {recent_order_count} >= {self.limits.max_order_rate_per_min} (ACC-404)",
            )

        # 5. Position Sizing Clamping (ACC-405)
        raw_size = float(intended_action.get("size", 1.0))
        clamped_size = min(max(0.0, raw_size), self.limits.max_position_size)

        return SafetyDecision(
            allowed=True,
            action="EXECUTE",
            clamped_size=clamped_size,
            reason="Action passed Capital Safety Kernel verification",
        )
