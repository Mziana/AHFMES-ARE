"""P2b — Invariant + Adversarial Mutation Suite (Pagar 5).

Setiap invariant diuji DUA arah: happy path + mutasi jahat. Sistem harus
GAGAL DENGAN BENAR (rejection eksplisit / error terdefinisi), bukan pass diam.
"""
import copy
import json
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import gates, registry, zones as Z
from strategy_v2.replay import build_funnel, run_decision_replay, run_execution_replay

M5_START = 1788739200
M15_START = 1788739200


def make_m5(n, base=4400.0, drift=0.02, vol=100):
    return [{"time": M5_START + i * 300, "open": base + drift * i, "high": base + drift * i + 1.2,
             "low": base + drift * i - 1.2, "close": base + drift * i + 0.4, "volume": vol + (i % 5)}
            for i in range(n)]


def make_m15(n, base=4400.0, drift=0.08):
    out = []
    for i in range(n):
        c = base + drift * i
        out.append({"time": M15_START + i * 900, "open": c, "high": c + 0.5, "low": c - 0.5,
                    "close": c, "volume": 400})
    return out


PROFILE = registry.load_profile("MICRO")
REG = registry.load_hypothesis_registry()


def replay(m5, m15, profile=PROFILE, calendar=None):
    cfg = {"config_hash": "a" * 64, "dataset_hash": "b" * 64, "balance": 1000.0, "spread_points": None}
    return run_decision_replay(m5, m15, profile, REG,
                               calendar or {"status": "empty", "events": [], "fetched_at": 0}, cfg)


# ── 1. NO-LOOKAHEAD GLOBAL (Pagar 2) ─────────────────────────────────────────

def test_inv1_no_lookahead_future_candle_does_not_change_past():
    """Inject future candle → hasil evaluasi T TIDAK berubah."""
    m5, m15 = make_m5(200), make_m15(200)
    base = replay(m5, m15)
    T_idx = 100
    T = int(m5[T_idx]["time"]) + 300
    # hasil pada T dari dataset penuh
    rec_full = next(r for r in base if r["evaluation_timestamp"] == T)
    # hasil pada T dari slice murni [0..T]
    m5_s = [b for b in m5 if int(b["time"]) + 300 <= T]
    m15_s = [b for b in m15 if int(b["time"]) + 900 <= T]
    rec_slice = replay(m5_s, m15_s)[-1]
    assert rec_full["all_gate_results"] == rec_slice["all_gate_results"]
    assert rec_full["decision"] == rec_slice["decision"]
    # sekarang inject candle masa depan → hasil pada T tetap identik
    fut = make_m5(60, base=9999.0, drift=5.0)
    for b in fut:
        b["time"] += int(m5[-1]["time"]) + 300 - M5_START + 300
    mixed = replay(m5 + fut, m15)
    rec_mixed = next(r for r in mixed if r["evaluation_timestamp"] == T)
    assert rec_mixed["all_gate_results"] == rec_full["all_gate_results"]
    assert rec_mixed["decision"] == rec_full["decision"]


def test_inv1_zones_pure_and_slice_sensitive():
    bars = make_m15(300)
    bars[250]["high"] = 9999.0  # puncak besar di masa depan relatif T=bar 100
    z_before = Z.build_zones(bars[:101])
    z_recompute = Z.build_zones(bars[:101])
    assert z_before == z_recompute                       # pure: identik kapan pun
    z_after = Z.build_zones(bars[:251])
    assert z_after != z_before                            # input > T → BERBEDA (bukti slice penting)


# ── 2. CLOSED-BAR SEMANTICS ──────────────────────────────────────────────────

def test_inv2_forming_bar_rejected():
    cfg = {"now_ts": M5_START + 300 * 10, "calendar": {"status": "empty"}}
    bars = make_m5(11)
    # bar terakhir belum closed pada now_ts (open + 300 > now)
    bars[-1]["time"] = M5_START + 300 * 10 + 60
    assert gates.b5_trigger(bars, "BUY_ONLY", cfg) == "FAIL:forming_bar"
    # dengan slicing benar, bar forming tidak pernah masuk slice — bukti via layer A
    cfg2 = {"now_ts": M5_START + 300 * 10, "layer_a": {}}
    assert gates.layer_a_data_integrity(bars[:-1], None, cfg2) == "DATA_VALID"


