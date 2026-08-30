"""
AHFMES-ARE — Habitat Confidence (ported from AHFMES-CHATGPT-DEEP M6)

Granularity Level + Habitat Trust Score.
"""

from dataclasses import dataclass

from are.habitat_schema import HabitatSchema, GranularityLevel
from are.habitat_state import HabitatStateResult


@dataclass(frozen=True)
class HabitatConfidenceResult:
    granularity: GranularityLevel
    trust_score: float
    sample_quality: float
    freshness: float
    real_ratio: float


class HabitatConfidenceAssessor:
    """Assess habitat confidence from state and memory data."""

    def __init__(self, schema: HabitatSchema):
        self.schema = schema
        self.learning_floor = 20.0
        self.proven_floor = 60.0

    def assess(self, state: HabitatStateResult, ev: dict) -> HabitatConfidenceResult:
        n_real = ev.get("real_signals_seen", 0)
        n_shadow = ev.get("shadow_signals_seen", 0)
        total_weighted = n_real + 0.25 * n_shadow

        # Sample Quality
        if n_real >= self.schema.proven_observations:
            sample_quality = 1.0
        elif n_real >= self.schema.min_observations_for_level:
            sample_quality = 0.5 + 0.5 * (
                (n_real - self.schema.min_observations_for_level)
                / (self.schema.proven_observations - self.schema.min_observations_for_level)
            )
        else:
            sample_quality = 0.2 * (n_real / max(1, self.schema.min_observations_for_level))

        # Freshness
        recency = state.recency_obs
        if recency <= 25:
            freshness = 1.0
        elif recency >= 200:
            freshness = 0.0
        else:
            freshness = 1.0 - (recency - 25) / 175.0

        # Real Ratio
        real_ratio = n_real / total_weighted if total_weighted > 0 else 0.0

        # Trust Score
        trust = (
            35.0 * sample_quality
            + 30.0 * freshness
            + 20.0 * real_ratio
            + 15.0 * max(0.0, min(1.0, (state.expectancy + 0.5) / 1.5))
        )

        # Granularity Level
        if n_real < self.schema.min_observations_for_level:
            granularity = GranularityLevel.UNKNOWN
        elif n_real >= self.schema.proven_observations and trust >= self.proven_floor:
            granularity = GranularityLevel.PROVEN
        elif trust >= self.learning_floor:
            granularity = GranularityLevel.LEARNING
        else:
            granularity = GranularityLevel.UNKNOWN

        return HabitatConfidenceResult(
            granularity=granularity,
            trust_score=round(trust, 2),
            sample_quality=round(sample_quality, 3),
            freshness=round(freshness, 3),
            real_ratio=round(real_ratio, 3),
        )
