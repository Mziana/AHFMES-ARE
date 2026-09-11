"""C2 — Review report contract tests (Analyst Desk v2.5).

- deterministik: input sama → markdown byte-identik
- usulan HANYA teks di laporan (TIDAK auto-applied): tidak ada penulisan
  hypothesis_registry.json dari modul ini
- usulan butuh n >= 20; tier PAPER expectancy <= 0 → usulan nonaktifkan
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import review_report as R


def _bucket(key, n, win, pnl, band):
    wr = win / n if n else 0.0
    return {"n": n, "win": win, "pts": 0.0, "pnl": round(pnl, 4), "updated": 0,
            "win_rate": round(wr, 4), "avg_rr": None,
            "expectancy": round(pnl / n, 4) if n else 0.0, "band": band}


def test_report_deterministic():
    buckets = {"micro|BUY|p_hammer|b_PAPER": _bucket("k", 25, 15, 12.5, "PAPER")}
    tiers = {"PAPER": {"n": 25, "win": 15, "pnl": 12.5, "win_rate": 0.6, "expectancy": 0.5}}
    a = R.build_review_report(buckets, tiers)
    b = R.build_review_report(buckets, tiers)
    assert a == b
    assert a.startswith("# Journal Review")


def test_report_empty_journal():
    out = R.build_review_report({}, None)
    assert "Journal kosong" in out


def test_proposal_requires_min_n_20():
    buckets = {"micro|BUY|p_hammer|b_PAST": _bucket("k", 19, 12, 9.5, "PAST")}
    out = R.build_review_report(buckets, None, min_n=20)
    assert "Belum ada usulan" in out
    buckets2 = {"micro|BUY|p_hammer|b_PAST": _bucket("k", 20, 13, 10.0, "PAST")}
    out2 = R.build_review_report(buckets2, None, min_n=20)
    assert "H-SCORE-DESK-01" in out2 and "turunkan" in out2


def test_proposal_negative_paper_band():
    buckets = {"micro|SELL|p_none|b_PAPER": _bucket("k", 30, 8, -15.0, "PAPER")}
    out = R.build_review_report(buckets, None)
    assert "naikkan" in out


def test_proposal_disable_paper_tier_on_negative_expectancy():
    buckets = {"micro|SELL|p_none|b_PAPER": _bucket("k", 30, 8, -15.0, "PAPER")}
    tiers = {"PAPER": {"n": 30, "win": 8, "pnl": -15.0, "win_rate": 0.27, "expectancy": -0.5}}
    out = R.build_review_report(buckets, tiers)
    assert "NONAKTIFKAN tier PAPER" in out
    assert "experiment freeze" in out   # freeze tetap ditegaskan


def test_no_auto_apply_module_never_writes_registry():
    """C2 kontrak: usulan = FILE teks; modul TIDAK menulis registry/kontrak."""
    src = Path(R.__file__).read_text(encoding="utf-8")
    assert "hypothesis_registry" not in src.replace(
        "hypothesis_registry", "hypothesis_registry") or "open(" not in src
    assert "json.dump" not in src
    assert "write_text" not in src
