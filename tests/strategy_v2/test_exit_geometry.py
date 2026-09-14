"""Paket Exit Geometry MICRO (owner 2026-09-11) — kontrak D + E.

D_exit (EXIT-D-01): entry parity A_base, exit diganti:
  D1 TP cap 600 pts   — M1 tidak diberi target 1.4×ATR-M5 saat ATR-M5 membesar
  D2 clamp struktur   — TP berhenti 0.25×ATR sebelum swing berlawanan M5/M15;
                        sisa TP < 100 pts → REJECT (fail-closed, tanpa order)
  D4 RSI-burn         — pola searah bias + RSI-M1 jenuh (≥60 BULL / ≤40 BEAR)
                        → TP × 0.7 (sisa-bakar RSI sedikit → target lebih pendek)
  D5 early exit       — posisi profit + pembalikan (pola lawan ATAU momentum
                        habis) + konfirmasi (EMA9/21 cross ATAU RSI patah 50)
E_atr_m1 (EXIT-E-01): geometri 0.9/1.4 × ATR-M1 — skala ikut karakter TF
  eksekusi (jawaban fundamental utk "ATR-M5 membesar").

Semua diuji SHADOW (tanpa order); arm live & kandidat A/B/C tidak boleh
berubah (bit-identik). Modul exit_geometry WAJIB pure (tanpa I/O).
"""
import ast
import inspect
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from strategy_v2 import candle_scoring as CS  # noqa: E402
from strategy_v2 import exit_geometry as EG  # noqa: E402
from strategy_v2 import micro_v2 as MV  # noqa: E402
from strategy_v2 import shadow_ab as SH  # noqa: E402


# ── fixtures ────────────────────────────────────────────────────────────────
def mk_bars(n, o0, step, rng, body, v=500, t0=1_700_000_000, tf=300):
    """Bar trending: open naik `step` per bar, range `rng`, body `body`.
    Body/range < 0.85 → bukan marubozu; step > 0 → tanpa swing fraktal."""
    out = []
    o = float(o0)
    for i in range(n):
        h, l, c = o + rng, o, o + body
        out.append({"time": t0 + i * tf, "open": o, "high": h, "low": l,
                    "close": c, "volume": v})
        o += step
    return out


def mk_flat(n, o=100.0, rng=8.0, c_off=0.2, v=500, t0=1_700_000_000, tf=300):
    """Bar flat (plateau) → SEMUA bar interior jadi swing high/low (>= fraktal)."""
    out = []
    for i in range(n):
        c = o + c_off
        out.append({"time": t0 + i * tf, "open": o, "high": o + rng,
                    "low": o, "close": c, "volume": v})
    return out


def mk_m1_rising_burn(n=30, o0=85.5):
    """M1 rising (RSI tinggi, >60) + bar terakhir marubozu bull → burn case D4."""
    bars = mk_bars(n, o0, step=0.5, rng=1.0, body=0.5, tf=60)
    b = bars[-1]
    o = b["close"] - 0.5
    bars[-1] = {"time": b["time"], "open": o, "high": o + 0.9, "low": o - 0.05,
                "close": o + 0.85, "volume": 900}
    return bars


def mk_m1_neutral(n=30):
    """M1 flat bergantian ±0.01 → RSI ~50 (tanpa burn)."""
    out = []
    o = 100.0
    for i in range(n):
        c = o + (0.01 if i % 2 == 0 else -0.01)
        out.append({"time": 1_700_000_000 + i * 60, "open": o,
                    "high": o + 0.15, "low": o - 0.15, "close": c, "volume": 400})
        o = c
    return out


