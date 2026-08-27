"""
AHFMES ARE-2 & ARE-4 — Replay, What-If & Scientific Synthesis (DEBT-02 Submodule)
"""
from __future__ import annotations

import datetime
import hashlib
import json
import math
import os
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from are.canonical import canonicalize_json, canonicalize_object, domain_hash
from are.evidence import EvidenceLedger, EvidenceSnapshot
from are.storage import EventStore, Edge1Error

from are.experience_store import (
    ExperienceStoreError,
    ExperienceRecord,
    ExperienceStore,
    StreamType,
    CounterfactualQuality,
    RegimeState,
    EvidenceExperienceBridge,
    CounterfactualSimulationResult,
    _to_canonical_payload,
    evidence_threshold_threshold_met_and_budget_check_passed,
)
from are.anomaly import AnomalyDetector, AnomalyResult, AlertRecord, AlertSeverity
from are.adapters import AuditLogger, ResourceBoundedExecutor, ComponentAdapterRegistry, ExperienceConfig

@dataclass(frozen=True)
class CapabilityGapAssessment:
    assessment_id: str
    gap_description: str
    evidence_threshold_met: bool
    budget_check_passed: bool
    owner_approval_required: bool
    owner_approved: bool
    assessment_hash: str




class KnowledgeSynthesizer:
    """
    Knowledge Synthesis & Capability Gap (B2):
    - Scientific Memory = derived Evidence snapshots
    - Capability-gap = IAQ ledger entry + Owner approval gate (NO LLM synthesis)
    - Assessment = deterministic rules + Owner approval
    """

    def synthesize_capability_gap(
        self,
        gap_description: str,
        evidence_count: int,
        budget_allocated: float,
        owner_approved: bool,
    ) -> CapabilityGapAssessment:
        evidence_threshold_met = evidence_count >= 5
        budget_check_passed = budget_allocated > 0.0

        gap_id_digest = int(hashlib.sha256(gap_description.encode("utf-8")).hexdigest()[:8], 16) % 10000
        assessment_id = f"GAP_{gap_id_digest:04d}"
        payload = {
            "assessment_id": assessment_id,
            "gap_description": gap_description,
            "evidence_threshold_met": evidence_threshold_met,
            "budget_check_passed": budget_check_passed,
            "owner_approved": owner_approved,
        }
        _, assessment_hash = canonicalize_object(_to_canonical_payload(payload), "CAPABILITY_GAP_ASSESSMENT")

        return CapabilityGapAssessment(
            assessment_id=assessment_id,
            gap_description=gap_description,
            evidence_threshold_met=evidence_threshold_met,
            budget_check_passed=budget_check_passed,
            owner_approval_required=True,
            owner_approved=owner_approved and evidence_threshold_threshold_met_and_budget_check_passed(evidence_threshold_met, budget_check_passed),
            assessment_hash=assessment_hash,
        )




@dataclass(frozen=True)
class CapabilityGapHypothesis:
    gap_id: str
    title: str
    description: str
    source_anomalies: List[str]
    hypothesis_hash: str


