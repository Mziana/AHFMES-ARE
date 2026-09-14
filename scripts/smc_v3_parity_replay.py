# REPLAY MULTI-VARIAN SMC v3 — full design parity (G1+G2+G3+G4) + baseline.
# v2 (audit artefak v1): perbaikan yang membuat v1 tidak valid:
#   - Jendela DIPIN KEDUA TEPI ke artefak replay lama (03 Agu 11:39 -> 11 Sep
#     17:09 UTC). v1 hanya memotong ujung akhir; tepi awal bergeser mengikuti
#     fetch -> baseline 141 vs 139.
#   - Kedalaman feed DIEMULASI ke fetch studi lama (M5 8000 / M15 3000 /
#     H4 250 bar; M1 difilter ke jendela) — 40k M1 = 8k M5 = 3k M15 menit-
#     trading, semua mencakup penuh jendela 39.2 hari (bar hanya ada saat
#     market buka), jadi emulasi ini meniru data yang dilihat studi lama.
#   - G4 memakai rantai penuh M15 -> H4 -> D1 (99 hari) — v1 memakai H4 250
#     bar asli -> hanya 12-23 bar D1 satu-hari -> structure_trend selalu None
#     -> veto semua sinyal (0 trade).
#   - Gate item-8 (G1) dihitung per bar dari ATR-M5 feed (field atr_m5_pts
#     engine hanya terisi di jalur TAKE).
#   - G3 tanpa evaluate ulang: rescore skor dari components.bos_ok +
#     bos_age_m5 (bobot BOS ditambah/dikurangkan; threshold sama).
# Semua varian: satu evaluate()/bar (konfigurasi legacy), keputusan per varian
# via rescoring + gate + veto D1; exit via strategy_v2.smc_exits.simulate
# (unit-tested): legacy = first-touch SL/TP (SL-priority ambigu, konservatif),
# g2 = desain §4 (TP1 50% -> BE -> trailing structure/ATR, TP2 via trailing).
# Posisi menutup lewat batas jendela di-DROP + dihitung terpisah (parity studi
# lama "masih_open_di_akhir_data").
# Read-only terhadap bridge & jalur live. Estimasi ~16-18 menit (SMC_SMOKE=1
# untuk smoke pendek).
from __future__ import annotations

import bisect
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
OUT_FILE = OUT_DIR / "smc_v3_parity_replay.json"
OLD_FILE = OUT_DIR / "smc_v3_replay.json"   # artefak studi lama (regresi silang)

POINT = 0.01
BASE_COST_PTS = 17.0
MUST_COST_PTS = 27.5
M1W, M5W, M15W, H4W = 400, 400, 300, 250   # == jendela driver live / studi lama
COOLDOWN_S = 5 * 60
SPREAD_PTS = 17.0
T_START_UTC = "2026-08-03T11:39:00+00:00"  # tepi awal artefak studi lama
CUTOFF_UTC = "2026-09-11T17:09:00+00:00"   # tepi akhir artefak studi lama
FEED_M5, FEED_M15, FEED_H4 = 8000, 3000, 250  # emulasi kedalaman fetch lama
SMOKE = bool(os.environ.get("SMC_SMOKE"))

SESSIONS = (("asia", 0, 7), ("london", 7, 12),
            ("overlap", 12, 16), ("ny_late", 16, 24))

# ── definisi varian ─────────────────────────────────────────────────────────
# exit_mode: "legacy" (first-touch parity studi lama) | "g2" (§4 partial+BE+trailing)
VARIANTS = {
    "baseline": {"exit_mode": "legacy", "bos_fresh": None, "gates": False,
                 "d1": False, "note": "parity studi lama (target 139 trade)"},
    "g2_exit":  {"exit_mode": "g2", "bos_fresh": None, "gates": False,
                 "d1": False, "note": "G2: TP1 50% -> BE -> trailing §4"},
    "g3_b24":   {"exit_mode": "legacy", "bos_fresh": 24, "gates": False,
                 "d1": False, "note": "G3 freshness BOS <= 24 bar M5"},
    "g3_b36":   {"exit_mode": "legacy", "bos_fresh": 36, "gates": False,
                 "d1": False, "note": "G3 freshness BOS <= 36 bar M5"},
    "g3_b48":   {"exit_mode": "legacy", "bos_fresh": 48, "gates": False,
                 "d1": False, "note": "G3 freshness BOS <= 48 bar M5"},
    "g1_gate":  {"exit_mode": "legacy", "bos_fresh": None, "gates": True,
                 "d1": False, "note": "G1: gate item-8 (spread+ATR band)"},
    "g4_d1":    {"exit_mode": "legacy", "bos_fresh": None, "gates": False,
                 "d1": True, "note": "G4: bias wajib D1+H4 searah"},
    "parity":   {"exit_mode": "g2", "bos_fresh": 36, "gates": True,
                 "d1": True, "note": "G1+G2+G3(36)+G4 bersamaan"},
}


