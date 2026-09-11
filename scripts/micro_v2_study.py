# STUDI OFFLINE - MICRO v2 "SCALP-M1" (replika SCALP turun satu TF)
# Desain owner (2026-09-11): eksekusi M1 close, bias momentum M5 (EMA9/21+RSI 45/55),
# RSI guard {65/35 | 70/30} di M5+M1, volume WAJIB {1.0x | 1.2x} avg5 M1
# (bonus +1 tetap hanya di 1.2x - decouple), SL/TP {1.1/1.7 | parity 1.25/2.0} x ATR M5,
# threshold skor 7, cooldown 5 menit, satu posisi per arm (parity driver live).
# Murni OFFLINE & read-only terhadap bridge. Tidak menyentuh driver/live path.
# Sel biaya kontrak R1 Stage 1: base 17 poin; must = x1.5 + slip2 = 27.5 poin.
# Kriteria kill: expNet_must > 0 DAN n >= 30.
from __future__ import annotations

import bisect
import json
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from strategy_v2 import candle_scoring as CS  # noqa: E402
from strategy_v2 import simple_variants as SV  # noqa: E402

BRIDGE = "http://127.0.0.1:18888"
TOKEN_FILE = ROOT / "data" / "bridge_token.txt"
OUT_DIR = ROOT / "data" / "research" / "micro_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

POINT = 0.01
BASE_COST_PTS = 17.0
MUST_COST_PTS = 27.5
M1_WINDOW = 400          # == jendela driver live
M5_WINDOW = 400          # == jendela driver live
COOLDOWN_S = 5 * 60
VOL_BONUS = 1.2          # bonus +1 tetap hanya di 1.2x (decouple)
THRESHOLD = 7.0
MIN_SIGNALS = 30
SLTP = {"M0.9_T1.4": (0.9, 1.4), "M1.1_T1.7": (1.1, 1.7), "PAR125_T200": (1.25, 2.0)}
RSIG = {"65_35": (65.0, 35.0), "70_30": (70.0, 30.0)}
VOLG = {"v1.0": 1.0, "v1.2": 1.2}
VARIANTS = [f"{v}|{r}|{s}" for v in VOLG for r in RSIG for s in SLTP]


