"""F1a — Broker metadata + spread unit normalization (desain §10.1 E-2).

Bridge `/account` melaporkan `spread` = (ask - bid) × 10000 (unit PRICE_1E4):
contoh riil bid 4412.42 / ask 4412.59 → spread "1700" (= 0.17 harga).
1 poin XAUUSD (0.01 harga) = $1/lot (kontrak 100 oz) → spread 0.17 harga =
17 poin (0.01) = $17/lot, BUKAN $1700 (bug unit 100× lama — E-2).

`point_value_usd_per_lot` DIHITUNG dari contract_size × point — bukan hardcode
(`price_mult = 0.01` dihapus dari replay). Bila broker `symbol_info` tidak
tersedia di payload bridge → fallback konstanta profil XAUUSD dengan label
FALLBACK. Unit spread tak dikenal → fail-closed (UnknownSpreadUnit).
"""
from __future__ import annotations

import hashlib
import json

# Unit spread yang bridge/replay boleh deklarasi. Tak dikenal → fail-closed.
PRICE_1E4 = "PRICE_1E4"    # (ask - bid) × 10000 — bridge /account (XAUUSD)
POINTS_001 = "POINTS_001"  # poin 0.01-harga langsung

KNOWN_UNITS = frozenset({PRICE_1E4, POINTS_001})

# Fallback konstanta profil XAUUSD (label FALLBACK bila symbol_info tak ada).
FALLBACK_META = {
    "symbol": "XAUUSD",
    "contract_size": 100.0,   # oz per lot (kontrak standard XAUUSD)
    "point": 0.01,            # harga poin (1 poin = 0.01 harga)
    "tick_value": 1.0,        # USD per poin per lot = contract_size × point
    "source": "FALLBACK",
}


class UnknownSpreadUnit(ValueError):
    """source_unit tak dikenal → fail-closed (E-2)."""


def normalize_spread(raw_value: float, source_unit: str) -> float:
    """Konversi spread ke poin 0.01-harga. Fail-closed bila unit tak dikenal.

    PRICE_1E4: 1 unit = 0.0001 harga = 0.01 poin (0.01 harga) → ÷100.
    POINTS_001: sudah poin 0.01-harga → passthrough.
    """
    if source_unit not in KNOWN_UNITS:
        raise UnknownSpreadUnit(
            f"source_unit={source_unit!r} tak dikenal — fail-closed (E-2)")
    v = float(raw_value)
    if source_unit == PRICE_1E4:
        return v / 100.0
    return v


def load_broker_meta(bridge_account: dict) -> dict:
    """Ekstrak contract_size/point/tick_value dari symbol_info bridge bila ada.

    Field baru di bridge TIDAK wajib — bila tak ada, fallback konstanta profil
    + label FALLBACK. `bridge_account`: dict dari GET /account (keys:
    ticks.<symbol>.spread/stops_level; symbol_info optional).

    tick_value CONFLICT GUARD (bukti kalibrasi 2026-09-08, Finex demo):
    broker melaporkan trade_tick_value=10.0 padahal order_calc_profit-nya
    sendiri membayar $1.00 per poin per lot (= contract_size × point).
    Metadata tick_value broker TIDAK konsisten dengan kalkulator profitnya —
    jadi tick_value yang dilaporkan hanya diadopsi bila konsisten (toleransi
    1%) dengan contract_size × point; bila tidak, nilai HITUNGAN yang dipakai
    dan konfliknya dicatat (tick_value_source=COMPUTED_CONFLICT).
    """
    info = (bridge_account.get("symbol_info") or {}).get("XAUUSD") or {}
    if info.get("contract_size") is not None:
        cs, pt = float(info["contract_size"]), float(info.get("point", 0.01))
        if cs <= 0 or pt <= 0:
            # Spec tidak valid → fail-closed ke FALLBACK (pv=0 mematikan PnL).
            meta = dict(FALLBACK_META)
        else:
            meta = {
                "symbol": "XAUUSD",
                "contract_size": cs,
                "point": pt,
                "tick_value": None,
                "source": "BRIDGE_SYMBOL_INFO",
            }
    else:
        meta = dict(FALLBACK_META)
    computed = meta["contract_size"] * meta["point"]
    reported = info.get("tick_value") if meta["source"] == "BRIDGE_SYMBOL_INFO" else None
    try:
        reported = float(reported) if reported is not None else None
    except (TypeError, ValueError):
        reported = None
    if reported is not None and reported > 0 and computed > 0 \
            and abs(reported - computed) / computed <= 0.01:
        meta["tick_value"] = reported
        meta["tick_value_source"] = "BROKER"
    else:
        meta["tick_value"] = computed
        if reported is not None and reported > 0:
            meta["tick_value_source"] = "COMPUTED_CONFLICT"
            meta["tick_value_reported_broker"] = reported
        else:
            meta["tick_value_source"] = "COMPUTED"
    return meta


def point_value_usd_per_lot(broker_meta: dict) -> float:
    """USD per poin (0.01 harga) per lot — DIHITUNG, bukan hardcode.

    XAUUSD kontrak 100 oz, point 0.01 → 100 × 0.01 = $1/lot per poin.
    """
    return broker_meta["contract_size"] * broker_meta["point"]


def broker_meta_hash(broker_meta: dict) -> str:
    """SHA-256 konten broker meta — masuk config_hash (Pagar 1, E-2)."""
    blob = json.dumps(broker_meta, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()