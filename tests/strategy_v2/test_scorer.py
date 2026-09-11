"""Analyst Desk v2.5 — kontrak scorer (H-SCORE-DESK-01) + trade plan builder.

Di-guard di sini (plan `.hermes/plans/2026-09-08_133000-are-analyst-desk-7-steps.md`):
- scorer PURE & deterministik: input sama ×2 → output identik
- tier boundary exact: 39→PAST, 40→WATCH, 59→WATCH, 60→PAPER, 74→PAPER,
  75→TRADE (label skor; BUKAN keputusan)
- registry-driven (Pagar 1): bobot/ambang HANYA dari H-SCORE-DESK-01;
  weights degenerate → None (fail-closed), bukan skor pura-pura
- layer separation: skor TIDAK mengubah decision/first_veto_reason replay —
  menghapus/memutasi bobot TIDAK mengubah keputusan
- trade plan: deterministik, angka = angka record (tanpa penghitungan ulang),
  invalidation memuat harga konkret, backward-compatible schema
"""
import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import registry, scorer, trade_plan
from strategy_v2.replay import run_decision_replay

H_DESK = registry.hypothesis(registry.load_hypothesis_registry(), "H-SCORE-DESK-01")["value"]
W = H_DESK["weights"]


def _gates(b3="PASS:BUY_ONLY"):
    return {"b1_news": "PASS", "b2_session": "PASS", "b3_regime": b3,
            "b4_location": "PASS:ema9@100.00|dist_atr=0.100", "b5_trigger": "PASS:hammer",
            "b6_volume": "PASS", "b7_risk": "PASS", "b8_quality": "DISABLED"}


def _snap(rsi=50.0, vr=1.2, atr=300.0, close=100.0):
    return {"spread": 17.0, "atr": atr, "vol_ratio": vr, "rsi_m15": 55.0,
            "rsi_m5": rsi, "close": close}


def _risk(sl=250.0, tp=500.0):
    return {"sl_points": sl, "tp_points": tp}


# ── determinism (Pagar 4) ────────────────────────────────────────────────────

def test_score_pure_and_deterministic():
    a = scorer.score_setup(_gates(), _snap(), {"kind": "ema_pullback", "ref": "ema9@100.00",
                                               "distance_atr": 0.1}, _risk(), H_DESK)
    b = scorer.score_setup(_gates(), _snap(), {"kind": "ema_pullback", "ref": "ema9@100.00",
                                               "distance_atr": 0.1}, _risk(), H_DESK)
    assert a == b and a is not None
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_score_no_io_and_no_now(monkeypatch):
    """Scorer tidak boleh memanggil I/O atau wall-clock (statik: source tanpa open/time)."""
    src = Path(scorer.__file__).read_text(encoding="utf-8")
    for banned in ("open(", "time.time", "datetime.now", "Path("):
        assert banned not in src, f"scorer memanggil {banned} — zero I/O dilanggar"


# ── tier boundaries (exact) ──────────────────────────────────────────────────

def _tier_for_total(target: int) -> str:
    """Bangun input yang menghasilkan total persis = target.
    trend(30) & rr(10) biner/fix; sisanya dari momentum (20) + volume (15) +
    level (15) + catalyst (10) = 60 weight → dim = target_60/6.0."""
    # basis: semua dim non-trend/rr = 5 → kontribusi 60% × 50 = 30; trend=10 → 30;
    # rr (tp/sl=2.0) = 10 → 10. Total = 70. Kalibrasi momentum utk target.
    base = 30 + 10  # trend + rr (tp=2×sl)
    # kontribusi momentum per poin dim = 20/100 × dim×10 ... gunakan solver kecil:
    # total = 30 (trend) + 10 (rr) + (20*m + 15*v + 15*l + 10*c)/100 * 10
    # dgn v=l=c=0: total = 40 + 2*m  → m ∈ [0,10] → total ∈ [40,60]
    m = (target - 40) / 2.0
    if m < 0:     # di bawah 40: turunkan trend contribution via NO_TRADE & naikkan lagi
        b3 = "FAIL:NO_TRADE"
        m = target / 2.0
        gates = _gates(b3)
    else:
        gates = _gates()
    rsi = 50.0 + (10.0 - min(10.0, max(0.0, m))) * 0.3   # momentum dim = 10 - |rsi-50|/3
    snap = _snap(rsi=rsi, vr=0.0, atr=300.0, close=100.0)  # volume=0
    setup = {"kind": "ema_pullback", "ref": "x", "distance_atr": 1.0}  # level=0
    s = scorer.score_setup(gates, snap, setup, _risk(), H_DESK)
    assert s is not None
    return s