def mk_m1_reversal_after_rise(n=30):
    """M1 naik, koreksi turun, lalu 2 bar bull kecil di akhir + bar terakhir
    bearish_engulfing menelan bar-2 → pembalikan terkonfirmasi (D5)."""
    bars = mk_bars(n, 95.0, step=0.4, rng=0.8, body=0.3, tf=60)
    for i in range(12):  # koreksi turun
        b = bars[-1]
        o = b["close"]
        bars.append({"time": b["time"] + 60, "open": o, "high": o + 0.1,
                     "low": o - 0.35, "close": o - 0.3, "volume": 400})
    # 2 bar bull kecil sebelum bar pola (b2 engulfing harus bull)
    for i in range(2):
        b = bars[-1]
        o = b["close"]
        bars.append({"time": b["time"] + 60, "open": o, "high": o + 0.45,
                     "low": o - 0.05, "close": o + 0.4, "volume": 400})
    # bar terakhir: bearish engulfing menelan body b2 (bull)
    b2 = bars[-2]
    o3 = b2["close"] + 0.05
    bars[-1] = {"time": b2["time"] + 60, "open": o3, "high": o3 + 0.05,
                "low": o3 - 1.2, "close": o3 - 1.1, "volume": 800}
    assert b2["close"] > b2["open"], "fixture: bar-2 harus bull"
    return bars


# ── 1. modul pure (struktural) ───────────────────────────────────────────────
def test_exit_geometry_is_pure_module():
    tree = ast.parse(open("strategy_v2/exit_geometry.py", encoding="utf-8").read())
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
            mods.update(f"{node.module}.{a.name}" for a in node.names)
    allowed = {"__future__", "__future__.annotations", "typing", "typing.Optional",
               "bisect", "strategy_v2", "strategy_v2.candle_scoring",
               "strategy_v2.simple_variants", "strategy_v2.micro_v2"}
    assert mods <= allowed, f"exit_geometry mengimpor modul di luar whitelist: {mods - allowed}"


# ── 2. D1: TP cap 600 pts ────────────────────────────────────────────────────
def test_d1_tp_capped_at_600pts():
    """ATR-M5 = 8 USD → 1.4×ATR = 1120 pts, TAPI cap → TP 600 pts."""
    m5 = mk_bars(30, 92.0, step=0.5, rng=8.0, body=3.0)   # rising → tanpa swing
    m1 = mk_m1_neutral()
    entry = m5[-1]["close"]
    plan = EG.plan_exit_d("BULL", entry, m1, m5, None)
    assert plan["ok"], plan
    assert plan["sl_pts"] == 720.0, plan           # 0.9×ATR-M5 TIDAK berubah
    assert plan["tp_pts"] == 600.0, plan           # cap aktif
    assert abs(plan["tp"] - (entry + 6.0)) < 1e-9


def test_d1_no_cap_when_atr_small():
    """ATR-M5 kecil → 1.4×ATR < 600 pts → TP ATR penuh (cap pasif)."""
    m5 = mk_bars(30, 98.0, step=0.1, rng=1.5, body=0.4)   # ATR = 1.5
    m1 = mk_m1_neutral()
    entry = m5[-1]["close"]
    plan = EG.plan_exit_d("BULL", entry, m1, m5, None)
    assert plan["ok"], plan
    assert plan["tp_pts"] == 210.0, plan           # 1.4 × 1.5 USD = 210 pts


# ── 3. D2: clamp struktur + reject ───────────────────────────────────────────
def test_d2_tp_clamped_to_swing():
    """Swing berlawanan 104, ATR 4 → TP berhenti di 104 − 0.25×4 = 103.
    (Cap 1.4×ATR = 560 pts tidak aktif di sini; clamp yang memotong.)
    Entry 100.2 → sisa 280 pts ≥ 100 → entry sah, TP dipotong."""
    m5 = mk_flat(30, o=100.0, rng=4.0, c_off=0.2)   # swing high = 104.0, ATR = 4
    m1 = mk_m1_neutral()
    entry = m5[-1]["close"]                          # 100.2
    plan = EG.plan_exit_d("BULL", entry, m1, m5, None)
    assert plan["ok"], plan
    assert abs(plan["tp"] - 103.0) < 1e-9, plan      # 104 − 0.25×4
    assert plan["tp_pts"] == 280.0, plan


def test_d2_reject_when_tp_remainder_below_100pts():
    """Swing 101.5, ATR 1.5 → limit 101.5 − 0.375 = 101.125; entry 100.2 →
    sisa 92.5 pts < 100 → REJECT (fail-closed, tanpa order shadow)."""
    m5 = mk_flat(30, o=100.0, rng=1.5, c_off=0.2)    # swing high 101.5, ATR 1.5
    m1 = mk_m1_neutral()
    entry = m5[-1]["close"]                          # 100.2
    plan = EG.plan_exit_d("BULL", entry, m1, m5, None)
    assert not plan["ok"], plan
    assert "tp_after_structure" in plan["reject_reason"], plan


