"""A4 — analisis wajib backward OOS (dari artefak A3 RUN ONCE, tanpa re-fit).

Analisis:
1. Statistik: expNet, moments, CI95, PSR (vs 0), DSR (N-trials jujur=15),
   max consecutive losses, tabel bulanan, worst week.
2. Dekomposisi rezim per trade (join ke bar): arah, jam sesi, kekuatan trend
   M15 (|slope EMA20|, tercile), rezim chop (slope < ambang H-REGIME-SLOPE-02),
   volatilitas (ATR M5 tercile).
3. Monotonisitas skor: bucket skor -> expNet (champion: hanya >=T* yang tereksekusi).
   PLUS arm diagnostik OBSERVATIONAL (threshold=null, BUKAN champion, bukan
   input verdict) untuk kurva penuh termasuk wilayah <T*.

Output: data/research/backward/a4_analysis.json
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from are.validation import calculate_deflated_sharpe_ratio
from strategy_v2 import broker_meta as bm
from strategy_v2 import registry
from strategy_v2.replay import run_decision_replay, run_execution_replay
from strategy_v2.zones import atr, ema

BACK = ROOT / "data" / "research" / "backward"
BASE_SPREAD = 17.0
BALANCE = 1136.65
DISABLE = ("b1_news", "b4_location")
SESSION_BREAK_S = 3600
TRAINING_FIRST_TS = 1785217800
N_TRIALS_DSR = 15  # 3 arm P4 + 12 sweep C1 (komposisi C4, jujur)


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def psr_of(sr: float, n: int, skew: float, kurt: float) -> float:
    if n < 2:
        return 0.0
    denom = math.sqrt(max(1e-12, 1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr * sr))
    z = sr * math.sqrt(n - 1) / denom
    return norm_cdf(z)


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


def bucket_stats(trades: list, key_fn) -> dict:
    buckets: dict = {}
    for t in trades:
        k = key_fn(t)
        if k is None:
            continue
        b = buckets.setdefault(k, {"n": 0, "net": 0.0, "wins": 0})
        b["n"] += 1
        b["net"] += t["net_usd"]
        b["wins"] += 1 if t["net_usd"] > 0 else 0
    out = {}
    for k, b in buckets.items():
        out[str(k)] = {"n": b["n"], "net_usd": round(b["net"], 2),
                       "exp_net": round(b["net"] / b["n"], 4),
                       "win_rate": round(b["wins"] / b["n"], 4)}
    return out


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
    a3 = json.loads((BACK / "a3_champion_run.json").read_text(encoding="utf-8"))
    m5_all = json.loads((BACK / "dataset_m5.json").read_text(encoding="utf-8"))["candles"]
    m15_all = json.loads((BACK / "dataset_m15.json").read_text(encoding="utf-8"))["candles"]
    acc = json.loads((BACK / "account_snapshot.json").read_text(encoding="utf-8"))
    qual = json.loads((BACK / "oos_qualification.json").read_text(encoding="utf-8"))

    m5 = [b for b in m5_all if int(b["time"]) < TRAINING_FIRST_TS]
    m15 = [b for b in m15_all if int(b["time"]) < TRAINING_FIRST_TS]
    meta = bm.load_broker_meta(acc)
    trades = a3["trades_base"]
    nets = [t["net_usd"] for t in trades]
    mo = moments(nets)
    sr = mo["mean"] / mo["std"] if mo["std"] > 0 else 0.0
    ci_lo = mo["mean"] - 1.96 * mo["std"] / math.sqrt(mo["n"])
    ci_hi = mo["mean"] + 1.96 * mo["std"] / math.sqrt(mo["n"])
    psr_v = psr_of(sr, mo["n"], mo["skew"], mo["kurt"])
    _, dsr_p = calculate_deflated_sharpe_ratio(
        observed_sharpe=sr, num_trials=N_TRIALS_DSR, num_observations=mo["n"],
        skewness=mo["skew"], kurtosis=mo["kurt"])

    # streak & bulanan
    max_streak = cur = 0
    for t in trades:
        cur = cur + 1 if t["net_usd"] <= 0 else 0
        max_streak = max(max_streak, cur)
    by_month: dict = {}
    for t in trades:
        m = datetime.fromtimestamp(int(t["signal_ts"]), tz=timezone.utc).strftime("%Y-%m")
        b = by_month.setdefault(m, {"n": 0, "net": 0.0})
        b["n"] += 1
        b["net"] += t["net_usd"]
    monthly = {k: {"n": v["n"], "net_usd": round(v["net"], 2), "exp_net": round(v["net"] / v["n"], 4)}
               for k, v in sorted(by_month.items())}

    # ── Fitur rezim di waktu sinyal ─────────────────────────────────────────
    m15_closes = [b["close"] for b in m15]
    ema20 = ema(m15_closes, 20)
    m15_ts = [int(b["time"]) for b in m15]
    m5_times = [int(b["time"]) for b in m5]
    slope_thresh = registry.hypothesis(registry.load_hypothesis_registry(), "H-REGIME-SLOPE-02")["value"].get("min_slope_pts_per_bar", 1.0)

    def m15_slope_at(ts: int):
        # slope pada M15 bar TERAKHIR yang sudah closed sebelum ts
        # REPLIKA PERSIS engine (gates.py): (ema[t] - ema[t-lookback])/0.01/lookback
        # = POIN per bar (1 poin = 0.01 harga), lookback H-REGIME-SLOPE-02 = 8
        lo, hi = 0, len(m15_ts) - 1
        idx = None
        while lo <= hi:
            mid = (lo + hi) // 2
            if m15_ts[mid] + 900 <= ts:
                idx = mid
                lo = mid + 1
            else:
                hi = mid - 1
        lb = int(registry.hypothesis(registry.load_hypothesis_registry(), "H-REGIME-SLOPE-02")["value"].get("lookback_bars", 8))
        if idx is None or idx < max(20, lb):
            return None
        return (ema20[idx] - ema20[idx - lb]) / 0.01 / lb

    atr_cache: dict = {}
    def atr_at(ts: int):
        lo, hi = 0, len(m5_times) - 1
        idx = None
        while lo <= hi:
            mid = (lo + hi) // 2
            if m5_times[mid] + 300 <= ts:
                idx = mid
                lo = mid + 1
            else:
                hi = mid - 1
        if idx is None or idx < 14:
            return None
        key = idx // 50
        if key not in atr_cache:
            atr_cache[key] = atr(m5[max(0, idx - 200):idx + 1], 14)
        return atr_cache[key]

    feats = []
    for t in trades:
        ts = int(t["signal_ts"])
        s = m15_slope_at(ts)
        a = atr_at(ts)
        feats.append({
            "slope": s, "atr": a,
            "hour": datetime.fromtimestamp(ts, tz=timezone.utc).hour,
            "direction": t["direction"], "score": t.get("quality_score"),
        })
    slopes = sorted(f["slope"] for f in feats if f["slope"] is not None)
    atrs = sorted(f["atr"] for f in feats if f["atr"] is not None)
    t1, t2 = slopes[len(slopes)//3], slopes[2*len(slopes)//3]
    a1, a2 = atrs[len(atrs)//3], atrs[2*len(atrs)//3]

    def tf_feat(t, i):
        f = feats[i]
        if f["slope"] is None:
            return None
        strength = "FLAT" if abs(f["slope"]) < slope_thresh else ("T1" if abs(f["slope"]) <= t1 else ("T2" if abs(f["slope"]) <= t2 else "T3"))
        vol = "V1" if f["atr"] <= a1 else ("V2" if f["atr"] <= a2 else "V3")
        sess = "asia" if f["hour"] < 7 else ("london" if f["hour"] < 13 else ("ny" if f["hour"] < 21 else "late"))
        return {"trend": strength, "vol": vol, "session": sess}

    decomp = {
        "direction": bucket_stats(trades, lambda t: t["direction"]),
        "trend_strength": bucket_stats(trades, lambda t: tf_feat(t, trades.index(t))["trend"] if tf_feat(t, trades.index(t)) else None),
        "chop_vs_trend": bucket_stats(trades, lambda t: "CHOP(<%.1fpt/bar)" % slope_thresh if tf_feat(t, trades.index(t)) and tf_feat(t, trades.index(t))["trend"] == "FLAT" else "TREND"),
        "volatility": bucket_stats(trades, lambda t: tf_feat(t, trades.index(t))["vol"] if tf_feat(t, trades.index(t)) else None),
        "session": bucket_stats(trades, lambda t: tf_feat(t, trades.index(t))["session"] if tf_feat(t, trades.index(t)) else None),
    }

    # ── Monotonisitas skor (champion: >=T* tereksekusi) ─────────────────────
    def score_bucket(t):
        s = t.get("quality_score")
        if s is None:
            return None
        if s < 50: return "<50"
        if s < 60: return "50-60"
        if s < 70: return "60-70"
        if s < 80: return "70-80"
        return "80+"
    score_buckets = bucket_stats(trades, score_bucket)
    ordered = [score_buckets.get(k) for k in ("60-70", "70-80", "80+") if k in score_buckets]
    monotonic = all(ordered[i]["exp_net"] <= ordered[i+1]["exp_net"] for i in range(len(ordered)-1)) if len(ordered) >= 2 else None
    buckets_testable = all(b["n"] >= 8 for b in ordered) if ordered else False

    # ── Arm diagnostik OBSERVATIONAL (threshold=null; BUKAN champion) ───────
    profile = registry.load_profile("MICRO")
    reg = registry.load_hypothesis_registry()
    prof_diag = {**profile, "scoring": {**profile["scoring"], "mode": "score",
                 "thresholds": {**profile["scoring"]["thresholds"], "candidate": None}}}
    chash = registry.compute_config_hash(prof_diag, reg, calendar_artifact_hash=None,
                                         broker_meta_hash=bm.broker_meta_hash(meta))
    cfg = {"config_hash": chash, "dataset_hash": a3["dataset_hash"], "balance": BALANCE,
           "risk_percent": prof_diag["risk"]["risk_percent"], "spread_points": BASE_SPREAD}
    recs = []
    for sess in sessions(m5):
        if len(sess) < 40:
            continue
        recs.extend(run_decision_replay(sess, m15, prof_diag, reg, None, cfg, disable_gates=DISABLE))
    ex_diag = run_execution_replay(recs, m5, prof_diag, spread_points=BASE_SPREAD,
                                   slippage_points=0.0, delay_bars=0, broker_meta=meta,
                                   spread_label="SNAPSHOT_BACKWARD")
    score_by_ts = {int(r["evaluation_timestamp"]): r["quality_score"].get("final_score")
                   for r in recs if r["decision"] in ("BUY", "SELL") and isinstance(r.get("quality_score"), dict)}
    diag_trades = [{**t, "quality_score": score_by_ts.get(int(t["signal_ts"]))} for t in ex_diag["trades"]]
    diag_curve = bucket_stats(diag_trades, score_bucket)
    diag_ordered = [diag_curve[k] for k in ("50-60", "60-70", "70-80", "80+") if k in diag_curve]
    diag_monotonic = all(diag_ordered[i]["exp_net"] <= diag_ordered[i+1]["exp_net"] for i in range(len(diag_ordered)-1)) if len(diag_ordered) >= 2 else None

    out = {
        "artifact_id": "A4-BACKWARD-ANALYSIS",
        "a3_results_hash_ref": a3["results_hash"],
        "dataset_hash": a3["dataset_hash"],
        "stats": {
            "n": mo["n"], "exp_net": round(mo["mean"], 4), "std": round(mo["std"], 4),
            "skew": round(mo["skew"], 4), "kurt": round(mo["kurt"], 4),
            "sr_per_trade": round(sr, 4), "ci95": [round(ci_lo, 4), round(ci_hi, 4)],
            "psr_vs0": round(psr_v, 4),
            "dsr_p_value": round(dsr_p, 4), "dsr_trials": N_TRIALS_DSR,
            "max_consecutive_losses": max_streak,
            "net_total_usd": round(sum(nets), 2),
        },
        "monthly": monthly,
        "regime_decomposition": decomp,
        "slope_threshold_pts_per_bar": slope_thresh,
        "score_buckets_champion": score_buckets,
        "score_monotonicity_champion": {"ordered_exp_net": [b["exp_net"] for b in ordered],
                                        "monotonic": monotonic, "all_buckets_n_ge_8": buckets_testable},
        "diagnostic_full_curve": {
            "label": "OBSERVATIONAL_DIAGNOSTIC threshold=null — BUKAN champion, BUKAN input verdict",
            "n_trades": len(diag_trades), "exp_net": round(ex_diag["expectancy_net_usd"], 4),
            "buckets": diag_curve,
            "monotonic_50_to_80": diag_monotonic,
        },
    }
    blob = json.dumps({k: v for k, v in out.items() if k != "results_hash"},
                      sort_keys=True, ensure_ascii=True)
    out["results_hash"] = hashlib.sha256(blob.encode()).hexdigest()
    (BACK / "a4_analysis.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")

    print(f"STATS: n={mo['n']} expNet={mo['mean']:+.4f} CI95=[{ci_lo:+.2f},{ci_hi:+.2f}] "
          f"PSR={psr_v:.3f} DSR_p={dsr_p:.3f} maxStreakLoss={max_streak}")
    print("MONTHLY:", json.dumps(monthly))
    for k, v in decomp.items():
        print(f"  {k}: " + " | ".join(f"{kk}: n={vv['n']} exp={vv['exp_net']:+.2f}" for kk, vv in v.items()))
    print(f"SCORE champion buckets: {json.dumps(score_buckets)} | monotonic={monotonic} (n>=8: {buckets_testable})")
    print(f"DIAG full curve: n={len(diag_trades)} expNet={ex_diag['expectancy_net_usd']:+.4f} "
          f"monotonic(50-80+)={diag_monotonic}")
    print(f"results_hash: {out['results_hash'][:16]}...")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
