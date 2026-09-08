"""C0 — Cognitive Layer scorer (H-SCORE-01, desain v2.1 counter-proposal).

PURE: zero I/O, zero now(), zero randomness (Pagar 2). Semua input = bar closed
<= T + nilai pre-computed dari evaluate_all. Unit: 1 poin = 0.01 harga;
ATR dalam POIN (XAUUSD M5 ~200-500 pts = $2-5).

8 komponen 0.0-1.0, skor total = SUM(weights[k] * comp[k]) (weights sum 100).
Guards dua tingkat:
  L1 (semantik utama): input inti degenerate (ATR None/<=0, sl_calc None/skip,
     SL None/<=0) -> skor None -> veto BQ:FAIL:score_error (fail-closed).
  L2 (backstop per komponen): atr/sl <= 1e-9 -> komponen 0.0.

sl_calc PIN ke compute_sl_tp existing: kunci "sl_points" / "tp_points" / "skip"
(TIDAK ada pemetaan nama baru).

Bias "NO_TRADE"/None -> ValueError (fail-closed; kandidat tidak boleh ada
tanpa bias dari B3 — ditest eksplisit).
"""
from __future__ import annotations

import math

from . import zones as Z

# ─── tier pola B5 (B5 tetap syarat kandidat; ini kualitasnya) ────────────────
TRIGGER_TIER = {
    "morning_star": 1.0, "three_white_soldiers": 1.0,
    "evening_star": 1.0, "three_black_crows": 1.0,
    "bullish_engulfing": 0.8, "bearish_engulfing": 0.8,
    "hammer": 0.6, "shooting_star": 0.6,
}
UNKNOWN_PATTERN_SCORE = 0.5   # pola di luar daftar (mis. ablation_any) -> netral


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def bias_dir_from(bias) -> int:
    """BUY_ONLY -> +1, SELL_ONLY -> -1, selain itu raise (fail-closed)."""
    if bias == "BUY_ONLY":
        return 1
    if bias == "SELL_ONLY":
        return -1
    raise ValueError(f"bias tidak valid untuk scorer: {bias!r}")


# ─── komponen (semua return float 0..1; None hanya via L1 di evaluate_quality) ─

def trend_alignment(slope_pt_per_bar: float | None, s_max: float) -> float | None:
    """Kekuatan alignment (arah = 1.0 by construction, kandidat hanya ada saat
    B3 memberi bias). Flip arah: slope berubah tanda -> B3 membatalkan/membalik
    bias -> kandidat lama lenyap; komponen ini konsisten drop bersama momentum."""
    if slope_pt_per_bar is None:
        return None
    return _clamp01(abs(slope_pt_per_bar) / s_max) if s_max > 0 else 0.0


def location_quality(close: float, ema21_m5: float, atr_m5: float | None) -> float:
    """Pengganti B4 binary — jarak kontinu ke EMA21 M5 (tanpa cliff 1.0 ATR)."""
    if atr_m5 is None or atr_m5 <= 1e-9:      # L2 backstop
        return 0.0
    d = abs(close - ema21_m5) / atr_m5
    return _clamp01(1.0 - d / 1.0)


def structure(dist_zone_atr_m15: float | None) -> float:
    """Jarak ke zona M15 searah (dist dalam unit ATR_M15) via zones.py existing.
    Tidak ada zona searah -> 0.0 (tanpa referensi struktur, tanpa kredit)."""
    if dist_zone_atr_m15 is None:
        return 0.0
    return _clamp01(1.0 - dist_zone_atr_m15 / 1.0)


def volume_confirmation(vr: float | None, baseline_valid: bool) -> float:
    """Proxy tick-activity. Baseline invalid -> 0.0 (fail-closed, TANPA kredit)."""
    if not baseline_valid or vr is None:
        return 0.0
    return _clamp01((vr - 0.8) / 0.6)


def cost_quality(spread_pts: float | None, sl_pts: float | None) -> float:
    """Fraksi biaya round-trip terhadap risiko trade: R = 2*spread/SL;
    R >= 0.25 (cost_R_bad) -> 0. Spread None (biaya tak diketahui) -> 0.0."""
    if spread_pts is None or sl_pts is None or sl_pts <= 1e-9:   # L2 backstop
        return 0.0
    r = 2.0 * spread_pts / sl_pts
    return _clamp01(1.0 - r / 0.25)


def trigger_quality(pattern: str) -> float:
    return TRIGGER_TIER.get(pattern, UNKNOWN_PATTERN_SCORE)


def rsi_graded(rsi: float | None, bias_dir: int, band: tuple) -> float:
    """RSI graded. BUY: >hi->1.0, [lo,hi]->0.5, <lo->0.0.
    SELL dibalik eksplisit: <lo->1.0, [lo,hi]->0.5, >hi->0.0."""
    if rsi is None:
        return 0.0
    lo, hi = band
    if bias_dir == 1:
        return 1.0 if rsi > hi else (0.5 if rsi >= lo else 0.0)
    return 1.0 if rsi < lo else (0.5 if rsi <= hi else 0.0)


