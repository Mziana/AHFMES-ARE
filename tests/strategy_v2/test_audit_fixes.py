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


# ─── P0-02 / P1-02: calendar artifact hash in config_hash ────────────────────

def test_p0_02_config_hash_changes_with_calendar_artifact():
    profile = registry.load_profile("MICRO")
    reg = registry.load_hypothesis_registry()
    h_none = registry.compute_config_hash(profile, reg)
    h_a = registry.compute_config_hash(profile, reg, calendar_artifact_hash="a" * 64)
    h_b = registry.compute_config_hash(profile, reg, calendar_artifact_hash="b" * 64)
    assert h_none != h_a != h_b and h_a != h_none
    # deterministik
    assert registry.compute_config_hash(profile, reg, calendar_artifact_hash="a" * 64) == h_a


def test_p0_02_calendar_artifact_hash_and_snapshot(tmp_path=None):
    from strategy_v2.replay import save_calendar_artifact, calendar_artifact_hash
    tmp = Path(__file__).parent / "_tmp_art_cal.json"
    tmp.write_text(json.dumps({"information_available_at": 1788700000,
                               "events": [{"date": "2026-09-07T08:30:00-04:00",
                                           "country": "USD", "impact": "High",
                                           "title": "CPI"}]}), encoding="utf-8")
    outdir = Path(__file__).parent / "_tmp_cal_art"
    try:
        raw = json.loads(tmp.read_text(encoding="utf-8"))
        art = save_calendar_artifact(raw, tmp, outdir, fetched_at=1788700000)
        # artifact tersimpan dengan provenance + nama deterministik dari hash konten
        assert art.exists() and art.name.startswith("calendar_")
        saved = json.loads(art.read_text(encoding="utf-8"))
        assert saved["information_available_at"] == 1788700000
        # hash konten artifact stabil & masuk config_hash via helper
        h1 = calendar_artifact_hash(art)
        h2 = calendar_artifact_hash(art)
        assert h1 == h2 and len(h1) == 64
        # file tidak ada → None (B1 fail-closed tetap jalan)
        assert calendar_artifact_hash(None) is None
        assert calendar_artifact_hash(art.parent / "nope.json") is None
    finally:
        tmp.unlink(missing_ok=True)
        import shutil as _sh
        _sh.rmtree(outdir, ignore_errors=True)


# ─── P0-03: fail-closed slippage/delay non-zero ──────────────────────────────

def test_p0_03_compute_cost_rejects_nonzero_slippage():
    import pytest
    from strategy_v2.costs import UnsupportedCostModel
    with pytest.raises(UnsupportedCostModel, match="slippage"):
        __import__("strategy_v2.costs", fromlist=["compute_cost"]).compute_cost(20.0, 20.0, slippage=1.0)


def test_p0_03_compute_cost_rejects_nonzero_delay():
    from strategy_v2.costs import UnsupportedCostModel, compute_cost
    import pytest
    with pytest.raises(UnsupportedCostModel, match="delay"):
        compute_cost(20.0, 20.0, delay=1)


def test_p0_03_default_zero_cost_model_accepted():
    from strategy_v2.costs import compute_cost
    c = compute_cost(20.0, 20.0)
    assert c["slippage_points"] == 0.0 and c["delay_bars"] == 0
    assert c["label"] == "HISTORICAL"


def test_p0_03_cost_model_mutation_fails_closed():
    # bila COST_MODEL di-mutasi non-zero → compute_cost menolak (bukan diam-diam)
    import pytest
    from strategy_v2.costs import UnsupportedCostModel, compute_cost
    import strategy_v2.registry as rm
    old = dict(rm.COST_MODEL)
    try:
        rm.COST_MODEL["slippage_points"] = 3.0
        with pytest.raises(UnsupportedCostModel):
            compute_cost(None, None)  # fallback path
    finally:
        rm.COST_MODEL.clear()
        rm.COST_MODEL.update(old)


def test_p0_03_execution_replay_runs_with_zero_cost():
    from strategy_v2.replay import run_decision_replay, run_execution_replay
    m5 = [{"time": 1788739200 + i * 300, "open": 4400.0, "high": 4401.2,
           "low": 4398.8, "close": 4400.4, "volume": 100 + (i % 5)} for i in range(220)]
    m15 = [{"time": 1788739200 + i * 900, "open": 4400.0 + 0.08 * i, "high": 4400.5 + 0.08 * i,
            "low": 4399.5 + 0.08 * i, "close": 4400.0 + 0.08 * i, "volume": 400} for i in range(220)]
    profile = registry.load_profile("MICRO")
    reg = registry.load_hypothesis_registry()
    cfg = {"config_hash": "a" * 64, "dataset_hash": "b" * 64, "balance": 1000.0, "spread_points": None}
    records = run_decision_replay(m5, m15, profile, reg,
                                  {"status": "empty", "events": [], "information_available_at": 0}, cfg)
    ex = run_execution_replay(records, m5, profile)
    assert ex["cost_label"] in ("HISTORICAL", "ESTIMATED_COST_MODEL")


# ─── P0-04: Layer A validasi M15 ─────────────────────────────────────────────

def _m15(n, start=1788739200, base=4400.0, drift=0.08):
    return [{"time": start + i * 900, "open": base + drift * i, "high": base + drift * i + 0.5,
             "low": base + drift * i - 0.5, "close": base + drift * i, "volume": 400}
            for i in range(n)]


def _m5(n, start=1788739200, base=4400.0):
    return [{"time": start + i * 300, "open": base, "high": base + 1.2, "low": base - 1.2,
             "close": base + 0.4, "volume": 100 + (i % 5)} for i in range(n)]


