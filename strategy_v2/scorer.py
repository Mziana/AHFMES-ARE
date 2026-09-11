"""Step 4 — SetupScorer (Analyst Desk v2.5, H-SCORE-DESK-01).

Paket A1 dari plan `.hermes/plans/2026-09-08_133000-are-analyst-desk-7-steps.md`.

PURE: zero I/O, zero now(), zero randomness (Pagar 2/4). Bukan mesin keputusan —
HANYA triage deskriptif untuk manusia & journal. Gate veto tetap satu-satunya
jalur entry (layer separation diuji eksplisit: mutasi bobot tidak mengubah
decision/first_veto_reason).

Input: satu record decision log (all_gate_results + setup + trigger +
market_snapshot + sl/tp). Semua bobot & ambang tier dari hypothesis registry
(H-SCORE-DESK-01) — Pagar 1: satu byte berubah → config_hash berubah.

Dimensi 0-10 × bobot registry → total 0-100 (bulat). Tier:
  total >= tiers.paper → "PAPER"
  total >= tiers.watch → "WATCH"
  else                 → "PAST"

Bias non-diral (NO_TRADE/None) → PAST (kandidat memang tidak ada).
Input degenerate (None/NaN/missing) → komponen 0, TANPA exception, TANPA
kredit (fail-closed gaya Layer B). Weights registry degenerate (sum <= 0) →
None (kontrak rusak = fail jelas, bukan skor pura-pura).
"""
from __future__ import annotations

import math

# Pola B5 → kekuatan katalis (sinkron TRIGGER_TIER scoring.py: STRONG >= 0.8,
# MODERATE >= 0.6; tier registry H-IBREAK-01 trigger_tier=0.7).
_STRONG_PATTERNS = {
    "morning_star", "three_white_soldiers", "evening_star", "three_black_crows",
    "bullish_engulfing", "bearish_engulfing",
}
_MODERATE_PATTERNS = {"hammer", "shooting_star", "inside_bar"}


def _clamp10(x: float) -> float:
    return 0.0 if x < 0.0 else (10.0 if x > 10.0 else x)


def _num(x) -> float | None:
    """Angka finite → float; bool/None/NaN/inf → None (tanpa exception)."""
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)) and math.isfinite(float(x)):
        return float(x)
    return None


def score_setup(all_gate_results: dict, market_snapshot: dict, setup: dict | None = None,
                risk: dict | None = None, weights: dict | None = None,
                trigger: dict | None = None) -> dict | None:
    """Skor deskriptif 0-100 dari gate diagnostics. PURE.

    `setup` = record["setup"] (kind/ref/distance_atr). `trigger` =
    record["trigger"] ({pattern, bar_ts}) — sumber kebenaran tunggal pola B5.
    `risk` = nilai risk record: sl_points/tp_points (dimensi rr).
    `weights` = H-SCORE-DESK-01["value"] dari registry.
    Return None HANYA bila kontrak weights registry degenerate (fail-closed
    Pagar 1).
    """
    w = weights or {}
    wt = w.get("weights") or {}
    tiers = w.get("tiers") or {}
    wsum = 0.0
    for v in wt.values():
        n = _num(v)
        if n is not None and n > 0:
            wsum += n
    if wsum <= 0:
        return None
    watch_t = _num(tiers.get("watch"))
    paper_t = _num(tiers.get("paper"))
    trade_t = _num(tiers.get("trade"))
    if watch_t is None or paper_t is None:
        return None

    gr = all_gate_results or {}
    snap = market_snapshot or {}
    setup = setup if isinstance(setup, dict) else {}
    pattern = (trigger or {}).get("pattern") if isinstance(trigger, dict) else None

    # ── trend: dari b3_regime (arah searah = 10; NO_TRADE/DISABLED/None = 0) ──
    b3 = str(gr.get("b3_regime") or "")
    trend = 10.0 if b3.startswith("PASS:BUY_ONLY") or b3.startswith("PASS:SELL_ONLY") else 0.0

    # ── momentum: RSI M5 dalam zona pullback (dekat 50 → bagus; 50±30 → 0) ──
    rsi = _num(snap.get("rsi_m5"))
    momentum = _clamp10(10.0 * (1.0 - abs(rsi - 50.0) / 30.0)) if rsi is not None else 0.0

    # ── volume: vol_ratio — >=1.2 → 10, linear turun ke 0 di 0.8, <0.8 → 0 ──
    vr = _num(snap.get("vol_ratio"))
    volume = _clamp10((vr - 0.8) / 0.4 * 10.0) if vr is not None else 0.0

    # ── level: b4 distance_atr (0.0 = tepat di level = 10; >=0.5 = 0) ──
    dist = _num(setup.get("distance_atr"))
    level = _clamp10((0.5 - dist) / 0.5 * 10.0) if dist is not None else 0.0

    # ── catalyst: kekuatan pola trigger B5 (STRONG=10, MODERATE=6, none=0) ──
    pat = str(pattern or "").lower()
    if pat in _STRONG_PATTERNS:
        catalyst = 10.0
    elif pat in _MODERATE_PATTERNS:
        catalyst = 6.0
    else:
        catalyst = 0.0

    # ── rr: tp_points/sl_points (>=2.0 → 10; 1.0 → 4; linear; <=0 → 0) ──
    sl_pts = _num((risk or {}).get("sl_points"))
    tp_pts = _num((risk or {}).get("tp_points"))
    if sl_pts is not None and tp_pts is not None and sl_pts > 1e-9:
        rr = _clamp10((tp_pts / sl_pts - 1.0) / 1.0 * 10.0 + 4.0)
    else:
        rr = 0.0

    dims = {"trend": trend, "momentum": momentum, "volume": volume,
            "level": level, "catalyst": catalyst, "rr": rr}
    total = 0.0
    for k, dim in dims.items():
        wv = _num(wt.get(k)) or 0.0
        if wv > 0:
            total += (wv / wsum) * dim * 10.0
    total = int(round(min(100.0, max(0.0, total))))

    if total >= paper_t:
        tier = "PAPER"
    elif total >= watch_t:
        tier = "WATCH"
    else:
        tier = "PAST"
    if trade_t is not None and total >= trade_t:
        tier = "TRADE"   # label skor saja — keputusan tetap milik gate (layer separation)
    return {"dimensions": {k: round(v, 4) for k, v in dims.items()},
            "total": total, "tier": tier}
