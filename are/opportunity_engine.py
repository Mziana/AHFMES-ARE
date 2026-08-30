"""
AHFMES-ARE — Opportunity Engine (ported from AHFMES-CHATGPT-DEEP M17)

Score 0-100. No direction. No execution.
Truth → Context → Policy. No double count.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OpportunityResult:
    score: float
    threshold: float
    reason: str
    should_enter: bool


class OpportunityEngine:
    """Decision compression: 'Is this habitat worth hunting?'"""

    THRESHOLD = 60.0

    def __init__(self, threshold: Optional[float] = None):
        self._threshold = threshold if threshold is not None else self.THRESHOLD

    def score(
        self,
        confidence: float,
        tier: int,
        habitat_tick_count: int,
    ) -> OpportunityResult:
        """
        Formula (frozen):
        - confidence: 70% (truth layer)
        - habitat_quality: 20% (stability = information)
        - tier_bonus: 10% (policy layer, small, non-dominant)
        """
        habitat_quality = 100.0 if habitat_tick_count >= 3 else 50.0
        tier_bonus = {0: 25.0, 1: 40.0, 2: 55.0, 3: 70.0}.get(tier, 25.0)

        score = (confidence * 0.70) + (habitat_quality * 0.20) + (tier_bonus * 0.10)
        score = max(0.0, min(100.0, score))

        reason = (
            f"Opportunity={score:.1f}: "
            f"confidence={confidence:.1f}×0.7 + "
            f"habitat_quality={habitat_quality:.0f}×0.2 + "
            f"tier_bonus={tier_bonus:.0f}×0.1"
        )

        should_enter = score >= self._threshold and habitat_tick_count > 0

        return OpportunityResult(
            score=score,
            threshold=self._threshold,
            reason=reason,
            should_enter=should_enter,
        )
