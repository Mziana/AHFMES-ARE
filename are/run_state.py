"""
AHFMES Run State Machine (§42)

Tracks run lifecycle: CREATED → RUNNING → COMPLETED/FAILED/INVALID → VERIFIED.
Prevents partial runs from being interpreted as successful.
Supports resume by checking previous state.
"""

import json
import os
import time
from enum import Enum
from typing import Dict, Optional

from are.atomic_io import atomic_write_json


class RunPhase(Enum):
    """Run lifecycle phases — never skip, never go backwards."""
    CREATED = "CREATED"
    RUNNING = " RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INVALID = "INVALID"
    VERIFIED = "VERIFIED"

    # Transitions allowed:
    # CREATED → RUNNING
    # RUNNING → COMPLETED | FAILED | INVALID
    # COMPLETED → VERIFIED
    # FAILED → (terminal, no further transitions)
    # INVALID → (terminal, no further transitions)
    # VERIFIED → (terminal, no further transitions)

    def can_transition_to(self, next_phase: "RunPhase") -> bool:
        allowed = {
            RunPhase.CREATED: {RunPhase.RUNNING},
            RunPhase.RUNNING: {RunPhase.COMPLETED, RunPhase.FAILED, RunPhase.INVALID},
            RunPhase.COMPLETED: {RunPhase.VERIFIED},
        }
        return next_phase in allowed.get(self, set())


class RunStateManager:
    """Persist and manage run lifecycle state."""

    STATE_FILE = "run_state.json"

    def __init__(self, run_dir: str):
        self.run_dir = run_dir
        self.state_path = os.path.join(run_dir, self.STATE_FILE)
        self._state: Dict = self._load()

    def _load(self) -> Dict:
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {"phase": RunPhase.CREATED.value, "stages_completed": [],
                "started_at": None, "completed_at": None, "error": None}

    def _save(self) -> None:
        os.makedirs(self.run_dir, exist_ok=True)
        atomic_write_json(self.state_path, self._state)

    @property
    def phase(self) -> RunPhase:
        return RunPhase(self._state["phase"])

    def transition(self, new_phase: RunPhase, error: Optional[str] = None) -> None:
        """Transition to new phase. Raises if transition is not allowed."""
        if not self.phase.can_transition_to(new_phase):
            raise ValueError(
                f"Invalid state transition: {self.phase.value} → {new_phase.value}"
            )
        self._state["phase"] = new_phase.value
        if new_phase == RunPhase.RUNNING:
            self._state["started_at"] = time.time()
        elif new_phase in (RunPhase.COMPLETED, RunPhase.FAILED, RunPhase.INVALID):
            self._state["completed_at"] = time.time()
        if error:
            self._state["error"] = error
        self._save()

    def mark_stage_completed(self, stage_name: str) -> None:
        """Record that a stage completed successfully."""
        if stage_name not in self._state["stages_completed"]:
            self._state["stages_completed"].append(stage_name)
            self._save()

    def is_resumable(self) -> bool:
        """Check if this run can be resumed (was RUNNING when interrupted)."""
        return self.phase == RunPhase.RUNNING

    def get_completed_stages(self) -> list:
        """Return list of stages that completed before interruption."""
        return list(self._state.get("stages_completed", []))

    def get_error(self) -> Optional[str]:
        return self._state.get("error")
