# CEK REDUNDANSI Bias<->BOS + umur BOS (review 3.2 / prioritas 2)
# Sumber: dataset cache (M1 150k bar, 5 bulan 8 Apr-9 Sep) — bridge sedang
# mati, dan cache ini lebih panjang (memuat regime non-trending juga).
# H4 diagregasi dari M15 (16x) utk struktur bias — diberi label eksplisit.
# Read-only; output: P(BOS searah | bias non-netral) + kuartil umur BOS.
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from strategy_v2 import smc  # noqa: E402

M5W = 400
M15W = 300
H4W = 250          # bar H4 agregat
EVERY = 12         # sampling tiap 12 bar M1 (~2.5 menit)
OUT = ROOT / "data/research/smc_v3/smc_v3_redundancy.json"


def load_candles(path: str) -> list:
    d = json.load(open(ROOT / path, encoding="utf-8"))
    return d.get("candles", d if isinstance(d, list) else [])


def m15_to_h4(m15: list) -> list:
    """Agregasi M15 -> H4 per kelipatan 4 jam UTC (label eksplisit utk audit)."""
    out = []
    cur_t, o, h, l, c, n = None, 0.0, 0.0, 0.0, 0.0, 0
    for b in m15:
        t = int(b["time"]) // 14400 * 14400
        if t != cur_t:
            if n == 16:
                out.append({"time": cur_t, "open": o, "high": h,
                            "low": l, "close": c, "volume": 0})
            cur_t, o, h, l, c, n = t, float(b["open"]), float(b["high"]), \
                float(b["low"]), float(b["close"]), 1
            continue
        h = max(h, float(b["high"]))
        l = min(l, float(b["low"]))
        c = float(b["close"])
        n += 1
    if n == 16:
        out.append({"time": cur_t, "open": o, "high": h, "low": l,
                    "close": c, "volume": 0})
    return out


def main() -> int:
    m1 = load_candles("data/research/r1/dataset_m1.json")
    m5 = load_candles("data/research/r1/dataset_m5_fresh.json")
    m15 = load_candles("data/research/r1/dataset_m15_fresh.json")
    h4 = m15_to_h4(m15)
    m5_by_t = {int(b["time"]): b for b in m5}
    m15_by_t = {int(b["time"]): b for b in m15}
    m5_ts = sorted(m5_by_t)
    m15_ts = sorted(m15_by_t)
    h4_ts = [int(b["time"]) for b in h4]

    n = bias_ne = bos_ok = 0
    bos_ages = []      # umur (bar M5) BOS searah TERBARU saat item OK
    for i in range(400, len(m1), EVERY):
        t = int(m1[i]["time"])
        m1h = m1[i + 1 - 400: i + 1]
        # window M5/M15: bar TERAKHIR yang SUDAH CLOSE sebelum t
        i5 = len([x for x in m5_ts if x + 300 <= t]) - 1
        i15 = len([x for x in m15_ts if x + 900 <= t]) - 1
        i4 = len([x for x in h4_ts if x + 14400 <= t]) - 1
        if i5 < 30 or i15 < 30 or i4 < 25:
            continue
        m5h = [m5_by_t[x] for x in m5_ts[max(0, i5 + 1 - M5W): i5 + 1]]
        m15h = [m15_by_t[x] for x in m15_ts[max(0, i15 + 1 - M15W): i15 + 1]]
        h4h = h4[max(0, i4 + 1 - H4W): i4 + 1]
        bias = smc.structure_trend(h4h)
        n += 1
        if not bias:
            continue
        bias_ne += 1
        ok = [e for e in smc.bos_choch(m15h) + smc.bos_choch(m5h)
              if e["dir"] == bias and e["type"] == "BOS"]
        if not ok:
            continue
        bos_ok += 1
        ages = []
        for e in ok:
            for k, b in enumerate(reversed(m5h)):
                if (e["dir"] == "BULL" and float(b["close"]) > e["level"]) or \
                   (e["dir"] == "BEAR" and float(b["close"]) < e["level"]):
                    ages.append(k)
                    break
        if ages:
            bos_ages.append(max(ages))

    p = bos_ok / bias_ne * 100 if bias_ne else 0
    a = sorted(bos_ages)
    out = {
        "source": "cache dataset_m1/m5/m15_fresh (8 Apr - 9 Sep, ~5 bulan); "
                  "H4 = agregasi 16xM15 (label eksplisit)",
        "n_samples": n, "bias_non_neutral": bias_ne,
        "bos_searah_ok": bos_ok,
        "p_bos_given_bias_non_neutral_pct": round(p, 1),
        "bos_age_m5_bars": ({"n": len(a), "p25": a[len(a)//4],
                             "median": a[len(a)//2], "p75": a[3*len(a)//4],
                             "max": a[-1]} if a else None),
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
