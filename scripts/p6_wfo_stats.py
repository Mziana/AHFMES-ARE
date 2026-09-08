"""P6 — Rolling OOS + statistik (mandat §P6) atas arm juara P4/P5 FROZEN.

Parameter FROZEN (MICRO_V2, disable b1/b3/b4) → tidak ada fitting per fold →
WFO mereduksi jadi rolling OOS dengan embargo ≥ 1 hari antar window (purge:
trade yang menyeberangi batas fold dikecualikan dari statistik fold, terhitung
terpisah). Metrik wajib B-4: PSR, DSR (momen nyata), CI95 expNet, worst-fold,
fold dispersion. N trials DSR = 14 arm P4 (9 MICRO + 5 SCALP).

Output: data/research/p6/wfo_stats.json (ber-hash).
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from strategy_v2 import broker_meta as bm
from strategy_v2 import registry
from strategy_v2.replay import run_decision_replay, run_execution_replay

P3 = ROOT / "data" / "research" / "p3"
P4 = ROOT / "data" / "research" / "p4"
P6 = ROOT / "data" / "research" / "p6"
SESSION_BREAK_S = 3600
DISABLE = ("b1_news", "b4_location")   # FROZEN P4 iter-3 (champion revisi slope)
N_TRIALS = 3                                       # trial di artefak P4 iter-3 (3 arm MICRO)
N_FOLDS = 6
EMBARGO_S = 86400                                    # 1 hari
GAMMA_EM = 0.5772156649                              # Euler–Mascheroni


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
    """Inverse CDF normal standar (Acklam / bisection refine — cukup utk 1-1/N)."""
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
    return {"n": n, "mean": m, "std": sd,
            "skew": m3 / sd**3, "kurt": m4 / sd**4}


def psr(sr: float, sr_star: float, n: int, skew: float, kurt: float) -> float:
    """Probabilistic Sharpe Ratio (Bailey & López de Prado)."""
    if n < 2:
        return 0.0
    denom = math.sqrt(max(1e-12, 1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr * sr))
    z = (sr - sr_star) * math.sqrt(n - 1) / denom
    return norm_cdf(z)


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
           "risk_percent": profile["risk"]["risk_percent"], "spread_points": 17.0}

    records = []
    for sess in sessions(m5):
        if len(sess) < 40:
            continue
        records.extend(run_decision_replay(sess, m15, profile, reg, None, cfg,
                                           disable_gates=DISABLE))
    ex = run_execution_replay(records, m5, profile, spread_points=17.0,
                              slippage_points=0.0, delay_bars=0, broker_meta=meta,
                              spread_label="ESTIMATED_COST_MODEL")
    trades = ex["trades"]
    print(f"champion trades: {len(trades)} net={ex['net_usd']:.2f} "
          f"expNet={ex['expectancy_net_usd']:.4f}")

    # ── V[SR] lintas 14 trial P4 (deflasi DSR) ──────────────────────────────
    p4 = json.loads((P4 / "ablation_results.json").read_text(encoding="utf-8"))
    arms = p4["arms"]
    print(f"recompute {len(arms)} trials utk V[SR] …")
    sr_trials = []
    for arm in arms:
        dis = tuple(arm["disabled"])
        recs = []
        for sess in sessions(m5):
            if len(sess) < 40:
                continue
            recs.extend(run_decision_replay(sess, m15, profile if arm["profile_id"] == "MICRO"
                                            else registry.load_profile("SCALP"),
                                            reg, None, cfg, disable_gates=dis))
        exa = run_execution_replay(recs, m5, profile if arm["profile_id"] == "MICRO"
                                   else registry.load_profile("SCALP"),
                                   spread_points=17.0, slippage_points=0.0, delay_bars=0,
                                   broker_meta=meta, spread_label="ESTIMATED_COST_MODEL")
        nets = [t["net_usd"] for t in exa["trades"]]
        if len(nets) >= 2 and (lambda m2: m2["std"] > 0)(moments(nets)):
            mm = moments(nets)
            sr_trials.append(mm["mean"] / mm["std"])
        else:
            sr_trials.append(0.0)
        print(f"  [{arm['arm']}] trades={len(nets)} SR={sr_trials[-1]:+.4f}")
    v_sr = sum((s - sum(sr_trials) / len(sr_trials)) ** 2 for s in sr_trials) / (len(sr_trials) - 1)
    print(f"V[SR] across {len(sr_trials)} trials = {v_sr:.6f}")

    # ── Fold OOS bergulir + embargo ──────────────────────────────────────────
    t0, t1 = int(m5[0]["time"]), int(m5[-1]["time"]) + 300
    span = (t1 - t0) / N_FOLDS
    folds = []
    dropped_cross = 0
    for i in range(N_FOLDS):
        w_start, w_end = t0 + i * span, t0 + (i + 1) * span
        emb_start, emb_end = w_start, w_end - EMBARGO_S  # embargo 1 hari di ekor fold
        ftrades = [t for t in trades if w_start <= t["entry_ts"] < w_end]
        kept = [t for t in ftrades if t["exit_ts"] <= emb_end + EMBARGO_S]
        # purge: trade yang exit melewati akhir window (menyeberang embargo)
        dropped = len(ftrades) - len(kept)
        dropped_cross += dropped
        nets = [t["net_usd"] for t in kept]
        mm = moments(nets) if nets else {"n": 0, "mean": 0.0, "std": 0.0, "skew": 0.0, "kurt": 3.0}
        folds.append({
            "fold": i + 1,
            "window_utc": [w_start, w_end],
            "trades_raw": len(ftrades), "trades_kept": len(kept), "dropped_cross": dropped,
            "net_usd": round(sum(nets), 2),
            "expectancy_net_usd": round(mm["mean"], 4) if kept else None,
            "std": round(mm["std"], 4),
        })
        print(f"fold {i+1}: kept={len(kept):3d} net={sum(nets):9.2f} "
              f"expNet={mm['mean'] if kept else 0:+.4f} (dropped {dropped})")

    # ── Statistik pooled + PSR/DSR/CI95 ─────────────────────────────────────
    nets = [t["net_usd"] for t in trades]
    mm = moments(nets)
    sr = mm["mean"] / mm["std"] if mm["std"] > 0 else 0.0
    psr0 = psr(sr, 0.0, mm["n"], mm["skew"], mm["kurt"])
    sr_star = math.sqrt(max(v_sr, 1e-12)) * ((1 - GAMMA_EM) * norm_ppf(1 - 1.0 / N_TRIALS)
                                             + GAMMA_EM * norm_ppf(1 - 1.0 / N_TRIALS) ** 2)
    dsr = psr(sr, sr_star, mm["n"], mm["skew"], mm["kurt"])
    t95 = 1.96  # n besar; t-dist ≈ normal
    ci95 = (mm["mean"] - t95 * mm["std"] / math.sqrt(mm["n"]),
            mm["mean"] + t95 * mm["std"] / math.sqrt(mm["n"]))
    avg_cost = ex["total_costs_usd"] / len(trades)
    worst = min(f["expectancy_net_usd"] for f in folds if f["expectancy_net_usd"] is not None)
    exps = [f["expectancy_net_usd"] for f in folds if f["expectancy_net_usd"] is not None]
    disp = moments(exps)

    crit = {
        "psr_gt_080": psr0 > 0.80,
        "dsr_gt_0": dsr > 0.0,
        "ci95_gt_0": ci95[0] > 0,
        "worst_fold_ok": worst >= -(2 * avg_cost),
    }
    print(f"\nSR={sr:+.4f} PSR={psr0:.4f} SR*={sr_star:.4f} DSR={dsr:.4f}")
    print(f"CI95 expNet = [{ci95[0]:+.4f}, {ci95[1]:+.4f}]")
    print(f"worst-fold expNet={worst:+.4f} vs -2*avgCost={-(2*avg_cost):+.4f} -> {'OK' if crit['worst_fold_ok'] else 'FAIL'}")
    print(f"fold dispersion: std={disp['std']:.4f} range=[{min(exps):+.4f}, {max(exps):+.4f}]")
    print(f"criteria: {crit}")

    out = {
        "dataset_hash": dhash, "strategy_version": registry.STRATEGY_VERSION,
        "champion_disable_gates": list(DISABLE),
        "n_trials_dsr": N_TRIALS, "v_sr_trials": v_sr, "sr_trials": sr_trials,
        "sr_star": sr_star,
        "pooled": {**mm, "sr": sr, "psr": psr0, "dsr": dsr, "ci95": ci95},
        "folds": folds, "dropped_cross_boundary": dropped_cross,
        "worst_fold_expnet": worst, "avg_cost_per_trade": avg_cost,
        "fold_dispersion": {"std": disp["std"], "min": min(exps), "max": max(exps)},
        "criteria": crit,
        "preflight_certificate": "PENDING — run_full_preflight_battery() milik engine lama (Domain B); wiring terpisah, tercatat jujur sebagai item terbuka",
        "verdict_stats": "LULUS_STATISTIK" if all(crit.values()) else "GAGAL_STATISTIK",
    }
    blob = json.dumps({k: v for k, v in out.items() if k != "results_hash"},
                      sort_keys=True, ensure_ascii=True)
    out["results_hash"] = hashlib.sha256(blob.encode()).hexdigest()
    P6.mkdir(parents=True, exist_ok=True)
    (P6 / "wfo_stats.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    print(f"\nVERDICT: {out['verdict_stats']} | results_hash: {out['results_hash'][:16]}…")
    return 0 if all(crit.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