# ── 3. EXECUTION TIMING ──────────────────────────────────────────────────────

def test_inv3_execution_at_next_bar_open_not_earlier():
    m5 = make_m5(220)
    records = replay(m5, make_m15(220))
    records[50]["decision"] = "BUY"
    records[50]["sl_points"] = 150.0
    records[50]["tp_points"] = 150.0
    records[50]["lot"] = 0.02
    ex = run_execution_replay(records, m5, PROFILE)
    t = ex["trades"][0]
    assert t["entry_ts"] == records[50]["evaluation_timestamp"]  # open bar T+1 sisi sinyal = bar dgn open ts == T
    entry_bar = next(b for b in m5 if b["time"] == t["entry_ts"])
    assert t["entry"] == entry_bar["open"] + ex["spread_model"]["entry_spread_points"] * 0.01


# ── 4. DETERMINISM ───────────────────────────────────────────────────────────

def _no_wallclock_calls(path: Path) -> list:
    """AST check: tidak ada pemanggilan now()/time.time()/datetime.now/utcnow."""
    import ast
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if name in ("now", "utcnow", "time", "monotonic"):
                bad.append(f"{path.name}:{node.lineno}:{name}")
    return bad


def test_inv9_no_wallclock_in_decision_path():
    """Pagar 4 — tidak ada now()/time.time() di seluruh jalur decision."""
    pkg = Path(registry.PKG_DIR)
    bad = []
    for fname in ["gates.py", "zones.py", "replay.py", "costs.py"]:
        bad += _no_wallclock_calls(pkg / fname)
    assert bad == [], f"pemanggilan wall-clock ditemukan: {bad}"


def test_inv4_replay_twice_bit_identical():
    m5, m15 = make_m5(180), make_m15(180)
    r1 = replay(m5, m15)
    r2 = replay(m5, m15)
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)


# ── 5. NEWS REASON CODES ─────────────────────────────────────────────────────

def test_inv5_news_codes_separate_all_veto():
    policy = PROFILE["news"]
    now = M5_START + 300 * 100
    codes = ["NEWS_EVENT_ACTIVE", "NEWS_PROVIDER_DOWN", "NEWS_DATA_STALE", "NEWS_CALENDAR_UNAVAILABLE"]
    seen = set()
    ev = {"ts": now, "impact": "high", "currency": "USD"}
    seen.add(gates.b1_news(now, {"status": "ok", "information_available_at": now - 60, "events": [dict(ev)]}, policy))
    seen.add(gates.b1_news(now, {"status": "down", "events": []}, policy))
    seen.add(gates.b1_news(now, {"status": "ok", "information_available_at": now - 5 * 3600, "events": [dict(ev)]}, policy))
    seen.add(gates.b1_news(now, {"status": "empty", "events": []}, policy))
    assert seen == set(codes)
    # semua → WAIT di decide (NO_NEW_ENTRY)
    for c in codes:
        d = {"all_gate_results": {"b1_news": c, "b2_session": "PASS", "b3_regime": "PASS:BUY_ONLY",
                                  "b4_location": "PASS:x", "b5_trigger": "PASS:hammer",
                                  "b6_volume": "PASS", "b7_risk": "PASS"},
             "bias": "BUY_ONLY", "trigger": {"pattern": "hammer", "bar_ts": 1}}
        fv, dec = gates.decide(d)
        assert fv == f"B1:{c}" and dec == "WAIT"


# ── 6. LAYER SEPARATION ──────────────────────────────────────────────────────

