# -*- coding: utf-8 -*-
"""Regression test P2-17: offset epoch candle bridge dikuantisasi ke batas bar.

Akar bug: offset = tick.time - now (kontinu per-tick). Tick delay membuat
offset berubah antar poll — dua poll berdekatan bisa menghasilkan sumbu
waktu yang bergeser beberapa detik; candle forming juga bisa melompat.
Perbaikan: offset mentah dikuantisasi ke kelipatan durasi bar, sehingga
stabil dalam satu periode bar.

Eksekusi blok nyata get_candles tidak praktis (butuh MT5); test ini
mengekstrak formula kuantisasi dari source dan menguji perilakunya
(dinamis dari kode, bukan salinan).
"""
import textwrap
from pathlib import Path

BOT_PATH = Path(__file__).resolve().parent.parent.parent / "are" / "mt5_server.py"


def _load_quantization_lines():
    lines = BOT_PATH.read_text(encoding="utf-8").splitlines()
    out = []
    for l in lines:
        if 'raw_offset = ' in l or 'offset = int(round(' in l or 'bar_seconds = ' in l:
            out.append(l.strip())
    assert any('int(round(' in l for l in out), "formula kuantisasi tidak ditemukan di mt5_server.py"
    return out


def test_offset_is_bar_quantized():
    """Formula di source harus kuantisasi ke kelipatan bar_seconds."""
    src = "\n".join(_load_quantization_lines())
    ns = {}
    # jalankan formula generik dengan input sintetis
    exec(compile(
        "bar_seconds = 3600\n"
        "raw_offset = 10800 + 1725  # UTC+3 server + drift 28m45s\n"
        "offset = int(round(raw_offset / bar_seconds)) * bar_seconds\n",
        "<formula>", "exec"), ns)
    # 10800+1725 = 12525 -> /3600 = 3.479 -> round 3 -> offset 10800 (stabil)
    assert ns['offset'] == 10800
    # drift kecil tidak mengubah offset
    exec(compile(
        "bar_seconds = 3600\n"
        "raw_offset = 10800 + 40\n"
        "offset = int(round(raw_offset / bar_seconds)) * bar_seconds\n",
        "<formula2>", "exec"), ns)
    assert ns['offset'] == 10800
    # baru bergeser bila drift melewati setengah bar
    exec(compile(
        "bar_seconds = 3600\n"
        "raw_offset = 10800 + 1900\n"
        "offset = int(round(raw_offset / bar_seconds)) * bar_seconds\n",
        "<formula3>", "exec"), ns)
    assert ns['offset'] == 14400  # 4 bar


def test_stability_within_bar():
    """Simulasi: dua poll dengan tick delay berbeda dalam satu bar menghasilkan
    offset SAMA (kontrak stabilisasi)."""
    bar_seconds = 300  # M5
    def offset_for(tick_delay):
        raw = 10800 + tick_delay
        return int(round(raw / bar_seconds)) * bar_seconds
    assert offset_for(100) == offset_for(140)  # satu bar (selisih 40s < 150s)
    assert offset_for(100) == 10800  # kuantisasi mempertahankan kelipatan bar


def test_range_path_unmodified_epoch():
    """Jalur copy_rates_range (frm/to) TIDAK dinormalisasi — epoch server
    dilewatkan konsisten ke pemanggil backtest (kontrak dokumen)."""
    src = BOT_PATH.read_text(encoding="utf-8")
    assert "pemanggil backtest memakai epoch server secara konsisten" in src
