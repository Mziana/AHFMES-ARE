"""
AHFMES-ARE — Confidence Engine (ported from AHFMES-CHATGPT-DEEP M8)

Truth Layer: Market Score + Performance Score → Confidence → Tier Ceiling.
4D weighted market scoring with dynamic market/perf weighting.
"""

from dataclasses import dataclass
from typing import Any

from are.habitat_schema import HabitatStateLevel


@dataclass(frozen=True)
class ConfidenceResult:
    confidence: float
    tier_ceiling: int  # 0=MICRO, 1=SCAVENGER, 2=HUNTER, 3=PREDATOR
    reason: str
    market_score: float = 0.0
    perf_score: float = 0.0
    market_weight: float = 0.8
    perf_weight: float = 0.2


class ConfidenceEngine:
    """
    Market 25/30/25/20 weighting.
    Dynamic market/perf weighting: 80/20 → 60/40 based on sample size.
    State = Tier Ceiling only (not multiplier).
    """

    STATE_CEILINGS = {
        HabitatStateLevel.UNKNOWN: 2,
        HabitatStateLevel.HEALTHY: 3,
        HabitatStateLevel.WARNING: 1,
        HabitatStateLevel.BROKEN: 0,
    }

    def compute(
        self,
        state_level: HabitatStateLevel,
        perf_score: float,
        trend_strength: float,
        volatility_quality: float,
        session_quality: float,
        spread_quality: float,
        total_evaluations: int,
    ) -> ConfidenceResult:
        """Calculate confidence score and tier ceiling."""

        # Market score: 4D weighted average
        market_score = (
            trend_strength * 0.25
            + volatility_quality * 0.30
            + session_quality * 0.25
            + spread_quality * 0.20
        )

        # Dynamic weighting
        if total_evaluations >= 20:
            market_weight = 0.60
            perf_weight = 0.40
        else:
            ratio = total_evaluations / 20.0
            market_weight = 0.80 - (0.20 * ratio)
            perf_weight = 0.20 + (0.20 * ratio)

        confidence = market_weight * market_score + perf_weight * perf_score

        ceiling = self.STATE_CEILINGS.get(state_level, 2)
        names = {0: "MICRO", 1: "SCAVENGER", 2: "HUNTER", 3: "PREDATOR"}

        return ConfidenceResult(
            confidence=max(0.0, min(100.0, confidence)),
            tier_ceiling=ceiling,
            reason=f"State={state_level.name}: confidence={confidence:.1f}, ceiling={names.get(ceiling, 'UNKNOWN')}",
            market_score=round(market_score, 1),
            perf_score=round(perf_score, 1),
            market_weight=round(market_weight, 2),
            perf_weight=round(perf_weight, 2),
        )
