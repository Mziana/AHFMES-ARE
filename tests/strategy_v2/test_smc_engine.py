"""Test SMC/ICT v3 engine (strategy_v2/smc.py) — kandidat pengganti MICRO.

Fixture = path harga sintetis (from_path) supaya tiap konsep SMC (swing,
BOS/CHoCH, OB, FVG, sweep, premium/discount) bisa dibuat deterministik.
Semua test pure — tanpa MT5, tanpa file state. Angka fixture dihitung tangan
(lihat komentar) supaya kegagalan test berarti bug implementasi, bukan fixture.
"""
import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from strategy_v2 import smc  # noqa: E402


# ── fixture helpers ─────────────────────────────────────────────────────────
def _bar(o, c, h=None, l=None, t=0):
    return {"open": o, "close": c,
            "high": h if h is not None else max(o, c),
            "low": l if l is not None else min(o, c),
            "time": t, "volume": 100}


def from_path(points, per_leg=5, t0=1_000_000):
    """Bars ramp linear antar titik path (tanpa gap antar bar)."""
    bars, t = [], t0
    for a, b in zip(points, points[1:]):
        for j in range(1, per_leg + 1):
            o = a + (b - a) * (j - 1) / per_leg
            c = a + (b - a) * j / per_leg
            bars.append(_bar(o, c, t=t))
            t += 60
    return bars


def flat(level, n, wick=0.02, dip=None, t0=2_000_000):
    """Zona sideways; `dip=(low, close)` menyuntik 1 bar sweep sebelum akhir."""
    bars, t = [], t0
    for i in range(n):
        if dip and i == n - 3:
            bars.append(_bar(level, dip[1], h=level + wick, l=dip[0], t=t))
        else:
            bars.append(_bar(level, level, h=level + wick, l=level - wick, t=t))
        t += 60
    return bars


# ── struktur: swing, trend, BOS/CHoCH ───────────────────────────────────────
def test_swings_seq_dedupes_same_side():
    bars = from_path([10, 11, 10.5, 11.5], per_leg=3)
    sw = smc.swings_seq(bars)
    kinds = [t for _, t, _ in sw]
    assert not any(a == b for a, b in zip(kinds, kinds[1:]))  # selang-seling
    assert kinds[0] == "H"


def test_structure_trend_bull_bear_and_range():
    bull = from_path([10, 11, 10.4, 11.5, 10.9, 12], per_leg=4)
    assert smc.structure_trend(bull) == "BULL"
    bear = from_path([12, 11, 11.6, 10.5, 11.1, 10], per_leg=4)
    assert smc.structure_trend(bear) == "BEAR"
    rng = flat(10, 30)
    assert smc.structure_trend(rng) is None


def test_bos_choch_no_lookahead_and_labels():
    # down leg, up leg menembus swing high, down lagi, up menembus lagi
    bars = from_path([10, 9, 11, 9.5, 11.5], per_leg=3)
    ev = smc.bos_choch(bars)
    assert ev, "harus ada event struktur"
    sw = smc.swings_seq(bars)
    for e in ev:
        # event tidak boleh terjadi sebelum swing yang ditembus terkonfirmasi
        confirmed = [i for i, t, p in sw
                     if (e["dir"] == "BULL" and t == "H" and e["level"] == p)
                     or (e["dir"] == "BEAR" and t == "L" and e["level"] == p)]
        assert any(i + smc.SWING_K <= e["idx"] for i in confirmed)
    # break pertama = BOS (belum ada karakter), pembalikan arah = CHoCH
    dirs = [e["dir"] for e in ev]
    assert ev[0]["type"] == "BOS"
    flips = [e for i, e in enumerate(ev) if i and e["dir"] != dirs[i - 1]]
    assert all(e["type"] == "CHoCH" for e in flips)


# ── likuiditas: sweep/SFP ───────────────────────────────────────────────────
def test_detect_sweep_sfp_and_rejection():
    lvl = 100.0
    bars = [_bar(100, 100, h=100.2, l=99.8) for _ in range(10)]
    assert smc.detect_sweep(bars, lvl, "H", 1.0) is None
    # wick menembus ke atas lalu close kembali di bawah → SFP
    bars[5] = _bar(100, 99.9, h=100.4, l=99.8)
    sw = smc.detect_sweep(bars, lvl, "H", 1.0)
    assert sw and sw["idx"] == 5 and sw["extreme"] == 100.4
    # close MENEMBUS level (break, bukan sweep) → bukan SFP
    bars2 = [_bar(100, 100, h=100.2, l=99.8) for _ in range(10)]
    bars2[5] = _bar(100, 100.6, h=100.8, l=99.9)
    assert smc.detect_sweep(bars2, lvl, "H", 1.0) is None


def test_equal_levels_clusters():
    bars = (flat(100, 12) + flat(101, 12, t0=3_000_000) +
            flat(100.05, 12, t0=4_000_000))
    lv = smc.equal_levels(bars, "H", 0.5)
    assert lv and lv[0][1] >= 3  # cluster 100/100.05 gabung


