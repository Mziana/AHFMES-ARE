"""P1 — Cost model komponen (desain §4) dengan label sumber (Pagar cost).

Bila spread historis per-bar tersedia → label HISTORICAL.
Bila tidak → fallback konstanta dari registry.COST_MODEL dengan label
ESTIMATED_COST_MODEL — TIDAK PERNAH disajikan sebagai market truth.
P0-03 opsi A (diimplementasikan): slippage & delay kini DIAPLIKASI di
execution replay — slippage = penyesuaian harga fill adverse (order market),
delay = geser fill beberapa bar. Deduksi biaya USD tetap spread + commission
saja (slippage mempengaruhi gross via harga fill, TIDAK dipotong dua kali).
"""
from __future__ import annotations

import math

from . import registry


class UnsupportedCostModel(ValueError):
    """Cost model invalid: slippage/delay negatif atau non-finite (P0-03)."""


def assert_supported_cost_model(cost: dict) -> None:
    """P0-03 — validasi cost model. Slippage/delay kini diaplikasikan nyata di
    execution replay, jadi nilai apapun >= 0 diterima; nilai invalid (negatif,
    non-finite, tipe salah) ditolak fail-closed."""
    slip = cost["slippage_points"]
    dly = cost["delay_bars"]
    if not (isinstance(slip, (int, float)) and not isinstance(slip, bool)
            and math.isfinite(slip) and slip >= 0):
        raise UnsupportedCostModel(
            f"slippage_points={slip!r} invalid — harus angka >= 0")
    if not (isinstance(dly, int) and not isinstance(dly, bool) and dly >= 0):
        raise UnsupportedCostModel(
            f"delay_bars={dly!r} invalid — harus int >= 0")


def compute_cost(entry_spread: float | None, exit_spread: float | None,
                 commission: float | None = None, slippage: float | None = None,
                 delay: int | None = None) -> dict:
    """Hitung biaya trade (poin XAUUSD + USD/lot). Semua input poin = 0.01 harga.

    entry_spread/exit_spread None → fallback konstanta → label ESTIMATED_COST_MODEL.
    """
    cm = registry.COST_MODEL
    historical = entry_spread is not None and exit_spread is not None
    es = float(entry_spread) if entry_spread is not None else cm["fallback_entry_spread_points"]
    xs = float(exit_spread) if exit_spread is not None else cm["fallback_exit_spread_points"]
    comm = float(commission) if commission is not None else cm["commission_per_lot_usd"]
    slip = float(slippage) if slippage is not None else cm["slippage_points"]
    dly = int(delay) if delay is not None else cm["delay_bars"]
    assert_supported_cost_model({"slippage_points": slip, "delay_bars": dly})

    # Deduksi USD = spread + commission SAJA. Slippage TIDAK masuk deduksi:
    # ia sudah diterapkan via harga fill adverse di execution replay (P0-03
    # opsi A) — memasukkannya di sini = double counting (tertangkap test).
    total_points = es + xs
    # XAUUSD: 1 lot = 100 oz → 1 poin (0.01) = $1 per lot.
    total_usd_per_lot = total_points * 1.0 + comm

    return {
        "label": cm["label_when_historical"] if historical else cm["label_when_fallback"],
        "entry_spread_points": es,
        "exit_spread_points": xs,
        "slippage_points": slip,
        "delay_bars": dly,
        "commission_usd_per_lot": comm,
        "total_points": total_points,
        "total_usd_per_lot": total_usd_per_lot,
    }
