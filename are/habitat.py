"""
AHFMES ARE-3 — Habitat Adapter & Market State (Slice-2 Part D)

Implements:
- MarketStateObservation: content-addressed observation record.
- ConditionAtlas: deterministic market regime classifier (ACC-316).
- HabitatAdapter: ingests market state observations with strict Information-Time barrier (SC-03, ACC-315)
  and persists observations into EventStore.

Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Optional

from are.storage import EventStore


@dataclass(frozen=True)
class MarketStateObservation:
    observation_id: str
    symbol: str
    timestamp: float
    regime: str
    features: Dict[str, float]
    observation_hash: str = ""

    def __post_init__(self):
        if not self.observation_hash:
            canonical_payload = {
                "observation_id": self.observation_id,
                "symbol": self.symbol,
                "timestamp": self.timestamp,
                "regime": self.regime,
                "features": self.features,
            }
            raw = json.dumps(canonical_payload, sort_keys=True).encode("utf-8")
            digest = hashlib.sha256(raw).hexdigest()
            object.__setattr__(self, "observation_hash", digest)


class ConditionAtlas:
    """
    Atlas of predefined market regimes with 100% deterministic rule-based classification (ACC-316).
    """

    VALID_REGIMES: FrozenSet[str] = frozenset({
        "TRENDING_EXPANSION",
        "RANGE_COMPRESSION",
        "VOLATILITY_EXPANSION",
        "REGIME_TRANSITION",
    })

    def classify_regime(self, features: Dict[str, float]) -> str:
        """
        Deterministically classifies market features into a discrete regime.
        """
        vol = float(features.get("volatility", features.get("vol", 1.0)))
        trend = float(features.get("trend_strength", features.get("adx", 0.0)))
        range_span = float(features.get("range_span", features.get("atr_ratio", 1.0)))

        if vol >= 1.5:
            return "VOLATILITY_EXPANSION"
        elif trend >= 1.0:
            return "TRENDING_EXPANSION"
        elif range_span <= 0.5:
            return "RANGE_COMPRESSION"
        else:
            return "REGIME_TRANSITION"


class HabitatAdapter:
    """
    Adapter interfacing environment observations with Information-Time gating (SC-03, ACC-315).
    """

    def __init__(self, condition_atlas: ConditionAtlas, event_store: EventStore):
        self.condition_atlas = condition_atlas
        self.event_store = event_store

    def ingest_market_state(
        self,
        symbol: str,
        timestamp: float,
        features: Dict[str, float],
        as_of_cutoff: float,
    ) -> MarketStateObservation:
        """
        Ingests market state snapshot strictly respecting Information-Time barrier.
        Raises ValueError (fail-closed) on any future-timestamp leakage (ACC-315).
        """
        ts = float(timestamp)
        cutoff = float(as_of_cutoff)

        # 1. Information-Time Barrier (SC-03, ACC-315)
        if ts > cutoff:
            raise ValueError(
                f"Information-Time violation (SC-03): market state timestamp {ts} exceeds cutoff {cutoff}"
            )

        # 2. Condition Atlas Classification (ACC-316)
        regime = self.condition_atlas.classify_regime(features)

        # 3. Deterministic Observation Identity
        obs_id = f"OBS_{symbol}_{int(ts)}"
        obs = MarketStateObservation(
            observation_id=obs_id,
            symbol=symbol,
            timestamp=ts,
            regime=regime,
            features=features,
        )

        # 4. Append to EventStore
        stream_id = f"market_state:{symbol}"
        payload = {
            "observation_id": obs.observation_id,
            "symbol": obs.symbol,
            "timestamp": obs.timestamp,
            "regime": obs.regime,
            "features": obs.features,
            "observation_hash": obs.observation_hash,
        }
        event_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")

        head = self.event_store.get_head(stream_id)
        expected_rev = 0 if head is None else head[0]
        prev_hash = "0" * 64 if head is None else head[1]

        self.event_store.append_event(
            stream_id=stream_id,
            event_data=event_bytes,
            expected_revision=expected_rev,
            prev_event_hash=prev_hash,
        )

        return obs