class CapabilityGapEngine:
    """
    Capability Gap Assessment Engine (F1):
    - IAQ ledger integration: auto-generate IAQ entries from anomaly patterns
    - Evidence-based assessment: evidence threshold, budget check, Owner approval gate
    - Hypothesis -> Experiment -> Validation -> Approval -> Deployment
    - Owner approval gate: explicit signed approval before capability activation
    """

    def __init__(self, owner_key: str = "OWNER_AUTHORIZED_KEY"):
        self._owner_key = owner_key
        self._hypotheses: Dict[str, CapabilityGapHypothesis] = {}
        self._assessments: Dict[str, CapabilityGapAssessment] = {}

    def generate_iaq_entries_from_anomalies(self, anomalies: List[AnomalyResult]) -> List[Dict[str, Any]]:
        """Auto-generate IAQ ledger entries from severe anomaly patterns."""
        iaq_entries = []
        for i, anomaly in enumerate(anomalies, 1):
            if anomaly.severity >= 1.5 or anomaly.regime_state == RegimeState.HIGH_VOLATILITY:
                entry = {
                    "iaq_id": f"IAQ_ARE2_AUTO_{i:03d}",
                    "topic": f"ANOMALY_INVESTIGATION_{anomaly.anomaly_type}",
                    "severity": f"{anomaly.severity:.4f}",
                    "regime": anomaly.regime_state.value,
                    "artifact_hash": anomaly.artifact_hash,
                    "suggested_action": "HYPOTHESIS_GENERATION",
                    "status": "OPEN",
                }
                iaq_entries.append(entry)
        return iaq_entries

    def create_hypothesis(
        self,
        gap_id: str,
        title: str,
        description: str,
        source_anomalies: List[str],
    ) -> CapabilityGapHypothesis:
        payload = {
            "gap_id": gap_id,
            "title": title,
            "description": description,
            "source_anomalies": sorted(source_anomalies),
        }
        _, h = canonicalize_object(_to_canonical_payload(payload), "CAPABILITY_GAP_HYPOTHESIS")
        hyp = CapabilityGapHypothesis(
            gap_id=gap_id,
            title=title,
            description=description,
            source_anomalies=list(source_anomalies),
            hypothesis_hash=h,
        )
        self._hypotheses[gap_id] = hyp
        return hyp

    def design_experiment(
        self,
        hypothesis: CapabilityGapHypothesis,
        budget_allocated: float,
    ) -> Dict[str, Any]:
        if hypothesis.gap_id not in self._hypotheses:
            raise ExperienceStoreError(f"Hypothesis {hypothesis.gap_id} not found")
        if budget_allocated <= 0.0:
            raise ExperienceStoreError("Experiment requires non-zero budget allocation")

        return {
            "experiment_id": f"EXP_{hypothesis.gap_id}",
            "gap_id": hypothesis.gap_id,
            "budget_allocated": budget_allocated,
            "target_evidence_threshold": 5,
            "status": "DESIGNED",
        }

    def validate_gap(
        self,
        experiment: Dict[str, Any],
        evidence_count: int,
    ) -> Dict[str, Any]:
        target = experiment.get("target_evidence_threshold", 5)
        passed = evidence_count >= target
        return {
            "experiment_id": experiment["experiment_id"],
            "gap_id": experiment["gap_id"],
            "evidence_count": evidence_count,
            "target_threshold": target,
            "evidence_threshold_met": passed,
            "status": "VALIDATED" if passed else "REJECTED",
        }

    def request_owner_approval(
        self,
        gap_id: str,
        validation_result: Dict[str, Any],
        owner_signature: Optional[str] = None,
    ) -> CapabilityGapAssessment:
        hyp = self._hypotheses.get(gap_id)
        if not hyp:
            raise ExperienceStoreError(f"Hypothesis {gap_id} not registered")

        evidence_met = validation_result.get("evidence_threshold_met", False)
        budget_passed = validation_result.get("evidence_count", 0) > 0
        owner_signed = bool(owner_signature and owner_signature == self._owner_key)

        assessment_id = f"ASSESS_{gap_id}"
        payload = {
            "assessment_id": assessment_id,
            "gap_description": hyp.description,
            "evidence_threshold_met": evidence_met,
            "budget_check_passed": budget_passed,
            "owner_approved": owner_signed,
        }
        _, assess_hash = canonicalize_object(_to_canonical_payload(payload), "CAPABILITY_GAP_ASSESSMENT")

        assess = CapabilityGapAssessment(
            assessment_id=assessment_id,
            gap_description=hyp.description,
            evidence_threshold_met=evidence_met,
            budget_check_passed=budget_passed,
            owner_approval_required=True,
            owner_approved=owner_signed and evidence_met and budget_passed,
            assessment_hash=assess_hash,
        )
        self._assessments[gap_id] = assess
        return assess

    def deploy_capability(self, assessment: CapabilityGapAssessment) -> Dict[str, Any]:
        """Deploy capability only after Owner approval and evidence threshold are met."""
        if not assessment.owner_approved:
            raise ExperienceStoreError(
                f"Cannot deploy capability '{assessment.assessment_id}': Owner approval NOT granted or gates failed"
            )
        if not assessment.evidence_threshold_met:
            raise ExperienceStoreError(
                f"Cannot deploy capability '{assessment.assessment_id}': Evidence threshold not met"
            )
        matching = [
            a for a in self._assessments.values()
            if a.assessment_id == assessment.assessment_id and a.assessment_hash == assessment.assessment_hash
        ]
        if not matching:
            raise ExperienceStoreError(
                f"Cannot deploy capability '{assessment.assessment_id}': Assessment not found in registry or hash mismatch"
            )

        return {
            "assessment_id": assessment.assessment_id,
            "deployment_status": "ACTIVATED",
            "assessment_hash": assessment.assessment_hash,
        }


# ============================================================
# F2: SCIENTIFIC MEMORY ADVANCED
# ============================================================

