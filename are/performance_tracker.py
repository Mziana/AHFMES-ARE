"""
AHFMES-ARE — Performance Tracker (ported from AHFMES-CHATGPT-DEEP M7)

Expectancy Efficiency 60% + Consistency 40%.
"""

from typing import Dict, Any


class PerformanceTracker:
    """Expectancy Efficiency + Consistency scoring."""

    def __init__(self, theoretical_max_r: float = 2.0):
        self.theoretical_max_r = theoretical_max_r

    def compute(self, ev: Dict[str, Any]) -> float:
        n = ev.get("real_signals_seen", 0)
        if n <= 0:
            return 0.0

        wr = ev.get("real_won", 0) / max(1, n)
        exp = wr - (ev.get("real_lost", 0) / max(1, n))

        # Expectancy Efficiency: 0% at -0.5R, 100% at +2.0R
        eff = (exp + 0.5) / (self.theoretical_max_r + 0.5) * 100.0
        eff = max(0.0, min(100.0, eff))

        # Consistency: 50% WR = 0, 0% or 100% = 100
        consist = abs(wr - 0.5) * 200.0
        if n < 10:
            consist *= n / 10.0
        consist = max(0.0, min(100.0, consist))

        return round(0.60 * eff + 0.40 * consist, 2)
