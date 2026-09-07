# -*- coding: utf-8 -*-
"""Regression test: clamp broker-minimum SL/TP di are/bot.py.

Akar penolakan 'Invalid stops' (retcode 10016, 2026-09-04): manual SL 2/TP 2
dikirim hampir apa adanya padahal spread XAUUSD live ~17 poin. Perbaikan awal
(clamp spread+5 = 22-23 poin) TERBUKTI MASIH KURANG — broker tetap menolak
(23 ditolak, 29.49 diterima). Clamp sekarang sadar stops_level broker:

    min_stop = max(MIN_SL_PER_STYLE[style],
                   round(spread_poin) + stops_level_poin + 5)   # bila dilaporkan
    bila stops_level tidak dilaporkan:
    min_stop = max(..., BROKER_MIN_STOP_FALLBACK=30)   # fallback empiris

    Catatan penting (2026-09-07): MT5 mengukur jarak SL/TP dari harga pasar
    (Bid utk BUY), BUKAN dari entry (Ask). Karena entry BUY = Ask, jarak
    minimum dari entry = spread + stops_level + margin. Formula lama
    max(spread+5, stops+5) menghasilkan 23 poin yang hanya 6 poin di bawah
    Bid -> DITOLAK broker; spread+stops = 27.91 poin (11 poin di bawah Bid)
    -> diterima. Jadi komponen spread dan stops_level DIJUMLAHKAN.

Blok clamp INLINE (bukan fungsi) tidak bisa diimpor. Test ini mengeksekusi
TEKS blok nyata yang dibaca dari source are/bot.py (di-dedent) dalam
namespace tiruan, jadi regression test mengikuti kode yang benar-benar
dikirim ke runtime. Bila clamp direfactor menjadi fungsi, test ini gagal
dengan pesan jelas dan tinggal diarahkan ke fungsi tsb.
"""
import math
import textwrap
from pathlib import Path

import pytest

import are.bot as bot_mod

BOT_PATH = Path(__file__).resolve().parent.parent / "are" / "bot.py"


def _load_clamp_block():
    """Potong blok clamp nyata dari are/bot.py lalu dedent (aslinya inline)."""
    lines = BOT_PATH.read_text(encoding="utf-8").splitlines()
    start = next(
        i for i, l in enumerate(lines)
        if "style_min_sl = MIN_SL_PER_STYLE.get(style, 5)" in l
    )
    end = next(
        i for i, l in enumerate(lines[start:], start)
        if l.strip().startswith('log("ENTRY"')
    )
    block = textwrap.dedent("\n".join(lines[start:end]))
    assert "CLAMP" in block, "blok clamp tidak ditemukan di are/bot.py"
    return block


def _run_clamp(style, sl_points, tp_points, tick=None, direction="BUY"):
    """Jalankan blok clamp nyata bot.py dgn input sintetis; kembalikan (sl, tp, logs)."""
    logs = []

    def _log(tag, msg):
        logs.append((tag, msg))

    ns = {
        "MIN_SL_PER_STYLE": bot_mod.MIN_SL_PER_STYLE,
        "BROKER_MIN_STOP_FALLBACK": bot_mod.BROKER_MIN_STOP_FALLBACK,
        "math": math,
        "log": _log,
        "style": style,
        "symbol": "XAUUSD",
        "dec": {"slPoints": sl_points, "tpPoints": tp_points, "decision": direction},
        "account": {"ticks": {"XAUUSD": tick}} if tick else {},
    }
    exec(compile(_load_clamp_block(), str(BOT_PATH), "exec"), ns)
    return ns["sl_pts"], ns["tp_pts"], logs


# Spread XAUUSD live nyata: bid 4383.68 / ask 4383.85 -> 17 poin
SPREAD17 = {"bid": 4383.68, "ask": 4383.85}


