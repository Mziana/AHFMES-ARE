"""P4 — test switch ablation: gate off → DISABLED terlabel + semantik forced."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import gates, registry
from strategy_v2.replay import run_decision_replay

M0 = 1788739200


def _m5(n, price=4400.0):
    return [{"time": M0 + i * 300, "open": price, "high": price + 1.0,
             "low": price - 1.0, "close": price, "volume": 100 + i % 5}
            for i in range(n)]


def _m15(n, price=4400.0):
    return [{"time": M0 + i * 900, "open": price, "high": price + 2.0,
             "low": price - 2.0, "close": price, "volume": 400}
            for i in range(n)]


def _run(profile, disable):
    reg = registry.load_hypothesis_registry()
    cfg = {"spread_points": 17.0, "balance": 1136.65,
           "risk_percent": profile["risk"]["risk_percent"],
           "config_hash": "0" * 64, "dataset_hash": "1" * 64}
    recs = run_decision_replay(_m5(60), _m15(60), profile, reg, None, cfg,
                               disable_gates=disable)
    # Layer B hanya berjalan di atas DATA_VALID (Pagar 3); record warmup awal
    # (M15 belum closed) validnya semua gate DISABLED by design.
    return [r for r in recs if r["layer_a"] == "DATA_VALID"]


def test_b4_disabled_labeled_not_pass():
    profile = registry.load_profile("MICRO")
    recs = _run(profile, ("b4_location",))
    assert recs, "harus ada record DATA_VALID"
    assert all(r["all_gate_results"]["b4_location"] == "DISABLED" for r in recs)
    # decide() melewatkan DISABLED → tidak ada veto B4
    assert all(not (r["first_veto_reason"] or "").startswith("B4:") for r in recs)


def test_b3_disabled_forces_bias():
    profile = registry.load_profile("MICRO")
    recs = _run(profile, ("b3_regime",))
    assert all(r["all_gate_results"]["b3_regime"] == "DISABLED" for r in recs)
    # arah dipaksa (long-only default) — arm tetap fungsional
    assert all(r["bias"] == "BUY_ONLY" for r in recs)
    assert all(r["decision"] in ("BUY", "SELL", "WAIT") for r in recs)


def test_b5_disabled_synth_trigger():
    profile = registry.load_profile("MICRO")
    recs = _run(profile, ("b5_trigger",))
    assert all(r["all_gate_results"]["b5_trigger"] == "DISABLED" for r in recs)
    # bar yang lolos rezim+lokasi membawa trigger sintetis terlabel
    assert all((r["trigger"] or {}).get("pattern") in (None, "ablation_any") for r in recs)


def test_b1_disabled_labeled():
    profile = registry.load_profile("MICRO")
    recs = _run(profile, ("b1_news",))
    assert all(r["all_gate_results"]["b1_news"] == "DISABLED" for r in recs)


def test_no_ablation_untouched():
    profile = registry.load_profile("MICRO")
    recs = _run(profile, ())
    assert all(r["all_gate_results"]["b4_location"] != "DISABLED" for r in recs)
    assert all(r["all_gate_results"]["b3_regime"] != "DISABLED" for r in recs)
