"""
AHFMES-ARE — Direction Discovery (ported from AHFMES-CHATGPT-DEEP M16)

Buy/Sell weight computation from habitat memory. Deterministic, auditable.
"""

import math
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class DirectionResult:
    buy_weight: float
    sell_weight: float
    selected_direction: str
    reason: str


class DirectionDiscovery:
    """Compute buy/sell weights from habitat memory data."""

    SHADOW_WEIGHT = 0.25  # Virtual < Real

    def discover(self, memory_data: Dict[str, Any]) -> DirectionResult:
        """Compute direction from accumulated evidence."""
        buy_eval = memory_data.get("buy_eval_real", 0) + self.SHADOW_WEIGHT * memory_data.get("buy_eval_shadow", 0)
        buy_win = memory_data.get("buy_win_real", 0) + self.SHADOW_WEIGHT * memory_data.get("buy_win_shadow", 0)
        sell_eval = memory_data.get("sell_eval_real", 0) + self.SHADOW_WEIGHT * memory_data.get("sell_eval_shadow", 0)
        sell_win = memory_data.get("sell_win_real", 0) + self.SHADOW_WEIGHT * memory_data.get("sell_win_shadow", 0)

        # Win rates with Laplace smoothing
        buy_wr = buy_win / max(1.0, buy_eval) if buy_eval > 0 else 0.5
        sell_wr = sell_win / max(1.0, sell_eval) if sell_eval > 0 else 0.5

        buy_weight = buy_wr
        sell_weight = sell_wr

        # Selection
        EPS = 1e-9
        if abs(buy_weight - sell_weight) < EPS:
            selected = "buy"  # Default on equality
            reason = f"Equal weights ({buy_weight:.4f}), defaulting to buy"
        else:
            selected = "buy" if buy_weight > sell_weight else "sell"
            reason = f"buy_wr={buy_wr:.3f}, sell_wr={sell_wr:.3f}"

        return DirectionResult(
            buy_weight=buy_weight,
            sell_weight=sell_weight,
            selected_direction=selected,
            reason=reason,
        )
