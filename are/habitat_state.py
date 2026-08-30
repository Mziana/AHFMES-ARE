"""
AHFMES-ARE — Habitat State Assessment (ported from AHFMES-CHATGPT-DEEP M5)

Observer: assesses habitat health from memory quality.
Outputs HabitatStateLevel + reasoning + edge decay metadata.
"""

from dataclasses import dataclass
from typing import Optional

from are.habitat_schema import HabitatKey, HabitatSchema, HabitatStateLevel
from are.habitat_memory import HabitatMemory


class EdgeSeverity:
    HEALTHY = 0
    MILD = 1
    MODERATE = 2
    SEVERE = 3
    DEAD = 4


@dataclass(frozen=True)
class HabitatStateResult:
    level: HabitatStateLevel
    reason: str
    sample_size: int
    expectancy: float
    recency_obs: int
    edge_severity: int
    edge_reason: Optional[str]
    consistency_score: float


class HabitatStateAssessor:
    """Assesses habitat health based on memory quality."""

    def __init__(self, schema: HabitatSchema):
        self.schema = schema
        self.expectancy_healthy_threshold = 0.15
        self.expectancy_broken_threshold = -0.10
        self.recency_warning_threshold = 100
        self.recency_broken_threshold = 200
        self.edge_decay_window = 20

    def _calculate_consistency(self, ev: dict) -> float:
        n = ev.get("real_signals_seen", 0)
        if n < 10:
            return 0.5
        wr = ev.get("real_won", 0) / max(1, n)
        return min(1.0, max(0.0, abs(wr - 0.5) * 2.0))

    def _calculate_edge_decay(self, ev: dict) -> tuple:
        n = ev.get("real_signals_seen", 0)
        if n < self.edge_decay_window:
            return (EdgeSeverity.HEALTHY, None)

        won = ev.get("real_won", 0)
        lost = ev.get("real_lost", 0)
        exp = (won / max(1, n)) - (lost / max(1, n))

        if exp <= -0.20:
            return (EdgeSeverity.DEAD, f"Expectancy {exp:.2f}R — habitat edge dead")
        if exp <= -0.10:
            return (EdgeSeverity.SEVERE, f"Expectancy {exp:.2f}R — severe decay")
        if exp <= 0.0:
            return (EdgeSeverity.MODERATE, f"Expectancy {exp:.2f}R — moderate decay")
        if exp < self.expectancy_healthy_threshold:
            return (EdgeSeverity.MILD, f"Expectancy {exp:.2f}R — mild decay")
        return (EdgeSeverity.HEALTHY, None)

    def assess(self, key: HabitatKey, memory: HabitatMemory) -> HabitatStateResult:
        ev = memory.get_memory(key)
        sample = ev.get("real_signals_seen", 0)

        if sample < self.schema.min_observations_for_level:
            return HabitatStateResult(
                level=HabitatStateLevel.UNKNOWN,
                reason=f"Insufficient real observations: {sample} < {self.schema.min_observations_for_level}",
                sample_size=sample, expectancy=0.0,
                recency_obs=ev.get("total_evaluations", 0) - ev.get("last_update_observation", 0),
                edge_severity=EdgeSeverity.HEALTHY, edge_reason=None, consistency_score=0.0,
            )

        won = ev.get("real_won", 0)
        lost = ev.get("real_lost", 0)
        expectancy = (won / max(1, sample)) - (lost / max(1, sample))
        recency = ev.get("total_evaluations", 0) - ev.get("last_update_observation", 0)
        consistency = self._calculate_consistency(ev)
        edge_sev, edge_reason = self._calculate_edge_decay(ev)

        # BROKEN check
        broken_reasons = []
        if expectancy <= self.expectancy_broken_threshold:
            broken_reasons.append(f"Expectancy {expectancy:.2f}R")
        if recency >= self.recency_broken_threshold:
            broken_reasons.append(f"Stale {recency} obs")
        if edge_sev >= EdgeSeverity.SEVERE:
            broken_reasons.append(edge_reason or "Edge severe/dead")

        if len(broken_reasons) >= 2 or edge_sev == EdgeSeverity.DEAD:
            return HabitatStateResult(
                level=HabitatStateLevel.BROKEN,
                reason="; ".join(broken_reasons), sample_size=sample,
                expectancy=expectancy, recency_obs=recency,
                edge_severity=edge_sev, edge_reason=edge_reason, consistency_score=consistency,
            )

        # WARNING check
        warning_reasons = []
        if self.expectancy_broken_threshold < expectancy < self.expectancy_healthy_threshold:
            warning_reasons.append(f"Expectancy {expectancy:.2f}R below healthy")
        if recency >= self.recency_warning_threshold:
            warning_reasons.append(f"Stale {recency} obs")
        if edge_sev in (EdgeSeverity.MILD, EdgeSeverity.MODERATE):
            warning_reasons.append(edge_reason or "Edge decay")

        if warning_reasons:
            return HabitatStateResult(
                level=HabitatStateLevel.WARNING,
                reason="; ".join(warning_reasons), sample_size=sample,
                expectancy=expectancy, recency_obs=recency,
                edge_severity=edge_sev, edge_reason=edge_reason, consistency_score=consistency,
            )

        return HabitatStateResult(
            level=HabitatStateLevel.HEALTHY,
            reason=f"Expectancy {expectancy:.2f}R, consistency {consistency:.2f}",
            sample_size=sample, expectancy=expectancy, recency_obs=recency,
            edge_severity=edge_sev, edge_reason=edge_reason, consistency_score=consistency,
        )
