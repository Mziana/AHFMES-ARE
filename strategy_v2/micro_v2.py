"""MICRO v2.1 "SCALP-M1 0.9/1.4" — mesin SCALP turun satu TF (owner-approved 2026-09-11).

Hipotesis terdaftar MICRO-V2.1-0.9-1.4 (genealogy: parent SCALP-M5, pelajaran
H-EXEC-M1-01 + studi offline REPORT_MICRO_V2_STUDY.md). Replika PERSIS konfigurasi
varian utama studi offline (scripts/micro_v2_study.py, varian "v1.0|65_35|M0.9_T1.4"):

  - Eksekusi sinyal   : bar M1 CLOSE (jendela 400 bar == driver)
  - Bias momentum     : M5 EMA9/21 + RSI 45/55 (SV.momentum_bias — kode asli)
  - RSI ekstrem guard : 65/35 di M5 + M1 (revisi owner — lebih ketat utk volatilitas)
  - Skor candle       : score_candle profil SCALP di M1 (threshold 7, kode asli)
  - Volume wajib      : >= 1.1x avg5 M1 (owner rev 2026-09-11 sore — "lucky
                        shot": 2W/1L perdana terlalu kecil utk dipercaya);
                        bonus +1 TETAP hanya di >= 1.2x
                        (decouple — replika score_for_variant studi)
  - Level eksekusi    : EMA9/21 M5 terdekat searah (parity pullback SCALP)
  - SL/TP             : 0.9 / 1.4 x ATR M5 (owner 2026-09-11 — geometri "real dulu",
                        biaya tidak jadi lensa keputusan; hasil replay: WR 40.1%,
                        gross-flat — diuji live dgn kill switch + review n>=20)
  - Cooldown          : 5 menit antar entri (dari driver via last_entry_ts)
  - Lot               : rule lama (SV.fixed_lot): equity >150 -> 0.02, else 0.01
  - Tanpa momentum-habis / struktur H4 / TP-cut swing (warisan MICRO v1 dihapus)

PURE decision layer: tanpa I/O, tanpa now() — semua dari bar + now_epoch. Order
tetap dikirim driver (_run_arm) dengan tag jurnal "MICRO" (UI/toggle/KS tetap).
"""
from __future__ import annotations

from typing import Optional

from strategy_v2 import candle_scoring as CS
from strategy_v2 import simple_variants as SV

# ── Parameter terkunci (owner 2026-09-11) — jangan ubah tanpa hipotesis baru ──
SL_MULT = 0.9                 # x ATR M5
TP_MULT = 1.4                 # x ATR M5
RSI_STOP_BUY = 65.0           # guard M5+M1
RSI_STOP_SELL = 35.0
VOL_MIN = 1.1                 # veto volume (x avg5 M1) — owner rev sore 09-11 (dari 1.0)
VOL_BONUS = 1.2               # bonus +1 hanya di sini (decouple)
THRESHOLD = 7.0               # threshold skor SCALP
POINT = 0.01

# guard: sampel indikator minimal (parity studi & driver)
MIN_M5 = 30
MIN_M1 = 30


def nearest_ema_level(direction: str, e9: Optional[float], e21: Optional[float],
                      px: float) -> Optional[float]:
    """Parity SCALP: EMA9/21 M5 terdekat searah (pullback) — kode asli SV."""
    opts = [v for v in (e9, e21) if v is not None]
    if not opts:
        return None
    if direction == "BULL":
        below = [v for v in opts if v <= px]
        return max(below) if below else max(opts)
    above = [v for v in opts if v >= px]
    return min(above) if above else min(opts)


def _score_volume_v10(m1_bars: list, level: Optional[float]) -> dict:
    """score_candle SCALP dgn veto 1.1x + bonus terpisah 1.2x (replika studi).

    Identik studi: monkeypatch VOL_MULT_SCALP=VOL_MIN (veto), lalu bila bar
    lolos hanya karena [1.1x, 1.2x) → skor −1 (bonus dicabut) dan ok dihitung
    ulang terhadap threshold 7."""
    orig = CS.VOL_MULT_SCALP
    CS.VOL_MULT_SCALP = VOL_MIN
    try:
        res = CS.score_candle(m1_bars, level, "SCALP", require_volume=True)
    finally:
        CS.VOL_MULT_SCALP = orig
    if res.get("ok"):
        avg5 = sum(int(b.get("volume", 0)) for b in m1_bars[-6:-1]) / 5.0
        vol = int(m1_bars[-1].get("volume", 0))
        if avg5 > 0 and VOL_MIN * avg5 <= vol < VOL_BONUS * avg5:
            res = dict(res)
            res["score"] = res.get("score", 0) - 1.0
            res["ok"] = res["score"] >= THRESHOLD
            res["reason"] = "" if res["ok"] else f"skor {res['score']:.0f} < {THRESHOLD:.0f}"
    return res


