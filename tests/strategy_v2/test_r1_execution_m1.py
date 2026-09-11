"""Test kontrak R1 (S0.2/S0.3/S0.4):
- engine M1 identitas eksak vs run_execution_replay (zero-delay, grid M5)
- gate inside-bar: gated default-off, strict range, forming-bar, placement
- engine M1 pending STOP: placement→trigger→fill, expiry 12, scan pas-bar-placement,
  cancel saat market entry / reversal, ONE_POSITION_ONLY
- B4 threading ambang dari profil (Arm A 0,75)

Skala sintetis: point = 0.01 (1 poin = 0.01 harga), jadi sl_points=1.0 → 0.01.
Grid M1 = 60 detik: dari base B, bar ke-k = B + 60k (B, B+60, B+120, ...).
Semua bar M15 sintetis WAJIB fresh terhadap now_ts (staleness ≤ 3 bar = 2700s).
"""
from __future__ import annotations

import pytest

from strategy_v2 import broker_meta as bm
from strategy_v2.execution_m1 import M1_BAR, M5_BAR, run_execution_m1
from strategy_v2.gates import b5_inside_bar_signal, evaluate_all
from strategy_v2.replay import run_execution_replay

META = bm.load_broker_meta({})
PROFILE = {"risk": {"cooldown_minutes": 5},
           "session_windows_utc": [[0, 24]],
           "news": {"policy": "FAIL_CLOSED", "window_minutes": 30,
                    "staleness_hours": 4, "impacts": ["high"]}}

# M15 uptrend yang VALID utk now_ts tertentu: 30 bar, bar terakhir = now-900
# (1 bar stale), grid 900s, closes naik → B3 classic = BUY_ONLY.


def up_m15_upto(last_close_ts: int, n: int = 30) -> list:
    out = []
    for i in range(n):
        t = last_close_ts - (n - 1 - i) * 900
        c = 1.0 + i * 0.01
        out.append({"time": t, "open": c - 0.005, "high": c + 0.01,
                    "low": c - 0.01, "close": c, "volume": 1000})
    return out


def flat5(t, o, h, l, c, v=1):
    return {"time": t, "open": o, "high": h, "low": l, "close": c, "volume": v}


def m1_from_m5(m5):
    """Grid M1 60s: tiap bar M5 [B, B+300) dipecah jadi 5 bar M1 (B+60k)."""
    out = []
    for b in m5:
        for k in range(5):
            out.append({"time": b["time"] + k * M1_BAR, "open": b["open"],
                        "high": b["high"], "low": b["low"],
                        "close": b["close"], "volume": b.get("volume", 1)})
    return out


def rec(T, decision="BUY", sl=3.0, tp=4.5, lot=0.02, bias="BUY_ONLY", **kw):
    d = {"evaluation_timestamp": T, "decision": decision, "sl_points": sl,
         "tp_points": tp, "lot": lot, "bias": bias}
    d.update(kw)
    return d


def ex_m1(records, m5, m1, **kw):
    kw.setdefault("spread_points", 17.0)
    kw.setdefault("slippage_points", 0.0)
    kw.setdefault("broker_meta", META)
    return run_execution_m1(records, m5, m1, PROFILE, **kw)


# ── identitas M1 vs M5 (zero-delay) ─────────────────────────────────────────

def test_m1_identity_with_m5_engine_buy():
    m5 = [flat5(1000, 1.000, 1.001, 0.999, 1.000),
          flat5(1300, 1.000, 1.002, 0.999, 1.001),
          flat5(1600, 1.001, 1.010, 1.001, 1.009),
          flat5(1900, 1.009, 1.012, 1.008, 1.010)]
    recs = [rec(1300, sl=1.0, tp=1.5)]   # SL 0.01 / TP 0.015 di harga
    a = ex_m1(recs, m5, m1_from_m5(m5))
    b = run_execution_replay(recs, m5, PROFILE, spread_points=17.0, slippage_points=0.0,
                             delay_bars=0, broker_meta=META)
    ta, tb = a["trades"][0], b["trades"][0]
    assert ta["entry_ts"] == tb["entry_ts"] == 1300
    assert ta["entry"] == tb["entry"]
    assert ta["exit_reason"] == tb["exit_reason"] and ta["exit"] == tb["exit"]
    assert ta["net_usd"] == tb["net_usd"]


