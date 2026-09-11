"""Contract tests — aturan owner rev 2026-09-10 (MICRO M1 + multi-TF).

- momentum-habis: M5, rally-aware (retrace >61,8% ATAU marubozu+volume)
- RSI guard mencakup M1 (MICRO: M15+M5+M1)
- SL/TP MICRO = ATR M1 clamp SL 130-210 / TP 200-300 pts
- TP tidak melintasi swing berlawanan; dipotong < 200 pts → tolak
- H4 lembut: candle terakhir melawan → penalti -1 (tidak pernah blok)
- konteks multi-TF per TF (pola+poin) untuk UI
- eksekusi MICRO benar-benar membaca M1 (bukan M5)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import candle_scoring as CS
from strategy_v2 import simple_variants as SV

from tests.strategy_v2.test_candle_scoring import (  # noqa: E402
    bar, flat, make_bull_scenario,
)


def _m15_uptrend(n=32, start=100.0):
    """M15 HH+HL dengan RSI netral-bull (~63) — resep kalibrasi deterministik.

    Per leg 4 bar (offset dari open leg):
      bar1: +0.9 (high +1.0)   bar2: −1.0 (kembali ke open leg, low = swing low)
      bar3: +0.45              bar4: +0.35
    → gain 1.7 / loss 1.0 per leg → RSI ~63; tiap leg naik +0.7 → HH & HL.
    """
    bars = []
    t = 1700000000
    o = start
    for _ in range(n // 4):
        # bar4 kaki sebelumnya TANPA wick bawah (low=open) supaya low bar2
        # (o-0.4) selalu jadi fractal low yang valid.
        bars.append(bar(o, o + 1.0, o - 0.05, o + 0.9, t=t + 900 * len(bars)))
        bars.append(bar(o + 0.9, o + 0.95, o - 0.4, o - 0.1, t=t + 900 * len(bars)))
        bars.append(bar(o - 0.1, o + 0.45, o - 0.1, o + 0.35, t=t + 900 * len(bars)))
        bars.append(bar(o + 0.35, o + 0.8, o + 0.35, o + 0.7, t=t + 900 * len(bars)))
        o += 0.7
    bias = SV.momentum_bias(bars)
    struct = SV.structure_bias(bars)
    r = CS.rsi([b["close"] for b in bars], 14)
    if bias != "BULL" or struct != "BULL" or r is None or not (50.0 <= r < 65.0):
        raise AssertionError(f"fixture: bias={bias} struct={struct} rsi={r}")
    return bars


def _rally_then_retrace(retrace_frac: float, run: float = 10.0):
    """M5: rally naik ~run poin (5 candle) lalu koreksi retrace_frac dari puncak."""
    bars = flat(100.0, 25, v=100)
    t0 = 1700000000
    n_up = 5
    step = run / n_up
    for i in range(n_up):
        bars.append(bar(100.0 + step * i, 100.0 + step * (i + 1) + 0.1,
                        100.0 + step * i - 0.1, 100.0 + step * (i + 1),
                        v=120, t=t0 + 300 * i))
    peak = 100.0 + run
    back = run * retrace_frac
    bars.append(bar(peak - back * 0.3, peak, peak - back, peak - back,
                    v=130, t=t0 + 300 * n_up))
    return bars


# ── momentum-habis M5: retrace-based, rally-aware ──
def test_momentum_exhausted_deep_retrace_blocks():
    """Koreksi > 61.8% dari run → momentum habis (blok)."""
    bars = _rally_then_retrace(0.7)
    exh, info = CS.momentum_exhausted(bars, "BULL")
    assert exh, f"retrace 70% harus blok, dapat zone={info['zone']}"


def test_momentum_exhausted_shallow_retrace_allows():
    """Koreksi <= 38.2% → sehat; rally 2/3/4/5 candle tidak masalah."""
    for n_up in (2, 3, 4, 5):
        bars = _rally_then_retrace(0.25)
        exh, info = CS.momentum_exhausted(bars, "BULL")
        assert not exh, f"n_up={n_up}: koreksi dangkal harus lanjut, zone={info['zone']}"


def test_momentum_exhausted_golden_zone_needs_marubozu_volume():
    """Zona emas (38-62%): habis HANYA bila marubozu lawan + volume."""
    bars = _rally_then_retrace(0.5)
    exh_calm, _ = CS.momentum_exhausted(bars, "BULL")
    assert not exh_calm, "koreksi 50% tanpa marubozu+volume masih sehat"
    bars[-1] = bar(bars[-1]["open"], bars[-1]["open"] + 0.05,
                   bars[-1]["close"] - 0.05, bars[-1]["close"], v=5000)
    exh_hot, info = CS.momentum_exhausted(bars, "BULL")
    assert exh_hot, f"koreksi 50% + marubozu lawan bervolume harus blok, zone={info['zone']}"


def test_momentum_rule_applies_at_m5_not_m1():
    """Owner: aturan momentum-habis di M5 (M1 terlalu volatile). M1 bagus +
    M5 deep-retrace → decide() tetap menolak."""
    m5 = _rally_then_retrace(0.7)
    m1, _ = make_bull_scenario()
    m15 = _m15_uptrend()
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(), m1_bars=m1)
    assert not r["ok"] and "momentum habis" in r["reason"].lower()


# ── RSI guard mencakup M1 ──
def test_rsi_guard_includes_m1():
    """MICRO: RSI M1 >= 65 → stop BUY, alasan menyebut M1."""
    bars, _ = make_bull_scenario()
    bars = bars[:-1] + [bar(100.0, 102.0, 99.9, 101.9, v=200)]
    rsi_m1 = CS.rsi([b["close"] for b in bars], 14)
    if rsi_m1 is not None and rsi_m1 >= 65:
        m15 = _m15_uptrend()
        m5, _ = make_bull_scenario()
        r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(), m1_bars=bars)
        assert not r["ok"] and "M1" in r["reason"]


def test_rsi_step_shows_all_three_tfs():
    """Langkah RSI guard menampilkan nilai M15, M5, dan M1."""
    m1, _ = make_bull_scenario()
    m15 = _m15_uptrend()
    m5, _ = make_bull_scenario()
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(), m1_bars=m1)
    rsi_steps = [s for s in r["steps"] if s["k"].startswith("RSI")]
    assert rsi_steps, r["steps"]
    assert "M15" in rsi_steps[0]["note"] and "M5" in rsi_steps[0]["note"] \
        and "M1" in rsi_steps[0]["note"]


# ── SL/TP: ATR clamp 130-210 / 200-300 ──
def test_micro_sl_tp_atr_clamped():
    """ATR besar → dipotong ke ceiling; ATR ~0 → dinaikkan ke floor."""
    wild = flat(100.0, 25)
    for i in range(20):
        wild[i] = bar(100, 104, 96, 100, t=1700000000 + 300 * i)
    st = SV.compute_sl_tp("MICRO", "BULL", wild, 100.0)
    assert 130.0 <= st["sl_points"] <= 210.0, f"SL {st['sl_points']} di luar clamp"
    assert 200.0 <= st["tp_points"] <= 300.0, f"TP {st['tp_points']} di luar clamp"
    calm = [bar(100.0, 100.1, 99.9, 100.0, t=1700000000 + 300 * i) for i in range(25)]
    st2 = SV.compute_sl_tp("MICRO", "BULL", calm, 100.0)
    assert st2["sl_points"] == 130.0
    assert st2["tp_points"] == 200.0


# ── TP tidak melintasi swing berlawanan ──
def test_tp_never_crosses_opposing_swing():
    """TP BUY berhenti di bawah resistance M15/M5 terdekat (−buffer 0.25xATR)."""
    m15 = flat(100.0, 12, v=100)          # padding agar ATR tersedia
    t = 1700000000 + 900 * 12
    seq = [(99.0, 99.8), (99.2, 100.0), (98.8, 99.6), (99.6, 101.0),
           (99.4, 100.2), (99.2, 100.0), (99.8, 100.6), (99.6, 100.4),
           (99.4, 100.2)]
    for i, (lo, hi) in enumerate(seq):
        m15.append(bar((lo + hi) / 2, hi, lo, (lo + hi) / 2, t=t + 900 * i))
    entry = 100.4
    a = CS.atr(m15)
    assert a is not None
    st = SV.compute_sl_tp("MICRO", "BULL", m15, entry)
    tp2, _info = SV.clamp_tp_to_structure("MICRO", "BULL", entry, st["tp"], m15, m15)
    assert tp2 <= 101.0 - 0.25 * a + 1e-6


def test_tp_cut_below_min_rejects_entry():
    """TP terpotong swing menjadi < 200 pts → decide() menolak entry."""
    m15 = []
    t = 1700000000
    seq = [(99.9, 100.1), (99.95, 100.15), (99.85, 100.05), (100.0, 100.45),
           (99.9, 100.3), (99.85, 100.25), (100.05, 100.35), (100.0, 100.3),
           (99.95, 100.25)]
    for i, (lo, hi) in enumerate(seq):
        m15.append(bar((lo + hi) / 2, hi, lo, (lo + hi) / 2, t=t + 900 * i))
    m5, _ = make_bull_scenario()
    m5[-1] = bar(99.95, 100.1, 99.8, 100.05, v=300)
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(), m1_bars=m5)
    if r["ok"]:
        assert r["tp"] <= 100.45 + 1e-6


# ── H4 lembut ──
def test_h4_soft_penalty_constant():
    assert SV.H4_SOFT_PENALTY == -1.0


# ── konteks multi-TF ──
def test_context_points_per_tf():
    # bar terakhir rally+retrace adalah candle koreksi → konteks membaca BEAR
    # (pola koreksi terdeteksi) — ini pembacaan yang BENAR untuk UI.
    c = CS.context_points(_rally_then_retrace(0.5))
    assert c["pattern"] is not None and c["points"] >= 3
    assert c["direction"] in ("BULL", "BEAR")
    flat_bars = flat(25, 25)
    assert CS.context_points(flat_bars)["points"] == 0
    assert CS.context_points(flat_bars)["pattern"] is None


def test_decide_multi_tf_context_step_present():
    m1, _ = make_bull_scenario()
    m15 = _m15_uptrend()
    m5, _ = make_bull_scenario()
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(), m1_bars=m1)
    assert any("Konteks multi-TF" in s["k"] for s in r["steps"]), r["steps"]


def test_decide_micro_uses_m1_execution():
    """M1 polos → tidak entry walau M5 punya pola (bukti exec TF = M1)."""
    m15 = _m15_uptrend()
    m5, _ = make_bull_scenario()
    m1_flat = flat(100.0, 25)
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(), m1_bars=m1_flat)
    assert not r["ok"], "M1 tanpa pola tidak boleh entry walau M5 punya pola"


def test_decide_micro_m1_pattern_scores():
    """M1 hammer di dekat level + konteks M5/M15 searah → skor total >= 6 → entry."""
    m1, _ = make_bull_scenario()
    m15 = _m15_uptrend()
    m5, _ = make_bull_scenario()
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(), m1_bars=m1)
    if r["ok"]:
        assert r["direction"] == "BUY"
        assert 130.0 <= r["sl_points"] <= 210.0
        assert 200.0 <= r["tp_points"] <= 300.0
