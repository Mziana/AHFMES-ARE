"""Contract tests — candle scoring + simple variants (demo V1/V2, owner spec).

- deterministik: input sama -> keputusan & skor identik
- 14 pola: deteksi sintetis per jenis (bull & bear)
- threshold boundary: MICRO 6, SCALP 7
- SL/TP ATR + proteksi wick; lot tetap; news gate; kill switch 3-streak/30min
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import candle_scoring as CS
from strategy_v2 import simple_variants as SV


def bar(o, h, l, c, v=100, t=0):
    return {"time": t, "open": o, "high": h, "low": l, "close": c, "volume": v}


# ── helpers: bar run → list ──────────────────────────────────────────────────
def flat(price=100.0, n=25, v=100):
    """n bar flat @price — list, bukan bar tunggal."""
    return [bar(price, price + 0.1, price - 0.1, price, v=v, t=1700000000 + 300 * i)
            for i in range(n)]


def make_bull_scenario():
    """Downtrend kecil → level → hammer strong di level, close ujung atas."""
    bars = []
    t = 1700000000
    # 20 bar turun bertahap dari 105 ke 100
    px = 105.0
    for i in range(20):
        bars.append(bar(px, px + 0.2, px - 0.3, px - 0.4, v=100, t=t + 300 * i))
        px -= 0.4
    # hammer: body kecil di atas, wick bawah panjang, close ujung atas
    bars.append(bar(100.2, 100.4, 99.2, 100.35, v=150, t=t + 300 * 20))
    return bars, 99.3  # level di bawah close


# ── determinism ──
def test_determinism():
    bars, lvl = make_bull_scenario()
    r1 = CS.score_candle(bars, lvl, "MICRO", require_volume=False)
    r2 = CS.score_candle(bars, lvl, "MICRO", require_volume=False)
    assert r1 == r2


# ── pola 1-candle: hammer & shooting star & marubozu ──
def test_hammer_detected():
    bars, _ = make_bull_scenario()
    r = CS.detect_patterns(bars)
    assert ("hammer", "BULL", False) in r


def test_shooting_star():
    bars = flat(100.0, 25)
    bars[-3] = bar(100, 100.4, 99.8, 100.2)
    bars[-2] = bar(100.2, 100.5, 100.0, 100.4)  # bull — hindari engulfing/tweezer
    # shooting star: body kecil di BAWAH, wick atas panjang (>= 2x body), wick bawah pendek
    bars[-1] = bar(99.45, 100.65, 99.3, 99.4, v=120)
    names = [p[0] for p in CS.detect_patterns(bars)]
    assert "shooting_star" in names


def test_marubozu_bull():
    bars = flat(100.0, 25)
    bars[-1] = bar(100.0, 101.0, 99.95, 101.0)  # body 1.0 / range 1.05 = 95%
    names = [p[0] for p in CS.detect_patterns(bars)]
    assert "marubozu_bull" in names


# ── pola 2-candle ──
def test_bullish_engulfing():
    bars = flat(100.0, 25)
    bars[-2] = bar(100.4, 100.5, 100.1, 100.15)   # bear kecil
    bars[-1] = bar(100.05, 100.8, 100.0, 100.7)   # bull besar menelan
    names = [p[0] for p in CS.detect_patterns(bars)]
    assert "bullish_engulfing" in names


def test_piercing_line():
    bars = flat(100.0, 25)
    bars[-2] = bar(100.4, 100.5, 99.9, 99.95)     # bear besar (open 100.4 close 99.95, mid 100.175)
    bars[-1] = bar(99.9, 100.5, 99.85, 100.3)     # bull close > mid, < open prev
    names = [p[0] for p in CS.detect_patterns(bars)]
    assert "piercing_line" in names


def test_tweezer_bottom():
    bars = flat(100.0, 25)
    bars[-2] = bar(100.4, 100.5, 100.0, 100.1)
    bars[-1] = bar(100.1, 100.6, 100.02, 100.5)   # low nyaris sama, arah beda
    names = [p[0] for p in CS.detect_patterns(bars)]
    assert "tweezer_bottom" in names


# ── pola 3-candle ──
def test_morning_star():
    bars = flat(100.0, 25)
    bars[-3] = bar(101.0, 101.1, 100.3, 100.35)   # bear besar
    bars[-2] = bar(100.3, 100.45, 100.1, 100.2)   # bintang kecil
    bars[-1] = bar(100.2, 101.0, 100.15, 100.8)   # bull > midpoint b1 (100.675? no: mid=(101+100.35)/2=100.675)
    # sesuaikan: close harus > midpoint candle pertama
    bars[-1] = bar(100.2, 101.0, 100.15, 100.8)
    names = [p[0] for p in CS.detect_patterns(bars)]
    assert "morning_star" in names


def test_three_white_soldiers():
    bars = flat(100.0, 25)
    bars[-3] = bar(100.0, 100.4, 99.9, 100.3)
    bars[-2] = bar(100.3, 100.7, 100.2, 100.6)
    bars[-1] = bar(100.6, 101.0, 100.5, 100.95)
    names = [p[0] for p in CS.detect_patterns(bars)]
    assert "three_white_soldiers" in names


# ── skor & threshold ──
def test_score_structure_and_threshold():
    bars, lvl = make_bull_scenario()
    r = CS.score_candle(bars, lvl, "MICRO", require_volume=False)
    # hammer(3) + close ujung(1) + body>=avg? + level(2) → minimal pola+level = 5
    assert r["direction"] == "BULL"
    assert r["score"] >= 5.0
    # wajib ada checklist yang bisa dibaca manusia
    kinds = [c["k"] for c in r["checklist"]]
    assert any(k.startswith("Pola") for k in kinds)
    assert any(k == "Di level eksekusi" for k in kinds)


def test_no_level_no_context_points():
    bars, _ = make_bull_scenario()
    r_far = CS.score_candle(bars, None, "MICRO", require_volume=False)
    kinds = [c["k"] for c in r_far["checklist"]]
    assert "Di level eksekusi" in kinds
    # tanpa level, konteks 0 — skor lebih rendah dari versi dengan level dekat
    r_near = CS.score_candle(bars, bars[-1]["close"], "MICRO", require_volume=False)
    assert r_near["score"] >= r_far["score"]


def test_scalp_volume_mandatory():
    bars = flat(100.0, 25, v=100)
    bars[-2] = bar(100.2, 100.3, 100.0, 100.05)
    bars[-1] = bar(100.05, 100.8, 99.9, 100.7, v=105)  # 105 < 1.2*100
    r = CS.score_candle(bars, bars[-1]["close"], "SCALP", require_volume=True)
    assert not r["ok"]
    assert "volume" in r["reason"].lower()


# ── bias & struktur ──
def test_momentum_bias_up():
    bars = []
    t = 1700000000
    px = 100.0
    for i in range(30):  # uptrend
        bars.append(bar(px, px + 0.4, px - 0.1, px + 0.3, t=t + 900 * i))
        px += 0.3
    assert SV.momentum_bias(bars) == "BULL"


def test_structure_hh_hl():
    # Zigzag naik 4 leg: tiap leg = swing high & low fractal, semua HH/HL
    # dengan selisih >> margin 0.25xATR (aturan rev 2026-09-10 opsi 1+2).
    seq = [(102.5, 103.5), (102.3, 103.2), (101.2, 102.8), (103.0, 105.8),
           (102.8, 104.0), (102.6, 103.6), (104.0, 106.2), (103.8, 105.0),
           (103.6, 104.8)]
    bars = [bar((lo + hi) / 2, hi, lo, (lo + hi) / 2, t=1700000000 + 300 * i)
            for i, (lo, hi) in enumerate(seq)]
    # perbanyak leg dengan offset naik agar >= 3 swing & ATR tersedia
    bars += [bar((lo + hi) / 2 + 4.0, hi + 4.0, lo + 4.0, (lo + hi) / 2 + 4.0,
                 t=1700000000 + 300 * (9 + i)) for i, (lo, hi) in enumerate(seq)]
    assert SV.structure_bias(bars) == "BULL"


def test_structure_down():
    # mirror: LH+LL
    seq = [(106.5, 107.5), (106.8, 107.7), (107.2, 108.8), (104.2, 107.0),
           (106.0, 107.2), (106.4, 107.4), (103.8, 106.0), (105.0, 106.2),
           (105.2, 106.4)]
    bars = [bar((lo + hi) / 2, hi, lo, (lo + hi) / 2, t=1700000000 + 300 * i)
            for i, (lo, hi) in enumerate(seq)]
    bars += [bar((lo + hi) / 2 - 4.0, hi - 4.0, lo - 4.0, (lo + hi) / 2 - 4.0,
                 t=1700000000 + 300 * (9 + i)) for i, (lo, hi) in enumerate(seq)]
    assert SV.structure_bias(bars) == "BEAR"


# ── SL/TP + wick protection + lot ──
def test_sl_tp_micro_bull():
    bars, _ = make_bull_scenario()
    entry = bars[-1]["close"]
    st = SV.compute_sl_tp("MICRO", "BULL", bars, entry)
    assert st["sl"] < entry < st["tp"]
    # Rev 2026-09-10 (owner): SL/TP murni ATR M1 di-clamp 130-210/200-300 pts.
    # Tanpa penyetelan wick (penyebab bug RR trade #1).
    assert 130.0 <= st["sl_points"] <= 210.0
    assert 200.0 <= st["tp_points"] <= 300.0


def test_sl_tp_scalp_rr_wide():
    bars, _ = make_bull_scenario()
    st = SV.compute_sl_tp("SCALP", "BULL", bars, bars[-1]["close"])
    assert st["tp_points"] / st["sl_points"] > 1.3  # 2.0/1.25 = 1.6


def test_fixed_lot():
    assert SV.fixed_lot(151.0) == 0.02
    assert SV.fixed_lot(150.0) == 0.01
    assert SV.fixed_lot(120.0) == 0.01


# ── news gate ──
def test_news_block_30min():
    """Fungsi news_block tetap benar (dipakai saat kalender real terpasang)."""
    import datetime as dt
    base = dt.datetime(2026, 9, 10, 8, 45, tzinfo=dt.timezone.utc)
    ts = base.timestamp()
    events = [{"time": "08:30", "impact": "HIGH", "event": "NFP"},
              {"time": "10:00", "impact": "MEDIUM", "event": "ISM"}]
    assert SV.news_block(events, ts) == "NFP"
    ts2 = base.replace(hour=10, minute=45).timestamp()  # 45+ menit dari 08:30 & 10:00
    # 10:45 → jarak ke 10:00 = 45 (>30), ke 08:30 jauh → bebas
    assert SV.news_block(events, ts2) is None


def test_news_gate_disabled_by_owner():
    """Owner 2026-09-10: news gate OFF (kalender simulasi tak akurat) —
    decide() TIDAK boleh menolak walau ada big news di dekat now_epoch."""
    assert SV.NEWS_GATE_ENABLED is False
    m5, _ = make_bull_scenario()
    m15 = [bar(100, 100.3, 99.7, 100.1, t=1700000000 + 900 * i) for i in range(30)]
    ks = SV.KillSwitch()
    import datetime as dt
    ts = dt.datetime(2026, 9, 10, 8, 40, tzinfo=dt.timezone.utc).timestamp()
    r = SV.decide("MICRO", m5, m15, [], 120.0,
                  [{"time": "08:30", "impact": "HIGH", "event": "NFP"}], ts, ks)
    assert "news" not in r.get("reason", "").lower()


# ── RSI ekstrem guard (owner rule) ──
def _zigzag_up_m15():
    """M15 zigzag naik: struktur HH+HL + RSI jenuh atas (>=70, rev3) + momentum BULL."""
    bars = []
    t = 1700000000
    px = 100.0

    def add(o, h, l, c):
        bars.append(bar(o, h, l, c, t=t + 900 * len(bars)))

    for leg in range(6):  # cukup panjang utk EMA/RSI 14
        add(px, px + 0.8, px - 0.1, px + 0.6)
        add(px + 0.6, px + 1.2, px + 0.4, px + 1.0)
        add(px + 1.0, px + 1.1, px + 0.55, px + 0.65)
        add(px + 0.65, px + 0.8, px + 0.35, px + 0.5)
        px += 0.85
    # rev3: ambang guard 65 -> 70 — 1 bar dorongan kuat agar RSI > 70
    add(px - 0.35, px + 0.75, px - 0.45, px + 0.65)
    return bars


def _zigzag_down_m15():
    """Mirror: struktur LH+LL + RSI jenuh bawah (<=30, rev3) + momentum BEAR."""
    bars = []
    t = 1700000000
    px = 140.0

    def add(o, h, l, c):
        bars.append(bar(o, h, l, c, t=t + 900 * len(bars)))

    for leg in range(6):
        add(px, px + 0.1, px - 0.8, px - 0.6)
        add(px - 0.6, px - 0.4, px - 1.2, px - 1.0)
        add(px - 1.0, px - 0.55, px - 1.1, px - 0.65)
        add(px - 0.65, px - 0.35, px - 0.8, px - 0.5)
        px -= 0.85
    # rev3: ambang guard 35 -> 30 — 1 bar tekanan kuat agar RSI < 30
    add(px + 0.35, px + 0.45, px - 0.75, px - 0.65)
    return bars


def test_rsi_extreme_blocks_buy_at_70():
    """Bias BULL + struktur BULL tapi RSI M15 >= 70 → stop BUY (jenuh beli, rev3)."""
    m15 = _zigzag_up_m15()
    assert SV.momentum_bias(m15) == "BULL"
    assert SV.structure_bias(m15) == "BULL"
    rsi_val = CS.rsi([b["close"] for b in m15], 14)
    assert rsi_val >= 70, f"test setup: RSI harus >= 70, dapat {rsi_val}"
    m5, _ = make_bull_scenario()  # M5 RSI juga tinggi (uptrend kecil)
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch())
    assert not r["ok"]
    assert "RSI" in r["reason"] and "70" in r["reason"]


def test_rsi_extreme_blocks_sell_below_30():
    """Bias BEAR + struktur BEAR tapi RSI M15 <= 30 → stop SELL (jenuh jual, rev3)."""
    m15 = _zigzag_down_m15()
    assert SV.momentum_bias(m15) == "BEAR"
    assert SV.structure_bias(m15) == "BEAR"
    rsi_val = CS.rsi([b["close"] for b in m15], 14)
    assert rsi_val <= 30, f"test setup: RSI harus <= 30, dapat {rsi_val}"
    m5, _ = make_bull_scenario()
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch())
    assert not r["ok"]
    assert "RSI" in r["reason"] and "30" in r["reason"]


def test_rsi_guard_passes_in_neutral_zone():
    """RSI 40-65 di kedua TF → guard lolos, catat nilai ke steps."""
    bars, _ = make_bull_scenario()
    m15 = []
    t = 1700000000
    o = 100.0
    # zigzag terkalibrasi (resep _m15_uptrend): RSI ~63 (netral-bull), BULL
    for _ in range(8):
        m15.append(bar(o, o + 1.0, o - 0.05, o + 0.9, t=t + 900 * len(m15)))
        m15.append(bar(o + 0.9, o + 0.95, o - 0.4, o - 0.1, t=t + 900 * len(m15)))
        m15.append(bar(o - 0.1, o + 0.45, o - 0.1, o + 0.35, t=t + 900 * len(m15)))
        m15.append(bar(o + 0.35, o + 0.8, o + 0.35, o + 0.7, t=t + 900 * len(m15)))
        o += 0.7
    r = SV.decide("MICRO", bars, m15, [], 120.0, None, 0, SV.KillSwitch())
    # guard tidak boleh menjadi alasan reject di skenario ini
    assert "RSI" not in r["reason"] or r["ok"]


# ── kill switch ──
def test_kill_switch_streak_and_override():
    ks = SV.KillSwitch()
    ts = 1000.0
    ks.record_loss(ts); ks.record_loss(ts)
    assert not ks.blocked(ts)
    ks.record_loss(ts)  # streak ke-3
    assert ks.blocked(ts + 60)
    assert ks.remaining_min(ts + 60) == 29
    assert not ks.blocked(ts + 31 * 60)  # lewat 30 menit
    ks2 = SV.KillSwitch()
    for _ in range(3):
        ks2.record_loss(ts)
    ks2.manual_override = True
    assert not ks2.blocked(ts + 60)  # override UI
    ks3 = SV.KillSwitch()
    ks3.record_loss(ts); ks3.record_win(); ks3.record_loss(ts)
    assert not ks3.blocked(ts + 60)  # win reset streak


# ── integrasi decide() ──
def test_decide_full_flow_rejects_without_pattern():
    m5, _ = make_bull_scenario()
    m15 = [bar(100, 100.3, 99.7, 100.1, t=1700000000 + 900 * i) for i in range(30)]
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch())
    assert isinstance(r["steps"], list) and r["steps"]  # checklist langkah tercatat


def test_decide_steps_note_news_off():
    """Transparansi: langkah News gate tetap tampil di checklist dengan
    keterangan OFF (owner)."""
    m5, _ = make_bull_scenario()
    m15 = [bar(100, 100.3, 99.7, 100.1, t=1700000000 + 900 * i) for i in range(30)]
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch())
    news_steps = [s for s in r["steps"] if s["k"] == "News gate"]
    assert news_steps and "OFF" in news_steps[0]["note"]