# ── zona: OB & FVG ──────────────────────────────────────────────────────────
def test_order_block_fresh_then_mitigated():
    # bear OB = candle bull TERAKHIR sebelum leg TURUN impulsif (supply zone,
    # rencana §2.4). Anatomi: rally 99.2→106.8 (9 bar) → drop impulsif ke 100.1
    # (6 bar) → bounce kecil (2 bar). ATR ~0.90 → gate 1.2xATR ~1.08; leg drop
    # 6.7 ✅. Swing H@9 (106.8, konfirmasi bar 10-11), L@14 (100.1, konfirmasi
    # bar 15-16). OB = bar 8 (o=105.9556, c=106.8) — candle bull terakhir.
    rally = from_path([99.2, 106.8], per_leg=9)
    drop = from_path([106.8, 100.1], per_leg=6)
    bounce = from_path([100.1, 100.9], per_leg=2)
    bars = rally + drop + bounce  # 17 bar → ATR(14) terhitung
    obs = [o for o in smc.order_blocks(bars) if o["type"] == "bear"]
    assert len(obs) == 1, f"tepat 1 bear OB: {obs}"
    ob = obs[0]
    assert ob["idx"] == 8
    exp_bottom = 99.2 + 7.6 * 8 / 9  # open bar 8
    assert abs(ob["top"] - 106.8) < 1e-9
    assert abs(ob["bottom"] - exp_bottom) < 1e-9
    assert ob["fresh"] is True  # belum ada close > top sejak leg selesai
    # close menembus DI ATAS zona → bear zone violated (mitigated)
    bars3 = bars + [_bar(105.5, 107.2, h=107.3, l=105.4)]
    obs3 = [o for o in smc.order_blocks(bars3) if o["type"] == "bear"
            and o["idx"] == ob["idx"]]
    assert obs3 and obs3[-1]["fresh"] is False


def test_ob_displacement_filter():
    # ATR window penuh ~0.9 (bar liar TR=10 + 23 bar TR~0.2): 1.2xATR ~1.08.
    # leg kecil 100.05→100.11 (0.06) JAUH di bawah → tidak boleh ada OB dari
    # leg kecil itu. Bar liar (TR=10) jauh di atas → jadi satu-satunya OB sah.
    noise = [_bar(100.05, 100.05, h=100.1, l=99.9) for _ in range(8)]
    wild = [_bar(100.05, 100.05, h=105.0, l=95.0)]
    quiet = [_bar(100.05, 100.05, h=100.1, l=99.9) for _ in range(14)]
    leg = [_bar(100.05, 100.08, h=100.09, l=100.03),
           _bar(100.08, 100.10, h=100.12, l=100.06),
           _bar(100.10, 100.11, h=100.13, l=100.08),
           _bar(100.11, 100.09, h=100.11, l=100.07),
           _bar(100.09, 100.08, h=100.10, l=100.06)]
    bars = noise + wild + quiet + leg
    obs = smc.order_blocks(bars)
    small = [o for o in obs if o["idx"] >= len(noise) + len(wild) + len(quiet)]
    assert not small, f"leg kecil tidak boleh membentuk OB: {small}"
    assert any(abs((o["top"] - o["bottom"]) - 10.0) < 1e-9 for o in obs), \
        "bar liar (range 10) harus jadi satu-satunya OB sah"


def test_fvg_fresh_and_filled():
    # bullish FVG: high[c1]=101.2 < low[c3]=101.3
    bars = [_bar(100, 100.5), _bar(100.5, 101.2, h=101.2, l=100.9),
            _bar(101.3, 101.8, l=101.3)]
    fs = smc.fvgs(bars)
    assert fs and fs[0]["type"] == "bull" and fs[0]["fresh"] is True
    # close turun DI BAWAH bottom → violated
    bars2 = bars + [_bar(101.4, 100.3, h=101.4, l=100.2)]
    assert smc.fvgs(bars2)[0]["fresh"] is False
    # sentuhan wick saja (low 100.7 > bottom) → TETAP fresh
    bars3 = bars + [_bar(101.4, 101.2, h=101.4, l=100.7)]
    assert smc.fvgs(bars3)[0]["fresh"] is True


def test_premium_discount():
    rng = from_path([100, 110, 105], per_leg=5)
    assert smc.premium_discount(rng, 104) == "DISCOUNT"
    assert smc.premium_discount(rng, 108) == "PREMIUM"
    assert smc.premium_discount(from_path([100, 100.1], per_leg=3), 100.05) is None