def get(path: str) -> dict:
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    req = urllib.request.Request(BRIDGE + path,
                                 headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def iso_ts(s: str) -> int:
    return int(datetime.fromisoformat(s).timestamp())


def m15_to_h4(m15: list) -> list:
    """Agregasi M15 -> H4 per 4 jam UTC (sumber G4; label eksplisit)."""
    out, cur = [], None
    for b in m15:
        t = int(b["time"]) // 14400 * 14400
        if cur is None or cur["time"] != t:
            if cur is not None:
                out.append(cur)
            cur = {"time": t, "open": float(b["open"]), "high": float(b["high"]),
                   "low": float(b["low"]), "close": float(b["close"])}
            continue
        cur["high"] = max(cur["high"], float(b["high"]))
        cur["low"] = min(cur["low"], float(b["low"]))
        cur["close"] = float(b["close"])
    if cur is not None:
        out.append(cur)
    return out


def h4_to_d1(h4w: list) -> list:
    """Agregasi H4 -> D1 per hari UTC (rantai penuh utk G4)."""
    d1, cur = [], None
    for b in h4w:
        tt = int(b["time"]) // 86400 * 86400
        if cur is None or cur["time"] != tt:
            if cur is not None:
                d1.append(cur)
            cur = {"time": tt, "open": b["open"], "high": b["high"],
                   "low": b["low"], "close": b["close"]}
            continue
        cur["high"] = max(cur["high"], b["high"])
        cur["low"] = min(cur["low"], b["low"])
        cur["close"] = b["close"]
    if cur is not None:
        d1.append(cur)
    return d1


def d1_ok(bias: str, h4agg: list, t: int) -> str:
    """G4: struktur D1 (rantai penuh M15->H4->D1, hanya bar CLOSED <= t) searah
    bias. Return "ok" | "veto" | "data" (D1 < 25 bar = belum layak dinilai)."""
    h4w = [b for b in h4agg if int(b["time"]) + 14400 <= t]
    d1 = h4_to_d1(h4w)
    if len(d1) < 25:
        return "data"
    tr = smc.structure_trend(d1)
    if tr is None:
        return "veto"      # D1 ranging/campur -> no-trade (desain §1.1)
    return "ok" if ((bias == "BULL" and tr == "BULL") or
                    (bias == "BEAR" and tr == "BEAR")) else "veto"


def decide(base: dict, cfg: dict):
    """Keputusan per varian dari hasil evaluate legacy (rescoring G3).
    Return (take_v, bucket_block, score_v)."""
    r = base.get("reason", "")
    if not base.get("take"):
        if r.startswith("gate "):
            return False, "gate_item8", base.get("score", 0)
        if "bias H4" in r:
            return False, "bias_h4_netral", base.get("score", 0)
        if "SL struktural" in r:
            return False, "tanpa_sl_struktural", base.get("score", 0)
        if "target likuiditas" in r:
            return False, "tanpa_target_likuiditas", base.get("score", 0)
        if r.startswith("RR "):
            return False, "rr_gate", base.get("score", 0)
        if r.startswith("data TF"):
            return False, "data_kurang", base.get("score", 0)
    # jalur skor (take, atau skor < threshold) -> rescore G3 bila varian fresh
    score = base.get("score", 0)
    if cfg["bos_fresh"] is not None:
        base_bos = bool(base.get("components", {}).get("bos_ok"))
        age = base.get("bos_age_m5")
        age_ok = age is not None and age <= cfg["bos_fresh"]
        if age_ok and not base_bos:
            score += smc.WEIGHTS["bos"]
        elif base_bos and not age_ok:
            score -= smc.WEIGHTS["bos"]
    if score >= smc.SCORE_THRESHOLD:
        return True, "", score
    return False, "skor_threshold", score


def empty_stats() -> dict:
    return {"n": 0, "win": 0, "gross_pts": 0.0, "outcomes": Counter(),
            "by_dir": {}, "by_sess": {}, "by_score": {}, "trades": [],
            "blocked": Counter()}


def session_of(t: int) -> str:
    h = datetime.fromtimestamp(t, tz=timezone.utc).hour
    for name, a, b in SESSIONS:
        if a <= h < b:
            return name
    return "?"


def record(s: dict, base: dict, score_v: int, bar: dict, t: int,
           res: dict) -> None:
    entry_px = float(bar["close"])
    outcome = res["outcome"]
    gross = round(res["gross_pts"], 1)
    s["outcomes"][outcome] += 1
    s["n"] += 1
    s["win"] += 1 if gross > 0 else 0
    s["gross_pts"] = round(s["gross_pts"] + gross, 1)
    sess = session_of(t)
    for attr, k in (("by_dir", base["direction"]), ("by_sess", sess),
                    ("by_score", str(score_v))):
        b = s[attr].setdefault(k, [0, 0, 0.0])
        b[0] += 1
        b[1] += 1 if gross > 0 else 0
        b[2] = round(b[2] + gross, 1)
    s["trades"].append({
        "time": datetime.fromtimestamp(t, tz=timezone.utc).isoformat(),
        "dir": base["direction"], "sess": sess, "score": score_v,
        "rr": base.get("rr"), "sl_pts": base.get("sl_pts"),
        "tp_pts": base.get("tp1_pts"), "outcome": outcome,
        "gross_pts": gross,
        "net_base_pts": round(gross - BASE_COST_PTS, 1),
        "net_must_pts": round(gross - MUST_COST_PTS, 1)})


def main() -> int:
    print("fetch data ...", flush=True)
    m1_raw = get("/candles?symbol=XAUUSD&timeframe=M1&count=60000").get("candles", [])[:-1]
    m5_raw = get("/candles?symbol=XAUUSD&timeframe=M5&count=14000").get("candles", [])[:-1]
    m15_raw = get("/candles?symbol=XAUUSD&timeframe=M15&count=6500").get("candles", [])[:-1]
    h4_raw = get("/candles?symbol=XAUUSD&timeframe=H4&count=250").get("candles", [])[:-1]

    t_start, cutoff = iso_ts(T_START_UTC), iso_ts(CUTOFF_UTC)
    m1_all = [b for b in m1_raw if t_start <= int(b["time"]) < cutoff]
    # emulasi kedalaman fetch studi lama (bar CLOSED <= cutoff)
    m5_all = [b for b in m5_raw if int(b["time"]) + 300 <= cutoff][-FEED_M5:]
    m15_all = [b for b in m15_raw if int(b["time"]) + 900 <= cutoff][-FEED_M15:]
    h4_all = [b for b in h4_raw if int(b["time"]) + 14400 <= cutoff][-FEED_H4:]
    if SMOKE:
        skip = int(os.environ.get("SMC_SMOKE_START", "0"))
        m1_all = m1_all[skip:skip + M1W + 3000]

    m1_by_time = {b["time"]: b for b in m1_all}
    m1_times = sorted(m1_by_time)
    m5_by_time = {b["time"]: b for b in m5_all}
    m5_times = sorted(m5_by_time)
    m15_by_time = {b["time"]: b for b in m15_all}
    m15_times = sorted(m15_by_time)
    h4_by_time = {b["time"]: b for b in h4_all}
    h4_times = sorted(h4_by_time)
    h4agg = m15_to_h4(m15_all)     # rantai penuh utk G4
    t0, t1 = int(m1_all[0]["time"]), int(m1_all[-1]["time"])
    days = (t1 - t0) / 86400.0
    print(f"M1 {len(m1_all)} | M5 {len(m5_all)} | M15 {len(m15_all)} | "
          f"H4 {len(h4_all)} bar | jendela DIPIN {days:.1f} hari "
          f"({datetime.fromtimestamp(t0, tz=timezone.utc):%m-%d %H:%M} -> "
          f"{datetime.fromtimestamp(t1, tz=timezone.utc):%m-%d %H:%M} UTC)"
          + (" [SMOKE]" if SMOKE else ""), flush=True)
    if m1_all[0]["time"] > t_start:
        print(f"  PERINGATAN: M1 feed baru mulai "
              f"{datetime.fromtimestamp(int(m1_all[0]['time']), tz=timezone.utc):%m-%d %H:%M}"
              f" — tepi awal tidak tercover penuh", flush=True)

    st = {v: empty_stats() for v in VARIANTS}
    busy_until = {v: 0.0 for v in VARIANTS}
    last_entry = {v: 0.0 for v in VARIANTS}

    idx5 = idx15 = idx4 = -1
    n_eval = 0
    for i in range(M1W, len(m1_all)):
        bar = m1_all[i]
        t = int(bar["time"])
        while idx5 + 1 < len(m5_times) and m5_times[idx5 + 1] + 300 <= t:
            idx5 += 1
        while idx15 + 1 < len(m15_times) and m15_times[idx15 + 1] + 900 <= t:
            idx15 += 1
        while idx4 + 1 < len(h4_times) and h4_times[idx4 + 1] + 14400 <= t:
            idx4 += 1
        m1_hist = m1_all[i + 1 - M1W: i + 1]
        m5_hist = m5_all[max(0, idx5 + 1 - M5W): idx5 + 1] if idx5 >= 0 else []
        m15_hist = m15_all[max(0, idx15 + 1 - M15W): idx15 + 1] if idx15 >= 0 else []
        h4_hist = h4_all[: idx4 + 1][-H4W:] if idx4 >= 0 else []

        base = smc.evaluate(m1_hist, m5_hist, m15_hist, h4_hist,
                            spread_pts=SPREAD_PTS)
        n_eval += 1
        atr5 = CS.atr(m5_hist) if m5_hist else None
        gate_ok = (SPREAD_PTS <= smc.GATE_MAX_SPREAD_PTS and atr5 is not None
                   and smc.GATE_ATR_M5_MIN_PTS <= atr5 / POINT
                   <= smc.GATE_ATR_M5_MAX_PTS)

        for v, cfg in VARIANTS.items():
            s = st[v]
            if t < busy_until[v]:
                s["blocked"]["posisi_terbuka"] += 1
                continue
            if last_entry[v] and t - last_entry[v] < COOLDOWN_S:
                s["blocked"]["cooldown"] += 1
                continue
            if cfg["gates"] and not gate_ok:
                s["blocked"]["gate_item8"] += 1
                continue
            take_v, bucket, score_v = decide(base, cfg)
            if not take_v:
                s["blocked"][bucket] += 1
                continue
            if cfg["d1"]:
                dstat = d1_ok(base["bias"], h4agg, t)
                if dstat != "ok":
                    s["blocked"]["d1_veto" if dstat == "veto"
                               else "d1_data_kurang"] += 1
                    continue
            res = EX.simulate(base["direction"], float(bar["close"]),
                              base["sl"], base["tp1"], t, m1_by_time, m1_times,
                              mode=cfg["exit_mode"], atr_fn=CS.atr)
            if res["outcome"] in ("OPEN", "OPEN_TP1"):
                s["blocked"]["masih_open_di_akhir_data"] += 1
                continue
            record(s, base, score_v, bar, t, res)
            busy_until[v] = float(res["exit_time"]) + 60.0
            last_entry[v] = float(t)

    summary = {}
    for v, cfg in VARIANTS.items():
        s = st[v]
        n, w = s["n"], s["win"]
        gp = s["gross_pts"] / n if n else 0.0
        summary[v] = {
            "note": cfg["note"], "n": n,
            "signals_per_day": round(n / days, 2) if days else None,
            "win_rate_pct": round(w / n * 100, 1) if n else None,
            "gross_pts_per_trade": round(gp, 2),
            "net_base_pts": round(gp - BASE_COST_PTS, 2),
            "net_must_pts": round(gp - MUST_COST_PTS, 2),
            "outcomes": dict(s["outcomes"]),
            "by_dir": s["by_dir"], "by_sess": s["by_sess"],
            "by_score": s["by_score"],
            "blocked": dict(s["blocked"]),
            "trades": s["trades"] if not SMOKE else [],
        }
    out = {
        "meta": {"generated_at": datetime.now(tz=timezone.utc).isoformat(),
                 "smoke": SMOKE,
                 "window_utc": [
                     datetime.fromtimestamp(t0, tz=timezone.utc).isoformat(),
                     datetime.fromtimestamp(t1, tz=timezone.utc).isoformat()],
                 "window_pinned_to_old_artifact": [T_START_UTC, CUTOFF_UTC],
                 "n_evaluated_bars": n_eval,
                 "feed_emulation": {"m5": FEED_M5, "m15": FEED_M15,
                                    "h4": FEED_H4,
                                    "m1": "filtered ke jendela terpin"},
                 "cost": {"base": BASE_COST_PTS, "must": MUST_COST_PTS,
                          "label": "ESTIMATED_COST_MODEL"},
                 "g2_params": {"tp1_fraction": EX.G2_TP1_FRACTION,
                               "trail_k_atr": EX.G2_TRAIL_K_ATR,
                               "trail_mode": "max(structure, atr)",
                               "max_hold_s": EX.MAX_HOLD_S},
                 "catatan": ["news gate OFF (keputusan owner)",
                             "SL-priority ambigu (konservatif)",
                             "G2: TP2 = None, sisa posisi exit via trailing",
                             "posisi open di akhir jendela di-drop "
                             "(masih_open_di_akhir_data)"],
                 "variants": {v: c["note"] for v, c in VARIANTS.items()}},
        "summary": summary,
    }
    OUT_FILE.write_text(json.dumps(out, indent=1), encoding="utf-8")
    _print_report(summary, days, n_eval)
    return 0


def _print_report(summary: dict, days: float, n_eval: int) -> None:
    print(f"\n== REPLAY MULTI-VARIAN ({days:.1f} hari terpin, "
          f"{n_eval} evaluasi) ==")
    print(f"{'varian':12s} {'n':>4s} {'/hari':>5s} {'WR%':>6s} "
          f"{'gross':>8s} {'net_base':>9s} {'net_must':>9s}")
    for v, s in summary.items():
        print(f"{v:12s} {s['n']:4d} {s['signals_per_day'] or 0:5.2f} "
              f"{s['win_rate_pct'] or 0:6.1f} {s['gross_pts_per_trade']:8.2f} "
              f"{s['net_base_pts']:9.2f} {s['net_must_pts']:9.2f}")
    print("\noutcomes per varian:")
    for v, s in summary.items():
        oc = ", ".join(f"{k}={n}" for k, n in sorted(s["outcomes"].items()))
        print(f"  {v:12s} {oc or '-'}")
    print("\nblocked (top) per varian:")
    for v, s in summary.items():
        top = sorted(s["blocked"].items(), key=lambda kv: -kv[1])[:5]
        print(f"  {v:12s} " + ", ".join(f"{k}={n}" for k, n in top))
    # regresi silang vs artefak studi lama
    if OLD_FILE.exists():
        try:
            old = json.loads(OLD_FILE.read_text(encoding="utf-8"))["summary"]
            b = summary["baseline"]
            print(f"\nregresi silang baseline vs studi lama: "
                  f"n {b['n']} vs {old['n_signals_taken']} | "
                  f"gross/tr {b['gross_pts_per_trade']} vs "
                  f"{old['gross_pts_per_trade']} | outcomes "
                  f"{b['outcomes']} vs {old['outcomes']}")
        except Exception as e:  # noqa: BLE001
            print(f"(regresi silang dilewati: {e})")
    print(f"artefak: {OUT_FILE}")


if __name__ == "__main__":
    raise SystemExit(main())