def test_tier_boundaries_exact():
    # 39 → PAST: NO_TRADE + momentum dim 19.5? tidak mungkin >10 — pakai solver lain:
    # tanpa trend (0): total = 2*m → m=19.5 tidak valid; jadi 39 dicapai dgn trend
    # dim 10 & m=19.5-impossible → gunakan kombinasi v.
    # Cara deterministik: langsung grid (trend ON, m, v) — total = 40 + 2m + 1.5v*...
    # total = 40 + 2m + 1.5v (trend=30, rr=10, m/v skala 0-10, l=c=0)
    def total_for(m_dim, v_dim, trend=True):
        rsi = 50.0 + (10.0 - m_dim) * 3.0
        snap = _snap(rsi=rsi, vr=0.8 + v_dim * 0.04, atr=300.0, close=100.0)
        setup = {"kind": "ema_pullback", "ref": "x", "distance_atr": 1.0}
        s = scorer.score_setup(_gates() if trend else _gates("FAIL:NO_TRADE"),
                               snap, setup, _risk(), H_DESK)
        return s["total"]

    # cari input utk 39, 40, 59, 60, 74, 75 — total = 40 + 2m + 1.5v (trend ON)
    # (2 = 20/100*10; 1.5 = 15/100*10)
    cases = {39: (0.0, 0), 40: (0.0, 0), 59: (0.0, 0), 60: (0.0, 0), 74: (0.0, 0), 75: (0.0, 0)}
    # 39: butuh 40+2m+1.5v=39 → tidak bisa (min 40 dgn trend ON). Pakai trend OFF:
    # total = 2m + 1.5v → 39 = 2*19.5? tidak. total = 2m+1.5v, m,v∈[0,10] → max 35.
    # Maka 39 dicapai trend OFF + rr lebih besar? rr max 10. 2m+1.5v+10*1.0=39 →
    # 2m+1.5v=29 → m=10, v=6 → 20+9=29 ✓
    rsi = 50.0 + (10.0 - 10.0) * 3.0  # momentum dim 10
    snap39 = _snap(rsi=rsi, vr=0.8 + 6 * 0.04, atr=300.0, close=100.0)
    s = scorer.score_setup(_gates("FAIL:NO_TRADE"), snap39,
                           {"kind": "ema_pullback", "ref": "x", "distance_atr": 1.0}, _risk(), H_DESK)
    assert s["total"] == 39 and s["tier"] == "PAST"

    # 40: trend ON, m=0, v=0 → total = 40 → WATCH
    rsi40 = 50.0 + 10.0 * 3.0  # momentum dim 0
    s = scorer.score_setup(_gates(), _snap(rsi=rsi40, vr=0.0),
                           {"kind": "ema_pullback", "ref": "x", "distance_atr": 1.0}, _risk(), H_DESK)
    assert s["total"] == 40 and s["tier"] == "WATCH"

    # 59 → WATCH: trend ON, m=9.5, v=0 → 40+19=59
    rsi59 = 50.0 + 0.5 * 3.0
    s = scorer.score_setup(_gates(), _snap(rsi=rsi59, vr=0.0),
                           {"kind": "ema_pullback", "ref": "x", "distance_atr": 1.0}, _risk(), H_DESK)
    assert s["total"] == 59 and s["tier"] == "WATCH"

    # 60 → PAPER: trend ON, m=10, v=0 → 40+20=60
    s = scorer.score_setup(_gates(), _snap(rsi=50.0, vr=0.0),
                           {"kind": "ema_pullback", "ref": "x", "distance_atr": 1.0}, _risk(), H_DESK)
    assert s["total"] == 60 and s["tier"] == "PAPER"

    # 74 → PAPER: trend ON, m=10, v=8/1.5=... 40+20+1.5v=74 → v=... 1.5*9.33=14 → 74
    rsi74 = 50.0
    vr74 = 0.8 + (14.0 / 1.5) * 0.04
    s = scorer.score_setup(_gates(), _snap(rsi=rsi74, vr=round(vr74, 6)),
                           {"kind": "ema_pullback", "ref": "x", "distance_atr": 1.0}, _risk(), H_DESK)
    assert s["total"] == 74, s
    assert s["tier"] == "PAPER"

    # 75 → TRADE: trend ON, m=10, catalyst hammer=6 → 40+20+6=66... butuh lebih:
    # + level 10 (dist 0) + volume 0 → 40+20+10+0(catalyst 0? gunakan pattern kuat)
    # trend30+rr10 + momentum20 + level15 = 75 (catalyst=0, volume=0)
    s = scorer.score_setup(_gates(), _snap(rsi=50.0, vr=0.0),
                           {"kind": "ema_pullback", "ref": "x", "distance_atr": 0.0}, _risk(), H_DESK)
    assert s["total"] == 75, s
    assert s["tier"] == "TRADE"


