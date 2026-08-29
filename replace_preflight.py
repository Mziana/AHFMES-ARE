import re

with open("are/preflight.py", "r", encoding="utf-8") as f:
    content = f.read()

imports_to_add = """
import enum
from are.backtest import WFOEvidence
from are.validation import (
    validate_wfo_integrity,
    evaluate_dsr_from_evidence,
    evaluate_wfo_performance
)

class GateStatus(enum.Enum):
    INVALID = "INVALID"
    FAIL = "FAIL"
    BORDERLINE = "BORDERLINE"
    PASS = "PASS"
"""

if "class GateStatus" not in content:
    content = content.replace("import time", "import time\n" + imports_to_add)

start_idx = content.find("def audit_checkpoint_5_institutional_rigor")
end_idx = content.find("def audit_checkpoint_6_alerting_heartbeat", start_idx)

new_func = """def audit_checkpoint_5_institutional_rigor(
        self,
        strategy_logic: Optional[Callable[[pl.DataFrame], pl.DataFrame]] = None,
        wfo_evidence: Optional[WFOEvidence] = None,
    ) -> CheckpointResult:
        \"\"\"
        Checkpoint 5: Institutional Statistical Rigor & Portfolio Independence (RES-WFO-01, RES-WFO-10).
        Strictly consumer of WFOEvidence.
        \"\"\"
        try:
            if wfo_evidence is None:
                return CheckpointResult(
                    checkpoint_id=5,
                    name="Institutional Statistical Rigor & Portfolio Independence",
                    passed=False,
                    details={"gate_status": GateStatus.INVALID.value, "reason": "No WFOEvidence provided"},
                )
                
            integrity = validate_wfo_integrity(wfo_evidence)
            if not integrity.is_valid:
                return CheckpointResult(
                    checkpoint_id=5,
                    name="Institutional Statistical Rigor & Portfolio Independence",
                    passed=False,
                    details={"gate_status": GateStatus.INVALID.value, "reason": integrity.fail_reason},
                )
                
            dsr = evaluate_dsr_from_evidence(wfo_evidence)
            if not dsr.is_valid:
                return CheckpointResult(
                    checkpoint_id=5,
                    name="Institutional Statistical Rigor & Portfolio Independence",
                    passed=False,
                    details={"gate_status": GateStatus.FAIL.value, "reason": dsr.fail_reason, "dsr": dsr.dsr_value, "p_value": dsr.p_value},
                )
                
            perf = evaluate_wfo_performance(wfo_evidence)
            if not perf.is_valid:
                return CheckpointResult(
                    checkpoint_id=5,
                    name="Institutional Statistical Rigor & Portfolio Independence",
                    passed=False,
                    details={"gate_status": GateStatus.BORDERLINE.value, "reason": perf.fail_reason, "sharpe": perf.pooled_sharpe},
                )
                
            return CheckpointResult(
                checkpoint_id=5,
                name="Institutional Statistical Rigor & Portfolio Independence",
                passed=True,
                details={
                    "gate_status": GateStatus.PASS.value,
                    "dsr": round(dsr.dsr_value, 4),
                    "p_value": round(dsr.p_value, 4),
                    "sharpe": round(perf.pooled_sharpe, 4),
                    "return": round(perf.pooled_return, 4),
                    "max_drawdown": round(perf.pooled_max_dd, 4),
                },
            )
        except Exception as e:
            return CheckpointResult(
                checkpoint_id=5,
                name="Institutional Statistical Rigor & Portfolio Independence",
                passed=False,
                details={"gate_status": GateStatus.FAIL.value},
                error_message=str(e),
            )

    """

new_content = content[:start_idx] + new_func + content[end_idx:]

battery_start = new_content.find("def run_full_preflight_battery")
battery_end = new_content.find("def ", battery_start + 10)
if battery_end == -1: battery_end = len(new_content)

battery_code = new_content[battery_start:battery_end]
battery_code = battery_code.replace(
    "strategy_logic: Optional[Callable[[pl.DataFrame], pl.DataFrame]] = None,\n    ) -> Phase5PreFlightReport:",
    "strategy_logic: Optional[Callable[[pl.DataFrame], pl.DataFrame]] = None,\n        wfo_evidence: Optional[WFOEvidence] = None,\n    ) -> Phase5PreFlightReport:"
)
battery_code = battery_code.replace(
    "self.audit_checkpoint_5_institutional_rigor(strategy_logic=strategy_logic),",
    "self.audit_checkpoint_5_institutional_rigor(strategy_logic=strategy_logic, wfo_evidence=wfo_evidence),"
)

new_content = new_content[:battery_start] + battery_code + new_content[battery_end:]

with open("are/preflight.py", "w", encoding="utf-8") as f:
    f.write(new_content)