# ── 4. D4: RSI-burn ──────────────────────────────────────────────────────────
def test_d4_burn_shortens_tp_when_rsi_high_and_pattern_aligned():
    """Bias BULL + marubozu bull M1 + RSI-M1 > 60 → TP = cap 600 × 0.7 = 420.
    ATR-M5 = 8 (cap aktif) → tanpa burn TP 600; burn → 420. SL tetap 720."""
    m5 = mk_bars(30, 92.0, step=0.5, rng=8.0, body=3.0)
    m1 = mk_m1_rising_burn()
    entry = m5[-1]["close"]
    rsi1 = CS.rsi([b["close"] for b in m1], 14)
    assert rsi1 is not None and rsi1 > 60, rsi1
    plan = EG.plan_exit_d("BULL", entry, m1, m5, None)
    assert plan["ok"], plan
    assert plan["burned"] is True, plan
    assert plan["tp_pts"] == 420.0, plan             # 600 × 0.7
    assert plan["sl_pts"] == 720.0, plan             # SL tidak tersentuh burn


def test_d4_no_burn_when_rsi_neutral():
    m5 = mk_bars(30, 92.0, step=0.5, rng=8.0, body=3.0)
    m1 = mk_m1_neutral()
    plan = EG.plan_exit_d("BULL", m5[-1]["close"], m1, m5, None)
    assert plan["ok"], plan
    assert plan["burned"] is False, plan
    assert plan["tp_pts"] == 600.0, plan


# ── 5. D5: early exit ────────────────────────────────────────────────────────
def test_d5_early_exit_on_reversal_with_momentum_break():
    bars = mk_m1_reversal_after_rise()
    entry = 99.0                                     # posisi profit (close < entry utk SELL... )
    # pakai BUY dengan entry di bawah harga sekarang (profit):
    entry = bars[-1]["close"] - 1.0
    res = EG.early_exit_check("BUY", entry, bars)
    assert res["exit"] is True, res
    assert "early-exit" in res["reason"], res


def test_d5_no_early_exit_when_position_losing():
    bars = mk_m1_reversal_after_rise()
    entry = bars[-1]["close"] + 1.0                  # BUY rugi → jangan tutup
    res = EG.early_exit_check("BUY", entry, bars)
    assert res["exit"] is False, res
    assert "profit" in res["reason"], res


def test_d5_no_early_exit_without_reversal_or_exhaustion():
    bars = mk_bars(30, 95.0, step=0.4, rng=0.8, body=0.3, tf=60)  # naik terus
    entry = bars[-1]["close"] - 1.0                  # BUY profit
    res = EG.early_exit_check("BUY", entry, bars)
    assert res["exit"] is False, res


# ── 6. E: geometri ATR-M1 ────────────────────────────────────────────────────
def test_e_plan_uses_atr_m1_scale():
    m1 = mk_bars(30, 98.0, step=0.1, rng=2.0, body=0.5, tf=60)   # ATR-M1 = 2
    entry = m1[-1]["close"]
    plan = EG.exit_plan_atr_m1("BULL", entry, m1)
    assert plan["ok"], plan
    assert plan["sl_pts"] == 180.0, plan             # 0.9 × 2.0 USD
    assert plan["tp_pts"] == 280.0, plan             # 1.4 × 2.0 USD
    assert abs(plan["sl"] - (entry - 1.8)) < 1e-9
    assert abs(plan["tp"] - (entry + 2.8)) < 1e-9


def test_e_reject_without_data():
    plan = EG.exit_plan_atr_m1("BULL", 100.0, [])
    assert not plan["ok"]
    assert "DATA_INVALID" in plan["reject_reason"]


# ── 7. Kandidat shadow D_exit & E_atr_m1 (A/B/C bit-identik) ─────────────────
def test_shadow_candidates_d_e_exist_with_entry_parity():
    a = SH.CANDIDATES["A_base"]
    d = SH.CANDIDATES["D_exit"]
    e = SH.CANDIDATES["E_atr_m1"]
    for c in (d, e):
        assert c["vol_min"] == a["vol_min"], "parity entry: VOL_MIN"
        assert c["rsi"] == a["rsi"], "parity entry: RSI guard"
        assert c["sess"] is None and c["dirs"] is None
    assert d["exit"] == "D" and e["exit"] == "E"


