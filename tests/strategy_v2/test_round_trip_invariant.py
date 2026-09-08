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


def test_broker_meta_tick_value_conflict_guard():
    """Kalibrasi empiris 2026-09-08 (Finex demo): broker melaporkan
    trade_tick_value=10.0 padahal order_calc_profit-nya sendiri membayar
    $1.00/poin/lot (= contract_size x point). tick_value yang dilaporkan
    TIDAK konsisten → nilai HITUNGAN yang dipakai + konflik dicatat.
    Guard $17/lot tidak boleh dirusak metadata broker yang salah."""
    meta = load_broker_meta({"symbol_info": {"XAUUSD": {
        "contract_size": 100.0, "point": 0.01, "tick_value": 10.0}}})
    assert meta["source"] == "BRIDGE_SYMBOL_INFO"
    assert meta["tick_value"] == pytest.approx(1.0)          # computed wins
    assert meta["tick_value_source"] == "COMPUTED_CONFLICT"
    assert meta["tick_value_reported_broker"] == pytest.approx(10.0)
    assert point_value_usd_per_lot(meta) == pytest.approx(1.0)


def test_broker_meta_tick_value_consistent_adopted_from_broker():
    """tick_value broker konsisten (±1%) dengan contract_size x point →
    diadopsi apa adanya (sumber BROKER)."""
    meta = load_broker_meta({"symbol_info": {"XAUUSD": {
        "contract_size": 100.0, "point": 0.01, "tick_value": 1.0}}})
    assert meta["tick_value"] == pytest.approx(1.0)
    assert meta["tick_value_source"] == "BROKER"


def test_broker_meta_invalid_spec_fails_closed_to_fallback():
    """Spec nol/rusak (pv akan 0) → FALLBACK, bukan meta mati."""
    meta = load_broker_meta({"symbol_info": {"XAUUSD": {
        "contract_size": 0.0, "point": 0.01}}})
    assert meta["source"] == "FALLBACK"
    assert point_value_usd_per_lot(meta) == pytest.approx(1.0)


# ─── PRICE BASIS / SIDES (E-1) ──────────────────────────────────────────────

def test_price_basis_sides_recorded():
    """BUY fill di ASK (open+spread), SELL fill di BID (open); exit di sisi
    berlawanan; candle_price_basis = BID tetap (E-1)."""
    tb = _flat_round_trip("BUY")
    ts = _flat_round_trip("SELL")
    assert (tb["entry_side"], tb["exit_side"]) == ("ASK", "BID")
    assert (ts["entry_side"], ts["exit_side"]) == ("BID", "ASK")
    assert tb["price_basis"] == ts["price_basis"] == "BID"
    assert tb["entry"] == pytest.approx(4400.0 + 17.0 * 0.01)  # spread masuk harga
    assert ts["entry"] == pytest.approx(4400.0)                # SELL di BID: tanpa spread
    assert len(tb["broker_meta_hash"]) == 64


# ─── POSITION STATE MACHINE (E-3, ONE_POSITION_ONLY) ────────────────────────

def test_state_machine_same_direction_rejected_position_open():
    """Sinyal searah saat LONG terbuka → REJECTED:position_open, 1 trade saja
    (tidak ada phantom stacking)."""
    m5 = flat_m5(60)
    recs = signal_record("BUY", idx=40, lot=0.1) + signal_record("BUY", idx=45, lot=0.1)
    ex = run_execution_replay(recs, m5, PROFILE, spread_points=17.0,
                              slippage_points=0.0, delay_bars=0)
    assert len(ex["trades"]) == 1
    assert any(r["reason"] == "position_open" for r in ex["rejected_executions"])
    # state terbuka saat EOD (state_after FLAT karena EOD_MARK tutup posisi)
    assert ex["trades"][0]["state_before"] == "LONG"
    assert ex["trades"][0]["state_after"] == "FLAT"


