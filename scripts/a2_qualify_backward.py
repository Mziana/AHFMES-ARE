"""A2 tahap 2 — qualification dataset BACKWARD OOS (standar diketatkan).

Perbedaan vs P3 (kesepakatan kontrak final):
1. Gap intra-hari (< 3600s): MAX 0 bar (P3 boleh <=0.1%) — fail-closed.
2. Session break >= 3600s: diklasifikasi & direkam (bukan korupsi).
3. Disjoint DUA LAPIS vs dataset training P3 (86014edf...):
   (a) dataset_hash OOS != hash training;
   (b) tidak ada bar bersama: bar OOS terakhir < first_ts training
       (union dengan C1-C4 tercakup — semuanya di dalam window training).
4. Window OOS: maksimum bar backward yang bersih, dipotong di hari terakhir
   SEBELUM 2026-07-29 00:00 UTC (first bar training).

Output: data/research/backward/oos_qualification.json (artefak ber-hash).
Gagal kriteria -> verdict TIDAK_LAYAK + exit 1 (fail-closed).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from strategy_v2 import broker_meta as bm
from strategy_v2 import registry

BACK = ROOT / "data" / "research" / "backward"
P3_QUAL = ROOT / "data" / "research" / "p3" / "qualification.json"
TF_SEC = {"m5": 300, "m15": 900}
TRAINING_FIRST_TS = 1785217800  # first bar M5 training P3 (2026-07-29)

OOS_TARGET_END_TS = (TRAINING_FIRST_TS // 300) * 300  # bar M5 terakhir OOS


def iso(ts: int) -> str:
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def pct(vals: list, p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    k = max(0, min(len(s) - 1, int(round(p / 100.0 * (len(s) - 1)))))
    return s[k]


def check_tf(bars: list, tf: str) -> dict:
    step = TF_SEC[tf]
    rep = {"timeframe": tf.upper(), "bars_raw": len(bars)}
    if not bars:
        rep["FATAL"] = "empty dataset"
        return rep

    # Potong window OOS: hanya bar dengan time < TRAINING_FIRST_TS
    oos_bars = [b for b in bars if int(b["time"]) < TRAINING_FIRST_TS]
    rep["bars_oos"] = len(oos_bars)
    if not oos_bars:
        rep["FATAL"] = "tidak ada bar di luar window training"
        return rep

    rep["first_ts"] = int(oos_bars[0]["time"])
    rep["last_ts"] = int(oos_bars[-1]["time"])
    rep["first_utc"] = iso(rep["first_ts"])
    rep["last_utc"] = iso(rep["last_ts"])

    seen: set = set()
    dup = nan = ohlc_bad = vol_missing = 0
    vols: list = []
    for b in oos_bars:
        t = b.get("time")
        if t in seen:
            dup += 1
        seen.add(t)
        o, h, l, c = b.get("open"), b.get("high"), b.get("low"), b.get("close")
        if any(x is None or x != x for x in (o, h, l, c)):
            nan += 1
        elif h < max(o, c) or l > min(o, c) or min(o, h, l, c) <= 0:
            ohlc_bad += 1
        v = b.get("volume")
        if v is None or v != v or v < 0:
            vol_missing += 1
        else:
            vols.append(int(v))
    rep["duplicate_ts"] = dup
    rep["nan"] = nan
    rep["ohlc_invalid"] = ohlc_bad
    rep["volume_missing_negative"] = vol_missing
    rep["tick_volume_p50_p95_p99"] = [pct(vols, 50), pct(vols, 95), pct(vols, 99)] if vols else None

    gaps_intra, session_breaks, off_grid = [], [], []
    prev = None
    for b in oos_bars:
        t = int(b["time"])
        if prev is not None:
            d = t - prev
            if d != step:
                if d % step != 0:
                    off_grid.append({"from": prev, "to": t, "delta_s": d})
                if d >= 3600:
                    session_breaks.append({"from": prev, "to": t, "delta_s": d})
                else:
                    gaps_intra.append({"from": prev, "to": t, "delta_s": d})
        prev = t
    rep["gaps_intra_day"] = gaps_intra
    rep["gaps_intra_day_count"] = len(gaps_intra)
    rep["session_breaks"] = {"count": len(session_breaks), "items": session_breaks}
    rep["off_grid_deltas"] = off_grid
    rep["trading_days"] = round((len(oos_bars) - 1) * step / 86400.0, 2)
    rep["fail_closed_total"] = dup + nan + ohlc_bad + len(gaps_intra) + len(off_grid)
    return rep


def main() -> int:
    m5_all = json.loads((BACK / "dataset_m5.json").read_text(encoding="utf-8"))["candles"]
    m15_all = json.loads((BACK / "dataset_m15.json").read_text(encoding="utf-8"))["candles"]
    acc = json.loads((BACK / "account_snapshot.json").read_text(encoding="utf-8"))
    p3 = json.loads(P3_QUAL.read_text(encoding="utf-8"))

    q = {"m5": check_tf(m5_all, "m5"), "m15": check_tf(m15_all, "m15")}

    xau = (acc.get("ticks") or {}).get("XAUUSD") or {}
    raw_spread = xau.get("spread")
    spread_pts = bm.normalize_spread(raw_spread, bm.PRICE_1E4) if raw_spread is not None else None
    q["spread"] = {
        "source": "live_snapshot (/account)", "raw": raw_spread, "unit": "PRICE_1E4",
        "points": spread_pts,
        "note": "snapshot live untuk symbol spec; model biaya OOS tetap cost model terkunci (17 poin, $1/poin/lot)",
    }
    meta = bm.load_broker_meta(acc)
    q["symbol_spec"] = {
        "from_snapshot": (acc.get("symbol_info") or {}).get("XAUUSD"),
        "broker_meta": meta,
        "broker_meta_hash": bm.broker_meta_hash(meta),
        "point_value_usd_per_lot": bm.point_value_usd_per_lot(meta),
        "stops_level": xau.get("stops_level"),
    }

    # --- Disjoint check DUA LAPIS ---
    training_hash = p3["dataset_hash"]
    m5_oos = [b for b in m5_all if int(b["time"]) < TRAINING_FIRST_TS]
    m15_oos = [b for b in m15_all if int(b["time"]) < TRAINING_FIRST_TS]
    oos_hash = registry.dataset_hash({"m5": m5_oos, "m15": m15_oos})
    last_oos_ts = int(m5_oos[-1]["time"])
    no_shared_bars = last_oos_ts < int(p3["m5"]["first_ts"])
    q["disjoint_check"] = {
        "layer_a_hash_different": oos_hash != training_hash,
        "layer_b_no_shared_bars": {
            "ok": no_shared_bars,
            "oos_last_ts": last_oos_ts,
            "oos_last_utc": iso(last_oos_ts),
            "training_first_ts": int(p3["m5"]["first_ts"]),
            "training_first_utc": p3["m5"]["first_utc"],
        },
        "training_dataset_hash": training_hash,
        "oos_dataset_hash": oos_hash,
        "verdict": "DISJOINT" if (oos_hash != training_hash and no_shared_bars) else "OVERLAP",
    }

    # --- Verdict kriteria ketat ---
    fails = []
    for tf, r in q.items():
        if not isinstance(r, dict) or "fail_closed_total" not in r:
            continue
        if r["fail_closed_total"] != 0:
            fails.append(f"{tf}: fail-closed total={r['fail_closed_total']} "
                         f"(dup={r['duplicate_ts']} nan={r['nan']} ohlc={r['ohlc_invalid']} "
                         f"gap_intra={r['gaps_intra_day_count']} off_grid={len(r['off_grid_deltas'])})")
        if r["trading_days"] < 14:
            fails.append(f"{tf}: hanya {r['trading_days']} hari trading < 14 minimum")
    q["verdict"] = "LAYAK" if not fails and q["disjoint_check"]["verdict"] == "DISJOINT" else "TIDAK_LAYAK"
    q["verdict_failures"] = fails

    out = BACK / "oos_qualification.json"
    out.write_text(json.dumps(q, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")

    print(f"OOS dataset_hash: {oos_hash[:16]}... | training: {training_hash[:16]}...")
    print(f"disjoint: {q['disjoint_check']['verdict']} "
          f"(hash_diff={q['disjoint_check']['layer_a_hash_different']}, "
          f"no_shared={no_shared_bars}: OOS last {iso(last_oos_ts)} < training first {p3['m5']['first_utc']})")
    for tf in ("m5", "m15"):
        r = q[tf]
        print(f"\n[{tf.upper()}] bars_oos={r.get('bars_oos')} window={r.get('first_utc')} .. {r.get('last_utc')} ({r.get('trading_days')} hari trading)")
        print(f"  fail-closed: dup={r.get('duplicate_ts')} nan={r.get('nan')} ohlc={r.get('ohlc_invalid')} "
              f"gap_intra={r.get('gaps_intra_day_count')} off_grid={len(r.get('off_grid_deltas', []))}")
        print(f"  session_break: {r['session_breaks']['count']} | tick_volume p50/p95/p99: {r.get('tick_volume_p50_p95_p99')}")
        for g in r.get("gaps_intra_day", [])[:5]:
            print(f"    GAP FAIL: {iso(g['from'])} -> {iso(g['to'])} ({g['delta_s']}s)")
    print(f"\nspread live snapshot: {spread_pts} poin (raw {raw_spread})")
    print(f"\nVERDICT: {q['verdict']}")
    for f in fails:
        print(f"  FAIL: {f}")
    return 0 if q["verdict"] == "LAYAK" else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
