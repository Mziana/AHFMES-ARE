# REPLAY SENSITIVITY SMC v3 — review prio 4 (kurva threshold), 7 (POI_REACH),
# 8 (window sideways) dalam SATU infrastruktur replay.
#
# Dua pass, dua sumber data:
#   pass "trend"  — bridge, jendela DIPIN ke artefak studi lama (39.2 hari)
#   pass "side"   — cache R1 (M1 150k/M5/M15), window sideways terpilih dari
#                   smc_v3_regime_scan.json (dipilih TANPA melihat PnL):
#                   2026-06-04T21:52 +10 hari — ER 0.0044 (terendah), range
#                   16.0xATR-H4, structure_trend None, ATR5 mean 674p.
#
# Konfigurasi POI (4) dievaluasi TERPISAH di engine (jangkauan zona
# mengubah POI terpilih → SL/TP1/RR berubah — bukan rescorable):
#   poi_d150 (default 1.5xATR reach) | poi_d075 (0.75xATR) |
#   poi_d050 (0.5xATR) | poi_strict (in-zone, desain §3.1)
#
# Dua lapis hasil per konfig:
#   "signals" — SEMUA bar dgn skor >= TAKE_FLOOR & jalur skor penuh
#               (RR/SL lolos), TANPA gating posisi (bebas bias seleksi)
#               → kurva threshold 6..12 & segmentasi skor (prio 3/4).
#   "trades"  — hanya skor >= threshold engine (8) dengan gating posisi
#               (busy/cooldown, parity studi lama) → headline comparable.
#
# Kedalaman feed diemulasi seperti studi (M5 8000 / M15 3000 / H4 250).
# Posisi menutup lewat batas jendela di-DROP. Biaya sel R1: base 17 /
# must 27.5 (bandingable). News gate OFF (keputusan owner).
from __future__ import annotations

import json
import os
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from strategy_v2 import candle_scoring as CS  # noqa: E402
from strategy_v2 import smc, smc_exits as EX  # noqa: E402

BRIDGE = "http://127.0.0.1:18888"
TOKEN_FILE = ROOT / "data" / "bridge_token.txt"
OUT_DIR = ROOT / "data" / "research" / "smc_v3"
OUT_FILE = OUT_DIR / "smc_v3_sensitivity_replay.json"

BASE_COST_PTS = 17.0
MUST_COST_PTS = 27.5
M1W, M5W, M15W, H4W = 400, 400, 300, 250
COOLDOWN_S = 5 * 60
SPREAD_PTS = 17.0
FEED_M5, FEED_M15, FEED_H4 = 8000, 3000, 250
TAKE_FLOOR = 6
SCORES = list(range(6, 13))
ENGINE_THRESHOLD = smc.SCORE_THRESHOLD   # 8
CACHE_M1 = ROOT / "data/research/r1/dataset_m1.json"
CACHE_M5 = ROOT / "data/research/r1/dataset_m5_fresh.json"
CACHE_M15 = ROOT / "data/research/r1/dataset_m15_fresh.json"
SMOKE = bool(os.environ.get("SMC_SMOKE"))

TREND_START = "2026-08-03T11:39:00+00:00"
TREND_CUTOFF = "2026-09-11T17:09:00+00:00"
SIDE_START = "2026-06-04T21:52:00+00:00"   # dari regime-scan (buta PnL)
SIDE_DAYS = 10

POI_CFGS = {
    "poi_d150": {"poi_mode": "reach", "poi_reach": 1.5,
                 "note": "default 1.5xATR (legacy)"},
    "poi_d075": {"poi_mode": "reach", "poi_reach": 0.75,
                 "note": "0.75xATR — setengah jangkauan default"},
    "poi_d050": {"poi_mode": "reach", "poi_reach": 0.5,
                 "note": "0.5xATR — jangkauan ketat"},
    "poi_strict": {"poi_mode": "strict", "poi_reach": None,
                   "note": "strict in-zone (desain §3.1 literal)"},
}
EXIT_MODES = ("legacy", "g2")
SESSIONS = (("asia", 0, 7), ("london", 7, 12),
            ("overlap", 12, 16), ("ny_late", 16, 24))


