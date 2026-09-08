"""P5 — Cost stress grid (mandat §P5) atas arm juara P4, parameter FROZEN.

Arm: MICRO_V2, disable_gates = ("b1_news", "b3_regime", "b4_location") —
keputusan P4 (REPORT_P4.md). Decision records dihitung SEKALI (deterministik,
harus 220 sinyal = parity P4), lalu grid eksekusi:
  spread {×1.25, ×1.5, ×2.0} × slippage {0,2,5} × delay {0,1} = 18 kombinasi.

Garis lulus wajib desain: spread ×1.5 + slip 2 + delay 0 → expNet > 0.
Output: data/research/p5/cost_stress.json (ber-hash).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from strategy_v2 import broker_meta as bm
from strategy_v2 import registry
from strategy_v2.replay import run_decision_replay, run_execution_replay

P3 = ROOT / "data" / "research" / "p3"
P5 = ROOT / "data" / "research" / "p5"
SESSION_BREAK_S = 3600
DISABLE = ("b1_news", "b3_regime", "b4_location")   # FROZEN dari P4
BASE_SPREAD = 17.0                                   # poin (snapshot P3)


def sessions(m5: list) -> list[list]:
    out, cur = [], [m5[0]]
    for b in m5[1:]:
        if int(b["time"]) - int(cur[-1]["time"]) >= SESSION_BREAK_S:
            out.append(cur)
            cur = [b]
        else:
            cur.append(b)
    out.append(cur)
    return out


def main() -> int:
    m5 = json.loads((P3 / "dataset_m5.json").read_text(encoding="utf-8"))["candles"]
    m15 = json.loads((P3 / "dataset_m15.json").read_text(encoding="utf-8"))["candles"]
    acc = json.loads((P3 / "account_snapshot.json").read_text(encoding="utf-8"))
    dhash = json.loads((P3 / "qualification.json").read_text(encoding="utf-8"))["dataset_hash"]

    profile = registry.load_profile("MICRO")
    reg = registry.load_hypothesis_registry()
    meta = bm.load_broker_meta(acc)
    chash = registry.compute_config_hash(profile, reg, calendar_artifact_hash=None,
                                         broker_meta_hash=bm.broker_meta_hash(meta))
    cfg = {"config_hash": chash, "dataset_hash": dhash, "balance": 1136.65,
           "risk_percent": profile["risk"]["risk_percent"], "spread_points": BASE_SPREAD}

    records = []
    for sess in sessions(m5):
        if len(sess) < 40:
            continue
        records.extend(run_decision_replay(sess, m15, profile, reg, None, cfg,
                                           disable_gates=DISABLE))
    signals = sum(1 for r in records if r["decision"] in ("BUY", "SELL"))
    print(f"decision records: {len(records)}, signals: {signals} (parity P4: 220)")
    if signals != 220:
        print("FATAL: parity P4 pecah — identitas eksperimen berubah, P5 batal")
        return 1

    grid = []
    for smult in (1.25, 1.5, 2.0):
        for slip in (0, 2, 5):
            for delay in (0, 1):
                sp = BASE_SPREAD * smult
                ex = run_execution_replay(records, m5, profile, spread_points=sp,
                                          slippage_points=float(slip), delay_bars=delay,
                                          broker_meta=meta,
                                          spread_label="ESTIMATED_COST_MODEL")
                cell = {
                    "spread_mult": smult, "spread_points": sp,
                    "slippage_points": slip, "delay_bars": delay,
                    "executed_trades": ex["executed_trades"],
                    "rejected": len(ex["rejected_executions"]),
                    "net_usd": ex["net_usd"],
                    "expectancy_net_usd": ex["expectancy_net_usd"],
                    "expectancy_gross_usd": ex["expectancy_gross_usd"],
                    "total_costs_usd": ex["total_costs_usd"],
                }
                grid.append(cell)
                print(f"spread x{smult} ({sp:5.1f}p) slip={slip} delay={delay} -> "
                      f"trades={cell['executed_trades']:3d} net={cell['net_usd']:9.2f} "
                      f"expNet={cell['expectancy_net_usd']:+.4f}")

    must = next(c for c in grid
                if c["spread_mult"] == 1.5 and c["slippage_points"] == 2 and c["delay_bars"] == 0)
    verdict = "LULUS" if must["expectancy_net_usd"] > 0 else "GAGAL"
    out = {
        "dataset_hash": dhash, "strategy_version": registry.STRATEGY_VERSION,
        "champion_disable_gates": list(DISABLE), "signals": signals,
        "grid": grid,
        "must_pass_cell": {"spread_mult": 1.5, "slippage_points": 2, "delay_bars": 0,
                           "expectancy_net_usd": must["expectancy_net_usd"]},
        "verdict": verdict,
    }
    blob = json.dumps({k: v for k, v in out.items() if k != "results_hash"},
                      sort_keys=True, ensure_ascii=True)
    out["results_hash"] = hashlib.sha256(blob.encode()).hexdigest()
    P5.mkdir(parents=True, exist_ok=True)
    (P5 / "cost_stress.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    print(f"\nGARIS WAJIB (x1.5 + slip2 + delay0): expNet={must['expectancy_net_usd']:+.4f} -> {verdict}")
    print(f"results_hash: {out['results_hash'][:16]}…")
    return 0 if verdict == "LULUS" else 1


if __name__ == "__main__":
    sys.exit(main())
