"""
AHFMES P001 — Rich Terminal ANSI/ASCII Operational Dashboard (ACC-501)

Stdlib only (sys, os, time, json).
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, Optional


def format_dashboard(
    champion_info: Dict[str, Any],
    safety_info: Dict[str, Any],
    stream_stats: Dict[str, Any],
    is_live_mode: bool = False,
) -> str:
    """
    Renders a formatted ASCII/ANSI terminal status dashboard.
    """
    now_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    mode_str = "LIVE / EMULATED" if is_live_mode else "STANDALONE / RESEARCH"

    # Extract champion info
    champ_id = champion_info.get("champion_id", "NONE (GENESIS)")
    cand_id = champion_info.get("candidate_id", "N/A")
    status = champion_info.get("status", "ACTIVE")
    activated_at = champion_info.get("activated_at", 0.0)
    act_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(activated_at)) if activated_at > 0 else "N/A"

    # Extract safety info
    kill_switch = safety_info.get("kill_switch_active", False)
    ks_status = "[ACTIVE - TRADING BLOCKED]" if kill_switch else "[INACTIVE - NORMAL]"
    max_dd = safety_info.get("max_drawdown_pct", 0.15) * 100.0
    vol_cutoff = safety_info.get("volatility_cutoff", 2.5)
    max_rate = safety_info.get("max_order_rate_per_min", 10)

    # Extract stream stats
    total_ticks = stream_stats.get("total_ticks", 0)
    veto_count = stream_stats.get("veto_count", 0)
    veto_ratio = (veto_count / total_ticks * 100.0) if total_ticks > 0 else 0.0
    chain_health = stream_stats.get("chain_health", "VERIFIED")

    lines = [
        "=" * 72,
        f"  AHFMES-ARE RECURSIVE AUTONOMOUS ENGINE — OPERATIONAL DASHBOARD",
        f"  Time: {now_str} | Mode: {mode_str}",
        "=" * 72,
        " [1] ACTIVE CHAMPION REGISTRY",
        f"     • Champion ID    : {champ_id}",
        f"     • Candidate ID   : {cand_id}",
        f"     • Status         : {status}",
        f"     • Activated At   : {act_str}",
        "-" * 72,
        " [2] CAPITAL SAFETY KERNEL (CSK) FIREWALL",
        f"     • Kill Switch    : {ks_status}",
        f"     • Max Drawdown   : {max_dd:.1f}%",
        f"     • Volatility Cut : {vol_cutoff:.2f} sigma",
        f"     • Rate Limit     : {max_rate} orders/min",
        "-" * 72,
        " [3] OPERATIONAL STREAMS & LEDGER HEALTH",
        f"     • Operational Ticks: {total_ticks}",
        f"     • Veto/Regret Events: {veto_count} ({veto_ratio:.1f}%)",
        f"     • Chain Integrity   : {chain_health}",
        "=" * 72,
    ]
    return "\n".join(lines)


class TerminalDashboard:
    """Dashboard renderer fetching live state from registries & stores."""

    def render(
        self,
        champion_registry: Any,
        safety_kernel: Any,
        event_store: Any,
        stream_id: str = "operational_signals",
    ) -> str:
        # 1. Champion info
        champ = champion_registry.get_active_champion()
        champ_info = {
            "champion_id": champ.champion_id if champ else "NONE (GENESIS)",
            "candidate_id": champ.candidate_id if champ else "N/A",
            "status": champ.status if champ else "INACTIVE",
            "activated_at": champ.activated_at if champ else 0.0,
        }

        # 2. Safety info
        limits = safety_kernel.limits
        safety_info = {
            "kill_switch_active": limits.kill_switch_active,
            "max_drawdown_pct": limits.max_drawdown_pct,
            "volatility_cutoff": limits.volatility_cutoff,
            "max_order_rate_per_min": limits.max_order_rate_per_min,
        }

        # 3. Stream stats
        head = event_store.get_head(stream_id)
        total_ticks = head[0] if head is not None else 0
        veto_count = 0

        if head is not None:
            for rev in range(1, head[0] + 1):
                ev = event_store.get_event(stream_id, rev)
                if ev:
                    try:
                        d = json.loads(ev.event_data.decode("utf-8"))
                        if d.get("final_action") in ("ABSTAIN", "EMERGENCY_FLAT") or d.get("safety_decision", {}).get("allowed") is False:
                            veto_count += 1
                    except Exception:
                        pass

        chain_ok = event_store.verify_chain(stream_id) if total_ticks > 0 else True
        stream_stats = {
            "total_ticks": total_ticks,
            "veto_count": veto_count,
            "chain_health": "VERIFIED (OK)" if chain_ok else "CORRUPTED (FAIL)",
        }

        return format_dashboard(champ_info, safety_info, stream_stats)

    def print_dashboard(
        self,
        champion_registry: Any,
        safety_kernel: Any,
        event_store: Any,
        stream_id: str = "operational_signals",
    ) -> None:
        text = self.render(champion_registry, safety_kernel, event_store, stream_id)
        print(text)
