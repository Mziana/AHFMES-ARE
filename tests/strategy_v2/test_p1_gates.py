"""P1 pure gate engine — basic semantics tests (full invariant suite = Paket 4)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import gates, registry, zones as Z


def make_m5(n, start=1788739200, base=4400.0, vol=100):
    return [{"time": start + i * 300, "open": base, "high": base + 1, "low": base - 1,
             "close": base + 0.5, "volume": vol} for i in range(n)]


def make_m15(n, start=1788739200, base=4400.0, drift=0.05):
    return [{"time": start + i * 900, "open": base, "high": base + 1, "low": base - 1,
             "close": base + drift * i, "volume": 400} for i in range(n)]


CFG_BASE = {"calendar": {"status": "empty", "events": []}}


def test_b1_news_four_codes():
    policy = registry.load_profile("MICRO")["news"]
    now = 1788799380
    ev = {"ts": now, "impact": "high", "currency": "USD"}
    assert gates.b1_news(now, {"status": "ok", "fetched_at": now - 600, "events": [dict(ev)]}, policy) == "NEWS_EVENT_ACTIVE"
    assert gates.b1_news(now, {"status": "ok", "fetched_at": now - 600, "events": [{**ev, "ts": now - 3600}]}, policy) == "PASS"
    assert gates.b1_news(now, {"status": "down", "events": []}, policy) == "NEWS_PROVIDER_DOWN"
    assert gates.b1_news(now, {"status": "ok", "fetched_at": now - 5 * 3600, "events": [dict(ev)]}, policy) == "NEWS_DATA_STALE"
    assert gates.b1_news(now, {"status": "empty", "events": []}, policy) == "NEWS_CALENDAR_UNAVAILABLE"
    # event non-USD / impact lain tidak memicu
    assert gates.b1_news(now, {"status": "ok", "fetched_at": now - 600,
                               "events": [{"ts": now, "impact": "high", "currency": "EUR"}]}, policy) == "PASS"


def test_b3_regime_thresholds():
    cfg = {**CFG_BASE, "rsi_bias_threshold": 50}
    up = make_m15(300, drift=0.2)     # close naik terus → RSI tinggi, close>EMA
    assert gates.b3_regime(up, cfg) == "PASS:BUY_ONLY"
    down = make_m15(300, drift=-0.2)
    assert gates.b3_regime(down, cfg) == "PASS:SELL_ONLY"
    flat = make_m15(300, drift=0.0)
    assert gates.b3_regime(flat, cfg) == "FAIL:NO_TRADE"
    assert gates.b3_regime(make_m15(20), cfg) == "FAIL:NO_TRADE"  # warmup kurang


def test_b6_volume_exclude_self_and_guards():
    cfg = {"volume_gate_enabled": True, "vol_ratio": 1.2, "vol_baseline_bars": 5}
    bars = make_m5(10, vol=100)
    bars[-1]["volume"] = 130  # > 1.2 × 100
    assert gates.b6_volume(bars, cfg) == "PASS"
    bars[-1]["volume"] = 110  # < 1.2 × 100
    assert gates.b6_volume(bars, cfg) == "FAIL:ratio"
    # baseline zero-volume → FAIL (bukan PASS)
    for b in bars[-6:-1]:
        b["volume"] = 0
    assert gates.b6_volume(bars, cfg) == "FAIL:baseline_invalid"
    # missing volume → FAIL
    for b in bars:
        b["volume"] = None
    assert gates.b6_volume(bars, cfg) == "FAIL:baseline_invalid"
    # disabled → DISABLED
    assert gates.b6_volume(bars, {"volume_gate_enabled": False}) == "DISABLED"


def test_layer_a_reasons_in_order():
    cfg = {**CFG_BASE, "now_ts": 1788739200 + 300 * 50, "layer_a": {}}
    bars = make_m5(50)
    assert gates.layer_a_data_integrity(bars, None, cfg) == "DATA_VALID"
    # duplicate ts
    bad = make_m5(50)
    bad[10]["time"] = bad[9]["time"]
    assert gates.layer_a_data_integrity(bad, None, cfg) == "DATA_INVALID:duplicate_ts"
    # gap
    bad = make_m5(50)
    bad[10]["time"] += 300
    assert gates.layer_a_data_integrity(bad, None, cfg) == "DATA_INVALID:missing_bar"
    # ohlc
    bad = make_m5(50)
    bad[10]["high"] = bad[10]["low"] - 1
    assert gates.layer_a_data_integrity(bad, None, cfg) == "DATA_INVALID:ohlc"
    # nan
    bad = make_m5(50)
    bad[10]["close"] = float("nan")
    assert gates.layer_a_data_integrity(bad, None, cfg) == "DATA_INVALID:nan"
    # stale
    cfg2 = {**CFG_BASE, "now_ts": 1788739200 + 300 * 500, "layer_a": {}}
    assert gates.layer_a_data_integrity(make_m5(50), None, cfg2) == "DATA_INVALID:stale"
    # spread extreme
    assert gates.layer_a_data_integrity(make_m5(50), {"spread_points": 500}, cfg) == "DATA_INVALID:spread_extreme"


def test_b7_risk_order_and_bounds():
    profile = registry.load_profile("MICRO")
    # cap
    assert gates.b7_risk({"trades_today": 20, "now_ts": 0}, profile, {"skip": False}) == "FAIL:cap"
    # cooldown
    assert gates.b7_risk({"trades_today": 1, "last_entry_ts": 100, "now_ts": 100 + 60}, profile, {"skip": False}) == "FAIL:cooldown"
    assert gates.b7_risk({"trades_today": 1, "last_entry_ts": 100, "now_ts": 100 + 301}, profile, {"skip": False}) == "PASS"
    # stop bounds skip
    assert gates.b7_risk({"trades_today": 0, "now_ts": 0}, profile, {"skip": True}) == "FAIL:stop_bounds"


def test_compute_sl_tp_min_stop_and_skip():
    profile = registry.load_profile("MICRO")
    r = gates.compute_sl_tp(profile, atr_points=100.0, spread_points=20.0)
    # SL raw = 1.25 × 100 = 125 poin; floor = 3×20+0+10 = 70 → SL = 125
    assert r["sl_points"] == 125.0 and not r["skip"]
    # spread ekstrem → floor > cap 250 → skip
    r = gates.compute_sl_tp(profile, atr_points=100.0, spread_points=1000.0)
    assert r["skip"] is True


def test_zones_pure_and_confirmed():
    bars = make_m15(300)
    bars[100]["high"] = 9999.0  # satu puncak jelas
    bars[200]["low"] = 1000.0
    z1 = Z.build_zones(bars[:250])
    z2 = Z.build_zones(bars[:250])
    assert z1 == z2  # pure
    highs = [z["level"] for z in z1["resistances"]]
    assert any(abs(h - 9999.0) < 5 for h in highs)
    lows = [z["level"] for z in z1["supports"]]
    assert any(abs(l - 1000.0) < 5 for l in lows)
    # window 200: swing di bar 100 tidak masuk bila di luar window
    z3 = Z.build_zones(bars[100:250])
    assert all(z["level"] <= 300 + 500 for z in z3["resistances"])


def test_evaluate_all_data_invalid_disables_layer_b():
    profile = registry.load_profile("MICRO")
    cfg = {"now_ts": 1788739200 + 300 * 60, "calendar": {"status": "empty", "events": []}, "layer_a": {}}
    bars = make_m5(60)
    bars[5]["high"] = -1  # ohlc invalid
    d = gates.evaluate_all({"m5": bars, "m15": make_m15(300)}, profile, cfg, {})
    assert d["layer_a"].startswith("DATA_INVALID")
    assert d["layer_b_ran"] is False
    assert all(v == "DISABLED" for v in d["all_gate_results"].values())
    fv, dec = gates.decide(d)
    assert dec == "WAIT"


def test_decide_first_veto_order_and_diagnostic_neutrality():
    profile = registry.load_profile("MICRO")
    cfg = {"now_ts": 1788739200 + 300 * 60, "calendar": {"status": "empty", "events": []}, "layer_a": {}}
    d = gates.evaluate_all({"m5": make_m5(60), "m15": make_m15(300)}, profile, cfg, {})
    results_before = dict(d["all_gate_results"])
    fv, dec = gates.decide(d)
    assert d["all_gate_results"] == results_before  # decide tidak mengubah diagnostic
    assert fv is None or fv.startswith("B")
    assert dec in ("BUY", "SELL", "WAIT")
