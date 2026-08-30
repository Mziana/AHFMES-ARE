"""
AHFMES-ARE — Unified Trading Engine

Bridges AHFMES trading modules (habitat, confidence, opportunity, direction,
shadow, breaker, health) into ARE governance framework (CSK, EventStore,
Champion Registry, Search Tree).

This is the heart of the merged system:
- AHFMES provides the trading intelligence (perception, decision, execution)
- ARE provides the safety & governance layer (CSK veto, audit trail, champion management)

Architecture:
    Tick → Habitat Classification → Confidence Engine → Opportunity Engine
    → Direction Discovery → Trade Health → CSK Veto → EventStore

Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# === AHFMES Trading Modules ===
from are.habitat_schema import (
    HabitatSchema, Session, Regime, ATRState, SpreadState, HabitatStateLevel,
)
from are.habitat_perception import (
    classify_session, classify_regime, classify_atr, classify_spread,
    apply_atr_hysteresis, build_habitat_key, build_reason_chain,
)
from are.habitat_memory import HabitatMemory
from are.habitat_state import HabitatStateAssessor, HabitatStateResult
from are.habitat_confidence import HabitatConfidenceAssessor, HabitatConfidenceResult
from are.confidence_engine import ConfidenceEngine, ConfidenceResult
from are.performance_tracker import PerformanceTracker
from are.opportunity_engine import OpportunityEngine, OpportunityResult
from are.direction_discovery import DirectionDiscovery, DirectionResult
from are.shadow_direction import ShadowDirectionSystem
from are.breaker import CircuitBreaker, CircuitBreakerResult
from are.trade_health import TradeHealthObserver, HealthResult

# === ARE Governance Modules ===
from are.safety import CapitalSafetyKernel, SafetyDecision
from are.storage import EventStore
from are.champion import ChampionRegistry


@dataclass(frozen=True)
class TickResult:
    """Complete result of processing one market tick through the unified engine."""
    timestamp: float
    habitat_key: tuple
    session: str
    regime: str
    atr_state: str
    spread_state: str
    habitat_changed: bool
    state_level: str
    confidence: float
    tier_ceiling: int
    opportunity_score: float
    should_enter: bool
    direction: str
    direction_reason: str
    shadow_status: str
    shadow_confidence: float
    cb_trading_allowed: bool
    cb_halt_reason: Optional[str]
    cb_dd_pct: Optional[float]
    csk_allowed: bool
    csk_action: str
    csk_reason: str
    final_action: str
    tick_count: int
    eval_count: int
    habitat_observations: int
    reason_chain: str


class ARETradingEngine:
    """
    Unified trading engine combining AHFMES intelligence with ARE governance.

    Usage:
        engine = ARETradingEngine(event_store=event_store, champion_registry=champion)
        result = engine.process_tick(
            price=3245.50, bid=3245.30, ask=3245.70, spread=4.0,
            timestamp=time.time(),
            rates=[...],  # OHLC bars for ADX calculation
            equity=10000.0,
        )
    """

    ADX_BARS = 30

    def __init__(
        self,
        event_store: EventStore,
        champion_registry: ChampionRegistry,
        safety_kernel: Optional[CapitalSafetyKernel] = None,
        max_dd_pct: float = 15.0,
        opportunity_threshold: float = 60.0,
        memory_path: Optional[str] = None,
    ):
        # Governance
        self.event_store = event_store
        self.champion_registry = champion_registry
        self.safety_kernel = safety_kernel or CapitalSafetyKernel()

        # P0-02: Check persistent kill switch on startup
        from are.execution_state import ExecutionStateMachine
        self._exec_state = ExecutionStateMachine()
        if self._exec_state.kill_switch_active:
            from are.safety import SafetyLimits
            self.safety_kernel = CapitalSafetyKernel(SafetyLimits(kill_switch_active=True))

        # AHFMES Core
        self.schema = HabitatSchema()
        self.state_assessor = HabitatStateAssessor(schema=self.schema)
        self.confidence_assessor = HabitatConfidenceAssessor(schema=self.schema)
        self.confidence_engine = ConfidenceEngine()
        self.performance_tracker = PerformanceTracker()
        self.opportunity_engine = OpportunityEngine(threshold=opportunity_threshold)
        self.direction_discovery = DirectionDiscovery()
        self.shadow_direction = ShadowDirectionSystem()
        self.circuit_breaker = CircuitBreaker(max_dd_pct=max_dd_pct)
        self.trade_health = TradeHealthObserver()
        self.memory = HabitatMemory(persistence_path=memory_path)

        # State
        self._tick_count = 0
        self._eval_count = 0
        self._last_habitat_key: Optional[tuple] = None
        self._atr_stable: Optional[int] = None
        self._atr_candidate: Optional[int] = None
        self._atr_candidate_count: int = 0
        self._atr_flips_blocked: int = 0
        self._habitat_changes: int = 0
        self._habitat_tick_count: int = 0
        self.atr_history: List[float] = []
        self.spread_history: List[float] = []
        self.HISTORY_MAXLEN = 30

    def _calculate_adx(self, rates: List[Dict]) -> Dict[str, float]:
        """Calculate ADX proxy from OHLC bars. Simplified version."""
        if not rates or len(rates) < self.ADX_BARS:
            return {"adx": 25.0, "di_plus": 20.0, "di_minus": 20.0}

        # Simplified ADX: use last N bars
        recent = rates[-self.ADX_BARS:]
        tr_list = []
        plus_dm_list = []
        minus_dm_list = []

        for i in range(1, len(recent)):
            high = recent[i].get("high", 0)
            low = recent[i].get("low", 0)
            prev_high = recent[i-1].get("high", 0)
            prev_low = recent[i-1].get("low", 0)
            prev_close = recent[i-1].get("close", 0)

            # True Range
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_list.append(tr)

            # Directional Movement
            up_move = high - prev_high
            down_move = prev_low - low
            plus_dm_list.append(up_move if up_move > down_move and up_move > 0 else 0)
            minus_dm_list.append(down_move if down_move > up_move and down_move > 0 else 0)

        if not tr_list:
            return {"adx": 25.0, "di_plus": 20.0, "di_minus": 20.0}

        # Smoothed averages (Wilder's smoothing)
        atr = sum(tr_list) / len(tr_list)
        plus_dm = sum(plus_dm_list) / len(plus_dm_list)
        minus_dm = sum(minus_dm_list) / len(minus_dm_list)

        di_plus = (plus_dm / atr * 100) if atr > 0 else 0
        di_minus = (minus_dm / atr * 100) if atr > 0 else 0

        # DX and ADX approximation
        dx_sum = di_plus + di_minus
        if dx_sum > 0:
            dx = abs(di_plus - di_minus) / dx_sum * 100
        else:
            dx = 0

        adx = dx  # Simplified: single-period ADX ≈ DX

        return {"adx": adx, "di_plus": di_plus, "di_minus": di_minus}

    def _calculate_market_scores(
        self, adx: float, atr: float, spread: float, session: Session
    ) -> Dict[str, float]:
        """Calculate 4D market quality scores (0-100 each)."""
        # Trend strength: ADX 25-40 = good, too high or low = bad
        trend = max(0, min(100, 100 - abs(adx - 32) * 3))

        # Volatility quality: moderate ATR = good
        vol_hist = list(self.atr_history)
        if vol_hist:
            median_atr = sorted(vol_hist)[len(vol_hist) // 2]
            if median_atr > 0:
                vol_ratio = atr / median_atr
                vol = max(0, min(100, 100 - abs(vol_ratio - 1.0) * 100))
            else:
                vol = 50.0
        else:
            vol = 50.0

        # Session quality: London > NY > Asia
        session_scores = {Session.LONDON: 80.0, Session.NEWYORK: 65.0, Session.ASIA: 50.0}
        sess = session_scores.get(session, 50.0)

        # Spread quality: lower spread = better
        spread_hist = list(self.spread_history)
        if spread_hist:
            median_spread = sorted(spread_hist)[len(spread_hist) // 2]
            if median_spread > 0:
                spread_ratio = spread / median_spread
                spread_q = max(0, min(100, 100 - abs(spread_ratio - 1.0) * 100))
            else:
                spread_q = 70.0
        else:
            spread_q = 70.0

        return {
            "trend": trend,
            "volatility": vol,
            "session": sess,
            "spread": spread_q,
        }

    def process_tick(
        self,
        price: float,
        bid: float,
        ask: float,
        spread: float,
        timestamp: float,
        rates: Optional[List[Dict]] = None,
        equity: float = 10000.0,
        emergency_signal: bool = False,
    ) -> TickResult:
        """
        Process one market tick through the full AHFMES → ARE pipeline.
        """
        self._tick_count += 1
        tick_count = self._tick_count

        # --- 1. Circuit Breaker (equity-based) ---
        cb_result = self.circuit_breaker.update(equity=equity)

        # --- 2. Habitat Classification ---
        dt = datetime.utcfromtimestamp(timestamp)
        hour_utc = dt.hour
        session = classify_session(hour_utc)

        adx_data = self._calculate_adx(rates or [])
        adx = adx_data["adx"]
        di_plus = adx_data["di_plus"]
        di_minus = adx_data["di_minus"]

        atr = 0.0
        if rates and len(rates) >= 2:
            atr = rates[-1].get("high", 0) - rates[-1].get("low", 0)

        if spread > 0:
            self.spread_history.append(spread)
            if len(self.spread_history) > self.HISTORY_MAXLEN:
                self.spread_history.pop(0)
        if atr > 0:
            self.atr_history.append(atr)
            if len(self.atr_history) > self.HISTORY_MAXLEN:
                self.atr_history.pop(0)

        regime = classify_regime(adx, di_plus, di_minus)
        atr_raw = classify_atr(atr, self.atr_history, self.schema)
        atr_filtered, new_stable, new_candidate, new_count, flips = apply_atr_hysteresis(
            atr_raw, self._atr_stable, self._atr_candidate, self._atr_candidate_count,
        )
        self._atr_stable = new_stable
        self._atr_candidate = new_candidate
        self._atr_candidate_count = new_count
        self._atr_flips_blocked += flips
        spread_state = classify_spread(spread, self.spread_history, self.schema)

        habitat_key = build_habitat_key(session, regime, atr_filtered, spread_state)
        habitat_changed = habitat_key != self._last_habitat_key
        if habitat_changed:
            self._last_habitat_key = habitat_key
            self._habitat_changes += 1
            self._habitat_tick_count = 0
        self._habitat_tick_count += 1

        reason_chain = build_reason_chain(session, regime, atr_filtered, spread_state)

        # --- 3. Memory & State Assessment ---
        self.memory.record_observation(
            habitat=habitat_key,
            session=session.name,
            regime=regime.name,
            atr_state=atr_filtered.name,
            spread_state=spread_state.name,
        )
        memory_data = self.memory.get_memory(habitat_key)
        state_result = self.state_assessor.assess(habitat_key, self.memory)

        # --- 4. Confidence Engine ---
        market_scores = self._calculate_market_scores(adx, atr, spread, session)
        perf_score = self.performance_tracker.compute(memory_data)

        confidence_result = self.confidence_engine.compute(
            state_level=state_result.level,
            perf_score=perf_score,
            trend_strength=market_scores["trend"],
            volatility_quality=market_scores["volatility"],
            session_quality=market_scores["session"],
            spread_quality=market_scores["spread"],
            total_evaluations=memory_data.get("total_evaluations", 0),
        )

        # --- 5. Opportunity Engine ---
        opp_result = self.opportunity_engine.score(
            confidence=confidence_result.confidence,
            tier=confidence_result.tier_ceiling,
            habitat_tick_count=self._habitat_tick_count,
        )

        # --- 6. Direction Discovery ---
        direction_result = self.direction_discovery.discover(memory_data)

        # --- 7. Shadow Direction Summary ---
        shadow_summary = self.shadow_direction.get_summary(habitat_key)

        # --- 8. CSK Veto Gate ---
        risk_state = {
            "drawdown": (cb_result.current_dd_pct or 0.0) / 100.0,
            "volatility": 1.0,  # Would need real vol calculation
            "order_count": 0,   # Would need rate tracking
            "emergency_signal": emergency_signal,
        }

        # Determine intended action
        if not cb_result.trading_allowed:
            intended_action = {"action": "ABSTAIN", "size": 0.0, "is_ambiguous": False}
        elif not opp_result.should_enter:
            intended_action = {"action": "HOLD", "size": 0.0, "is_ambiguous": False}
        else:
            intended_action = {
                "action": direction_result.selected_direction.upper(),
                "size": 1.0,
                "price": price,
                "is_ambiguous": False,
            }

        safety_decision = self.safety_kernel.evaluate_action(
            intended_action=intended_action,
            current_drawdown=risk_state,
        )

        # --- 9. Final Action ---
        if safety_decision.action == "EMERGENCY_FLAT":
            final_action = "EMERGENCY_FLAT"
        elif not safety_decision.allowed or safety_decision.action == "ABSTAIN":
            final_action = "ABSTAIN"
        elif not cb_result.trading_allowed:
            final_action = "CIRCUIT_BREAKER_HALT"
        elif opp_result.should_enter:
            final_action = direction_result.selected_direction.upper()
        else:
            final_action = "HOLD"

        # --- 10. Record to EventStore ---
        self._record_signal(
            tick_count=tick_count,
            habitat_key=habitat_key,
            final_action=final_action,
            confidence=confidence_result,
            opportunity=opp_result,
            safety=safety_decision,
            cb=cb_result,
            shadow=shadow_summary,
            timestamp=timestamp,
        )

        return TickResult(
            timestamp=timestamp,
            habitat_key=habitat_key,
            session=session.name,
            regime=regime.name,
            atr_state=atr_filtered.name,
            spread_state=spread_state.name,
            habitat_changed=habitat_changed,
            state_level=state_result.level.name,
            confidence=confidence_result.confidence,
            tier_ceiling=confidence_result.tier_ceiling,
            opportunity_score=opp_result.score,
            should_enter=opp_result.should_enter,
            direction=direction_result.selected_direction,
            direction_reason=direction_result.reason,
            shadow_status=shadow_summary.get("shadow_status", "NO_DATA"),
            shadow_confidence=shadow_summary.get("shadow_confidence", 0.0),
            cb_trading_allowed=cb_result.trading_allowed,
            cb_halt_reason=cb_result.halt_reason,
            cb_dd_pct=cb_result.current_dd_pct,
            csk_allowed=safety_decision.allowed,
            csk_action=safety_decision.action,
            csk_reason=safety_decision.reason,
            final_action=final_action,
            tick_count=tick_count,
            eval_count=self._eval_count,
            habitat_observations=memory_data.get("real_signals_seen", 0),
            reason_chain=reason_chain,
        )

    def _record_signal(
        self,
        tick_count: int,
        habitat_key: tuple,
        final_action: str,
        confidence: ConfidenceResult,
        opportunity: OpportunityResult,
        safety: SafetyDecision,
        cb: CircuitBreakerResult,
        shadow: dict,
        timestamp: float,
    ):
        """Record operational signal to EventStore."""
        signal_id = f"SIG_{int(timestamp)}_{tick_count}"
        payload = {
            "signal_id": signal_id,
            "tick_count": tick_count,
            "habitat_key": list(habitat_key),
            "final_action": final_action,
            "confidence": {
                "score": confidence.confidence,
                "tier_ceiling": confidence.tier_ceiling,
                "market_score": confidence.market_score,
                "perf_score": confidence.perf_score,
            },
            "opportunity": {
                "score": opportunity.score,
                "threshold": opportunity.threshold,
                "should_enter": opportunity.should_enter,
            },
            "safety": {
                "allowed": safety.allowed,
                "action": safety.action,
                "reason": safety.reason,
                "decision_hash": safety.decision_hash,
            },
            "circuit_breaker": {
                "trading_allowed": cb.trading_allowed,
                "halt_code": cb.halt_code,
                "dd_pct": cb.current_dd_pct,
            },
            "shadow": shadow,
            "timestamp": timestamp,
        }

        event_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        stream_id = "operational_signals"

        try:
            head = self.event_store.get_head(stream_id)
            expected_rev = 0 if head is None else head[0]
            prev_hash = "0" * 64 if head is None else head[1]
            self.event_store.append_event(
                stream_id=stream_id,
                event_data=event_bytes,
                expected_revision=expected_rev,
                prev_event_hash=prev_hash,
            )
        except Exception:
            pass  # Non-fatal: signal recording failure doesn't halt trading

    def get_engine_status(self) -> Dict[str, Any]:
        """Get comprehensive engine status for UI/API."""
        # Habitat breakdown
        habitat_stats = {}
        for key_str, data in self.memory.data.items():
            habitat_stats[key_str] = {
                "real_trades": data.get("real_signals_seen", 0),
                "shadow_trades": data.get("shadow_signals_seen", 0),
                "real_wr": (
                    data.get("real_won", 0) / max(1, data.get("real_signals_seen", 1)) * 100
                ),
            }

        # Circuit breaker status
        cb_status = {
            "trading_allowed": self.circuit_breaker.session_peak_equity is None or not self.circuit_breaker._halted,
            "peak_equity": self.circuit_breaker.session_peak_equity,
            "halt_code": self.circuit_breaker._halt_code,
        }

        # Champion info
        active_champ = self.champion_registry.get_active_champion()
        champion_info = None
        if active_champ:
            champion_info = {
                "champion_id": active_champ.champion_id,
                "candidate_id": active_champ.candidate_id,
                "status": active_champ.status,
                "activated_at": active_champ.activated_at,
            }

        return {
            "tick_count": self._tick_count,
            "eval_count": self._eval_count,
            "habitat_changes": self._habitat_changes,
            "atr_flips_blocked": self._atr_flips_blocked,
            "total_habitats_seen": len(self.memory.data),
            "habitat_stats": habitat_stats,
            "circuit_breaker": cb_status,
            "champion": champion_info,
            "last_habitat_key": list(self._last_habitat_key) if self._last_habitat_key else None,
            "opportunity_threshold": self.opportunity_engine._threshold,
            "csk_limits": {
                "max_drawdown_pct": self.safety_kernel.limits.max_drawdown_pct,
                "volatility_cutoff": self.safety_kernel.limits.volatility_cutoff,
                "max_order_rate_per_min": self.safety_kernel.limits.max_order_rate_per_min,
                "max_position_size": self.safety_kernel.limits.max_position_size,
                "kill_switch_active": self.safety_kernel.limits.kill_switch_active,
            },
        }
