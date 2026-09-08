"""P4 iterasi 3 — revisi H-REGIME-SLOPE-02 (budget mandat terakhir: 3/3).

Arms MICRO di dataset terkunci P3, cost model identik (spread snapshot 17 pts,
ESTIMATED_COST_MODEL, broker meta riil):
  no_b3_b4 : baseline juara iter-2 (B3 off -> long-only paksa, B4 off) — pembanding
  slope    : revisi B3 slope dua-arah (EMA20 M15), B4 off (iter-2: B4 perusak nilai)
  slope_b4 : revisi B3 slope + B4 + B5 (stack penuh dengan B3 baru)
B1 tetap DISABLED terlabel utk SEMUA arm (kalender historis per-bar tidak tersedia).

Output menimpa data/research/p4/ablation_results.json (kanonik utk P6) —
iterasi 2 diarsipkan sebagai ablation_results_iter2.json.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from strategy_v2 import registry
from p4_baseline_ablation import P3, P4, run_arm

ARMS = {
    "no_b3_b4": ("b3_regime", "b4_location"),
    "slope": ("b4_location",),
    "slope_b4": (),
}


def main() -> int:
    m5 = json.loads((P3 / "dataset_m5.json").read_text(encoding="utf-8"))["candles"]
    m15 = json.loads((P3 / "dataset_m15.json").read_text(encoding="utf-8"))["candles"]
    acc = json.loads((P3 / "account_snapshot.json").read_text(encoding="utf-8"))
    dhash = json.loads((P3 / "qualification.json").read_text(encoding="utf-8"))["dataset_hash"]

    arms = []
    for name, disable in ARMS.items():
        disable = tuple(sorted(set(disable) | {"b1_news"}))
        arm = run_arm("MICRO", disable, m5, m15, acc, dhash)
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
        "iteration": 3,
        "revision_hypotheses": ["H-REGIME-SLOPE-02", "H-SPREADCAP-03"],
        "b1_note": "B1 DISABLED terlabel utk SEMUA arm (kalender historis per-bar tidak tersedia)",
        "arms": arms,
    }
    blob = json.dumps(out, sort_keys=True, ensure_ascii=True)
    out["results_hash"] = hashlib.sha256(blob.encode()).hexdigest()
    (P4 / "ablation_results.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    print(f"\nresults_hash: {out['results_hash'][:16]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
