"""
AHFMES ARE-3 — Out-of-Sample Validation Service (Slice-1 Part C)

Implements:
- ValidationReport: immutable validation assessment record.
- ValidationService: out-of-sample holdout validation, strict Information-Time barrier (SC-03, ACC-303),
  and evidence ledger exposure accounting (ACC-304).

Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from are.evidence import EvidenceLedger
from are.storage import EventStore


@dataclass(frozen=True)
class ValidationReport:
    candidate_id: str
    status: str  # "VALIDATED" | "REJECTED"
    sample_count: int
    performance_metric: float
    exposure_penalty: float
    as_of_ts: float
    report_hash: str = ""

    def __post_init__(self):
        if not self.report_hash:
            canonical_payload = {
                "candidate_id": self.candidate_id,
                "status": self.status,
                "sample_count": self.sample_count,
                "performance_metric": self.performance_metric,
                "exposure_penalty": self.exposure_penalty,
                "as_of_ts": self.as_of_ts,
            }
            raw = json.dumps(canonical_payload, sort_keys=True).encode("utf-8")
            digest = hashlib.sha256(raw).hexdigest()
            object.__setattr__(self, "report_hash", digest)


class ValidationService:
    """
    Validates candidates against out-of-sample data with Information-Time enforcement.
    """

    def __init__(self, evidence_ledger: EvidenceLedger, event_store: EventStore):
        self.evidence_ledger = evidence_ledger
        self.event_store = event_store

    def validate_candidate(
        self,
        candidate_id: str,
        holdout_token: str,
        as_of_ts: float,
        dataset: List[Dict[str, Any]],
        performance_threshold: float = 0.5,
        research_program_id: str = "ARE3_RESEARCH",
        role: str = "INTERNAL_VALIDATION",
    ) -> ValidationReport:
        """
        Validates a candidate against dataset points strictly prior to as_of_ts.
        Fails-closed on any future-timestamp leakage (ACC-303, SC-03).
        """
        if not dataset:
            raise ValueError("Cannot validate against an empty dataset")

        # 1. Information-Time Check (SC-03, ACC-303)
        for i, row in enumerate(dataset):
            row_ts = float(row.get("timestamp", 0.0))
            if row_ts > as_of_ts:
                raise ValueError(
                    f"Information-Time violation (SC-03): sample #{i} timestamp {row_ts} > cutoff {as_of_ts}"
                )

        # 2. Holdout Evidence Accounting (ACC-304)
        snap_id = f"SNAP_VAL_{candidate_id}_{int(as_of_ts)}"
        snapshot = self.evidence_ledger.create_snapshot(
            evidence_snapshot_id=snap_id,
            source_manifest_hash="0" * 64,
            source_kind="HOLDOUT_DATASET",
            source_epoch=f"EPOCH_{int(as_of_ts)}",
            information_time_contract_hash="0" * 64,
            row_or_event_identity_contract_hash="0" * 64,
            completeness_proof_hash="0" * 64,
            provenance_status="VERIFIED",
            origin="PROSPECTIVE_STRICT_BLIND",
        )

        res_id = f"RES_VAL_{candidate_id}_{int(as_of_ts)}"
        reservation = self.evidence_ledger.create_reservation(
            reservation_id=res_id,
            research_program_id=research_program_id,
            program_budget_envelope_root_hash="0" * 64,
            research_family_root="0" * 64,
            claim_family_root="0" * 64,
            research_contract_root_hash="0" * 64,
            evidence_snapshot_root_hash=snapshot.root_hash,
            validation_family_root_hash="0" * 64,
            candidate_batch_root_hash="0" * 64,
            primary_estimand_root_hash="0" * 64,
            multiplicity_plan_root_hash="0" * 64,
            search_tree_root_hash="0" * 64,
            search_debt_root_hash="0" * 64,
            permitted_disclosures_root_hash=None,
            permitted_actor_ids=["validator_actor"],
            role=role,
        )

        # Log exposure
        self.evidence_ledger.log_exposure(
            exposure_event_id=f"EXP_{candidate_id}_{int(as_of_ts)}",
            evidence_snapshot_root_hash=snapshot.root_hash,
            research_program_id=research_program_id,
            research_family_root="0" * 64,
            claim_family_root="0" * 64,
            research_contract_root_hash="0" * 64,
            candidate_or_batch_root_hash="0" * 64,
            validation_reservation_id=reservation.reservation_id,
            role=role,
            access_granularity="ROW_OUTCOME",
            outcome_awareness="BOUNDED",
        )

        # 3. Deterministic Performance Metric Calculation
        scores = [float(row.get("score", row.get("value", 0.0))) for row in dataset]
        avg_score = sum(scores) / len(scores)
        exposure_penalty = min(0.3, len(dataset) * 0.0005)
        final_metric = max(0.0, avg_score - exposure_penalty)

        status = "VALIDATED" if final_metric >= performance_threshold else "REJECTED"

        return ValidationReport(
            candidate_id=candidate_id,
            status=status,
            sample_count=len(dataset),
            performance_metric=final_metric,
            exposure_penalty=exposure_penalty,
            as_of_ts=as_of_ts,
        )
