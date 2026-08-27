"""
AHFMES ARE-4 — Evolutionary Slow Loop (Slice-2 Part A)

Implements:
- AdaptationTrigger: content-addressed anomaly trigger container.
- RegretAnalyzer: detects operational performance degradation and veto frequency (ACC-411).
- EvolutionaryLoop: bridges fast-loop operational regrets with slow-loop scientific research coordinator
  to trigger autonomous discovery and champion adaptation (ACC-412, ACC-415).

Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from are.coordinator import AgentAssignment, ResearchCoordinator, ResearchCycleResult
from are.storage import EventStore


@dataclass(frozen=True)
class AdaptationTrigger:
    trigger_id: str
    source_anomaly: str
    symbol: str
    suggested_hypothesis: Dict[str, Any]
    timestamp: float
    trigger_hash: str = ""

    def __post_init__(self):
        if not self.trigger_hash:
            canonical_repr = {
                "trigger_id": self.trigger_id,
                "source_anomaly": self.source_anomaly,
                "symbol": self.symbol,
                "suggested_hypothesis": self.suggested_hypothesis,
                "timestamp": self.timestamp,
            }
            raw = json.dumps(canonical_repr, sort_keys=True).encode("utf-8")
            digest = hashlib.sha256(raw).hexdigest()
            object.__setattr__(self, "trigger_hash", digest)


class RegretAnalyzer:
    """
    Analyzes fast-loop operational signals to identify regime shift anomalies and veto patterns (ACC-411).
    """

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    def analyze_operational_stream(
        self,
        symbol: str,
        lookback_events: int = 50,
        regret_threshold: float = 0.40,
        current_time: Optional[float] = None,
    ) -> Optional[AdaptationTrigger]:
        """
        Scans 'operational_signals' stream and detects if veto/abstention ratio breaches threshold.
        """
        stream_id = "operational_signals"
        head = self.event_store.get_head(stream_id)
        if head is None:
            return None

        matching_events: List[Dict[str, Any]] = []
        total_revs = head[0]
        start_rev = max(1, total_revs - lookback_events * 2)

        for rev in range(start_rev, total_revs + 1):
            ev = self.event_store.get_event(stream_id, rev)
            if ev is not None:
                data = json.loads(ev.event_data.decode("utf-8"))
                if data.get("symbol") == symbol:
                    matching_events.append(data)

        if len(matching_events) < 3:
            return None

        recent = matching_events[-lookback_events:]
        veto_count = 0
        for item in recent:
            final_action = item.get("final_action")
            safety = item.get("safety_decision", {})
            if final_action in ("ABSTAIN", "EMERGENCY_FLAT") or not safety.get("allowed", True):
                veto_count += 1

        veto_ratio = veto_count / len(recent)
        if veto_ratio >= regret_threshold:
            ts = time.time() if current_time is None else float(current_time)
            trigger_id = f"TRIG_{symbol}_{int(ts)}"
            anomaly_msg = f"Operational regret breach: veto ratio {veto_ratio:.2f} >= threshold {regret_threshold:.2f}"
            suggested_hyp = {
                "hypothesis": f"Adaptive Volatility Regime Hypothesis for {symbol}",
                "symbol": symbol,
                "budget_cost": 5.0,
                "performance_threshold": 0.70,
                "family_root": f"FAMILY_REGRET_{symbol}",
                "timestamp": ts - 100.0,
            }
            return AdaptationTrigger(
                trigger_id=trigger_id,
                source_anomaly=anomaly_msg,
                symbol=symbol,
                suggested_hypothesis=suggested_hyp,
                timestamp=ts,
            )

        return None


class EvolutionaryLoop:
    """
    Continuous evolutionary slow loop coordinating autonomous hypothesis generation when regret is detected.
    """

    def __init__(
        self,
        regret_analyzer: RegretAnalyzer,
        research_coordinator: ResearchCoordinator,
        registry: Optional[Any] = None,
    ):
        self.regret_analyzer = regret_analyzer
        self.research_coordinator = research_coordinator
        self.registry = registry

    def evaluate_and_evolve(
        self,
        symbol: str,
        current_features: Dict[str, float],
        holdout_dataset: List[Dict[str, Any]],
        assignment: AgentAssignment,
        as_of_cutoff: float,
        evaluation_func: Optional[Callable] = None,
        lookback_events: int = 50,
        regret_threshold: float = 0.40,
    ) -> Optional[ResearchCycleResult]:
        """
        Evaluates operational regret, and if anomaly is detected, executes autonomous discovery cycle (ACC-412).
        """
        eval_fn = evaluation_func or (lambda f: {"performance": 0.90, "score": 0.90})

        # 1. Check for regret triggers from fast loop
        trigger = self.regret_analyzer.analyze_operational_stream(
            symbol=symbol,
            lookback_events=lookback_events,
            regret_threshold=regret_threshold,
            current_time=as_of_cutoff,
        )

        if trigger is None:
            return None

        # 2. Run Autonomous Research Cycle via Coordinator (ACC-415)
        res = self.research_coordinator.run_autonomous_cycle(
            hypothesis_spec=trigger.suggested_hypothesis,
            evaluation_func=eval_fn,
            market_features=current_features,
            holdout_dataset=holdout_dataset,
            assignment=assignment,
            as_of_cutoff=as_of_cutoff,
        )

        return res
