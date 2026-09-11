"""C1 — JournalLoop contract tests (Analyst Desk v2.5, plan C1).

- determinism: urutan operasi sama → file byte-identik
- append-only: file TIDAK pernah dimodifikasi mundur (prefix stabil; ukuran
  tidak mengecil); tidak ada API edit/hapus baris
- review math benar: win_rate, avg_rr, expectancy = avg net
- format kompatibel data/learning/buckets.json (n/win/pts/pnl/updated)
- layer separation: paper trade TIDAK pernah mengubah decision gate — journal
  murni pembaca record & penulis buku besar (statik: tanpa import gates/replay)
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import journal as J


PLAN_BUY = {
    "plan_id": "TP-MICRO_V2-1788739200",
    "direction": "BUY", "tier": "PAPER",
    "thesis": "XAUUSD pulled back to ema9@4399.12 with elevated volume; BUY regime aligned.",
    "invalidation": "Close back below 4397.50 (SL 250 pts).",
    "confidence": 62,
    "entry_points": 4400.0, "stop_points": 250.0, "target_points": 500.0, "rr": 2.0,
    "setup_score": {"dimensions": {}, "total": 62, "tier": "PAPER"},
    "trigger": {"pattern": "hammer", "bar_ts": 1788739500},
    "profile_id": "MICRO_V2",
}


@pytest.fixture()
def jpath(tmp_path):
    return tmp_path / "journal_micro.jsonl"


def _open(jpath, plan=PLAN_BUY, ts=1788800000, price=4400.0):
    return J.open_paper_trade(plan, ts, price, profile="MICRO", out_dir=jpath.parent)


def test_open_close_round_trip_and_outcome(jpath):
    entry = _open(jpath, ts=1788800000, price=4400.0)
    rec = J.close_paper_trade(entry, exit_ts=1788801800, exit_price=4403.0,
                              reason="TP", point_value_usd_per_lot=1.0, lot=0.01,
                              out_dir=jpath.parent)
    assert rec["pnl_points"] == 3.0
    assert rec["rr_realized"] == pytest.approx(3.0 / 250.0)
    assert rec["pnl_usd"] == pytest.approx(3.0 * 1.0 * 0.01, abs=1e-6)
    assert rec["win"] == 1 and rec["paper"] is True
    rows = J.read_journal(jpath)
    assert [r["evt"] for r in rows] == ["open", "close"]
    assert rows[0]["paper"] is True


def test_journal_append_only_never_rewrites_prefix(jpath):
    """Append-only: setelah tiap operasi, baris lama TIDAK berubah (prefix stabil),
    ukuran tidak mengecil, dan tidak ada jalur rewrite (file dibuka mode 'a')."""
    entry = _open(jpath, ts=1788800000, price=4400.0)
    snapshot1 = jpath.read_bytes()
    J.close_paper_trade(entry, 1788801800, 4403.0, "TP", out_dir=jpath.parent)
    snapshot2 = jpath.read_bytes()
    assert snapshot2.startswith(snapshot1)      # prefix = baris lama, tak tersentuh
    entry2 = _open(jpath, plan={**PLAN_BUY, "plan_id": "TP-2"}, ts=1788803600, price=4401.0)
    snapshot3 = jpath.read_bytes()
    assert snapshot3.startswith(snapshot2)
    assert len(snapshot3) > len(snapshot2)
    # src hanya memakai append ('a'), tanpa 'w' truncate di jalur journal
    src = Path(J.__file__).read_text(encoding="utf-8")
    assert "with open(path, \"a\"" in src
    assert "with open(path, \"w\"" not in src


def test_review_math_expectancy_avg_net(jpath):
    e1 = _open(jpath, plan={**PLAN_BUY, "plan_id": "TP-1"}, ts=1788800000)
    J.close_paper_trade(e1, 1788801800, 4405.0, "TP", point_value_usd_per_lot=1.0,
                        lot=1.0, out_dir=jpath.parent)              # +5 pts → +$5
    e2 = _open(jpath, plan={**PLAN_BUY, "plan_id": "TP-2"}, ts=1788803600)
    J.close_paper_trade(e2, 1788805400, 4398.0, "SL", point_value_usd_per_lot=1.0,
                        lot=1.0, out_dir=jpath.parent)              # -2 pts → -$2
    e3 = _open(jpath, plan={**PLAN_BUY, "plan_id": "TP-3"}, ts=1788807200)
    J.close_paper_trade(e3, 1788809000, 4404.0, "TP", point_value_usd_per_lot=1.0,
                        lot=1.0, out_dir=jpath.parent)              # +4 pts → +$4
    buckets = J.review(jpath)
    assert len(buckets) == 1
    b = buckets[list(buckets)[0]]
    assert b["n"] == 3 and b["win"] == 2
    assert b["win_rate"] == pytest.approx(2 / 3, abs=1e-3)   # dibulatkan 4 desimal
    assert b["pnl"] == pytest.approx(5.0 - 2.0 + 4.0)
    assert b["expectancy"] == pytest.approx((5.0 - 2.0 + 4.0) / 3, abs=1e-3)  # avg net (4 desimal)
    # format kompatibel buckets.json (are/learning.py)
    for k in ("n", "win", "pts", "pnl", "updated"):
        assert k in b
    assert b["avg_rr"] is not None


def test_review_by_tier_and_score_band(jpath):
    e = _open(jpath, ts=1788800000)
    J.close_paper_trade(e, 1788801800, 4405.0, "TP", point_value_usd_per_lot=1.0, lot=1.0,
                        out_dir=jpath.parent)
    tiers = J.review_by_tier(jpath)
    assert tiers["PAPER"]["n"] == 1
    assert tiers["PAPER"]["expectancy"] == pytest.approx(5.0)
    rows = J.read_journal(jpath)
    assert rows[1]["bucket_key"].endswith("|b_PAPER")   # skor 62 → band PAPER [60,75)
    assert J.score_band(39) == "PAST" and J.score_band(40) == "WATCH"
    assert J.score_band(60) == "PAPER" and J.score_band(75) == "TRADE"


def test_review_deterministic(jpath):
    e1 = _open(jpath, plan={**PLAN_BUY, "plan_id": "TP-1"}, ts=1788800000)
    J.close_paper_trade(e1, 1788801800, 4405.0, "TP", out_dir=jpath.parent)
    r1 = J.review(jpath)
    r2 = J.review(jpath)
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)


def test_layer_separation_journal_never_touches_gates():
    """Journal TIDAK mengubah decision gate: secara struktural ia tidak mengimpor
    gate engine/replay (murni buku besar paper), dan tidak punya API untuk itu."""
    src = Path(J.__file__).read_text(encoding="utf-8")
    assert "import gates" not in src and "from .gates" not in src
    assert "import replay" not in src and "from .replay" not in src
    assert "decision" not in {f for f in dir(J)}


def test_open_requires_plan_id(jpath):
    with pytest.raises(ValueError):
        J.open_paper_trade({}, 1788800000, 4400.0, out_dir=jpath.parent)
    with pytest.raises(ValueError):
        J.close_paper_trade({}, 1788801800, 4403.0, "TP", out_dir=jpath.parent)
