# -*- coding: utf-8 -*-
"""Regression test P0-03: circuit breaker berbasis EQUITY di are/bot.py.

Akar bug (2026-09-07 audit): breaker lama menghitung loss dari BALANCE
(realized saja). Dengan leverage 1:500 pada XAUUSD, posisi mengambang -5%
tidak pernah men-trigger stop — sistem "terlihat aman" padahal equity sudah
jatuh melewati batas harian. Perbaikan: loss dihitung dari EQUITY broker
(balance + floating PnL), fallback last_known_equity yang dipersist saat
bridge gagal — BUKAN starting_balance (itu = deteksi loss dimatikan).

Blok breaker INLINE di loop run_bot tidak bisa diimpor. Test ini mengeksekusi
TEKS blok nyata dari are/bot.py (di-dedent, dibungkus while True: agar `break`
valid), jadi regression mengikuti kode yang benar-benar berjalan.
"""
import textwrap
from pathlib import Path

import pytest

import are.bot as bot_mod

BOT_PATH = Path(__file__).resolve().parent.parent / "are" / "bot.py"


def _load_breaker_block():
    """Potong blok breaker nyata dari are/bot.py lalu dedent."""
    lines = BOT_PATH.read_text(encoding="utf-8").splitlines()
    start = next(
        i for i, l in enumerate(lines)
        if "# Daily loss circuit breaker" in l
    )
    end = next(
        i for i, l in enumerate(lines[start:], start)
        if l.strip() == "break"
    )
    block = textwrap.dedent("\n".join(lines[start:end + 1]))
    assert "current_equity" in block, "blok breaker equity tidak ditemukan di are/bot.py"
    return block


def _run_breaker(state, account=None, bridge_down=False, max_daily_loss=5.0):
    """Jalankan blok breaker nyata; kembalikan state (dimutasi in-place)."""
    logs = []
    saved = []

    def _log(tag, msg=""):
        logs.append((tag, msg))

    def _save(s, style):
        saved.append(dict(s))

    def _get_account():
        if bridge_down:
            raise bot_mod.BridgeError("simulated bridge down")
        return account or {}

    ns = {
        "get_account": _get_account,
        "BridgeError": bot_mod.BridgeError,
        "state": state,
        "style": "micro",  # blok memakai variabel run_bot scope: save_state(state, style)
        "log": _log,
        "save_state": _save,
        "max_daily_loss": max_daily_loss,
    }
    body = textwrap.indent(_load_breaker_block(), "    ")
    src = "while True:\n" + body + "\n    break\n"
    exec(compile(src, str(BOT_PATH), "exec"), ns)
    return {"state": state, "logs": logs, "saved": saved}


def _base_state(**over):
    s = {
        "starting_balance": 1000.0,
        "last_known_equity": 0.0,
        "status": "running",
    }
    s.update(over)
    return s


def test_floating_loss_triggers_breaker():
    """THE regression: balance tak berubah tapi equity jatuh -6% (floating)
    HARUS men-trigger breaker. Kode lama membiarkannya lewat."""
    st = _base_state()
    res = _run_breaker(st, account={"balance": 1000.0, "equity": 940.0},
                       max_daily_loss=5.0)
    assert res["state"]["status"] == "circuit_breaker"
    assert any(t == "CIRCUIT_BREAKER" for t, _ in res["logs"])


def test_realized_loss_still_triggers():
    st = _base_state()
    res = _run_breaker(st, account={"balance": 940.0, "equity": 940.0},
                       max_daily_loss=5.0)
    assert res["state"]["status"] == "circuit_breaker"


def test_healthy_equity_no_trigger():
    st = _base_state()
    res = _run_breaker(st, account={"balance": 1000.0, "equity": 990.0},
                       max_daily_loss=5.0)
    assert res["state"]["status"] == "running"
    assert res["state"]["last_known_equity"] == 990.0  # dipersist utk fallback


def test_bridge_down_uses_persisted_equity():
    """Bridge mati: breaker memakai last_known_equity terakhir (bukan
    starting_balance yang berarti deteksi loss dimatikan)."""
    st = _base_state(last_known_equity=940.0)
    res = _run_breaker(st, bridge_down=True, max_daily_loss=5.0)
    assert res["state"]["status"] == "circuit_breaker"


def test_missing_equity_field_degrades_to_balance():
    """Bridge tidak melaporkan equity (field hilang/0): fallback balance —
    degraded tapi tetap berfungsi utk loss realized."""
    st = _base_state()
    res = _run_breaker(st, account={"balance": 940.0}, max_daily_loss=5.0)
    assert res["state"]["status"] == "circuit_breaker"


def test_breaker_state_saved_before_exit():
    """Status circuit_breaker harus di-save sebelum loop keluar (audit trail)."""
    st = _base_state()
    res = _run_breaker(st, account={"balance": 1000.0, "equity": 900.0},
                       max_daily_loss=5.0)
    assert res["saved"], "save_state harus dipanggil sebelum break"
    assert res["saved"][-1]["status"] == "circuit_breaker"
