"""P0 contract freeze tests — Pagar 1 (experiment freeze) + schema."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import registry as reg

PKG = Path(reg.PKG_DIR)


def test_hypothesis_registry_complete():
    r = reg.load_hypothesis_registry()
    required = ["H-SESSION-01", "H-RSI-BIAS-01", "H-RSI-ENTRY-01", "H-LOC-01",
                "H-LOC-02", "H-VOL-01", "H-ATR-01", "H-Q1"]
    for h in required:
        assert h in r["hypotheses"], f"hipotesis {h} hilang"
        e = r["hypotheses"][h]
        assert set(["id", "value", "status", "source"]).issubset(e.keys())
        assert e["status"] == "HYPOTHESIS"
        assert e["source"] == "design_v2.3"


def test_profiles_frozen_fields():
    for pid, cap, cd in (("SCALP", 400, 30), ("MICRO", 250, 5)):
        p = reg.load_profile(pid)
        assert p["risk"]["max_stop_points"] == cap
        assert p["risk"]["cooldown_minutes"] == cd
        assert p["risk"]["max_trades_per_day"] in (6, 20)
        assert p["session_windows_utc"] == [[7, 17]]
        assert p["news"]["policy"] == "FAIL_CLOSED"
    micro = reg.load_profile("MICRO")
    assert micro["volume_gate"]["enabled"] is True
    assert micro["volume_gate"]["exclude_self"] is True
    scalp = reg.load_profile("SCALP")
    assert scalp["volume_gate"]["enabled"] is False


def test_config_hash_changes_on_any_contract_byte():
    p = reg.load_profile("MICRO")
    r = reg.load_hypothesis_registry()
    h1 = reg.compute_config_hash(p, r)

    # mutasi kecil di profile → identity baru
    import copy
    p2 = copy.deepcopy(p)
    p2["risk"]["max_trades_per_day"] += 1
    assert reg.compute_config_hash(p2, r) != h1

    # mutasi kecil di registry → identity baru
    r2 = copy.deepcopy(r)
    r2["hypotheses"]["H-VOL-01"]["value"]["ratio"] = 1.3
    assert reg.compute_config_hash(p, r2) != h1

    # mutasi cost model → identity baru
    import strategy_v2.registry as rm
    old = dict(rm.COST_MODEL)
    try:
        rm.COST_MODEL["slippage_points"] = 1.0
        assert reg.compute_config_hash(p, r) != h1
    finally:
        rm.COST_MODEL.clear()
        rm.COST_MODEL.update(old)

    # dataset ikut identity bila diberikan
    assert reg.compute_config_hash(p, r, dataset_sha="ab" * 32) != h1

    # deterministik: sama input → hash sama
    assert reg.compute_config_hash(p, r) == h1


def test_decision_log_schema_shape():
    s = json.loads((PKG / "schemas" / "decision_log.schema.json").read_text(encoding="utf-8"))
    req = s["required"]
    for f in ["evaluation_timestamp", "data_available_until", "strategy_version",
              "profile_id", "hypothesis_registry_id", "config_hash", "dataset_hash",
              "first_veto_reason", "all_gate_results", "decision", "market_snapshot"]:
        assert f in req, f"field wajib {f} hilang dari schema"
    gates = s["properties"]["all_gate_results"]["properties"]
    assert set(gates["b1_news"]["enum"]) == {
        "PASS", "NEWS_EVENT_ACTIVE", "NEWS_PROVIDER_DOWN", "NEWS_DATA_STALE",
        "NEWS_CALENDAR_UNAVAILABLE"}
    assert set(gates["b7_risk"]["enum"]) == {"PASS", "FAIL:cap", "FAIL:cooldown", "FAIL:stop_bounds"}