def test_m1_identity_sell_and_spread_once():
    m5 = [flat5(1000, 2.000, 2.001, 1.999, 2.000),
          flat5(1300, 2.000, 2.002, 1.999, 2.001),
          flat5(1600, 2.001, 2.002, 1.990, 1.991),
          flat5(1900, 1.991, 1.992, 1.988, 1.990)]
    recs = [rec(1300, decision="SELL", bias="SELL_ONLY", sl=1.0, tp=1.5)]
    a = ex_m1(recs, m5, m1_from_m5(m5))
    b = run_execution_replay(recs, m5, PROFILE, spread_points=17.0, slippage_points=0.0,
                             delay_bars=0, broker_meta=META)
    ta, tb = a["trades"][0], b["trades"][0]
    assert ta["entry"] == tb["entry"]
    assert ta["net_usd"] == tb["net_usd"]
    assert ta["entry_side"] == "BID" and ta["exit_side"] == "ASK"


def test_m1_first_available_bar_skips_gap():
    # grid M1 dari bar M5 1300: 1300,1360,1420,1480,1540. Hole di 1420, sinyal
    # T=1370 → first AVAILABLE = 1480 (aturan disetujui owner 2026-09-09).
    m5 = [flat5(1000, 1.000, 1.001, 0.999, 1.000),
          flat5(1300, 1.000, 1.002, 0.999, 1.001),
          flat5(1600, 1.001, 1.010, 1.001, 1.009),
          flat5(1900, 1.009, 1.012, 1.008, 1.010)]
    m1 = m1_from_m5(m5)
    m1 = [b for b in m1 if b["time"] != 1420]  # hole tepat di menit entry
    a = ex_m1([rec(1370, sl=1.0, tp=1.5)], m5, m1)
    assert a["trades"][0]["entry_ts"] == 1480
    # fail-closed: tidak ada bar sama sekali >= T
    m1_empty = [b for b in m1 if b["time"] < 1370]
    c = ex_m1([rec(1370, sl=1.0, tp=1.5)], m5, m1_empty)
    assert c["trades"] == [] and any(r["reason"] == "no_m1_bar" for r in c["rejected_executions"])


# ── gate inside-bar ──────────────────────────────────────────────────────────

def test_inside_bar_gate_contracts():
    mother = flat5(1000, 1.00, 1.10, 0.90, 1.05)
    inside = flat5(1300, 1.02, 1.08, 0.95, 1.04)
    cfg_ok = {"now_ts": 1600, "inside_bar_enabled": True}
    ts, typ, stop = b5_inside_bar_signal([mother, inside], "BUY_ONLY", cfg_ok)
    assert (ts, typ, stop) == (1300, "BUY_STOP", 1.11)
    ts, typ, stop = b5_inside_bar_signal([mother, inside], "SELL_ONLY", cfg_ok)
    assert (ts, typ, stop) == (1300, "SELL_STOP", 0.89)
    # strict: equal-high bukan inside
    eq = flat5(1300, 1.02, 1.10, 0.95, 1.04)
    ts, why = b5_inside_bar_signal([mother, eq], "BUY_ONLY", cfg_ok)
    assert ts is None and why == "FAIL:none"
    # forming bar
    ts, why = b5_inside_bar_signal([mother, inside], "BUY_ONLY", {"now_ts": 1300, "inside_bar_enabled": True})
    assert ts is None and why == "FAIL:forming_bar"
    # default OFF
    ts, why = b5_inside_bar_signal([mother, inside], "BUY_ONLY", {"now_ts": 1600})
    assert ts is None and why == "DISABLED"


