# WR per hari utk MICRO v2.1 (SL/TP 0.9/1.4 x ATR M5) dari artefak studi offline.
# Mode = {v1.0, v1.2} x RSI {65/35, 70/30}. Pembanding: kontrol SCALP M5 produksi.
# Sumber: data/research/micro_v2/study_results_v2_sl09_tp14.json + control_scalp_m5.json
# (read-only; output: daily_wr.json + tabel konsol)
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "research" / "micro_v2"

MODES = [
    ("MICRO v1.0|RSI65/35 (LIVE)", "v1.0|65_35|M0.9_T1.4"),
    ("MICRO v1.0|RSI70/30", "v1.0|70_30|M0.9_T1.4"),
    ("MICRO v1.2|RSI65/35", "v1.2|65_35|M0.9_T1.4"),
    ("MICRO v1.2|RSI70/30", "v1.2|70_30|M0.9_T1.4"),
]


def day_of(iso: str) -> str:
    return datetime.fromisoformat(iso).astimezone(timezone.utc).strftime("%m-%d")


def agg(trades: list) -> dict:
    by = defaultdict(lambda: {"n": 0, "w": 0})
    for t in trades:
        d = day_of(t["time"])
        by[d]["n"] += 1
        by[d]["w"] += 1 if t["outcome"] == "TP" else 0
    return by


def main() -> int:
    study = json.loads((D / "study_results_v2_sl09_tp14.json").read_text(encoding="utf-8"))
    rows = {r["varian"]: r for r in study["rows"]}
    ctrl = json.loads((D / "control_scalp_m5.json").read_text(encoding="utf-8"))

    per_day = {}
    overall = {}
    for label, var in MODES:
        r = rows[var]
        per_day[label] = agg(r["trades"])
        overall[label] = {"n": r["entries"], "w": r["win"], "wr": r["wr"]}
    per_day["SCALP M5 (kontrol)"] = agg(ctrl["trades"])
    overall["SCALP M5 (kontrol)"] = {"n": ctrl["entries"], "w": ctrl["win"],
                                     "wr": ctrl["wr"]}

    labels = [l for l, _ in MODES] + ["SCALP M5 (kontrol)"]
    days = sorted({d for l in labels for d in per_day[l]})

    # tabel gabungan
    header = "hari   " + "".join(f"{l.split('|')[0][-4:] + '/' + (l.split('|')[1] if '|' in l else 'SCALP'):>11} "
                                 for l in labels)
    print("Cell = WR% (n=trade). Mode MICRO: vol/RSI-guard, semua SL/TP 0.9/1.4 ATR M5.")
    print(header)
    print("-" * len(header))
    for d in days:
        cells = []
        for l in labels:
            x = per_day[l].get(d)
            cells.append(f"{'—':>11} " if not x or not x["n"] else
                         f"{100 * x['w'] / x['n']:>5.0f}% (n={x['n']:>2}) ")
        print(f"{d}  " + "".join(cells))

    print("\nRINGKASAN")
    print(f"{'mode':28s} {'n':>5s} {'WR%':>6s} {'hari aktif':>10s} {'median n/hari':>13s} "
          f"{'hari WR>=50%':>12s} {'hari 0W':>8s}")
    for l in labels:
        by = per_day[l]
        active = [by[d] for d in days if by[d]["n"] > 0]
        ns = sorted(x["n"] for x in active)
        med_n = ns[len(ns) // 2] if ns else 0
        good = sum(1 for x in active if x["w"] / x["n"] >= 0.5)
        zero = sum(1 for x in active if x["w"] == 0)
        print(f"{l:28s} {overall[l]['n']:5d} {overall[l]['wr']:6.1f} {len(active):10d} "
              f"{med_n:13d} {good:12d} {zero:8d}")

    out = {"generated": datetime.now(timezone.utc).isoformat(),
           "window": study["window"],
           "note": "WR per hari dari replay offline 41 hari (first-touch, tanpa biaya); "
                   "hari = UTC. Mode MICRO = vol x RSI-guard, SL/TP 0.9/1.4 ATR M5.",
           "overall": overall,
           "per_day": {l: per_day[l] for l in labels}}
    (D / "daily_wr.json").write_text(json.dumps(out, indent=2, ensure_ascii=False),
                                     encoding="utf-8")
    print(f"\nartefak: {D / 'daily_wr.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
