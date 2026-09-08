"""Regression tests — audit findings fix (P0-01..P1-03), satu blok per finding.

Blok P0-01 masuk commit provenance; blok berikutnya ditambah per commit.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import gates, registry
from strategy_v2.replay import load_calendar


# ─── P0-01: news temporal provenance ─────────────────────────────────────────

POLICY = registry.load_profile("MICRO")["news"]


def _cal(info_at, events):
    return {"status": "ok", "information_available_at": info_at, "events": events}


def test_p0_01_old_snapshot_is_stale_even_if_event_recent():
    # event ts dekat T, tapi snapshot diambil LAMA → provenance mendeteksi staleness
    now = 1788799380
    ev = [{"ts": now - 60, "impact": "high", "currency": "USD"}]
    assert gates.b1_news(now, _cal(now - 5 * 3600, ev), POLICY) == "NEWS_DATA_STALE"


def test_p0_01_fresh_snapshot_active_event():
    now = 1788799380
    ev = [{"ts": now - 60, "impact": "high", "currency": "USD"}]
    assert gates.b1_news(now, _cal(now - 600, ev), POLICY) == "NEWS_EVENT_ACTIVE"


def test_p0_01_missing_provenance_fail_closed():
    # snapshot TANPA information_available_at → jujur STALE, bukan heuristic PASS
    now = 1788799380
    ev = [{"ts": now - 60, "impact": "high", "currency": "USD"}]
    cal = {"status": "ok", "events": ev}  # tanpa field provenance
    assert gates.b1_news(now, cal, POLICY) == "NEWS_DATA_STALE"


def test_p0_01_event_ts_and_availability_are_separate_axes():
    # dua axis berbeda: availability segar + event di luar window → PASS
    now = 1788799380
    ev = [{"ts": now - 6 * 3600, "impact": "high", "currency": "USD"}]
    assert gates.b1_news(now, _cal(now - 600, ev), POLICY) == "PASS"
    # availability tua + event di luar window → tetap STALE (availability menang)
    assert gates.b1_news(now, _cal(now - 5 * 3600, ev), POLICY) == "NEWS_DATA_STALE"


def test_p0_01_load_calendar_reads_explicit_provenance():
    tmp = Path(__file__).parent / "_tmp_prov_cal.json"
    tmp.write_text(json.dumps({"information_available_at": 1788700000,
                               "events": [{"date": "2026-09-07T08:30:00-04:00",
                                           "country": "USD", "impact": "High",
                                           "title": "CPI"}]}), encoding="utf-8")
    try:
        cal = load_calendar(tmp)
        assert cal["information_available_at"] == 1788700000
        assert cal["status"] == "ok"
    finally:
        tmp.unlink(missing_ok=True)
    # artifact tanpa field → None (fail-closed di b1_news)
    tmp2 = Path(__file__).parent / "_tmp_noprov_cal.json"
    tmp2.write_text(json.dumps([{"date": "2026-09-07T08:30:00-04:00",
                                 "country": "USD", "impact": "High", "title": "CPI"}]),
                    encoding="utf-8")
    try:
        cal2 = load_calendar(tmp2)
        assert cal2["information_available_at"] is None
    finally:
        tmp2.unlink(missing_ok=True)
