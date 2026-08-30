"""
AHFMES-ARE — Trade Health Monitor (ported from AHFMES-CHATGPT-DEEP M11)

Monitors position health based on R-multiple and duration.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class HealthState(Enum):
    THRIVING = auto()
    HEALTHY = auto()
    WARNING = auto()
    CRITICAL = auto()
    DEAD_CANDIDATE = auto()
    DEAD = auto()


class TriggerType(Enum):
    NONE = auto()
    BREAKEVEN = auto()
    TRAIL = auto()
    PROFIT_LOCK = auto()
    CLOSE = auto()


@dataclass(frozen=True)
class HealthResult:
    state: HealthState
    r_multiple: float
    trigger: Optional[TriggerType]
    trigger_reason: str
    duration_ticks: int


class TradeHealthObserver:
    """Evaluates trade health from R-multiple and duration."""

    def evaluate(
        self,
        r_multiple: float,
        duration_ticks: int = 0,
        max_duration_ticks: int = 3600,
    ) -> HealthResult:
        """Determine health state from R-multiple."""
        trigger = None
        trigger_reason = "No trigger"

        if r_multiple >= 2.0:
            state = HealthState.THRIVING
            trigger = TriggerType.PROFIT_LOCK
            trigger_reason = f"Profit lock at {r_multiple:.2f}R"
        elif r_multiple >= 1.0:
            state = HealthState.HEALTHY
            trigger = TriggerType.TRAIL
            trigger_reason = f"Trail at {r_multiple:.2f}R"
        elif r_multiple >= 0.3:
            state = HealthState.HEALTHY
            trigger = TriggerType.BREAKEVEN
            trigger_reason = f"Breakeven at {r_multiple:.2f}R"
        elif r_multiple >= 0.0:
            state = HealthState.WARNING
        elif r_multiple >= -0.5:
            state = HealthState.WARNING
        elif r_multiple >= -1.0:
            state = HealthState.CRITICAL
            trigger = TriggerType.CLOSE
            trigger_reason = f"Critical at {r_multiple:.2f}R"
        else:
            state = HealthState.DEAD_CANDIDATE
            trigger = TriggerType.CLOSE
            trigger_reason = f"Dead candidate at {r_multiple:.2f}R"

        return HealthResult(
            state=state,
            r_multiple=r_multiple,
            trigger=trigger,
            trigger_reason=trigger_reason,
            duration_ticks=duration_ticks,
        )
