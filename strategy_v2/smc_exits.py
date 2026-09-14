"""Simulator exit SMC v3 — parity desain §4 (G2) + baseline single-touch.

PURE: tanpa I/O, tanpa now(), tanpa import smc (hindari siklus; hanya
candle_scoring utk ATR trailing). Semua dari bar M1.

Mode:
  "legacy" — first-touch SL/TP penuh, SL-priority ambigu (parity simulator
             replay lama & shadow_ab → angka comparable baseline 139 trade).
  "g2"     — desain §4: TP1 partial 50% → SL ke breakeven → trailing sisa
             posisi (structure trailing via swing LTF + ATR trailing).
             TP2 = None (exit sisa via trailing; konsisten desain "atau pakai
             trailing"). Time-based exit: MAX_HOLD_S (opsional §4).

Anti-lookahead: posisi di-scan mulai bar M1 SETELAH bar sinyal (bisect atas
entry_time). Trailing hanya melihat swing/ATR yang SUDAH CLOSED pada bar tsb.
SL-priority ambigu (bar menyentuh dua level) → dianggap kena SL (konservatif,
parity simulator lama) — dicatat eksplisit di artefak.
"""
from __future__ import annotations

import bisect

from strategy_v2 import candle_scoring as CS

POINT = 0.01

# ── parameter G2 (rencana §4) ───────────────────────────────────────────────
G2_TP1_FRACTION = 0.5      # partial close 50% di TP1
G2_TRAIL_K_ATR = 2.0       # ATR trailing k×ATR(14) M1 (desain §4: 1.5–2.5)
G2_TRAIL_MODE = "max"      # trailing = max(structure, atr) → selalu ketat yg relevan
MAX_HOLD_S = 24 * 3600     # time-based expire (parity replay baseline)


def _swing_sl_for_trail(direction: str, bars: list) -> float | None:
    """Swing LTF terakhir SEBELUM bar terakhir (tanpa lookahead: bar [-1]
    tidak dianggap terkonfirmasi). BUY → swing low terbaru; SELL → swing high."""
    k = 2
    if len(bars) < 2 * k + 2:
        return None
    body = bars[:-1]
    best = None
    for i in range(len(body) - k):
        win = body[i:i + 2 * k + 1]
        if direction == "BUY":
            if min(float(b["low"]) for b in win) == float(win[k]["low"]):
                best = float(win[k]["low"])  # terbaru menimpa
        else:
            if max(float(b["high"]) for b in win) == float(win[k]["high"]):
                best = float(win[k]["high"])
    return best


def simulate(direction: str, entry: float, sl: float, tp: float,
             entry_time: int, m1_by_time: dict, m1_times: list,
             mode: str = "legacy", atr_fn=None) -> dict:
    """Simulasi exit dari bar M1 setelah entry_time. Return:
    {outcome, exit_px, exit_time, gross_pts (per 1.0 posisi), parts}.

    gross_pts mode g2 = 0.5*leg1 + 0.5*leg2 (weighting eksplisit).
    """
    sign = 1 if direction == "BUY" else -1
    start = bisect.bisect_right(m1_times, entry_time)
    if mode == "legacy":
        prev_t = entry_time
        for k in range(start, len(m1_times)):
            t = m1_times[k]
            if t - entry_time > MAX_HOLD_S:
                px = float(m1_by_time[t]["close"])
                return {"outcome": "EXPIRE", "exit_px": px, "exit_time": t,
                        "gross_pts": round(sign * (px - entry) / POINT, 1)}
            b = m1_by_time[t]
            hit_sl = b["low"] <= sl if direction == "BUY" else b["high"] >= sl
            hit_tp = b["high"] >= tp if direction == "BUY" else b["low"] <= tp
            if hit_sl:
                return {"outcome": "SL", "exit_px": sl, "exit_time": t,
                        "gross_pts": round(-abs(entry - sl) / POINT, 1)}
            if hit_tp:
                return {"outcome": "TP", "exit_px": tp, "exit_time": t,
                        "gross_pts": round(abs(tp - entry) / POINT, 1)}
        return {"outcome": "OPEN", "exit_px": None, "exit_time": None,
                "gross_pts": 0.0}

    # ── mode g2: partial 50% + BE + trailing ──
    be = False
    leg1_done = False
    trail = sl            # SL utk sisa posisi (mulai = SL awal)
    for k in range(start, len(m1_times)):
        t = m1_times[k]
        if t - entry_time > MAX_HOLD_S:
            px = float(m1_by_time[t]["close"])
            # sisa posisi tutup di close (mtm); leg1 sudah fix bila selesai
            if leg1_done:
                g = (G2_TP1_FRACTION * abs(tp - entry) +
                     (1 - G2_TP1_FRACTION) * sign * (px - entry)) / POINT
                return {"outcome": "TP1_EXPIRE", "exit_px": px, "exit_time": t,
                        "gross_pts": round(g, 1)}
            g = sign * (px - entry) / POINT
            return {"outcome": "EXPIRE", "exit_px": px, "exit_time": t,
                    "gross_pts": round(g, 1)}
        b = m1_by_time[t]
        if direction == "BUY":
            hit_sl = float(b["low"]) <= trail
            hit_tp = (not leg1_done) and float(b["high"]) >= tp
        else:
            hit_sl = float(b["high"]) >= trail
            hit_tp = (not leg1_done) and float(b["low"]) <= tp

        # SL DULU (konservatif): bar yang menyentuh TP1 DAN SL lama bersamaan
        # → SL_full; BE/trailing baru efektif utk bar BERIKUTNYA.
        if hit_sl:
            if not leg1_done:
                return {"outcome": "SL_full", "exit_px": trail,
                        "exit_time": t,
                        "gross_pts": round(-abs(entry - sl) / POINT, 1)}
            # sisa posisi keluar di trail (BE / structure / ATR)
            leg1_pts = abs(tp - entry) / POINT          # unit harga → poin
            leg2 = sign * (trail - entry) / POINT
            g = (G2_TP1_FRACTION * leg1_pts +
                 (1 - G2_TP1_FRACTION) * leg2)
            outcome = ("TP1_BE" if abs(trail - entry) < 1e-9
                       else "TP1_TRAIL")
            return {"outcome": outcome, "exit_px": trail, "exit_time": t,
                    "gross_pts": round(g, 1)}
        if hit_tp:
            leg1_done = True
            # BE: SL sisa = entry (desain §4 "pindahkan SL ke breakeven")
            trail = entry

        # trailing update utk bar BERIKUTNYA (hanya data closed — no lookahead)
        if leg1_done:
            cand = []
            hist = [m1_by_time[x] for x in m1_times[max(0, k - 60):k + 1]]
            sw = _swing_sl_for_trail(direction, hist)
            if sw is not None:
                cand.append(sw - 0.05 if direction == "BUY" else sw + 0.05)
            if atr_fn is not None:
                a = atr_fn(hist[-120:])
                if a:
                    cand.append(float(b["close"]) -
                                G2_TRAIL_K_ATR * a if direction == "BUY"
                                else float(b["close"]) + G2_TRAIL_K_ATR * a)
            if cand:
                new = max(cand) if direction == "BUY" else min(cand)
                # SL tidak pernah mundur (melonggar) — kontrak test bab 4
                if direction == "BUY":
                    trail = max(trail, new)
                else:
                    trail = min(trail, new)
    if leg1_done:
        return {"outcome": "OPEN_TP1", "exit_px": None, "exit_time": None,
                "gross_pts": 0.0}
    return {"outcome": "OPEN", "exit_px": None, "exit_time": None,
            "gross_pts": 0.0}
