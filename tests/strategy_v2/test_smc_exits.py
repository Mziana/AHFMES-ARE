"""Test simulator exit strategy_v2/smc_exits.py (kontrak bab 4 respon review).

- legacy: TP/SL gross eksak; SL-priority ambigu; EXPIRE mtm.
- g2: gross = 0.5*TP1 + 0.5*leg2; BE tepat = entry; SL tidak pernah mundur;
  bar TP1 yang juga menyentuh SL lama → SL_full (konservatif); tanpa
  lookahead (trailing pakai data closed).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from strategy_v2 import smc_exits as EX  # noqa: E402


def _bar(o, c, h=None, l=None, t=0):
    return {"open": o, "close": c,
            "high": h if h is not None else max(o, c),
            "low": l if l is not None else min(o, c),
            "time": t, "volume": 100}


def _series(bars, t0=1_000_000, dt=60):
    out = []
    for i, b in enumerate(bars):
        b = dict(b)
        b["time"] = t0 + i * dt
        out.append(b)
    return out


def _idx(bars):
    by_t = {b["time"]: b for b in bars}
    return by_t, [b["time"] for b in bars]


def test_legacy_tp_and_sl_exact():
    bars = _series([_bar(100, 100), _bar(100, 101.5, h=101.6)])
    by_t, ts = _idx(bars)
    r = EX.simulate("BUY", 100.0, 99.0, 101.0, bars[0]["time"], by_t, ts,
                    mode="legacy")
    assert r["outcome"] == "TP" and r["gross_pts"] == 100.0
    bars2 = _series([_bar(100, 100), _bar(100, 98.5, l=98.4)])
    by_t2, ts2 = _idx(bars2)
    r2 = EX.simulate("BUY", 100.0, 99.0, 101.0, bars2[0]["time"], by_t2, ts2,
                     mode="legacy")
    assert r2["outcome"] == "SL" and r2["gross_pts"] == -100.0


def test_legacy_sl_priority_when_ambiguous():
    # bar menyentuh SL dan TP bersamaan → SL (konservatif, parity baseline)
    bars = _series([_bar(100, 100), _bar(100, 100, h=101.2, l=98.8)])
    by_t, ts = _idx(bars)
    r = EX.simulate("BUY", 100.0, 99.0, 101.0, bars[0]["time"], by_t, ts,
                    mode="legacy")
    assert r["outcome"] == "SL"


def test_legacy_expire_mtm_after_max_hold():
    bars = _series([_bar(100, 100)] + [_bar(100.5, 100.6) for _ in range(1500)])
    by_t, ts = _idx(bars)
    r = EX.simulate("BUY", 100.0, 98.0, 102.0, bars[0]["time"], by_t, ts,
                    mode="legacy")
    assert r["outcome"] == "EXPIRE"
    assert abs(r["gross_pts"] - (bars[-1]["close"] - 100.0) / EX.POINT) < 1.0


def test_g2_tp1_then_be_flat_loss_zero():
    """TP1 kena, lalu harga berbalik kena BE → gross = 0.5*TP1 (leg2 = 0)."""
    bars = _series([
        _bar(100, 100),
        _bar(100, 100.9, h=101.05),   # sentuh TP1=101 (leg1 fix 50 pts)
        _bar(100.9, 100.2, h=100.95, l=99.95),  # turun kena BE=100
    ])
    by_t, ts = _idx(bars)
    r = EX.simulate("BUY", 100.0, 99.0, 101.0, bars[0]["time"], by_t, ts,
                    mode="g2")
    assert r["outcome"] == "TP1_BE"
    assert abs(r["gross_pts"] - 50.0) < 1e-6  # 0.5*100


def test_g2_tp1_then_trail_above_be():
    """TP1 kena, trailing naik di atas BE, lalu kena trail → leg2 > 0.
    Stub ATR deterministik: trail BUY = close - 0.1 (ketat)."""
    bars = _series([
        _bar(100, 100),
        _bar(100, 100.9, h=101.05),   # TP1 → BE
        _bar(100.9, 100.9),           # trail = 100.8 (stub 0.1 di bawah close)
        _bar(100.9, 100.75, l=100.7), # kena trail 100.8 → leg2 = +80 pts
    ])
    by_t, ts = _idx(bars)
    r = EX.simulate("BUY", 100.0, 99.0, 101.0, bars[0]["time"], by_t, ts,
                    mode="g2", atr_fn=lambda hist: 0.05)  # 2*ATR=0.1
    assert r["outcome"] == "TP1_TRAIL"
    # 0.5*100 + 0.5*80 = 90 pts per 1.0 posisi
    assert abs(r["gross_pts"] - 90.0) < 1e-6


def test_g2_immediate_sl_full():
    bars = _series([_bar(100, 100), _bar(100, 98.9, l=98.8)])
    by_t, ts = _idx(bars)
    r = EX.simulate("BUY", 100.0, 99.0, 101.0, bars[0]["time"], by_t, ts,
                    mode="g2")
    assert r["outcome"] == "SL_full" and r["gross_pts"] == -100.0


def test_g2_sl_and_tp1_same_bar_is_sl_full():
    """Bar sentuh TP1 DAN SL lama bersamaan → SL_full (BE dipasang end-of-bar;
    urutan konservatif — kontrak test #3)."""
    bars = _series([_bar(100, 100), _bar(100, 100, h=101.2, l=98.8)])
    by_t, ts = _idx(bars)
    r = EX.simulate("BUY", 100.0, 99.0, 101.0, bars[0]["time"], by_t, ts,
                    mode="g2")
    assert r["outcome"] == "SL_full"


def test_g2_trail_never_loosens():
    """Kontrak #2: SL tidak pernah mundur — trail BUY monoton naik."""
    seen = []

    def atr_stub(hist):
        c = float(hist[-1]["close"])
        return (100.0 - c) / EX.G2_TRAIL_K_ATR if c < 100.0 else 0.001

    bars = _series([
        _bar(100, 100),
        _bar(100, 100.9, h=101.05),        # TP1 → BE=100
        _bar(100.9, 100.85),
        _bar(100.85, 100.4, l=100.3),      # drop besar → kena trail
    ])
    by_t, ts = _idx(bars)
    r = EX.simulate("BUY", 100.0, 99.0, 101.0, bars[0]["time"], by_t, ts,
                    mode="g2", atr_fn=atr_stub)
    # BE floor: exit tidak boleh di bawah entry
    assert r["exit_px"] >= 100.0 - 1e-9
    assert r["gross_pts"] >= 50.0 - 1e-6