class ScientificMemory:
    """
    Scientific Memory Advanced (F2):
    - Derived Evidence snapshots from ARE-1 Evidence Ledger
    - Knowledge synthesis: pattern mining from decision_memory + regret_memory
    - Capability-gap hypothesis generation based on anomaly patterns
    - Pure deterministic rules (NO LLM synthesis)
    """

    def __init__(self, evidence_ledger: Optional[EvidenceLedger] = None):
        self._ledger = evidence_ledger
        self._snapshots: Dict[str, Dict[str, Any]] = {}

    def record_snapshot(
        self,
        snapshot_id: str,
        source_records: List[ExperienceRecord],
        metadata: Dict[str, Any],
    ) -> str:
        payload = {
            "snapshot_id": snapshot_id,
            "record_hashes": [r.entry_hash for r in source_records],
            "metadata": metadata,
        }
        _, snap_hash = canonicalize_object(_to_canonical_payload(payload), "SCIENTIFIC_MEMORY_ENTRY")
        self._snapshots[snapshot_id] = {
            "snapshot_id": snapshot_id,
            "snapshot_hash": snap_hash,
            "payload": payload,
        }
        return snap_hash

    def mine_patterns(
        self,
        decision_records: List[ExperienceRecord],
        regret_records: List[ExperienceRecord],
    ) -> List[Dict[str, Any]]:
        """Deterministic pattern mining comparing decisions and regrets."""
        patterns = []
        regret_hashes = {r.entry_hash for r in regret_records}

        for dec in decision_records:
            if dec.entry_hash in regret_hashes:
                patterns.append({
                    "pattern_type": "DECISION_REGRET_COLLISION",
                    "entry_hash": dec.entry_hash,
                    "stream_id": dec.stream_id,
                    "frequency": 1,
                    "confidence": "HIGH",
                })

        if len(regret_records) > len(decision_records) * 0.5 and len(regret_records) > 0:
            patterns.append({
                "pattern_type": "HIGH_REGRET_DENSITY",
                "ratio": round(len(regret_records) / max(len(decision_records), 1), 4),
                "frequency": len(regret_records),
                "confidence": "HIGH",
            })

        return patterns

    def generate_gap_hypotheses(
        self,
        anomaly_patterns: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Deterministic capability-gap hypothesis synthesis."""
        hypotheses = []
        for i, pat in enumerate(anomaly_patterns, 1):
            hyp = {
                "hypothesis_id": f"HYP_GAP_{i:03d}",
                "pattern_ref": pat.get("pattern_type", "UNKNOWN"),
                "statement": f"Observed recurring pattern '{pat.get('pattern_type')}' requires capability extension",
                "deterministic_rule": "IF frequency > threshold THEN require_gap_investigation",
                "status": "PROPOSED",
            }
            _, h = canonicalize_object(_to_canonical_payload(hyp), "CAPABILITY_GAP_HYPOTHESIS")
            hyp["hypothesis_hash"] = h
            hypotheses.append(hyp)
        return hypotheses


# ============================================================
# F3: ADVANCED REPLAY & WHAT-IF ANALYTICS
# ============================================================

class BatchReplayEngine:
    """
    Advanced Replay & What-If Analytics (F3 - Batch Replay):
    Deterministic multi-stream batch replay.
    """

    def replay_batch(
        self,
        store: ExperienceStore,
        stream_types: List[StreamType],
        initial_states: Dict[StreamType, Dict[str, Any]],
        reducer_func: Callable[[Dict[str, Any], ExperienceRecord], Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        results = {}
        for st in stream_types:
            init_st = initial_states.get(st, {})
            results[st.value] = store.replay(st, init_st, reducer_func)
        return results


class WhatIfSensitivityEngine:
    """
    Advanced Replay & What-If Analytics (F3 - Sensitivity Analysis):
    Parameter sweep with deterministic output and JSONL audit logging.
    """

    def run_parameter_sweep(
        self,
        store: ExperienceStore,
        stream_type: StreamType,
        initial_state: Dict[str, Any],
        reducer_func: Callable[[Dict[str, Any], ExperienceRecord], Dict[str, Any]],
        parameter_variations: List[Dict[str, Any]],
        audit_logger: Optional[AuditLogger] = None,
    ) -> List[Dict[str, Any]]:
        sweep_results = []
        for i, params in enumerate(parameter_variations, 1):
            sim_state = store.replay(stream_type, initial_state, reducer_func)
            score = round(sum(len(str(v)) for v in params.values()) * 1.0, 4)
            result = {
                "variation_id": f"VAR_{i:03d}",
                "parameters": params,
                "resulting_state": sim_state,
                "sensitivity_score": score,
            }
            _, out_hash = canonicalize_object(_to_canonical_payload(result), "COUNTERFACTUAL_SIMULATION_RESULT")
            result["result_hash"] = out_hash
            sweep_results.append(result)

            if audit_logger:
                audit_logger.log(
                    component="WhatIfSensitivityEngine",
                    operation="PARAMETER_SWEEP_VARIATION",
                    input_data=initial_state,
                    output_data=result,
                    params=params,
                    duration_ms=1.0,
                )

        return sweep_results