def test_shadow_candidates_abc_untouched():
    assert SH.CANDIDATES["A_base"].get("exit") is None
    assert SH.CANDIDATES["B_london_sell"]["sess"] == "london"
    assert SH.CANDIDATES["B_london_sell"]["dirs"] == ("SELL",)
    assert SH.CANDIDATES["C_london_all"]["sess"] == "london"
    for cid in ("A_base", "B_london_sell", "C_london_all"):
        assert SH.CANDIDATES[cid]["sltp"] == (MV.SL_MULT, MV.TP_MULT)


def test_shadow_exit_for_candidate_d_routes_to_plan_d():
    m5 = mk_bars(30, 92.0, step=0.5, rng=8.0, body=3.0)
    m1 = mk_m1_neutral()
    plan = SH._exit_for_candidate("D_exit", SH.CANDIDATES["D_exit"],
                                  "BULL", m5[-1]["close"], m1, m5, None)
    assert plan["ok"] and plan["tp_pts"] == 600.0 and plan["sl_pts"] == 720.0, plan


def test_shadow_exit_for_candidate_e_routes_to_plan_e():
    m1 = mk_bars(30, 98.0, step=0.1, rng=2.0, body=0.5, tf=60)
    plan = SH._exit_for_candidate("E_atr_m1", SH.CANDIDATES["E_atr_m1"],
                                  "BULL", m1[-1]["close"], m1, mk_bars(30, 90.0, 0.5, 8.0, 3.0), None)
    assert plan["ok"] and plan["sl_pts"] == 180.0 and plan["tp_pts"] == 280.0, plan


def test_shadow_exit_for_candidate_base_parity_abc():
    """Default (tanpa 'exit') = geometri dasar 0.9/1.4×ATR-M5 — identik A/B/C."""
    m5 = mk_bars(30, 92.0, step=0.5, rng=8.0, body=3.0)
    m1 = mk_m1_neutral()
    plan = SH._exit_for_candidate("A_base", SH.CANDIDATES["A_base"],
                                  "BULL", m5[-1]["close"], m1, m5, None)
    assert plan["ok"]
    assert plan["sl_pts"] == 720.0 and plan["tp_pts"] == 1120.0, plan
    assert plan["burned"] is False and plan["clamp"] == "none"


def test_on_m1_close_accepts_m15_kwarg():
    sig = inspect.signature(SH.on_m1_close)
    assert "m15" in sig.parameters
    assert sig.parameters["m15"].default is None


# ── 8. Registry: EXIT-D-01 & EXIT-E-01 (Pagar 1 — tanpa angka bebas) ────────
def test_registry_exit_d_e_registered_and_match_module():
    reg = json.load(open("strategy_v2/contracts/hypothesis_registry.json",
                         encoding="utf-8"))
    hyps = reg["hypotheses"]
    for hid in ("EXIT-D-01", "EXIT-E-01"):
        assert hid in hyps, f"{hid} belum terdaftar (Pagar 1)"
        assert hyps[hid]["status"] == "HYPOTHESIS"
        assert hyps[hid]["genealogy"]["parent_id"], "hipotesis baru wajib parent"
    vd, ve = hyps["EXIT-D-01"]["value"], hyps["EXIT-E-01"]["value"]
    for k, val in EG.PARAMS_D.items():
        assert vd[k] == val, f"EXIT-D-01.{k} != PARAMS_D"
    assert vd["early_exit_params"] == EG.PARAMS_EARLY, "D5 params wajib teregistrasi"
    for k, val in EG.PARAMS_E.items():
        assert ve[k] == val, f"EXIT-E-01.{k} != PARAMS_E"


# ── 9. Early-exit hanya utk kandidat D (flag di pending) ────────────────────
def test_early_exit_flag_only_for_d():
    assert EG.PARAMS_D["early_exit"] is True
    assert "early_exit" not in EG.PARAMS_E
    assert "early_exit" not in EG.PARAMS_EARLY
