"""Step 6 — TradePlanBuilder (Analyst Desk v2.5, plan B1).

PURE: zero I/O, zero now(), zero randomness (Pagar 2/4). Narrative DETERMINISTIK:
teks = template + angka dari record. Dilarang LLM/free-text. Tidak ada angka
yang dihitung ulang di luar record (consistency dengan execution replay):
stop/target = sl_points/tp_points record; confidence = total H-SCORE-DESK-01
(transparan, dilabeli deskriptif — bukan probabilitas terkalibrasi).

Plan dibuat untuk tier PAPER/TRADE (dan WATCH sebagai plan hipotesis) — tier
PAST tidak butuh plan, tapi tetap bisa dibangun bila diminta (bias ada).
Bias non-diral (NO_TRADE/None) → None (tidak ada arah, tidak ada plan jujur).

Point value XAUUSD: 1 poin = 0.01 harga (kontrak strategy_v2; broker_meta
point=0.01). Harga = angka dari record; TANPA pembulatan penghitungan baru.
"""
from __future__ import annotations

import math


def _num(x) -> float | None:
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)) and math.isfinite(float(x)):
        return float(x)
    return None


def _px(x) -> str:
    """Format harga XAUUSD 2 desimal (deterministik)."""
    return f"{x:.2f}"


def build_trade_plan(record: dict, profile: dict, broker_meta: dict | None = None) -> dict | None:
    """Trade plan narrative dari satu record decision log. PURE.

    Return None bila tidak ada arah (bias NO_TRADE/None) atau SL invalid —
    plan tanpa invalidation konkret lebih bahaya daripada tanpa plan.
    """
    decision = record.get("decision")
    bias = record.get("bias")
    if decision not in ("BUY", "SELL") and bias not in ("BUY_ONLY", "SELL_ONLY"):
        return None

    sl_pts = _num(record.get("sl_points"))
    if sl_pts is None or sl_pts <= 0:
        return None
    tp_pts = _num(record.get("tp_points"))
    snap = record.get("market_snapshot") or {}
    close = _num(snap.get("close"))
    atr_pts = _num(snap.get("atr"))
    setup = record.get("setup") or {}
    trigger = record.get("trigger") or {}
    score = record.get("setup_score") or {}
    total = _num(score.get("total"))
    tier = str(score.get("tier") or "WATCH")

    point = _num((broker_meta or {}).get("point")) or 0.01
    kind = str(setup.get("kind") or "")
    ref = str(setup.get("ref") or "n/a")
    pattern = str(trigger.get("pattern") or "none")
    direction = "BUY" if (decision == "BUY" or bias == "BUY_ONLY") else "SELL"
    side = "pulled back to" if kind == "ema_pullback" else "bounced off"

    # ── thesis (template + angka record; bahasa Inggris — konsisten log) ──
    vol_state = "elevated" if (_num(snap.get("vol_ratio")) or 0) >= 1.2 else "subdued"
    regime = str(bias or decision).replace("_ONLY", "")
    if atr_pts is not None:
        thesis = (f"XAUUSD {side} {ref} with {vol_state} volume; {regime} regime aligned "
                  f"(ATR {atr_pts:.0f} pts, {pattern} trigger).")
    else:
        thesis = f"XAUUSD {side} {ref} with {vol_state} volume; {regime} regime aligned ({pattern} trigger)."

    # ── invalidation: harga konkret dari SL record (basis arah trade) ──
    if close is not None:
        if direction == "BUY":
            inv_price = close - sl_pts * point
            invalidation = f"Close back below {_px(inv_price)} (SL {sl_pts:.0f} pts from {ref})."
        else:
            inv_price = close + sl_pts * point
            invalidation = f"Close back above {_px(inv_price)} (SL {sl_pts:.0f} pts from {ref})."
    else:
        invalidation = f"Signal-bar invalidation: SL {sl_pts:.0f} pts from {ref} (close price unavailable)."

    # ── confidence = skor deskriptif transparan (BUKAN probabilitas) ──
    confidence = int(total) if total is not None else 0

    rr = round(tp_pts / sl_pts, 2) if (tp_pts is not None and tp_pts > 0) else None
    return {
        "plan_id": f"TP-{record.get('profile_id', 'X')}-{record.get('evaluation_timestamp', 0)}",
        "direction": direction,
        "thesis": thesis,
        "invalidation": invalidation,
        "confidence": confidence,
        "confidence_note": "descriptive score (H-SCORE-DESK-01), not calibrated probability",
        "tier": tier,
        "entry_points": close if close is not None else 0.0,
        "stop_points": round(sl_pts, 2),
        "target_points": round(tp_pts, 2) if tp_pts is not None else 0.0,
        "rr": rr,
    }
