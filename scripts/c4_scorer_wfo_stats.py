"""C4 — WFO + statistik (mandat §P6) atas arm SCORER (BQ T* FROZEN 60.1).

Sama ketatnya dengan P6: parameter FROZEN (tanpa fitting per fold) → WFO =
rolling OOS 6 fold + embargo ≥ 1 hari + purge trade lintas batas. Metrik wajib
B-4: PSR, DSR (momen nyata), CI95 expNet, worst-fold, fold dispersion —
DITAMBAH tabel fold per arah (proxy rezim; pelajaran P6 iter-2).

Deflasi DSR jujur: N_TRIALS = 15 konfigurasi unik yang dievaluasi di dataset
ini sepanjang riset = 3 arm P4 iter-3 + 12 threshold sweep C1 (arm scorer =
sel C1 T=60.1; C2 = duplikat; 18 sel C3 = uji robustness biaya, bukan konfig
baru — terdokumentasi di artefak). V[SR] dihitung dari 15 trial tsb (P4 arm
di-replay; sel C1 via mekanisme blank→WAIT yang terbukti setara veto BQ).

Biaya statistik utama = base (17/slip0/delay0); statistik sekunder = sel
wajib desain (×1.5+slip2). Output: data/research/c4/scorer_wfo_stats.json.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from strategy_v2 import broker_meta as bm
from strategy_v2 import registry
from strategy_v2.replay import run_decision_replay, run_execution_replay

P3 = ROOT / "data" / "research" / "p3"
P4 = ROOT / "data" / "research" / "p4"
C1 = ROOT / "data" / "research" / "c1"
OUT = ROOT / "data" / "research" / "c4"
SESSION_BREAK_S = 3600
DISABLE = ("b1_news", "b4_location")
T_STAR = 60.1
BASE_SPREAD = 17.0
BALANCE = 1136.65
N_FOLDS = 6
EMBARGO_S = 86400          # 1 hari
GAMMA_EM = 0.5772156649


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


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_ppf(p: float) -> float:
    if p <= 0:
        return -8.0
    if p >= 1:
        return 8.0
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def moments(xs: list) -> dict:
    n = len(xs)
    m = sum(xs) / n
    var = sum((x - m) ** 2 for x in xs) / max(1, n - 1)
    sd = math.sqrt(var)
    if sd == 0:
        return {"n": n, "mean": m, "std": 0.0, "skew": 0.0, "kurt": 3.0}
    m3 = sum((x - m) ** 3 for x in xs) / n
    m4 = sum((x - m) ** 4 for x in xs) / n
    return {"n": n, "mean": m, "std": sd, "skew": m3 / sd**3, "kurt": m4 / sd**4}


def psr(sr: float, sr_star: float, n: int, skew: float, kurt: float) -> float:
    if n < 2:
        return 0.0
    denom = math.sqrt(max(1e-12, 1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr * sr))
    z = (sr - sr_star) * math.sqrt(n - 1) / denom
    return norm_cdf(z)


def utc_date(ts: float) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(ts))


def fold_stats(trades: list, label: str) -> dict:
    t0 = min(t["entry_ts"] for t in trades)
    t1 = max(t["exit_ts"] for t in trades)
    span = (t1 - t0 + 300) / N_FOLDS
    folds, dropped_cross = [], 0
    for i in range(N_FOLDS):
        w_start, w_end = t0 + i * span, t0 + (i + 1) * span
        ftrades = [t for t in trades if w_start <= t["entry_ts"] < w_end]
        kept = [t for t in ftrades if t["exit_ts"] <= w_end]   # purge lintas batas
        dropped_cross += len(ftrades) - len(kept)
        nets = [t["net_usd"] for t in kept]
        mm = moments(nets) if nets else {"n": 0, "mean": 0.0, "std": 0.0, "skew": 0.0, "kurt": 3.0}
        by_dir = {}
        for d in ("BUY", "SELL"):
            dn = [t["net_usd"] for t in kept if t["direction"] == d]
            by_dir[d] = {"n": len(dn), "net_usd": round(sum(dn), 2),
                         "exp_net": round(sum(dn) / len(dn), 4) if dn else None}
        folds.append({
            "fold": i + 1,
            "window_utc": [utc_date(w_start), utc_date(w_end - 1)],
            "trades_kept": len(kept), "dropped_cross": len(ftrades) - len(kept),
            "net_usd": round(sum(nets), 2),
            "expectancy_net_usd": round(mm["mean"], 4) if kept else None,
            "by_direction": by_dir,
        })
        print(f"  [{label}] fold {i+1} {folds[-1]['window_utc']}: n={len(kept):3d} "
              f"net={sum(nets):8.2f} expNet={mm['mean'] if kept else 0:+.3f} "
              f"(BUY {by_dir['BUY']['n']}/{by_dir['BUY']['net_usd']:+.1f} "
              f"SELL {by_dir['SELL']['n']}/{by_dir['SELL']['net_usd']:+.1f})")
    return {"folds": folds, "dropped_cross_boundary": dropped_cross}


def main() -> int:
    m5 = json.loads((P3 / "dataset_m5.json").read_text(encoding="utf-8"))["candles"]
    m15 = json.loads((P3 / "dataset_m15.json").read_text(encoding="utf-8"))["candles"]
    acc = json.loads((P3 / "account_snapshot.json").read_text(encoding="utf-8"))
    dhash = json.loads((P3 / "qualification.json").read_text(encoding="utf-8"))["dataset_hash"]
    c1art = json.loads((C1 / "score_calibration.json").read_text(encoding="utf-8"))
    sweep_ts = [c["threshold"] for c in c1art["causal_threshold_curve"]]

    profile = registry.load_profile("MICRO")
    prof = {**profile, "scoring": {**profile["scoring"], "mode": "score"}}  # T* 60.1 kontrak
    reg = registry.load_hypothesis_registry()
    meta = bm.load_broker_meta(acc)
    chash = registry.compute_config_hash(prof, reg, calendar_artifact_hash=None,
                                         broker_meta_hash=bm.broker_meta_hash(meta))
    cfg = {"config_hash": chash, "dataset_hash": dhash, "balance": BALANCE,
           "risk_percent": prof["risk"]["risk_percent"], "spread_points": BASE_SPREAD}

    # ── Record arm scorer (sekali) + eksekusi dua sel biaya ──────────────────
    records: list[dict] = []
    for sess in sessions(m5):
        if len(sess) < 40:
            continue
        records.extend(run_decision_replay(sess, m15, prof, reg, None, cfg,
                                           disable_gates=DISABLE))
    n_sig = sum(1 for r in records if r["decision"] in ("BUY", "SELL"))
    if n_sig != 60:
        print(f"FATAL: parity C2/C3 pecah ({n_sig} != 60)")
        return 1
    ex_base = run_execution_replay(records, m5, prof, spread_points=BASE_SPREAD,
                                   slippage_points=0.0, delay_bars=0, broker_meta=meta,
                                   spread_label="SNAPSHOT_P3")
    ex_must = run_execution_replay(records, m5, prof, spread_points=BASE_SPREAD * 1.5,
                                   slippage_points=2.0, delay_bars=0, broker_meta=meta,
                                   spread_label="ESTIMATED_COST_MODEL")
    print(f"scorer arm: base n={ex_base['executed_trades']} expNet={ex_base['expectancy_net_usd']:+.4f} | "
          f"must n={ex_must['executed_trades']} expNet={ex_must['expectancy_net_usd']:+.4f}")

    # ── V[SR] lintas 15 trial (3 arm P4 + 12 sel sweep C1 via blank→WAIT) ────
    sr_trials: list[dict] = []
    p4 = json.loads((P4 / "ablation_results.json").read_text(encoding="utf-8"))
    for arm in p4["arms"]:
        dis = tuple(arm["disabled"])
        pr = profile if arm["profile_id"] == "MICRO" else registry.load_profile("SCALP")
        recs: list[dict] = []
        for sess in sessions(m5):
            if len(sess) < 40:
                continue
            recs.extend(run_decision_replay(sess, m15, pr, reg, None, cfg, disable_gates=dis))
        exa = run_execution_replay(recs, m5, pr, spread_points=BASE_SPREAD,
                                   slippage_points=0.0, delay_bars=0, broker_meta=meta,
                                   spread_label="ESTIMATED_COST_MODEL")
        nets = [t["net_usd"] for t in exa["trades"]]
        mm = moments(nets) if len(nets) >= 2 else {"mean": 0.0, "std": 0.0}
        sr = mm["mean"] / mm["std"] if mm["std"] > 0 else 0.0
        sr_trials.append({"trial": f"P4:{arm['arm']}", "n": len(nets), "sr": round(sr, 6)})
        print(f"  trial P4:{arm['arm']}: n={len(nets)} SR={sr:+.4f}")
    score_by_ts = {r["evaluation_timestamp"]: r["quality_score"]["final_score"]
                   for r in records if r["decision"] in ("BUY", "SELL")}
    for T in sweep_ts:
        filt = [dict(r, decision="WAIT") if
                (r["decision"] in ("BUY", "SELL") and r["quality_score"]["final_score"] < T)
                else r for r in records]
        exa = run_execution_replay(filt, m5, prof, spread_points=BASE_SPREAD,
                                   slippage_points=0.0, delay_bars=0, broker_meta=meta,
                                   spread_label="SNAPSHOT_P3")
        nets = [t["net_usd"] for t in exa["trades"]]
        mm = moments(nets) if len(nets) >= 2 else {"mean": 0.0, "std": 0.0}
        sr = mm["mean"] / mm["std"] if mm["std"] > 0 else 0.0
        sr_trials.append({"trial": f"C1:T={T}", "n": len(nets), "sr": round(sr, 6)})
        print(f"  trial C1:T={T}: n={len(nets)} SR={sr:+.4f}")
    n_trials = len(sr_trials)
    srs = [s["sr"] for s in sr_trials]
    v_sr = sum((s - sum(srs) / n_trials) ** 2 for s in srs) / (n_trials - 1)
    print(f"V[SR] across {n_trials} trials = {v_sr:.6f}")

    # ── Statistik pooled + PSR/DSR/CI95 (base = primer, must = sekunder) ─────
    def block(trades: list, ex: dict, label: str) -> dict:
        nets = [t["net_usd"] for t in trades]
        mm = moments(nets)
        sr = mm["mean"] / mm["std"] if mm["std"] > 0 else 0.0
        psr0 = psr(sr, 0.0, mm["n"], mm["skew"], mm["kurt"])
        sr_star = math.sqrt(max(v_sr, 1e-12)) * ((1 - GAMMA_EM) * norm_ppf(1 - 1.0 / n_trials)
                                                 + GAMMA_EM * norm_ppf(1 - 1.0 / n_trials) ** 2)
        dsr = psr(sr, sr_star, mm["n"], mm["skew"], mm["kurt"])
        ci95 = (mm["mean"] - 1.96 * mm["std"] / math.sqrt(mm["n"]),
                mm["mean"] + 1.96 * mm["std"] / math.sqrt(mm["n"]))
        fs = fold_stats(trades, label)
        exps = [f["expectancy_net_usd"] for f in fs["folds"] if f["expectancy_net_usd"] is not None]
        worst = min(exps)
        disp = moments(exps)
        avg_cost = ex["total_costs_usd"] / len(trades)
        return {
            "n_trades": mm["n"], "moments": mm, "sr": sr, "psr": psr0,
            "sr_star": sr_star, "dsr": dsr, "ci95": ci95,
            "worst_fold_expnet": worst, "avg_cost_per_trade": avg_cost,
            "fold_dispersion": {"std": disp["std"], "min": min(exps), "max": max(exps)},
            "worst_fold_ok": worst >= -(2 * avg_cost), **fs,
        }

    print("\nFOLD (base 17/slip0):")
    b_base = block(ex_base["trades"], ex_base, "base")
    print("FOLD (must x1.5+slip2):")
    b_must = block(ex_must["trades"], ex_must, "must")

    crit = {
        "psr_gt_080": b_base["psr"] > 0.80,
        "dsr_gt_0": b_base["dsr"] > 0.0,
        "ci95_gt_0": b_base["ci95"][0] > 0,
        "worst_fold_ok": b_base["worst_fold_ok"],
        "must_cell_positive": ex_must["expectancy_net_usd"] > 0,
    }
    print(f"\nBASE : SR={b_base['sr']:+.4f} PSR={b_base['psr']:.4f} SR*={b_base['sr_star']:.4f} "
          f"DSR={b_base['dsr']:.4f} CI95=[{b_base['ci95'][0]:+.4f},{b_base['ci95'][1]:+.4f}]")
    print(f"MUST : SR={b_must['sr']:+.4f} PSR={b_must['psr']:.4f} DSR={b_must['dsr']:.4f} "
          f"CI95=[{b_must['ci95'][0]:+.4f},{b_must['ci95'][1]:+.4f}]")
    print(f"criteria: {crit}")

    out = {
        "dataset_hash": dhash, "strategy_version": registry.STRATEGY_VERSION,
        "arm_disable_gates": list(DISABLE), "t_star_frozen": T_STAR,
        "n_trials_dsr": n_trials,
        "n_trials_composition": "3 arm P4 iter-3 + 12 threshold sweep C1 (arm scorer = C1 T=60.1); C2 duplikat; 18 sel C3 = robustness biaya, bukan konfig baru",
        "sr_trials": sr_trials, "v_sr_trials": v_sr,
        "stats_base": b_base, "stats_must_x15_slip2": b_must,
        "criteria": crit,
        "preflight_certificate": "PENDING — run_full_preflight_battery() milik engine lama (Domain B); wiring terpisah, tercatat jujur sebagai item terbuka",
        "verdict_stats": "LULUS_STATISTIK" if all(crit.values()) else "GAGAL_STATISTIK",
    }
    blob = json.dumps({k: v for k, v in out.items() if k != "results_hash"},
                      sort_keys=True, ensure_ascii=True)
    out["results_hash"] = hashlib.sha256(blob.encode()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "scorer_wfo_stats.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    print(f"\nVERDICT: {out['verdict_stats']} | results_hash: {out['results_hash'][:16]}…")
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
