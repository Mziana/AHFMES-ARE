"""
AHFMES-ARE — Habitat Perception (ported from AHFMES-CHATGPT-DEEP M3)

Pure functions for market classification. History-aware ATR/Spread classification.
108 potential habitats: Session(3) × Regime(4) × ATR(3) × Spread(3).
"""

from typing import List, Optional

from are.habitat_schema import (
    Session, Regime, ATRState, SpreadState, HabitatSchema, HabitatKey,
)


def classify_session(hour_utc: int) -> Session:
    """Classify trading session by UTC hour."""
    if 0 <= hour_utc < 8:
        return Session.ASIA
    elif 8 <= hour_utc < 16:
        return Session.LONDON
    else:
        return Session.NEWYORK


def classify_regime(adx: float, di_plus: float, di_minus: float) -> Regime:
    """
    ADX-based regime classification.
    ADX < 18:  SIDEWAYS
    18-35:     RANGE
    >= 35:     TRENDING (directional) or VOLATILE (choppy)
    """
    if adx < 18.0:
        return Regime.SIDEWAYS
    elif adx < 35.0:
        return Regime.RANGE
    else:
        if di_plus > di_minus * 1.3 or di_minus > di_plus * 1.3:
            return Regime.TRENDING
        else:
            return Regime.VOLATILE


def classify_atr(
    atr_current: float,
    atr_history: List[float],
    schema: Optional[HabitatSchema],
) -> ATRState:
    """History-aware ATR classification. Uses rolling median if available."""
    if not atr_history or len(atr_history) < 5:
        if schema is None:
            return ATRState.NORMAL
        sorted_hist = sorted(atr_history) if atr_history else [atr_current]
        low = sorted_hist[max(0, len(sorted_hist) // 4)]
        high = sorted_hist[min(len(sorted_hist) - 1, len(sorted_hist) * 3 // 4)]
        if atr_current < low:
            return ATRState.LOW
        elif atr_current > high:
            return ATRState.HIGH
        return ATRState.NORMAL

    sorted_hist = sorted(atr_history)
    median = sorted_hist[len(sorted_hist) // 2]

    if atr_current < median * 0.7:
        return ATRState.LOW
    elif atr_current > median * 1.3:
        return ATRState.HIGH
    return ATRState.NORMAL


def classify_spread(
    spread_points: float,
    spread_history: List[float],
    schema: Optional[HabitatSchema],
) -> SpreadState:
    """History-aware spread classification."""
    if not spread_history or len(spread_history) < 5:
        if schema is None:
            return SpreadState.NORMAL
        tight = schema.spread_tight_pct
        wide = schema.spread_wide_pct
        if spread_points < tight:
            return SpreadState.TIGHT
        elif spread_points > wide:
            return SpreadState.WIDE
        return SpreadState.NORMAL

    sorted_hist = sorted(spread_history)
    median = sorted_hist[len(sorted_hist) // 2]

    if spread_points < median * 0.6:
        return SpreadState.TIGHT
    elif spread_points > median * 1.5:
        return SpreadState.WIDE
    return SpreadState.NORMAL


def apply_atr_hysteresis(
    raw_state: ATRState,
    current_stable: Optional[int],
    candidate: Optional[int],
    candidate_count: int,
) -> tuple:
    """
    ATR hysteresis filter: new state must appear 3 consecutive ticks before active.
    Returns (filtered_state, new_stable, new_candidate, new_count, flips_blocked).
    """
    raw_val = raw_state.value

    # Cold start
    if current_stable is None:
        return raw_state, raw_val, raw_val, 1, 0

    # Same as stable → reset candidate
    if raw_val == current_stable:
        return ATRState(current_stable), current_stable, raw_val, 1, 0

    # Same as candidate → increment
    if raw_val == candidate:
        new_count = candidate_count + 1
    else:
        new_count = 1

    # Check if candidate confirmed (3 consecutive)
    if new_count >= 3:
        return raw_state, raw_val, raw_val, new_count, 0
    else:
        return ATRState(current_stable), current_stable, candidate, new_count, 1


def build_habitat_key(
    session: Session,
    regime: Regime,
    atr: ATRState,
    spread: SpreadState,
) -> HabitatKey:
    """Build 4D habitat key tuple."""
    return (session.value, regime.value, atr.value, spread.value)


def build_reason_chain(
    session: Session,
    regime: Regime,
    atr_state: ATRState,
    spread_state: SpreadState,
) -> str:
    """Build human-readable reason chain for telemetry."""
    return (
        f"SESSION={session.name}, REGIME={regime.name}, "
        f"ATR={atr_state.name}, SPREAD={spread_state.name}"
    )
