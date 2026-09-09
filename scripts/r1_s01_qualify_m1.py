"""R1 S0.1 tahap 2 — kualifikasi dataset M1 (standar A2) + identitas rantai data.

Kriteria (gaya A2, diperketat):
1. Fail-closed MAX 0: duplicate=0, NaN/OHLC invalid=0, gap intra-hari (<60s?
   tidak — gap sub-session) — untuk M1: grid 60s, gap <3600s = fail-closed,
   gap >=3600s = session_break (terklasifikasi).
2. OHLC valid & volume >= 0 semua bar.
3. Cek silang M1<->M5 (pasangan segar satu pull): untuk tiap 5-menit bucket,
   OHLC M5 harus identik dengan agregat OHLC M1; open/close wajib match,
   high/low wajib match. Ketidakcocokan = FATAL (mengindikasikan dua sumber
   sejarah berbeda).
4. Identitas rantai (dua metrik jujur):
   P3 — (a) hash arsip stored P3 harus reproduce hash terkunci 86014edf...;
        (b) SEMUA BAR TERTUTUP fresh == stored bar-per-bar (bar forming terakhir
            window dikecualikan — ia memang memfinalisasi setelah pull asli).
   A2 — hash OOS dihitung dari slice dengan batas bawah TERCATAT di artefak A2
        (history kini lebih dalam; tanpa batas itu rekonstruksi memuat bar ekstra).
   Gagal identitas = FATAL fail-closed.

Output: data/research/r1/m1_qualification.json (artefak ber-hash).
Gagal kriteria -> verdict TIDAK_LAYAK + exit 1.
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

R1 = ROOT / "data" / "research" / "r1"
BACK = ROOT / "data" / "research" / "backward"
P3 = ROOT / "data" / "research" / "p3"
TF_SEC_M1 = 60


def iso(ts: int) -> str:
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def pct(vals: list, p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    k = max(0, min(len(s) - 1, int(round(p / 100.0 * (len(s) - 1)))))
    return s[k]


def slice_hash(candles: list, first_ts: int, last_ts: int) -> str:
    """Hash slice [first_ts, last_ts] inclusive dari candle list fresh."""
    sl = [b for b in candles if first_ts <= int(b["time"]) <= last_ts]
    return registry.dataset_hash(sl), len(sl)


def check_m1(bars: list) -> dict:
    rep = {"timeframe": "M1", "bars": len(bars)}
    seen: set = set()
    dup = nan = ohlc_bad = vol_bad = 0
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
            vol_bad += 1
        else:
            vols.append(int(v))
    rep.update({
        "first_ts": int(bars[0]["time"]), "last_ts": int(bars[-1]["time"]),
        "first_utc": iso(bars[0]["time"]), "last_utc": iso(bars[-1]["time"]),
        "duplicate_ts": dup, "nan": nan, "ohlc_invalid": ohlc_bad,
        "volume_missing_negative": vol_bad,
        "tick_volume_p50_p95_p99": [pct(vols, 50), pct(vols, 95), pct(vols, 99)] if vols else None,
    })

    gaps, session_breaks, off_grid = [], [], []
    prev = None
    for b in bars:
        t = int(b["time"])
        if prev is not None:
            d = t - prev
            if d != TF_SEC_M1:
                if d % TF_SEC_M1 != 0:
                    off_grid.append({"from": prev, "to": t, "delta_s": d})
                if d >= 3600:
                    session_breaks.append({"from": prev, "to": t, "delta_s": d})
                else:
                    gaps.append({"from": prev, "to": t, "delta_s": d})
        prev = t
    rep["gaps_intra_day"] = gaps
    rep["gaps_intra_day_count"] = len(gaps)
    rep["session_breaks"] = {"count": len(session_breaks), "items": session_breaks}
    rep["off_grid_deltas"] = off_grid
    rep["trading_days"] = round((len(bars) - 1) * TF_SEC_M1 / 86400.0, 2)
    rep["fail_closed_total"] = dup + nan + ohlc_bad + vol_bad + len(gaps) + len(off_grid)
    return rep


def crosscheck_m1_m5(m1: list, m5: list, tolerance_note: str) -> dict:
    """Agregat M1 per 5 menit harus identik dengan OHLC M5 (open/close/high/low)."""
    buckets: dict = {}
    for b in m1:
        t = int(b["time"])
        k = (t // 300) * 300
        rec = buckets.setdefault(k, {"open": None, "high": None, "low": None, "close": None, "n": 0})
        if rec["open"] is None:
            rec["open"] = b["open"]
        rec["high"] = b["high"] if rec["high"] is None else max(rec["high"], b["high"])
        rec["low"] = b["low"] if rec["low"] is None else min(rec["low"], b["low"])
        rec["close"] = b["close"]
        rec["n"] += 1

    m5_idx = {int(b["time"]): b for b in m5}
    checked = mismatch_open = mismatch_high = mismatch_low = mismatch_close = 0
    incomplete = 0
    mism_sample = []
    for k, rec in buckets.items():
        if rec["n"] != 5:
            incomplete += 1
            continue
        ref = m5_idx.get(k)
        if ref is None:
            continue  # M5 window bisa lebih pendek/panjang tepi — bukan mismatch
        checked += 1
        bad = []
        if abs(rec["open"] - ref["open"]) > 1e-9:
            mismatch_open += 1; bad.append("open")
        if abs(rec["high"] - ref["high"]) > 1e-9:
            mismatch_high += 1; bad.append("high")
        if abs(rec["low"] - ref["low"]) > 1e-9:
            mismatch_low += 1; bad.append("low")
        if abs(rec["close"] - ref["close"]) > 1e-9:
            mismatch_close += 1; bad.append("close")
        if bad and len(mism_sample) < 5:
            mism_sample.append({"bucket_utc": iso(k), "fields": bad,
                                "m1": {f: rec[f] for f in ("open", "high", "low", "close")},
                                "m5": {f: ref[f] for f in ("open", "high", "low", "close")}})
    return {
        "note": tolerance_note,
        "buckets_5m_checked": checked,
        "buckets_incomplete_skipped": incomplete,
        "mismatch_open": mismatch_open, "mismatch_high": mismatch_high,
        "mismatch_low": mismatch_low, "mismatch_close": mismatch_close,
        "mismatch_total": mismatch_open + mismatch_high + mismatch_low + mismatch_close,
        "mismatch_samples": mism_sample,
    }


def main() -> int:
    m1 = json.loads((R1 / "dataset_m1.json").read_text(encoding="utf-8"))["candles"]
    m5_fresh = json.loads((R1 / "dataset_m5_fresh.json").read_text(encoding="utf-8"))["candles"]
    m15_fresh = json.loads((R1 / "dataset_m15_fresh.json").read_text(encoding="utf-8"))["candles"]
    acc = json.loads((R1 / "account_snapshot.json").read_text(encoding="utf-8")) if (R1 / "account_snapshot.json").exists() else None
    if acc is None:
        acc = json.loads((BACK / "account_snapshot.json").read_text(encoding="utf-8"))

    q: dict = {"m1": check_m1(m1)}

    # --- Cek silang M1<->M5 ---
    q["crosscheck_m1_vs_m5"] = crosscheck_m1_m5(m1, m5_fresh, "pasangan segar satu pull (identik sejarah)")

    # --- Identitas rantai data: slice fresh vs dataset terkunci ---
    p3q = json.loads((P3 / "qualification.json").read_text(encoding="utf-8"))
    a2q = json.loads((BACK / "oos_qualification.json").read_text(encoding="utf-8"))
    p3_m5, p3_m15 = p3q["m5"], p3q["m15"]

    p3_m5_stored = json.loads((P3 / "dataset_m5.json").read_text(encoding="utf-8"))["candles"]
    p3_m15_stored = json.loads((P3 / "dataset_m15.json").read_text(encoding="utf-8"))["candles"]

    def window(bars: list, first: int, last: int) -> list:
        return [b for b in bars if first <= int(b["time"]) <= last]

    def closed_bar_diff(stored: list, fresh: list) -> dict:
        sm = {int(b["time"]): b for b in stored}
        fm = {int(b["time"]): b for b in fresh}
        common = sorted(set(sm) & set(fm))
        diffs = []
        for t in common:
            if sm[t] != fm[t]:
                diffs.append({"ts": t, "utc": iso(t), "stored": sm[t], "fresh": fm[t]})
        return {
            "bars_common": len(common),
            "bars_diff": len(diffs),
            "diff_ts": [d["ts"] for d in diffs],
            "diff_samples": diffs[:3],
        }

    def only_forming_bar(diffs: list, last_ts: int) -> bool:
        """True bila satu-satunya perbedaan adalah bar terakhir window (forming saat pull asli)."""
        return bool(diffs) and all(int(d) == int(last_ts) for d in diffs)

    # P3: integritas arsip (stored reproduce hash terkunci) + kesetaraan bar tertutup fresh vs stored:
    p3_m5_win_stored = window(p3_m5_stored, int(p3_m5["first_ts"]), int(p3_m5["last_ts"]))
    p3_m15_win_stored = window(p3_m15_stored, int(p3_m15["first_ts"]), int(p3_m15["last_ts"]))
    p3_stored_reconstructed = registry.dataset_hash({"m5": p3_m5_win_stored, "m15": p3_m15_win_stored})

    p3_m5_cmp = closed_bar_diff(p3_m5_win_stored, window(m5_fresh, int(p3_m5["first_ts"]), int(p3_m5["last_ts"])))
    p3_m15_cmp = closed_bar_diff(p3_m15_win_stored, window(m15_fresh, int(p3_m15["first_ts"]), int(p3_m15["last_ts"])))

    m5_ok = p3_m5_cmp["bars_diff"] == 0 or only_forming_bar(p3_m5_cmp["diff_ts"], int(p3_m5["last_ts"]))
    m15_ok = p3_m15_cmp["bars_diff"] == 0 or only_forming_bar(p3_m15_cmp["diff_ts"], int(p3_m15["last_ts"]))
    archive_ok = p3_stored_reconstructed == p3q["dataset_hash"]
    p3_ok = m5_ok and m15_ok and archive_ok

    # A2: integritas arsip (stored reproduce hash terkunci) + kesetaraan konten
    # bar-per-bar pada SEMUA bar bersama fresh vs stored. Jendela "N bar terakhir"
    # broker bergeser seiring bar baru — fresh bisa kehilangan beberapa bar TER tua
    # di tepi kiri; itu CATATAN CAKUPAN, bukan korupsi (nol diff konten = identitas).
    # Run OOS R1 memakai dataset A2 TERSIMPAN (byte-identik dgn yang terkunci),
    # jadi komparabilitas dengan run champion lama terjaga penuh.
    TRAINING_FIRST_TS = 1785217800
    a2_m5_stored = [b for b in json.loads((BACK / "dataset_m5.json").read_text(encoding="utf-8"))["candles"]
                    if int(b["time"]) < TRAINING_FIRST_TS]
    a2_m15_stored = [b for b in json.loads((BACK / "dataset_m15.json").read_text(encoding="utf-8"))["candles"]
                     if int(b["time"]) < TRAINING_FIRST_TS]
    a2_archive_hash = registry.dataset_hash({"m5": a2_m5_stored, "m15": a2_m15_stored})
    archive_a2_ok = a2_archive_hash == a2q["disjoint_check"]["oos_dataset_hash"]

    a2_m5_cmp = closed_bar_diff(a2_m5_stored, [b for b in m5_fresh if int(b["time"]) < TRAINING_FIRST_TS])
    a2_m15_cmp = closed_bar_diff(a2_m15_stored, [b for b in m15_fresh if int(b["time"]) < TRAINING_FIRST_TS])
    a2_ok = archive_a2_ok and a2_m5_cmp["bars_diff"] == 0 and a2_m15_cmp["bars_diff"] == 0
    a2_coverage = {
        "m5": {"stored": len(a2_m5_stored), "fresh_common": a2_m5_cmp["bars_common"],
               "fresh_missing_oldest": len(a2_m5_stored) - a2_m5_cmp["bars_common"]},
        "m15": {"stored": len(a2_m15_stored), "fresh_common": a2_m15_cmp["bars_common"],
                "fresh_missing_oldest": len(a2_m15_stored) - a2_m15_cmp["bars_common"]},
    }

    q["identity_check"] = {
        "p3_training_slice": {
            "p3_locked_hash": p3q["dataset_hash"],
            "stored_reconstructed_hash": p3_stored_reconstructed,
            "archive_integrity_ok": archive_ok,
            "closed_bar_comparison_m5": p3_m5_cmp,
            "closed_bar_comparison_m15": p3_m15_cmp,
            "closed_bars_match": m5_ok and m15_ok,
            "match": p3_ok,
            "method": "archive hash reproduction + closed-bar equality (bar forming terakhir dikecualikan)",
        },
        "a2_oos_slice": {
            "a2_locked_hash": a2q["disjoint_check"]["oos_dataset_hash"],
            "stored_archive_hash": a2_archive_hash,
            "archive_integrity_ok": archive_a2_ok,
            "closed_bar_comparison_m5": a2_m5_cmp,
            "closed_bar_comparison_m15": a2_m15_cmp,
            "coverage": a2_coverage,
            "match": a2_ok,
            "method": "archive hash reproduction + zero content-diff pada semua bar bersama; bar ter-ua hilang dari fresh = catatan cakupan (run OOS memakai dataset A2 tersimpan)",
        },
    }

    # --- Spread & symbol spec (snapshot) ---
    xau = (acc.get("ticks") or {}).get("XAUUSD") or {}
    raw_spread = xau.get("spread")
    q["spread"] = {
        "source": "live_snapshot (/account)", "raw": raw_spread, "unit": "PRICE_1E4",
        "points": bm.normalize_spread(raw_spread, bm.PRICE_1E4) if raw_spread is not None else None,
        "note": "model biaya R1 tetap cost model terkunci (17 poin, $1/poin/lot)",
    }
    meta = bm.load_broker_meta(acc)
    q["symbol_spec"] = {
        "from_snapshot": (acc.get("symbol_info") or {}).get("XAUUSD"),
        "broker_meta_hash": bm.broker_meta_hash(meta),
        "point_value_usd_per_lot": bm.point_value_usd_per_lot(meta),
    }

    # --- Keputusan kelayakan ---
    fails = []
    r = q["m1"]
    # Deviasi terdokumentasi: gap M1 broker feed. Standar kontrak R1 = fail-closed 0.
    # Realitas feed M1: N gap masing-masing 120s (satu bar hilang). Kasus DIENUMERASI
    # penuh di bawah dan dilaporkan sebagai KNOWN_DEVIATION ke owner — bukan diam-diam
    # dilonggarkan. Engine memakai aturan "first AVAILABLE M1 open >= T" sehingga bar
    # hilang tidak merusak semantik eksekusi; risiko hanya jika hole tepat di menit
    # entry (probabilitas ~5 bar / 150.000).
    if r["fail_closed_total"] != 0:
        known_dev = (r["gaps_intra_day_count"] > 0
                     and all(g["delta_s"] == 120 for g in r["gaps_intra_day"])
                     and r["duplicate_ts"] == 0 and r["nan"] == 0
                     and r["ohlc_invalid"] == 0 and r["volume_missing_negative"] == 0
                     and len(r["off_grid_deltas"]) == 0)
        if not known_dev:
            fails.append(f"M1 fail-closed total={r['fail_closed_total']} (wajib 0, di luar deviasi terdokumentasi)")
        q["known_deviation"] = {
            "type": "m1_single_bar_gaps",
            "count": r["gaps_intra_day_count"],
            "items": r["gaps_intra_day"],
            "status": "DILAPORKAN ke owner — setujui atau tolak sebelum Stage 1",
            "engine_handling": "entry = first AVAILABLE M1 open >= T (aturan kontrak, toleran bar hilang)",
        }
    cc = q["crosscheck_m1_vs_m5"]
    if cc["mismatch_total"] != 0:
        fails.append(f"crosscheck M1<->M5 mismatch={cc['mismatch_total']}")
    ic = q["identity_check"]
    if not ic["p3_training_slice"]["match"]:
        fails.append("identitas training: bar tertutup fresh != stored P3 ATAU arsip P3 tidak reproduce hash terkunci")
    if not ic["a2_oos_slice"]["match"]:
        fails.append("identitas OOS: arsip A2 tidak reproduce hash terkunci ATAU ada diff konten bar bersama")

    q["verdict"] = ("LAYAK" if not fails else "TIDAK_LAYAK")
    if q["verdict"] == "LAYAK" and q.get("known_deviation"):
        q["verdict"] = "LAYAK_DENGAN_DEVIASI_TERDOKUMENTASI (menunggu konfirmasi owner sebelum Stage 1)"
    q["verdict_failures"] = fails
    q["generated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    q["m1_dataset_hash"] = registry.dataset_hash(m1)

    qh = registry.dataset_hash(json.dumps(q, sort_keys=True, default=str))
    q["qualification_hash"] = qh

    (R1 / "m1_qualification.json").write_text(json.dumps(q, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"M1: {r['bars']} bar  {r['first_utc']} .. {r['last_utc']}  ({r['trading_days']} hari trading)")
    print(f"  fail-closed: dup={r['duplicate_ts']} nan={r['nan']} ohlc={r['ohlc_invalid']} vol={r['volume_missing_negative']} gaps={r['gaps_intra_day_count']} offgrid={len(r['off_grid_deltas'])}")
    print(f"  session_break: {r['session_breaks']['count']}")
    print(f"crosscheck M1<->M5: buckets={cc['buckets_5m_checked']} mismatch={cc['mismatch_total']}")
    print(f"identitas: P3 training slice match={ic['p3_training_slice']['match']} | A2 OOS slice match={ic['a2_oos_slice']['match']}")
    print(f"VERDICT: {q['verdict']}" + (f" — {fails}" if fails else ""))
    print(f"qualification_hash: {qh[:16]}")
    return 0 if q["verdict"] == "LAYAK" else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
