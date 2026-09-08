"""C2 — Head-to-head: champion SCORER (BQ T* FROZEN 60.1) vs champion BINARY.

Dataset, biaya, arm dasar (disable b1_news+b4_location), dan kontrak eksekusi
IDENTIK dengan P4 iter-3 — satu-satunya perbedaan: BQ aktif dan memveto skor
< T*. Dua pertanyaan (dua kriteria lulus independen):
  1. Efisiensi biaya: expNet scorer (base) > expNet binary (base)?
     (skorer memangkas trade buruk pada biaya yang sama — ukuran utama)
  2. Sel wajib: expNet scorer (x1.5+slip2) > 0?
     (bila binary gagal sel ini — terbukti di P5 — scorer boleh lulus via
     jalur ini tanpa harus mengungguli di base)
Output: data/research/c2/scorer_vs_binary.json (ber-hash).
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
OUT = ROOT / "data" / "research" / "c2"
SESSION_BREAK_S = 3600
DISABLE = ("b1_news", "b4_location")
T_STAR = 60.1                 # FROZEN dari C1 (provenance H-SCORE-01) — TIDAK diubah di sini
BASE_SPREAD = 17.0
BALANCE = 1136.65


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


def run_arm(m5, m15, profile, reg, meta, dhash, scoring_mode: str):
    prof = dict(profile)
    if scoring_mode == "score":
        prof = {**prof, "scoring": {**prof["scoring"], "mode": "score"}}  # T* dari kontrak (60.1)
    chash = registry.compute_config_hash(prof, reg, calendar_artifact_hash=None,
                                         broker_meta_hash=bm.broker_meta_hash(meta))
    cfg = {"config_hash": chash, "dataset_hash": dhash, "balance": BALANCE,
           "risk_percent": prof["risk"]["risk_percent"], "spread_points": BASE_SPREAD}
    records: list[dict] = []
    for sess in sessions(m5):
        if len(sess) < 40:
            continue
        records.extend(run_decision_replay(sess, m15, prof, reg, None, cfg,
                                           disable_gates=DISABLE))
    signals = sum(1 for r in records if r["decision"] in ("BUY", "SELL"))
    ex_base = run_execution_replay(records, m5, prof, spread_points=BASE_SPREAD,
                                   slippage_points=0.0, delay_bars=0, broker_meta=meta,
                                   spread_label="SNAPSHOT_P3")
    ex_must = run_execution_replay(records, m5, prof, spread_points=BASE_SPREAD * 1.5,
                                   slippage_points=2.0, delay_bars=0, broker_meta=meta,
                                   spread_label="ESTIMATED_COST_MODEL")
    return {
        "mode": scoring_mode, "signals": signals,
        "base": {"trades": ex_base["executed_trades"], "net_usd": ex_base["net_usd"],
                 "exp_net": ex_base["expectancy_net_usd"],
                 "win_rate": (sum(1 for t in ex_base["trades"] if t["net_usd"] > 0)
                              / ex_base["executed_trades"]) if ex_base["executed_trades"] else None},
        "must_x15_slip2": {"trades": ex_must["executed_trades"], "net_usd": ex_must["net_usd"],
                           "exp_net": ex_must["expectancy_net_usd"]},
        "_records": records, "_ex_base": ex_base,
    }


def main() -> int:
    m5 = json.loads((P3 / "dataset_m5.json").read_text(encoding="utf-8"))["candles"]
    m15 = json.loads((P3 / "dataset_m15.json").read_text(encoding="utf-8"))["candles"]
    acc = json.loads((P3 / "account_snapshot.json").read_text(encoding="utf-8"))
    dhash = json.loads((P3 / "qualification.json").read_text(encoding="utf-8"))["dataset_hash"]

    profile = registry.load_profile("MICRO")
    reg = registry.load_hypothesis_registry()
    meta = bm.load_broker_meta(acc)

    binary = run_arm(m5, m15, profile, reg, meta, dhash, "off")
    scorer = run_arm(m5, m15, profile, reg, meta, dhash, "score")

    n_veto = sum(1 for r in scorer["_records"]
                 if r["all_gate_results"]["b8_quality"] == "FAIL:score_low")
    print(f"BINARY : signals={binary['signals']} | base n={binary['base']['trades']} "
          f"expNet={binary['base']['exp_net']:+.4f} | must n={binary['must_x15_slip2']['trades']} "
          f"expNet={binary['must_x15_slip2']['exp_net']:+.4f}")
    print(f"SCORER : signals={scorer['signals']} (BQ veto={n_veto}) | "
          f"base n={scorer['base']['trades']} expNet={scorer['base']['exp_net']:+.4f} "
          f"WR={scorer['base']['win_rate']:.3f} | must n={scorer['must_x15_slip2']['trades']} "
          f"expNet={scorer['must_x15_slip2']['exp_net']:+.4f}")

    crit_eff = scorer["base"]["exp_net"] > binary["base"]["exp_net"]
    crit_must = scorer["must_x15_slip2"]["exp_net"] > 0
    verdict = "SCORER_MENANG" if (crit_eff and crit_must) else \
              "SCORER_LULUS_MUST_ONLY" if crit_must else "GAGAL"

    trades = [{"signal_ts": t["signal_ts"], "direction": t["direction"],
               "entry_ts": t["entry_ts"], "exit_ts": t["exit_ts"],
               "exit_reason": t["exit_reason"], "net_usd": t["net_usd"]}
              for t in scorer["_ex_base"]["trades"]]
    out = {
        "dataset_hash": dhash, "strategy_version": registry.STRATEGY_VERSION,
        "arm_disable_gates": list(DISABLE), "t_star": T_STAR,
        "t_star_frozen_from": "data/research/c1/score_calibration.json (2b99583dbe563eb1)",
        "binary": {k: v for k, v in binary.items() if not k.startswith("_")},
        "scorer": {k: v for k, v in scorer.items() if not k.startswith("_")},
        "scorer_trades_base": trades,
        "criteria": {"efficiency_base": crit_eff, "must_cell_positive": crit_must},
        "verdict": verdict,
    }
    blob = json.dumps({k: v for k, v in out.items() if k != "results_hash"},
                      sort_keys=True, ensure_ascii=True)
    out["results_hash"] = hashlib.sha256(blob.encode()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "scorer_vs_binary.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    print(f"\nVERDICT: {verdict} (efisiensi_base={crit_eff}, sel_wajib={crit_must})")
    print(f"results_hash: {out['results_hash'][:16]}…")
    return 0 if crit_must else 1


if __name__ == "__main__":
    sys.exit(main())