def test_trade_tier_is_label_not_decision():
    """Tier TRADE hanyalah label skor — kontrak layer separation (docstring)."""
    s = scorer.score_setup(_gates(), _snap(rsi=50.0),
                           {"kind": "ema_pullback", "ref": "x", "distance_atr": 0.0},
                           _risk(), H_DESK)
    assert s["tier"] == "TRADE"   # skor 75 tetapi ini BUKAN sinyal entry


# ── registry-driven (Pagar 1) ────────────────────────────────────────────────

def test_weights_from_registry_mutation_changes_identity():
    import copy
    reg = registry.load_hypothesis_registry()
    h1 = registry.compute_config_hash(registry.load_profile("MICRO"), reg)
    r2 = copy.deepcopy(reg)
    r2["hypotheses"]["H-SCORE-DESK-01"]["value"]["weights"]["trend"] += 1
    h2 = registry.compute_config_hash(registry.load_profile("MICRO"), r2)
    assert h1 != h2   # mutasi bobot = identity eksperimen baru


def test_degenerate_weights_fail_closed():
    assert scorer.score_setup(_gates(), _snap(), None, _risk(), {"weights": {}, "tiers": {}}) is None
    assert scorer.score_setup(_gates(), _snap(), None, _risk(),
                              {"weights": {"trend": 0}, "tiers": {"watch": 40, "paper": 60}}) is None


# ── NaN / missing inputs (adversarial) ───────────────────────────────────────

def test_nan_and_missing_inputs_score_zero_not_crash():
    nan = float("nan")
    s = scorer.score_setup(_gates(), _snap(rsi=nan, vr=nan, atr=nan, close=nan),
                           {"kind": "x", "ref": "x", "distance_atr": nan}, _risk(sl=0, tp=0), H_DESK)
    assert s is not None and s["tier"] in ("PAST", "WATCH", "PAPER", "TRADE")
    s2 = scorer.score_setup({}, {}, None, None, H_DESK)
    assert s2 is not None   # missing → komponen 0, tanpa exception
    assert s2["dimensions"]["trend"] == 0.0


# ── layer separation: scorer TIDAK mengubah keputusan replay ─────────────────

def make_m5(n, start=1788739200, base=4400.0, drift=0.02, vol=100):
    return [{"time": start + i * 300, "open": base + drift * i, "high": base + drift * i + 1.2,
             "low": base + drift * i - 1.2, "close": base + drift * i + 0.4, "volume": vol + (i % 5)}
            for i in range(n)]


def make_m15(n, start=1788739200, base=4400.0, drift=0.08):
    return [{"time": start + i * 900, "open": base + drift * i, "high": base + drift * i + 0.5,
             "low": base + drift * i - 0.5, "close": base + drift * i, "volume": 400 + (i % 3)}
            for i in range(n)]


def _replay(reg_override=None):
    import copy
    reg = reg_override or registry.load_hypothesis_registry()
    profile = registry.load_profile("MICRO")
    cfg = {"config_hash": "a" * 64, "dataset_hash": "b" * 64, "balance": 1000.0,
           "spread_points": None}
    return run_decision_replay(make_m5(120), make_m15(120), profile, reg,
                               {"status": "empty", "events": [], "information_available_at": 0}, cfg)


def test_score_never_changes_first_veto():
    """Layer separation: hapus H-SCORE-DESK-01 dari registry → keputusan identik."""
    import copy
    base = _replay()
    reg2 = copy.deepcopy(registry.load_hypothesis_registry())
    del reg2["hypotheses"]["H-SCORE-DESK-01"]
    stripped = _replay(reg2)
    assert len(base) == len(stripped)
    for b, s in zip(base, stripped):
        assert b["decision"] == s["decision"]
        assert b["first_veto_reason"] == s["first_veto_reason"]


