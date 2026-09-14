# SCAN REGIME — cari window sideways/choppy di cache 5 bulan (review prio 8).
# KRITERIA (semua dari struktur H4 agregat, TANPA PnL/sinyal/replay apapun —
# pemilihan window wajib buta terhadap hasil trading):
#   1. Efficiency Ratio (Kaufman): |P_end - P_start| / sum|dP| pada window H4
#      250 bar (~60 hari) — makin RENDAH makin choppy.
#   2. Range ternormalisasi: (maxH-minL)/ATR-H4 pada window sama — makin
#      RENDAH makin range-bound (tidak trending jauh).
#   3. Struktur swing: structure_trend() engine (None = campur/range).
#   4. Vitalitas: ATR-M5 rata-rata di eval window >= 150 pts (di atas gate
#      item-8 min 120 dengan headroom) — window sepi total tidak layak
#      diuji karena gate sendiri akan memblok semua (replay jadi kosong).
# Output: tabel kandidat (10 hari, step 6 jam) diurut ER naik + metrics
# window trending ter-pin (39.2 hari, potongan 10 hari pertama) sbg pembanding.
from __future__ import annotations

import bisect
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from strategy_v2 import candle_scoring as CS  # noqa: E402
from strategy_v2 import smc  # noqa: E402

OUT = ROOT / "data/research/smc_v3/smc_v3_regime_scan.json"
M1_CACHE = "data/research/r1/dataset_m1.json"
M5_CACHE = "data/research/r1/dataset_m5_fresh.json"
M15_CACHE = "data/research/r1/dataset_m15_fresh.json"
H4W = 250            # window H4 utk ER/range/struktur (~60 hari)
EVAL_DAYS = 10       # panjang window evaluasi yang dicari
STEP_S = 6 * 3600    # grid kandidat tiap 6 jam
MIN_ATR5_PTS = 150.0 # vitalitas minimal (di atas gate 120 + headroom)


def load(path: str) -> list:
    d = json.load(open(ROOT / path, encoding="utf-8"))
    return d.get("candles", d if isinstance(d, list) else [])


def m15_to_h4(m15: list) -> list:
    """Agregasi M15 -> H4 per kelipatan 4 jam UTC (hanya bucket penuh 16 bar)."""
    out, cur = [], None
    for b in m15:
        t = int(b["time"]) // 14400 * 14400
        if cur is None or cur["time"] != t:
            if cur is not None and cur["n"] == 16:
                out.append({k: cur[k] for k in ("time", "open", "high",
                                                "low", "close")})
            cur = {"time": t, "open": float(b["open"]), "high": float(b["high"]),
                   "low": float(b["low"]), "close": float(b["close"]), "n": 1}
            continue
        cur["high"] = max(cur["high"], float(b["high"]))
        cur["low"] = min(cur["low"], float(b["low"]))
        cur["close"] = float(b["close"])
        cur["n"] += 1
    if cur is not None and cur["n"] == 16:
        out.append({k: cur[k] for k in ("time", "open", "high", "low", "close")})
    return out


def metrics(h4w: list) -> dict:
    closes = [float(b["close"]) for b in h4w]
    sdp = sum(abs(closes[i + 1] - closes[i]) for i in range(len(closes) - 1))
    er = abs(closes[-1] - closes[0]) / sdp if sdp > 0 else 1.0
    hi = max(float(b["high"]) for b in h4w)
    lo = min(float(b["low"]) for b in h4w)
    a4 = CS.atr(h4w[-100:]) or 1.0
    rng = (hi - lo) / a4
    trend = smc.structure_trend(h4w)
    return {"er": round(er, 4), "range_atr": round(rng, 1), "trend": trend}


