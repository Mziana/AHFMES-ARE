# STUDI OFFLINE - SMC/ICT v3 (kandidat pengganti MICRO, rencana owner 11 Sep)
# Filosofi: "HTF memberi peta, LTF memberi pemicu" - tunggu di ZONA (POI),
# lalu tuntut BUKTI (sweep + CHoCH mikro + pola) sebelum entry. Skor confluence
# 12 poin, gate RR>=1.3, SL struktural di luar POI/sweep + buffer 0.15xATR-M5.
# Murni OFFLINE & read-only terhadap bridge: mirror persis jendela driver live
# (M1 400 / M5 400 bar), cooldown 5 menit, satu posisi, eksekusi di close M1,
# first-touch SL/TP di bar M1 berikutnya (SL-priority saat ambigu).
# Sel biaya kontrak R1 Stage 1: base 17 poin; must = x1.5 + slip2 = 27.5 poin.
# Kriteria keputusan (parity kontrak): expNet_must > 0 DAN n >= 30.
# Label biaya: ESTIMATED_COST_MODEL (spread snapshot, bukan historis per-bar).
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

from strategy_v2 import smc  # noqa: E402

BRIDGE = "http://127.0.0.1:18888"
TOKEN_FILE = ROOT / "data" / "bridge_token.txt"
OUT_DIR = ROOT / "data" / "research" / "smc_v3"
OUT_DIR.mkdir(parents=True, exist_ok=True)

POINT = 0.01
BASE_COST_PTS = 17.0
MUST_COST_PTS = 27.5
M1_WINDOW = 400          # == jendela driver live
M5_WINDOW = 400          # == jendela driver live
M15_WINDOW = 300
H4_WINDOW = 250
COOLDOWN_S = 5 * 60      # parity live MICRO
MAX_HOLD_S = 24 * 3600   # posisi nyangkut > 1 hari → expire di close (mtm)
SPREAD_PTS = 17.0        # snapshot demo (ESTIMATED_COST_MODEL)

SESSIONS = (             # parity micro_v2_session_decomp (UTC)
    ("asia", 0, 7),
    ("london", 7, 12),
    ("overlap", 12, 16),
    ("ny_late", 16, 24),
)

# Alasan no-trade yang dipetakan ke bucket funnel (dari smc.evaluate.reason)
BLOCK_MAP = {
    "data TF kurang": "data_kurang",
    "bias H4 netral/campur": "bias_h4_netral",
    "tidak ada acuan SL struktural (POI/sweep)": "tanpa_sl_struktural",
    "tidak ada target likuiditas searah": "tanpa_target_likuiditas",
}