def momentum_quality(close: float, ema9: float, ema21: float,
                     rsi: float | None, d_rsi: float | None,
                     bias_dir: int, rsi_band: tuple) -> float:
    """Mean 4 sub-check biner/graded (definisi eksplisit H-SCORE-01)."""
    checks = [
        1.0 if (close - ema9) * bias_dir > 0 else 0.0,
        1.0 if (ema9 - ema21) * bias_dir > 0 else 0.0,
        rsi_graded(rsi, bias_dir, rsi_band),
        1.0 if (d_rsi is not None and d_rsi * bias_dir > 0) else 0.0,
    ]
    return sum(checks) / 4.0


def volatility_quality(atr_m5_pts: float | None, band: tuple) -> float:
    """Rezim volatilitas (bukan biaya): in-band -> 1.0; luar band -0.2/100 pts."""
    if atr_m5_pts is None or atr_m5_pts <= 1e-9:   # L2 backstop
        return 0.0
    lo, hi = band
    if lo <= atr_m5_pts <= hi:
        return 1.0
    if atr_m5_pts < lo:
        return max(0.0, 1.0 - 0.2 * ((lo - atr_m5_pts) / 100.0))
    return max(0.0, 1.0 - 0.2 * ((atr_m5_pts - hi) / 100.0))


# ─── risk adjustments (deterministik, post-total) ────────────────────────────

def nearest_any_zone_distance_pts(zones: dict | None, price: float) -> float | None:
    if not zones:
        return None
    levels = [z["level"] for z in zones.get("supports", [])]
    levels += [z["level"] for z in zones.get("resistances", [])]
    if not levels:
        return None
    return min(abs(price - lv) for lv in levels) * 100.0   # harga -> poin


def risk_adjustments(sl_calc: dict | None, spread_pts: float | None,
                     last_bar: dict, atr_m5_pts: float | None,
                     zones: dict | None, adj_cfg: dict) -> tuple[list, str | None]:
    """3 rule penalti. Guard: sl_calc None/skip/SL<=0 -> ([], alasan) — hanya
    penyesuaian di-skip (scoring tetap dihitung bila dipanggil langsung;
    evaluate_quality memvalidasi L1 SEBELUM fungsi ini)."""
    if sl_calc is None or sl_calc.get("skip"):
        return [], "sl_calc None/skip -> adjustments skipped"
    sl_pts = sl_calc.get("sl_points")
    if sl_pts is None or sl_pts <= 0:
        return [], "sl_points None/<=0 -> adjustments skipped"
    adjs: list = []
    if spread_pts is not None and sl_pts < 1.5 * spread_pts:
        adjs.append({"rule": "sl_lt_1_5_spread", "delta": int(adj_cfg["adj_sl_lt_1_5_spread"])})
    if atr_m5_pts is not None:
        rng_pts = (last_bar["high"] - last_bar["low"]) * 100.0
        if rng_pts > 2.0 * atr_m5_pts:
            adjs.append({"rule": "range_gt_2_atr", "delta": int(adj_cfg["adj_range_gt_2_atr"])})
    bias = adj_cfg.get("bias")
    if bias in ("BUY_ONLY", "SELL_ONLY"):
        sl_price = last_bar["close"] - sl_pts / 100.0 if bias == "BUY_ONLY" \
            else last_bar["close"] + sl_pts / 100.0
        d = nearest_any_zone_distance_pts(zones, sl_price)
        if d is not None and d < 20.0:
            adjs.append({"rule": "sl_near_zone", "delta": int(adj_cfg["adj_sl_near_zone"])})
    return adjs, None


# ─── entry point utama ────────────────────────────────────────────────────────