def test_state_machine_opposite_direction_exit_then_reverse():
    """Sinyal berlawanan saat terbuka → exit_then_reverse: posisi lama tutup
    pada bar sinyal (REVERSAL), posisi baru fill next-bar-open."""
    m5 = flat_m5(60)
    recs = signal_record("BUY", idx=40, lot=0.1) + signal_record("SELL", idx=45, lot=0.1)
    ex = run_execution_replay(recs, m5, PROFILE, spread_points=17.0,
                              slippage_points=0.0, delay_bars=0)
    assert len(ex["trades"]) == 2
    t0, t1 = ex["trades"]
    assert t0["exit_reason"] == "REVERSAL" and t0["direction"] == "BUY"
    assert t1["direction"] == "SELL"
    assert t1["entry_ts"] == t1["signal_ts"]  # fill di bar T+1 (open ts == T)
    assert ex["state_transitions"]["reversals"] == 1
    assert t0["state_before"] == "LONG" and t0["state_after"] == "FLAT"
    assert t1["state_before"] == "SHORT" and t1["state_after"] == "FLAT"


def test_state_machine_eod_mark_labeled():
    """Posisi terbuka di akhir dataset → EOD_MARK dilabeli, state FLAT."""
    m5 = flat_m5(60)
    recs = signal_record("BUY", idx=55, lot=0.1)
    ex = run_execution_replay(recs, m5, PROFILE, spread_points=17.0,
                              slippage_points=0.0, delay_bars=0)
    assert len(ex["trades"]) == 1
    assert ex["trades"][0]["exit_reason"] == "EOD_MARK"
    assert ex["state_transitions"]["eod_marks"] == 1
    assert ex["position_state"] == "FLAT"


# ─── SELL TRIGGER SEMANTICS (E-1: exit SELL di ASK = level + spread) ────────

def test_sell_sl_trigger_bid_equivalent_not_premature():
    """SELL SL di ASK level → trigger saat BID >= level − spread (bukan level
    + spread — itu premature). Bar high 4401.00, SL level 4401.00, spread
    0.17 → trigger TEPAT di bar itu (4401.00 >= 4400.83), exit = ASK level."""
    m5 = flat_m5(60)
    m5[52]["high"] = 4401.00  # tepat menyentuh level SL
    recs = signal_record("SELL", idx=50, sl=100.0, tp=100.0, lot=0.1)
    ex = run_execution_replay(recs, m5, PROFILE, spread_points=17.0,
                              slippage_points=0.0, delay_bars=0)
    t = ex["trades"][0]
    assert t["exit_reason"] == "SL"
    assert t["exit"] == pytest.approx(4401.00)   # exit di ASK level (BID + spread)
    # loss harga = 100 poin (4400.00 BID-in → 4401.00 ASK-out)
    assert t["gross_points"] == pytest.approx(-100.0)


def test_sell_sl_not_triggered_below_bid_threshold():
    """Bar high di bawah threshold BID (level − spread) → TIDAK trigger
    (dulu buggy: trigger pada level + spread = premature)."""
    m5 = flat_m5(60)
    m5[52]["high"] = 4400.80  # < 4401.00 − 0.17 = 4400.83 → belum kena
    recs = signal_record("SELL", idx=50, sl=100.0, tp=100.0, lot=0.1)
    ex = run_execution_replay(recs, m5, PROFILE, spread_points=17.0,
                              slippage_points=0.0, delay_bars=0)
    assert ex["trades"][0]["exit_reason"] == "EOD_MARK"


def test_position_closed_chronologically_without_later_signal():
    """Scan kronologis: SL hit di bar 52 (1 bar setelah entry) → tutup di bar
    itu walau TIDAK ADA sinyal setelahnya (dulu buggy: posisi menggantung
    sampai EOD_MARK)."""
    m5 = flat_m5(60)
    m5[52]["low"] = 4390.0  # SL hit 1 bar setelah entry
    recs = signal_record("BUY", idx=50, sl=100.0, tp=100.0, lot=0.1)
    ex = run_execution_replay(recs, m5, PROFILE, spread_points=17.0,
                              slippage_points=0.0, delay_bars=0)
    t = ex["trades"][0]
    assert t["exit_reason"] == "SL"
    assert t["exit_ts"] == M5_START + 53 * 300  # close bar 52
    assert ex["state_transitions"]["eod_marks"] == 0


