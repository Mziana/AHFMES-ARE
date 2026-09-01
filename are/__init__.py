"""
AHFMES ARE — Autonomous Research Engine
Vectorized backtesting, WFO/DSR pipeline, MT5 execution.
"""

from __future__ import annotations

__version__ = "0.1.0"

# Core backtest engine
from are.backtest import (
    BacktestResult,
    BacktestResearchContract,
    IsolatedBacktestEngine,
    WFOEvidence,
    WFOFoldEvidence,
)

# Runtime engine
from are.engine import ARETradingEngine, TickResult

# Safety & risk
from are.safety import CapitalSafetyKernel, SafetyDecision, SafetyLimits
from are.breaker import CircuitBreaker, CircuitBreakerResult

# Execution
from are.mt5_gateway import MT5ExecutionGateway, MT5OrderRequest, MT5OrderResult

# Validation & proposal screening
from are.validation import (
    DSRResult,
    PerformanceResult,
    ValidationReport,
    ValidationService,
    WFOIntegrityResult,
)

# Data pipeline
from are.data_pipeline import DataPurifier, DataQualityReport

# Research pipeline
from are.research.orchestrator import (
    ArtifactManifest,
    BacktestOrchestrator,
    BacktestRun,
    GateDecision,
    RunStage,
    RunStatus,
    StageResult,
)

__all__ = [
    # Version
    "__version__",
    # Backtest
    "BacktestResult",
    "BacktestResearchContract",
    "IsolatedBacktestEngine",
    "WFOEvidence",
    "WFOFoldEvidence",
    # Engine
    "ARETradingEngine",
    "TickResult",
    # Safety
    "CapitalSafetyKernel",
    "SafetyDecision",
    "SafetyLimits",
    "CircuitBreaker",
    "CircuitBreakerResult",
    # Execution
    "MT5ExecutionGateway",
    "MT5OrderRequest",
    "MT5OrderResult",
    # Validation
    "DSRResult",
    "PerformanceResult",
    "ValidationReport",
    "ValidationService",
    "WFOIntegrityResult",
    # Data
    "DataPurifier",
    "DataQualityReport",
    # Research
    "ArtifactManifest",
    "BacktestOrchestrator",
    "BacktestRun",
    "GateDecision",
    "RunStage",
    "RunStatus",
    "StageResult",
]
