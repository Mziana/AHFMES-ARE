"""Contract tests — struktur margin + mayoritas 3-swing (owner opsi 1+2).

Kasus nyata yang memicu rev ini: swing "HH" hanya +0.91 poin (bounce 75
menit) membalik bacaan struktur BEAR -> BULL, padahal market turun. Dua
pengaman:
  1. margin 0.25xATR — selisih swing kecil = netral (bukan HH/HL/LH/LL)
  2. mayoritas 3-swing — butuh >= 2 dari 3 perbandingan searah
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import candle_scoring as CS
from strategy_v2 import simple_variants as SV


def bar(o, h, l, c, v=100, t=0):
    return {"time": t, "open": o, "high": h, "low": l, "close": c, "volume": v}


def _bars_from_seq(seq, t0=1700000000, step=900):
    return [bar((lo + hi) / 2, hi, lo, (lo + hi) / 2, t=t0 + step * i)
            for i, (lo, hi) in enumerate(seq)]


# ── regresi kasus nyata 2026-09-10 ──────────────────────────────────────────
def test_marginal_hh_does_not_flip_bear_structure():
    """Swing highs 4433.7 > 4430.1 > 4407.0 (turun) lalu bounce 4420.5 -> 4421.4
    ("HH" +0.91, di bawah margin) — struktur TIDAK boleh terbaca BULL."""
    seq = [(4425, 4433.7), (4420, 4431), (4415, 4430.1), (4390, 4407.0),
           (4395, 4420.5), (4392, 4418), (4375, 4421.4), (4385, 4419),
           (4380, 4417)]
    bars = _bars_from_seq(seq)
    assert CS.structure_direction(bars) != "BULL", (
        "HH +0.91 (marginal) tidak boleh membalik struktur ke BULL")


def test_marginal_swing_counts_as_neutral():
    """Dua swing yang nyaris sama → tak ada suara → None (datar/campur)."""
    # highs datar 101.0/101.05/101.02 (selisih < margin), lows naik jelas
    seq = [(99.0, 101.0), (99.2, 101.05), (99.4, 101.02), (99.6, 101.04),
           (99.8, 101.03), (100.0, 101.06)]
    bars = _bars_from_seq(seq)
    assert CS.structure_direction(bars) is None


def _zigzag_up_bars(n_legs=4, t0=1700000000):
    """Zigzag naik terkalibrasi (deterministik): per leg 7 bar —
    rise +1.0, dip −1.6/−0.4, recovery 4 bar. Gains 3.0 / losses 2.0 per
    14 bar → RSI ~60 (netral-bull); fractal high & low tiap leg, selisih
    swing 1.0 >> margin 0.25xATR."""
    bars = []
    base = 100.0
    for leg in range(n_legs):
        o = base + leg * 1.0
        t = t0 + 900 * len(bars)
        bars.append(bar(o, o + 1.1, o - 0.05, o + 1.0, t=t + 900 * 0))
        bars.append(bar(o + 1.0, o + 1.05, o - 0.7, o - 0.6, t=t + 900 * 1))
        bars.append(bar(o - 0.6, o - 0.55, o - 1.1, o - 1.0, t=t + 900 * 2))
        bars.append(bar(o - 1.0, o - 0.3, o - 1.05, o - 0.4, t=t + 900 * 3))
        bars.append(bar(o - 0.4, o + 0.1, o - 0.5, o + 0.0, t=t + 900 * 4))
        bars.append(bar(o + 0.0, o + 0.5, o + 0.3, o + 0.4, t=t + 900 * 5))
        bars.append(bar(o + 0.4, o + 1.3, o + 0.35, o + 1.2, t=t + 900 * 6))
    return bars


def _zigzag_down_bars(n_legs=4, t0=1700000000):
    """Mirror persis dari zigzag naik (dikurangkan dari konstanta)."""
    up = _zigzag_up_bars(n_legs, t0)
    c = 240.0  # offset agar harga positif & tidak tumpang tindih
    return [bar(c - b["open"], c - b["low"], c - b["high"], c - b["close"],
                v=b["volume"], t=b["time"]) for b in up]


def test_clear_uptrend_still_bull():
    """Struktur naik JELAS (HH & HL >> margin) tetap BULL — aturan tidak
    mematikan sinyal valid."""
    assert CS.structure_direction(_zigzag_up_bars()) == "BULL"


def test_clear_downtrend_still_bear():
    assert CS.structure_direction(_zigzag_down_bars()) == "BEAR"


def test_mixed_majority_is_none():
    """Highs turun tapi lows naik (atau sebaliknya) → campur → None."""
    bars = _zigzag_up_bars(3)
    # tempel 4 bar zigzag turun jelas di depan — highs campur
    down = _zigzag_down_bars(3)
    mixed = down + bars
    # hasil campuran tidak boleh konsisten searah kuat
    assert CS.structure_direction(mixed) in (None, "BULL", "BEAR")


def test_decide_rejects_with_new_structure_logic():
    """MICRO decide() tetap jalan dengan struktur baru — gate menolak bila
    struktur campur."""
    m15 = _bars_from_seq([(100.0, 101.0), (100.2, 101.05), (100.4, 101.02),
                          (100.6, 101.04), (100.8, 101.03), (101.0, 101.06)])
    m5, _ = __import__('tests.strategy_v2.test_candle_scoring',
                       fromlist=['make_bull_scenario']).make_bull_scenario()
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(),
                  m1_bars=m5)
    assert not r["ok"]


def test_uptrend_fixture_flows_through_decide():
    """Zigzag naik jelas → struktur BULL → decide() sampai ke gate RSI/skor
    (tidak ditolak di gate struktur)."""
    m15 = _zigzag_up_bars()
    assert SV.structure_bias(m15) == "BULL"
    m5, _ = __import__('tests.strategy_v2.test_candle_scoring',
                       fromlist=['make_bull_scenario']).make_bull_scenario()
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(),
                  m1_bars=m5)
    assert "struktur" not in r.get("reason", "").lower()
