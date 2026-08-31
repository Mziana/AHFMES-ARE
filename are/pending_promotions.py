"""
AHFMES ARE — Pending Promotion Registry

When FINAL_GATE = PASS, strategies enter PENDING_HUMAN_ACK state.
Operator must explicitly approve before promotion takes effect.
This prevents fully-automated capital allocation without human review.

Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


PENDING_FILE = "data/research/pending_promotions.json"


@dataclass
class PendingPromotion:
    """A promotion waiting for human approval."""
    candidate_id: str
    champion_id: str
    gate_decision: str  # The final gate result that triggered this
    rationale: str
    disposition_hash: str
    created_at: float
    approved_at: float = 0.0
    approved_by: str = ""
    status: str = "PENDING"  # PENDING | APPROVED | REJECTED
    rejection_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PendingPromotionRegistry:
    """Manages promotions waiting for human approval."""

    def __init__(self, filepath: str = PENDING_FILE):
        self._filepath = filepath
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        self._pending: Dict[str, PendingPromotion] = self._load()

    def _load(self) -> Dict[str, PendingPromotion]:
        try:
            if os.path.exists(self._filepath):
                with open(self._filepath) as f:
                    data = json.load(f)
                return {
                    k: PendingPromotion(**v)
                    for k, v in data.items()
                }
        except Exception:
            pass
        return {}

    def _save(self):
        with open(self._filepath, "w") as f:
            json.dump(
                {k: v.to_dict() for k, v in self._pending.items()},
                f, indent=2,
            )

    def submit(
        self,
        candidate_id: str,
        champion_id: str,
        gate_decision: str,
        rationale: str,
        disposition_hash: str,
    ) -> PendingPromotion:
        """Submit a promotion for human approval."""
        promo = PendingPromotion(
            candidate_id=candidate_id,
            champion_id=champion_id,
            gate_decision=gate_decision,
            rationale=rationale,
            disposition_hash=disposition_hash,
            created_at=time.time(),
        )
        self._pending[candidate_id] = promo
        self._save()
        return promo

    def approve(self, candidate_id: str, approved_by: str = "operator") -> PendingPromotion:
        """Approve a pending promotion."""
        promo = self._pending.get(candidate_id)
        if not promo:
            raise KeyError(f"No pending promotion for {candidate_id}")
        if promo.status != "PENDING":
            raise ValueError(f"Promotion {candidate_id} already {promo.status}")
        promo.status = "APPROVED"
        promo.approved_at = time.time()
        promo.approved_by = approved_by
        self._save()
        return promo

    def reject(self, candidate_id: str, reason: str = "", rejected_by: str = "operator") -> PendingPromotion:
        """Reject a pending promotion."""
        promo = self._pending.get(candidate_id)
        if not promo:
            raise KeyError(f"No pending promotion for {candidate_id}")
        if promo.status != "PENDING":
            raise ValueError(f"Promotion {candidate_id} already {promo.status}")
        promo.status = "REJECTED"
        promo.rejection_reason = reason
        promo.approved_by = rejected_by
        self._save()
        return promo

    def get_pending(self, candidate_id: Optional[str] = None) -> List[PendingPromotion]:
        """Get pending promotions. If candidate_id given, return that one."""
        if candidate_id:
            p = self._pending.get(candidate_id)
            return [p] if p and p.status == "PENDING" else []
        return [p for p in self._pending.values() if p.status == "PENDING"]

    def get_approved_not_promoted(self) -> List[PendingPromotion]:
        """Get promotions that are APPROVED but haven't been promoted yet."""
        return [p for p in self._pending.values() if p.status == "APPROVED"]

    def is_approved(self, candidate_id: str) -> bool:
        """Check if a promotion has been approved."""
        promo = self._pending.get(candidate_id)
        return promo is not None and promo.status == "APPROVED"

    def list_all(self) -> List[PendingPromotion]:
        """List all promotions (pending, approved, rejected)."""
        return list(self._pending.values())

    def cleanup_old(self, max_age_hours: int = 168):
        """Remove rejected promotions older than max_age_hours (default: 7 days)."""
        cutoff = time.time() - (max_age_hours * 3600)
        to_remove = [
            k for k, v in self._pending.items()
            if v.status == "REJECTED" and v.created_at < cutoff
        ]
        for k in to_remove:
            del self._pending[k]
        if to_remove:
            self._save()
