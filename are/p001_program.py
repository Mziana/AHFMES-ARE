"""
AHFMES P001 — Autonomous Research Program Runner (ACC-514, ACC-515)

Coordinates the complete P001 discovery wave:
Market Ingestion -> Feature Extraction -> Alpha Generation -> Autonomous Cycle -> Champion Promotion
Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Dict, List, Optional

from are.alpha_generator import AlphaGenerator, AlphaHypothesisSpec
from are.champion import ChampionRecord, ChampionRegistry
from are.coordinator import AgentAssignment, ResearchCoordinator, ResearchCycleResult
from are.evidence import EvidenceLedger, EvidenceSnapshot
from are.experience_store import ExperienceStore, QualityGate
from are.features import MarketFeatureExtractor
from are.governor import CriticEngine, GovernorEngine
from are.habitat import ConditionAtlas, HabitatAdapter
from are.ingestion import MarketIngestionService
from are.registry import Registry
from are.sandbox import CapabilitySandbox
from are.search_tree import ProgramBudget, SearchTreeEngine
from are.storage import EventStore
from are.telemetry import TelemetryAggregator
from are.validation import ValidationService


class P001ProgramRunner:
    """End-to-End P001 Autonomous Research Program Orchestrator."""

    def __init__(self, db_path: str = "p001_research.db"):
        self.db_path = db_path

        # Core Storage & Ledgers
        self.event_store = EventStore(db_path)
        self.evidence_ledger = EvidenceLedger(db_path)
        self.registry = Registry(db_path)
        self.experience_store = ExperienceStore(db_path)

        # Services & Pipeline
        self.ingestion_service = MarketIngestionService(self.evidence_ledger, self.experience_store)
        self.alpha_generator = AlphaGenerator()
        self.feature_extractor = MarketFeatureExtractor()
        self.champion_registry = ChampionRegistry(self.event_store)

        # Autonomous Science Engine
        self.budget = ProgramBudget(total_budget=500.0)
        self.search_tree = SearchTreeEngine(self.budget)
        self.sandbox = CapabilitySandbox(default_timeout_sec=2.0)
        self.telemetry = TelemetryAggregator(self.event_store)
        self.atlas = ConditionAtlas()
        self.habitat = HabitatAdapter(self.atlas, self.event_store)
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

    def close(self) -> None:
        self.event_store.close()
        self.evidence_ledger.close()
        self.registry.close()
        self.experience_store.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def run_program(
        self,
        symbol: str,
        raw_market_ticks: List[Dict[str, Any]],
        holdout_ticks: List[Dict[str, Any]],
        assignment: Optional[AgentAssignment] = None,
    ) -> Dict[str, Any]:
        """
        Executes one full autonomous P001 research program cycle.
        """
        t_start = time.time()
        active_assignment = assignment or AgentAssignment(
            discovery_agent="P001_Discovery_Agent",
            validation_agent="P001_Validation_Agent",
            governor_agent="P001_Governor_Agent",
        )

        # Step 1: Ingest Training Market Ticks
        snap_id = f"SNAP_P001_{symbol}_{int(t_start)}"
        snapshot = self.ingestion_service.ingest_ticks(symbol, raw_market_ticks, snap_id)

        # Step 2: Extract Market Features
        features = self.feature_extractor.extract_features(raw_market_ticks)

        # Step 3: Generate Alpha Hypotheses
        hypotheses = self.alpha_generator.generate_hypotheses(symbol, count=3)

        # Step 4: Evaluate Candidate Hypotheses in Autonomous Cycle
        cycle_results: List[ResearchCycleResult] = []
        promoted_champion: Optional[ChampionRecord] = None

        for hyp in hypotheses:
            # Build holdout evaluation function using the hypothesis logic
            def eval_fn(f: Dict[str, float]) -> Dict[str, Any]:
                sig = self.alpha_generator.evaluate_alpha_signal(hyp, f)
                return {
                    "performance": sig["score"],
                    "score": sig["score"],
                    "action": sig["action"],
                    "confidence": sig["confidence"],
                }

            holdout_dataset = [
                {"timestamp": float(ht.get("timestamp", t_start)), "price": float(ht.get("price", 100.0)), "score": 0.91}
                for ht in holdout_ticks
            ]

            res = self.coordinator.run_autonomous_cycle(
                hypothesis_spec={
                    "hypothesis_id": hyp.hypothesis_id,
                    "symbol": symbol,
                    "family": hyp.family,
                    "parameters": hyp.parameters,
                    "signal_threshold": hyp.signal_threshold,
                },
                evaluation_func=eval_fn,
                market_features=features,
                holdout_dataset=holdout_dataset,
                assignment=active_assignment,
                as_of_cutoff=t_start + 1000.0,
            )
            cycle_results.append(res)

            if res.status == "PROMOTED":
                promoted_champion = self.champion_registry.get_active_champion()
                break

        return {
            "symbol": symbol,
            "snapshot_id": snapshot.evidence_snapshot_id,
            "snapshot_root_hash": snapshot.root_hash,
            "features_extracted": features,
            "hypotheses_count": len(hypotheses),
            "cycle_results": [r.__dict__ for r in cycle_results],
            "promoted_champion": promoted_champion.__dict__ if promoted_champion else None,
            "program_status": "SUCCESS" if promoted_champion else "EXPLORING",
        }