# ── engine end-to-end ───────────────────────────────────────────────────────
def _bull_market():
    """Pasar BULL utuh (angka dihitung tangan):
    - h4 30 bar: swing HH/HL → BULL; price 4217.72 < eq 4219.05 → DISCOUNT
    - m15: up-leg + flat; FVG bull segar 4217.63-4217.68 dekat harga (POI)
    - m5: leg naik (BOS BULL) + flat dengan dip 4217.40 (sweep EQL 4217.58)
    - m1: flat → dip → rally (CHoCH mikro BULL + three_white_soldiers)
    """
    h4 = from_path([4216.5, 4219.5, 4217.5, 4220.2, 4218.2, 4221.6], per_leg=6)
    m15 = (from_path([4215.0, 4218.5, 4216.0, 4219.0, 4217.0, 4217.6],
                     per_leg=5) + flat(4217.6, 30) +
           [_bar(4217.6, 4217.62, h=4217.63, l=4217.59),
            _bar(4217.62, 4217.64, h=4217.645, l=4217.61),
            _bar(4217.68, 4217.70, h=4217.71, l=4217.68)])
    m5 = (from_path([4217.0, 4219.2, 4217.3, 4217.6], per_leg=6) +
          flat(4217.6, 30, dip=(4217.40, 4217.62)))
    m1 = (flat(4217.6, 55) + from_path([4217.6, 4217.42], per_leg=2) +
          from_path([4217.42, 4217.72], per_leg=6))
    return m1, m5, m15, h4


def test_engine_takes_full_confluence_bull():
    r = smc.evaluate(*_bull_market())
    assert r["take"] is True, r["reason"]
    assert r["direction"] == "BUY"
    assert r["score"] == r["max_score"] == 12
    assert r["bias"] == "BULL" and r["pd"] == "DISCOUNT"
    # SL di bawah harga & beranchor struktural; RR >= 1.3
    assert r["sl"] < r["tp1"]
    assert r["rr"] >= smc.MIN_RR
    ok_keys = {c["k"] for c in r["checklist"] if c["ok"]}
    assert {"Liquidity sweep (SFP)", "CHoCH mikro M1 (30 bar terakhir)",
            "POI fresh (OB/FVG M15/M5)"} <= ok_keys


def test_engine_waits_when_h4_ranging():
    m1, m5, m15, _ = _bull_market()
    r = smc.evaluate(m1, m5, m15, flat(4218, 30))
    assert r["take"] is False
    assert "bias" in r["reason"]


def test_engine_rejects_when_no_liquidity_target():
    m1, m5, m15, h4 = _bull_market()
    # m5 flat total → tak ada swing/EQ di atas harga → TP1 None → no-trade
    r = smc.evaluate(m1, flat(4217.3, 80), m15, h4)
    assert r["take"] is False


def test_engine_shortdata_guard():
    r = smc.evaluate([], [], [], [])
    assert r["take"] is False and r["reason"] == "data TF kurang"


def test_engine_never_takes_with_inverted_sl():
    """Regresi replay 39 hari (13 trade): extrem sweep STALE di sisi SALAH
    dari harga jadi anchor SL (`ext < (sl_base or 1e9)` selalu true saat
    sl_base None) → BUY dengan sl > entry → RR palsu lolos gate, label 'SL'
    dengan gross positif. Sekarang: anchor sweep wajib di sisi yang benar
    dari harga sekarang + guard fail-closed terakhir."""
    m1, m5, m15, h4 = _bull_market()
    # harga diturunkan JAUH di bawah extrem sweep m5 (dip 4217.40):
    # sweep lama itu stale — tidak boleh jadi SL utk BUY di 4216.80
    m1 = m1 + from_path([4217.72, 4216.80], per_leg=4)
    r = smc.evaluate(m1, m5, m15, h4)
    if r["take"]:
        assert r["direction"] == "BUY"
        assert r["sl"] < m1[-1]["close"], f"SL terbalik utk BUY: {r}"
    else:
        # jalur sukses: reject dgn alasan SL struktural, BUKAN RR palsu
        assert "SL struktural" in r["reason"] or "RR" in r["reason"] or \
            "skor" in r["reason"]


def test_engine_sl_side_invariant_on_take():
    """Invariant sisi SL di semua fixture engine: BUY → sl < close terakhir,
    SELL → sl > close terakhir (dipanggil di beberapa pasar)."""
    m1, m5, m15, h4 = _bull_market()
    for m1_var in (m1, m1 + from_path([4217.72, 4216.9], per_leg=3)):
        r = smc.evaluate(m1_var, m5, m15, h4)
        if r["take"]:
            last = float(m1_var[-1]["close"])
            if r["direction"] == "BUY":
                assert r["sl"] < last, f"sl {r['sl']} >= entry {last}: {r}"
            else:
                assert r["sl"] > last, f"sl {r['sl']} <= entry {last}: {r}"


# ── struktural: whitelist import (konvensi repo) ────────────────────────────
def test_smc_import_whitelist():
    src = open("strategy_v2/smc.py", encoding="utf-8").read()
    tree = ast.parse(src)
    allowed = {"candle_scoring", "simple_variants", "micro_v2"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(a.name.split(".")[0] in allowed for a in node.names), \
                f"import non-whitelist: {node.names}"
        elif isinstance(node, ast.ImportFrom) and node.module:
            top = node.module.split(".")[0]
            assert top in allowed | {"strategy_v2", "typing", "__future__"}, \
                f"import non-whitelist: {node.module}"