def test_b5_mode_inside_bar_sets_pending_in_record():
    # M5: mother 18800 → inside 19100; now 19700 (2 bar stale, valid).
    # M15 uptrend fresh → BUY_ONLY → pending BUY_STOP di mother.high+1 poin.
    m15 = up_m15_upto(19100)
    m5 = [flat5(18800, 1.00, 1.10, 0.90, 1.05, 10),
          flat5(19100, 1.02, 1.08, 0.95, 1.04, 8)]
    profile = {"profile_id": "MICRO_V2", "layer_a": {"b3_enabled": True, "b4_enabled": True,
                                                     "b5_enabled": True},
               "volume_gate": {"enabled": False}, "scoring": {"mode": "off"},
               "location": {"kind": "ema_pullback", "ema_pullback_distance_atr": 1.0},
               "risk": {"sl_atr_mult": 1.25, "tp_atr_mult": 1.5, "cooldown_minutes": 5,
                        "max_stop_points": 350,
                        "min_stop_params": {"spread_mult": 3, "stops_level_poin": 0, "buffer_poin": 10}},
               "session_windows_utc": [[0, 24]],
               "news": {"policy": "FAIL_CLOSED", "window_minutes": 30,
                        "staleness_hours": 4, "impacts": ["high"]}}
    cfg = {"now_ts": 19700, "inside_bar_enabled": True, "b5_mode": "inside_bar",
           "layer_a": profile["layer_a"], "min_bars_m15_warmup": 20}
    # tanpa M15 → Layer A invalid → pending None (fail-closed)
    diag = evaluate_all({"m5": m5, "m15": []}, profile, cfg, {})
    assert diag["pending_order"] is None
    diag = evaluate_all({"m5": m5, "m15": m15}, profile, cfg, {})
    assert diag["bias"] == "BUY_ONLY"
    assert diag["pending_order"] is not None
    assert diag["pending_order"]["order_type"] == "BUY_STOP"
    assert diag["pending_order"]["placement_ts"] == 19100
    assert diag["pending_order"]["stop_price"] == pytest.approx(1.11)
    assert diag["pending_order"]["expiry_bars"] == 12
    assert diag["pending_order"]["trigger_tier"] == 0.7
    assert diag["trigger"]["pattern"] == "inside_bar"


# ── pending STOP engine ─────────────────────────────────────────────────────

def test_pending_trigger_fill_and_exit_scan():
    # Place di T=1000 (expiry_ts = 1000+12×60 = 1720, order live mulai 1060).
    # Bar M1 1060 di-override high=1.115 → trigger di record T=1300
    # (window [cursor 1060, 1600) ∧ ≤1720). Fill = stop 1.11 (BUY di ASK).
    # SL = 1.11−0.01 = 1.10; low bar M5 1300 = 1.05 menyentuh:
    #   - default (grid M5, mode paritas): exit_ts = 1300+300 = 1600
    #   - scan_m1_exits=True (resolusi M1, mode produksi Arm D): bar M1 1300
    #     → exit_ts = 1360. Harga exit sama (SL), hanya resolusi waktu.
    # Mother bar dibuat tanpa zona SL (low 1.105 > 1.10) agar bar trigger
    # tidak sekaligus kena SL — atribusi bersih trigger→fill→exit.
    m5 = [flat5(1000, 1.105, 1.12, 1.105, 1.11),
          flat5(1300, 1.08, 1.09, 1.05, 1.06),
          flat5(1600, 1.06, 1.07, 1.03, 1.04),
          flat5(1900, 1.04, 1.05, 1.00, 1.01)]
    m1 = m1_from_m5(m5)
    for b in m1:
        if b["time"] == 1060:
            b["high"] = 1.115   # M5 bar 1000 high 1.12 ≥ 1.115 (konsisten)
    po = {"placement_ts": 1000, "order_type": "BUY_STOP", "stop_price": 1.11,
          "expiry_bars": 12, "trigger_tier": 0.7}
    recs = [dict(rec(1000, sl=1.0, tp=5.0), order_mode="PENDING_STOP", pending_order=po),
            rec(1300, decision="WAIT"),
            rec(1600, decision="WAIT")]
    ex = ex_m1(recs, m5, m1)
    assert ex["pending_stats"]["placed"] == 1 and ex["pending_stats"]["triggered"] == 1
    assert ex["pending_stats"]["expired"] == 0
    t = ex["trades"][0]
    assert t["entry_kind"] == "PENDING_STOP_M1" and t["entry_ts"] == 1060
    assert t["entry"] == pytest.approx(1.11)          # BUY fill di ASK = stop
    assert t["exit_reason"] == "SL" and t["exit"] == pytest.approx(1.10)
    assert t["exit_ts"] == 1600                        # grid M5 (paritas)
    assert t["entry_side"] == "ASK" and t["exit_side"] == "BID"
    # gross = (1.10−1.11)/0.01 × pv1.0 × lot0.02 = −0.02
    # cost = (17pt spread × pv + $1 comm) × 0.02 lot = 0.36
    assert t["gross_usd"] == pytest.approx(-0.02)
    assert t["cost_usd"] == pytest.approx(0.36)
    assert t["net_usd"] == pytest.approx(-0.38)
    # resolusi M1 (produksi): exit lebih cepat terdeteksi, harga & PnL identik
    ex1 = ex_m1(recs, m5, m1, scan_m1_exits=True)
    t1 = ex1["trades"][0]
    assert t1["exit_ts"] == 1360 and t1["exit"] == pytest.approx(1.10)
    assert t1["net_usd"] == pytest.approx(t["net_usd"])


