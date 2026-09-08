"""P3 — Data qualification penuh (mandat docs/MANDAT_P3_P6_INTEGRATION.md §P3).

Input:  data/research/p3/dataset_m5.json, dataset_m15.json, account_snapshot.json
Output: data/research/p3/qualification.json (artefak ber-hash) + ringkasan stdout.

Fail-closed (harus 0): duplicate_ts, NaN, OHLC invalid.
Dilaporkan per-angka: gap intra-hari (<=0.1% bar), session_break, kontinuitas
grid timezone (semua delta kelipatan interval), distribusi tick_volume,
spread live snapshot (PRICE_1E4 -> poin), symbol spec + broker_meta_hash,
dataset_hash (DIKUNCI untuk P4-P6).
"""
from __future__ import annotations

import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from strategy_v2 import broker_meta as bm
from strategy_v2 import registry

P3 = ROOT / "data" / "research" / "p3"
TF_SEC = {"m5": 300, "m15": 900}


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
    rep = {"timeframe": tf.upper(), "bars": len(bars)}
    if not bars:
        rep["FATAL"] = "empty dataset"
        return rep

    rep["first_ts"] = int(bars[0]["time"])
    rep["last_ts"] = int(bars[-1]["time"])
    rep["first_utc"] = iso(rep["first_ts"])
    rep["last_utc"] = iso(rep["last_ts"])

    seen: set = set()
    dup = 0
    nan = 0
    ohlc_bad = 0
    vol_missing = 0
    vols: list = []
    for b in bars:
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

    # Gap + kontinuitas grid (timezone: epoch kontinu, delta kelipatan interval)
    gaps_intra = []       # < 3600s — kehilangan data intra-sesi
    session_breaks = []   # >= 3600s — break sesi (maintenance/weekend)
    off_grid = []         # delta bukan kelipatan step — kontinuitas timezone rusak
    prev = None
    for b in bars:
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
    rep["gaps_intra_day_ratio"] = round(len(gaps_intra) / len(bars), 6)
    rep["session_breaks"] = {"count": len(session_breaks), "items": session_breaks}
    rep["off_grid_deltas"] = off_grid

    # Estimasi waktu trading: (n-1) bar x step
    rep["trading_days"] = round((len(bars) - 1) * step / 86400.0, 2)

    rep["fail_closed_total"] = dup + nan + ohlc_bad
    return rep


def main() -> int:
    m5 = json.loads((P3 / "dataset_m5.json").read_text(encoding="utf-8"))["candles"]
    m15 = json.loads((P3 / "dataset_m15.json").read_text(encoding="utf-8"))["candles"]
    acc = json.loads((P3 / "account_snapshot.json").read_text(encoding="utf-8"))

    q = {"m5": check_tf(m5, "m5"), "m15": check_tf(m15, "m15")}

    # Spread live snapshot + unit normalisasi (E-2)
    xau = (acc.get("ticks") or {}).get("XAUUSD") or {}
    raw_spread = xau.get("spread")
    spread_pts = bm.normalize_spread(raw_spread, bm.PRICE_1E4) if raw_spread is not None else None
    q["spread"] = {
        "source": "live_snapshot (/account)", "raw": raw_spread, "unit": "PRICE_1E4",
        "points": spread_pts,
        "note": "per-bar historis tidak tersedia dari candle bridge — model biaya P4 memakai snapshot ini (ESTIMATED_COST_MODEL)",
    }

    # Symbol spec + broker meta (conflict guard tick_value)
    meta = bm.load_broker_meta(acc)
    q["symbol_spec"] = {
        "from_snapshot": (acc.get("symbol_info") or {}).get("XAUUSD"),
        "broker_meta": meta,
        "broker_meta_hash": bm.broker_meta_hash(meta),
        "point_value_usd_per_lot": bm.point_value_usd_per_lot(meta),
        "stops_level": xau.get("stops_level"),
        "order_calc_profit_calibration": "2026-09-08: $1/point/lot (tick_value broker 10.0 TIDAK dipakai — konflik tercatat)",
    }

    # dataset_hash DIKUNCI untuk P4-P6
    dhash = registry.dataset_hash({"m5": m5, "m15": m15})
    q["dataset_hash"] = dhash
    q["locked_for"] = ["P4", "P5", "P6"]

    # Keputusan kelayakan (kriteria mandat §P3)
    fails = []
    for tf, r in q.items():
        if not isinstance(r, dict) or "fail_closed_total" not in r:
            continue
        if r["fail_closed_total"] != 0:
            fails.append(f"{tf}: fail-closed={r['fail_closed_total']}")
        if r["gaps_intra_day_ratio"] > 0.001:
            fails.append(f"{tf}: gap intra-hari {r['gaps_intra_day_ratio']*100:.3f}% > 0.1%")
        if r["off_grid_deltas"]:
            fails.append(f"{tf}: {len(r['off_grid_deltas'])} delta off-grid (timezone kontinuitas rusak)")
        if r["trading_days"] < 14:
            fails.append(f"{tf}: hanya {r['trading_days']} hari trading < 14 minimum")
    q["verdict"] = "LAYAK" if not fails else "TIDAK_LAYAK"
    q["verdict_failures"] = fails

    out = P3 / "qualification.json"
    out.write_text(json.dumps(q, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")

    print(f"dataset_hash (LOCKED): {dhash}")
    for tf in ("m5", "m15"):
        r = q[tf]
        print(f"\n[{tf.upper()}] bars={r['bars']} window={r['first_utc']} .. {r['last_utc']} ({r['trading_days']} hari trading)")
        print(f"  fail-closed: dup={r['duplicate_ts']} nan={r['nan']} ohlc={r['ohlc_invalid']} vol={r['volume_missing_negative']}")
        print(f"  gap intra-hari: {len(r['gaps_intra_day'])} ({r['gaps_intra_day_ratio']*100:.4f}%) | session_break: {r['session_breaks']['count']} | off-grid: {len(r['off_grid_deltas'])}")
        print(f"  tick_volume p50/p95/p99: {r['tick_volume_p50_p95_p99']}")
        for g in r["gaps_intra_day"][:5]:
            print(f"    gap: {iso(g['from'])} -> {iso(g['to'])} ({g['delta_s']}s)")
    print(f"\nspread live: raw={raw_spread} PRICE_1E4 -> {spread_pts} poin")
    print(f"broker meta: source={meta['source']} pv={bm.point_value_usd_per_lot(meta)} tick_value_source={meta.get('tick_value_source')}")
    print(f"\nVERDICT: {q['verdict']}")
    for f in fails:
        print(f"  FAIL: {f}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
