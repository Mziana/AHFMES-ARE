"""P1 — Cost model komponen (desain §4) dengan label sumber (Pagar cost).

Bila spread historis per-bar tersedia → label HISTORICAL.
Bila tidak → fallback konstanta dari registry.COST_MODEL dengan label
ESTIMATED_COST_MODEL — TIDAK PERNAH disajikan sebagai market truth.
"""
from __future__ import annotations

from . import registry


class UnsupportedCostModel(ValueError):
    """Slippage/delay non-zero di-declare tapi TIDAK didukung executor (P0-03)."""


def assert_supported_cost_model(cost: dict) -> None:
    """P0-03 — fail-closed: slippage/delay adalah komponen yang DI-DECLARE tapi
    BELUM di-apply di execution replay. Bila ada yang men-set nilai non-zero
    (config/model/pemanggil), replay harus MENOLAK, bukan diam-diam mengabaikan
    biaya yang tidak diterapkan. Spread + commission memang diterapkan nyata
    (entry ask/bid + potongan USD/lot); slippage & delay wajib 0 sampai
    diimplementasikan."""
    if cost["slippage_points"] != 0.0:
        raise UnsupportedCostModel(
            f"slippage_points={cost['slippage_points']} declared but not applied in "
            "execution replay — set 0 or implement slippage application first")
    if cost["delay_bars"] != 0:
        raise UnsupportedCostModel(
            f"delay_bars={cost['delay_bars']} declared but not applied in "
            "execution replay — set 0 or implement delay shifting first")


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

    total_points = es + xs + slip
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
