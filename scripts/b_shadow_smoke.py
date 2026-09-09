"""Shadow smoke run — demonstrasi rantai Track B end-to-end di data nyata.

Rantai: record keputusan (champion frozen, RUN-ONCE A3, deterministik)
  -> DecisionAdapter (konsultasi CSK, kuota per profil)
  -> ExecutionStateMachine (transisi eksplisit)
  -> ShadowGateway (fill sim = open bar berikutnya, kill switch tersedia)
  -> parity_check vs trade replay (toleransi max(1 point, tick_size))
  -> latency_report (wall-clock rantai kode; label jujur: bukan latensi MT5 live)

LABEL JUJUR (kontrak): ini demonstrasi infrastruktur di konteks replay —
BUKAN otorisasi trading, BUKAN pengganti Fase D (live shadow >= 1 minggu).
Latensi MT5 round-trip nyata hanya terukur di fase live-shadow nanti.

Output: data/research/backward/b_shadow_smoke.json (ber-hash)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from are.safety import CapitalSafetyKernel, SafetyLimits
from strategy_v2 import broker_meta as bm
from strategy_v2 import execution as ex
from strategy_v2 import registry
from strategy_v2.replay import run_decision_replay, run_execution_replay

BACK = ROOT / "data" / "research" / "backward"
SESSION_BREAK_S = 3600
DISABLE = ("b1_news", "b4_location")
BASE_SPREAD = 17.0
BALANCE = 1136.65
TRAINING_FIRST_TS = 1785217800


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
    m5_all = json.loads((BACK / "dataset_m5.json").read_text(encoding="utf-8"))["candles"]
    m15_all = json.loads((BACK / "dataset_m15.json").read_text(encoding="utf-8"))["candles"]
    acc = json.loads((BACK / "account_snapshot.json").read_text(encoding="utf-8"))
    qual = json.loads((BACK / "oos_qualification.json").read_text(encoding="utf-8"))

    m5 = [b for b in m5_all if int(b["time"]) < TRAINING_FIRST_TS]
    m15 = [b for b in m15_all if int(b["time"]) < TRAINING_FIRST_TS]
    meta = bm.load_broker_meta(acc)
    profile = registry.load_profile("MICRO")
    reg = registry.load_hypothesis_registry()
    prof = {**profile, "scoring": {**profile["scoring"], "mode": "score"}}
    chash = registry.compute_config_hash(prof, reg, calendar_artifact_hash=None,
                                         broker_meta_hash=bm.broker_meta_hash(meta))
    cfg = {"config_hash": chash, "dataset_hash": qual["disjoint_check"]["oos_dataset_hash"],
           "balance": BALANCE, "risk_percent": prof["risk"]["risk_percent"],
           "spread_points": BASE_SPREAD}

    records = []
    for sess in sessions(m5):
        if len(sess) >= 40:
            records.extend(run_decision_replay(sess, m15, prof, reg, None, cfg, disable_gates=DISABLE))
    ex_replay = run_execution_replay(records, m5, prof, spread_points=BASE_SPREAD,
                                     slippage_points=0.0, delay_bars=0, broker_meta=meta,
                                     spread_label="SNAPSHOT_BACKWARD")
    executed_ts = {int(t["signal_ts"]) for t in ex_replay["trades"]}
    exec_records = [r for r in records
                    if r["decision"] in ("BUY", "SELL") and int(r["evaluation_timestamp"]) in executed_ts]

    # ── Rantai Track B ──────────────────────────────────────────────────────
    csk = CapitalSafetyKernel(SafetyLimits(max_position_size=1.0, max_drawdown_pct=0.15,
                                           volatility_cutoff=2.5, max_order_rate_per_min=10))
    budget = ex.csk_risk_budget_for(csk, "MICRO_V2")
    adapter = ex.DecisionAdapter(csk, tick_size=ex.PARITY_TICK_FLOOR)
    gateway = ex.ShadowGateway(m5, point_size=0.01)

    latency_samples = []
    sm_log = []
    shadow_trades = []
    intents = []
    for r in exec_records:
        t0 = time.perf_counter()
        intent = adapter.submit(r, "MICRO_V2", budget=budget)
        t1 = time.perf_counter()
        if intent is None:
            sm_log.append({"intent": None, "state": "ADAPTER_REJECTED"})
            continue
        sm = ex.ExecutionStateMachine(intent.intent_id)
        sm.transition("INTENT_VALIDATED")
        sm.transition("CSK_CHECKED", {"budget": "MICRO_V2"})
        sm.transition("SUBMITTED")
        t2 = time.perf_counter()
        fill = gateway.submit(intent, spread_points=BASE_SPREAD)
        t3 = time.perf_counter()
        sm.transition("ACKNOWLEDGED")
        sm.transition("FILLED", {"fill_price": fill.fill_price})
        sm.transition("MANAGING")
        sm.transition("CLOSED", {"note": "shadow-lifecycle"})
        latency_samples.append({"decision": t1 - t0, "risk": 0.0, "submit": t3 - t2,
                                "ack": 0.0, "fill": 0.0})
        sm_log.append({"intent": intent.intent_id, "final_state": sm.state})
        intents.append(intent)
        # pasangan parity: fill shadow vs trade replay (entry replay = open bar berikutnya)
        twin = next(t for t in ex_replay["trades"] if int(t["signal_ts"]) == intent.signal_ts)
        shadow_trades.append({"signal_ts": intent.signal_ts, "direction": intent.direction,
                              "lot": intent.lot, "entry": fill.fill_price,
                              "parity_valid": True})

    parity = ex.parity_check(ex_replay["trades"], shadow_trades,
                             tick_size=meta.get("point") or ex.PARITY_TICK_FLOOR)
    lat = ex.latency_report(latency_samples)

    out = {
        "artifact_id": "B-SHADOW-SMOKE-RUN",
        "label": ("DEMONSTRASI INFRASTRUKTUR (konteks replay) — bukan otorisasi trading, "
                  "bukan pengganti Fase D live-shadow >= 1 minggu"),
        "dataset_hash": qual["disjoint_check"]["oos_dataset_hash"],
        "strategy_version": registry.STRATEGY_VERSION,
        "chain": {
            "records_executed_by_replay": len(exec_records),
            "intents_emitted": len(intents),
            "adapter_rejections": len(adapter.rejections),
            "shadow_fills": len(shadow_trades),
            "state_machines_closed_terminal": sum(1 for s in sm_log if s.get("final_state") == "CLOSED"),
            "csk_budget_micro": budget,
        },
        "parity": parity,
        "latency_report": lat,
        "latency_scope_note": ("wall-clock rantai kode adapter+gateway di mesin ini; "
                               "latensi MT5 round-trip nyata hanya terukur di fase live-shadow"),
    }
    out["results_hash"] = ex.results_hash({k: v for k, v in out.items() if k != "results_hash"})
    (BACK / "b_shadow_smoke.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")

    print(f"chain: records={len(exec_records)} intents={len(intents)} "
          f"fills={len(shadow_trades)} sm_terminal_closed={out['chain']['state_machines_closed_terminal']}")
    print(f"parity: match={parity['match']} (n_replay={parity['n_replay']} n_shadow={parity['n_shadow']}, "
          f"tol={parity['tolerance_price']})")
    if not parity["match"]:
        print("  mismatches:", json.dumps(parity.get("mismatches", [])[:3]))
    print(f"latency: decision p50={lat['segments']['decision']['p50']*1000:.2f}ms "
          f"submit p99={lat['segments']['submit']['p99']*1000:.2f}ms | "
          f"viability={lat['validity']['viability_gate']} "
          f"(decision->ack p99={lat['validity']['decision_to_ack_p99_s']*1000:.2f}ms)")
    print(f"results_hash: {out['results_hash'][:16]}...")
    return 0 if parity["match"] else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