def iso_ts(s: str) -> int:
    return int(datetime.fromisoformat(s).timestamp())


def fetch(path: str) -> dict:
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    req = urllib.request.Request(BRIDGE + path,
                                 headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def load_cache(path: Path) -> list:
    d = json.loads(path.read_text(encoding="utf-8"))
    return d.get("candles", d if isinstance(d, list) else [])


def m15_to_h4(m15: list) -> list:
    """Agregasi M15 -> H4 per kelipatan 4 jam UTC (bucket penuh 16 bar)."""
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


def m1_from_m5(m5: list) -> list:
    """M1 sintetis dari M5 (cache tak punya M1 utk 10 Jun): 5 bar per M5.

    HANYA untuk exit-sim & jendela M1 engine — struktur sinyal tetap dari
    M5/M15 asli; pola M1 = pola M5 (labeled eksplisit di artefak)."""
    out = []
    for b in m5:
        o, h, l, c = (float(b[k]) for k in ("open", "high", "low", "close"))
        t = int(b["time"])
        out.append({"time": t, "open": o, "high": h, "low": l, "close": c})
        if h != o or l != o:
            out.append({"time": t + 60, "open": o, "high": h,
                        "low": min(l, o), "close": o})
        out.append({"time": t + 120, "open": o, "high": max(h, c),
                    "low": min(l, o), "close": c})
        if h != c or l != c:
            out.append({"time": t + 180, "open": c, "high": max(h, c),
                        "low": l, "close": c})
        out.append({"time": t + 240, "open": c, "high": h, "low": l,
                    "close": c})
    return out


def session_of(t: int) -> str:
    h = datetime.fromtimestamp(t, tz=timezone.utc).hour
    for name, a, b in SESSIONS:
        if a <= h < b:
            return name
    return "?"


def make_entry(base: dict, bar: dict, t: int) -> dict:
    return {"t": datetime.fromtimestamp(t, tz=timezone.utc).isoformat(),
            "dir": base["direction"], "score": int(base["score"]),
            "rr": base.get("rr"), "sl_pts": base.get("sl_pts"),
            "tp1_pts": base.get("tp1_pts"),
            "poi_dist_atr": base.get("poi_dist_atr"),
            "sess": session_of(t)}


def poi_dist_atr(base: dict, price: float, m15_hist: list,
                 m5_hist: list):
    """Jarak harga ke POI terpilih / ATR TF-seleksi (replikasi rumus engine)."""
    poi = base.get("poi")
    if not poi:
        return None
    top, bot = poi["top"], poi["bottom"]
    dist = 0.0 if bot <= price <= top else (
        (bot - price) if price < bot else (price - top))
    a15 = CS.atr(m15_hist) or 0.0
    a5 = CS.atr(m5_hist) or 0.0
    a_sel = a15 if a15 else a5
    return round(dist / a_sel, 3) if a_sel else None


def summarize(entries: list) -> dict:
    n = len(entries)
    w = sum(1 for x in entries if x["gross"] > 0)
    gp = sum(x["gross"] for x in entries) / n if n else 0.0
    return {
        "n": n,
        "signals_per_day": None,  # diisi penelepon
        "win_rate_pct": round(w / n * 100, 1) if n else None,
        "gross_pts_per_trade": round(gp, 2) if n else None,
        "net_base_pts": round(gp - BASE_COST_PTS, 2) if n else None,
        "net_must_pts": round(gp - MUST_COST_PTS, 2) if n else None,
        "outcomes": dict(Counter(x["oc"] for x in entries)),
        "by_threshold": {
            str(th): {
                "n": sum(1 for x in entries if x["score"] >= th),
                "win": sum(1 for x in entries if x["score"] >= th
                           and x["gross"] > 0),
                "gross_pts": round(sum(x["gross"] for x in entries
                                       if x["score"] >= th), 1),
            } for th in SCORES},
        "by_score": {},
        "by_dir": {}, "by_sess": {},
    }


def fill_breakdowns(s: dict, entries: list, days: float) -> None:
    s["signals_per_day"] = round(s["n"] / days, 2) if days else None
    for attr, key in (("dir", "by_dir"), ("sess", "by_sess")):
        acc = {}
        for x in entries:
            b = acc.setdefault(x[attr], [0, 0, 0.0])
            b[0] += 1
            b[1] += 1 if x["gross"] > 0 else 0
            b[2] = round(b[2] + x["gross"], 1)
        s[key] = acc
    acc = {}
    for x in entries:
        b = acc.setdefault(str(x["score"]), [0, 0, 0.0])
        b[0] += 1
        b[1] += 1 if x["gross"] > 0 else 0
        b[2] = round(b[2] + x["gross"], 1)
    s["by_score"] = acc


def run_pass(name: str, m1_all: list, m5_all: list, m15_all: list,
             h4_all: list, poi_cfgs: dict, synthetic: bool = False) -> dict:
    m1_by_time = {int(b["time"]): b for b in m1_all}
    m1_times = sorted(m1_by_time)
    m5_by_time = {int(b["time"]): b for b in m5_all}
    m5_times = sorted(m5_by_time)
    m15_times = sorted(int(b["time"]) for b in m15_all)
    h4_times = sorted(int(b["time"]) for b in h4_all)
    t0, t1 = int(m1_all[0]["time"]), int(m1_all[-1]["time"])
    days = (t1 - t0) / 86400.0
    print(f"[{name}] M1 {len(m1_all)} | M5 {len(m5_all)} | M15 {len(m15_all)} "
          f"| H4 {len(h4_all)} | jendela {days:.2f} hari "
          f"({datetime.fromtimestamp(t0, tz=timezone.utc):%m-%d %H:%M} -> "
          f"{datetime.fromtimestamp(t1, tz=timezone.utc):%m-%d %H:%M} UTC)",
          flush=True)

    sig = {k: {"legacy": [], "g2": []} for k in poi_cfgs}
    trd = {k: {"legacy": [], "g2": []} for k in poi_cfgs}
    blocked = {k: Counter() for k in poi_cfgs}
    busy = {k: 0.0 for k in poi_cfgs}
    last_ent = {k: 0.0 for k in poi_cfgs}
    idx5 = idx15 = idx4 = -1
    n_eval = 0
    # M1 sintetis (5 bar/M5): warmup 400 M5; M1 bridge asli: warmup 400 M1
    start_i = M5W * 5 if synthetic else M1W
    for i in range(start_i, len(m1_all)):
        bar = m1_all[i]
        t = int(bar["time"])
        while idx5 + 1 < len(m5_times) and m5_times[idx5 + 1] + 300 <= t:
            idx5 += 1
        while idx15 + 1 < len(m15_times) and m15_times[idx15 + 1] + 900 <= t:
            idx15 += 1
        while idx4 + 1 < len(h4_times) and h4_times[idx4 + 1] + 14400 <= t:
            idx4 += 1
        if idx5 < 30 or idx15 < 30 or idx4 < 25:
            continue
        m1_hist = m1_all[i + 1 - M1W: i + 1]
        m5_hist = m5_all[max(0, idx5 + 1 - M5W): idx5 + 1]
        m15_hist = m15_all[max(0, idx15 + 1 - M15W): idx15 + 1]
        h4_hist = h4_all[max(0, idx4 + 1 - H4W): idx4 + 1]
        n_eval += 1

        for key, cfg in poi_cfgs.items():
            r = smc.evaluate(m1_hist, m5_hist, m15_hist, h4_hist,
                             spread_pts=SPREAD_PTS,
                             poi_mode=cfg["poi_mode"],
                             poi_reach=cfg["poi_reach"])
            if r["take"] or (r["components"] and r["score"] >= TAKE_FLOOR):
                res_leg = EX.simulate(r["direction"], float(bar["close"]),
                                      r["sl"], r["tp1"], t, m1_by_time,
                                      m1_times, mode="legacy", atr_fn=CS.atr)
                if res_leg["outcome"] in ("OPEN", "OPEN_TP1"):
                    blocked[key]["masih_open"] += 1
                    continue
                res_g2 = EX.simulate(r["direction"], float(bar["close"]),
                                     r["sl"], r["tp1"], t, m1_by_time,
                                     m1_times, mode="g2", atr_fn=CS.atr)
                e = make_entry(r, bar, t)
                e["poi_dist_atr"] = poi_dist_atr(r, float(bar["close"]),
                                                 m15_hist, m5_hist)
                e_leg = dict(e, gross=round(res_leg["gross_pts"], 1),
                             oc=res_leg["outcome"])
                e_g2 = dict(e, gross=round(res_g2["gross_pts"], 1),
                            oc=res_g2["outcome"])
                # lapis sinyal: tanpa gating posisi (bebas bias seleksi)
                sig[key]["legacy"].append(e_leg)
                sig[key]["g2"].append(e_g2)
                # lapis trade: gating posisi, hanya skor >= threshold engine
                if r["take"]:
                    if t < busy[key]:
                        blocked[key]["posisi_terbuka"] += 1
                        continue
                    if last_ent[key] and t - last_ent[key] < COOLDOWN_S:
                        blocked[key]["cooldown"] += 1
                        continue
                    trd[key]["legacy"].append(e_leg)
                    trd[key]["g2"].append(e_g2)
                    busy[key] = float(res_leg["exit_time"]) + 60.0
                    last_ent[key] = float(t)
            elif r["components"]:
                blocked[key][f"skor<{TAKE_FLOOR}"] += 1

    out_cfg = {}
    for key in poi_cfgs:
        modes = {}
        for mode in EXIT_MODES:
            s_sig = summarize(sig[key][mode])
            fill_breakdowns(s_sig, sig[key][mode], days)
            s_trd = summarize(trd[key][mode])
            fill_breakdowns(s_trd, trd[key][mode], days)
            modes[mode] = {"signals": s_sig, "trades": s_trd}
        out_cfg[key] = {"note": poi_cfgs[key]["note"], "modes": modes,
                        "blocked": dict(blocked[key])}
    return {"window_utc": [datetime.fromtimestamp(t0, tz=timezone.utc)
                           .isoformat(),
                           datetime.fromtimestamp(t1, tz=timezone.utc)
                           .isoformat()],
            "days": round(days, 2), "n_evaluated_bars": n_eval,
            "configs": out_cfg}


def main() -> int:
    poi_cfgs = dict(POI_CFGS)
    passes = {}

    # ── pass A: trending (bridge, jendela terpin ke studi lama) ──
    t_start, cutoff = iso_ts(TREND_START), iso_ts(TREND_CUTOFF)
    m1_raw = fetch("/candles?symbol=XAUUSD&timeframe=M1&count=60000")["candles"][:-1]
    m5_raw = fetch("/candles?symbol=XAUUSD&timeframe=M5&count=14000")["candles"][:-1]
    m15_raw = fetch("/candles?symbol=XAUUSD&timeframe=M15&count=6500")["candles"][:-1]
    h4_raw = fetch("/candles?symbol=XAUUSD&timeframe=H4&count=250")["candles"][:-1]
    m1_all = [b for b in m1_raw if t_start <= int(b["time"]) < cutoff]
    if SMOKE:   # segmen aktif (offset 30k = awal Sep, H4 non-netral)
        m1_all = m1_all[30000:30000 + M1W + 1000]
    m5_all = [b for b in m5_raw if int(b["time"]) + 300 <= cutoff][-FEED_M5:]
    m15_all = [b for b in m15_raw if int(b["time"]) + 900 <= cutoff][-FEED_M15:]
    h4_all = [b for b in h4_raw if int(b["time"]) + 14400 <= cutoff][-FEED_H4:]
    passes["trend"] = run_pass("trend", m1_all, m5_all, m15_all, h4_all,
                               poi_cfgs, synthetic=False)

    # ── pass B: sideways (cache R1, window hasil regime-scan buta) ──
    s_start = iso_ts(SIDE_START)
    s_end = s_start + SIDE_DAYS * 86400
    c5 = [b for b in load_cache(CACHE_M5)
          if int(b["time"]) + 300 <= s_end][-FEED_M5:]
    c15 = [b for b in load_cache(CACHE_M15)
           if int(b["time"]) + 900 <= s_end][-FEED_M15:]
    h4c = m15_to_h4(c15)
    m1s = [b for b in m1_from_m5(c5)
           if s_start <= int(b["time"]) < s_end]   # HANYA window terpilih
    if SMOKE:
        m1s = m1s[:M5W * 5 + 1000]   # warmup 2000 + 1000 bar evaluasi
    passes["side"] = run_pass("side", m1s, c5, c15, h4c, poi_cfgs,
                              synthetic=True)

    out = {"meta": {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "smoke": SMOKE,
        "biaya": {"base": BASE_COST_PTS, "must": MUST_COST_PTS,
                  "label": "ESTIMATED_COST_MODEL — arah perbandingan, bukan "
                           "dollar; sim understates live (−12.34$ vs −28.32$)"},
        "side_window_dipilih": "smc_v3_regime_scan.py (buta PnL): ER terendah "
                               "0.0044, range 16.0xATR-H4, trend None, "
                               "ATR5 mean 674p — 2026-06-04T21:52+10d UTC",
        "poi_configs": {k: c["note"] for k, c in poi_cfgs.items()},
        "take_floor": TAKE_FLOOR, "scores": SCORES,
        "engine_threshold": ENGINE_THRESHOLD,
        "catatan": [
            "news gate OFF (keputusan owner)",
            "SL-priority ambigu (konservatif); exit legacy = parity studi lama",
            "signals = tanpa gating posisi (bebas bias seleksi, utk kurva "
            "threshold); trades = gating busy/cooldown parity (skor >= 8)",
            "pass side: M1 sintetis 5-bar/M5 utk exit-sim & window M1; "
            "struktur sinyal dari M5/M15 asli",
            "posisi open di akhir jendela di-drop (masih_open)",
            "cooldown 5m, 1 posisi; busy dihitung dari exit legacy"]},
        "passes": passes}
    OUT_FILE.write_text(json.dumps(out, indent=1), encoding="utf-8")
    _print_report(passes)
    return 0


def _print_report(passes: dict) -> None:
    def f2(v):
        return f"{v:8.2f}" if v is not None else "    None"

    for pname, p in passes.items():
        print(f"\n== PASS {pname.upper()} — {p['days']} hari, "
              f"{p['n_evaluated_bars']} bar evaluasi ==")
        for key, c in p["configs"].items():
            for mode in EXIT_MODES:
                m = c["modes"][mode]["trades"]
                s = c["modes"][mode]["signals"]
                wr = m['win_rate_pct']
                print(f"  {key:11s} {mode:6s} trade n={m['n']:3d} "
                      f"WR={(wr if wr is not None else 0):5.1f}% "
                      f"gross={f2(m['gross_pts_per_trade'])} "
                      f"net_must={f2(m['net_must_pts'])} | "
                      f"sig n={s['n']}")
    print(f"artefak: {OUT_FILE}")


if __name__ == "__main__":
    raise SystemExit(main())
