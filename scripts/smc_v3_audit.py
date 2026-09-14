# AUDIT SMC/ICT v3 vs desain owner (rencana-trading-scalping-xauusd.md §0-§8)
# Bukti utk owner: (1) pass-rate tiap item checklist dari SAMPLING bar M1,
# (2) asersi sisi SL di SETIAP sinyal take, (3) TRACE KASUS: checklist lengkap
# 3 trade nyata dari replay (TP / SL / skor tinggi) — manusia-baca.
# Murni read-only via bridge; sampling tiap-6 bar (estimasi ~2.5 menit).
from __future__ import annotations

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

M1_WINDOW = 400
M5_WINDOW = 400
M15_WINDOW = 300
H4_WINDOW = 250
SPREAD_PTS = 17.0
SAMPLE_EVERY = 6          # sampling audit (bukan replay penuh)
CASE_KEYS = ("TP", "SL")  # kasus yang di-trace dari replay artifact


def get(path: str) -> dict:
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    req = urllib.request.Request(BRIDGE + path,
                                 headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def windows_at(i: int, m1_all, m5_all, m15_all, h4_all):
    """Slice window persis konvensi replay (bar tertutup saja)."""
    t = int(m1_all[i]["time"])
    m1h = m1_all[i + 1 - M1_WINDOW: i + 1]
    m5h = [b for b in m5_all if int(b["time"]) + 300 <= t][-M5_WINDOW:]
    m15h = [b for b in m15_all if int(b["time"]) + 900 <= t][-M15_WINDOW:]
    h4h = [b for b in h4_all if int(b["time"]) + 14400 <= t][-H4_WINDOW:]
    return m1h, m5h, m15h, h4h


def main() -> int:
    print("fetch data ...", flush=True)
    m1_all = get("/candles?symbol=XAUUSD&timeframe=M1&count=40000").get("candles", [])[:-1]
    m5_all = get("/candles?symbol=XAUUSD&timeframe=M5&count=8000").get("candles", [])[:-1]
    m15_all = get("/candles?symbol=XAUUSD&timeframe=M15&count=3000").get("candles", [])[:-1]
    h4_all = get("/candles?symbol=XAUUSD&timeframe=H4&count=250").get("candles", [])[:-1]
    t0 = m1_all[M1_WINDOW]["time"]
    t1 = m1_all[-1]["time"]
    days = (t1 - t0) / 86400.0
    print(f"jendela {days:.1f} hari | sampling tiap {SAMPLE_EVERY} bar", flush=True)

    acc = {"n_eval": 0, "take": 0,
           "gate": Counter(), "items": Counter(),
           "score_hist": Counter(),
           "taken_combo": Counter(),          # item yang ADA saat take
           "taken_missing": Counter(),        # item bobot-2 yang HILANG saat take
           "sl_side_violation": [],           # asersi sisi SL
           "sl_side_checked": 0,
           "rr_values": [],
           "ema_veto_fired": 0,
           "wrong_side_anchor_rejected": 0}
    samples = []
    keys_items = ("Bias H4 (HH/HL-LH/LL)", "Premium/Discount (range H4)",
                  "POI fresh (OB/FVG M15/M5)", "BOS searah (M15/M5)",
                  "Liquidity sweep (SFP)", "CHoCH mikro M1 (30 bar terakhir)",
                  "Pola candle M1")

    for i in range(M1_WINDOW, len(m1_all), SAMPLE_EVERY):
        m1h, m5h, m15h, h4h = windows_at(i, m1_all, m5_all, m15_all, h4_all)
        r = smc.evaluate(m1h, m5h, m15h, h4h, spread_pts=SPREAD_PTS)
        acc["n_eval"] += 1
        acc["score_hist"][int(r["score"])] += 1
        for c in r["checklist"]:
            if c["k"] in keys_items:
                acc["items"][c["k"]] += 1 if c["ok"] else 0
            if c["k"] == "Filter EMA50/200 H4" and c["ok"] is False:
                acc["ema_veto_fired"] += 1
        reason = r.get("reason") or ""
        if "bias H4" in reason:
            acc["gate"]["bias_netral"] += 1
            continue
        if "SL struktural" in reason:
            acc["gate"]["tanpa_sl_struktural"] += 1
            continue
        if "target likuiditas" in reason:
            acc["gate"]["tanpa_target"] += 1
            continue
        if reason.startswith("RR "):
            acc["gate"]["rr_gate"] += 1
            continue
        if reason.startswith("skor") and "<" in reason:
            acc["gate"]["skor_threshold"] += 1
            continue
        # ── take: asersi sisi SL ──
        price = float(m1h[-1]["close"])
        acc["sl_side_checked"] += 1
        bad = (r["direction"] == "BUY" and r["sl"] >= price) or \
              (r["direction"] == "SELL" and r["sl"] <= price)
        if bad:
            acc["sl_side_violation"].append(
                {"t": datetime.fromtimestamp(int(m1h[-1]["time"]), tz=timezone.utc).isoformat(),
                 "dir": r["direction"], "sl": r["sl"], "price": price})
        acc["take"] += 1
        acc["rr_values"].append(r["rr"])
        ok_items = [c["k"] for c in r["checklist"] if c.get("ok") and c["k"] in keys_items]
        acc["taken_combo"][tuple(sorted(ok_items))] += 1
        for k, w in (("Liquidity sweep (SFP)", "sweep"),
                     ("CHoCH mikro M1 (30 bar terakhir)", "choch_mikro"),
                     ("Pola candle M1", "pola")):
            if k not in ok_items:
                acc["taken_missing"][w] += 1
        if len(samples) < 400:
            samples.append({"t": datetime.fromtimestamp(int(m1h[-1]["time"]),
                                                        tz=timezone.utc).isoformat(),
                            "score": r["score"], "dir": r["direction"],
                            "sl_pts": r["sl_pts"], "tp1_pts": r["tp1_pts"],
                            "rr": r["rr"]})

    # ── trace kasus dari replay artifact ──
    artifact = OUT_DIR / "smc_v3_replay.json"
    cases = []
    if artifact.exists():
        rep = json.loads(artifact.read_text(encoding="utf-8"))
        trades = rep["trades"]
        pick = {}
        for key in CASE_KEYS:
            cand = next((t for t in trades if t["outcome"] == key), None)
            if cand:
                pick[key] = cand
        hi = max(trades, key=lambda t: t["score"]) if trades else None
        if hi:
            pick["SKOR_MAKS"] = hi
        m1_times = [int(b["time"]) for b in m1_all]
        for label, tr in pick.items():
            tt = int(datetime.fromisoformat(tr["time"]).timestamp())
            i = m1_times.index(tt) if tt in m1_times else None
            if i is None:
                continue
            m1h, m5h, m15h, h4h = windows_at(i, m1_all, m5_all, m15_all, h4_all)
            r = smc.evaluate(m1h, m5h, m15h, h4h, spread_pts=SPREAD_PTS)
            cases.append({"case": label, "trade": tr,
                          "re_eval": {k: r[k] for k in
                                      ("take", "reason", "direction", "score",
                                       "sl", "tp1", "rr", "sl_pts", "tp1_pts",
                                       "bias", "pd")},
                          "checklist": r["checklist"]})

    n_eval = acc["n_eval"]
    out = {
        "meta": {"sampled_every": SAMPLE_EVERY, "n_eval": n_eval,
                 "window_days": round(days, 1),
                 "generated_at": datetime.now(tz=timezone.utc).isoformat()},
        "funnel_pct": {k: round(v / n_eval * 100, 1)
                       for k, v in acc["gate"].items()},
        "item_pass_rate_pct": {k: round(acc["items"][k] / n_eval * 100, 1)
                               for k in keys_items},
        "ema_veto_fired": acc["ema_veto_fired"],
        "score_hist": {str(k): v for k, v in sorted(acc["score_hist"].items())},
        "take_rate_pct": round(acc["take"] / n_eval * 100, 2),
        "taken_n_sampled": acc["take"],
        "taken_missing_bobot2": dict(acc["taken_missing"]),
        "taken_combo_top": {", ".join(k): v for k, v in
                            acc["taken_combo"].most_common(8)},
        "sl_side_checked": acc["sl_side_checked"],
        "sl_side_violation": acc["sl_side_violation"],
        "rr_mean_sampled": (round(sum(acc["rr_values"]) / len(acc["rr_values"]), 2)
                            if acc["rr_values"] else None),
        "cases": cases,
        "samples": samples,
    }
    (OUT_DIR / "smc_v3_audit.json").write_text(json.dumps(out, indent=1),
                                               encoding="utf-8")

    print(f"\n== AUDIT SMC v3 ({n_eval} sampel, tiap-{SAMPLE_EVERY} bar) ==")
    print("funnel :", out["funnel_pct"])
    print("pass-rate item:")
    for k, v in out["item_pass_rate_pct"].items():
        print(f"  {k:38s} {v:5.1f}%")
    print(f"EMA50/200 veto fired : {acc['ema_veto_fired']}x")
    print(f"take : {out['take_rate_pct']}% "
          f"({acc['take']} sinyal dari {n_eval} sampel)")
    print(f"take TANPA item bobot-2 : {out['taken_missing_bobot2']}")
    print(f"SL sisi: dicek {acc['sl_side_checked']} | pelanggaran "
          f"{len(acc['sl_side_violation'])}")
    print(f"kasus di-trace : {[c['case'] for c in cases]}")
    print("artefak : data/research/smc_v3/smc_v3_audit.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
