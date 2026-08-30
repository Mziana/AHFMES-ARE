"""
AHFMES-ARE — Habitat Schema (ported from AHFMES-CHATGPT-DEEP M1)

4D Habitat Key: Session × Regime × ATR × Spread = up to 3×4×3×3 = 108 habitats.
Pure definition — no logic, no state.
"""

from dataclasses import dataclass
from enum import Enum, auto


class Session(Enum):
    ASIA = auto()
    LONDON = auto()
    NEWYORK = auto()


class Regime(Enum):
    TRENDING = auto()
    SIDEWAYS = auto()
    RANGE = auto()
    VOLATILE = auto()


class ATRState(Enum):
    HIGH = auto()
    NORMAL = auto()
    LOW = auto()


class SpreadState(Enum):
    WIDE = auto()
    NORMAL = auto()
    TIGHT = auto()


class HabitatStateLevel(Enum):
    UNKNOWN = auto()
    HEALTHY = auto()
    WARNING = auto()
    BROKEN = auto()


class GranularityLevel(Enum):
    UNKNOWN = 0      # <5 real evaluations
    LEARNING = 1     # 5+ real eval, confidence >= 40
    PROVEN = 2       # 20+ real eval, confidence >= 60


@dataclass(frozen=True)
class HabitatSchema:
    """Static thresholds per habitat dimension."""
    atr_high_pct: float = 0.75
    atr_low_pct: float = 0.25
    spread_wide_pct: float = 0.80
    spread_tight_pct: float = 0.20
    min_observations_for_level: int = 5
    proven_observations: int = 20
    learning_confidence_threshold: float = 40.0
    proven_confidence_threshold: float = 60.0


# Type alias for habitat key
HabitatKey = tuple  # (Session.value, Regime.value, ATRState.value, SpreadState.value)
