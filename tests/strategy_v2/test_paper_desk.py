"""C1 wiring — paper desk driver tests (Analyst Desk v2.5).

- tier PAPER/TRADE di-paper-trade otomatis via simulator F1b yang sama
- deterministik: dua run di direktori terpisah → journal byte-identik
- input records TIDAK dimutasi (layer separation — journal hanya pembaca)
- cooldown diterapkan antar paper entry
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import paper, registry
from strategy_v2.paper import run_paper_desk
from strategy_v2.replay import run_decision_replay
from tests.strategy_v2.test_scorer import make_m15, make_m5


def _records_and_bars():
    m5 = make_m5(160)
    m15 = make_m15(160)
    profile = registry.load_profile("MICRO")
    reg = registry.load_hypothesis_registry()
    cfg = {"config_hash": "a" * 64, "dataset_hash": "b" * 64, "balance": 1000.0,
           "spread_points": 17.0}
    records = run_decision_replay(m5, m15, profile, reg,
                                  {"status": "empty", "events": [],
                                   "information_available_at": 0}, cfg)
    return records, m5, profile


def test_paper_desk_runs_and_writes_journal(tmp_path):
    records, m5, profile = _records_and_bars()
    before = json.dumps(records, sort_keys=True)
    res = run_paper_desk(records, m5, profile, spread_points=17.0, out_dir=tmp_path)
    # input tak dimutasi (layer separation)
    assert json.dumps(records, sort_keys=True) == before
    assert res["papered"] >= 0 and res["opened"] == res["closed"]
    if res["opened"] > 0:
        assert Path(res["journal_path"]).exists()
        rows = [json.loads(l) for l in Path(res["journal_path"]).read_text(encoding="utf-8").splitlines() if l.strip()]
        assert all(r.get("paper") is True for r in rows)
        assert rows[0]["evt"] == "open"
        # expectancy math jalan
        assert isinstance(res["review"], dict)
        assert "PAPER" in res["review_by_tier"] or "TRADE" in res["review_by_tier"] or res["review"]


def test_paper_desk_deterministic_two_runs(tmp_path):
    records, m5, profile = _records_and_bars()
    d1, d2 = tmp_path / "r1", tmp_path / "r2"
    res1 = run_paper_desk(records, m5, profile, spread_points=17.0, out_dir=d1)
    res2 = run_paper_desk(records, m5, profile, spread_points=17.0, out_dir=d2)
    j1, j2 = Path(res1["journal_path"]), Path(res2["journal_path"])
    if res1["opened"] == 0:
        assert res2["opened"] == 0
        return
    assert j1.read_bytes() == j2.read_bytes()   # byte-identik (Pagar 4)


def test_paper_desk_respects_cooldown(tmp_path):
    """Filter cooldown diterapkan eksplisit antar paper entry (unit: _cooldown_ok
    + driver `papered` < sinyal mentah saat sinyal lebih rapat dari cooldown)."""
    records, m5, profile = _records_and_bars()
    cd = profile["risk"]["cooldown_minutes"]
    # unit: rule cooldown
    assert paper._cooldown_ok(None, 1000, cd) is True
    assert paper._cooldown_ok(1000, 1000 + cd * 60, cd) is True
    assert paper._cooldown_ok(1000, 1000 + cd * 60 - 1, cd) is False

    # driver: paksa banyak sinyal PAPER rapat (fake record minimal) —
    # `papered` harus < jumlah sinyal karena spacing cooldown.
    fake = []
    base = 1788800000
    for i in range(6):
        fake.append({"evaluation_timestamp": base + i * 180, "decision": "BUY",   # 3 menit — lebih rapat dari cooldown
                     "bias": "BUY_ONLY",
                     "setup_score": {"dimensions": {}, "total": 70, "tier": "PAPER"},
                     "risk_calc": {"sl_points": 250.0, "tp_points": 500.0},
                     "trade_plan": {"plan_id": f"TP-{i}", "direction": "BUY",
                                    "stop_points": 250.0, "tier": "PAPER",
                                    "setup_score": {"total": 70}, "trigger": {"pattern": "x"}}})
    res = run_paper_desk(fake, make_m5(40, start=base - 40 * 300), profile,
                         spread_points=17.0, out_dir=tmp_path)
    assert res["papered"] < 6   # 6 sinyal @ 5 menit, cooldown MICRO 5m → terfilter


def test_paper_tier_constant_contract():
    # kontrak plan: PAPER + TRADE di-paper-trade; WATCH/PAST tidak
    assert paper.PAPER_TIERS == ("PAPER", "TRADE")
