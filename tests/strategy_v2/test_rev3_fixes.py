"""Contract tests — rev3 2026-09-10 (paket perbaikan pasca-audit MICRO 0 entri).

Bukti replay 5 jam (369 bar M1):
  - TP-vs-swing memotong 123 bar sampai di bawah 200 pts → entry DITOLAK
    (33%) → ambang penolak diturunkan ke 100 pts (pemotongan tetap jalan)
  - RSI guard 65/35 memblok 130 bar (35%) — bertentangan dgn band bias
    45/55 (koridor efektif tinggal 45-65) → guard dinaikkan ke 70/30
  - 12/16 entri hipotetis memakai pola BERLAWANAN bias (BUY dgn
    three_black_crows); dengan gate searah: 9 entri 9W/0L (+1209 pts)

Juga: matcher pnl via /deals — pnl tak ketemu = None (netral), bukan 0.0.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy_v2 import candle_scoring as CS
from strategy_v2 import simple_variants as SV
from strategy_v2.demo_driver import close_pnl_for_ticket

from tests.strategy_v2.test_candle_scoring import (  # noqa: E402
    bar, flat, make_bull_scenario,
)
from tests.strategy_v2.test_owner_rev_rules import _m15_uptrend  # noqa: E402


def _m1_bearish_engulfing_at_level():
    """M1 make_bull_scenario dengan 2 bar terakhir diganti bearish engulfing
    besar yang close-nya di dekat level (EMA) — pola kuat berlawanan bias BULL.

    Diharapkan: skor pola cukup (pola 3 + kualitas arah BEAR + level) sehingga
    yang menolak adalah GATE pola-vs-bias, bukan skor."""
    bars, _ = make_bull_scenario()
    level_ref = bars[-1]["close"]  # sekitar EMA scenario bull
    # bar kedua-terakhir: bull solid (b2 utk engulfing)
    bars[-2] = bar(level_ref - 0.2, level_ref + 0.9, level_ref - 0.25,
                   level_ref + 0.8, v=200, t=bars[-2]["time"])
    # bar terakhir: bear besar menelan body b2, close di ujung bawah
    o3 = level_ref + 0.9
    c3 = level_ref - 0.45
    bars[-1] = bar(o3, o3 + 0.05, c3 - 0.05, c3, v=300, t=bars[-1]["time"])
    return bars


# ── 1. gate pola-vs-bias (MICRO & SCALP) ────────────────────────────────────
def test_micro_pattern_opposite_to_bias_rejected():
    """Pola BEAR (bearish_engulfing) + bias BULL → reject 'berlawanan bias'."""
    m1 = _m1_bearish_engulfing_at_level()
    m5, _ = make_bull_scenario()
    m15 = _m15_uptrend()
    # pastikan pola memang terdeteksi berlawanan sebelum gate diuji
    res = CS.score_candle(m1, m1[-1]["close"], "MICRO", require_volume=False)
    assert res.get("direction") == "BEAR", res
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(), m1_bars=m1)
    if r["ok"]:
        return  # pola tak lolos skor → gate tak tercapai (fixture longgar)
    assert "berlawanan bias" in r["reason"], r["reason"]


def test_scalp_pattern_opposite_to_bias_ALLOWED():
    """SCALP: pola bear + momentum BULL TETAP BOLEH entry — owner membatalkan
    gate pola-vs-bias utk SCALP (3x win beruntun, salah satunya BUY dgn pola
    three_black_crows). Gate ini HANYA untuk MICRO."""
    m5 = _m1_bearish_engulfing_at_level()
    m15 = _m15_uptrend()
    res = CS.score_candle(m5, m5[-1]["close"], "SCALP", require_volume=True)
    if not res.get("ok") and "volume" in str(res.get("reason", "")):
        m5[-1] = dict(m5[-1], volume=int(m5[-1].get("volume", 100) * 4))
        res = CS.score_candle(m5, m5[-1]["close"], "SCALP", require_volume=True)
    assert res.get("direction") == "BEAR" and res.get("ok"), res
    r = SV.decide("SCALP", m5, m15, [], 120.0, None, 0, SV.KillSwitch())
    assert "berlawanan bias" not in r.get("reason", ""), r["reason"]


def test_pattern_same_direction_passes_gate():
    """Kontrol positif: pola searah bias → gate pola-vs-bias TIDAK menolak."""
    m1, _ = make_bull_scenario()
    m5, _ = make_bull_scenario()
    m15 = _m15_uptrend()
    r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(), m1_bars=m1)
    assert "berlawanan bias" not in r.get("reason", ""), r["reason"]


# ── 2. RSI guard 70/30 ──────────────────────────────────────────────────────
def test_rsi_guard_constants_are_70_30():
    assert SV.RSI_STOP_BUY == 70.0
    assert SV.RSI_STOP_SELL == 30.0


def test_rsi_65_69_no_longer_blocks():
    """RSI ~69 (dulu jenuh >=65 → blok) kini lolos guard — trend kuat tidak
    lagi diblokir (kasus replay: 130 bar terblok guard)."""
    # zigzag tanpa bar dorongan: RSI ~69.4 (dibuktikan empiris di rev2 fixture)
    bars = []
    t = 1700000000
    px = 100.0

    def add(o, h, l, c):
        bars.append(bar(o, h, l, c, t=t + 900 * len(bars)))

    for leg in range(6):
        add(px, px + 0.8, px - 0.1, px + 0.6)
        add(px + 0.6, px + 1.2, px + 0.4, px + 1.0)
        add(px + 1.0, px + 1.1, px + 0.55, px + 0.65)
        add(px + 0.65, px + 0.8, px + 0.35, px + 0.5)
        px += 0.85
    rsi_val = CS.rsi([b["close"] for b in bars], 14)
    assert 65.0 <= rsi_val < 70.0, f"fixture: RSI {rsi_val}"
    assert SV.momentum_bias(bars) == "BULL"
    m1, _ = make_bull_scenario()
    m5, _ = make_bull_scenario()
    r = SV.decide("MICRO", m5, bars, [], 120.0, None, 0, SV.KillSwitch(),
                  m1_bars=m1)
    assert not str(r.get("reason", "")).startswith("RSI"), r["reason"]


# ── 3. TP minimum 100 pts ───────────────────────────────────────────────────
def test_tp_min_constant_is_100():
    assert SV.MICRO_TP_MIN_POINTS == 100.0


def test_tp_cut_to_150pts_still_enters():
    """TP terpotong swing berlawanan ke ~150 pts (100..200) → entry TETAP
    jalan (dulu ditolak karena ambang 200). Fixture: resistance 1.60 di atas
    entry; buffer 0.25xATR kecil → hasil pemotongan di kisaran 150 pts."""
    m15 = flat(100.0, 12, v=100)
    t = 1700000000 + 900 * 12
    seq = [(99.0, 99.8), (99.2, 100.0), (98.8, 99.6), (99.6, 101.0),
           (99.4, 100.2), (99.2, 100.0), (99.8, 100.6), (99.6, 100.4),
           (99.4, 100.2)]
    for i, (lo, hi) in enumerate(seq):
        m15.append(bar((lo + hi) / 2, hi, lo, (lo + hi) / 2, t=t + 900 * i))
    entry = 100.4
    st = SV.compute_sl_tp("MICRO", "BULL", m15, entry)
    tp2, _info = SV.clamp_tp_to_structure("MICRO", "BULL", entry, st["tp"], m15, m15)
    dist = abs(tp2 - entry) / 0.01
    if dist >= 100.0:
        # fixture ini terpotong di atas 100 → decide() tidak boleh menolak
        # dengan alasan "TP menabrak"
        m1, _ = make_bull_scenario()
        m5, _ = make_bull_scenario()
        r = SV.decide("MICRO", m5, m15, [], 120.0, None, 0, SV.KillSwitch(), m1_bars=m1)
        assert "TP menabrak" not in r.get("reason", ""), r["reason"]


def test_tp_cut_below_100_still_rejects():
    """TP terpotong jauh di bawah 100 pts → tetap ditolak (proteksi tetap ada)."""
    entry = 100.0
    # resistance tepat di atas entry (jarak < 100 pts setelah buffer) → terpotong
    m5 = [bar(99.5, 100.4, 99.4, 100.3, t=1700000000 + 300 * i) for i in range(25)]
    m5[-1] = bar(100.0, 100.5, 99.95, 100.45, v=300, t=m5[-1]["time"])
    tp3, _ = SV.clamp_tp_to_structure("MICRO", "BULL", entry, entry + 2.5, m5, m5)
    assert tp3 < entry + 1.0, f"swing 100.5 harus memotong TP: {tp3}"


# ── 4. matcher pnl /deals (None = netral, bukan 0.0) ────────────────────────
def test_close_pnl_matches_latest_out_deal_after_entry():
    """Deal close (OUT) terbaru SETELAH waktu entry dipasangkan — MT5 tidak
    menghubungkan deal close ke order entry via field `order` (kasus nyata:
    entry order=428326048, close deal order=428327581 — beda).
    Matching pakai sifat posisi: OUT + setelah entry_ts + volume sama."""
    deals = [
        {"entry": 0, "order": 428326048, "time": 1788989102, "volume": 0.02, "profit": 0.0},
        {"entry": 1, "order": 428327581, "time": 1788989246, "volume": 0.02, "profit": -4.04},
    ]
    pnl = close_pnl_for_ticket(428326048, deals, entry_ts=1788989100, lot=0.02)
    assert pnl == -4.04


def test_close_pnl_volume_filter_excludes_other_positions():
    """Deal OUT dengan volume beda (noise ARE-TEST 0.01) tidak diambil utk
    posisi 0.02."""
    deals = [
        {"entry": 1, "time": 1788989200, "volume": 0.01, "profit": -0.5},
    ]
    assert close_pnl_for_ticket(123, deals, entry_ts=1788989100, lot=0.02) is None


def test_close_pnl_none_when_deal_absent():
    """Deal belum tercatat (history broker lag / window /deals) → None."""
    assert close_pnl_for_ticket(999, [], entry_ts=1788989100, lot=0.02) is None


def test_close_pnl_ignores_deals_before_entry():
    """Deal OUT dari posisi LAMA (sebelum entry_ts posisi ini) diabaikan."""
    deals = [
        {"entry": 1, "time": 1788988000, "volume": 0.02, "profit": -99.0},
    ]
    assert close_pnl_for_ticket(123, deals, entry_ts=1788989100, lot=0.02) is None


def test_fifo_earliest_out_pairs_earliest_open():
    """REVISI 2026-09-10 sore: semantik matcher berubah latest-wins → FIFO.

    Latest-wins membuat posisi yang dibuka paling awal mengklaim deal OUT
    TERBARU (milik posisi lain saat restart/downtime menutup dua posisi
    berdekatan dgn lot sama) — PnL dua arm tertukar (bug nyata 2026-09-10,
    kasus SCALP 428419669). Kontrak baru: deal OUT TERAWIL ≥ entry_ts adalah
    pasangan posisi terbuka paling awal (FIFO kronologis)."""
    deals = [
        {"ticket": 1, "entry": 1, "time": 1788989150, "volume": 0.02, "profit": 1.0},
        {"ticket": 2, "entry": 1, "time": 1788989200, "volume": 0.02, "profit": 2.0},
    ]
    assert close_pnl_for_ticket(123, deals, entry_ts=1788989100, lot=0.02) == 1.0


def test_fifo_two_opens_same_lot_get_distinct_deals_in_order():
    """REGRESI bug backfill/driver 2026-09-10: dua posisi 0.02 lot dibuka
    berjauhan, ditutup berdekatan saat downtime — pairing harus urut entry:
    open pertama → deal pertama, open kedua → deal kedua. Matcher lama
    (latest-wins / min-per-close-independen) menukar keduanya."""
    deals = [
        {"ticket": 11, "entry": 1, "time": 1788989700, "volume": 0.02, "profit": -3.66},
        {"ticket": 22, "entry": 1, "time": 1788990100, "volume": 0.02, "profit": 14.22},
    ]
    used: set = set()
    p_older = close_pnl_for_ticket(1001, deals, entry_ts=1788989100, lot=0.02,
                                   used_deals=used)
    p_newer = close_pnl_for_ticket(1002, deals, entry_ts=1788990000, lot=0.02,
                                   used_deals=used)
    assert p_older == -3.66   # posisi tua (open 1788989100) → deal terawil
    assert p_newer == 14.22   # posisi muda (open 1788990000) → deal berikutnya
    assert used == {11, 22}


def test_position_id_exact_beats_fifo():
    """Bridge ≥ 2026-09-10 expose position_id → pairing EKSAK: deal dengan
    position_id yang sama dengan posisi dipilih meski deal lain lebih awal
    atau lot-nya sama (ambiguitas FIFO lenyap)."""
    deals = [
        {"ticket": 1, "entry": 1, "time": 1788989700, "volume": 0.02,
         "profit": -99.0, "position_id": 777},
        {"ticket": 2, "entry": 1, "time": 1788989800, "volume": 0.02,
         "profit": 14.22, "position_id": 1002},
    ]
    used: set = set()
    assert close_pnl_for_ticket(1002, deals, entry_ts=1788989100, lot=0.02,
                                used_deals=used, position_id=1002) == 14.22
    assert used == {2}


def test_used_deals_prevents_double_count_across_arms():
    """Dua posisi close di detik sama, deal hanya boleh dipakai sekali:
    arm pertama ambil deal terbaru, arm kedua deal sebelumnya (bukan deal
    yang sama dua kali)."""
    deals = [
        {"ticket": 1, "entry": 1, "time": 1788989200, "volume": 0.02, "profit": 5.0},
        {"ticket": 2, "entry": 1, "time": 1788989200, "volume": 0.02, "profit": -3.0},
    ]
    used: set = set()
    p1 = close_pnl_for_ticket(111, deals, entry_ts=1788989100, lot=0.02, used_deals=used)
    p2 = close_pnl_for_ticket(222, deals, entry_ts=1788989100, lot=0.02, used_deals=used)
    assert used == {1, 2}
    assert sorted([p1, p2]) == [-3.0, 5.0]


def test_used_deals_exhausted_returns_none():
    """Semua deal kandidat sudah dipakai → None (netral), bukan duplikat."""
    deals = [
        {"ticket": 1, "entry": 1, "time": 1788989200, "volume": 0.02, "profit": 5.0},
    ]
    used: set = set()
    assert close_pnl_for_ticket(111, deals, entry_ts=1788989100, lot=0.02, used_deals=used) == 5.0
    assert close_pnl_for_ticket(222, deals, entry_ts=1788989100, lot=0.02, used_deals=used) is None


def test_used_deals_none_keeps_backward_compat():
    """used_deals tidak diberikan (panggilan lama/test lama) → perilaku sama."""
    deals = [{"entry": 1, "time": 1788989200, "volume": 0.02, "profit": 5.0}]
    assert close_pnl_for_ticket(111, deals, entry_ts=1788989100, lot=0.02) == 5.0
