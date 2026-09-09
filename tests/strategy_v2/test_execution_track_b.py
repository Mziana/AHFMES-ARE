"""Track B (B2–B7) — kontrak eksekusi shadow-only.

Dijaga di sini (kontrak final, disepakati owner & reviewer):
- Real order = OFF arsitektural: STRUKTURAL TEST membuktikan modul Track B
  tidak mengimpor MT5ExecutionGateway; ShadowGateway satu-satunya gateway.
- CSK satu kebenaran: budget per profil via csk_risk_budget_for(); profil
  tak dikenal -> fail-closed; slot/daily-loss/risk cap di-enforce adapter.
- State machine: transisi ilegal -> ValueError.
- Kill switch + flatten_all() di gateway layer.
- Latency: hard-fail >= 1 bar; viability P99 decision->ack <= 5s.
- Parity: toleransi max(1 point, tick_size).
- Genealogy: hipotesis baru wajib parent; retro-link ditandai inferred.
"""
import ast
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from are.safety import CapitalSafetyKernel, SafetyLimits  # noqa: E402
from strategy_v2 import execution as ex  # noqa: E402
from strategy_v2 import genealogy as gen  # noqa: E402


# ── Struktural: tidak ada gateway order-real di dependency graph Track B ────
def test_no_real_gateway_import_in_track_b_modules():
    for mod_path in ("strategy_v2/execution.py", "strategy_v2/genealogy.py"):
        tree = ast.parse(open(mod_path, encoding="utf-8").read())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for n in names:
                assert "mt5_gateway" not in n.lower(), \
                    f"{mod_path} mengimpor gateway order-real: {n} (violasi WAJIB #1)"


def test_shadow_gateway_is_only_gateway_symbol():
    src = open("strategy_v2/execution.py", encoding="utf-8").read()
    assert "class ShadowGateway" in src
    assert "MT5ExecutionGateway" not in src
    assert "order_send" not in src.lower()


# ── B2: adapter + CSK ────────────────────────────────────────────────────────
def _record(decision="BUY", sl=300.0, tp=380.0, lot=0.07, ts=1_700_000_000):
    return {"evaluation_timestamp": ts, "signal_ts": ts - 300, "decision": decision,
            "sl_points": sl, "tp_points": tp, "lot": lot,
            "config_hash": "cfg", "dataset_hash": "ds",
            "strategy_version": "strategy_v2/0.4.1-c1", "hypothesis_registry_id": "reg-v2",
            "quality_score": {"final_score": 63.2}}


class TestAdapter:
    def test_unknown_profile_fails_closed(self):
        csk = CapitalSafetyKernel(SafetyLimits())
        with pytest.raises(ex.CskProfileBudgetDenied):
            ex.csk_risk_budget_for(csk, "PROFILE_FANTASI")

    def test_valid_record_becomes_intent(self):
        csk = CapitalSafetyKernel(SafetyLimits())
        ad = ex.DecisionAdapter(csk)
        it = ad.submit(_record(), "MICRO_V2")
        assert it is not None and it.direction == "BUY" and it.profile_id == "MICRO_V2"
        assert it.provenance["quality_score"] == 63.2

    def test_slot_full_rejects(self):
        csk = CapitalSafetyKernel(SafetyLimits())
        ad = ex.DecisionAdapter(csk)
        assert ad.submit(_record(), "MICRO_V2") is not None
        st = ad.state["MICRO_V2"]
        st.open_positions = 1  # slot penuh
        it = ad.submit(_record(ts=1_700_000_300), "MICRO_V2")
        assert it is None and ad.rejections[-1]["reason"] == "PROFILE_SLOT_FULL"

    def test_daily_loss_cap_rejects(self):
        csk = CapitalSafetyKernel(SafetyLimits())
        ad = ex.DecisionAdapter(csk)
        ad.state["MICRO_V2"] = ex.ProfileRuntimeState(daily_loss_usd=90.0)
        it = ad.submit(_record(), "MICRO_V2")
        assert it is None and ad.rejections[-1]["reason"] == "PROFILE_DAILY_LOSS_CAP"

    def test_invalid_decision_rejected_with_log(self):
        csk = CapitalSafetyKernel(SafetyLimits())
        ad = ex.DecisionAdapter(csk)
        assert ad.submit(_record(decision="WAIT"), "MICRO_V2") is None
        assert ad.rejections[-1]["reason"] == "ADAPTER_INVALID"

    def test_negative_sl_fails_closed(self):
        csk = CapitalSafetyKernel(SafetyLimits())
        ad = ex.DecisionAdapter(csk)
        assert ad.submit(_record(sl=-5), "MICRO_V2") is None
        assert ad.rejections[-1]["reason"] == "ADAPTER_INVALID"