def test_bug_case_manual_2_2_clamped_fallback_floor_30():
    """Akar bug: micro manual SL 2/TP 2 + spread XAUUSD live, tanpa stops_level.
    Catatan float: (4383.85-4383.68)/0.01 = 17.000000000000004 -> ceil 18 ->
    18+5=23 — TAPI 23 terbukti DITOLAK broker (2026-09-04), jadi fallback
    BROKER_MIN_STOP_FALLBACK=30 yang menang: 30/30."""
    sl, tp, logs = _run_clamp("micro", 2, 2, tick=SPREAD17)
    assert (sl, tp) == (30, 30)  # max(3, round(17)+5=22, 30) = 30
    assert "CLAMP" in [t for t, _ in logs]


def test_stops_level_reported_overrides_fallback():
    """stops_level broker dilaporkan (mis. 40 poin): min = spread 17 + 40 + 5 = 62."""
    sl, tp, logs = _run_clamp("micro", 2, 2, tick={**SPREAD17, "stops_level": 40})
    assert (sl, tp) == (62, 62)
    clamps = [m for t, m in logs if t == "CLAMP"]
    assert clamps and "spread 17 + stops_level 40 poin + 5" in clamps[0]


def test_stops_level_25_with_spread_17():
    """stops_level 25: min = 17 + 25 + 5 = 47 (komponen dijumlahkan)."""
    sl, tp, _ = _run_clamp("micro", 2, 2, tick={**SPREAD17, "stops_level": 25})
    assert (sl, tp) == (47, 47)


def test_already_above_minimum_unchanged():
    """Nilai >= minimum broker tidak boleh diubah (150/150 tetap 150/150)."""
    sl, tp, logs = _run_clamp("micro", 150, 150,
                              tick={**SPREAD17, "stops_level": 40})
    assert (sl, tp) == (150, 150)  # 150 >= 62
    assert "CLAMP" not in [t for t, _ in logs]


def test_style_floor_wins_when_stops_small():
    """min = max(min_style, spread+stops+5): scalp floor 8 == 2+1+5 = 8 -> 8."""
    sl, tp, logs = _run_clamp("scalp", 2, 2,
                              tick={"bid": 1.0, "ask": 1.02, "stops_level": 1})
    assert (sl, tp) == (8, 8)  # floor 8 == spread 2 + stops 1 + 5 = 8
    assert "CLAMP" not in [t for t, _ in logs]  # floor cukup — tidak perlu clamp


@pytest.mark.parametrize("direction", ["BUY", "SELL"])
def test_direction_symmetric(direction):
    """Clamp berbasis poin identik utk BUY dan SELL (arah SL/TP di bridge)."""
    sl, tp, _ = _run_clamp("micro", 2, 2, tick=SPREAD17, direction=direction)
    assert (sl, tp) == (30, 30)  # tanpa stops_level -> fallback 30


def test_fractional_spread_uses_round_and_floor():
    """Spread 17.4 poin -> round 17 -> +5=22, kalah oleh fallback 30 -> 30."""
    sl, tp, _ = _run_clamp("micro", 2, 2, tick={"bid": 100.0, "ask": 100.174})
    assert (sl, tp) == (30, 30)


def test_spread_25_exact_formula():
    """Spread presisi bersih 0.25: round(25)+5=30 == fallback 30 -> 30."""
    sl, tp, _ = _run_clamp("micro", 2, 2, tick={"bid": 100.0, "ask": 100.25})
    assert (sl, tp) == (30, 30)


def test_no_ticks_no_clamp_no_crash():
    """Tanpa ticks live: tanpa CLAMP (tidak tahu spread/stops), floor min_style tetap."""
    sl, tp, logs = _run_clamp("micro", 2, 2, tick=None)
    assert (sl, tp) == (3, 3)
    assert "CLAMP" not in [t for t, _ in logs]
    assert "CLAMP_ERR" not in [t for t, _ in logs]


def test_clamp_log_message_records_mapping_and_basis():
    """Log CLAMP mencatat mapping SL/TP asli -> baru + dasar perhitungan."""
    _, _, logs = _run_clamp("micro", 2, 2, tick={**SPREAD17, "stops_level": 40})
    clamps = [m for t, m in logs if t == "CLAMP"]
    assert clamps, "tidak ada log CLAMP padahal clamp terjadi"
    assert "SL/TP 3/3 -> 62/62" in clamps[0]
    assert "spread 17 + stops_level 40 poin + 5" in clamps[0]
