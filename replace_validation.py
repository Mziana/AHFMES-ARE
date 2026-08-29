import hashlib
import json

with open("are/validation.py", "r", encoding="utf-8") as f:
    content = f.read()

import_str = "from are.storage import EventStore\n"
if import_str in content:
    content = content.replace(import_str, import_str + "from are.backtest import WFOEvidence\n")

new_code = """
@dataclass(frozen=True)
class WFOIntegrityResult:
    is_valid: bool
    fail_reason: Optional[str]
    overlap_count: int

@dataclass(frozen=True)
class DSRResult:
    is_valid: bool
    fail_reason: Optional[str]
    dsr_value: float
    p_value: float

@dataclass(frozen=True)
class PerformanceResult:
    is_valid: bool
    fail_reason: Optional[str]
    pooled_sharpe: float
    pooled_return: float
    pooled_max_dd: float

def validate_wfo_integrity(evidence: WFOEvidence) -> WFOIntegrityResult:
    overlap_count = 0
    for i in range(len(evidence.folds) - 1):
        if evidence.folds[i].oos_end_ts >= evidence.folds[i+1].oos_start_ts:
            overlap_count += 1
            
    if overlap_count > 0:
        return WFOIntegrityResult(is_valid=False, fail_reason=f"OOS overlap detected between {overlap_count} folds", overlap_count=overlap_count)
        
    data_dict = {
        "folds": [
            {
                "winner_params": f.winner_params,
                "oos_sharpe": f.oos_metrics.get("sharpe_ratio", 0.0)
            } for f in evidence.folds
        ],
        "pooled_sharpe": evidence.pooled_oos_sharpe
    }
    import hashlib
    import json
    calculated_hash = hashlib.sha256(json.dumps(data_dict, sort_keys=True).encode()).hexdigest()
    if calculated_hash != evidence.provenance_hash:
        return WFOIntegrityResult(is_valid=False, fail_reason="Provenance hash mismatch", overlap_count=0)
        
    return WFOIntegrityResult(is_valid=True, fail_reason=None, overlap_count=0)

def evaluate_dsr_from_evidence(evidence: WFOEvidence) -> DSRResult:
    sr = evidence.pooled_oos_sharpe
    trials = evidence.evaluation_count
    n_obs = len(evidence.pooled_oos_returns)
    if trials < 1: trials = 1
    if n_obs < 2: 
        return DSRResult(is_valid=False, fail_reason="Not enough OOS observations", dsr_value=0.0, p_value=1.0)
    
    dsr_val, p_val = calculate_deflated_sharpe_ratio(
        observed_sharpe=sr,
        num_trials=trials,
        num_observations=n_obs
    )
    
    is_valid = p_val < 0.05
    fail_reason = None if is_valid else f"DSR p-value {p_val:.4f} >= 0.05"
    return DSRResult(is_valid=is_valid, fail_reason=fail_reason, dsr_value=dsr_val, p_value=p_val)

def evaluate_wfo_performance(evidence: WFOEvidence) -> PerformanceResult:
    is_valid = True
    fail_reason = []
    
    if evidence.pooled_oos_sharpe < 1.0:
        is_valid = False
        fail_reason.append(f"Sharpe {evidence.pooled_oos_sharpe:.2f} < 1.0")
        
    if evidence.pooled_oos_return <= 0.0:
        is_valid = False
        fail_reason.append("Negative or zero total return")
        
    if evidence.pooled_oos_max_drawdown >= 0.20:
        is_valid = False
        fail_reason.append(f"Max DD {evidence.pooled_oos_max_drawdown:.2f} >= 20%")
        
    return PerformanceResult(
        is_valid=is_valid,
        fail_reason="; ".join(fail_reason) if fail_reason else None,
        pooled_sharpe=evidence.pooled_oos_sharpe,
        pooled_return=evidence.pooled_oos_return,
        pooled_max_dd=evidence.pooled_oos_max_drawdown
    )
"""

if "class WFOIntegrityResult" not in content:
    content = content + "\n" + new_code

with open("are/validation.py", "w", encoding="utf-8") as f:
    f.write(content)