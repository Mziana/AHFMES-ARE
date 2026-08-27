"""
AHFMES ARE-3 — Multi-Agent Research Coordinator (Slice-3 Part B)

Implements:
- AgentAssignment: principal definitions enforcing Separation of Duties across agent roles (ACC-322).
- ResearchCycleResult: unified outcome container for autonomous research cycles.
- ResearchCoordinator: orchestrates full autonomous loop from Search Tree exploration to Sandbox execution,
  Telemetry tracking, Habitat observation, Out-of-sample Validation, Critic comparison, Governor gating,
  and Champion promotion (ACC-321, ACC-326).

Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from are.champion import ChampionRegistry
from are.governor import CriticEngine, GovernorEngine
from are.habitat import HabitatAdapter
from are.sandbox import CapabilitySandbox
from are.search_tree import SearchTreeEngine, SearchTreeNode
from are.telemetry import ExperimentTrace, TelemetryAggregator
from are.validation import ValidationService


@dataclass(frozen=True)
class AgentAssignment:
    discovery_agent: str
    validation_agent: str
    governor_agent: str


@dataclass(frozen=True)
class ResearchCycleResult:
    cycle_id: str
    candidate_id: str
    status: str  # "PROMOTED" | "REJECTED" | "NO_EDGE_FOUND"
    details: Dict[str, Any]


class ResearchCoordinator:
    """
    Orchestrates end-to-end autonomous research workflows among specialized agents.
    """

    def __init__(
        self,
        search_tree_engine: SearchTreeEngine,
        sandbox: CapabilitySandbox,
        telemetry: TelemetryAggregator,
        habitat: HabitatAdapter,
        validation: ValidationService,
        critic: CriticEngine,
        governor: GovernorEngine,
        champion_registry: ChampionRegistry,
    ):
        self.search_tree_engine = search_tree_engine
        self.sandbox = sandbox
        self.telemetry = telemetry
        self.habitat = habitat
        self.validation = validation
        self.critic = critic
        self.governor = governor
        self.champion_registry = champion_registry

    def run_autonomous_cycle(
        self,
        hypothesis_spec: Dict[str, Any],
        evaluation_func: Callable,
        market_features: Dict[str, float],
        holdout_dataset: List[Dict[str, Any]],
        assignment: AgentAssignment,
        as_of_cutoff: float,
        candidate_id: Optional[str] = None,
    ) -> ResearchCycleResult:
        """
        Executes one full autonomous research iteration (ACC-321, ACC-326).
        """
        # 1. Separation of Duties Gate (ACC-322)
        self.governor.verify_sod(
            creator_principal=assignment.discovery_agent,
            validator_principal=assignment.validation_agent,
            promoter_principal=assignment.governor_agent,
        )

        family_root = hypothesis_spec.get("family_root", "FAMILY_ARE3_ROOT")
        cycle_id = f"CYCLE_{int(as_of_cutoff)}_{int(time.time() * 1000) % 100000}"

        # 2. Check Search Tree Stopping Rule
        stopping = self.search_tree_engine.evaluate_stopping_rule(family_root)
        if stopping == "NO_EDGE_FOUND":
            return ResearchCycleResult(
                cycle_id=cycle_id,
                candidate_id=candidate_id or "NO_CANDIDATE",
                status="NO_EDGE_FOUND",
                details={"reason": "Search tree budget or failure stopping rule triggered"},
            )

        # 3. Habitat Ingestion under Information-Time Barrier
        obs = self.habitat.ingest_market_state(
            symbol=hypothesis_spec.get("symbol", "BTCUSDT"),
            timestamp=hypothesis_spec.get("timestamp", as_of_cutoff - 60.0),
            features=market_features,
            as_of_cutoff=as_of_cutoff,
        )

        # 4. Search Tree Node Spawning
        parent_node = hypothesis_spec.get("parent_node")
        node = self.search_tree_engine.spawn_node(
            parent_node=parent_node,
            hypothesis_data=hypothesis_spec,
            budget_cost=hypothesis_spec.get("budget_cost", 1.0),
        )

        cand_id = candidate_id or f"CAND_{node.node_id}"

        # 5. Capability Sandbox Execution
        exec_res = self.sandbox.execute(evaluation_func, args=(market_features,))
        if not exec_res.success:
            self.search_tree_engine.record_node_outcome(node.node_id, success=False)
            return ResearchCycleResult(
                cycle_id=cycle_id,
                candidate_id=cand_id,
                status="REJECTED",
                details={"error": exec_res.error, "stage": "SANDBOX_EXECUTION"},
            )

        # 6. Telemetry Recording
        score_val = 0.8
        if isinstance(exec_res.output, dict):
            score_val = float(exec_res.output.get("score", exec_res.output.get("performance", 0.8)))

        trace = ExperimentTrace(
            experiment_id=f"EXP_{cand_id}",
            candidate_id=cand_id,
            timestamp=as_of_cutoff - 30.0,
            metrics={"performance": score_val, "score": score_val},
            tags=[obs.regime, "autonomous_cycle"],
        )
        self.telemetry.record_trace(trace)
        aggs = self.telemetry.compute_aggregate_metrics(cand_id)

        # 7. Out-of-Sample Validation
        val_report = self.validation.validate_candidate(
            candidate_id=cand_id,
            holdout_token=hypothesis_spec.get("holdout_token", "HOLDOUT_TOKEN_ARE3"),
            as_of_ts=as_of_cutoff,
            dataset=holdout_dataset,
            performance_threshold=hypothesis_spec.get("performance_threshold", 0.70),
        )

        if val_report.status != "VALIDATED":
            self.search_tree_engine.record_node_outcome(node.node_id, success=False)
            return ResearchCycleResult(
                cycle_id=cycle_id,
                candidate_id=cand_id,
                status="REJECTED",
                details={"validation_status": val_report.status, "stage": "HOLDOUT_VALIDATION"},
            )

        # 8. Critic Adversarial Evaluation against Current Champion
        active_champ = self.champion_registry.get_active_champion()
        champion_id = active_champ.champion_id if active_champ else "GENESIS_CHAMPION"
        champion_metrics = hypothesis_spec.get("champion_metrics", {"performance": 0.70, "drawdown": 0.15})
        challenger_metrics = {"performance": val_report.performance_metric, "drawdown": 0.05}

        critic_passed = self.critic.evaluate_adversarial(
            challenger_metrics=challenger_metrics,
            champion_metrics=champion_metrics,
            stress_factor=hypothesis_spec.get("stress_factor", 1.1),
        )

        # 9. Governor Promotion Decision
        disposition = self.governor.evaluate_promotion(
            candidate_id=cand_id,
            champion_id=champion_id,
            validation_report=val_report,
            critic_passed=critic_passed,
            creator_principal=assignment.discovery_agent,
            validator_principal=assignment.validation_agent,
            promoter_principal=assignment.governor_agent,
            current_ts=as_of_cutoff,
        )

        # 10. Promotion to Champion Registry
        if disposition.decision == "PROMOTED":
            champ_rec = self.champion_registry.promote_champion(
                candidate_id=cand_id,
                promotion_disposition=disposition,
            )
            self.search_tree_engine.record_node_outcome(node.node_id, success=True)
            return ResearchCycleResult(
                cycle_id=cycle_id,
                candidate_id=cand_id,
                status="PROMOTED",
                details={
                    "champion_id": champ_rec.champion_id,
                    "disposition": disposition.decision,
                    "rationale": disposition.rationale,
                    "aggregate_metrics": aggs,
                },
            )
        else:
            self.search_tree_engine.record_node_outcome(node.node_id, success=False)
            return ResearchCycleResult(
                cycle_id=cycle_id,
                candidate_id=cand_id,
                status="REJECTED",
                details={
                    "disposition": disposition.decision,
                    "rationale": disposition.rationale,
                },
            )
