"""F1a — RED invariant: round-trip execution + unit normalisasi (E-1/E-2).

INVARIANT ROUND-TRIP (desain §10.1 E-1): pada harga flat, round-trip BUY dan
SELL (slippage=0, delay=0, komisi=0) masing-masing menghasilkan

    net_usd = -(entry_spread + exit_spread) * point_value * lot

PERSIS. Selisih apa pun = fail.

Test ini HARUS GAGAL terhadap kode sebelum F1b (bukti bug PnL fiksi):
- double-count spread: entry BUY sudah = open + spread (biaya masuk harga),
  lalu cost_usd memotong entry+exit spread LAGI → net di bawah invariant;
- unit spread 100×: bridge PRICE_1E4 (1700 = 0.17 harga) vs poin 0.01 →
  cost $3400/lot padahal realita $17/lot (E-2).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import registry
from strategy_v2.broker_meta import (UnknownSpreadUnit, broker_meta_hash,
                                     load_broker_meta, normalize_spread,
                                     point_value_usd_per_lot)
from strategy_v2.replay import run_execution_replay

M5_START = 1788739200  # 2026-09-07 00:00 UTC


def flat_m5(n: int = 60, price: float = 4400.0) -> list:
    """Harga flat — round-trip invariant: zero market move, costs only."""
    return [{"time": M5_START + i * 300, "open": price, "high": price,
             "low": price, "close": price, "volume": 100 + (i % 5)}
            for i in range(n)]


def signal_record(decision: str, idx: int = 50, sl: float = 100.0,
                  tp: float = 100.0, lot: float = 1.0) -> list:
    return [{"evaluation_timestamp": M5_START + (idx + 1) * 300,
             "decision": decision, "sl_points": sl, "tp_points": tp,
             "lot": lot}]


PROFILE = registry.load_profile("MICRO")


# ─── INVARIANT ROUND-TRIP (E-1) ─────────────────────────────────────────────

def _flat_round_trip(direction: str, entry_spread: float = 17.0,
                     exit_spread: float = 17.0, commission: float = 0.0,
                     lot: float = 1.0) -> dict:
    m5 = flat_m5()
    records = signal_record(direction, lot=lot)
    ex = run_execution_replay(records, m5, PROFILE,
                              spread_points=entry_spread,
                              slippage_points=0.0, delay_bars=0,
                              commission_usd_per_lot=commission)
    assert len(ex["trades"]) == 1, "round-trip harus menghasilkan 1 trade"
    return ex["trades"][0]


def test_invariant_round_trip_buy_flat_price():
    """BUY flat: net = -(entry_spread + exit_spread) * point_value * lot."""
    t = _flat_round_trip("BUY")
    pv = point_value_usd_per_lot(load_broker_meta({}))
    assert t["net_usd"] == pytest.approx(-(17.0 + 17.0) * pv * t["lot"], abs=1e-9)


def test_invariant_round_trip_sell_flat_price():
    """SELL flat: mirror — sama loss persis (konsisten untuk BUY & SELL)."""
    t = _flat_round_trip("SELL")
    pv = point_value_usd_per_lot(load_broker_meta({}))
    assert t["net_usd"] == pytest.approx(-(17.0 + 17.0) * pv * t["lot"], abs=1e-9)


def test_invariant_round_trip_with_commission():
    """Komisi masuk invariant: net = -(entry+exit+commission) * pv * lot."""
    t = _flat_round_trip("BUY", commission=1.0)
    pv = point_value_usd_per_lot(load_broker_meta({}))
    assert t["net_usd"] == pytest.approx(-(17.0 + 17.0 + 1.0) * pv * t["lot"],
                                         abs=1e-9)


# ─── UNIT NORMALISASI (E-2) ─────────────────────────────────────────────────

def test_normalize_spread_price_1e4_to_points():
    # conto riil bridge: bid 4412.42 / ask 4412.59 → spread 1700 (PRICE_1E4)
    # = 0.17 harga = 17 poin (0.01)
    assert normalize_spread(1700, "PRICE_1E4") == pytest.approx(17.0)
    assert normalize_spread(17, "POINTS_001") == pytest.approx(17.0)


def test_normalize_spread_unknown_unit_fails_closed():
    with pytest.raises(UnknownSpreadUnit):
        normalize_spread(10.0, "RAW_UNIT")


def test_point_value_xauusd_computed_not_hardcoded():
    meta = load_broker_meta({})  # fallback XAUUSD
    assert meta["source"] == "FALLBACK"
    assert point_value_usd_per_lot(meta) == pytest.approx(1.0)  # 100 oz × 0.01
    # broker meta eksplisit (field baru bridge) → dihitung dari contract_size × point
    meta2 = load_broker_meta(
        {"symbol_info": {"XAUUSD": {"contract_size": 100.0, "point": 0.01}}})
    assert meta2["source"] == "BRIDGE_SYMBOL_INFO"
    assert point_value_usd_per_lot(meta2) == pytest.approx(1.0)


def test_broker_meta_hash_stable_and_sensitive():
    h1 = broker_meta_hash(load_broker_meta({}))
    h2 = broker_meta_hash(load_broker_meta({}))
    assert h1 == h2 and len(h1) == 64
    meta2 = load_broker_meta(
        {"symbol_info": {"XAUUSD": {"contract_size": 100.0, "point": 0.01}}})
    assert broker_meta_hash(meta2) != h1