def get(path: str) -> dict:
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    req = urllib.request.Request(BRIDGE + path,
                                 headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def nearest_ema_level(direction: str, e9, e21, px: float):
    """Parity SCALP: EMA9/21 M5 terdekat searah (pullback)."""
    opts = [v for v in (e9, e21) if v is not None]
    if not opts:
        return None
    if direction == "BULL":
        below = [v for v in opts if v <= px]
        return max(below) if below else max(opts)
    above = [v for v in opts if v >= px]
    return min(above) if above else min(opts)


def simulate_exit(direction: str, sl: float, tp: float, entry_time: int,
                  m1_by_time: dict, m1_times: list) -> dict:
    """First-touch SL/TP dari bar M1 SETELAH bar sinyal (SL-priority ambigu).
    BUY: SL low<=sl, TP high>=tp. SELL: SL high>=sl, TP low<=tp.
    Return outcome/exit_time/gap. 'OPEN' bila tak tuntas s.d. akhir data."""
    start = bisect.bisect_right(m1_times, entry_time)
    prev_t = entry_time
    gap = False
    for k in range(start, len(m1_times)):
        t = m1_times[k]
        if t - prev_t > 900:
            gap = True
        prev_t = t
        b = m1_by_time[t]
        if direction == "BUY":
            hit_sl = b["low"] <= sl
            hit_tp = b["high"] >= tp
        else:
            hit_sl = b["high"] >= sl
            hit_tp = b["low"] <= tp
        if hit_sl:
            return {"outcome": "SL", "exit_time": t + 60, "gap": gap}
        if hit_tp:
            return {"outcome": "TP", "exit_time": t + 60, "gap": gap}
    return {"outcome": "OPEN", "exit_time": None, "gap": gap}


def score_for_variant(m1_hist: list, level, vm_key: str, orig_vmult: float) -> dict:
    """score_candle SCALP dengan gate volume sesuai varian.
    vm=1.2: persis produksi. vm=1.0: veto dilonggarkan ke 1.0x; bonus +1
    dicabut utk bar di [1.0x, 1.2x) - bonus tetap hanya di >=1.2x (decouple)."""
    vm = VOLG[vm_key]
    CS.VOL_MULT_SCALP = vm
    try:
        res = CS.score_candle(m1_hist, level, "SCALP", require_volume=True)
    finally:
        CS.VOL_MULT_SCALP = orig_vmult
    if vm < VOL_BONUS and res.get("ok"):
        avg5 = sum(int(b.get("volume", 0)) for b in m1_hist[-6:-1]) / 5.0
        vol = int(m1_hist[-1].get("volume", 0))
        if avg5 > 0 and vm * avg5 <= vol < VOL_BONUS * avg5:
            res = dict(res)
            res["score"] = res.get("score", 0) - 1.0
            res["ok"] = res["score"] >= THRESHOLD
            res["reason"] = "" if res["ok"] else f"skor {res['score']:.0f} < 7"
    return res


def classify_block(res: dict) -> str:
    reason = res.get("reason") or ""
    if "volume" in reason:
        return "volume_gate"
    if "pola" in reason:
        return "pola_tidak_ada"
    return "threshold"


def run_study() -> dict:
    print("fetch data ...", flush=True)
    m1_all = get("/candles?symbol=XAUUSD&timeframe=M1&count=40000").get("candles", [])[:-1]
    m5_all = get("/candles?symbol=XAUUSD&timeframe=M5&count=8000").get("candles", [])[:-1]
    m1_by_time = {b["time"]: b for b in m1_all}
    m1_times = sorted(m1_by_time)
    m5_by_time = {b["time"]: b for b in m5_all}
    m5_times = sorted(m5_by_time)
    t0, t1 = m1_times[0], m1_times[-1]
    days = (t1 - t0) / 86400.0
    print(f"M1 {len(m1_all)} bar | M5 {len(m5_all)} bar | jendela {days:.1f} hari "
          f"({datetime.fromtimestamp(t0, tz=timezone.utc):%m-%d %H:%M} -> "
          f"{datetime.fromtimestamp(t1, tz=timezone.utc):%m-%d %H:%M} UTC)", flush=True)

    stats = {v: {"entries": 0, "win": 0, "loss": 0, "gross_pts": 0.0,
                 "blocked": Counter(), "trades": [], "by_hour": Counter(),
                 "by_dir": Counter(), "gaps": 0} for v in VARIANTS}
    last_entry = {v: 0.0 for v in VARIANTS}
    busy_until = {v: 0.0 for v in VARIANTS}

    orig_vmult = CS.VOL_MULT_SCALP
    idx5 = -1
    e9 = e21 = mb = r_m5 = atr_m5 = None
    m5_hist: list = []
    n_eval = 0

    for i in range(M1_WINDOW, len(m1_all)):
        bar = m1_all[i]
        t = bar["time"]
        advanced = False
        while idx5 + 1 < len(m5_times) and m5_times[idx5 + 1] + 300 <= t:
            idx5 += 1
            advanced = True
        if advanced:
            m5_hist = [m5_by_time[tt]
                       for tt in m5_times[max(0, idx5 + 1 - M5_WINDOW): idx5 + 1]]
            if len(m5_hist) >= 30:
                closes = [b["close"] for b in m5_hist]
                e9, e21 = CS.ema(closes, 9), CS.ema(closes, 21)
                mb = SV.momentum_bias(m5_hist)
                r_m5 = CS.rsi(closes, 14)
                atr_m5 = CS.atr(m5_hist)
            else:
                mb = r_m5 = atr_m5 = None
        if mb is None or atr_m5 is None:
            for v in VARIANTS:
                stats[v]["blocked"]["bias_momentum_atau_data_kurang"] += 1
            continue
        n_eval += 1

        m1_hist = m1_all[i + 1 - M1_WINDOW: i + 1]
        r_m1 = CS.rsi([b["close"] for b in m1_hist], 14)
        direction = mb
        entry_px = float(bar["close"])
        level = nearest_ema_level(direction, e9, e21, entry_px)
        dir_sign = 1 if direction == "BULL" else -1  # noqa: F841 (dokumentasi arah)
        dir_str = "BUY" if direction == "BULL" else "SELL"

        res_for: dict = {}
        for v in VARIANTS:
            vm_key, r_key, s_key = v.split("|")
            sb, ss = RSIG[r_key]
            slm, tpm = SLTP[s_key]
            st = stats[v]
            if t < busy_until[v]:
                st["blocked"]["posisi_terbuka"] += 1
                continue
            if last_entry[v] and t - last_entry[v] < COOLDOWN_S:
                st["blocked"]["cooldown"] += 1
                continue
            guard_hit = False
            for rv in (r_m5, r_m1):
                if rv is None:
                    continue
                if (direction == "BULL" and rv >= sb) or \
                        (direction == "BEAR" and rv <= ss):
                    guard_hit = True
                    break
            if guard_hit:
                st["blocked"]["rsi_guard"] += 1
                continue
            if vm_key not in res_for:
                res_for[vm_key] = score_for_variant(m1_hist, level, vm_key, orig_vmult)
            res = res_for[vm_key]
            if not res.get("ok"):
                st["blocked"][classify_block(res)] += 1
                continue

            sl_dist, tp_dist = slm * atr_m5, tpm * atr_m5
            if direction == "BULL":
                sl, tp = entry_px - sl_dist, entry_px + tp_dist
            else:
                sl, tp = entry_px + sl_dist, entry_px - tp_dist
            out = simulate_exit(dir_str, sl, tp, t, m1_by_time, m1_times)
            if out["outcome"] == "OPEN":
                st["blocked"]["belum_tuntas_end_of_data"] += 1
                continue

            # gross poin: TP = +tp_dist, SL = -sl_dist (exit di level, tanpa slip;
            # spread/slip masuk sel biaya base/must)
            pts = tp_dist if out["outcome"] == "TP" else -sl_dist
            st["entries"] += 1
            last_entry[v] = t
            busy_until[v] = out["exit_time"]
            if out["gap"]:
                st["gaps"] += 1
            st["by_hour"][datetime.fromtimestamp(t, tz=timezone.utc).hour] += 1
            st["by_dir"][dir_str] += 1
            if out["outcome"] == "TP":
                st["win"] += 1
            else:
                st["loss"] += 1
            st["gross_pts"] += pts
            st["trades"].append({
                "time": datetime.fromtimestamp(t, tz=timezone.utc).isoformat(),
                "dir": dir_str, "pattern": res.get("pattern"),
                "score": res.get("score"),
                "sl_pts": round(sl_dist / POINT, 1), "tp_pts": round(tp_dist / POINT, 1),
                "outcome": out["outcome"], "gross_pts": round(pts, 1),
                "gap": out["gap"]})

    return {"m1_total": len(m1_all), "m5_total": len(m5_all), "days": days,
            "n_eval": n_eval, "stats": stats,
            "t0": datetime.fromtimestamp(t0, tz=timezone.utc).isoformat(),
            "t1": datetime.fromtimestamp(t1, tz=timezone.utc).isoformat()}


def summarize(result: dict) -> list:
    rows = []
    for v, s in result["stats"].items():
        n, w, l = s["entries"], s["win"], s["loss"]
        closed = w + l
        wr = (w / closed * 100.0) if closed else 0.0
        exp_base = (s["gross_pts"] - n * BASE_COST_PTS) / n if n else 0.0
        exp_must = (s["gross_pts"] - n * MUST_COST_PTS) / n if n else 0.0
        rows.append({
            "varian": v, "entries": n, "win": w, "loss": l,
            "wr": round(wr, 1),
            "exp_net_base_pts": round(exp_base, 2),
            "exp_net_must_pts": round(exp_must, 2),
            "usd_per_trade_at_002": round(exp_must * 0.02, 2),
            "avg_gross_pts": round(s["gross_pts"] / n, 1) if n else 0.0,
            "sinyal_per_hari": round(n / result["days"], 2),
            "cross_gap": s["gaps"],
            "pass": bool(exp_must > 0 and n >= MIN_SIGNALS),
            "pass_n_kurang": bool(exp_must > 0 and n < MIN_SIGNALS),
            "blocked": dict(s["blocked"]), "by_dir": dict(s["by_dir"]),
            "by_hour": {str(k): c for k, c in sorted(s["by_hour"].items())},
            "trades": s["trades"]})
    rows.sort(key=lambda r: -r["exp_net_must_pts"])
    return rows


def main() -> int:
    out_name = sys.argv[1] if len(sys.argv) > 1 else "study_results.json"
    result = run_study()
    rows = summarize(result)
    out = {"generated": datetime.now(timezone.utc).isoformat(),
           "window": {"m1_bars": result["m1_total"], "m5_bars": result["m5_total"],
                      "days": round(result["days"], 2),
                      "from": result["t0"], "to": result["t1"]},
           "n_eval_m1_bars": result["n_eval"],
           "cost_cells": {"base_pts": BASE_COST_PTS, "must_pts": MUST_COST_PTS},
           "criteria": f"expNet_must > 0 dan n >= {MIN_SIGNALS}",
           "rows": rows}
    path = OUT_DIR / out_name
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nhasil: {path}\n")
    hdr = (f"{'varian':26s} {'n':>4s} {'W/L':>8s} {'WR%':>6s} "
           f"{'expBase':>8s} {'expMust':>8s} {'$/tr@0.02':>9s} {'n/hr':>5s}  verdict")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        verdict = ("PASS" if r["pass"] else
                   "PASS(n<30)" if r["pass_n_kurang"] else "KILL")
        print(f"{r['varian']:26s} {r['entries']:4d} "
              f"{str(r['win']) + '/' + str(r['loss']):>8s} {r['wr']:6.1f} "
              f"{r['exp_net_base_pts']:8.2f} {r['exp_net_must_pts']:8.2f} "
              f"{r['usd_per_trade_at_002']:9.2f} {r['sinyal_per_hari']:5.2f}  {verdict}")
    for want in ("v1.0|65_35|M0.9_T1.4", "v1.2|65_35|M0.9_T1.4"):
        r = next((x for x in rows if x["varian"] == want), None)
        if r:
            print(f"\nfunnel {want}: n_eval={result['n_eval']}")
            for k, c in sorted(r["blocked"].items(), key=lambda x: -x[1]):
                print(f"  {k:28s} {c}")
            print(f"  ENTRI                        {r['entries']}")
            print(f"  arah: {r['by_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
