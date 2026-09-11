# Dekomposisi sesi MICRO v2.1.1 (replay 41 hari) - owner 2026-09-11.
#
# Pertanyaan owner: apa yang membedakan sesi London vs sesi lain di backtest,
# berapa WR per sesi, dan WR per sesi per hari. Tujuan: varian MICRO yang
# AKTIF HANYA di sesi London (jendela emas dgn tuning per sesi, bukan avoidance).
#
# Sumber: data/research/micro_v2/study_results_v2_v11.json (trades varian
# v1.1|65_35|M0.9_T1.4 - konfigurasi live MICRO saat ini).
# Blok sesi = kontrak R1 Stage 1 (UTC): asia 0-7, london 7-12,
# overlap 12-16, ny_late 16-24. Output CSV/JSON memakai jam UTC; konversi
# WIB = UTC+7 ditampilkan di laporan.
#
# Read-only terhadap bridge; tulis hanya di data/research/micro_v2/.

import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "research" / "micro_v2" / "study_results_v2_v11.json"
OUT_DIR = ROOT / "data" / "research" / "micro_v2"

SESSIONS = (
    ("asia", 0, 7),
    ("london", 7, 12),
    ("overlap", 12, 16),
    ("ny_late", 16, 24),
)


def session_of(iso_ts: str) -> str:
    h = datetime.fromisoformat(iso_ts).hour  # sudah UTC (dibuat dgn tz=utc)
    for name, a, b in SESSIONS:
        if a <= h < b:
            return name
    return "?"


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    row = next(r for r in data["rows"] if r["varian"].startswith("v1.1"))
    trades = row["trades"]
    days = data["window"]["days"]
    print(f"sumber: {SRC.name} | varian {row['varian']} | n={len(trades)} | "
          f"jendela {days} hari\n")

    # 1) agregat per sesi
    per = defaultdict(lambda: {"n": 0, "w": 0, "gross": 0.0, "sl": [], "tp": [],
                               "hours": defaultdict(lambda: [0, 0]),
                               "patterns": defaultdict(lambda: [0, 0]),
                               "dirs": defaultdict(lambda: [0, 0])})
    for t in trades:
        s = session_of(t["time"])
        p = per[s]
        p["n"] += 1
        p["gross"] += t["gross_pts"]
        p["sl"].append(t["sl_pts"])
        p["tp"].append(t["tp_pts"])
        if t["outcome"] == "TP":
            p["w"] += 1
        h = datetime.fromisoformat(t["time"]).hour
        p["hours"][h][0] += 1
        p["hours"][h][1] += 1 if t["outcome"] == "TP" else 0
        if t.get("pattern"):
            p["patterns"][t["pattern"]][0] += 1
            p["patterns"][t["pattern"]][1] += 1 if t["outcome"] == "TP" else 0
        p["dirs"][t["dir"]][0] += 1
        p["dirs"][t["dir"]][1] += 1 if t["outcome"] == "TP" else 0

    print("== WR & karakter per sesi (UTC; WIB = +7) ==")
    hdr = (f"{'sesi':9s} {'n':>4s} {'W/L':>9s} {'WR%':>6s} {'gross/tr':>9s} "
           f"{'avgSL':>6s} {'avgTP':>6s} {'n/hari':>7s}")
    print(hdr)
    print("-" * len(hdr))
    for name, a, b in SESSIONS:
        p = per[name]
        closed_wl = f"{p['w']}/{p['n'] - p['w']}"
        wr = p["w"] / p["n"] * 100 if p["n"] else 0.0
        gpt = p["gross"] / p["n"] if p["n"] else 0.0
        avgsl = statistics.mean(p["sl"]) if p["sl"] else 0
        avgtp = statistics.mean(p["tp"]) if p["tp"] else 0
        print(f"{name:9s} {p['n']:4d} {closed_wl:>9s} {wr:6.1f} {gpt:9.1f} "
              f"{avgsl:6.0f} {avgtp:6.0f} {p['n'] / days:7.2f}")

    # 2) per sesi per hari
    by_day = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # day -> sesi -> [n, w]
    for t in trades:
        dt = datetime.fromisoformat(t["time"])
        day = dt.strftime("%m-%d")
        s = session_of(t["time"])
        by_day[day][s][0] += 1
        by_day[day][s][1] += 1 if t["outcome"] == "TP" else 0

    print("\n== WR per sesi per hari (cell = WR% (n); kosong = tak ada trade) ==")
    sess_names = [s for s, _, _ in SESSIONS]
    print(f"{'hari':6s} " + " ".join(f"{s:>12s}" for s in sess_names))
    for day in sorted(by_day):
        cells = []
        for s in sess_names:
            n, w = by_day[day].get(s, [0, 0])
            cells.append(f"{(w / n * 100):5.0f}% ({n:2d})" if n else "-")
        print(f"{day:6s} " + " ".join(f"{c:>12s}" for c in cells))

    # 3) jam per sesi (deteksi jam terbaik london)
    print("\n== Jam terbaik (n>=10) ==")
    all_hours = defaultdict(lambda: [0, 0])
    for t in trades:
        h = datetime.fromisoformat(t["time"]).hour
        all_hours[h][0] += 1
        all_hours[h][1] += 1 if t["outcome"] == "TP" else 0
    for h in sorted(all_hours):
        n, w = all_hours[h]
        if n >= 10:
            print(f"  {h:02d}:00 UTC ({(h + 7) % 24:02d}:00 WIB) n={n:3d} "
                  f"WR={w / n * 100:5.1f}%")

    # 4) pola & arah di london
    print("\n== Profil LONDON: pola & arah ==")
    p = per["london"]
    for pat, (n, w) in sorted(p["patterns"].items(), key=lambda kv: -kv[1][0]):
        print(f"  {pat:22s} n={n:3d} WR={w / n * 100:5.1f}%")
    for d, (n, w) in sorted(p["dirs"].items()):
        print(f"  arah {d:4s} n={n:3d} WR={w / n * 100:5.1f}%")

    # simpan artefak
    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "source": SRC.name,
        "variant": row["varian"],
        "n_trades": len(trades),
        "days": days,
        "sessions_utc": {n: [a, b] for n, a, b in SESSIONS},
        "per_session": {name: {
            "n": p["n"], "wins": p["w"],
            "wr": round(p["w"] / p["n"] * 100, 1) if p["n"] else None,
            "gross_pts": round(p["gross"], 1),
            "gross_per_trade": round(p["gross"] / p["n"], 2) if p["n"] else None,
            "avg_sl_pts": round(statistics.mean(p["sl"]), 1) if p["sl"] else None,
            "avg_tp_pts": round(statistics.mean(p["tp"]), 1) if p["tp"] else None,
            "trades_per_day": round(p["n"] / days, 2),
            "by_hour": {str(h): {"n": v[0], "wins": v[1]} for h, v in sorted(p["hours"].items())},
            "patterns": {k: {"n": v[0], "wins": v[1]} for k, v in sorted(p["patterns"].items(), key=lambda kv: -kv[1][0])},
            "dirs": {k: {"n": v[0], "wins": v[1]} for k, v in p["dirs"].items()},
        } for name, p in per.items()},
        "per_day_per_session": {day: {s: {"n": v[0], "wr": round(v[1] / v[0] * 100, 1)}
                                      for s, v in ses.items() if v[0]}
                                for day, ses in sorted(by_day.items())},
    }
    out_path = OUT_DIR / "session_decomp_v11.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nartefak: {out_path}")


if __name__ == "__main__":
    main()
