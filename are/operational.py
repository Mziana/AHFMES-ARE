"""
AHFMES ARE-4 — Operational Brain & Fast Loop (Slice-1 Part B)

Implements:
- OperationalSignal: immutable, content-addressed fast-loop decision signal.
- OperationalBrain: fast execution loop processing live/simulated market ticks,
  validating Information-Time (ACC-406), querying active champion, passing through CSK (ACC-407),
  and recording operational signals to EventStore stream "operational_signals" (ACC-408).

Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from are.champion import ChampionRegistry
from are.habitat import HabitatAdapter
from are.safety import CapitalSafetyKernel, SafetyDecision
from are.storage import EventStore


@dataclass(frozen=True)
class OperationalSignal:
    signal_id: str
    symbol: str
    raw_decision: Dict[str, Any]
    safety_decision: SafetyDecision
    final_action: str
    timestamp: float
    signal_hash: str = ""

    def __post_init__(self):
        if not self.signal_hash:
            canonical_repr = {
                "signal_id": self.signal_id,
                "symbol": self.symbol,
                "raw_decision": self.raw_decision,
                "safety_decision_hash": self.safety_decision.decision_hash,
                "final_action": self.final_action,
                "timestamp": self.timestamp,
            }
            raw = json.dumps(canonical_repr, sort_keys=True).encode("utf-8")
            digest = hashlib.sha256(raw).hexdigest()
            object.__setattr__(self, "signal_hash", digest)


class OperationalBrain:
    """
    Fast-loop runtime engine driving model inference, risk gating, and signal emission.
    """

    STREAM_ID = "operational_signals"

    def __init__(
        self,
        champion_registry: ChampionRegistry,
        safety_kernel: CapitalSafetyKernel,
        habitat: HabitatAdapter,
        event_store: EventStore,
    ):
        self.champion_registry = champion_registry
        self.safety_kernel = safety_kernel
        self.habitat = habitat
        self.event_store = event_store

    def process_tick(
        self,
        symbol: str,
        timestamp: float,
        market_features: Dict[str, float],
        current_risk_state: Dict[str, float],
        as_of_cutoff: float,
        emergency_signal: bool = False,
    ) -> OperationalSignal:
        """
        Processes a discrete market tick through Information-Time barrier, Champion model, CSK,
        and records signal to EventStore (ACC-406..ACC-408).
        """
        ts = float(timestamp)
        cutoff = float(as_of_cutoff)

        # 1. Information-Time Barrier Validation (ACC-406)
        if ts > cutoff:
            raise ValueError(
                f"Information-time barrier violated: timestamp in future ({ts} > {cutoff}) (ACC-406)"
            )

        # 2. Ingest Environment Observation into Habitat
        obs = self.habitat.ingest_market_state(
            symbol=symbol,
            timestamp=ts,
            features=market_features,
            as_of_cutoff=cutoff,
        )

        # 3. Active Champion Evaluation
        active_champ = self.champion_registry.get_active_champion()
        if active_champ is None:
            raw_decision = {
                "action": "ABSTAIN",
                "size": 0.0,
                "reason": "No active champion deployed in registry",
                "regime": obs.regime,
            }
        else:
            # Deterministic champion decision logic based on observed regime
            if obs.regime in ("TRENDING_EXPANSION", "VOLATILITY_EXPANSION"):
                raw_decision = {
                    "action": "BUY",
                    "size": 1.0,
                    "regime": obs.regime,
                    "champion_id": active_champ.champion_id,
                }
            else:
                raw_decision = {
                    "action": "HOLD",
                    "size": 0.0,
                    "regime": obs.regime,
                    "champion_id": active_champ.champion_id,
                }

        # 4. Capital Safety Kernel Veto Evaluation (ACC-407)
        safety_decision = self.safety_kernel.evaluate_action(
            intended_action=raw_decision,
            current_drawdown=float(current_risk_state.get("drawdown", 0.0)),
            current_volatility=float(current_risk_state.get("volatility", 1.0)),
            recent_order_count=int(current_risk_state.get("order_count", 0)),
            emergency_signal=emergency_signal,
        )

        # 5. Final Action Determination
        if safety_decision.action == "EMERGENCY_FLAT":
            final_action = "EMERGENCY_FLAT"
        elif not safety_decision.allowed or safety_decision.action == "ABSTAIN":
            final_action = "ABSTAIN"
        else:
            final_action = raw_decision.get("action", "EXECUTE")

        signal_id = f"SIG_{symbol}_{int(ts)}"
        signal = OperationalSignal(
            signal_id=signal_id,
            symbol=symbol,
            raw_decision=raw_decision,
            safety_decision=safety_decision,
            final_action=final_action,
            timestamp=ts,
        )

        # 6. Record to EventStore Stream "operational_signals" (ACC-408)
        event_payload = {
            "signal_id": signal.signal_id,
            "symbol": signal.symbol,
            "raw_decision": signal.raw_decision,
            "safety_decision": {
                "allowed": safety_decision.allowed,
                "action": safety_decision.action,
                "clamped_size": safety_decision.clamped_size,
                "reason": safety_decision.reason,
                "decision_hash": safety_decision.decision_hash,
            },
            "final_action": signal.final_action,
            "timestamp": signal.timestamp,
            "signal_hash": signal.signal_hash,
        }
        event_bytes = json.dumps(event_payload, sort_keys=True).encode("utf-8")

        head = self.event_store.get_head(self.STREAM_ID)
        expected_rev = 0 if head is None else head[0]
        prev_hash = "0" * 64 if head is None else head[1]

        self.event_store.append_event(
            stream_id=self.STREAM_ID,
            event_data=event_bytes,
            expected_revision=expected_rev,
            prev_event_hash=prev_hash,
        )

        return signal