def test_pending_expiry_12_bars():
    # expiry_ts = 1000 + 12×60 = 1720. Record T=1300 masih dalam masa order
    # (tidak expired); record T=1800 > 1720 tanpa tembusan → expired tercatat.
    m5 = [flat5(1000, 1.00, 1.10, 0.90, 1.05),
          flat5(4000, 1.00, 1.10, 0.90, 1.05)]
    m1 = m1_from_m5(m5)
    po = {"placement_ts": 1000, "order_type": "BUY_STOP", "stop_price": 1.11,
          "expiry_bars": 12, "trigger_tier": 0.7}
    recs = [dict(rec(1000), order_mode="PENDING_STOP", pending_order=po),
            rec(1800, decision="WAIT")]
    ex = ex_m1(recs, m5, m1)
    assert ex["pending_stats"]["expired"] == 1 and ex["trades"] == []
    assert any(r["reason"] == "pending_expired" for r in ex["rejected_executions"])
    # order MASIH hidup pada record dalam masa berlaku (1300 < 1720):
    recs_alive = [dict(rec(1000), order_mode="PENDING_STOP", pending_order=po),
                  rec(1300, decision="WAIT")]
    ex_alive = ex_m1(recs_alive, m5, m1)
    assert ex_alive["pending_stats"]["expired"] == 1   # expired di EOD, bukan di 1300
    assert all(r["reason"] != "pending_expired" for r in ex_alive["rejected_executions"])


def test_pending_scan_starts_after_placement_bar():
    # Bar placement 1000 high 1.10 ≥ stop 1.05 — TAPI order belum live di bar
    # placement (cursor = 1060). Trigger pertama yang sah = 1060. Kalau engine
    # salah memindai bar placement, entry_ts = 1000; kontrak: entry_ts = 1060.
    m5 = [flat5(1000, 1.00, 1.10, 0.90, 1.05),
          flat5(4000, 1.00, 1.10, 0.90, 1.05)]
    m1 = m1_from_m5(m5)
    po = {"placement_ts": 1000, "order_type": "BUY_STOP", "stop_price": 1.05,
          "expiry_bars": 12, "trigger_tier": 0.7}
    recs = [dict(rec(1000, sl=3.0, tp=9.0), order_mode="PENDING_STOP", pending_order=po),
            rec(1300, decision="WAIT")]
    ex = ex_m1(recs, m5, m1)
    trig = [t for t in ex["trades"] if t["entry_kind"] == "PENDING_STOP_M1"]
    assert len(trig) == 1 and trig[0]["entry_ts"] == 1060   # > placement, bukan 1000
    assert trig[0]["entry"] == pytest.approx(1.05)
    assert all(t["entry_ts"] > 1000 for t in ex["trades"])


