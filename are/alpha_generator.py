"""
AHFMES P001 — Alpha Hypothesis Generator & Evaluator (ACC-512)

Generates quantitative trading hypotheses and evaluates signals against real-time market features.
Zero external dependencies (stdlib only: json, hashlib, typing, dataclasses).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class AlphaHypothesisSpec:
    hypothesis_id: str
    family: str  # "MOMENTUM" | "MEAN_REVERSION" | "ORDERBOOK_IMBALANCE"
    parameters: Dict[str, Any]
    signal_threshold: float
    stop_loss_pct: float
    take_profit_pct: float
    spec_hash: str = ""

    def __post_init__(self):
        if not self.spec_hash:
            canonical = {
                "hypothesis_id": self.hypothesis_id,
                "family": self.family,
                "parameters": self.parameters,
                "signal_threshold": self.signal_threshold,
                "stop_loss_pct": self.stop_loss_pct,
                "take_profit_pct": self.take_profit_pct,
            }
            raw = json.dumps(canonical, sort_keys=True).encode("utf-8")
            digest = hashlib.sha256(raw).hexdigest()
            object.__setattr__(self, "spec_hash", digest)


class AlphaGenerator:
    """Generates structured alpha hypotheses and evaluates quantitative trade signals."""

    SUPPORTED_FAMILIES = ("MOMENTUM", "MEAN_REVERSION", "ORDERBOOK_IMBALANCE")

    def generate_hypotheses(
        self,
        symbol: str,
        family: Optional[str] = None,
        count: int = 5,
    ) -> List[AlphaHypothesisSpec]:
        """
        Deterministically produces candidate AlphaHypothesisSpec instances.
        """
        families = [family.upper()] if family and family.upper() in self.SUPPORTED_FAMILIES else list(self.SUPPORTED_FAMILIES)
        results: List[AlphaHypothesisSpec] = []

        idx = 0
        while len(results) < count:
            target_family = families[idx % len(families)]
            seq = (idx // len(families)) + 1
            hyp_id = f"ALPHA_{symbol}_{target_family}_{seq:03d}"

            if target_family == "MOMENTUM":
                params = {
                    "fast_period": 5 + (seq * 2),
                    "slow_period": 20 + (seq * 5),
                    "velocity_weight": 0.5 + (seq * 0.1),
                }
                sig_thresh = 0.001 * seq
                sl = 0.02
                tp = 0.05
            elif target_family == "MEAN_REVERSION":
                params = {
                    "zscore_entry": 1.8 + (seq * 0.2),
                    "zscore_exit": 0.5,
                    "window": 20 + (seq * 5),
                }
                sig_thresh = 1.8 + (seq * 0.2)
                sl = 0.015
                tp = 0.03
            else:  # ORDERBOOK_IMBALANCE
                params = {
                    "imbalance_threshold": 0.25 + (seq * 0.05),
                    "max_spread_pct": 0.001,
                    "depth_levels": 5 + seq,
                }
                sig_thresh = 0.25 + (seq * 0.05)
                sl = 0.01
                tp = 0.02

            spec = AlphaHypothesisSpec(
                hypothesis_id=hyp_id,
                family=target_family,
                parameters=params,
                signal_threshold=sig_thresh,
                stop_loss_pct=sl,
                take_profit_pct=tp,
            )
            results.append(spec)
            idx += 1

        return results

    def evaluate_alpha_signal(
        self,
        hypothesis: AlphaHypothesisSpec,
        features: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Evaluates a market feature vector against a specific AlphaHypothesisSpec.
        Returns trade decision dict with action, confidence, and internal scores.
        """
        family = hypothesis.family
        action = "HOLD"
        confidence = 0.0
        score = 0.5

        if family == "MOMENTUM":
            crossover = features.get("crossover_diff", 0.0)
            velocity = features.get("price_velocity", 0.0)
            combined_signal = crossover + velocity

            if combined_signal > hypothesis.signal_threshold:
                action = "BUY"
                confidence = min(1.0, 0.6 + abs(combined_signal) * 10.0)
                score = 0.85 + (confidence * 0.1)
            elif combined_signal < -hypothesis.signal_threshold:
                action = "SELL"
                confidence = min(1.0, 0.6 + abs(combined_signal) * 10.0)
                score = 0.85 + (confidence * 0.1)

        elif family == "MEAN_REVERSION":
            zscore = features.get("zscore", 0.0)
            if zscore <= -hypothesis.signal_threshold:
                action = "BUY"
                confidence = min(1.0, 0.7 + (abs(zscore) - hypothesis.signal_threshold) * 0.2)
                score = 0.88 + (confidence * 0.1)
            elif zscore >= hypothesis.signal_threshold:
                action = "SELL"
                confidence = min(1.0, 0.7 + (abs(zscore) - hypothesis.signal_threshold) * 0.2)
                score = 0.88 + (confidence * 0.1)

        elif family == "ORDERBOOK_IMBALANCE":
            imbalance = features.get("imbalance_ratio", 0.0)
            if imbalance >= hypothesis.signal_threshold:
                action = "BUY"
                confidence = min(1.0, 0.65 + abs(imbalance) * 0.3)
                score = 0.86 + (confidence * 0.1)
            elif imbalance <= -hypothesis.signal_threshold:
                action = "SELL"
                confidence = min(1.0, 0.65 + abs(imbalance) * 0.3)
                score = 0.86 + (confidence * 0.1)

        return {
            "hypothesis_id": hypothesis.hypothesis_id,
            "family": hypothesis.family,
            "action": action,
            "confidence": confidence,
            "score": score,
            "features_evaluated": features,
        }
