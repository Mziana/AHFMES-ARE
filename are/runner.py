"""
AHFMES P001 — Operational Runner Daemon (ACC-502)

Coordinates real-time tick consumption, safety gating, regret anomaly detection,
and automated evolutionary adaptation.
Stdlib only (time, threading, json, typing, dataclasses).
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from are.champion import ChampionRegistry
from are.coordinator import AgentAssignment, ResearchCoordinator, ResearchCycleResult
from are.evidence import EvidenceLedger
from are.evolution import AdaptationTrigger, EvolutionaryLoop, RegretAnalyzer
from are.governor import CriticEngine, GovernorEngine
from are.habitat import ConditionAtlas, HabitatAdapter
from are.operational import OperationalBrain, OperationalSignal
from are.registry import Registry
from are.safety import CapitalSafetyKernel, SafetyLimits
from are.sandbox import CapabilitySandbox
from are.search_tree import ProgramBudget, SearchTreeEngine
from are.storage import EventStore
from are.telemetry import TelemetryAggregator
from are.validation import ValidationService


@dataclass
class RunnerConfig:
    db_path: str = "ahfmes_are.db"
    symbol: str = "BTCUSDT"
    tick_interval_sec: float = 1.0
    lookback_events: int = 50
    regret_threshold: float = 0.40
    auto_evolve: bool = True
    max_position_size: float = 1.0
    max_drawdown_pct: float = 0.15
    volatility_cutoff: float = 2.5
    max_order_rate_per_min: int = 10


class OperationalRunner:
    """Operational Daemon orchestrating fast-loop brain and slow-loop evolutionary engine."""

    def __init__(self, config: Optional[RunnerConfig] = None):
        self.config = config or RunnerConfig()

        # Storage & Ledger
        self.event_store = EventStore(self.config.db_path)
        self.evidence_ledger = EvidenceLedger(self.config.db_path)
        self.registry = Registry(self.config.db_path)

        # Safety & Champion
        self.champion_registry = ChampionRegistry(self.event_store)
        self.safety_limits = SafetyLimits(
            max_position_size=self.config.max_position_size,
            max_drawdown_pct=self.config.max_drawdown_pct,
            volatility_cutoff=self.config.volatility_cutoff,
            max_order_rate_per_min=self.config.max_order_rate_per_min,
        )
        self.safety_kernel = CapitalSafetyKernel(self.safety_limits)

        # Habitat & Brain
        self.atlas = ConditionAtlas()
        self.habitat = HabitatAdapter(self.atlas, self.event_store)
        self.brain = OperationalBrain(
            champion_registry=self.champion_registry,
            safety_kernel=self.safety_kernel,
            habitat=self.habitat,
            event_store=self.event_store,
        )

        # Research Engine & Evolution
        self.budget = ProgramBudget(total_budget=500.0)
        self.search_tree = SearchTreeEngine(self.budget)
        self.sandbox = CapabilitySandbox(default_timeout_sec=2.0)
        self.telemetry = TelemetryAggregator(self.event_store)
        self.validation = ValidationService(self.evidence_ledger, self.event_store)
        self.critic = CriticEngine()
        self.governor = GovernorEngine()

        self.coordinator = ResearchCoordinator(
            search_tree_engine=self.search_tree,
            sandbox=self.sandbox,
            telemetry=self.telemetry,
            habitat=self.habitat,
            validation=self.validation,
            critic=self.critic,
            governor=self.governor,
            champion_registry=self.champion_registry,
        )

        self.regret_analyzer = RegretAnalyzer(self.event_store)
        self.evolutionary_loop = EvolutionaryLoop(
            regret_analyzer=self.regret_analyzer,
            research_coordinator=self.coordinator,
            registry=self.registry,
        )

        self._running = False
        self._lock = threading.Lock()

    def close(self) -> None:
        self.event_store.close()
        self.evidence_ledger.close()
        self.registry.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def step_tick(
        self,
        market_features: Dict[str, float],
        current_risk_state: Dict[str, Any],
        timestamp: Optional[float] = None,
    ) -> OperationalSignal:
        """Processes a single operational tick through the Operational Brain."""
        ts = timestamp if timestamp is not None else time.time()
        return self.brain.process_tick(
            symbol=self.config.symbol,
            timestamp=ts,
            market_features=market_features,
            current_risk_state=current_risk_state,
            as_of_cutoff=ts,
        )

    def check_and_adapt(
        self,
        current_features: Dict[str, float],
        holdout_dataset: List[Dict[str, Any]],
        assignment: Optional[AgentAssignment] = None,
        as_of_cutoff: Optional[float] = None,
        evaluation_func: Optional[Callable] = None,
    ) -> Optional[ResearchCycleResult]:
        """Checks for operational regret anomalies and triggers autonomous slow-loop adaptation if breached."""
        active_assignment = assignment or AgentAssignment(
            discovery_agent="Daemon_Discovery_Agent",
            validation_agent="Daemon_Validation_Agent",
            governor_agent="Daemon_Governor_Agent",
        )
        cutoff = as_of_cutoff if as_of_cutoff is not None else time.time()

        return self.evolutionary_loop.evaluate_and_evolve(
            symbol=self.config.symbol,
            current_features=current_features,
            holdout_dataset=holdout_dataset,
            assignment=active_assignment,
            as_of_cutoff=cutoff,
            lookback_events=self.config.lookback_events,
            regret_threshold=self.config.regret_threshold,
            evaluation_func=evaluation_func,
        )

    def run_loop(
        self,
        tick_generator_fn: Callable[[], Tuple[Dict[str, float], Dict[str, Any]]],
        max_ticks: Optional[int] = None,
        assignment: Optional[AgentAssignment] = None,
        holdout_dataset: Optional[List[Dict[str, Any]]] = None,
        evaluation_func: Optional[Callable] = None,
    ) -> int:
        """Runs the operational daemon loop for up to max_ticks (or indefinitely if None)."""
        self._running = True
        ticks_processed = 0
        default_holdout = holdout_dataset or [{"timestamp": time.time(), "score": 0.90}]

        while self._running:
            if max_ticks is not None and ticks_processed >= max_ticks:
                break

            try:
                features, risk_state = tick_generator_fn()
                self.step_tick(features, risk_state)
                ticks_processed += 1

                if self.config.auto_evolve and ticks_processed % 5 == 0:
                    self.check_and_adapt(
                        current_features=features,
                        holdout_dataset=default_holdout,
                        assignment=assignment,
                        evaluation_func=evaluation_func,
                    )

                if self.config.tick_interval_sec > 0:
                    time.sleep(self.config.tick_interval_sec)

            except KeyboardInterrupt:
                break
            except Exception as e:
                # Fail-closed: log and continue or stop gracefully
                break

        self._running = False
        return ticks_processed

    def stop(self) -> None:
        self._running = False