# ── B3: state machine ───────────────────────────────────────────────────────
class TestStateMachine:
    def test_happy_path(self):
        sm = ex.ExecutionStateMachine("I-x")
        for nxt in ("INTENT_VALIDATED", "CSK_CHECKED", "SUBMITTED", "ACKNOWLEDGED",
                    "FILLED", "MANAGING", "CLOSED"):
            sm.transition(nxt)
        assert sm.is_terminal()

    def test_illegal_transition_raises(self):
        sm = ex.ExecutionStateMachine("I-y")
        with pytest.raises(ValueError):
            sm.transition("FILLED")  # IDLE -> FILLED ilegal

    def test_unknown_state_raises(self):
        sm = ex.ExecutionStateMachine("I-z")
        with pytest.raises(ValueError):
            sm.transition("MOON")


# ── B4: shadow gateway ──────────────────────────────────────────────────────
def _bars():
    return [{"time": 1_700_000_000 + i * 300, "open": 2400.0 + i, "high": 2401 + i,
             "low": 2399 + i, "close": 2400.5 + i, "volume": 100} for i in range(20)]


class TestShadowGateway:
    def test_submit_fills_next_bar_open(self):
        gw = ex.ShadowGateway(_bars())
        csk = CapitalSafetyKernel(SafetyLimits())
        ad = ex.DecisionAdapter(csk)
        it = ad.submit(_record(ts=1_700_000_000), "MICRO_V2")
        fill = gw.submit(it)
        assert fill.fill_ts == 1_700_000_000 + 300
        assert abs(fill.fill_price - 2401.0) < 1e-9  # open bar berikutnya

    def test_kill_switch_blocks_submit(self):
        gw = ex.ShadowGateway(_bars(), kill_switch_active=True)
        csk = CapitalSafetyKernel(SafetyLimits())
        it = ex.DecisionAdapter(csk).submit(_record(), "MICRO_V2")
        with pytest.raises(RuntimeError):
            gw.submit(it)

    def test_flatten_all_closes_and_arms_kill_switch(self):
        gw = ex.ShadowGateway(_bars())
        csk = CapitalSafetyKernel(SafetyLimits())
        ad = ex.DecisionAdapter(csk)
        for k in range(3):
            it = ad.submit(_record(ts=1_700_000_000 + k * 300), "MICRO_V2")
            gw.submit(it)
        res = gw.flatten_all("TEST")
        assert res["flattened"] == 3 and res["kill_switch_active"] is True
        assert not gw.open_shadows
        with pytest.raises(RuntimeError):
            csk_intent = None  # noqa: F841
            gw.submit(ad.submit(_record(ts=1_700_000_900), "MICRO_V2"))

    def test_flatten_log_recorded(self):
        gw = ex.ShadowGateway(_bars())
        gw.flatten_all("AUDIT")
        assert gw.flatten_log[-1]["reason"] == "AUDIT"


