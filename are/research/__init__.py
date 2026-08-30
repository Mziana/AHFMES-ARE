"""
AHFMES ARE — Research Plane

Provides the Backtest Operating System:
- DatasetRegistry: Freeze and verify research datasets
- StrategyRegistry: Track strategy identity and source hash
- ExperimentConfig: Frozen experiment configuration
- ExecutionModel: First-class execution simulation
- BacktestOrchestrator: Full lifecycle from data to artifact
- BacktestRun: Primary research object
- DataQualityGate: Pre-backtest data validation
"""

from are.research.dataset_registry import DatasetRegistry, DatasetManifest, DataQualityGate
from are.research.experiment_config import (
    StrategyRegistry, StrategyIdentity, ExecutionModel, ExperimentConfig,
    ParameterGrid, build_execution_model, build_parameter_grid, build_experiment_config,
)
from are.research.orchestrator import (
    BacktestOrchestrator, BacktestRun, RunStage, RunStatus, GateDecision, ArtifactManifest,
)
