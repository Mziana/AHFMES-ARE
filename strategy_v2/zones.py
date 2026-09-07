"""P1 — Deterministic zone construction, ANTI-LOOKAHEAD (koreksi review #4).

RE-IMPLEMENTASI swing detection & S/R clustering yang pure dan hanya memakai
bar ≤ T (evaluation-time slicing oleh pemanggil). DILARANG memanggil
`getSupportResistanceZones` / `findSwingPoints` dari `UI/src/lib/indicators.ts`
untuk replay — versi TS mengakses `highs[i+k]` (bar masa depan) = lookahead.

Definisi (desain §B4):
- swing = bar dengan high tertinggi / low terendah vs 5 bar kiri+kanan
  CONFIRMED — swing di index i hanya terkonfirmasi bila bar [i+k] ada DI
  DALAM slice (artinya bar i+k sudah closed pada T). Konsekuensi: swing baru
  muncul setelah k bar selesai — deterministik, tidak pernah melihat > T.
- cluster distance = 0.75×ATR(M15); zona = mean level cluster ± 0.5×ATR band;
  maks 5 zona per sisi; window 200 bar M15.

Semua fungsi PURE: input sama → output identik, kapan pun dihitung ulang.
"""
from __future__ import annotations

import math

K_SWING = 5
CLUSTER_ATR_MULT = 0.75
BAND_ATR_MULT = 0.5
MAX_ZONES_PER_SIDE = 5
WINDOW_BARS = 200
RSI_PERIOD = 14
ATR_PERIOD = 14


def ema(values: list, period: int) -> list:
    """EMA rekursif alpha=2/(n+1), seed = nilai pertama. Pure & deterministik."""
    if not values:
        return []
    alpha = 2.0 / (period + 1.0)
    out = [values[0]]
    for v in values[1:]:
        out.append(alpha * v + (1.0 - alpha) * out[-1])
    return out


def rsi(closes: list, period: int = RSI_PERIOD) -> float | None:
    """RSI Wilder. None bila warmup < period+1 (jujur, bukan angka karangan)."""
    if len(closes) < period + 1:
        return None
    gains = losses = 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        if d > 0:
            gains += d
        else:
            losses -= d
    avg_gain = gains / period
    avg_loss = losses / period
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        g = d if d > 0 else 0.0
        l = -d if d < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def true_ranges(bars: list) -> list:
    trs = []
    for i, b in enumerate(bars):
        if i == 0:
            trs.append(b["high"] - b["low"])
        else:
            pc = bars[i - 1]["close"]
            trs.append(max(b["high"] - b["low"], abs(b["high"] - pc), abs(b["low"] - pc)))
    return trs


def atr(bars: list, period: int = ATR_PERIOD) -> float | None:
    """ATR = mean TR `period` bar terakhir. None bila data kurang."""
    if len(bars) < 2:
        return None
    trs = true_ranges(bars)
    window = trs[-period:]
    return sum(window) / len(window)


def find_swing_points(bars: list, k: int = K_SWING) -> tuple[list, list]:
    """Swing CONFIRMED deterministik dari bars ≤ T.

    Return (swing_highs, swing_lows) — list index i. Swing high di i butuh
    bars[i+k] ADA di slice (bar i+k closed pada T) → tidak pernah lookahead.
    """
    highs = [b["high"] for b in bars]
    lows = [b["low"] for b in bars]
    swing_highs, swing_lows = [], []
    n = len(bars)
    for i in range(k, n - k):
        window_h = highs[i - k:i + k + 1]
        window_l = lows[i - k:i + k + 1]
        if highs[i] == max(window_h) and window_h.count(highs[i]) == 1:
            swing_highs.append(i)
        if lows[i] == min(window_l) and window_l.count(lows[i]) == 1:
            swing_lows.append(i)
    return swing_highs, swing_lows


def _cluster(levels: list, distance: float) -> list[list[float]]:
    """Greedy cluster deterministik: sort naik, gabung bila gap <= distance."""
    if not levels:
        return []
    lv = sorted(levels)
    clusters = [[lv[0]]]
    for v in lv[1:]:
        if v - clusters[-1][-1] <= distance:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    return clusters


def build_zones(m15_bars: list) -> dict:
    """Bangun zona S/R dari m15_bars (harus ≤ T). PURE.

    Output: {'supports': [{'level','band'}...], 'resistances': [...],
             'atr_m15': float, 'window_bars': int, 'n_swings': [int,int]}
    """
    window = m15_bars[-WINDOW_BARS:]
    a = atr(window)
    if a is None or not math.isfinite(a) or a <= 0:
        return {"supports": [], "resistances": [], "atr_m15": None, "window_bars": len(window), "n_swings": [0, 0]}
    swing_highs, swing_lows = find_swing_points(window)
    sh_levels = [window[i]["high"] for i in swing_highs]
    sl_levels = [window[i]["low"] for i in swing_lows]

    def to_zones(levels: list) -> list:
        clusters = _cluster(levels, CLUSTER_ATR_MULT * a)
        zs = [{"level": sum(c) / len(c), "band": BAND_ATR_MULT * a, "members": len(c)} for c in clusters]
        # deterministik: terbanyak member dulu, lalu level terbesar
        zs.sort(key=lambda z: (-z["members"], -z["level"]))
        return zs[:MAX_ZONES_PER_SIDE]

    return {
        "supports": to_zones(sl_levels),
        "resistances": to_zones(sh_levels),
        "atr_m15": a,
        "window_bars": len(window),
        "n_swings": [len(swing_highs), len(swing_lows)],
    }


def nearest_zone_distance(zones: dict, price: float, bias: str) -> tuple[float, str] | None:
    """Jarak harga ke zona searah bias. Return (distance, ref) atau None.

    BUY_ONLY → support zone; SELL_ONLY → resistance zone.
    """
    if not zones or zones.get("atr_m15") in (None, 0):
        return None
    side = "supports" if bias == "BUY_ONLY" else "resistances"
    best = None
    for z in zones.get(side, []):
        d = abs(price - z["level"])
        if best is None or d < best[0]:
            best = (d, f"{side[:-1]}@{z['level']:.2f}")
    return best
