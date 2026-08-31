"""
AHFMES Error Taxonomy (§40)

Semantic exception categories for fail-closed pipeline.
Each error carries a severity (retryable/fatal/invalid_evidence)
and a stage name for traceability.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional


class ErrorSeverity(Enum):
    """How the Final Gate should interpret this error."""
    RETRYABLE = "retryable"
    FATAL = "fatal"
    INVALID_EVIDENCE = "invalid_evidence"


class AREFrameworkError(Exception):
    """Base class for all AHFMES pipeline errors."""

    severity: ErrorSeverity = ErrorSeverity.FATAL
    stage: str = "unknown"

    def __init__(self, message: str, *, stage: str = "unknown",
                 severity: Optional[ErrorSeverity] = None):
        self.stage = stage
        if severity is not None:
            self.severity = severity
        super().__init__(f"[{self.severity.value.upper()}] [{stage}] {message}")


class DataError(AREFrameworkError):
    """Dataset loading, hashing, or validation failure."""
    severity = ErrorSeverity.INVALID_EVIDENCE


class ConfigurationError(AREFrameworkError):
    """Invalid experiment configuration."""
    severity = ErrorSeverity.FATAL


class LeakageError(AREFrameworkError):
    """Future data contamination detected."""
    severity = ErrorSeverity.INVALID_EVIDENCE


class EvidenceError(AREFrameworkError):
    """Evidence object missing, corrupt, or incomplete."""
    severity = ErrorSeverity.INVALID_EVIDENCE


class ValidationError(AREFrameworkError):
    """Statistical validation failure (DSR, PSR, etc.)."""
    severity = ErrorSeverity.INVALID_EVIDENCE


class VerificationError(AREFrameworkError):
    """Independent verification detected mismatch."""
    severity = ErrorSeverity.INVALID_EVIDENCE


class TimeoutError_(AREFrameworkError):
    """Stage exceeded time budget."""
    severity = ErrorSeverity.FATAL

    def __init__(self, message: str, *, stage: str = "unknown",
                 severity: Optional[ErrorSeverity] = None):
        # Name has trailing underscore to avoid shadowing builtin TimeoutError
        super().__init__(message, stage=stage, severity=severity)


class PersistenceError(AREFrameworkError):
    """Artifact write/read/hash verification failure."""
    severity = ErrorSeverity.FATAL


class StrategyContractError(AREFrameworkError):
    """Strategy violated its output contract (no signal column, etc.)."""
    severity = ErrorSeverity.INVALID_EVIDENCE


class HoldoutError(AREFrameworkError):
    """Holdout lifecycle violation."""
    severity = ErrorSeverity.INVALID_EVIDENCE


class ParameterBindingError(AREFrameworkError):
    """Strategy does not respond to parameter variations (false optimization)."""
    severity = ErrorSeverity.INVALID_EVIDENCE


def classify_exception(exc: Exception) -> AREFrameworkError:
    """Wrap any exception into the appropriate taxonomy class."""
    if isinstance(exc, AREFrameworkError):
        return exc
    msg = str(exc)
    lower = msg.lower()
    if any(k in lower for k in ("timeout", "timed out", "deadline")):
        return TimeoutError_(msg)
    if any(k in lower for k in ("permission", "access", "locked")):
        return PersistenceError(msg)
    if any(k in lower for k in ("nan", "inf", "division by zero", "invalid value")):
        return ValidationError(msg)
    if any(k in lower for k in ("signal", "column", "key error")):
        return StrategyContractError(msg)
    return AREFrameworkError(msg)
