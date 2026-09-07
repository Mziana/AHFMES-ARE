"""
AHFMES ARE — Research Pipeline Shared Types

Enums and dataclasses shared across orchestrator and stage modules.
Extracted to avoid circular imports.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class RunStage(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class RunStatus(Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class GateDecision(Enum):
    PASS = "PASS"
    BORDERLINE = "BORDERLINE"
    FAIL = "FAIL"
    INVALID = "INVALID"


@dataclass
class StageResult:
    stage: str
    status: RunStage
    started_at: float = 0.0
    completed_at: float = 0.0
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ArtifactManifest:
    """Complete artifact manifest for a backtest run."""
    run_id: str
    artifact_hash: str
    dataset_hash: str
    strategy_hash: str
    config_hash: str
    execution_model_hash: str
    wfo_provenance_hash: str
    files: Dict[str, str] = field(default_factory=dict)  # path -> hash
    created_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BacktestRun:
    """
    Primary research object. One run = one immutable experiment.
    Contains the full lifecycle of a backtest from data to artifact.
    """
    run_id: str
    experiment_id: str
    created_at: float
    engine_version: str = "4.0.0"

    # Identity
    strategy_id: str = ""
    strategy_version: str = ""
    dataset_id: str = ""
    dataset_hash: str = ""
    purified_hash: str = ""
    config_hash: str = ""
    execution_model_hash: str = ""

    # Status
    status: RunStatus = RunStatus.CREATED
    stages: Dict[str, StageResult] = field(default_factory=dict)

    # Results
    baseline_result: Optional[Dict[str, Any]] = None
    wfo_result: Optional[Dict[str, Any]] = None
    oos_result: Optional[Dict[str, Any]] = None
    statistics_result: Optional[Dict[str, Any]] = None
    crisis_result: Optional[Dict[str, Any]] = None
    stability_result: Optional[Dict[str, Any]] = None
    final_gate: Optional[Dict[str, Any]] = None
    quality_report: Optional[Dict[str, Any]] = None
    initial_capital: float = 10000.0

    # RNG / Seed governance
    random_seed: int = 42
    rng_algorithm: str = "PythonRandom"
    mc_simulations: int = 1000

    # Integrity
    temporal_contract_hash: str = ""
    leakage_check_passed: bool = False
    holdout_locked: bool = False
    holdout_evaluated: bool = False
    verification_status: str = "PENDING"  # PENDING, VERIFIED, REJECTED

    # Evidence chain
    holdout_evidence: Optional[Dict[str, Any]] = None  # HoldoutEvidence.to_dict()
    holdout_invalid_reason: Optional[str] = None  # WFO tanpa winner (param dideklarasikan) -> holdout INVALID
    evidence_binding: Optional[Dict[str, Any]] = None  # EvidenceBinding.to_dict()

    # Artifact
    artifact_manifest: Optional[ArtifactManifest] = None
    provenance_hash: str = ""

    # Timestamps
    started_at: float = 0.0
    completed_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = {}
        for f in dataclasses.fields(self):
            val = getattr(self, f.name)
            if isinstance(val, Enum):
                d[f.name] = val.value
            elif f.name == "stages":
                d[f.name] = {}
                for sk, sv in val.items():
                    if isinstance(sv, StageResult):
                        sd = {kk: vv.value if isinstance(vv, Enum) else vv for kk, vv in asdict(sv).items()}
                        d[f.name][sk] = sd
                    else:
                        d[f.name][sk] = sv
            elif isinstance(val, list):
                d[f.name] = [item.to_dict() if hasattr(item, "to_dict") else item for item in val]
            elif hasattr(val, "to_dict"):
                d[f.name] = val.to_dict()
            else:
                d[f.name] = val
        return d
