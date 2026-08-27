"""
AHFMES ARE-2 & ARE-4 — Adapters, Logging & Resource Management (DEBT-02 Submodule)
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
    ResourceLimitExceededError,
    _to_canonical_payload,
)

@dataclass(frozen=True)
class AuditEntry:
    timestamp: float
    component: str
    operation: str
    input_hash: str
    output_hash: str
    params_hash: str
    duration_ms: float
    success: bool


@dataclass(frozen=True)
class ExperienceConfig:
    max_memory_mb: int = 512
    max_replay_sec: float = 5.0
    max_anomaly_ms: float = 100.0
    alert_cooldown_sec: float = 60.0
    config_hash: str = ""

    def __post_init__(self):
        if not self.config_hash:
            data = {
                "max_memory_mb": self.max_memory_mb,
                "max_replay_sec": f"{self.max_replay_sec:.2f}",
                "max_anomaly_ms": f"{self.max_anomaly_ms:.2f}",
                "alert_cooldown_sec": f"{self.alert_cooldown_sec:.2f}",
            }
            _, h = canonicalize_object(data, "EXPERIENCE_STORE_CONFIG")
            object.__setattr__(self, "config_hash", h)


# ============================================================
# D1/D3: AUDIT LOGGING & REPRODUCIBILITY
# ============================================================

class AuditLogger:
    """
    Structured JSONL Audit Logger (D1/D3):
    Records deterministic, content-addressed audit trails for all operations.
    """

    def __init__(self, log_path: Optional[str] = None):
        self._log_path = log_path
        self._entries: List[AuditEntry] = []
        self._lock = threading.Lock()

    def log(
        self,
        component: str,
        operation: str,
        input_data: Any,
        output_data: Any,
        params: Any,
        duration_ms: float,
        success: bool = True,
    ) -> AuditEntry:
        _, input_hash = canonicalize_object(_to_canonical_payload(input_data), "EXPERIENCE_STORE_ENTRY")
        _, output_hash = canonicalize_object(_to_canonical_payload(output_data), "EXPERIENCE_STORE_ENTRY")
        _, params_hash = canonicalize_object(_to_canonical_payload(params), "EXPERIENCE_STORE_ENTRY")

        entry = AuditEntry(
            timestamp=time.time(),
            component=component,
            operation=operation,
            input_hash=input_hash,
            output_hash=output_hash,
            params_hash=params_hash,
            duration_ms=round(duration_ms, 4),
            success=success,
        )

        with self._lock:
            self._entries.append(entry)
            if self._log_path:
                os.makedirs(os.path.dirname(self._log_path), exist_ok=True)
                with open(self._log_path, "a", encoding="utf-8") as f:
                    rec = {
                        "timestamp": entry.timestamp,
                        "component": entry.component,
                        "operation": entry.operation,
                        "input_hash": entry.input_hash,
                        "output_hash": entry.output_hash,
                        "params_hash": entry.params_hash,
                        "duration_ms": entry.duration_ms,
                        "success": entry.success,
                    }
                    f.write(json.dumps(rec) + "\n")

        return entry

    def get_entries(self) -> List[AuditEntry]:
        with self._lock:
            return list(self._entries)


# ============================================================
# D2: RESOURCE BOUNDS ENFORCEMENT
# ============================================================

class ResourceBoundedExecutor:
    """
    Performance & Resource Bounds Enforcer (D2):
    Validates execution quotas (memory, latency, duration). Fail-closed rejection.
    """

    def __init__(self, config: ExperienceConfig):
        self._config = config

    def check_anomaly_latency(self, duration_ms: float) -> None:
        if duration_ms > self._config.max_anomaly_ms:
            raise ResourceLimitExceededError(
                f"Anomaly detection duration ({duration_ms:.2f}ms) exceeded quota ({self._config.max_anomaly_ms}ms)"
            )

    def check_replay_duration(self, duration_sec: float) -> None:
        if duration_sec > self._config.max_replay_sec:
            raise ResourceLimitExceededError(
                f"Replay duration ({duration_sec:.2f}s) exceeded quota ({self._config.max_replay_sec}s)"
            )


# ============================================================
# A3: DATA QUALITY GATE & OBSERVABILITY
# ============================================================



class ComponentAdapterRegistry:
    """
    Reuse Existing Components Adapters (C2):
    Adapter pattern per component for existing AHFMES modules.
    Zero modification to existing code.
    """

    SUPPORTED_COMPONENTS = frozenset({
        "orchestrator",
        "habitat_memory",
        "evaluation_writer",
        "pattern_events",
        "pattern_recovery",
        "policy_contract",
        "freeze_snapshot",
        "runtime_identity",
        "telemetry",
        "direction_discovery",
        "micro_executor",
    })

    def __init__(self):
        self._adapters: Dict[str, Dict[str, Any]] = {}

    def register_adapter(self, component_name: str, adapter_details: Dict[str, Any]) -> str:
        if component_name not in self.SUPPORTED_COMPONENTS:
            raise ExperienceStoreError(f"Unsupported component for adapter reuse: {component_name}")
        _, interface_hash = canonicalize_object(
            _to_canonical_payload({"component": component_name, "details": adapter_details}),
            "ORCHESTRATOR_ADAPTER_INTERFACE" if component_name == "orchestrator" else "HABITAT_MEMORY_ADAPTER_INTERFACE",
        )
        self._adapters[component_name] = {
            "component_name": component_name,
            "details": adapter_details,
            "interface_hash": interface_hash,
        }
        return interface_hash

    def get_adapter(self, component_name: str) -> Optional[Dict[str, Any]]:
        return self._adapters.get(component_name)



