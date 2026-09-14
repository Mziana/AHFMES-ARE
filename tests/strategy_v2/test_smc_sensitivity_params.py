"""Test parameter sensitivity (review prio 4 & 7) di strategy_v2/smc.py.

Kontrak:
- Default 100% backward-compatible: evaluate() == evaluate(min_score=None,
  poi_reach=None, poi_mode=None) — konfigurasi live tidak berubah.
- min_score: threshold skor overridable TANPA mengubah jalur skor lain
  (reason & struktur dict tetap; hanya ambang take yang bergeser).
- poi_mode="strict": desain §3.1 literal — harga WAJIB di dalam zona (touch);
  poi_reach=0.0 pada mode "reach" identik dengan strict.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from strategy_v2 import smc  # noqa: E402
from tests.strategy_v2.test_smc_engine import _bull_market  # noqa: E402


def test_defaults_fully_backward_compatible():
    m1, m5, m15, h4 = _bull_market()
    r0 = smc.evaluate(m1, m5, m15, h4, spread_pts=17.0)
    r1 = smc.evaluate(m1, m5, m15, h4, spread_pts=17.0, min_score=None,
                      poi_reach=None, poi_mode=None)
    assert r0 == r1


def test_min_score_higher_blocks_take_without_early_exit():
    """Threshold 99 memblok take di jalur skor (bukan early-exit): dict penuh
    dengan SL/TP1 tetap dihitung, reason menyebut skor vs threshold."""
    m1, m5, m15, h4 = _bull_market()
    r0 = smc.evaluate(m1, m5, m15, h4, spread_pts=17.0)
    assert r0["take"] is True and r0["score"] == r0["max_score"] == 12
    r1 = smc.evaluate(m1, m5, m15, h4, spread_pts=17.0, min_score=99)
    assert r1["take"] is False
    assert r1["score"] == 12                      # skor tidak berubah
    assert r1["sl"] is not None and r1["tp1"] is not None
    assert "skor 12" in r1["reason"] and "99" in r1["reason"]
    # threshold lebih rendah tidak mengubah fixture penuh
    r2 = smc.evaluate(m1, m5, m15, h4, spread_pts=17.0, min_score=0)
    assert r2["take"] is True and r2["score"] == r0["score"]


def test_poi_strict_requires_price_inside_zone():
    """strict: POI hanya OK bila harga di dalam zona terpilih (dist == 0)."""
    m1, m5, m15, h4 = _bull_market()
    r0 = smc.evaluate(m1, m5, m15, h4, spread_pts=17.0)
    assert r0["components"]["poi_ok"] is True
    price = float(m1[-1]["close"])
    top, bot = r0["poi"]["top"], r0["poi"]["bottom"]
    inside = bot <= price <= top                  # zona terpilih (terdekat)
    r1 = smc.evaluate(m1, m5, m15, h4, spread_pts=17.0, poi_mode="strict")
    if r1["components"]:                          # jalur skor penuh tercapai
        assert r1["components"]["poi_ok"] is inside
        assert r0["score"] - r1["score"] == (0 if inside else
                                             smc.WEIGHTS["poi_fresh"])
    else:
        # strict menghapus POI → jalur berhenti di RR/SL: reason menyebutnya
        assert ("SL struktural" in r1["reason"]) or r1["reason"].startswith("RR")


def test_poi_reach_zero_equals_strict():
    m1, m5, m15, h4 = _bull_market()
    a = smc.evaluate(m1, m5, m15, h4, spread_pts=17.0, poi_mode="strict")
    b = smc.evaluate(m1, m5, m15, h4, spread_pts=17.0, poi_mode="reach",
                     poi_reach=0.0)
    assert a == b


def test_poi_reach_wider_only_adds_zones_not_removes():
    """Reach lebih lebar adalah superset: bila default (1.5) ambil POI,
    reach 3.0 juga ambil — skor tidak mungkin turun."""
    m1, m5, m15, h4 = _bull_market()
    r0 = smc.evaluate(m1, m5, m15, h4, spread_pts=17.0)
    r3 = smc.evaluate(m1, m5, m15, h4, spread_pts=17.0, poi_reach=3.0)
    if r3["components"]:
        assert r3["score"] >= r0["score"]