# ─── REGRESSION GUARD: $17/lot, BUKAN $3400 (E-2) ───────────────────────────

def test_cost_17_usd_per_lot_regression_guard():
    """Contoh riil bridge: spread 0.17 harga (raw 1700 PRICE_1E4) → cost
    $17/lot per sisi, BUKAN $3400 (bug unit 100× tidak boleh kembali).
    Mandat F2b: guard permanen atas contoh riil ini."""
    pts = normalize_spread(1700.0, "PRICE_1E4")
    assert pts == pytest.approx(17.0)
    m5 = flat_m5(60)
    # BUY flat, lot 1.0, komisi 0: cost_usd = exit spread saja = $17/lot
    ex = run_execution_replay(signal_record("BUY", idx=50, lot=1.0), m5, PROFILE,
                              spread_points=pts, slippage_points=0.0, delay_bars=0,
                              commission_usd_per_lot=0.0)
    t = ex["trades"][0]
    assert t["cost_usd"] == pytest.approx(17.0)   # exit spread saja (BUY)
    assert t["net_usd"] == pytest.approx(-34.0)   # entry+exit spread, flat
    assert t["gross_usd"] == pytest.approx(-17.0)  # spread entry di path harga
    # SELL flat identik: cost_usd = entry spread saja = $17/lot
    ex2 = run_execution_replay(signal_record("SELL", idx=50, lot=1.0), m5, PROFILE,
                               spread_points=pts, slippage_points=0.0, delay_bars=0,
                               commission_usd_per_lot=0.0)
    t2 = ex2["trades"][0]
    assert t2["cost_usd"] == pytest.approx(17.0)   # entry spread saja (SELL)
    assert t2["net_usd"] == pytest.approx(-34.0)
    assert t2["gross_usd"] == pytest.approx(-17.0)  # spread exit di path harga
    # dan model biaya langsung: 17+17 poin = $34/lot round-trip (tanpa komisi)
    from strategy_v2.costs import compute_cost
    c = compute_cost(pts, pts, commission=0.0)
    assert c["total_usd_per_lot"] == pytest.approx(34.0)


def test_state_machine_cooldown_still_enforced():
    """Cooldown tetap berlaku per entry (incl. setelah FLAT) — bukan hanya
    position gate."""
    m5 = flat_m5(60)
    recs = signal_record("BUY", idx=20, lot=0.1) + signal_record("BUY", idx=24, lot=0.1)
    ex = run_execution_replay(recs, m5, PROFILE, spread_points=17.0,
                              slippage_points=0.0, delay_bars=0)
    # flat price → posisi pertama tidak pernah hit SL/TP; kedua = position_open
    assert any(r["reason"] == "position_open" for r in ex["rejected_executions"])
    # skenario cooldown murni: posisi tutup (SL di bar entry) lalu sinyal baru
    # dekat — cooldown 5m == 1 bar, jadi T2-T1 = 300 tidak < 300 → perlu profil
    # dengan cooldown lebih panjang dari 1 bar utk men-test rejection.
    P2 = dict(PROFILE)
    P2["risk"] = {**PROFILE["risk"], "cooldown_minutes": 10}
    m5b = flat_m5(60)
    m5b[21]["low"] = 4300.0  # SL hit pada bar entry sendiri
    recs2 = signal_record("BUY", idx=20, lot=0.1) + signal_record("BUY", idx=21, lot=0.1)
    ex2 = run_execution_replay(recs2, m5b, P2, spread_points=17.0,
                               slippage_points=0.0, delay_bars=0)
    assert len(ex2["trades"]) == 1
    assert any(r["reason"] == "cooldown" for r in ex2["rejected_executions"])