def test_pending_cancel_on_market_entry_and_regime_flip():
    m5 = [flat5(1000, 1.00, 1.10, 0.90, 1.05),
          flat5(1300, 1.00, 1.10, 0.90, 1.05)]
    m1 = m1_from_m5(m5)
    po = {"placement_ts": 1000, "order_type": "BUY_STOP", "stop_price": 1.11,
          "expiry_bars": 12, "trigger_tier": 0.7}
    recs = [
        dict(rec(1000), order_mode="PENDING_STOP", pending_order=po),
        rec(1300),  # market entry → pending wajib cancel
    ]
    ex = ex_m1(recs, m5, m1)
    assert ex["pending_stats"]["cancelled"] == 1
    assert ex["pending_stats"]["triggered"] == 0
    assert ex["trades"][0]["entry_kind"] == "MARKET_M1"
    # regime flip via record SELL (bias SELL_ONLY): pending BUY cancel, market SELL jalan
    recs2 = [
        dict(rec(1000), order_mode="PENDING_STOP", pending_order=po),
        rec(1300, decision="SELL", bias="SELL_ONLY"),
    ]
    ex2 = ex_m1(recs2, m5, m1)
    assert ex2["pending_stats"]["cancelled"] == 1
    assert ex2["trades"][0]["direction"] == "SELL" and ex2["trades"][0]["entry_kind"] == "MARKET_M1"


# ── S0.3 — pending STOP di ShadowGateway (mirror engine) ────────────────────

from strategy_v2.execution import (ExecutionStateMachine, ShadowGateway,
                                   decision_to_intent)


def test_gateway_pending_mirrors_engine_fill():
    # Engine (kebenaran): place T=1000 stop 1.11 exp 12 → fill 1060 @1.11.
    # Gateway HARUS menghasilkan fill_ts/fill_price identik di grid M1 sama.
    m5 = [flat5(1000, 1.105, 1.12, 1.105, 1.11),
          flat5(1300, 1.08, 1.09, 1.05, 1.06),
          flat5(1600, 1.06, 1.07, 1.03, 1.04),
          flat5(1900, 1.04, 1.05, 1.00, 1.01)]
    m1 = m1_from_m5(m5)
    for b in m1:
        if b["time"] == 1060:
            b["high"] = 1.115
    recd = dict(rec(1000, sl=1.0, tp=5.0), order_mode="PENDING_STOP",
                pending_order={"placement_ts": 1000, "order_type": "BUY_STOP",
                               "stop_price": 1.11, "expiry_bars": 12,
                               "trigger_tier": 0.7})
    recd["decision"] = "BUY"
    intent = decision_to_intent(recd, "MICRO_V2")
    gw = ShadowGateway(m5)
    sm = ExecutionStateMachine(intent.intent_id)
    sm.transition("INTENT_VALIDATED"); sm.transition("CSK_CHECKED")
    sm.transition("SUBMITTED"); sm.transition("ACKNOWLEDGED")
    order = gw.submit_pending(intent, "BUY_STOP", 1.11, expiry_bars=12)
    assert order.expiry_ts == 1000 + 12 * 60
    assert order.trigger_scan_from == 1060   # bar placement TIDAK trigger
    res = gw.resolve_pending(order.order_id, m1)
    assert res.outcome == "FILLED"
    assert res.fill_ts == 1060 and res.fill_price == pytest.approx(1.11)
    sm.transition("FILLED"); sm.transition("CLOSED")
    assert sm.is_terminal()
    # resting table berselah setelah fill
    assert order.order_id not in gw.pending_orders


def test_gateway_pending_open_then_expire_aborted():
    m5 = [flat5(1000, 1.00, 1.05, 0.90, 1.00),
          flat5(4000, 1.00, 1.05, 0.90, 1.00)]   # tidak pernah tembus 1.11
    m1 = m1_from_m5(m5)
    recd = dict(rec(1000), order_mode="PENDING_STOP",
                pending_order={"placement_ts": 1000, "order_type": "BUY_STOP",
                               "stop_price": 1.11, "expiry_bars": 12,
                               "trigger_tier": 0.7})
    recd["decision"] = "BUY"
    intent = decision_to_intent(recd, "MICRO_V2")
    gw = ShadowGateway(m5)
    order = gw.submit_pending(intent, "BUY_STOP", 1.11, expiry_bars=12)
    res = gw.resolve_pending(order.order_id, m1)
    assert res.outcome == "OPEN"           # masih resting
    assert order.order_id in gw.pending_orders
    # expired eksplisit (now > expiry) → CANCELLED:pending_expired; SM → ABORTED
    res2 = gw.expire_pending(order.order_id, now_ts=1000 + 13 * 60)
    assert res2.outcome == "CANCELLED" and res2.reason == "pending_expired"
    sm = ExecutionStateMachine(intent.intent_id)
    for st in ("INTENT_VALIDATED", "CSK_CHECKED", "SUBMITTED", "ACKNOWLEDGED"):
        sm.transition(st)
    sm.transition("ABORTED")
    assert sm.is_terminal()