def test_inv6_data_invalid_not_in_strategy_stats():
    m5, m15 = make_m5(120), make_m15(120)
    m5[10]["close"] = float("nan")  # NaN di histori → semua T ≥ bar10 invalid
    records = replay(m5, m15)
    invalid = [r for r in records if r["layer_a"] != "DATA_VALID"]
    assert invalid, "harus ada DATA_INVALID"
    funnel = build_funnel(records, None)
    assert funnel["data_invalid"] == len(invalid)
    assert funnel["layer_b_evaluated"] == len(records) - len(invalid)
    # veto strategi hanya dihitung dari valid
    veto_total = sum(1 for r in records if r["layer_a"] == "DATA_VALID" and r["first_veto_reason"])
    assert sum(funnel["veto_by_gate"].values()) == veto_total


# ── 7. VOLUME BASELINE GUARD ─────────────────────────────────────────────────

def test_inv7_volume_baseline_guards():
    cfg = {"volume_gate_enabled": True, "vol_ratio": 1.2, "vol_baseline_bars": 5}
    bars = make_m5(10)
    bars[-1]["volume"] = 200
    assert gates.b6_volume(bars, cfg) == "PASS"
    # exclude-self: signal bar raksasa tidak mengangkat baseline
    bars[-1]["volume"] = 100000
    assert gates.b6_volume(bars, cfg) == "PASS"
    # zero baseline
    for b in bars[-6:-1]:
        b["volume"] = 0
    assert gates.b6_volume(bars, cfg) == "FAIL:baseline_invalid"
    # missing
    for b in bars:
        b["volume"] = None
    assert gates.b6_volume(bars, cfg) == "FAIL:baseline_invalid"


# ── 8. DIAGNOSTIC ≠ OPERATIONAL ──────────────────────────────────────────────

def test_inv8_full_evaluation_does_not_change_decision():
    cfg = {"now_ts": M5_START + 300 * 60, "calendar": {"status": "empty"}, "layer_a": {}}
    d = gates.evaluate_all({"m5": make_m5(60), "m15": make_m15(300)}, PROFILE, cfg, {})
    snap1 = json.dumps(d, sort_keys=True)
    fv1, dec1 = gates.decide(d)
    fv2, dec2 = gates.decide(d)
    assert (fv1, dec1) == (fv2, dec2)
    assert json.dumps(d, sort_keys=True) == snap1  # decide pure — tidak mengubah diagnostic


# ── 9. ADVERSARIAL MUTATION SUITE ────────────────────────────────────────────

def test_adv_future_candle_inserted_mid_dataset():
    m5, m15 = make_m5(200), make_m15(200)
    base = replay(m5, m15)
    # sisipkan candle "dari masa depan" di tengah (timestamp mundur, harga ekstrem)
    mutant = copy.deepcopy(m5)
    mutant.insert(50, {"time": M5_START + 300 * 50, "open": 1.0, "high": 99999.0,
                       "low": 0.5, "close": 50000.0, "volume": 10**9})
    recs = replay(mutant, m15)
    # duplicate ts → Layer A harus menolak, bukan diam-diam menghitung
    invalid = [r for r in recs if r["layer_a"] == "DATA_INVALID:duplicate_ts"]
    assert invalid


def test_adv_historical_candle_modified_changes_eval():
    m5, m15 = make_m5(200), make_m15(200)
    base = replay(m5, m15)
    mutant = copy.deepcopy(m5)
    mutant[150]["close"] = 9999.0  # modifikasi histori → evaluasi SETELAH bar itu berubah
    recs = replay(mutant, m15)
    T = int(m5[160]["time"]) + 300
    b = next(r for r in base if r["evaluation_timestamp"] == T)
    m = next(r for r in recs if r["evaluation_timestamp"] == T)
    assert m["market_snapshot"] != b["market_snapshot"]  # histori memang mempengaruhi T>modifikasi (bukan lookahead — bar 150 < T)


def test_adv_missing_and_nan_data_fail_closed():
    m5 = make_m5(120)
    m5[60].pop("volume")
    recs = replay(m5, make_m15(120))
    assert any(r["layer_a"] == "DATA_INVALID:volume_missing" for r in recs)
    m5b = make_m5(120)
    m5b[60]["close"] = float("nan")
    recs = replay(m5b, make_m15(120))
    assert any(r["layer_a"] == "DATA_INVALID:nan" for r in recs)


