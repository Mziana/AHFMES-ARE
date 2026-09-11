# KONTROL STUDI MICRO v2 - SCALP M5 ASLI (decide() produksi) di jendela data sama.
# Tujuan: anchor validasi — apakah mesin SCALP M5 yang live menang (5 trade, 4W/1L)
# juga breakeven-gross di window 41 hari ini, ataukah positif (→ M1-downshift-lah
# yang merusak). Pakai SV.decide() produksi persis (bias M15, skor M5, volume wajib
# 1.2x, guard RSI M15+M5 70/30, SL/TP 1.25/2.0 x ATR M5). Exit: first-touch SL/TP
# grid M5 (konvensi eksekusi replay R1), satu posisi, tanpa cooldown (parity SCALP).
# Read-only terhadap bridge.
from __future__ import annotations

import bisect
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from strategy_v2 import simple_variants as SV  # noqa: E402

BRIDGE = "http://127.0.0.1:18888"
TOKEN_FILE = ROOT / "data" / "bridge_token.txt"
OUT_DIR = ROOT / "data" / "research" / "micro_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

POINT = 0.01
BASE_COST_PTS = 17.0
MUST_COST_PTS = 27.5
M5_WINDOW = 400
M15_WINDOW = 300


def get(path: str) -> dict:
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    req = urllib.request.Request(BRIDGE + path,
                                 headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def main() -> int:
    SV.NEWS_GATE_ENABLED = False  # parity live (owner OFF, kalender simulasi)
    print("fetch data ...", flush=True)
    m5_all = get("/candles?symbol=XAUUSD&timeframe=M5&count=8000").get("candles", [])[:-1]
    m15_all = get("/candles?symbol=XAUUSD&timeframe=M15&count=6000").get("candles", [])[:-1]
    m5_by_time = {b["time"]: b for b in m5_all}
    m5_times = sorted(m5_by_time)
    m15_times = sorted(b["time"] for b in m15_all)
    t0, t1 = m5_times[0], m5_times[-1]
    days = (t1 - t0) / 86400.0
    print(f"M5 {len(m5_all)} bar | M15 {len(m15_all)} bar | {days:.1f} hari "
          f"({datetime.fromtimestamp(t0, tz=timezone.utc):%m-%d %H:%M} -> "
          f"{datetime.fromtimestamp(t1, tz=timezone.utc):%m-%d %H:%M} UTC)", flush=True)

    entries = 0
    win = loss = 0
    gross_pts = 0.0
    trades = []
    blocked: dict = {}
    busy_until = 0.0
    idx15 = -1
    m15_hist: list = []

    for i in range(M5_WINDOW, len(m5_all)):
        bar = m5_all[i]
        t = bar["time"]
        while idx15 + 1 < len(m15_times) and m15_times[idx15 + 1] + 900 <= t:
            idx15 += 1
        if idx15 >= M15_WINDOW:
            m15_hist = m15_all[idx15 + 1 - M15_WINDOW: idx15 + 1]
        else:
            m15_hist = []
        if t < busy_until:
            blocked["posisi_terbuka"] = blocked.get("posisi_terbuka", 0) + 1
            continue
        if len(m15_hist) < 40:
            blocked["m15_kurang"] = blocked.get("m15_kurang", 0) + 1
            continue
        m5_hist = m5_all[i + 1 - M5_WINDOW: i + 1]
        dec = SV.decide("SCALP", m5_hist, m15_hist, [], 200.0,
                        news_events=None, now_epoch=t, kill=None,
                        m1_bars=None, last_entry_ts=None)
        if not dec.get("ok"):
            r = (dec.get("reason") or "?")[:40]
            key = ("volume" if "volume" in r else
                   "bias/struktur" if ("netral" in r or "struktur" in r) else
                   "rsi_guard" if "RSI" in r else "skor/pola")
            blocked[key] = blocked.get(key, 0) + 1
            continue
        entry_px = float(dec["entry"])
        direction = dec["direction"]
        sl, tp = float(dec["sl"]), float(dec["tp"])
        # exit first-touch grid M5 setelah bar sinyal (SL-priority)
        start = bisect.bisect_right(m5_times, t)
        outcome = "OPEN"
        exit_t = None
        for k in range(start, len(m5_times)):
            bt = m5_times[k]
            b = m5_by_time[bt]
            if direction == "BUY":
                hit_sl = b["low"] <= sl
                hit_tp = b["high"] >= tp
            else:
                hit_sl = b["high"] >= sl
                hit_tp = b["low"] <= tp
            if hit_sl:
                outcome, exit_t = "SL", bt + 300
                break
            if hit_tp:
                outcome, exit_t = "TP", bt + 300
                break
        if outcome == "OPEN":
            blocked["belum_tuntas_end_of_data"] = blocked.get("belum_tuntas_end_of_data", 0) + 1
            continue
        sl_dist, tp_dist = abs(entry_px - sl) / POINT, abs(tp - entry_px) / POINT
        pts = tp_dist if outcome == "TP" else -sl_dist
        entries += 1
        busy_until = exit_t
        gross_pts += pts
        if outcome == "TP":
            win += 1
        else:
            loss += 1
        trades.append({"time": datetime.fromtimestamp(t, tz=timezone.utc).isoformat(),
                       "dir": direction, "pattern": dec.get("pattern"),
                       "outcome": outcome, "gross_pts": round(pts, 1)})

    n = entries
    wr = (win / (win + loss) * 100.0) if (win + loss) else 0.0
    exp_base = (gross_pts - n * BASE_COST_PTS) / n if n else 0.0
    exp_must = (gross_pts - n * MUST_COST_PTS) / n if n else 0.0
    result = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "window_days": round(days, 2), "m5_bars": len(m5_all),
        "entries": n, "win": win, "loss": loss, "wr": round(wr, 1),
        "avg_gross_pts": round(gross_pts / n, 1) if n else 0.0,
        "exp_net_base_pts": round(exp_base, 2),
        "exp_net_must_pts": round(exp_must, 2),
        "usd_per_trade_at_002": round(exp_must * 0.02, 2),
        "sinyal_per_hari": round(n / days, 2) if days else 0.0,
        "blocked": blocked, "trades": trades}
    path = OUT_DIR / "control_scalp_m5.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"KONTROL SCALP M5 (jendela sama {days:.1f} hari): "
          f"n={n} W/L={win}/{loss} WR={wr:.1f}% "
          f"avgGross={result['avg_gross_pts']} expBase={exp_base:.2f} "
          f"expMust={exp_must:.2f} $/tr@0.02={exp_must*0.02:.2f}")
    print(f"blocked: {blocked}")
    print(f"hasil: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
