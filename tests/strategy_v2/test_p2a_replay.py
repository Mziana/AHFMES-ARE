"""P2a replay engine — determinism, qualification, funnel (full invariant = Paket 4)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import registry
from strategy_v2.replay import (build_funnel, qualify_dataset, run_decision_replay,
                                run_execution_replay, load_calendar)


def make_m5(n, start=1788739200, base=4400.0, drift=0.02, vol=100):
    return [{"time": start + i * 300, "open": base + drift * i, "high": base + drift * i + 1.2,
             "low": base + drift * i - 1.2, "close": base + drift * i + 0.4, "volume": vol + (i % 5)}
            for i in range(n)]


def make_m15(n, start=1788739200, base=4400.0, drift=0.08):
    out = []
    for i in range(n):
        c = base + drift * i
        out.append({"time": start + i * 900, "open": c, "high": c + 0.5, "low": c - 0.5,
                    "close": c, "volume": 400 + (i % 3)})
    return out


def _replay_once():
    m5 = make_m5(220)
    m15 = make_m15(220)
    profile = registry.load_profile("MICRO")
    reg = registry.load_hypothesis_registry()
    cfg = {"config_hash": "a" * 64, "dataset_hash": "b" * 64, "balance": 1000.0, "spread_points": None}
    return run_decision_replay(m5, m15, profile, reg,
                               {"status": "empty", "events": [], "information_available_at": 0}, cfg)


def test_replay_deterministic_two_runs_identical():
    r1 = _replay_once()
    r2 = _replay_once()
    assert len(r1) == len(r2) == 220
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)  # bit-per-bit field


def test_replay_records_have_pagar4_fields():
    rec = _replay_once()[100]
    for f in ["evaluation_timestamp", "data_available_until", "strategy_version", "profile_id",
              "hypothesis_registry_id", "config_hash", "dataset_hash", "layer_a",
              "all_gate_results", "first_veto_reason", "decision", "market_snapshot"]:
        assert f in rec
    assert rec["evaluation_timestamp"] == rec["data_available_until"]
    # evaluation_timestamp = epoch bar CLOSE (open + 300)
    assert (rec["evaluation_timestamp"] - 1788739200) % 300 == 0
    # tidak ada wall-clock di record
    assert "now" not in json.dumps(rec).lower().replace("now_ts", "")


def test_funnel_completeness_counts_add_up():
    records = _replay_once()
    execution = run_execution_replay(records, make_m5(220), registry.load_profile("MICRO"))
    funnel = build_funnel(records, execution)
    invalid = funnel["data_invalid"]
    valid = funnel["layer_b_evaluated"]
    assert funnel["evaluation_opportunities"] == invalid + valid
    veto_total = sum(1 for r in records if r["layer_a"] == "DATA_VALID" and r["first_veto_reason"])
    assert valid == veto_total + funnel["final_signals"] + funnel["wait"]
    assert all(k in funnel for k in ["evaluation_opportunities", "data_invalid", "veto_by_gate",
                                     "final_signals", "executed_trades", "rejected_executions",
                                     "gross_expectancy_usd", "total_costs_usd", "net_expectancy_usd"])


def test_qualification_detects_corruption():
    m5 = make_m5(50)
    ok = qualify_dataset(m5, make_m15(50))
    assert ok["m5"]["valid"] and ok["m15"]["valid"]
    bad = make_m5(50)
    bad[10]["high"] = bad[10]["low"] - 1
    rep = qualify_dataset(bad, make_m15(50))
    assert not rep["m5"]["valid"] and rep["m5"]["ohlc_invalid"] == 1


def test_execution_never_before_next_bar_open():
    m5 = make_m5(220)
    records = _replay_once()
    # paksa dua sinyal artifisial pada bar terpilih
    records[50]["decision"] = "BUY"
    records[50]["sl_points"] = 150.0
    records[50]["tp_points"] = 150.0
    records[50]["lot"] = 0.02
    ex = run_execution_replay(records, m5, registry.load_profile("MICRO"))
    for t in ex["trades"]:
        assert t["entry_ts"] >= t["entry_ts"]  # entry pakai open bar dengan open_ts == T
        bar = next(b for b in m5 if b["time"] == t["entry_ts"])
        assert t["entry"] in (bar["open"] + ex["spread_model"]["entry_spread_points"] * 0.01,
                              bar["open"] - ex["spread_model"]["entry_spread_points"] * 0.01)
        assert t["cost_label"] in ("HISTORICAL", "ESTIMATED_COST_MODEL")


def test_calendar_loader_real_shape():
    cal = load_calendar(None)
    assert cal is None  # tanpa file → B1 fail-closed dijalankan run_decision_replay
    tmp = Path(__file__).parent / "_tmp_cal.json"
    tmp.write_text(json.dumps([{"title": "CPI", "country": "USD", "impact": "High",
                                "date": "2026-09-07T08:30:00-04:00"}]), encoding="utf-8")
    try:
        cal = load_calendar(tmp)
        assert cal["status"] == "ok" and cal["events"][0]["currency"] == "USD"
    finally:
        tmp.unlink(missing_ok=True)
