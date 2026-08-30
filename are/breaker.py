"""
AHFMES-ARE — Circuit Breaker (ported from AHFMES-CHATGPT-DEEP)

Session-peak equity circuit breaker with manual-reset entry latch.
"""

import math
from collections import deque
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CircuitBreakerResult:
    trading_allowed: bool
    halt_code: Optional[str]
    halt_reason: Optional[str]
    observed_equity: Optional[float]
    current_dd_pct: Optional[float]
    session_peak_equity: Optional[float]


class CircuitBreaker:
    """Latch entry HALT on invalid equity, insolvency, or session-peak DD."""

    def __init__(self, max_dd_pct: float = 15.0, snapshot_maxlen: int = 500):
        if not isinstance(max_dd_pct, (int, float)) or isinstance(max_dd_pct, bool):
            raise ValueError("max_dd_pct must be numeric")
        self.max_dd_pct = float(max_dd_pct)
        if not math.isfinite(self.max_dd_pct) or not 0 < self.max_dd_pct < 100:
            raise ValueError("max_dd_pct must satisfy 0 < value < 100")
        self.snapshots: deque = deque(maxlen=snapshot_maxlen)
        self.session_peak_equity: Optional[float] = None
        self._halted = False
        self._halt_code: Optional[str] = None
        self._halt_reason: Optional[str] = None

    def _latch(self, code: str, reason: str) -> None:
        if not self._halted:
            self._halted = True
            self._halt_code = code
            self._halt_reason = reason

    def update(self, equity: float, valid: bool = True, error_code: str = "") -> CircuitBreakerResult:
        observed = equity if valid else None
        dd_pct = None

        if not valid:
            self._latch("EQUITY_SOURCE_INVALID", f"Equity source invalid: {error_code}")
        else:
            self.snapshots.append(equity)
            if equity <= 0:
                if self.session_peak_equity is not None:
                    dd_pct = (self.session_peak_equity - equity) / self.session_peak_equity * 100.0
                self._latch("NONPOSITIVE_EQUITY", f"Observed equity is nonpositive: {equity}")
            else:
                if self.session_peak_equity is None or equity > self.session_peak_equity:
                    self.session_peak_equity = equity
                dd_pct = (self.session_peak_equity - equity) / self.session_peak_equity * 100.0
                if dd_pct >= self.max_dd_pct:
                    self._latch(
                        "MAX_DRAWDOWN",
                        f"Session-peak DD {dd_pct:.2f}% >= {self.max_dd_pct:.2f}%",
                    )

        return CircuitBreakerResult(
            trading_allowed=not self._halted,
            halt_code=self._halt_code,
            halt_reason=self._halt_reason,
            observed_equity=observed,
            current_dd_pct=None if dd_pct is None else round(dd_pct, 2),
            session_peak_equity=None if self.session_peak_equity is None else round(self.session_peak_equity, 2),
        )

    def reset(self):
        self._halted = False
        self._halt_code = None
        self._halt_reason = None
        self.session_peak_equity = None
        self.snapshots.clear()
