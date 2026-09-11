"""MICRO STUDY — observer & replay untuk desain ulang gate MICRO (owner request).

MODE observe : loop --duration detik, tiap close M1 catat pipeline penuh ke
               data/research/r1/demo/observer.jsonl (read-only, tidak order).
MODE replay  : walk-forward di data M1/M5/M15 bridge (tanpa lookahead: tiap
               bar hanya melihat data s.d. bar itu), hitung varian gate &
               outcome entri hipotetis SL/TP pts yang ditentukan.

PURE logika dipakai dari simple_variants/candle_scoring; modul ini hanya
alat ukur riset, bukan bagian dari trading driver.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "data" / "research" / "r1" / "demo"
sys.path.insert(0, str(ROOT / "strategy_v2"))

from strategy_v2 import candle_scoring as CS  # noqa: E402
from strategy_v2 import simple_variants as SV  # noqa: E402
from strategy_v2.demo_driver import get, tf_candles  # noqa: E402


def first_block(dec: dict) -> str:
    for s in dec.get("steps", []):
        if not s.get("ok", True):
            return s.get("k", "?")
    # langkah bernilai ok False pada reject() tinggal satu: reason dari reject
    r = dec.get("reason", "")
    for key, name in (("kill switch", "KillSwitch"), ("news gate", "News"),
                      ("bias momentum", "Momentum"), ("struktur", "Struktur"),
                      ("RSI", "RSI-guard"), ("momentum habis", "Exhausted"),
                      ("skor candle", "Skor"), ("TP menabrak", "TP-vs-level")):
        if key in r.lower():
            return name
    return "LOLOS" if dec.get("ok") else "?"


def pipeline_snapshot(m1, m5, m15, h4, now_epoch) -> dict:
    """Pipeline MICRO penuh pada satu titik waktu (tanpa efek samping)."""
    ks = SV.KillSwitch()
    dec = SV.decide("MICRO", m5, m15, h4, 0.0, None, now_epoch, ks, m1_bars=m1)
    ctx = {tf: CS.context_points(bars) for tf, bars in
           (("M1", m1), ("M5", m5), ("M15", m15)) if bars and len(bars) >= 3}
    sb = CS.structure_direction(m15)
    return {
        "ts": now_epoch,
        "momentum": SV.momentum_bias(m15),
        "structure": sb,
        "rsi": {"M15": CS.rsi([b["close"] for b in m15], 14),
                "M5": CS.rsi([b["close"] for b in m5], 14),
                "M1": CS.rsi([b["close"] for b in m1], 14)},
        "exhausted": CS.momentum_exhausted(m5, dec.get("direction") or "BULL")[0],
        "m1_pattern": (ctx.get("M1") or {}).get("pattern"),
        "m1_points": (ctx.get("M1") or {}).get("points", 0),
        "m1_score": dec.get("score", 0.0) if dec.get("checklist") else None,
        "ctx_M5_dir": (ctx.get("M5") or {}).get("direction"),
        "ctx_M15_dir": (ctx.get("M15") or {}).get("direction"),
        "blocked_at": first_block(dec),
        "reason": dec.get("reason", ""),
        "ok": dec.get("ok", False),
    }


def run_observe(duration_s: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    obs = OUT / "observer.jsonl"
    print(f"observe {duration_s}s -> {obs}")
    last_m1 = None
    t0 = time.time()
    while time.time() - t0 < duration_s:
        time.sleep(5)
        try:
            m1_now = tf_candles("M1", 3)
            newest = int(m1_now[-1]["time"])
            if last_m1 is not None and newest <= last_m1:
                continue
            last_m1 = newest
            m1 = tf_candles("M1", 400)[:-1]
            m5 = tf_candles("M5", 400)[:-1]
            m15 = tf_candles("M15", 300)[:-1]
            h4 = tf_candles("H4", 120)[:-1]
            row = pipeline_snapshot(m1, m5, m15, h4, int(time.time()))
            row["candles"] = {"M1": m1[-1]["time"], "M5": m5[-1]["time"],
                              "M15": m15[-1]["time"]}
            with open(obs, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=True) + "\n")
            print(f"[{datetime.now(timezone.utc):%H:%M:%S}] blocked_at={row['blocked_at']:14s}"
                  f" m1={row['m1_pattern'] or '-':22s} pts={row['m1_points']}"
                  f" mom={row['momentum']} struct={row['structure']}")
        except Exception as e:
            print("observe error:", e)
    print("observe selesai")


def run_replay(hours: float, sl_pts: float, tp_pts: float, cooldown_min: int = 0) -> dict:
    """Walk-forward 5 jam terakhir: tiap close M1, evaluasi pipeline dengan
    data s.d. bar itu (tanpa lookahead), lalu simulasikan entri hipotetis.

    Varian gate:
      BASE   : aturan live sekarang (margin 0.25, mayoritas 3)
      M15    : margin 0.15xATR
      MAJ2   : mayoritas 2-swing (dengan margin tetap 0.25)
      MOMFALL: struktur campur TAPI momentum + skor M1 >= 8 → boleh entry
    Outcome dihitung first-touch SL/TP dari bar M1 setelah entry.
    """
    m1_all = tf_candles("M1", 540)[:-1]     # ~9 jam
    m5_all = tf_candles("M5", 400)[:-1]
    m15_all = tf_candles("M15", 300)[:-1]
    h4_all = tf_candles("H4", 120)[:-1]
    t_end = m1_all[-1]["time"]
    t_start = t_end - hours * 3600
    last_entry_epoch = {v: 0.0 for v in ("BASE", "M15", "MAJ2", "MOMFALL", "V4")}

    variants = ("BASE", "M15", "MAJ2", "MOMFALL", "V4")
    stats = {v: {"entries": 0, "win": 0, "loss": 0, "pnl_pts": 0.0,
                 "blocked": {}} for v in variants}

    def struct_variant(bars, variant):
        if variant == "BASE":
            return CS.structure_direction(bars)
        if variant == "M15":
            return CS.structure_direction(bars, margin_atr=0.15, lookback=3)
        if variant == "MAJ2":
            return CS.structure_direction(bars, margin_atr=0.25, lookback=2)
        return CS.structure_direction(bars)

    idx_m5 = 0
    for i in range(40, len(m1_all)):
        bar_t = m1_all[i]["time"]
        if bar_t < t_start:
            continue
        while idx_m5 + 1 < len(m5_all) and m5_all[idx_m5 + 1]["time"] <= bar_t:
            idx_m5 += 1
        m1 = m1_all[:i + 1]
        m5 = [b for b in m5_all[:idx_m5 + 1] if b["time"] <= bar_t]
        m15 = [b for b in m15_all if b["time"] <= bar_t]
        h4 = [b for b in h4_all if b["time"] <= bar_t]
        if len(m5) < 30 or len(m15) < 40 or not m1:
            continue
        # entri hipotetis pada close bar ini; outcome dari bar-bar berikut
        entry = m1_all[i]["close"]
        future = m1_all[i + 1:]
        after_mins = (t_end - bar_t) / 60.0

        for v in variants:
            mb = SV.momentum_bias(m15)
            sb = struct_variant(m15, v)
            block = None
            if v in ("MOMFALL", "V4"):
                # MOMFALL: struktur campur boleh asal skor M1 >= 8;
                # V4: struktur TIDAK lagi gate — campur boleh, bertentangan
                # tetap ditolak; arah dari momentum, fallback konteks M5.
                if sb is not None and mb is not None and sb != mb:
                    if v == "V4":
                        block = "Struktur-bertentangan"
                    else:
                        res0 = CS.score_candle(m1, None, "MICRO", require_volume=False)
                        block = None if res0.get("score", 0) >= 8 else "Skor<8-fallback"
                elif mb is None:
                    block = "Momentum"
                # sb None (campur) → lanjut (fallback skor utk MOMFALL dibawah)
                if block is None and v == "MOMFALL" and sb is None:
                    res0 = CS.score_candle(m1, None, "MICRO", require_volume=False)
                    block = None if res0.get("score", 0) >= 8 else "Skor<8-fallback"
            elif not mb:
                block = "Momentum"
            elif not sb:
                block = "Struktur-campur"
            elif sb != mb:
                block = "Struktur-bertentangan"
            if block:
                stats[v]["blocked"][block] = stats[v]["blocked"].get(block, 0) + 1
                continue
            direction = mb if mb else (CS.context_points(m5) or {}).get("direction") if v == "V4" else mb
            if direction not in ("BULL", "BEAR"):
                stats[v]["blocked"]["Tanpa-arah"] = stats[v]["blocked"].get("Tanpa-arah", 0) + 1
                continue
            rsi_m15 = CS.rsi([b["close"] for b in m15], 14)
            rsi_m5 = CS.rsi([b["close"] for b in m5], 14)
            rsi_m1 = CS.rsi([b["close"] for b in m1], 14)
            direction = mb
            for rv in (rsi_m15, rsi_m5, rsi_m1):
                if rv is None:
                    continue
                if (direction == "BULL" and rv >= SV.RSI_STOP_BUY) or \
                   (direction == "BEAR" and rv <= SV.RSI_STOP_SELL):
                    block = "RSI-guard"
                    break
            if block:
                stats[v]["blocked"][block] = stats[v]["blocked"].get(block, 0) + 1
                continue
            exh, _ = CS.momentum_exhausted(m5, direction)
            if exh:
                stats[v]["blocked"]["Exhausted"] = stats[v]["blocked"].get("Exhausted", 0) + 1
                continue
            # skor M1 threshold 6 (level None utk replay sederhana = paling longgar)
            res = CS.score_candle(m1, None, "MICRO", require_volume=False)
            bname = "Skor<6" if not res.get("ok") else "Arah-pola"
            if not res.get("ok") or res.get("direction") != direction:
                stats[v]["blocked"][bname] = stats[v]["blocked"].get(bname, 0) + 1
                continue
            if cooldown_min and bar_t - last_entry_epoch[v] < cooldown_min * 60:
                stats[v]["blocked"]["Cooldown"] = stats[v]["blocked"].get("Cooldown", 0) + 1
                continue
            # entri hipotetis
            sl_d, tp_d = sl_pts * 0.01, tp_pts * 0.01
            sl = entry - sl_d if direction == "BULL" else entry + sl_d
            tp = entry + tp_d if direction == "BULL" else entry - tp_d
            hit = None
            for fb in future:
                if direction == "BULL":
                    if fb["low"] <= sl:
                        hit = "loss"
                        break
                    if fb["high"] >= tp:
                        hit = "win"
                        break
                else:
                    if fb["high"] >= sl:
                        hit = "loss"
                        break
                    if fb["low"] <= tp:
                        hit = "win"
                        break
            stats[v]["entries"] += 1
            last_entry_epoch[v] = bar_t  # cooldown: blok entri terlalu rapat
            if hit == "win":
                stats[v]["win"] += 1
                stats[v]["pnl_pts"] += tp_pts
            elif hit == "loss":
                stats[v]["loss"] += 1
                stats[v]["pnl_pts"] -= sl_pts
            else:
                # belum sentuh sampai data habis (hanya untuk bar2 paling akhir)
                stats[v]["entries"] -= 1
                continue
            stats[v].setdefault("detail", []).append({
                "ts": bar_t, "dir": direction, "pattern": res.get("pattern"),
                "score": res.get("score"), "outcome": hit,
                "struct": sb, "hour": datetime.fromtimestamp(
                    bar_t, tz=timezone.utc).strftime("%H:00")})
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["observe", "replay"])
    ap.add_argument("--duration", type=int, default=1800)
    ap.add_argument("--hours", type=float, default=5.0)
    ap.add_argument("--sl", type=float, default=170)
    ap.add_argument("--tp", type=float, default=250)
    ap.add_argument("--cooldown", type=int, default=0,
                    help="menit minimal antar entri (anti clustering)")
    args = ap.parse_args()
    if args.mode == "observe":
        run_observe(args.duration)
        return 0
    stats = run_replay(args.hours, args.sl, args.tp, args.cooldown)
    print(json.dumps(stats, indent=2, ensure_ascii=True))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "replay_variants.json").write_text(
        json.dumps({"hours": args.hours, "sl_pts": args.sl, "tp_pts": args.tp,
                    "stats": stats}, indent=2), encoding="utf-8")
    print("-> data/research/r1/demo/replay_variants.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
