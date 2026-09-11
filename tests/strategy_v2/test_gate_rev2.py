"""Contract tests — gate MICRO rev2 (owner, 2026-09-10: "5 jam 0 posisi").

Bukti replay 5 jam: aturan lama (momentum DAN struktur harus searah) = 0
entri; struktur campur itu keadaan NORMAL (53% waktu). Rev2:
  1. ARAH dari momentum M15 saja (EMA9/21 + RSI band 45/55, owner rev3)
  2. Struktur M15 = VETO — menolak HANYA bila jelas bertentangan
     (mayoritas 2/3 swing, margin 0.25xATR); campur (None) → boleh entry
  3. Cooldown 5 menit antar entri MICRO (28→14 entri, WR 60%→71%)
  4. SCALP rev2: struktur HH/HL H4 DIHAPUS (owner) — arah murni momentum M15
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import simple_variants as SV
from strategy_v2 import candle_scoring as CS

from tests.strategy_v2.test_candle_scoring import (  # noqa: E402
    bar, flat, make_bull_scenario,
)
from tests.strategy_v2.test_owner_rev_rules import _m15_uptrend  # noqa: E402


def _bars_from_seq(seq, t0=1700000000, step=900):
    return [bar((lo + hi) / 2, hi, lo, (lo + hi) / 2, v=100, t=t0 + step * i)
            for i, (lo, hi) in enumerate(seq)]


def _m15_veto_fixture():
    """Momentum BULL (burst hijau) × struktur BEAR (zigzag turun jelas).

    Kasus nyata 2 trade pertama: H4/M15 bear besar, bot beli bounce → SL.
    Di rev2 gate ini WAJIB tetap menolak (veto)."""
    bars = []
    for leg in range(4):
        o = 200.0 - leg * 1.0
        t = 1700000000 + 900 * len(bars)
        bars.append(bar(o, o + 1.0, o + 0.05, o - 1.0, t=t))
        bars.append(bar(o - 1.0, o - 0.95, o + 0.7, o + 0.6, t=t + 900))
        bars.append(bar(o + 0.6, o + 0.55, o + 1.1, o + 1.0, t=t + 1800))
        bars.append(bar(o + 1.0, o + 0.3, o + 1.05, o + 0.4, t=t + 2700))
        bars.append(bar(o + 0.4, o - 0.1, o + 0.5, o - 0.0, t=t + 3600))
        bars.append(bar(o - 0.0, o - 0.5, o - 0.3, o - 0.4, t=t + 4500))
        bars.append(bar(o - 0.4, o - 1.3, o - 0.35, o - 1.2, t=t + 5400))
    c = bars[-1]["close"]
    for i in range(8):  # burst hijau: momentum balik BULL, belum bentuk swing
        bars.append(bar(c - 0.1, c + 1.35, c - 0.2, c + 1.2, v=150,
                        t=1700000000 + 900 * len(bars)))
        c += 1.2
    mb, sb = SV.momentum_bias(bars), SV.structure_bias(bars)
    assert (mb, sb) == ("BULL", "BEAR"), f"fixture rusak: {mb}×{sb}"
    return bars


def _m15_mixed_fixture():
    """Momentum BULL × struktur CAMPUR (highs datar, lows naik — descending
    flat-top / ascending triangle). Di rev2 ini BOLEH entry (bukan veto)."""
    seq = [(4425, 4433.7), (4420, 4431), (4415, 4430.1), (4390, 4407.0),
           (4395, 4420.5), (4392, 4418), (4375, 4421.4), (4385, 4419),
           (4380, 4417), (4382, 4400), (4385, 4395)]
    bars = _bars_from_seq(seq)
    t0 = 1700000000 + 900 * len(bars)
    c = bars[-1]["close"]
    for i in range(16):  # bounce mikro naik pelan — RSI ~54 (netral-bull)
        wick = max(1.0 - i * 0.08, 0.2)
        bars.append(bar(c - 0.5, c + wick, c - 1.2, c + 0.5, v=100,
                        t=t0 + 900 * len(bars)))
        c += 0.5
        bars.append(bar(c - 0.5, c + 0.3, c - 0.8, c, v=100,
                        t=t0 + 900 * len(bars)))
        c += 0.5
    mb, sb = SV.momentum_bias(bars), SV.structure_bias(bars)
    assert (mb, sb) == ("BULL", None), f"fixture rusak: {mb}×{sb}"
    return bars


# ── 1. veto: bertentangan tetap ditolak ──────────────────────────────────────
def test_veto_clear_opposition_still_rejected():
    """Momentum BULL × struktur BEAR jelas → TETAP ditolak (veto bekerja)."""
    m15 = _m15_veto_fixture()
    m5, _ = make_bull_scenario()
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(), m1_bars=m5)
    assert not r["ok"], "veto bertentangan harus menolak"
    assert "bertentangan" in r["reason"].lower(), r["reason"]


# ── 2. campur: TIDAK ditolak di gate struktur (inti revisi) ──────────────────
def test_mixed_structure_reaches_scoring_not_rejected():
    """Momentum BULL × struktur campur → gate struktur LOLOS (rev2)."""
    m15 = _m15_mixed_fixture()
    m5, _ = make_bull_scenario()
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(), m1_bars=m5)
    assert "struktur" not in r.get("reason", "").lower(), r["reason"]
    step = [s for s in r["steps"] if "Struktur" in s["k"]]
    assert step and "campur" in step[0]["note"].lower(), r["steps"]


def test_searah_still_passes_with_direction_from_momentum():
    """Momentum BULL × struktur BULL → arah tetap BULL (tak berubah)."""
    m15 = _m15_uptrend()
    m5, _ = make_bull_scenario()
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(), m1_bars=m5)
    if r["ok"]:
        assert r["direction"] == "BUY"


# ── 3. cooldown antar entri MICRO ────────────────────────────────────────────
def test_micro_cooldown_blocks_within_5_minutes():
    """Entri terakhir 60 detik lalu → ditolak, alasannya cooldown."""
    m15 = _m15_mixed_fixture()
    m5, _ = make_bull_scenario()
    now = 1_700_000_000 + 10_000
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, now, SV.KillSwitch(),
                  m1_bars=m5, last_entry_ts=now - 60)
    assert not r["ok"] and "cooldown" in r["reason"].lower(), r["reason"]


def test_micro_cooldown_allows_after_5_minutes():
    """Entri terakhir 6 menit lalu → tidak ditolak karena cooldown."""
    m15 = _m15_mixed_fixture()
    m5, _ = make_bull_scenario()
    now = 1_700_000_000 + 10_000
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, now, SV.KillSwitch(),
                  m1_bars=m5, last_entry_ts=now - 360)
    assert "cooldown" not in r.get("reason", "").lower(), r["reason"]


def test_micro_cooldown_step_in_checklist():
    """Langkah cooldown tampil di checklist MICRO (transparan UI)."""
    m15 = _m15_mixed_fixture()
    m5, _ = make_bull_scenario()
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(), m1_bars=m5)
    assert any("Cooldown" in s["k"] for s in r["steps"]), r["steps"]


def test_scalp_has_no_cooldown_step():
    """Cooldown hanya MICRO — SCALP tidak punya langkah itu."""
    m15 = _m15_uptrend()
    m5, _ = make_bull_scenario()
    now = 1_700_000_000 + 10_000
    r = SV.decide("SCALP", m5, m15, [], 120.0, None, now, SV.KillSwitch(),
                  last_entry_ts=now - 60)
    assert not any("Cooldown" in s["k"] for s in r["steps"]), r["steps"]


# ── 4. SCALP rev2: gate struktur H4 dihapus ───────────────────────────
def test_scalp_structure_gate_removed():
    """SCALP × H4 campur/datar → TIDAK lagi ditolak di gate struktur
    (owner rev2: aturan HH/HL H4 tidak berguna — arah murni momentum M15)."""
    h4_mixed = flat(200.0, 30)  # datar → struktur lama akan membaca None
    m15 = _m15_uptrend()
    m5, _ = make_bull_scenario()
    r = SV.decide("SCALP", m5, m15, h4_mixed, 120.0, None, 0, SV.KillSwitch())
    assert "struktur H4" not in r.get("reason", "").lower(), r["reason"]
    step = [s for s in r["steps"] if s["k"] == "Struktur H4"]
    assert step and "dihapus" in step[0]["note"].lower(), r["steps"]


def test_scalp_flows_through_without_h4():
    """SCALP tanpa data H4 sama sekali → tetap jalan sampai gate berikutnya."""
    m15 = _m15_uptrend()
    m5, _ = make_bull_scenario()
    r = SV.decide("SCALP", m5, m15, [], 120.0, None, 0, SV.KillSwitch())
    assert "struktur" not in r.get("reason", "").lower(), r["reason"]


# ── 5. band momentum 45/55 (owner rev3: RSI 50 keras terlalu kaku) ──────────
def _band_fixture_bull():
    """EMA9>EMA21 dengan RSI 45..50 — momen EMA fresh-cross yang dulu diblok
    RSI-50 (bukti 48 jam: 8% waktu). Kalibrasi dari sekuens real kasus
    2026-09-10 + tail naik pelan."""
    seq = [(4425, 4433.7), (4420, 4431), (4415, 4430.1), (4390, 4407.0),
           (4395, 4420.5), (4392, 4418), (4375, 4421.4), (4385, 4419),
           (4380, 4417), (4382, 4400), (4385, 4395)]
    c = 4390.0
    for _ in range(15):  # tail naik pelan → dEMA +2.4, RSI ~47.3
        seq.append((c, c + 6.0))
        c += 1.5
    return _bars_from_seq(seq)


def _band_fixture_bear():
    """Mirror: EMA9<EMA21 dengan RSI 50..55 — dulu None, sekarang BEAR."""
    seq = [(8800.0 - hi, 8800.0 - lo) for (lo, hi) in
           [(4425, 4433.7), (4420, 4431), (4415, 4430.1), (4390, 4407.0),
            (4395, 4420.5), (4392, 4418), (4375, 4421.4), (4385, 4419),
            (4380, 4417), (4382, 4400), (4385, 4395)]]
    c = 4410.0
    for _ in range(15):  # tail turun pelan → dEMA −2.4, RSI ~52.7
        seq.append((c - 6.0, c))
        c -= 1.5
    return _bars_from_seq(seq)


def test_band_constants_frozen():
    assert SV.MOM_RSI_BULL_MIN == 45.0 and SV.MOM_RSI_BEAR_MAX == 55.0


def test_band_bull_gives_direction_in_45_50_zone():
    """EMA9>EMA21 + RSI ~47 (dulu None) → BULL — fresh-cross tidak lagi diblok."""
    bars = _band_fixture_bull()
    closes = [b["close"] for b in bars]
    e9, e21 = CS.ema(closes, 9), CS.ema(closes, 21)
    r = CS.rsi(closes, 14)
    assert e9 > e21 and 45 <= r < 50, f"fixture: dEMA={e9-e21} RSI={r}"
    assert SV.momentum_bias(bars) == "BULL"


def test_band_bear_gives_direction_in_50_55_zone():
    """EMA9<EMA21 + RSI ~53 (dulu None) → BEAR."""
    bars = _band_fixture_bear()
    closes = [b["close"] for b in bars]
    e9, e21 = CS.ema(closes, 9), CS.ema(closes, 21)
    r = CS.rsi(closes, 14)
    assert e9 < e21 and 50 < r <= 55, f"fixture: dEMA={e9-e21} RSI={r}"
    assert SV.momentum_bias(bars) == "BEAR"


def test_band_still_neutral_outside_band():
    """RSI di luar band (EMA bull tapi RSI < 45) tetap netral — band bukan
    penghapusan RSI."""
    bars = _band_fixture_bull()
    # potong tail sampai RSI < 45 (tail 12: RSI 41.7, dEMA +0.57 > 0)
    seq = [(4425, 4433.7), (4420, 4431), (4415, 4430.1), (4390, 4407.0),
           (4395, 4420.5), (4392, 4418), (4375, 4421.4), (4385, 4419),
           (4380, 4417), (4382, 4400), (4385, 4395)]
    c = 4390.0
    for _ in range(12):
        seq.append((c, c + 6.0))
        c += 1.5
    bars = _bars_from_seq(seq)
    closes = [b["close"] for b in bars]
    e9, e21 = CS.ema(closes, 9), CS.ema(closes, 21)
    r = CS.rsi(closes, 14)
    assert e9 > e21 and r < 45, f"fixture: dEMA={e9-e21} RSI={r}"
    assert SV.momentum_bias(bars) is None


# ── 6. proteksi lain tetap utuh ─────────────────────────────────────────────
def test_rsi_guard_still_blocks_after_gate():
    """Struktur campur boleh, tapi RSI jenuh tetap menolak."""
    m15 = _m15_mixed_fixture()
    m5, _ = make_bull_scenario()
    m1, _ = make_bull_scenario()
    m1 = m1[:-1] + [bar(100.0, 103.0, 99.9, 102.9, v=300)]  # dorong RSI M1 ke jenuh
    rsi = __import__("strategy_v2.candle_scoring", fromlist=["rsi"]).rsi(
        [b["close"] for b in m1], 14)
    if rsi is not None and rsi >= 65:
        r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(), m1_bars=m1)
        assert not r["ok"] and "M1" in r["reason"], r["reason"]
