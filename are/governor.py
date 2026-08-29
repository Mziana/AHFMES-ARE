"""
AHFMES ARE-3 — Critic & Governor Engine (Slice-1 Part D)

Implements:
- PromotionDisposition: immutable record of promotion decision.
- CriticEngine: adversarial evaluation comparing Challenger against Champion (SC-14, ACC-306).
- GovernorEngine: strict Separation of Duties (SoD) gatekeeper (SC-01, SC-02, G16, G17, ACC-305)
  and cryptographic promotion authority.

Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from are.validation import ValidationReport


@dataclass(frozen=True)
class PromotionDisposition:
    candidate_id: str
    champion_id: str
    decision: str  # "PROMOTED" | "DISMISSED"
    rationale: str
    governor_signature: str
    timestamp: float
    disposition_hash: str = ""

    def __post_init__(self):
        if not self.disposition_hash:
            canonical_payload = {
                "candidate_id": self.candidate_id,
                "champion_id": self.champion_id,
                "decision": self.decision,
                "rationale": self.rationale,
                "governor_signature": self.governor_signature,
                "timestamp": self.timestamp,
            }
            raw = json.dumps(canonical_payload, sort_keys=True).encode("utf-8")
            digest = hashlib.sha256(raw).hexdigest()
            object.__setattr__(self, "disposition_hash", digest)


class CriticEngine:
    """
    Adversarial evaluation comparing Challenger against Champion under stress conditions (SC-14, ACC-306).
    """

    def evaluate_adversarial(
        self,
        challenger_metrics: Dict[str, Any],
        champion_metrics: Dict[str, Any],
        stress_factor: float = 1.0,
    ) -> bool:
        """
        Evaluates whether Challenger demonstrably outperforms Champion under stress.
        """
        if stress_factor <= 0.0:
            raise ValueError(f"Stress factor must be positive: {stress_factor}")

        challenger_perf = float(challenger_metrics.get("performance", challenger_metrics.get("score", 0.0)))
        champion_perf = float(champion_metrics.get("performance", champion_metrics.get("score", 0.0)))

        challenger_drawdown = float(challenger_metrics.get("drawdown", challenger_metrics.get("risk", 0.0)))
        champion_drawdown = float(champion_metrics.get("drawdown", champion_metrics.get("risk", 0.0)))

        # Adjusted score under stress factor
        challenger_adj = (challenger_perf / stress_factor) - (challenger_drawdown * stress_factor * 0.1)
        champion_adj = champion_perf - (champion_drawdown * 0.1)

        return challenger_adj > champion_adj


class GovernorEngine:
    """
    Governor authority enforcing Separation of Duties and promotion gating (SC-01, SC-02, G16, G17).
    """

    def __init__(self, secret_key: str = "GOVERNOR_AUTHORITY_KEY_ARE3"):
        self.secret_key = secret_key

    def verify_sod(
        self,
        creator_principal: str,
        validator_principal: str,
        promoter_principal: str,
    ) -> None:
        """
        Enforces strict Separation of Duties (SC-01, SC-02, G16, G17, ACC-305).
        Creator, Validator, and Promoter must all be distinct principals.
        """
        if not creator_principal or not validator_principal or not promoter_principal:
            raise ValueError("All authority principals (creator, validator, promoter) must be specified")

        principals = {
            "creator": creator_principal,
            "validator": validator_principal,
            "promoter": promoter_principal,
        }

        if len(set(principals.values())) < 3:
            raise ValueError(
                f"Separation of Duties (SoD) violation: creator='{creator_principal}', "
                f"validator='{validator_principal}', promoter='{promoter_principal}' cannot overlap."
            )

    def evaluate_promotion(
        self,
        candidate_id: str,
        champion_id: str,
        validation_report: ValidationReport,
        critic_passed: bool,
        creator_principal: str,
        validator_principal: str,
        promoter_principal: str,
        current_ts: Optional[float] = None,
        statistical_robustness: Optional[tuple[bool, str]] = None,
        candidate_dsr_p_value: Optional[float] = None,
        candidate_psr: Optional[float] = None,
        crisis_survival: Optional[bool] = None,
        crisis_metrics: Optional[Dict[str, Any]] = None,
    ) -> PromotionDisposition:
        """
        Evaluates promotion of a Candidate to replace Champion.
        Fails-closed if SoD is violated, validation is rejected, critic fails,
        statistical robustness fails, DSR p_value >= 0.05, PSR < 0.95, or crisis survival fails.
        """
        # 1. Enforce Separation of Duties
        self.verify_sod(creator_principal, validator_principal, promoter_principal)

        ts = time.time() if current_ts is None else float(current_ts)

        # 2. Gate Evaluation
        is_validated = validation_report.status == "VALIDATED"
        stat_passed = True
        stat_reason = ""
        if statistical_robustness is not None:
            stat_passed, stat_reason = statistical_robustness

        dsr_passed = True
        if candidate_dsr_p_value is not None and candidate_dsr_p_value >= 0.05:
            dsr_passed = False

        psr_passed = True
        if candidate_psr is not None and candidate_psr < 0.95:
            psr_passed = False

        crisis_passed = True
        if crisis_survival is False or (crisis_metrics is not None and not crisis_metrics.get("survival_bool", True)):
            crisis_passed = False

        if is_validated and critic_passed and stat_passed and dsr_passed and psr_passed and crisis_passed:
            decision = "PROMOTED"
            rationale = (
                f"Candidate '{candidate_id}' passed out-of-sample validation "
                f"(metric={validation_report.performance_metric:.4f}) and defeated "
                f"Champion '{champion_id}' in adversarial critic evaluation."
            )
        else:
            decision = "DISMISSED"
            reasons = []
            if not is_validated:
                reasons.append(f"validation status is {validation_report.status}")
            if not critic_passed:
                reasons.append("critic adversarial evaluation failed")
            if not stat_passed:
                reasons.append(f"statistical robustness validation failed ({stat_reason})")
            if not dsr_passed:
                reasons.append(f"REJECTED: DEFLATED_SHARPE_INSUFFICIENT (p_value={candidate_dsr_p_value:.4f} >= 0.05)")
            if not psr_passed:
                reasons.append(f"REJECTED: PROBABILISTIC_SHARPE_INSUFFICIENT (PSR={candidate_psr:.4f} < 0.95)")
            if not crisis_passed:
                reasons.append("REJECTED: CRISIS_REPLAY_BANKRUPTCY (failed Black Swan survival threshold)")
            rationale = (
                f"Candidate '{candidate_id}' dismissed against Champion '{champion_id}': "
                + "; ".join(reasons)
                + "."
            )

        # 3. Cryptographic Signature
        sig_body = f"{candidate_id}:{champion_id}:{decision}:{ts:.2f}:{promoter_principal}"
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            sig_body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return PromotionDisposition(
            candidate_id=candidate_id,
            champion_id=champion_id,
            decision=decision,
            rationale=rationale,
            governor_signature=signature,
            timestamp=ts,
        )