def decide(m5_bars: list, m1_bars: list, balance: float,
           now_epoch: int = 0, kill: SV.KillSwitch = None,
           last_entry_ts: float = None) -> dict:
    """Keputusan MICRO v2.1 — kontrak return kompatibel SV.decide (driver
    memakai: ok, reason, steps, checklist, score, direction, pattern,
    sl_points, tp_points, lot)."""
    steps = []
    m1_bars = m1_bars or []

    def reject(reason, checklist=None, score=0.0):
        return {"ok": False, "reason": reason, "steps": steps, "score": score,
                "direction": None, "pattern": None, "sl": None, "tp": None,
                "sl_points": None, "tp_points": None,
                "lot": SV.fixed_lot(balance), "checklist": checklist or []}

    # 0. kill switch per arm (kode asli)
    if kill and kill.blocked(now_epoch):
        return reject(f"kill switch: lose streak {kill.lose_streak}x — jeda "
                      f"{kill.remaining_min(now_epoch)} menit lagi")
    steps.append({"k": "Kill switch", "ok": True, "note": "aktif"})

    # 1. data minimum (parity studi: M5 & M1 >= 30 bar)
    if len(m5_bars) < MIN_M5:
        return reject(f"data M5 kurang ({len(m5_bars)} < {MIN_M5})")
    if len(m1_bars) < MIN_M1:
        return reject(f"data M1 kurang ({len(m1_bars)} < {MIN_M1})")

    # 2. bias momentum M5 (turun satu level — kode asli SV.momentum_bias)
    mb = SV.momentum_bias(m5_bars)
    if not mb:
        return reject("bias momentum M5 netral (EMA/RSI tidak searah)")
    steps.append({"k": "Momentum M5 (EMA9/21+RSI45/55)", "ok": True, "note": mb})
    direction = mb

    # 3. cooldown antar entri (dari driver — parity 5 menit)
    if last_entry_ts is not None and now_epoch - last_entry_ts < SV.MICRO_COOLDOWN_S:
        return reject(f"cooldown: {SV.MICRO_COOLDOWN_S // 60} menit antar entri "
                      f"(sisa {int(SV.MICRO_COOLDOWN_S - (now_epoch - last_entry_ts))} detik)")
    steps.append({"k": "Cooldown antar entri", "ok": True,
                  "note": f"{SV.MICRO_COOLDOWN_S // 60} menit"})

    # 4. RSI ekstrem guard 65/35 di M5 + M1 (owner rev — lebih ketat)
    r_m5 = CS.rsi([b["close"] for b in m5_bars], 14)
    r_m1 = CS.rsi([b["close"] for b in m1_bars], 14)
    for tf_name, r_val in (("M5", r_m5), ("M1", r_m1)):
        if r_val is None:
            continue
        if direction == "BULL" and r_val >= RSI_STOP_BUY:
            return reject(f"RSI {tf_name} {r_val:.0f} >= {RSI_STOP_BUY:.0f} "
                          f"(jenuh beli, guard 65/35) — stop BUY")
        if direction == "BEAR" and r_val <= RSI_STOP_SELL:
            return reject(f"RSI {tf_name} {r_val:.0f} <= {RSI_STOP_SELL:.0f} "
                          f"(jenuh jual, guard 65/35) — stop SELL")

    def _fmt(v):
        return f"{v:.0f}" if v is not None else "—"
    steps.append({"k": "RSI ekstrem guard", "ok": True,
                  "note": f"M5 {_fmt(r_m5)} · M1 {_fmt(r_m1)} · "
                          f"stop buy >={RSI_STOP_BUY:.0f}, stop sell <={RSI_STOP_SELL:.0f}"})

    # 5. skor candle M1 (profil SCALP, veto 1.1x, bonus 1.2x decouple)
    entry_px = float(m1_bars[-1]["close"])
    closes5 = [b["close"] for b in m5_bars]
    e9, e21 = CS.ema(closes5, 9), CS.ema(closes5, 21)
    level = nearest_ema_level(direction, e9, e21, entry_px)
    res = _score_volume_v10(m1_bars, level)
    steps.append({"k": "Skor candle M1", "ok": res.get("ok", False),
                  "note": f"{res.get('score', 0):.0f} pts — {res.get('pattern') or '-'}"})
    if not res.get("ok"):
        return reject(res.get("reason") or "skor candle di bawah threshold",
                      checklist=res.get("checklist", []),
                      score=res.get("score", 0.0))

    # 6. SL/TP = 0.9 / 1.4 x ATR M5 (owner 2026-09-11)
    a = CS.atr(m5_bars)
    if not a or entry_px <= 0:
        return reject("ATR M5 tidak tersedia untuk SL/TP")
    sl_dist, tp_dist = SL_MULT * a, TP_MULT * a
    if direction == "BULL":
        sl, tp = entry_px - sl_dist, entry_px + tp_dist
    else:
        sl, tp = entry_px + sl_dist, entry_px - tp_dist
    lot = SV.fixed_lot(balance)
    steps.append({"k": "SL/TP (0.9/1.4 x ATR M5)", "ok": True,
                  "note": f"SL {sl_dist / POINT:.0f}p / TP {tp_dist / POINT:.0f}p · lot {lot}"})

    return {"ok": True, "reason": "", "steps": steps, "score": res.get("score", 0.0),
            "direction": "BUY" if direction == "BULL" else "SELL",
            "pattern": res.get("pattern"), "checklist": res.get("checklist", []),
            "entry": entry_px, "sl": round(sl, 2), "tp": round(tp, 2),
            "sl_points": round(sl_dist / POINT, 1),
            "tp_points": round(tp_dist / POINT, 1), "lot": lot,
            "context": {"M1": CS.context_points(m1_bars),
                        "M5": CS.context_points(m5_bars)}}
