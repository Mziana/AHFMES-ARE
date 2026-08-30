"""
AHFMES-ARE — Habitat Memory (ported from AHFMES-CHATGPT-DEEP M4)

Persistent per-habitat memory tracking observations, evaluations, wins/losses.
Stores both real and shadow (counterfactual) outcomes separately.
"""

from typing import Any, Dict, Optional


class HabitatMemory:
    """In-memory habitat data store with optional JSON persistence."""

    def __init__(self, persistence_path: Optional[str] = None):
        self.persistence_path = persistence_path
        self.data: Dict[str, Dict[str, Any]] = {}
        if persistence_path:
            self._load()

    def _load(self):
        import json, os
        if self.persistence_path and os.path.isfile(self.persistence_path):
            try:
                with open(self.persistence_path, "r") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def _save(self):
        if self.persistence_path:
            import json
            with open(self.persistence_path, "w") as f:
                json.dump(self.data, f, indent=2, default=str)

    def _key_str(self, habitat_key) -> str:
        if isinstance(habitat_key, tuple):
            return "[" + ", ".join(str(x) for x in habitat_key) + "]"
        return str(habitat_key)

    def record_observation(
        self,
        habitat: tuple,
        session: str,
        regime: str,
        atr_state: str,
        spread_state: str,
    ):
        """Record a new observation for a habitat."""
        key = self._key_str(habitat)
        if key not in self.data:
            self.data[key] = self._fresh_entry(session, regime, atr_state, spread_state)
        else:
            ev = self.data[key]
            ev["seen_count"] = ev.get("seen_count", 0) + 1
            ev["total_evaluations"] = ev.get("total_evaluations", 0) + 1

    def record_evaluation(
        self,
        habitat: tuple,
        is_win: bool,
        r_multiple: float = 0.0,
        is_shadow: bool = False,
        direction: str = "buy",
    ):
        """Record an evaluation outcome for a habitat."""
        key = self._key_str(habitat)
        if key not in self.data:
            self.data[key] = self._fresh_entry("UNKNOWN", "UNKNOWN", "NORMAL", "NORMAL")

        ev = self.data[key]
        ev["total_evaluations"] = ev.get("total_evaluations", 0) + 1
        ev["last_update_observation"] = ev.get("total_evaluations", 0)

        if is_shadow:
            ev["shadow_signals_seen"] = ev.get("shadow_signals_seen", 0) + 1
            if is_win:
                ev["shadow_won"] = ev.get("shadow_won", 0) + 1
            else:
                ev["shadow_lost"] = ev.get("shadow_lost", 0) + 1
        else:
            ev["real_signals_seen"] = ev.get("real_signals_seen", 0) + 1
            if is_win:
                ev["real_won"] = ev.get("real_won", 0) + 1
            else:
                ev["real_lost"] = ev.get("real_lost", 0) + 1

        # Direction-aware counters
        dir_prefix = "buy" if direction == "buy" else "sell"
        eval_key = f"{dir_prefix}_eval"
        win_key = f"{dir_prefix}_win"
        suffix = "_shadow" if is_shadow else "_real"
        ev[eval_key + suffix] = ev.get(eval_key + suffix, 0) + 1
        if is_win:
            ev[win_key + suffix] = ev.get(win_key + suffix, 0) + 1

    def get_memory(self, habitat_key) -> Dict[str, Any]:
        """Get memory for a habitat."""
        key = self._key_str(habitat_key)
        return self.data.get(key, self._fresh_entry("UNKNOWN", "UNKNOWN", "NORMAL", "NORMAL"))

    def _fresh_entry(self, session, regime, atr_state, spread_state) -> Dict[str, Any]:
        return {
            "session": session,
            "regime": regime,
            "atr_state": atr_state,
            "spread_state": spread_state,
            "seen_count": 0,
            "real_signals_seen": 0,
            "real_won": 0,
            "real_lost": 0,
            "shadow_signals_seen": 0,
            "shadow_won": 0,
            "shadow_lost": 0,
            "buy_eval_real": 0,
            "buy_win_real": 0,
            "sell_eval_real": 0,
            "sell_win_real": 0,
            "buy_eval_shadow": 0,
            "buy_win_shadow": 0,
            "sell_eval_shadow": 0,
            "sell_win_shadow": 0,
            "experience_count": 0,
            "total_evaluations": 0,
            "last_update_observation": 0,
            "maturity": 0,
        }

    def rebuild_counters(self):
        """Rebuild derived counters from base data."""
        for ev in self.data.values():
            real_n = ev.get("real_signals_seen", 0)
            shadow_n = ev.get("shadow_signals_seen", 0)
            ev["seen_count"] = real_n + shadow_n
