"""
Integrity layer — re-exports extracted modules for backward compatibility.

Modules are now split into:
- holdout.py: HoldoutManager, HoldoutEvaluationEngine, TemporalContract
- verification.py: IndependentVerifier, LeakageFirewall
- evidence_binding.py: EvidenceBinding, SensitivityAnalyzer, hash functions
- registries.py: GoldenDatasetRegistry, ResearchFamilyRegistry
"""

from are.research.holdout import (  # noqa: F401
    HoldoutManager,
    HoldoutEvaluationEngine,
    HoldoutEvidence,
    TemporalContract,
    HoldoutState,
    DatasetSplit,
)
from are.research.verification import (  # noqa: F401
    IndependentVerifier,
    LeakageFirewall,
)
from are.research.evidence_binding import (  # noqa: F401
    EvidenceBinding,
    SensitivityAnalyzer,
    compute_canonical_dataset_hash,
    compute_canonical_split_hash,
)
from are.research.registries import (  # noqa: F401
    GoldenDatasetRegistry,
    ResearchFamilyRegistry,
    ResearchFamily,
)

__all__ = [
    "HoldoutManager",
    "HoldoutEvaluationEngine",
    "HoldoutEvidence",
    "TemporalContract",
    "HoldoutState",
    "DatasetSplit",
    "IndependentVerifier",
    "LeakageFirewall",
    "EvidenceBinding",
    "SensitivityAnalyzer",
    "compute_canonical_dataset_hash",
    "compute_canonical_split_hash",
    "GoldenDatasetRegistry",
    "ResearchFamilyRegistry",
    "ResearchFamily",
]