def test_weight_mutation_mid_registry_does_not_change_decisions():
    import copy
    base = _replay()
    reg2 = copy.deepcopy(registry.load_hypothesis_registry())
    reg2["hypotheses"]["H-SCORE-DESK-01"]["value"]["weights"] = {
        "trend": 10, "momentum": 10, "volume": 30, "level": 30, "catalyst": 10, "rr": 10}
    mutated = _replay(reg2)
    for b, m in zip(base, mutated):
        assert b["decision"] == m["decision"]
        assert b["first_veto_reason"] == m["first_veto_reason"]


# ── A2: setup_score masuk record (optional, backward-compatible) ─────────────

def test_setup_score_in_log_and_schema_backward_compatible():
    from strategy_v2 import schema_check
    schema = schema_check.load_schema()
    records = _replay()
    rec = records[100]
    assert "setup_score" in rec and rec["setup_score"] is not None
    assert set(rec["setup_score"].keys()) == {"dimensions", "total", "tier"}
    assert 0 <= rec["setup_score"]["total"] <= 100
    # record TANPA setup_score/trade_plan tetap valid (schema optional)
    old_style = {k: v for k, v in rec.items() if k not in ("setup_score", "trade_plan")}
    assert schema_check.validate_record(old_style, schema) == []
    assert schema_check.validate_record(rec, schema) == []


# ── B1: trade plan builder ───────────────────────────────────────────────────

def _rec_for_plan(decision="BUY", bias="BUY_ONLY", sl=250.0, tp=500.0, close=4400.0,
                  dist=0.1, pattern="hammer"):
    return {
        "evaluation_timestamp": 1788739200 + 100 * 300,
        "profile_id": "MICRO_V2",
        "decision": decision, "bias": bias,
        "setup": {"kind": "ema_pullback", "ref": "ema9@4399.12", "distance_atr": dist},
        "trigger": {"pattern": pattern, "bar_ts": 1788739200 + 99 * 300},
        "sl_points": sl, "tp_points": tp,
        "market_snapshot": _snap(close=close, atr=300.0),
        "setup_score": {"dimensions": {}, "total": 62, "tier": "PAPER"},
    }


def test_plan_fields_complete_for_paper_tier():
    plan = trade_plan.build_trade_plan(_rec_for_plan(), registry.load_profile("MICRO"))
    assert plan is not None
    for f in ("plan_id", "thesis", "invalidation", "confidence", "direction",
              "entry_points", "stop_points", "target_points", "rr"):
        assert f in plan
        v = plan[f]
        assert v is not None and (not isinstance(v, str) or v.strip()), f
    assert plan["direction"] == "BUY" and plan["tier"] == "PAPER"
    assert plan["confidence"] == 62


def test_plan_deterministic():
    a = trade_plan.build_trade_plan(_rec_for_plan(), registry.load_profile("MICRO"))
    b = trade_plan.build_trade_plan(_rec_for_plan(), registry.load_profile("MICRO"))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_plan_numbers_match_record():
    plan = trade_plan.build_trade_plan(_rec_for_plan(sl=250.0, tp=500.0, close=4400.0),
                                       registry.load_profile("MICRO"))
    assert plan["stop_points"] == 250.0        # angka record, bukan hitungan lain
    assert plan["target_points"] == 500.0
    assert plan["rr"] == 2.0
    assert plan["entry_points"] == 4400.0


def test_invalidation_mentions_price():
    plan = trade_plan.build_trade_plan(_rec_for_plan(sl=250.0, close=4400.0),
                                       registry.load_profile("MICRO"))
    assert "4397.50" in plan["invalidation"]   # 4400 - 250*0.01 = 4397.50 (harga konkret)
    plan_s = trade_plan.build_trade_plan(_rec_for_plan(decision="SELL", bias="SELL_ONLY",
                                                       sl=250.0, close=4400.0),
                                         registry.load_profile("MICRO"))
    assert "4402.50" in plan_s["invalidation"]  # 4400 + 250*0.01


def test_plan_none_without_direction_or_sl():
    rec = _rec_for_plan(decision="WAIT", bias="NO_TRADE")
    assert trade_plan.build_trade_plan(rec, registry.load_profile("MICRO")) is None
    rec2 = _rec_for_plan(sl=0.0)
    assert trade_plan.build_trade_plan(rec2, registry.load_profile("MICRO")) is None