def get(path: str) -> dict:
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    req = urllib.request.Request(BRIDGE + path,
                                 headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def session_of(epoch: int) -> str:
    h = datetime.fromtimestamp(epoch, tz=timezone.utc).hour
    for name, a, b in SESSIONS:
        if a <= h < b:
            return name
    return "?"


def block_bucket(reason: str) -> str:
    for k, v in BLOCK_MAP.items():
        if reason.startswith(k[:20]):
            return v
    if reason.startswith("RR "):
        return "rr_gate"
    if reason.startswith("skor"):
        return "skor_threshold"
    return "lain:" + reason.split("(")[0].strip()[:40]


def first_touch(direction: str, sl: float, tp: float, entry_time: int,
                m1_by_time: dict, m1_times: list, now_epoch: int) -> dict:
    """First-touch SL/TP dari bar M1 SETELAH bar sinyal (SL-priority ambigu).
    EXPIRE bila >MAX_HOLD_S tanpa sentuhan (mark-to-market di close)."""
    start = bisect.bisect_right(m1_times, entry_time)
    for k in range(start, len(m1_times)):
        t = m1_times[k]
        if t - entry_time > MAX_HOLD_S:
            b = m1_by_time[t]
            return {"outcome": "EXPIRE", "exit_px": float(b["close"]),
                    "exit_time": t + 60, "exit_epoch": now_epoch}
        b = m1_by_time[t]
        if direction == "BUY":
            hit_sl = b["low"] <= sl
            hit_tp = b["high"] >= tp
        else:
            hit_sl = b["high"] >= sl
            hit_tp = b["low"] <= tp
        if hit_sl:
            return {"outcome": "SL", "exit_px": sl, "exit_time": t + 60,
                    "exit_epoch": now_epoch}
        if hit_tp:
            return {"outcome": "TP", "exit_px": tp, "exit_time": t + 60,
                    "exit_epoch": now_epoch}
    return {"outcome": "OPEN", "exit_px": None, "exit_time": None,
            "exit_epoch": None}


def run_study() -> dict:
    print("fetch data ...", flush=True)
    m1_all = get("/candles?symbol=XAUUSD&timeframe=M1&count=40000").get("candles", [])[:-1]
    m5_all = get("/candles?symbol=XAUUSD&timeframe=M5&count=8000").get("candles", [])[:-1]
    m15_all = get("/candles?symbol=XAUUSD&timeframe=M15&count=3000").get("candles", [])[:-1]
    h4_all = get("/candles?symbol=XAUUSD&timeframe=H4&count=250").get("candles", [])[:-1]
    m1_by_time = {b["time"]: b for b in m1_all}
    m1_times = sorted(m1_by_time)
    m5_by_time = {b["time"]: b for b in m5_all}
    m5_times = sorted(m5_by_time)
    m15_times = sorted(b["time"] for b in m15_all)
    h4_times = sorted(b["time"] for b in h4_all)
    t0, t1 = m1_times[0], m1_times[-1]
    days = (t1 - t0) / 86400.0
    print(f"M1 {len(m1_all)} | M5 {len(m5_all)} | M15 {len(m15_all)} | "
          f"H4 {len(h4_all)} bar | jendela {days:.1f} hari "
          f"({datetime.fromtimestamp(t0, tz=timezone.utc):%m-%d %H:%M} -> "
          f"{datetime.fromtimestamp(t1, tz=timezone.utc):%m-%d %H:%M} UTC)",
          flush=True)

    st = {"n": 0, "win": 0, "gross_pts": 0.0, "trades": [], "by_dir": {},
          "by_sess": {}, "by_hour": {}, "outcomes": Counter(),
          "reasons": Counter(), "score_hist": Counter(), "busy": 0}
    last_entry = 0.0
    busy_until = 0.0

    idx5 = idx15 = idx4 = -1
    n_eval = 0
    for i in range(M1_WINDOW, len(m1_all)):
        bar = m1_all[i]
        t = int(bar["time"])
        now_epoch = int(datetime.now(tz=timezone.utc).timestamp())

        while idx5 + 1 < len(m5_times) and m5_times[idx5 + 1] + 300 <= t:
            idx5 += 1
        while idx15 + 1 < len(m15_times) and m15_times[idx15 + 1] + 900 <= t:
            idx15 += 1
        while idx4 + 1 < len(h4_times) and h4_times[idx4 + 1] + 14400 <= t:
            idx4 += 1

        m1_hist = m1_all[i + 1 - M1_WINDOW: i + 1]
        m5_hist = m5_all[max(0, idx5 + 1 - M5_WINDOW): idx5 + 1] if idx5 >= 0 else []
        m15_hist = m15_all[max(0, idx15 + 1 - M15_WINDOW): idx15 + 1] if idx15 >= 0 else []
        h4_hist = h4_all[: idx4 + 1][-H4_WINDOW:] if idx4 >= 0 else []

        if t < busy_until:
            st["busy"] += 1
            continue
        if last_entry and t - last_entry < COOLDOWN_S:
            st["reasons"]["cooldown"] += 1
            continue

        r = smc.evaluate(m1_hist, m5_hist, m15_hist, h4_hist, spread_pts=SPREAD_PTS)
        n_eval += 1
        st["score_hist"][int(r["score"])] += 1
        if not r.get("take"):
            st["reasons"][block_bucket(r["reason"])] += 1
            continue

        dir_str = r["direction"]
        entry_px = float(bar["close"])
        sl, tp = r["sl"], r["tp1"]
        last_entry = float(t)
        out = first_touch(dir_str, sl, tp, t, m1_by_time, m1_times, now_epoch)
        if out["outcome"] == "OPEN":  # data habis saat posisi masih terbuka
            st["reasons"]["masih_open_di_akhir_data"] += 1
            last_entry = 0.0  # tidak mengunci sisa loop
            continue
        sign = 1 if dir_str == "BUY" else -1
        gross = round(sign * (out["exit_px"] - entry_px) / POINT, 1)
        st["outcomes"][out["outcome"]] += 1
        st["n"] += 1
        st["win"] += 1 if gross > 0 else 0
        st["gross_pts"] = round(st["gross_pts"] + gross, 1)
        busy_until = float(out["exit_time"])
        sess = session_of(t)
        st["by_sess"].setdefault(sess, [0, 0, 0.0])
        st["by_sess"][sess][0] += 1
        st["by_sess"][sess][1] += 1 if gross > 0 else 0
        st["by_sess"][sess][2] = round(st["by_sess"][sess][2] + gross, 1)
        st["by_dir"].setdefault(dir_str, [0, 0, 0.0])
        st["by_dir"][dir_str][0] += 1
        st["by_dir"][dir_str][1] += 1 if gross > 0 else 0
        st["by_dir"][dir_str][2] = round(st["by_dir"][dir_str][2] + gross, 1)
        h = datetime.fromtimestamp(t, tz=timezone.utc).hour
        st["by_hour"].setdefault(h, [0, 0, 0.0])
        st["by_hour"][h][0] += 1
        st["by_hour"][h][1] += 1 if gross > 0 else 0
        st["by_hour"][h][2] = round(st["by_hour"][h][2] + gross, 1)
        st["trades"].append({
            "time": datetime.fromtimestamp(t, tz=timezone.utc).isoformat(),
            "dir": dir_str, "sess": sess, "hour": h,
            "entry": entry_px, "sl": sl, "tp": tp,
            "sl_pts": r["sl_pts"], "tp_pts": r["tp1_pts"], "rr": r["rr"],
            "score": r["score"], "outcome": out["outcome"],
            "gross_pts": gross,
            "net_base_pts": round(gross - BASE_COST_PTS, 1),
            "net_must_pts": round(gross - MUST_COST_PTS, 1),
        })

    n, w = st["n"], st["win"]
    gross_pt = st["gross_pts"] / n if n else 0.0
    net_base = gross_pt - BASE_COST_PTS
    net_must = gross_pt - MUST_COST_PTS
    verdict = ("GO-CANDIDATE" if (n >= 30 and net_must > 0) else
               "KILL (kriteria: expNet_must > 0 DAN n>=30)")
    summary = {
        "engine": "strategy_v2/smc.py (SMC/ICT v3)",
        "window_days": round(days, 1),
        "window_utc": [datetime.fromtimestamp(t0, tz=timezone.utc).isoformat(),
                       datetime.fromtimestamp(t1, tz=timezone.utc).isoformat()],
        "n_evaluated": n_eval,
        "n_signals_taken": n,
        "signals_per_day": round(n / days, 2) if days else None,
        "win_rate_pct": round(w / n * 100, 1) if n else None,
        "gross_pts_per_trade": round(gross_pt, 2),
        "net_base_pts_per_trade": round(net_base, 2),
        "net_must_pts_per_trade": round(net_must, 2),
        "outcomes": dict(st["outcomes"]),
        "avg_sl_pts": round(sum(x["sl_pts"] for x in st["trades"]) / n, 1) if n else None,
        "avg_tp_pts": round(sum(x["tp_pts"] for x in st["trades"]) / n, 1) if n else None,
        "avg_rr": round(sum(x["rr"] for x in st["trades"]) / n, 2) if n else None,
        "by_dir": {k: {"n": v[0], "wr_pct": round(v[1] / v[0] * 100, 1) if v[0] else None,
                       "gross_pts": v[2]} for k, v in st["by_dir"].items()},
        "by_session": {k: {"n": v[0], "wr_pct": round(v[1] / v[0] * 100, 1) if v[0] else None,
                           "gross_pts": v[2]} for k, v in st["by_sess"].items()},
        "by_hour": {h: {"n": v[0], "wr_pct": round(v[1] / v[0] * 100, 1) if v[0] else None,
                        "gross_pts": v[2]} for h, v in sorted(st["by_hour"].items())},
        "blocked": {"posisi_terbuka": st["busy"], **dict(st["reasons"])},
        "score_hist": {str(k): v for k, v in sorted(st["score_hist"].items())},
        "cost_label": "ESTIMATED_COST_MODEL",
        "cost_cells_pts": {"base": BASE_COST_PTS, "must": MUST_COST_PTS},
        "params": {"m1_window": M1_WINDOW, "m5_window": M5_WINDOW,
                   "m15_window": M15_WINDOW, "h4_window": H4_WINDOW,
                   "cooldown_s": COOLDOWN_S, "max_hold_s": MAX_HOLD_S,
                   "spread_pts": SPREAD_PTS, **{k: v for k, v in vars(smc).items()
                                                if k.isupper() and isinstance(
                                                    v, (int, float, str, tuple))}},
        "verdict": verdict,
    }
    return {"meta": {"fetched_at": datetime.now(tz=timezone.utc).isoformat(),
                     "bridge": BRIDGE, "symbol": "XAUUSD"},
            "summary": summary, "trades": st["trades"]}


def main() -> int:
    data = run_study()
    s = data["summary"]
    out = OUT_DIR / "smc_v3_replay.json"
    out.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"\n== SMC v3 replay ({s['window_days']} hari) ==")
    print(f"sinyal TAKE : {s['n_signals_taken']} "
          f"({s['signals_per_day']}/hari) dari {s['n_evaluated']} evaluasi")
    print(f"WR          : {s['win_rate_pct']}% | outcome {s['outcomes']}")
    print(f"gross/trade : {s['gross_pts_per_trade']} pts")
    print(f"net base    : {s['net_base_pts_per_trade']} pts/trade "
          f"(biaya {BASE_COST_PTS})")
    print(f"net must    : {s['net_must_pts_per_trade']} pts/trade "
          f"(biaya {MUST_COST_PTS})")
    print(f"avg SL/TP   : {s['avg_sl_pts']}/{s['avg_tp_pts']} pts | "
          f"avg RR {s['avg_rr']}")
    for k, v in s["by_dir"].items():
        print(f"  {k:4s}: n={v['n']} wr={v['wr_pct']}% gross={v['gross_pts']}")
    for k, v in s["by_session"].items():
        print(f"  {k:7s}: n={v['n']} wr={v['wr_pct']}% gross={v['gross_pts']}")
    top = sorted(s["blocked"].items(), key=lambda kv: -kv[1])[:8]
    print(f"block funnel: " + ", ".join(f"{k}={v}" for k, v in top))
    print(f"VERDICT     : {s['verdict']}")
    print(f"artefak     : {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