def test_gateway_pending_fail_closed():
    recd = dict(rec(1000), order_mode="PENDING_STOP",
                pending_order={"placement_ts": 1000, "order_type": "BUY_STOP",
                               "stop_price": 1.11, "expiry_bars": 12,
                               "trigger_tier": 0.7})
    recd["decision"] = "BUY"
    intent = decision_to_intent(recd, "MICRO_V2")
    gw = ShadowGateway([flat5(1000, 1.00, 1.05, 0.90, 1.00)])
    with pytest.raises(ValueError):        # arah/tipe mismatch
        gw.submit_pending(intent, "SELL_STOP", 1.11)
    with pytest.raises(ValueError):        # tipe bukan STOP
        gw.submit_pending(intent, "BUY_LIMIT", 1.11)
    with pytest.raises(ValueError):        # stop non-positif
        gw.submit_pending(intent, "BUY_STOP", 0.0)
    gw2 = ShadowGateway([flat5(1000, 1.00, 1.05, 0.90, 1.00)], kill_switch_active=True)
    with pytest.raises(RuntimeError):      # kill switch → fail-closed
        gw2.submit_pending(intent, "BUY_STOP", 1.11)


# ── B4 threading (Arm A) ────────────────────────────────────────────────────

def _profile_with_loc(threshold: float) -> dict:
    return {"profile_id": "MICRO_V2",
            "layer_a": {"b3_enabled": True, "b4_enabled": True, "b5_enabled": True},
            "volume_gate": {"enabled": False}, "scoring": {"mode": "off"},
            "location": {"kind": "ema_pullback", "ema_pullback_distance_atr": threshold},
            "risk": {"sl_atr_mult": 1.25, "tp_atr_mult": 1.5, "cooldown_minutes": 5,
                     "max_stop_points": 350,
                     "min_stop_params": {"spread_mult": 3, "stops_level_poin": 0, "buffer_poin": 10}},
            "session_windows_utc": [[0, 24]],
            "news": {"policy": "FAIL_CLOSED", "window_minutes": 30,
                     "staleness_hours": 4, "impacts": ["high"]}}


def test_b4_threshold_threaded_from_profile():
    # M5 flat ~1.01 (harga nempel EMA) → dist_atr kecil (≈0.1×ATR).
    # Profil 0.75 → PASS; profil 0.05 → FAIL:far. Data sama, hanya ambang beda
    # → membuktikan ambang benar-benar di-thread dari profil (Arm A 0,75).
    # M5 berakhir 27000 (2 bar stale thd now 27600) — tanpa bar masa depan.
    m5 = [flat5(20100 + k * 300, 1.01, 1.0105, 1.0095, 1.01, 5) for k in range(24)]
    m5[-1]["close"] = 1.0101
    m15 = up_m15_upto(26700)   # fresh terhadap now 27600, uptrend → BUY_ONLY
    cfg = {"now_ts": 27600, "layer_a": {"b3_enabled": True, "b4_enabled": True,
                                        "b5_enabled": True},
           "min_bars_m15_warmup": 20}
    diag = evaluate_all({"m5": m5, "m15": m15}, _profile_with_loc(0.75), cfg, {})
    assert diag["bias"] == "BUY_ONLY"
    b4 = diag["all_gate_results"]["b4_location"]
    assert b4.startswith("PASS:") and "dist_atr=" in b4
    dist = float(b4.split("dist_atr=")[1].split("|")[0])
    assert dist <= 0.75 and dist > 0.05   # zona yang membedakan kedua profil
    diag_tight = evaluate_all({"m5": m5, "m15": m15}, _profile_with_loc(0.05), cfg, {})
    assert diag_tight["all_gate_results"]["b4_location"] == "FAIL:far"