PROFILE_A = registry.load_profile("MICRO")


def _cfg(now_ts):
    return {"now_ts": now_ts, "layer_a": {}, "layer_b_ran": None,
            "calendar": {"status": "empty", "events": [], "information_available_at": None}}


def test_p0_04_m15_nan_fails_layer_a():
    m15 = _m15(120)
    m15[50]["close"] = float("nan")
    r = gates.layer_a_m15_integrity(m15, _cfg(_m15(120)[-1]["time"] + 900))
    assert r == "DATA_INVALID:m15:nan"


def test_p0_04_m15_gap_fails_layer_a():
    m15 = _m15(120)
    m15[60]["time"] += 900  # gap
    r = gates.layer_a_m15_integrity(m15, _cfg(m15[-1]["time"] + 900))
    assert r == "DATA_INVALID:m15:missing_bar"


def test_p0_04_m15_duplicate_fails_layer_a():
    m15 = _m15(120)
    m15[60]["time"] = m15[59]["time"]
    r = gates.layer_a_m15_integrity(m15, _cfg(m15[-1]["time"] + 900))
    assert r == "DATA_INVALID:m15:duplicate_ts"


def test_p0_04_m15_stale_fails_layer_a():
    m15 = _m15(120)
    far_future = m15[-1]["time"] + 900 + 4 * 900  # > 3 bar staleness
    r = gates.layer_a_m15_integrity(m15, _cfg(far_future))
    assert r == "DATA_INVALID:m15:stale"


def test_p0_04_evaluate_all_disables_layer_b_on_bad_m15():
    m5, m15 = _m5(60), _m15(300)
    m15[200]["close"] = float("nan")
    cfg = {"now_ts": m5[-1]["time"] + 300, "rsi_bias_threshold": 50,
           "min_bars_m15_warmup": 50, "layer_a": {},
           "calendar": {"status": "empty", "events": [], "information_available_at": None}}
    d = gates.evaluate_all({"m5": m5, "m15": m15}, PROFILE_A, cfg, {})
    assert d["layer_a"] == "DATA_INVALID:m15:nan"
    assert d["layer_b_ran"] is False
    assert all(v == "DISABLED" for v in d["all_gate_results"].values())


def test_p0_04_valid_m15_does_not_change_result():
    m5, m15 = _m5(60), _m15(300)
    cfg = {"now_ts": m5[-1]["time"] + 300, "rsi_bias_threshold": 50,
           "min_bars_m15_warmup": 50, "layer_a": {},
           "calendar": {"status": "empty", "events": [], "information_available_at": None}}
    d1 = gates.evaluate_all({"m5": m5, "m15": m15}, PROFILE_A, cfg, {})
    assert d1["layer_a"] == "DATA_VALID" and d1["layer_b_ran"] is True


# ─── P1-03: decision log schema validation ───────────────────────────────────

def test_p1_03_validator_rejects_violations():
    from strategy_v2 import schema_check
    schema = schema_check.load_schema()
    base = {
        "evaluation_timestamp": 1788739500, "data_available_until": 1788739500,
        "strategy_version": "strategy_v2/0.1.0-p0", "profile_id": "MICRO_V2",
        "hypothesis_registry_id": "registry-v2/1.0.0", "config_hash": "a" * 64,
        "dataset_hash": "b" * 64, "layer_a": "DATA_VALID",
        "all_gate_results": {"b1_news": "PASS", "b2_session": "PASS", "b3_regime": "PASS:BUY_ONLY",
                             "b4_location": "PASS:x", "b5_trigger": "PASS:hammer",
                             "b6_volume": "PASS", "b7_risk": "PASS"},
        "first_veto_reason": None, "bias": "BUY_ONLY", "decision": "BUY",
        "market_snapshot": {"spread": None, "atr": 120.0, "vol_ratio": 1.1,
                            "rsi_m15": 55.0, "rsi_m5": 52.0},
    }
    assert schema_check.validate_record(base, schema) == []
    # missing required
    bad = {k: v for k, v in base.items() if k != "config_hash"}
    errs = schema_check.validate_record(bad, schema)
    assert any("config_hash" in e for e in errs)
    # enum violation
    bad2 = dict(base, decision="MAYBE")
    assert any("enum" in e for e in schema_check.validate_record(bad2, schema))
    # pattern violation (config_hash bukan sha256)
    bad3 = dict(base, config_hash="nothex")
    assert any("pattern" in e for e in schema_check.validate_record(bad3, schema))
    # layer_a pattern: m15 reason valid, sampah ditolak
    ok4 = dict(base, layer_a="DATA_INVALID:m15:nan")
    assert schema_check.validate_record(ok4, schema) == []
    bad4 = dict(base, layer_a="DATA_INVALID:!!!")
    assert any("pattern" in e for e in schema_check.validate_record(bad4, schema))
    # gate enum violation di all_gate_results
    bad5 = dict(base, all_gate_results={**base["all_gate_results"], "b6_volume": "HUGE"})
    assert any("b6_volume" in e for e in schema_check.validate_record(bad5, schema))


def test_p1_03_real_replay_jsonl_validates_against_schema():
    from strategy_v2 import schema_check
    p_micro = Path("data/research/v2_replay/decision_micro.jsonl")
    p_scalp = Path("data/research/v2_replay/decision_scalp.jsonl")
    schema = schema_check.load_schema()
    for path in (p_micro, p_scalp):
        assert path.exists(), f"{path} tidak ada — jalankan replay dulu"
        n, errs = schema_check.validate_jsonl(path, schema)
        assert n > 0, f"{path} kosong"
        assert not errs, f"{path}: {len(errs)} pelanggaran schema, contoh: {errs[:3]}"
