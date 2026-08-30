"""
AHFMES ARE — Research Plane

Backtest Operating System with full integrity layer:
- DatasetRegistry: Freeze and verify research datasets
- StrategyRegistry: Track strategy identity and source hash
- ExperimentConfig: Frozen experiment configuration
- ExecutionModel: First-class execution simulation
- BacktestOrchestrator: Full lifecycle from data to artifact
- BacktestRun: Primary research object
- DataQualityGate: Pre-backtest data validation

Integrity Layer:
- HoldoutManager: TRAIN -> VALIDATION -> HOLDOUT with LOCKED state
- LeakageFirewall: Temporal contract enforcement (no look-ahead)
- ResearchFamilyRegistry: Multiple-testing governance across experiments
- IndependentVerifier: Recompute results from artifacts
- SensitivityAnalyzer: Parameter and cost stress testing
- GoldenDatasetRegistry: Regression oracle for engine verification
"""

from are.research.dataset_registry import DatasetRegistry, DatasetManifest, DataQualityGate
from are.research.experiment_config import (
    StrategyRegistry, StrategyIdentity, ExecutionModel, ExperimentConfig,
    ParameterGrid, build_execution_model, build_parameter_grid, build_experiment_config,
)
from are.research.orchestrator import (
    BacktestOrchestrator, BacktestRun, RunStage, RunStatus, GateDecision, ArtifactManifest,
)
from are.research.integrity import (
    HoldoutManager, HoldoutState, DatasetSplit,
    LeakageFirewall, TemporalContract,
    ResearchFamilyRegistry, ResearchFamily,
    IndependentVerifier,
    SensitivityAnalyzer,
    GoldenDatasetRegistry,
)
