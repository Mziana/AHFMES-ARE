"""
AHFMES ARE-2 & ARE-4 — Experience Intelligence (DEBT-02 Modular Facade)

Re-exports 100% of symbols from submodules for strict backward compatibility (ACC-421, ACC-422):
- are.experience_store
- are.anomaly
- are.replay
- are.adapters
"""
from are.experience_store import (
    ExperienceStoreError,
    QualityGateError,
    AnomalyDetectionError,
    ResourceLimitExceededError,
    AlertError,
    StreamType,
    CounterfactualQuality,
    RegimeState,
    REQUIRED_PROVENANCE_FIELDS,
    _to_canonical_payload,
    ProvenancedRecord,
    ExperienceRecord,
    GateMetrics,
    CounterfactualSimulationResult,
    QualityGate,
    ExperienceStore,
    evidence_threshold_threshold_met_and_budget_check_passed,
    EvidenceExperienceBridge,
)

from are.anomaly import (
    AlertSeverity,
    AnomalyResult,
    AlertRecord,
    AnomalyDetector,
    AnomalyAlertEngine,
)

from are.adapters import (
    AuditEntry,
    ExperienceConfig,
    AuditLogger,
    ResourceBoundedExecutor,
    ComponentAdapterRegistry,
)

from are.replay import (
    CapabilityGapAssessment,
    KnowledgeSynthesizer,
    CapabilityGapHypothesis,
    CapabilityGapEngine,
    ScientificMemory,
    BatchReplayEngine,
    WhatIfSensitivityEngine,
)
