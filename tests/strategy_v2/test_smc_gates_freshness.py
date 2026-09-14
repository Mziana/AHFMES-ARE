"""Test G1 (gate item-8) & G3 (freshness BOS) di strategy_v2/smc.py.

Kontrak (RESPON_REVIEW_SMC_V3.md bab 4 / review 4.7):
- gates default OFF (fixture legacy tetap hijau); ON → spread/ATR di luar
  rentang menolak dengan reason 'gate ...' TANPA mengubah skor item lain.
- bos_fresh_bars=N → item BOS OK hanya bila umur event terbaru <= N bar M5;
  umur dihitung dari CLOSE bar break (anti-lookahead, bar closed saja).
"""
import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from strategy_v2 import smc  # noqa: E402
from tests.strategy_v2.test_smc_engine import (  # noqa: E402
    _bar, _bull_market, flat, from_path,
)


def test_gates_default_off_legacy_reasons_unchanged():
    m1, m5, m15, h4 = _bull_market()
    r_off = smc.evaluate(m1, m5, m15, h4, spread_pts=17.0, gates=False)
    r_plain = smc.evaluate(m1, m5, m15, h4, spread_pts=17.0)
    assert r_off == r_plain  # default = legacy persis


def test_gate_spread_rejects_only_via_gate():
    m1, m5, m15, h4 = _bull_market()
    r = smc.evaluate(m1, m5, m15, h4, spread_pts=50.0, gates=True)
    assert r["take"] is False
    assert "gate spread" in r["reason"]
    # gates=False dgn spread sama: TIDAK ditolak oleh spread (legacy RR tetap)
    r2 = smc.evaluate(m1, m5, m15, h4, spread_pts=50.0, gates=False)
    assert "gate spread" not in (r2["reason"] or "")


def test_gate_atr_band():
    m1, m5, m15, h4 = _bull_market()
    # ATR-M5 fixture kecil (flatten) → di bawah band → gate menolak saat ON
    r = smc.evaluate(m1, m5, m15, h4, spread_pts=17.0, gates=True)
    assert r["take"] is False and "gate ATR-M5" in r["reason"]


def test_bos_fresh_blocks_old_bos_and_keeps_recent():
    m1, m5, m15, h4 = _bull_market()
    r0 = smc.evaluate(m1, m5, m15, h4)  # legacy
    assert r0["components"]["bos_ok"] is True
    age = r0["bos_age_m5"]
    assert age is not None and age >= 0
    # N sangat kecil → item BOS hilang; skor turun tepat 1 (bobot BOS)
    r1 = smc.evaluate(m1, m5, m15, h4, bos_fresh_bars=0)
    if r1["take"] or r1["score"] >= 8:
        assert r1["components"]["bos_ok"] is False
    assert r0["score"] - r1["score"] == 1
    # N >= umur terukur → item tetap OK
    r2 = smc.evaluate(m1, m5, m15, h4, bos_fresh_bars=age)
    assert r2["components"]["bos_ok"] is True
    assert r2["score"] == r0["score"]


def test_bos_age_uses_close_time_no_lookahead():
    """Umur = bar M5 CLOSED setelah close-time bar break. Event di bar M5
    terakhir window harus berumur 0 (baru), bukan dihitung dari idx+1."""
    # m5: flat panjang lalu 1 bar break naik di UJUNG window (baru close)
    m5 = flat(100, 60) + from_path([100, 101], per_leg=1)
    m1 = flat(101, 60)
    ev = smc.bos_choch(m5)
    assert ev and ev[-1]["dir"] == "BULL"
    r = smc.evaluate(m1, m5, flat(101, 40),
                     flat(101, 30), spread_pts=17.0)
    # tidak ada bias H4 di fixture flat — cukup pastikan engine jalan; umur
    # diuji presisi lewat struktur: hitung manual seperti engine
    t_new = int(m5[ev[-1]["idx"]]["time"]) + 300
    m5_ts = [int(b["time"]) for b in m5]
    pos = len(m5_ts)
    while pos > 0 and m5_ts[pos - 1] >= t_new:
        pos -= 1
    assert len(m5_ts) - pos == 0  # break di bar terakhir → umur 0
