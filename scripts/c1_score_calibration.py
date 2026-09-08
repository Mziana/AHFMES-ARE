"""C1 — Score calibration (Cognitive Layer v2.1, H-SCORE-01): threshold DARI DATA.

Prinsip (desain v2.1 + pelajaran P6): threshold tidak dipilih a priori (55/65/75
dokumen asli ditolak) — diturunkan dari kurva eks ekusi di dataset terkunci P3:

1. Decision replay arm champion P4 iter-3 (MICRO, disable b1_news+b4_location,
   B3 slope aktif) dengan scoring mode ON + threshold NULL — BQ mencatat skor,
   tidak memveto. Parity wajib: 199 sinyal (identik P5).
2. Kurva deskriptif: trade champion di-join ke skor sinyalnya (signal_ts) →
   expNet per desil skor.
3. Kurva KAUSAL (sumber T*): sweep threshold — record di bawah T di-blank ke
   WAIT (persis semantik veto BQ live) → run_execution_replay pada DUA sel
   biaya: base (17/slip0/delay0) dan garis wajib desain (×1.5/slip2/delay0).
4. T* = threshold TERENDAH (paling sedikit memangkas trade) yang memenuhi:
   expNet_base > 0 DAN expNet_must(×1.5+slip2) > 0 AND trades >= 30.
   Tidak ada kandidat → verdict NO_VIABLE_THRESHOLD (abort jujur, kembali ke
   owner) — TANPA memilih threshold "yang paling tidak buruk".

Multiple-testing jujur: n_trials_evaluated dicatat di artefak (bahan koreksi
DSR di C4). Output: data/research/c1/score_calibration.json (ber-hash).
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
OUT = ROOT / "data" / "research" / "c1"
SESSION_BREAK_S = 3600
DISABLE = ("b1_news", "b4_location")   # FROZEN champion P4 iter-3 (arm `slope`)
PARITY_SIGNALS = 199
BASE_SPREAD = 17.0
MIN_TRADES = 30
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


def pct(sorted_vals: list, p: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * p / 100.0
    f, c = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def main() -> int:
    m5 = json.loads((P3 / "dataset_m5.json").read_text(encoding="utf-8"))["candles"]
    m15 = json.loads((P3 / "dataset_m15.json").read_text(encoding="utf-8"))["candles"]
    acc = json.loads((P3 / "account_snapshot.json").read_text(encoding="utf-8"))
    dhash = json.loads((P3 / "qualification.json").read_text(encoding="utf-8"))["dataset_hash"]

    profile = registry.load_profile("MICRO")
    # Virtual profile: scoring ON, threshold NULL (C0/C1: skor dicatat, tanpa veto)
    profile_v = {**profile, "scoring": {**profile["scoring"], "mode": "on"}}
    reg = registry.load_hypothesis_registry()
    meta = bm.load_broker_meta(acc)
    chash = registry.compute_config_hash(profile_v, reg, calendar_artifact_hash=None,
                                         broker_meta_hash=bm.broker_meta_hash(meta))
    cfg = {"config_hash": chash, "dataset_hash": dhash, "balance": BALANCE,
           "risk_percent": profile_v["risk"]["risk_percent"], "spread_points": BASE_SPREAD}

    records: list[dict] = []
    for sess in sessions(m5):
        if len(sess) < 40:
            continue
        records.extend(run_decision_replay(sess, m15, profile_v, reg, None, cfg,
                                           disable_gates=DISABLE))
    signals = [r for r in records if r["decision"] in ("BUY", "SELL")]
    scores = [r["quality_score"]["final_score"] for r in signals
              if isinstance(r.get("quality_score"), dict)]
    n_score_error = sum(1 for r in signals if not isinstance(r.get("quality_score"), dict))
    print(f"records={len(records)} signals={len(signals)} scored={len(scores)} "
          f"score_error={n_score_error}")
    if len(signals) != PARITY_SIGNALS:
        print(f"FATAL: parity pecah ({len(signals)} != {PARITY_SIGNALS}) — identitas eksperimen berubah, C1 batal")
        return 1
    if n_score_error:
        print(f"FATAL: {n_score_error} sinyal tanpa skor (fail-closed) — C1 batal")
        return 1

    # ── Kurva deskriptif: desil skor atas trade champion (base cost) ──────────
    ex_base = run_execution_replay(records, m5, profile_v, spread_points=BASE_SPREAD,
                                   slippage_points=0.0, delay_bars=0, broker_meta=meta,
                                   spread_label="SNAPSHOT_P3")
    score_by_ts = {r["evaluation_timestamp"]: r["quality_score"]["final_score"]
                   for r in signals}
    trade_rows = [(score_by_ts[t["signal_ts"]], t["net_usd"], t["exit_reason"])
                  for t in ex_base["trades"] if t["signal_ts"] in score_by_ts]
    decile_curve = []
    ss = sorted(scores)
    for i in range(10):
        lo = pct(ss, i * 10.0)
        hi = pct(ss, (i + 1) * 10.0)
        rows = [x for x in trade_rows if (lo <= x[0] < hi) or (i == 9 and lo <= x[0] <= hi)]
        n = len(rows)
        decile_curve.append({
            "decile": i + 1, "score_lo": round(lo, 2), "score_hi": round(hi, 2),
            "n_trades": n,
            "exp_net_usd": round(sum(x[1] for x in rows) / n, 4) if n else None,
            "win_rate": round(sum(1 for x in rows if x[1] > 0) / n, 4) if n else None,
        })
    print("\ndesil skor -> expNet (deskriptif, trade champion):")
    for d in decile_curve:
        print(f"  D{d['decile']:2d} [{d['score_lo']:6.2f},{d['score_hi']:6.2f}] "
              f"n={d['n_trades']:3d} expNet={d['exp_net_usd']}")

    # ── Kurva kausal: sweep threshold, blank→WAIT, dua sel biaya ──────────────
    grid = sorted({round(pct(ss, p), 1) for p in
                   (0, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95)})
    cells = []
    for T in grid:
        filt = [dict(r, decision="WAIT") if
                (r["decision"] in ("BUY", "SELL") and r["quality_score"]["final_score"] < T)
                else r for r in records]
        kept = sum(1 for r in filt if r["decision"] in ("BUY", "SELL"))
        eb = run_execution_replay(filt, m5, profile_v, spread_points=BASE_SPREAD,
                                  slippage_points=0.0, delay_bars=0, broker_meta=meta,
                                  spread_label="SNAPSHOT_P3")
        em = run_execution_replay(filt, m5, profile_v, spread_points=BASE_SPREAD * 1.5,
                                  slippage_points=2.0, delay_bars=0, broker_meta=meta,
                                  spread_label="ESTIMATED_COST_MODEL")
        cells.append({
            "threshold": T, "signals_kept": kept,
            "trades_base": eb["executed_trades"], "exp_net_base": eb["expectancy_net_usd"],
            "trades_must": em["executed_trades"], "exp_net_must": em["expectancy_net_usd"],
        })
        print(f"T={T:6.1f} kept={kept:3d} base: n={eb['executed_trades']:3d} "
              f"expNet={eb['expectancy_net_usd']:+.4f} | must x1.5+slip2: "
              f"n={em['executed_trades']:3d} expNet={em['expectancy_net_usd']:+.4f}")

    viable = [c for c in cells
              if c["exp_net_base"] > 0 and c["exp_net_must"] > 0
              and c["trades_base"] >= MIN_TRADES and c["trades_must"] >= MIN_TRADES]
    if viable:
        t_star = min(viable, key=lambda c: c["threshold"])
        verdict = "T_FOUND"
    else:
        t_star = None
        verdict = "NO_VIABLE_THRESHOLD"

    out = {
        "dataset_hash": dhash,
        "strategy_version": registry.STRATEGY_VERSION,
        "arm_disable_gates": list(DISABLE),
        "scoring": {"mode": "on", "threshold_null": True},
        "config_hash": chash,
        "signals": len(signals),
        "score_stats": {
            "min": ss[0], "p25": pct(ss, 25), "median": pct(ss, 50),
            "p75": pct(ss, 75), "max": ss[-1],
        },
        "descriptive_decile_curve": decile_curve,
        "causal_threshold_curve": cells,
        "n_trials_evaluated": len(cells),   # bahan koreksi multiple-testing C4
        "selected_threshold": t_star["threshold"] if t_star else None,
        "selection_rule": "lowest T with exp_net_base>0 AND exp_net_must>0 AND trades>=30",
        "verdict": verdict,
    }
    blob = json.dumps({k: v for k, v in out.items() if k != "results_hash"},
                      sort_keys=True, ensure_ascii=True)
    out["results_hash"] = hashlib.sha256(blob.encode()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "score_calibration.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    print(f"\nVERDICT: {verdict}"
          + (f" | T* = {t_star['threshold']} (kept={t_star['signals_kept']})" if t_star else
             " — tidak ada rentang skor positif di kedua sel biaya; kembali ke owner"))
    print(f"results_hash: {out['results_hash'][:16]}…")
    return 0 if t_star else 1


if __name__ == "__main__":
    sys.exit(main())
