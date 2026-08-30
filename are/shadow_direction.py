"""
AHFMES-ARE — Shadow Direction System (ported from AHFMES-CHATGPT-DEEP G2.2)

Per-habitat observer with state machine, evidence scoring, hysteresis.
Observer ONLY — never mutates the decision path.
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class DirectionStatus(Enum):
    UNSTABLE = "UNSTABLE"
    LEAN_BUY = "LEAN_BUY"
    LEAN_SELL = "LEAN_SELL"
    CONFIRMED_BUY = "CONFIRMED_BUY"
    CONFIRMED_SELL = "CONFIRMED_SELL"
    DEGRADED = "DEGRADED"


@dataclass
class HabitatShadowState:
    """Per-habitat shadow direction tracking."""
    buy_wins: int = 0
    buy_losses: int = 0
    sell_wins: int = 0
    sell_losses: int = 0
    buy_r: float = 0.0
    sell_r: float = 0.0
    recent_outcomes: list = field(default_factory=list)
    status: DirectionStatus = DirectionStatus.UNSTABLE
    status_enter_tick: int = 0
    last_transition_tick: int = 0
    transition_history: list = field(default_factory=list)

    @property
    def n_buy(self) -> int:
        return self.buy_wins + self.buy_losses

    @property
    def n_sell(self) -> int:
        return self.sell_wins + self.sell_losses

    @property
    def n_total(self) -> int:
        return self.n_buy + self.n_sell

    @property
    def buy_wr(self) -> float:
        return (self.buy_wins / self.n_buy * 100) if self.n_buy > 0 else 0.0

    @property
    def sell_wr(self) -> float:
        return (self.sell_wins / self.n_sell * 100) if self.n_sell > 0 else 0.0

    @property
    def delta_wr(self) -> float:
        return self.sell_wr - self.buy_wr

    @property
    def delta_r(self) -> float:
        buy_exp = (self.buy_r / self.n_buy) if self.n_buy > 0 else 0.0
        sell_exp = (self.sell_r / self.n_sell) if self.n_sell > 0 else 0.0
        return sell_exp - buy_exp

    @property
    def entropy(self) -> float:
        total = self.n_total
        if total < 10:
            return 1.0
        if total == 0:
            return 0.0
        p_buy = self.n_buy / total
        p_sell = self.n_sell / total
        if p_buy == 0 or p_sell == 0:
            return 0.0
        return -(p_buy * math.log2(p_buy) + p_sell * math.log2(p_sell))

    @property
    def evidence_score(self) -> float:
        total = min(self.n_total, 30)
        sample_component = total / 30.0
        agreement_component = 1.0 - self.entropy
        abs_delta = abs(self.delta_r)
        profitability_component = 1.0 / (1.0 + math.exp(-20 * (abs_delta - 0.15)))
        evidence = sample_component * agreement_component * profitability_component
        return round(min(1.0, max(0.0, evidence)), 3)

    @property
    def confidence(self) -> float:
        return round(self.evidence_score * 100, 1)

    @property
    def recommendation(self) -> str:
        if self.status in (DirectionStatus.UNSTABLE, DirectionStatus.DEGRADED):
            return "NONE"
        if self.status in (DirectionStatus.LEAN_SELL, DirectionStatus.CONFIRMED_SELL):
            return "SELL"
        if self.status in (DirectionStatus.LEAN_BUY, DirectionStatus.CONFIRMED_BUY):
            return "BUY"
        return "NONE"

    @property
    def recent_net_r(self) -> float:
        if not self.recent_outcomes:
            return 0.0
        return sum(r for _, r in self.recent_outcomes)


class ShadowDirectionSystem:
    """Per-habitat shadow direction observer with hysteresis state machine."""

    ENTER_LEAN_DELTA = 15
    EXIT_LEAN_DELTA = 8
    ENTER_CONFIRMED_DELTA = 20
    EXIT_CONFIRMED_DELTA = 12
    MIN_SAMPLE_LEAN = 10
    MIN_SAMPLE_CONFIRMED = 15
    MAX_ENTROPY_CONFIRMED = 0.85
    DEGRADED_NET_R_THRESHOLD = 0.0
    RECENT_WINDOW = 10

    def __init__(self):
        self._habitats: Dict[str, HabitatShadowState] = {}

    def _key(self, habitat_key) -> str:
        if isinstance(habitat_key, tuple):
            return "[" + ", ".join(str(x) for x in habitat_key) + "]"
        return str(habitat_key)

    def _get_or_create(self, habitat_key) -> HabitatShadowState:
        key = self._key(habitat_key)
        if key not in self._habitats:
            self._habitats[key] = HabitatShadowState()
        return self._habitats[key]

    def observe(self, habitat_key, shadow_side: str, shadow_r: float, tick_count: int = 0):
        """Observe a completed shadow counterfactual outcome."""
        state = self._get_or_create(habitat_key)
        is_win = shadow_r > 0

        if shadow_side == "buy":
            if is_win:
                state.buy_wins += 1
            else:
                state.buy_losses += 1
            state.buy_r += shadow_r
        elif shadow_side == "sell":
            if is_win:
                state.sell_wins += 1
            else:
                state.sell_losses += 1
            state.sell_r += shadow_r

        state.recent_outcomes.append((shadow_side, shadow_r))
        if len(state.recent_outcomes) > self.RECENT_WINDOW:
            state.recent_outcomes = state.recent_outcomes[-self.RECENT_WINDOW:]

        self._update_status(state, tick_count)

    def _update_status(self, state: HabitatShadowState, tick_count: int = 0):
        """Update status with hysteresis bands."""
        abs_delta = abs(state.delta_wr)
        n = state.n_total
        current = state.status
        new_status = current

        if current in (DirectionStatus.CONFIRMED_BUY, DirectionStatus.CONFIRMED_SELL):
            if state.recent_net_r < self.DEGRADED_NET_R_THRESHOLD and n >= self.RECENT_WINDOW:
                new_status = DirectionStatus.DEGRADED
        elif current == DirectionStatus.UNSTABLE:
            if n >= self.MIN_SAMPLE_LEAN and abs_delta >= self.ENTER_LEAN_DELTA:
                new_status = DirectionStatus.LEAN_SELL if state.delta_wr > 0 else DirectionStatus.LEAN_BUY
        elif current in (DirectionStatus.LEAN_BUY, DirectionStatus.LEAN_SELL):
            if (n >= self.MIN_SAMPLE_CONFIRMED and abs_delta >= self.ENTER_CONFIRMED_DELTA
                    and state.entropy < self.MAX_ENTROPY_CONFIRMED):
                new_status = DirectionStatus.CONFIRMED_SELL if state.delta_wr > 0 else DirectionStatus.CONFIRMED_BUY
            elif abs_delta < self.EXIT_LEAN_DELTA:
                new_status = DirectionStatus.UNSTABLE
        elif current in (DirectionStatus.CONFIRMED_BUY, DirectionStatus.CONFIRMED_SELL):
            if abs_delta < self.EXIT_CONFIRMED_DELTA:
                new_status = DirectionStatus.LEAN_SELL if state.delta_wr > 0 else DirectionStatus.LEAN_BUY
        elif current == DirectionStatus.DEGRADED:
            if state.recent_net_r > 0 and abs_delta >= self.ENTER_LEAN_DELTA:
                new_status = DirectionStatus.LEAN_SELL if state.delta_wr > 0 else DirectionStatus.LEAN_BUY

        if new_status != current:
            state.transition_history.append((tick_count, current.value, new_status.value))
            if len(state.transition_history) > 20:
                state.transition_history = state.transition_history[-20:]
            state.status_enter_tick = tick_count
            state.last_transition_tick = tick_count

        state.status = new_status

    def get_state(self, habitat_key) -> Optional[HabitatShadowState]:
        key = self._key(habitat_key)
        return self._habitats.get(key)

    def get_summary(self, habitat_key) -> dict:
        state = self.get_state(habitat_key)
        if state is None:
            return {
                "shadow_status": "NO_DATA", "shadow_confidence": 0.0,
                "shadow_buy_wr": 0.0, "shadow_sell_wr": 0.0,
                "shadow_delta_wr": 0.0, "shadow_n": 0,
                "shadow_recommendation": "NONE",
            }
        return {
            "shadow_status": state.status.value,
            "shadow_confidence": state.confidence,
            "shadow_buy_wr": round(state.buy_wr, 1),
            "shadow_sell_wr": round(state.sell_wr, 1),
            "shadow_delta_wr": round(state.delta_wr, 1),
            "shadow_delta_r": round(state.delta_r, 3),
            "shadow_entropy": round(state.entropy, 3),
            "shadow_n": state.n_total,
            "shadow_recommendation": state.recommendation,
        }
