"""
AHFMES ARE-2 & ARE-4 — Experience Store & Quality Gates (DEBT-02 Submodule)
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


# Named SQLite Authorizer Action Codes & Return Codes (ARCH-04)
SQLITE_DROP_TABLE = 11
SQLITE_DROP_TRIGGER = 16
SQLITE_ATTACH = 24
SQLITE_DENY = 1
SQLITE_OK = 0

class ExperienceStoreError(Exception):
    """Base exception for Experience Store operations."""


class QualityGateError(ExperienceStoreError):
    """Raised when data quality gate checks fail."""


class AnomalyDetectionError(ExperienceStoreError):
    """Raised when anomaly detection operations encounter errors."""


class ResourceLimitExceededError(ExperienceStoreError):
    """Raised when resource bounds (memory, replay time, anomaly latency) are exceeded."""


class AlertError(ExperienceStoreError):
    """Raised when alerting operations fail or violate authority limits."""


# ============================================================
# ENUMS & TYPES
# ============================================================

class StreamType(Enum):
    DECISION_MEMORY = "decision_memory"
    REGRET_MEMORY = "regret_memory"
    ANOMALY_DETECTION = "anomaly_detection"


class CounterfactualQuality(Enum):
    CF_HIGH = "CF-HIGH"
    CF_MED = "CF-MED"
    CF_LOW = "CF-LOW"
    UNOBSERVABLE = "UNOBSERVABLE"


class RegimeState(Enum):
    STABLE = "STABLE"
    TRANSITIONING = "TRANSITIONING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"




REQUIRED_PROVENANCE_FIELDS = frozenset({
    "source_id",
    "timestamp",
    "session_id",
    "environment",
    "collector_version",
    "input_hash",
    "schema_version",
    "trace_id",
})



def _to_canonical_payload(obj: Any) -> Any:
    """Helper to convert floats to string/int for canonical identity compliance."""
    if isinstance(obj, float):
        return f"{obj:.6f}"
    elif isinstance(obj, dict):
        return {str(k): _to_canonical_payload(v) for k, v in sorted(obj.items())}
    elif isinstance(obj, list):
        return [_to_canonical_payload(x) for x in obj]
    return obj


# ============================================================
# DATACLASSES
# ============================================================

@dataclass(frozen=True)
class ProvenancedRecord:
    provenance: Dict[str, Any]
    payload: Dict[str, Any]


@dataclass(frozen=True)
class ExperienceRecord:
    stream_id: str
    revision: int
    entry_hash: str
    previous_hash: str
    data_bytes: bytes
    provenance: Dict[str, Any]




@dataclass(frozen=True)
class GateMetrics:
    total_ingested: int
    passed_gate: int
    quarantined: int
    completeness_rate: float
    avg_latency_ms: float


@dataclass(frozen=True)
class CounterfactualSimulationResult:
    fork_id: str
    original_state_hash: str
    simulation_state_hash: str
    final_state: Dict[str, Any]
    counterfactual_quality: CounterfactualQuality




class QualityGate:
    """
    Observability & Data Quality Gate (A3):
    - Completeness gate (99.9% target)
    - Latency gate (<100ms)
    - 8-field provenance validation
    - Fail-closed statistical quarantine for suspicious data
    """

    def __init__(self, max_latency_ms: float = 100.0, min_completeness_rate: float = 0.999):
        self._max_latency_ms = max_latency_ms
        self._min_completeness_rate = min_completeness_rate
        self._total_ingested = 0
        self._passed = 0
        self._quarantined: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def validate_provenance(self, provenance: Dict[str, Any]) -> None:
        """Validate 8 required provenance fields. Fail-closed if missing."""
        if not isinstance(provenance, dict):
            raise QualityGateError("Provenance must be a dict")
        missing = REQUIRED_PROVENANCE_FIELDS - set(provenance.keys())
        if missing:
            raise QualityGateError(f"Missing required provenance fields: {sorted(missing)}")

    def validate_and_ingest(self, record: ProvenancedRecord, latency_ms: float) -> Tuple[bool, str]:
        """
        Validate record against quality gates.
        Returns (passed, reason).
        If failed, record is placed in quarantine.
        """
        with self._lock:
            self._total_ingested += 1

            # Gate 1: Provenance 8-field check
            try:
                self.validate_provenance(record.provenance)
            except QualityGateError as e:
                self._quarantine(record, str(e))
                return False, f"PROVENANCE_FAIL: {e}"

            # Gate 2: Latency gate
            if latency_ms >= self._max_latency_ms:
                reason = f"LATENCY_FAIL: {latency_ms:.2f}ms >= {self._max_latency_ms}ms"
                self._quarantine(record, reason)
                return False, reason

            # Gate 3: Payload completeness check
            if not record.payload or not isinstance(record.payload, dict):
                reason = "COMPLETENESS_FAIL: Empty or invalid payload"
                self._quarantine(record, reason)
                return False, reason

            # Gate 4: Completeness rate check
            current_completeness = (self._passed + 1) / self._total_ingested
            if current_completeness < self._min_completeness_rate and self._total_ingested > 10:
                reason = f"COMPLETENESS_RATE_FAIL: {current_completeness:.4f} < {self._min_completeness_rate}"
                self._quarantine(record, reason)
                return False, reason

            self._passed += 1
            return True, "PASSED"

    def _quarantine(self, record: ProvenancedRecord, reason: str) -> None:
        self._quarantined.append({
            "record": record,
            "reason": reason,
            "quarantine_timestamp": record.provenance.get("timestamp", 0),
        })

    def get_quarantine(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._quarantined)

    def get_metrics(self) -> GateMetrics:
        with self._lock:
            rate = (self._passed / self._total_ingested) if self._total_ingested > 0 else 1.0
            return GateMetrics(
                total_ingested=self._total_ingested,
                passed_gate=self._passed,
                quarantined=len(self._quarantined),
                completeness_rate=rate,
                avg_latency_ms=0.0,
            )




class ExperienceStore:
    """
    Append-only Experience Store (A1, B1, B2, B3):
    - SQLite WAL storage with 3 streams (decision_memory, regret_memory, anomaly_detection)
    - Re-uses EventStore (are/storage.py) for append-only triggers, CAS, and WAL management (ACC-9, ACC-18)
    - Pure function replay & What-If fork simulation
    """

    GENESIS_HASH = "0" * 64

    def __init__(self, db_path: str, wal_mode: bool = True):
        self._db_path = db_path
        self._wal_mode = wal_mode
        self._event_store = EventStore(db_path, wal_mode=wal_mode)

    def close(self) -> None:
        self._event_store.close()

    def get_head(self, stream_type: StreamType) -> Tuple[int, str]:
        head = self._event_store.get_head(stream_type.value)
        if head is None:
            return 0, self.GENESIS_HASH
        return head[0], head[1]

    def append(
        self,
        stream_type: StreamType,
        payload: Dict[str, Any],
        provenance: Dict[str, Any],
        expected_revision: int,
    ) -> ExperienceRecord:
        stream_id = stream_type.value

        tag_map = {
            StreamType.DECISION_MEMORY: "DECISION_MEMORY_ENTRY",
            StreamType.REGRET_MEMORY: "REGRET_MEMORY_ENTRY",
            StreamType.ANOMALY_DETECTION: "ANOMALY_DETECTION_ENTRY",
        }
        tag = tag_map[stream_type]
        canonical_payload = _to_canonical_payload(payload)
        data_bytes, payload_hash = canonicalize_object(canonical_payload, tag)

        event_dict = {
            "data_bytes_hex": data_bytes.hex(),
            "payload_hash": payload_hash,
            "provenance": _to_canonical_payload(provenance),
        }
        event_bytes = json.dumps(event_dict, sort_keys=True).encode("utf-8")

        curr_rev, prev_hash = self.get_head(stream_type)
        if curr_rev != expected_revision:
            raise ExperienceStoreError(
                f"CAS mismatch on stream '{stream_id}': expected revision {expected_revision}, got {curr_rev}"
            )

        try:
            ev_rec = self._event_store.append_event(
                stream_id=stream_id,
                event_data=event_bytes,
                expected_revision=expected_revision,
                prev_event_hash=prev_hash,
            )
        except Edge1Error as e:
            raise ExperienceStoreError(f"CAS mismatch on stream '{stream_id}': {e}") from e

        return ExperienceRecord(
            stream_id=stream_id,
            revision=ev_rec.revision,
            entry_hash=ev_rec.event_hash,
            previous_hash=ev_rec.previous_event_hash,
            data_bytes=data_bytes,
            provenance=provenance,
        )

    def get_records(self, stream_type: StreamType) -> List[ExperienceRecord]:
        stream_id = stream_type.value
        head = self._event_store.get_head(stream_id)
        if head is None:
            return []
        last_rev = head[0]
        results = []
        for rev in range(1, last_rev + 1):
            ev = self._event_store.get_event(stream_id, rev)
            if ev is not None:
                raw = json.loads(ev.event_data.decode("utf-8"))
                data_bytes = bytes.fromhex(raw["data_bytes_hex"])
                prov = raw.get("provenance", {})
                results.append(
                    ExperienceRecord(
                        stream_id=ev.stream_id,
                        revision=ev.revision,
                        entry_hash=ev.event_hash,
                        previous_hash=ev.previous_event_hash,
                        data_bytes=data_bytes,
                        provenance=prov,
                    )
                )
        return results

    def verify_chain(self, stream_type: StreamType) -> bool:
        return self._event_store.verify_chain(stream_type.value)

    def replay(
        self,
        stream_type: StreamType,
        initial_state: Dict[str, Any],
        reducer_func: Callable[[Dict[str, Any], ExperienceRecord], Dict[str, Any]],
    ) -> Dict[str, Any]:
        records = self.get_records(stream_type)
        state = dict(initial_state)
        for rec in records:
            state = reducer_func(state, rec)
        return state

    def fork_what_if(
        self,
        stream_type: StreamType,
        initial_state: Dict[str, Any],
        reducer_func: Callable[[Dict[str, Any], ExperienceRecord], Dict[str, Any]],
        counterfactual_events: List[Dict[str, Any]],
    ) -> CounterfactualSimulationResult:
        """B1: What-If Engine simulation returning CounterfactualSimulationResult."""
        base_state = self.replay(stream_type, initial_state, reducer_func)
        fork_state = dict(base_state)

        fake_provenance = {k: "what_if_fork" for k in REQUIRED_PROVENANCE_FIELDS}
        for i, cf_payload in enumerate(counterfactual_events, 1):
            mock_record = ExperienceRecord(
                stream_id=f"{stream_type.value}_fork",
                revision=i,
                entry_hash=f"fork_hash_{i}",
                previous_hash="fork_prev",
                data_bytes=json.dumps(_to_canonical_payload(cf_payload)).encode("utf-8"),
                provenance=fake_provenance,
            )
            fork_state = reducer_func(fork_state, mock_record)

        _, orig_hash = canonicalize_object(_to_canonical_payload(base_state), "WHAT_IF_ENGINE_FORK")
        _, sim_hash = canonicalize_object(_to_canonical_payload(fork_state), "COUNTERFACTUAL_SIMULATION_RESULT")

        return CounterfactualSimulationResult(
            fork_id=f"fork_{int(time.time())}",
            original_state_hash=orig_hash,
            simulation_state_hash=sim_hash,
            final_state=fork_state,
            counterfactual_quality=CounterfactualQuality.CF_HIGH if len(counterfactual_events) <= 5 else CounterfactualQuality.CF_MED,
        )


# ============================================================
# B2: KNOWLEDGE SYNTHESIS & CAPABILITY GAP
# ============================================================



def evidence_threshold_threshold_met_and_budget_check_passed(ev: bool, bg: bool) -> bool:
    return ev and bg


# ============================================================
# B3: EVIDENCE LEDGER ARE-1 + EXPERIENCE STORE INTEGRATION
# ============================================================

class EvidenceExperienceBridge:
    """
    Integration: Evidence Ledger ARE-1 + Experience Store ARE-2 (B3):
    - Reuses EvidenceLedger reservation API and log_exposure
    - Derivative snapshot tracking with parent_roots
    - Zero IPC for MVP: same process, shared SQLite
    """

    def __init__(self, evidence_ledger: EvidenceLedger, experience_store: ExperienceStore):
        self.evidence_ledger = evidence_ledger
        self.experience_store = experience_store

    def record_derived_experience(
        self,
        reservation_id: str,
        stream_type: StreamType,
        payload: Dict[str, Any],
        provenance: Dict[str, Any],
        expected_revision: int,
    ) -> Tuple[ExperienceRecord, Any]:
        res = self.evidence_ledger.get_reservation(reservation_id)
        if not res:
            raise ExperienceStoreError(f"Validation reservation '{reservation_id}' not found")

        # Record exposure in Evidence Ledger
        exp_event = self.evidence_ledger.log_exposure(
            exposure_event_id=f"EXP_{int(time.time()*1000)}",
            evidence_snapshot_root_hash=res.evidence_snapshot_root_hash,
            research_program_id=res.research_program_id,
            research_family_root=res.research_family_root,
            claim_family_root=res.claim_family_root,
            research_contract_root_hash=res.research_contract_root_hash,
            candidate_or_batch_root_hash=res.candidate_batch_root_hash,
            validation_reservation_id=reservation_id,
            role=res.role,
            access_granularity="AGGREGATE_OUTCOME",
            outcome_awareness="FULL",
        )

        # Append derived payload to Experience Store
        enriched_payload = dict(payload)
        enriched_payload["parent_roots"] = {
            "evidence_snapshot": res.evidence_snapshot_root_hash,
            "research_contract": res.research_contract_root_hash,
            "exposure_event_id": exp_event.exposure_event_id,
        }

        rec = self.experience_store.append(
            stream_type=stream_type,
            payload=enriched_payload,
            provenance=provenance,
            expected_revision=expected_revision,
        )

        return rec, exp_event


# ============================================================
# C2: COMPONENT REUSE ADAPTERS
# ============================================================


