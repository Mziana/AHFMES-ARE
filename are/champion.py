"""
AHFMES ARE-3 — Champion Registry (Slice-3 Part A)

Implements:
- ChampionRecord: immutable champion metadata container.
- ChampionRegistry: manages succession, promotion gating against verified PromotionDisposition (ACC-324),
  and historical rollback of active champions (ACC-325) using EventStore stream "champion_registry".

Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from are.governor import PromotionDisposition
from are.storage import EventStore


@dataclass(frozen=True)
class ChampionRecord:
    champion_id: str
    candidate_id: str
    promotion_disposition_hash: str
    activated_at: float
    status: str  # "ACTIVE" | "SUPERSEDED" | "ROLLED_BACK"
    record_hash: str = ""

    def __post_init__(self):
        if not self.record_hash:
            canonical_repr = {
                "champion_id": self.champion_id,
                "candidate_id": self.candidate_id,
                "promotion_disposition_hash": self.promotion_disposition_hash,
                "activated_at": self.activated_at,
                "status": self.status,
            }
            raw = json.dumps(canonical_repr, sort_keys=True).encode("utf-8")
            digest = hashlib.sha256(raw).hexdigest()
            object.__setattr__(self, "record_hash", digest)


class ChampionRegistry:
    """
    Registry managing champion lifecycle, promotions, and rollbacks on EventStore stream "champion_registry".
    """

    STREAM_ID = "champion_registry"

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    def _get_history(self) -> List[Dict[str, Any]]:
        head = self.event_store.get_head(self.STREAM_ID)
        if head is None:
            return []

        history = []
        for rev in range(1, head[0] + 1):
            ev = self.event_store.get_event(self.STREAM_ID, rev)
            if ev is not None:
                history.append(json.loads(ev.event_data.decode("utf-8")))
        return history

    def get_active_champion(self) -> Optional[ChampionRecord]:
        """
        Reconstructs active champion from committed stream history (ACC-323).
        """
        history = self._get_history()
        active_champ: Optional[ChampionRecord] = None

        for event in history:
            ev_type = event.get("type")
            if ev_type == "PROMOTED":
                active_champ = ChampionRecord(
                    champion_id=event["champion_id"],
                    candidate_id=event["candidate_id"],
                    promotion_disposition_hash=event["promotion_disposition_hash"],
                    activated_at=float(event["activated_at"]),
                    status="ACTIVE",
                )
            elif ev_type == "ROLLED_BACK":
                restored_id = event.get("restored_champion_id")
                if restored_id:
                    # Find restored champion record details
                    for prev_ev in history:
                        if prev_ev.get("champion_id") == restored_id and prev_ev.get("type") == "PROMOTED":
                            active_champ = ChampionRecord(
                                champion_id=prev_ev["champion_id"],
                                candidate_id=prev_ev["candidate_id"],
                                promotion_disposition_hash=prev_ev["promotion_disposition_hash"],
                                activated_at=float(event["timestamp"]),
                                status="ACTIVE",
                            )
                            break
                else:
                    active_champ = None

        return active_champ

    def list_champion_lineage(self) -> List[ChampionRecord]:
        """
        Returns full succession lineage of all champions recorded in the stream.
        """
        history = self._get_history()
        records: List[ChampionRecord] = []
        for ev in history:
            if ev.get("type") == "PROMOTED":
                records.append(
                    ChampionRecord(
                        champion_id=ev["champion_id"],
                        candidate_id=ev["candidate_id"],
                        promotion_disposition_hash=ev["promotion_disposition_hash"],
                        activated_at=float(ev["activated_at"]),
                        status=ev.get("status", "SUPERSEDED"),
                    )
                )
        return records

    def promote_champion(
        self,
        candidate_id: str,
        promotion_disposition: PromotionDisposition,
    ) -> ChampionRecord:
        """
        Promotes a candidate to Champion status after rigorous verification of PromotionDisposition (ACC-324).
        """
        # 1. Verification of Promotion Authority
        if promotion_disposition.decision != "PROMOTED":
            raise ValueError(
                f"Unauthorized promotion attempt: disposition decision is '{promotion_disposition.decision}', expected 'PROMOTED' (ACC-324)"
            )
        if not promotion_disposition.governor_signature:
            raise ValueError("Unauthorized promotion attempt: missing governor cryptographic signature")
        if promotion_disposition.candidate_id != candidate_id:
            raise ValueError(
                f"Unauthorized promotion attempt: candidate mismatch '{candidate_id}' != '{promotion_disposition.candidate_id}'"
            )

        ts = promotion_disposition.timestamp
        champion_id = f"CHAMP_{candidate_id}_{int(ts)}"

        event_payload = {
            "type": "PROMOTED",
            "champion_id": champion_id,
            "candidate_id": candidate_id,
            "promotion_disposition_hash": promotion_disposition.disposition_hash,
            "activated_at": ts,
            "status": "ACTIVE",
        }
        event_bytes = json.dumps(event_payload, sort_keys=True).encode("utf-8")

        head = self.event_store.get_head(self.STREAM_ID)
        expected_rev = 0 if head is None else head[0]
        prev_hash = "0" * 64 if head is None else head[1]

        self.event_store.append_event(
            stream_id=self.STREAM_ID,
            event_data=event_bytes,
            expected_revision=expected_rev,
            prev_event_hash=prev_hash,
        )

        return ChampionRecord(
            champion_id=champion_id,
            candidate_id=candidate_id,
            promotion_disposition_hash=promotion_disposition.disposition_hash,
            activated_at=ts,
            status="ACTIVE",
        )

    def rollback_champion(self, reason: str, timestamp: Optional[float] = None) -> Optional[ChampionRecord]:
        """
        Rolls back the current active champion to previous champion version (ACC-325).
        """
        active_champ = self.get_active_champion()
        if active_champ is None:
            raise ValueError("No active champion available to rollback")

        ts = time.time() if timestamp is None else float(timestamp)

        # Find previous champion in lineage
        lineage = self.list_champion_lineage()
        prev_champ: Optional[ChampionRecord] = None

        for champ in reversed(lineage):
            if champ.champion_id != active_champ.champion_id:
                prev_champ = champ
                break

        event_payload = {
            "type": "ROLLED_BACK",
            "rolled_back_champion_id": active_champ.champion_id,
            "restored_champion_id": prev_champ.champion_id if prev_champ else None,
            "reason": reason,
            "timestamp": ts,
        }
        event_bytes = json.dumps(event_payload, sort_keys=True).encode("utf-8")

        head = self.event_store.get_head(self.STREAM_ID)
        expected_rev = 0 if head is None else head[0]
        prev_hash = "0" * 64 if head is None else head[1]

        self.event_store.append_event(
            stream_id=self.STREAM_ID,
            event_data=event_bytes,
            expected_revision=expected_rev,
            prev_event_hash=prev_hash,
        )

        if prev_champ:
            return ChampionRecord(
                champion_id=prev_champ.champion_id,
                candidate_id=prev_champ.candidate_id,
                promotion_disposition_hash=prev_champ.promotion_disposition_hash,
                activated_at=ts,
                status="ACTIVE",
            )
        return None
