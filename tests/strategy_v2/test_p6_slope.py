"""P6 revisi — kontrak B3 slope mode (H-REGIME-SLOPE-02).

Regresi yang dijaga: sufiks diagnostic |slope=... TIDAK BOLEH bocor ke bias —
exact-match bias di B4/B5 butuh "BUY_ONLY"/"SELL_ONLY" murni. Ditemukan saat
P4 iterasi 3 (kedua arm slope 0 sinyal karena bias terkontaminasi sufiks).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2.gates import b3_regime


def _m15(series):
    return [{"time": 900 * i, "open": v, "high": v + 0.5, "low": v - 0.5,
             "close": v + 0.2, "volume": 100} for i, v in enumerate(series)]


CFG = {"min_bars_m15_warmup": 50,
       "b3_slope": {"mode": "slope", "ema_period": 20, "lookback_bars": 8,
                    "min_abs_slope_points": 1.0}}


def _clean_bias(raw):
    return raw[5:].split("|")[0] if raw.startswith("PASS:") else None


def test_slope_bias_clean_in_uptrend():
    up = _m15([100 + 0.1 * i for i in range(60)])
    raw = b3_regime(up, CFG)
    assert raw.startswith("PASS:BUY_ONLY"), raw
    assert _clean_bias(raw) == "BUY_ONLY"          # kode bersih, tanpa sufiks
    assert "|slope=" in raw                         # sufiks tetap di diagnostic


def test_slope_sell_direction_and_clean_bias():
    down = _m15([300 - 0.1 * i for i in range(60)])
    raw = b3_regime(down, CFG)
    assert raw.startswith("PASS:SELL_ONLY"), raw    # arah dua-arah: SELL mungkin
    assert _clean_bias(raw) == "SELL_ONLY"


def test_slope_chop_filtered_to_no_trade():
    chop = _m15([100 + (0.02 * i if (i // 10) % 2 == 0 else -0.02 * i)
                 for i in range(120)])
    raw = b3_regime(chop, CFG)
    assert raw.startswith("FAIL:NO_TRADE|slope="), raw
    assert _clean_bias(raw) is None


def test_classic_mode_unchanged_without_b3_slope():
    # Tanpa b3_slope di config → mode classic (kontrak lama, tetap teruji)
    up = _m15([100 + 0.1 * i for i in range(60)])
    raw = b3_regime(up, {"min_bars_m15_warmup": 50, "rsi_bias_threshold": 50})
    assert raw.startswith("PASS:BUY_ONLY"), raw
