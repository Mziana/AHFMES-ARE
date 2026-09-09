"""A3 — BACKWARD OOS RUN ONCE (champion frozen).

Kontrak (manifest BACKWARD-OOS-FREEZE-A1 + manifest-final 29e8084):
- Dataset: backward OOS ter-kualifikasi (hash da72f41e..., bar < 2026-07-28
  05:50Z), DISJOINT dua lapis dari training P3 (86014edf...).
- Champion PERSIS frozen: profil MICRO, scoring.mode=score (T*=60.1 dari
  kontrak H-SCORE-01 — tidak diubah), disable_gates=("b1_news","b4_location"),
  kontrak eksekusi identik C2 (BID, next-bar-open, spread sekali per crossing).
- Dua sel biaya: base (17 poin, slip 0, delay 0) + reproduksi sel wajib
  x1.5+slip2+delay0 (bukti C3).
- RUN ONCE: hasil apa adanya jadi artefak ber-hash. Tanpa tuning.

Output: data/research/backward/a3_champion_run.json
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

BACK = ROOT / "data" / "research" / "backward"
SESSION_BREAK_S = 3600
DISABLE = ("b1_news", "b4_location")
BASE_SPREAD = 17.0
BALANCE = 1136.65
TRAINING_FIRST_TS = 1785217800  # bar OOS: time < ini (konsisten A2)


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
    manifest = json.loads((ROOT / "strategy_v2" / "BACKWARD_OOS_MANIFEST.json").read_text(encoding="utf-8"))

    if qual["verdict"] != "LAYAK":
        print("FATAL: dataset OOS tidak LAYAK — A3 batal (fail-closed)")
        return 1
    dhash = qual["disjoint_check"]["oos_dataset_hash"]

    m5 = [b for b in m5_all if int(b["time"]) < TRAINING_FIRST_TS]
    m15 = [b for b in m15_all if int(b["time"]) < TRAINING_FIRST_TS]
    meta = bm.load_broker_meta(acc)
    profile = registry.load_profile("MICRO")
    reg = registry.load_hypothesis_registry()

    prof = {**profile, "scoring": {**profile["scoring"], "mode": "score"}}  # T* dari kontrak (60.1)
    chash = registry.compute_config_hash(prof, reg, calendar_artifact_hash=None,
                                         broker_meta_hash=bm.broker_meta_hash(meta))
    cfg = {"config_hash": chash, "dataset_hash": dhash, "balance": BALANCE,
           "risk_percent": prof["risk"]["risk_percent"], "spread_points": BASE_SPREAD}

    records: list[dict] = []
    n_sess = 0
    for sess in sessions(m5):
        if len(sess) < 40:
            continue
        records.extend(run_decision_replay(sess, m15, prof, reg, None, cfg, disable_gates=DISABLE))
        n_sess += 1
    signals = [r for r in records if r["decision"] in ("BUY", "SELL")]
    bq_veto = sum(1 for r in records if r["all_gate_results"]["b8_quality"] == "FAIL:score_low")

    ex_base = run_execution_replay(records, m5, prof, spread_points=BASE_SPREAD,
                                   slippage_points=0.0, delay_bars=0, broker_meta=meta,
                                   spread_label="SNAPSHOT_BACKWARD")
    ex_must = run_execution_replay(records, m5, prof, spread_points=BASE_SPREAD * 1.5,
                                   slippage_points=2.0, delay_bars=0, broker_meta=meta,
                                   spread_label="ESTIMATED_COST_MODEL")

    # Join skor ke trade (untuk bucket A4)
    score_by_ts = {}
    for r in signals:
        q = r.get("quality_score")
        if isinstance(q, dict):
            score_by_ts[int(r["evaluation_timestamp"])] = q.get("final_score")
    trades = []
    for t in ex_base["trades"]:
        trades.append({
            "signal_ts": t["signal_ts"], "direction": t["direction"],
            "entry_ts": t["entry_ts"], "exit_ts": t["exit_ts"],
            "exit_reason": t["exit_reason"], "net_usd": t["net_usd"],
            "quality_score": score_by_ts.get(int(t["signal_ts"])),
        })

    def cell(ex):
        n = ex["executed_trades"]
        return {"trades": n, "net_usd": ex["net_usd"], "exp_net": ex["expectancy_net_usd"],
                "win_rate": (sum(1 for t in ex["trades"] if t["net_usd"] > 0) / n) if n else None}

    out = {
        "artifact_id": "A3-BACKWARD-OOS-RUN-ONCE",
        "manifest_id": manifest.get("manifest_id"),
        "manifest_dataset_oos_hash": manifest.get("dataset_oos_hash"),
        "dataset_hash": dhash,
        "config_hash": chash,
        "strategy_version": registry.STRATEGY_VERSION,
        "arm_disable_gates": list(DISABLE),
        "t_star": 60.1,
        "t_star_frozen_from": "H-SCORE-01 (provenance C1 2b99583dbe563eb1)",
        "cost_model": {"base": {"spread_points": BASE_SPREAD, "slippage_points": 0, "delay_bars": 0},
                       "must": {"spread_points": BASE_SPREAD * 1.5, "slippage_points": 2, "delay_bars": 0}},
        "window_utc": {"first": qual["m5"]["first_utc"], "last": qual["m5"]["last_utc"]},
        "sessions": n_sess, "decision_records": len(records),
        "signals": len(signals), "bq_veto": bq_veto,
        "base": cell(ex_base), "must_x15_slip2": cell(ex_must),
        "trades_base": trades,
        "run_once_note": "RUN ONCE sesuai manifest — hasil apa adanya, tanpa tuning; revisi (bila perlu) hanya lewat hipotesis registry baru",
    }
    blob = json.dumps({k: v for k, v in out.items() if k != "results_hash"},
                      sort_keys=True, ensure_ascii=True)
    out["results_hash"] = hashlib.sha256(blob.encode()).hexdigest()
    (BACK / "a3_champion_run.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")

    print(f"window: {out['window_utc']['first']} .. {out['window_utc']['last']}")
    print(f"sessions={n_sess} records={len(records)} signals={len(signals)} (BQ veto={bq_veto})")
    print(f"BASE  : n={out['base']['trades']} net={out['base']['net_usd']:+.2f} "
          f"expNet={out['base']['exp_net']:+.4f} WR={out['base']['win_rate'] if out['base']['win_rate'] is None else round(out['base']['win_rate'],4)}")
    print(f"MUST  : n={out['must_x15_slip2']['trades']} net={out['must_x15_slip2']['net_usd']:+.2f} "
          f"expNet={out['must_x15_slip2']['exp_net']:+.4f}")
    print(f"results_hash: {out['results_hash'][:16]}...")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
