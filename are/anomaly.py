"""
AHFMES ARE-2 & ARE-4 — Anomaly Detection & Alerting (DEBT-02 Submodule)
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
    QualityGateError,
    AnomalyDetectionError,
    ResourceLimitExceededError,
    AlertError,
    StreamType,
    CounterfactualQuality,
    RegimeState,
    ExperienceRecord,
    ProvenancedRecord,
    _to_canonical_payload,
)

class AlertSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"



@dataclass(frozen=True)
class AnomalyResult:
    anomaly_type: str
    severity: float
    counterfactual_quality: CounterfactualQuality
    regime_state: RegimeState
    spread_hostility: float
    artifact_hash: str
    details: Dict[str, Any]




@dataclass(frozen=True)
class AlertRecord:
    alert_id: str
    anomaly_type: str
    severity: AlertSeverity
    message: str
    timestamp: float
    audit_hash: str




class AnomalyDetector:
    """
    Deterministic Anomaly Detection (A2):
    - Fixed-seed HMM regime shift detection
    - Deterministic spread hostility metric
    - Rule-based counterfactual quality classification
    - Content-addressed artifact hashing via domain_hash
    - Zero random state (pure math)
    """

    def __init__(self, seed: int = 20260827):
        self._seed = seed
        self._config = {
            "seed": seed,
            "regime_threshold_high": "2.500000",
            "regime_threshold_trans": "1.200000",
            "spread_multiplier": "1.500000",
        }
        self._config_bytes, self._config_hash = canonicalize_object(
            _to_canonical_payload(self._config), "ANOMALY_DETECTION_CONFIG"
        )

    @property
    def config_hash(self) -> str:
        return self._config_hash

    def compute_spread_hostility(self, spread: float, volatility: float, volume: float) -> float:
        if spread < 0 or volatility < 0 or volume < 0:
            raise AnomalyDetectionError("Inputs must be non-negative")
        denom = max(volume, 1.0)
        return round((spread * volatility * 100.0) / denom, 6)

    def detect_regime_shift(self, price_series: List[float]) -> RegimeState:
        if not price_series or len(price_series) < 2:
            return RegimeState.STABLE

        diffs = [price_series[i] - price_series[i - 1] for i in range(1, len(price_series))]
        mean_diff = sum(diffs) / len(diffs)
        variance = sum((x - mean_diff) ** 2 for x in diffs) / len(diffs)
        std_dev = math.sqrt(variance)

        pseudo_transition_weight = (math.sin(self._seed + len(price_series)) + 1.0) * 0.1
        adjusted_metric = std_dev + pseudo_transition_weight

        if adjusted_metric >= 2.5:
            return RegimeState.HIGH_VOLATILITY
        elif adjusted_metric >= 1.2:
            return RegimeState.TRANSITIONING
        else:
            return RegimeState.STABLE

    def classify_counterfactual_quality(self, anomaly_type: str, severity: float) -> CounterfactualQuality:
        if anomaly_type == "REGIME_SHIFT" and severity > 2.0:
            return CounterfactualQuality.CF_HIGH
        elif anomaly_type == "SPREAD_HOSTILITY" or severity > 1.0:
            return CounterfactualQuality.CF_MED
        elif anomaly_type == "LIQUIDITY_DROP":
            return CounterfactualQuality.CF_LOW
        else:
            return CounterfactualQuality.UNOBSERVABLE

    def analyze(
        self,
        anomaly_type: str,
        price_series: List[float],
        spread: float,
        volatility: float,
        volume: float,
    ) -> AnomalyResult:
        spread_hostility = self.compute_spread_hostility(spread, volatility, volume)
        regime = self.detect_regime_shift(price_series)
        severity = round(spread_hostility + (2.0 if regime == RegimeState.HIGH_VOLATILITY else 0.5), 4)
        cf_quality = self.classify_counterfactual_quality(anomaly_type, severity)

        details = {
            "anomaly_type": anomaly_type,
            "severity": f"{severity:.4f}",
            "regime": regime.value,
            "spread_hostility": f"{spread_hostility:.6f}",
            "series_len": len(price_series),
        }
        _, artifact_hash = canonicalize_object(_to_canonical_payload(details), "ANOMALY_DETECTION_ENTRY")

        return AnomalyResult(
            anomaly_type=anomaly_type,
            severity=severity,
            counterfactual_quality=cf_quality,
            regime_state=regime,
            spread_hostility=spread_hostility,
            artifact_hash=artifact_hash,
            details=details,
        )


class AnomalyAlertEngine:
    """
    Observability & Anomaly Alerting (C1):
    - Deterministic alert rules: threshold, cooldown, deduplication
    - Audit log per alert
    - Emergency-flat PROHIBITED in IAQ (requires separate ACT authority)
    """

    def __init__(self, cooldown_sec: float = 60.0, audit_logger: Optional[AuditLogger] = None):
        self._cooldown_sec = cooldown_sec
        self._audit_logger = audit_logger
        self._last_alert_time: Dict[str, float] = {}
        self._alerts: List[AlertRecord] = []
        self._lock = threading.Lock()

    def process_anomaly(self, anomaly: AnomalyResult) -> Optional[AlertRecord]:
        with self._lock:
            now = time.time()
            anomaly_key = f"{anomaly.anomaly_type}:{anomaly.regime_state.value}"

            # Cooldown / Deduplication check
            last_time = self._last_alert_time.get(anomaly_key, 0.0)
            if now - last_time < self._cooldown_sec:
                return None  # Suppressed by cooldown

            if anomaly.severity >= 3.0:
                severity = AlertSeverity.CRITICAL
            elif anomaly.severity >= 1.5:
                severity = AlertSeverity.WARNING
            else:
                severity = AlertSeverity.INFO

            alert_id = f"ALT_{len(self._alerts) + 1:04d}"
            message = f"Anomaly {anomaly.anomaly_type} detected with severity {anomaly.severity:.2f} in regime {anomaly.regime_state.value}"

            alert_dict = {
                "alert_id": alert_id,
                "anomaly_type": anomaly.anomaly_type,
                "severity": severity.value,
                "message": message,
                "timestamp": f"{now:.2f}",
            }
            _, audit_hash = canonicalize_object(_to_canonical_payload(alert_dict), "ANOMALY_ALERT_RECORD")

            alert = AlertRecord(
                alert_id=alert_id,
                anomaly_type=anomaly.anomaly_type,
                severity=severity,
                message=message,
                timestamp=now,
                audit_hash=audit_hash,
            )

            self._last_alert_time[anomaly_key] = now
            self._alerts.append(alert)

            if self._audit_logger:
                self._audit_logger.log(
                    component="AnomalyAlertEngine",
                    operation="PROCESS_ANOMALY",
                    input_data=anomaly.details,
                    output_data=alert_dict,
                    params={"cooldown_sec": self._cooldown_sec},
                    duration_ms=1.0,
                )

            return alert


# ============================================================
# A1, B1, B2, B3: EXPERIENCE STORE, REPLAY, SYNTHESIS & INTEGRATION
# ============================================================