# ── B6: latency ─────────────────────────────────────────────────────────────
class TestLatency:
    def test_viability_pass_and_fail(self):
        good = [{"decision": 0.01, "risk": 0.01, "submit": 0.01, "ack": 0.02, "fill": 0.05}] * 20
        rep = ex.latency_report(good)
        assert rep["validity"]["viability_gate"] == "PASS"
        bad = [{"decision": 2.0, "risk": 1.0, "submit": 1.0, "ack": 2.0, "fill": 1.0}] * 20
        rep2 = ex.latency_report(bad)
        assert rep2["validity"]["viability_gate"] == "FAIL"

    def test_hard_fail_counts_over_one_bar(self):
        mix = [{"decision": 0, "risk": 0, "submit": 0, "ack": 0, "fill": 0}] * 9 + \
              [{"decision": 400.0, "risk": 0, "submit": 0, "ack": 0, "fill": 0}]
        rep = ex.latency_report(mix)
        assert rep["validity"]["samples_over_hard_limit"] == 1
        assert rep["validity"]["hard_fail_bar_limit_s"] == 300

    def test_percentile_shapes(self):
        rep = ex.latency_report([{"decision": 0.1, "risk": 0.1, "submit": 0.1,
                                  "ack": 0.1, "fill": 0.1}] * 5)
        for seg, v in rep["segments"].items():
            assert set(v) == {"p50", "p95", "p99", "max"}


# ── B5: parity ──────────────────────────────────────────────────────────────
class TestParity:
    def test_identical_sequences_match(self):
        a = [{"signal_ts": 1, "direction": "BUY", "lot": 0.07, "entry": 2400.0}]
        b = [{"signal_ts": 1, "direction": "BUY", "lot": 0.07, "entry": 2400.005}]
        assert ex.parity_check(a, b, tick_size=0.01)["match"] is True

    def test_price_beyond_tolerance_mismatches(self):
        a = [{"signal_ts": 1, "direction": "BUY", "lot": 0.07, "entry": 2400.0}]
        b = [{"signal_ts": 1, "direction": "BUY", "lot": 0.07, "entry": 2400.5}]
        rep = ex.parity_check(a, b, tick_size=0.01)
        assert rep["match"] is False and rep["mismatches"][0]["diffs"]["entry"][1] == 2400.5

    def test_count_mismatch_detected(self):
        a = [{"signal_ts": 1, "direction": "BUY", "lot": 0.07}]
        b = []
        rep = ex.parity_check(a, b)
        assert rep["match"] is False and "beda" in rep["reason"]

    def test_invalid_sample_excluded_from_parity(self):
        a = [{"signal_ts": 1, "direction": "BUY", "lot": 0.07, "entry": 2400.0}]
        b = [{"signal_ts": 1, "direction": "BUY", "lot": 0.07, "entry": 2400.0,
              "parity_valid": False}]
        rep = ex.parity_check(a, b)
        assert rep["match"] is False  # b terbuang -> count beda


# ── B7: genealogy ───────────────────────────────────────────────────────────
class TestGenealogy:
    def test_new_hypothesis_requires_parents(self):
        with pytest.raises(gen.GenealogyValidationError):
            gen.new_hypothesis("H-X", [], "stmt", "reason", ["d"], "p", "cfg")

    def test_new_hypothesis_full_schema(self):
        h = gen.new_hypothesis("H-TEST-99", ["H-SCORE-01"], "stmt", "reason",
                               ["A3 artifact"], "2026-04-23..07-28", "cfghash")
        for f in gen.GENEALOGY_FIELDS:
            assert f in h
        assert h["retroactive"] is False and h["confidence"] == "exact"
        assert h["parent_id"] == ["H-SCORE-01"]

    def test_retro_links_marked_inferred(self):
        view = gen.genealogy_view()
        e = view["genealogy_entries"]["H-SCORE-01"]
        assert e["retroactive"] is True and e["confidence"] == "inferred"
        assert set(e["parent_id"]) == {"H-REGIME-SLOPE-02", "H-LOC-02", "H-ATR-01"}

    def test_view_covers_whole_registry(self):
        view = gen.genealogy_view()
        reg = json.load(open(gen.REGISTRY_PATH, encoding="utf-8"))
        assert set(view["genealogy_entries"].keys()) == set(reg["hypotheses"].keys())
