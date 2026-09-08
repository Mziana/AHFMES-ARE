"""P4 — Baseline + Ablation (mandat §P4) di dataset_hash terkunci P3.

Arms: V2-MICRO, V2-SCALP (profil kontrak) x ablation {none, -B3, -B4, -B5, -B6}.
B1 dinonaktifkan TERLABEL (disable_gates=("b1_news",)) untuk SEMUA arm —
kalender historis per-bar tidak tersedia; seragam across arms → ablation valid.

Replay per-sesi: Layer A M5 strict pada gap → window dipotong di session break
(≥ 3600s); M15 tetap kontinu (warmup antar sesi dipertahankan). Identik dengan
kebijakan F2; funnel Pagar 6 dihitung atas seluruh bar (session break dilaporkan
terpisah, bukan hilang).

Output: data/research/p4/ablation_results.json (ber-hash) + ringkasan stdout.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from strategy_v2 import broker_meta as bm
from strategy_v2 import registry
from strategy_v2.replay import (build_funnel, run_decision_replay,
                                run_execution_replay)

P3 = ROOT / "data" / "research" / "p3"
P4 = ROOT / "data" / "research" / "p4"
BAR = 300
SESSION_BREAK_S = 3600

ABLATIONS = {
    "full": (),
    "no_b3": ("b3_regime",),
    "no_b4": ("b4_location",),
    "no_b5": ("b5_trigger",),
    "no_b6": ("b6_volume",),
    # Iterasi 2 — kombinasi kumulatif (evidence iterasi 1: B3/B4 perusak
    # nilai di MICRO, B5 bernilai; b3-off = long-only terpaksa, terlabel):
    "no_b3_b4": ("b3_regime", "b4_location"),
    "no_b3_b5": ("b3_regime", "b5_trigger"),
    "no_b4_b5": ("b4_location", "b5_trigger"),
    "no_b3_b4_b5": ("b3_regime", "b4_location", "b5_trigger"),
}
PROFILES = ("MICRO", "SCALP")


def sessions(m5: list) -> list[list]:
    """Pecah M5 di gap >= 3600s (session break)."""
    out, cur = [], [m5[0]]
    for b in m5[1:]:
        if int(b["time"]) - int(cur[-1]["time"]) >= SESSION_BREAK_S:
            out.append(cur)
            cur = [b]
        else:
            cur.append(b)
    out.append(cur)
    return out


def run_arm(profile_id: str, disable: tuple, m5: list, m15: list,
            acc: dict, dhash: str) -> dict:
    profile = registry.load_profile(profile_id)
    reg = registry.load_hypothesis_registry()
    meta = bm.load_broker_meta(acc)
    spread_pts = bm.normalize_spread(acc["ticks"]["XAUUSD"]["spread"], bm.PRICE_1E4)
    chash = registry.compute_config_hash(
        profile, reg,
        calendar_artifact_hash=None,
        broker_meta_hash=bm.broker_meta_hash(meta))
    cfg = {"config_hash": chash, "dataset_hash": dhash, "balance": 1136.65,
           "risk_percent": profile["risk"]["risk_percent"],
           "spread_points": spread_pts}

    t0 = time.time()
    records = []
    n_sessions = 0
    for sess in sessions(m5):
        if len(sess) < 40:  # sesi terlalu pendek → warmup M15 tak mungkin valid
            continue
        n_sessions += 1
        records.extend(run_decision_replay(sess, m15, profile, reg, None, cfg,
                                           disable_gates=disable))
    dt = time.time() - t0

    execution = run_execution_replay(records, m5, profile,
                                     spread_points=spread_pts,
                                     broker_meta=meta,
                                     spread_label="ESTIMATED_COST_MODEL")
    funnel = build_funnel(records, execution)
    funnel["sessions"] = n_sessions
    funnel["runtime_seconds"] = round(dt, 1)
    funnel["veto_by_gate"] = {k: v for k, v in sorted(
        funnel.get("veto_by_gate", {}).items())}
    return {"arm": f"{profile_id}:{disable or 'full'}", "profile_id": profile_id,
            "disabled": list(disable), "config_hash": chash,
            "funnel": funnel,
            "execution_summary": {k: v for k, v in execution.items()
                                  if k != "trades"},
            "n_trades_detail": len(execution["trades"])}


def main() -> int:
    m5 = json.loads((P3 / "dataset_m5.json").read_text(encoding="utf-8"))["candles"]
    m15 = json.loads((P3 / "dataset_m15.json").read_text(encoding="utf-8"))["candles"]
    acc = json.loads((P3 / "account_snapshot.json").read_text(encoding="utf-8"))
    q = json.loads((P3 / "qualification.json").read_text(encoding="utf-8"))
    dhash = q["dataset_hash"]  # TERKUNCI dari P3

    import os
    profiles = (os.environ.get("P4_PROFILES", "MICRO,SCALP").split(","))
    arms = []
    for pid in profiles:
        for name, disable in ABLATIONS.items():
            # B1 DISABLED terlabel utk SEMUA arm (kalender historis per-bar
            # tidak tersedia) — seragam across arms, ablation tetap valid.
            disable = tuple(sorted(set(disable) | {"b1_news"}))
            arm = run_arm(pid, disable, m5, m15, acc, dhash)
            arm["ablation"] = name
            arms.append(arm)
            f, e = arm["funnel"], arm["execution_summary"]
            print(f"[{arm['arm']}] sig={f['final_signals']} "
                  f"trades={f['executed_trades']} rej={f['rejected_executions']} "
                  f"net={e.get('net_usd')} expNet={e.get('expectancy_net_usd')} "
                  f"({f['runtime_seconds']}s)")

    out = {
        "dataset_hash": dhash,
        "strategy_version": registry.STRATEGY_VERSION,
        "b1_note": "B1 DISABLED terlabel utk SEMUA arm (kalender historis per-bar tidak tersedia)",
        "arms": arms,
    }
    blob = json.dumps(out, sort_keys=True, ensure_ascii=True)
    out["results_hash"] = hashlib.sha256(blob.encode()).hexdigest()
    P4.mkdir(parents=True, exist_ok=True)
    (P4 / "ablation_results.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    print(f"\nresults_hash: {out['results_hash'][:16]}…")
    return 0


if __name__ == "__main__":
    sys.exit(main())