def test_adv_duplicate_timestamp_rejected():
    m5 = make_m5(120)
    m5[30]["time"] = m5[29]["time"]
    recs = replay(m5, make_m15(120))
    assert any(r["layer_a"] == "DATA_INVALID:duplicate_ts" for r in recs)


def test_adv_extreme_spread_rejected():
    m5 = make_m5(120)
    cfg = {"config_hash": "a" * 64, "dataset_hash": "b" * 64, "balance": 1000.0,
           "spread_points": 100000}
    records = run_decision_replay(m5, make_m15(120), PROFILE, REG,
                                  {"status": "empty", "events": [], "fetched_at": 0}, cfg)
    assert any(r["layer_a"] == "DATA_INVALID:spread_extreme" for r in records)


def test_adv_stale_data_rejected():
    m5 = make_m5(120)
    cfg = {"config_hash": "a" * 64, "dataset_hash": "b" * 64, "balance": 1000.0,
           "spread_points": None, "layer_a": {"max_staleness_bars": 3}}
    # now_ts jauh di depan bar terakhir → stale. Simulasi: dataset dipotong
    # sementara now_ts tetap = close bar ke-500.
    records = []
    for bar in m5:
        T = int(bar["time"]) + 300
        slice_ = [b for b in m5 if int(b["time"]) + 300 <= T - 20 * 300]  # data basi 20 bar
        if not slice_:
            continue
        c = dict(cfg)
        c["now_ts"] = T
        records.append((T, gates.layer_a_data_integrity(slice_, None, c)))
    assert any(s == "DATA_INVALID:stale" for _, s in records)


def test_adv_config_change_mid_run_new_identity():
    """Config berubah mid-run → config_hash berubah → identity baru (Pagar 1)."""
    p1 = registry.compute_config_hash(PROFILE, REG)
    p2 = copy.deepcopy(PROFILE)
    p2["risk"]["cooldown_minutes"] = 99
    p2_hash = registry.compute_config_hash(p2, REG)
    assert p1 != p2
    # dan replay dengan profil berbeda menandai identity baru di record
    m5, m15 = make_m5(60), make_m15(60)
    cfg = {"config_hash": p2_hash, "dataset_hash": "b" * 64, "balance": 1000.0, "spread_points": None}
    recs = run_decision_replay(m5, m15, p2, REG, {"status": "empty", "events": [], "fetched_at": 0}, cfg)
    assert all(r["config_hash"] == p2_hash for r in recs)
    assert recs[0]["config_hash"] != p1


def test_adv_shuffled_input_order_detected():
    """Urutan input diacak → Layer A harus menolak (urutan bukan bebas)."""
    m5 = make_m5(120)
    rng = random.Random(42)
    shuffled = m5[:]
    rng.shuffle(shuffled)
    cfg = {"config_hash": "a" * 64, "dataset_hash": "b" * 64, "balance": 1000.0,
           "spread_points": None, "layer_a": {}}
    status = gates.layer_a_data_integrity(shuffled, None, {**cfg, "now_ts": M5_START + 300 * 200})
    assert status.startswith("DATA_INVALID")


# ── 10. FUNNEL COMPLETENESS ──────────────────────────────────────────────────

def test_inv10_funnel_complete_keys():
    records = replay(make_m5(150), make_m15(150))
    ex = run_execution_replay(records, make_m5(150), PROFILE)
    f = build_funnel(records, ex)
    required = ["evaluation_opportunities", "data_invalid", "data_invalid_by_reason",
                "layer_b_evaluated", "veto_by_gate", "veto_by_first_reason",
                "final_signals", "executed_trades", "rejected_executions",
                "gross_expectancy_usd", "total_costs_usd", "net_expectancy_usd"]
    for k in required:
        assert k in f, f"funnel kurang {k}"
    assert f["evaluation_opportunities"] == f["data_invalid"] + f["layer_b_evaluated"]
