"""C0 — kontrak Cognitive Layer scorer (H-SCORE-01) + parity wiring.

Di-guard di sini (desain v2.1 counter-proposal, disepakati owner & reviewer):
- 8 komponen deterministik 0..1 + respons arah
- guards dua tingkat: input inti degenerate -> skor None (fail-closed);
  volume baseline invalid -> 0.0 (tanpa kredit)
- weight-per-profile: MICRO & SCALP masing-masing sum=100, MICRO != SCALP
- parity: mode-off == score-on(threshold null) di tingkat keputusan
- eksekusi parity ketat: filter sinyal lolos BQ -> run_execution_replay hasil
  trades list IDENTIK dengan eksekusi records lengkap (BQ veto di decision
  stage; TIDAK ada filter terpisah di execution)
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import gates, registry, scoring as S
from strategy_v2.replay import run_decision_replay, run_execution_replay


def _m5(n=80, start=1788739200, base=100.0, drift=0.05, vol=1000.0, spike=None):
    out = [{"time": start + i * 300, "open": base + drift * i,
            "high": base + drift * i + 1.0, "low": base + drift * i - 1.0,
            "close": base + drift * i + 0.5, "volume": vol}
           for i in range(n)]
    if spike is not None:
        out[spike] = dict(out[spike], high=out[spike]["close"] + 8.0,
                          low=out[spike]["close"] - 8.0)
    return out


PROFILE = registry.load_profile("MICRO")
PROFILE_SCALP = registry.load_profile("SCALP")
H = registry.hypothesis(registry.load_hypothesis_registry(), "H-SCORE-01")["value"]
W = PROFILE["scoring"]["weights"]


# ── weight-per-profile contract ──────────────────────────────────────────────

def test_weights_sum_100_and_micro_differs_scalp():
    components = {"trend_alignment", "location_quality", "structure",
                  "volume_confirmation", "cost_quality", "trigger_quality",
                  "momentum_quality", "volatility_quality"}
    wm, ws = PROFILE["scoring"]["weights"], PROFILE_SCALP["scoring"]["weights"]
    assert set(wm) == set(ws) == components
    assert sum(wm.values()) == 100 and sum(ws.values()) == 100
    assert wm != ws


# ── komponen: bounds + respons arah ──────────────────────────────────────────

def test_trend_alignment_strength_and_bounds():
    assert S.trend_alignment(None, 5.0) is None
    assert S.trend_alignment(0.0, 5.0) == 0.0
    assert S.trend_alignment(-3.0, 5.0) == 0.6
    assert S.trend_alignment(9.0, 5.0) == 1.0          # capped
    assert S.trend_alignment(-9.0, 5.0) == 1.0         # arah tidak masuk (abs)


def test_location_quality_monotonic_decreasing_with_distance():
    assert S.location_quality(100.0, 100.0, 2.0) == 1.0    # tepat di EMA
    near = S.location_quality(100.4, 100.0, 2.0)           # 0.2 ATR
    far = S.location_quality(103.0, 100.0, 2.0)            # 1.5 ATR
    assert near > far >= 0.0
    assert far == 0.0                                       # > 1.0 ATR -> nol (dulu B4 FAIL:far)
    assert S.location_quality(100.0, 100.0, 0.0) == 0.0     # L2 backstop


def test_volume_confirmation_mapping_and_fail_closed_baseline():
    assert S.volume_confirmation(1.0, True) == pytest.approx(1 / 3)
    assert S.volume_confirmation(0.5, True) == 0.0          # di bawah 0.8
    assert S.volume_confirmation(2.0, True) == 1.0          # clamped
    assert S.volume_confirmation(1.5, False) == 0.0         # baseline invalid -> 0.0 (tanpa kredit)
    assert S.volume_confirmation(None, True) == 0.0


def test_cost_quality_monotonic_and_backstop():
    assert S.cost_quality(17.0, 250.0) == pytest.approx(1 - (34 / 250) / 0.25)
    assert S.cost_quality(17.0, 100.0) == 0.0               # R=0.34 > 0.25
    assert S.cost_quality(0.0, 250.0) == 1.0
    assert S.cost_quality(17.0, 0.0) == 0.0                 # L2 backstop
    assert S.cost_quality(None, 250.0) == 0.0


def test_rsi_graded_buy_and_sell_explicit():
    band = (45, 55)
    # BUY: >55 -> 1.0, [45,55] -> 0.5, <45 -> 0.0
    assert S.rsi_graded(60, 1, band) == 1.0
    assert S.rsi_graded(50, 1, band) == 0.5
    assert S.rsi_graded(40, 1, band) == 0.0
    # SELL dibalik eksplisit: <45 -> 1.0, [45,55] -> 0.5, >55 -> 0.0
    assert S.rsi_graded(40, -1, band) == 1.0
    assert S.rsi_graded(50, -1, band) == 0.5
    assert S.rsi_graded(60, -1, band) == 0.0
    assert S.rsi_graded(None, 1, band) == 0.0


def test_momentum_quality_direction_response():
    band = tuple(H["rsi_zone_band"])
    up = S.momentum_quality(close=105.0, ema9=104.0, ema21=103.0, rsi=60, d_rsi=5,
                            bias_dir=1, rsi_band=band)
    dn = S.momentum_quality(close=105.0, ema9=104.0, ema21=103.0, rsi=60, d_rsi=5,
                            bias_dir=-1, rsi_band=band)
    assert up == 1.0          # semua searah BUY
    assert dn == 0.0          # semua melawan SELL
    assert up != dn


def test_volatility_quality_band_edges():
    band = tuple(H["atr_band_pts"])
    assert S.volatility_quality(300.0, band) == 1.0
    assert S.volatility_quality(200.0, band) == 1.0 and S.volatility_quality(500.0, band) == 1.0
    below, above = S.volatility_quality(100.0, band), S.volatility_quality(700.0, band)
    assert below == pytest.approx(0.8)                      # 100 pts di bawah: -0.2
    assert above == pytest.approx(0.6)                      # 200 pts di atas: -0.4
    assert S.volatility_quality(0.0, band) == 0.0           # L2 backstop


# ── guards dua tingkat ───────────────────────────────────────────────────────

def test_bias_dir_fail_closed():
    with pytest.raises(ValueError):
        S.bias_dir_from("NO_TRADE")
    with pytest.raises(ValueError):
        S.bias_dir_from(None)
    with pytest.raises(ValueError):
        S.bias_dir_from("ANYTHING_ELSE")
    assert S.bias_dir_from("BUY_ONLY") == 1 and S.bias_dir_from("SELL_ONLY") == -1


def test_l1_fail_closed_skip_and_empty_bars():
    m5 = _m5()
    sl_ok = gates.compute_sl_tp(PROFILE, 200.0, 17.0)
    assert sl_ok["skip"] is False and sl_ok["sl_points"] == 250.0
    # sl_calc skip (SL > cap) -> None
    assert S.evaluate_quality(m5, None, "BUY_ONLY", 3.0, 17.0,
                              dict(sl_ok, skip=True), "hammer", W, H) is None
    # bar kosong -> None
    assert S.evaluate_quality([], None, "BUY_ONLY", 3.0, 17.0, sl_ok, "hammer", W, H) is None
    # bias invalid -> ValueError (bukan skor palsu)
    with pytest.raises(ValueError):
        S.evaluate_quality(m5, None, "NO_TRADE", 3.0, 17.0, sl_ok, "hammer", W, H)


def test_volume_baseline_invalid_gives_zero_component_and_flag():
    m5 = _m5()
    m5[-3]["volume"] = 0.0                       # baseline rusak
    sl_ok = gates.compute_sl_tp(PROFILE, 200.0, 17.0)
    q = S.evaluate_quality(m5, None, "BUY_ONLY", 3.0, 17.0, sl_ok, "hammer", W, H)
    assert q is not None                          # L1 tidak jatuh — komponen 0.0
    assert q["breakdown"]["volume_confirmation"] == 0.0
    assert q["inputs"]["volume_baseline_valid"] is False


# ── risk adjustments ─────────────────────────────────────────────────────────

def test_risk_adjustments_three_rules_and_skip_guard():
    sl_ok = {"sl_points": 250.0, "tp_points": 300.0, "skip": False}
    bar = {"high": 100.5, "low": 100.0, "close": 100.2}
    adj_cfg = {**H, "bias": "BUY_ONLY"}
    # rule 1: SL < 1.5*spread (250 < 25.5? tidak -> tidak aktif di angka ini;
    # pakai SL kecil eksplisit)
    adjs, _ = S.risk_adjustments({"sl_points": 20.0, "skip": False}, 17.0,
                                 bar, 300.0, None, adj_cfg)
    assert {"rule": "sl_lt_1_5_spread", "delta": -10} in adjs
    # rule 2: range bar > 2*ATR (650 pts > 600)
    bar_lebar = {"high": 104.5, "low": 98.0, "close": 100.2}
    adjs, _ = S.risk_adjustments(sl_ok, 17.0, bar_lebar, 300.0, None, adj_cfg)
    assert {"rule": "range_gt_2_atr", "delta": -5} in adjs
    # rule 2 tidak aktif saat range kecil (30 pts < 600)
    bar_kecil = {"high": 100.3, "low": 100.0, "close": 100.2}
    adjs, _ = S.risk_adjustments(sl_ok, 17.0, bar_kecil, 300.0, None, adj_cfg)
    assert all(a["rule"] != "range_gt_2_atr" for a in adjs)
    # guard: skip -> adjustments kosong + alasan terlog
    adjs, note = S.risk_adjustments({"sl_points": 250.0, "skip": True}, 17.0,
                                    bar, 300.0, None, adj_cfg)
    assert adjs == [] and "skip" in note


# ── tier + threshold ─────────────────────────────────────────────────────────

def test_tier_assignment_from_threshold():
    m5 = _m5()
    sl_ok = gates.compute_sl_tp(PROFILE, 200.0, 17.0)
    q0 = S.evaluate_quality(m5, None, "BUY_ONLY", 3.0, 17.0, sl_ok, "hammer", W, H)
    fin = q0["final_score"]
    q_lo = S.evaluate_quality(m5, None, "BUY_ONLY", 3.0, 17.0, sl_ok, "hammer", W,
                              {**H, "threshold": fin - 1.0})
    q_hi = S.evaluate_quality(m5, None, "BUY_ONLY", 3.0, 17.0, sl_ok, "hammer", W,
                              {**H, "threshold": fin + 1.0})
    assert q_lo["final_score"] == q_hi["final_score"]   # skor tak tergantung threshold
    assert q_lo["tier"] == "CANDIDATE" and q_hi["tier"] == "REJECT"
    q_strong = S.evaluate_quality(m5, None, "BUY_ONLY", 3.0, 17.0, sl_ok, "hammer", W,
                                  {**H, "threshold": fin - 11.0})
    assert q_strong["tier"] == "STRONG"
    h99 = {**H, "threshold": None}
    assert S.evaluate_quality(m5, None, "BUY_ONLY", 3.0, 17.0, sl_ok, "hammer", W, h99)["tier"] == "UNRANKED"


# ── parity wiring (data nyata, sesi pertama dataset terkunci P3) ─────────────

P3 = Path("data/research/p3")


def _first_session():
    m5 = json.loads((P3 / "dataset_m5.json").read_text(encoding="utf-8"))["candles"]
    m15 = json.loads((P3 / "dataset_m15.json").read_text(encoding="utf-8"))["candles"]
    sess = [m5[0]]
    for b in m5[1:]:
        if int(b["time"]) - int(sess[-1]["time"]) >= 3600:
            break
        sess.append(b)
    return sess, m15


def _run(profile, cfg_extra=None, disable=("b1_news", "b4_location")):
    reg = registry.load_hypothesis_registry()
    cfg = {"config_hash": "c" * 64, "dataset_hash": "d" * 64, "balance": 1136.65,
           "risk_percent": 2.0, "spread_points": 17.0}
    sess, m15 = _first_session()
    return run_decision_replay(sess, m15, profile, reg, None, cfg, disable_gates=disable), sess


def test_parity_mode_off_vs_score_on_null_threshold():
    off, _ = _run(registry.load_profile("MICRO"))
    prof = dict(registry.load_profile("MICRO"))
    # threshold NULL eksplisit — kontrak yang dites adalah mode-on tanpa veto;
    # kontrak file kini membawa T* C1 (60.1) dan TIDAK boleh bocor ke sini.
    prof["scoring"] = dict(prof["scoring"], mode="score",
                           thresholds={"candidate": None, "strong": None, "premium": None})
    on, _ = _run(prof)
    assert len(off) == len(on)
    for a, b in zip(off, on):
        assert a["decision"] == b["decision"]
        assert a["first_veto_reason"] == b["first_veto_reason"]
        # diagnostic BQ berbeda (DISABLED vs PASS) tapi operational identik
        assert a["all_gate_results"]["b8_quality"] == "DISABLED"
        assert b["all_gate_results"]["b8_quality"] in ("PASS", "DISABLED")


def test_execution_parity_strict_bq_veto_at_decision_stage():
    """BQ veto (score_low) terjadi di decision stage; execution TIDAK butuh
    filter terpisah: eksekusi records lengkap == eksekusi records terfilter."""
    prof = dict(registry.load_profile("MICRO"))
    prof["scoring"] = dict(prof["scoring"], mode="score",
                           thresholds={"candidate": 50, "strong": 60, "premium": 70})
    records, sess = _run(prof)
    bq_low = [r for r in records if r["all_gate_results"]["b8_quality"] == "FAIL:score_low"]
    assert len(bq_low) >= 1, "fixture harus men-exercise BQ veto (threshold 50)"
    for r in bq_low:
        assert r["decision"] == "WAIT" and r["first_veto_reason"] == "BQ:FAIL:score_low"
    signals = [r for r in records
               if r["decision"] in ("BUY", "SELL") and r["first_veto_reason"] is None]
    assert len(signals) >= 1

    ex_full = run_execution_replay(records, sess, prof, spread_points=17.0,
                                   slippage_points=0.0, delay_bars=0)
    ex_filt = run_execution_replay(signals, sess, prof, spread_points=17.0,
                                   slippage_points=0.0, delay_bars=0)
    key = lambda ts: [(t["entry_ts"], t["direction"], t["lot"], t["net_usd"]) for t in ts]
    assert key(ex_full["trades"]) == key(ex_filt["trades"])
    assert len(ex_full["trades"]) == len(signals)       # sinyal lolos BQ = dieksekusi semua