def main() -> int:
    m1 = load(M1_CACHE)
    m5 = load(M5_CACHE)
    m15 = load(M15_CACHE)
    h4 = m15_to_h4(m15)
    h4_ts = [int(b["time"]) for b in h4]
    m5_ts = sorted(int(b["time"]) for b in m5)
    print(f"cache: M1 {len(m1)} | M5 {len(m5)} | M15 {len(m15)} | H4agg {len(h4)}")
    print(f"  M1 {datetime.fromtimestamp(int(m1[0]['time']), tz=timezone.utc):%m-%d}"
          f" -> {datetime.fromtimestamp(int(m1[-1]['time']), tz=timezone.utc):%m-%d}"
          f" | H4agg {datetime.fromtimestamp(h4_ts[0], tz=timezone.utc):%m-%d}"
          f" -> {datetime.fromtimestamp(h4_ts[-1], tz=timezone.utc):%m-%d} UTC")

    t_lo = max(int(m1[0]["time"]), h4_ts[0]) + EVAL_DAYS * 86400
    t_hi = int(m1[-1]["time"]) - 300

    # precompute rolling ATR-M5 (period 14) utk seluruh seri M5 — O(N)
    m5.sort(key=lambda b: int(b["time"]))
    m5_ts = [int(b["time"]) for b in m5]
    pre = [0.0]
    for i in range(1, len(m5)):
        h, l = float(m5[i]["high"]), float(m5[i]["low"])
        pc = float(m5[i - 1]["close"])
        tr = max(h - l, abs(h - pc), abs(l - pc))
        pre.append(pre[-1] + tr)

    def atr_at(j: int):
        """ATR-14 bar M5 ke-j (close bar j; butuh j >= 14 dan j+1 < len(pre))."""
        if 14 <= j < len(pre) - 1:
            return (pre[j + 1] - pre[j + 1 - 14]) / 14
        return None

    cands = []
    t = t_lo
    while t <= t_hi:
        t_end = t + EVAL_DAYS * 86400
        # window H4 yang CLOSED sebelum t (anti-lookahead)
        i4 = len([x for x in h4_ts if x + 14400 <= t]) - 1
        if i4 + 1 >= H4W:
            h4w = h4[i4 + 1 - H4W: i4 + 1]
            mm = metrics(h4w)
            # vitalitas: mean ATR-M5 rolling-14 di dalam eval window
            vals = []
            j = bisect.bisect_left(m5_ts, t)
            while j < len(m5_ts) and m5_ts[j] + 300 <= t_end:
                a = atr_at(j)
                if a is not None:
                    vals.append(a)
                j += 1
            atr5_mean_pts = (sum(vals) / len(vals)) / smc.POINT if vals else 0.0
            mm["atr5_mean_pts"] = round(atr5_mean_pts, 1)
            mm["t_start"] = datetime.fromtimestamp(t, tz=timezone.utc).isoformat()
            mm["t_end"] = datetime.fromtimestamp(t_end, tz=timezone.utc).isoformat()
            mm["layak"] = bool(atr5_mean_pts >= MIN_ATR5_PTS)
            cands.append(mm)
        t += STEP_S

    layak = [c for c in cands if c["layak"]]
    layak.sort(key=lambda c: c["er"])
    print(f"\nkandidat 10-hari: {len(cands)} grid, {len(layak)} layak "
          f"(ATR5 mean >= {MIN_ATR5_PTS:.0f}p)")
    print(f"{'mulai (UTC)':17s} {'ER':>7s} {'rng/ATR':>8s} {'trend':>6s} "
          f"{'ATR5m':>7s}")
    for c in layak[:12]:
        print(f"{c['t_start'][:16]:17s} {c['er']:7.4f} {c['range_atr']:8.1f} "
              f"{str(c['trend']):>6s} {c['atr5_mean_pts']:7.0f}")
    print("... pembanding: window trending ter-pin (potongan 10 hari pertama):")
    tt = datetime.fromisoformat("2026-08-03T11:39:00+00:00").timestamp()
    i4 = len([x for x in h4_ts if x + 14400 <= tt]) - 1
    if i4 + 1 >= H4W:
        mm = metrics(h4[i4 + 1 - H4W: i4 + 1])
        print(f"  2026-08-03T11:39  ER={mm['er']:.4f} rng/ATR={mm['range_atr']:.1f} "
              f"trend={mm['trend']}")

    out = {"meta": {"kriteria": [
                        "ER Kaufman H4 250-bar (makin rendah makin choppy)",
                        "range/ATR-H4 250-bar (makin rendah makin range-bound)",
                        "structure_trend H4 (None = campur)",
                        f"ATR-M5 mean >= {MIN_ATR5_PTS} pts (vitalitas, di atas gate 120)",
                        "TANPA PnL/sinyal — pemilihan buta terhadap hasil trading"],
                    "eval_days": EVAL_DAYS, "grid_step_s": STEP_S,
                    "h4_source": "agregasi 16x M15 (bucket penuh)"},
           "candidates_top": layak[:12],
           "n_candidates_total": len(cands), "n_layak": len(layak)}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nartefak: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