def evaluate_quality(m5: list, zones15: dict | None, bias: str | None,
                     slope_pt_per_bar: float | None, spread_pts: float | None,
                     sl_calc: dict | None, pattern: str,
                     weights: dict, h_score: dict) -> dict | None:
    """Hitung quality_score untuk SATU kandidat. Return None = fail-closed (L1).

    Kandidat = lolos B3 (bias) + B5 (trigger PASS -> `pattern` non-empty) + B7
    (PASS). Dipanggil evaluate_all SETELAH B7 — hanya membaca nilai pre-B7
    (tanpa siklus). `pattern` = pola B5 (hasil evaluate_all, sumber kebenaran
    tunggal untuk trigger_quality).
    """
    # ── L1 guards (semantik utama) ──
    bd = bias_dir_from(bias)                      # raise bila bias tidak valid
    atr5 = Z.atr(m5)
    if atr5 is None or atr5 <= 0:
        return None
    atr5_pts = atr5 * 100.0
    if sl_calc is None or sl_calc.get("skip"):
        return None
    sl_pts = sl_calc.get("sl_points")
    if sl_pts is None or sl_pts <= 0:
        return None
    if not m5:
        return None

    h = h_score or {}
    closes = [b["close"] for b in m5]
    close = closes[-1]
    ema9 = Z.ema(closes, 9)[-1]
    ema21 = Z.ema(closes, 21)[-1]
    rsi_now = Z.rsi(closes)
    # dRSI(5) := rsi[-1] - rsi[-6]  (RSI atas seri tanpa 5 bar terakhir)
    rsi_past = Z.rsi(closes[:-5]) if len(closes) >= 5 + Z.RSI_PERIOD + 1 else None
    d_rsi = (rsi_now - rsi_past) if (rsi_now is not None and rsi_past is not None) else None

    # volume proxy (independen dari B6 yang mungkin disabled via profil)
    n_base = 5
    baseline_valid = len(m5) >= n_base + 1 and all(
        isinstance(b.get("volume"), (int, float)) and not isinstance(b.get("volume"), bool)
        and math.isfinite(b["volume"]) and b["volume"] > 0 for b in m5[-1 - n_base:-1])
    vr = (m5[-1]["volume"] / (sum(b["volume"] for b in m5[-1 - n_base:-1]) / n_base)
          if baseline_valid else None)

    # structure: zona M15 searah (dist harga -> unit ATR15)
    dist_atr15 = None
    if zones15 and zones15.get("atr_m15"):
        res = Z.nearest_zone_distance(zones15, close, bias)
        if res is not None:
            dist_atr15 = res[0] / zones15["atr_m15"]

    breakdown = {
        "trend_alignment": trend_alignment(slope_pt_per_bar, float(h.get("s_max_pt_per_bar", 5.0))),
        "location_quality": location_quality(close, ema21, atr5),
        "structure": structure(dist_atr15),
        "volume_confirmation": volume_confirmation(vr, baseline_valid),
        "cost_quality": cost_quality(spread_pts, sl_pts),
        "trigger_quality": trigger_quality(pattern),
        "momentum_quality": momentum_quality(close, ema9, ema21, rsi_now, d_rsi, bd,
                                             tuple(h.get("rsi_zone_band", (45, 55)))),
        "volatility_quality": volatility_quality(atr5_pts, tuple(h.get("atr_band_pts", (200.0, 500.0)))),
    }
    return _finalize(breakdown, weights, h, m5, atr5_pts, spread_pts, sl_calc,
                     zones15, bd, close, baseline_valid, dist_atr15, slope_pt_per_bar,
                     vr, sl_pts)


def _finalize(breakdown: dict, weights: dict, h: dict, m5: list, atr5_pts: float,
              spread_pts, sl_calc, zones15, bd: int, close: float,
              baseline_valid: bool, dist_atr15, slope_pt_per_bar, vr, sl_pts) -> dict:
    """Skor + adjustments + tier. Dipisah agar pattern (dari evaluate_all)
    bisa diinjeksi tanpa mengubah urutan guard L1."""
    # trigger_quality diinjeksi caller via breakdown["trigger_quality"]
    if any(v is None for v in breakdown.values()):
        return None                                   # L1: komponen inti tak terhitung
    score = sum(float(weights.get(k, 0)) * v for k, v in breakdown.items())
    adj_cfg = {**h, "bias": "BUY_ONLY" if bd == 1 else "SELL_ONLY"}
    adjs, adj_note = risk_adjustments(sl_calc, spread_pts, m5[-1], atr5_pts, zones15, adj_cfg)
    final = max(0.0, min(100.0, score + sum(a["delta"] for a in adjs)))
    thr = h.get("threshold")
    if thr is None:
        tier = "UNRANKED"                             # C0: threshold belum terkalibrasi
    elif final >= float(thr) + 20:
        tier = "PREMIUM"
    elif final >= float(thr) + 10:
        tier = "STRONG"
    elif final >= float(thr):
        tier = "CANDIDATE"
    else:
        tier = "REJECT"
    return {
        "score": round(score, 2),
        "final_score": round(final, 2),
        "breakdown": {k: round(v, 4) for k, v in breakdown.items()},
        "adjustments": adjs,
        "adjustments_note": adj_note,
        "tier": tier,
        "inputs": {
            "slope_pt_per_bar": slope_pt_per_bar,
            "atr_pts": round(atr5_pts, 2),
            "sl_points": round(sl_pts, 2),
            "vr": round(vr, 4) if vr is not None else None,
            "volume_baseline_valid": baseline_valid,
            "dist_zone_atr_m15": round(dist_atr15, 4) if dist_atr15 is not None else None,
        },
    }
