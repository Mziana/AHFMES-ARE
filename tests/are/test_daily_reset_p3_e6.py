# -*- coding: utf-8 -*-
"""Regression test E-6: reset harian circuit breaker (kalender UTC) di are/bot.py.

Akar (bukti runtime 2026-09-07): max_daily_loss dihitung dari starting_balance
sesi berjalan; tidak ada reset otomatis pergantian hari — bot yang menyeberang
tengah malam membawa baseline sesi lama. Perbaikan: state menyimpan
session_date (UTC YYYY-MM-DD) + daily_start_balance; di awal tiap iterasi loop,
bila tanggal berganti, baseline di-reset ke balance broker HARI INI dan
daily_pnl/trade_count dipindahkan ke daily_pnl_prev (audit). last_trade_at /
last_reject_at TIDAK direset (backoff tetap berlaku lintas hari).

Blok reset INLINE di loop run_bot tidak bisa diimpor; test mengeksekusi TEKS
blok nyata dari are/bot.py (pola ekstraksi-blok — sama seperti
test_bot_equity_breaker.py / test_bot_killswitch_authority.py).
"""
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import are.bot as bot_mod

BOT_PATH = Path(__file__).resolve().parent.parent.parent / "are" / "bot.py"


def _load_reset_block():
    """Potong blok reset harian nyata dari are/bot.py lalu dedent."""
    lines = BOT_PATH.read_text(encoding="utf-8").splitlines()
    start = next(
        i for i, l in enumerate(lines)
        if "# Daily reset (E-6)" in l
    )
    end = next(
        i for i, l in enumerate(lines[start:], start)
        if "new_style = current_state.get(\"pending_style\")" in l
    )
    block = textwrap.dedent("\n".join(lines[start:end]))
    assert "session_date" in block, "blok reset harian tidak ditemukan di are/bot.py"
    return block


def _run_reset(state, account=None, bridge_down=False):
    logs = []

    def _log(tag, msg=""):
        logs.append((tag, msg))

    def _get_account():
        if bridge_down:
            raise bot_mod.BridgeError("simulated bridge down")
        return account or {}

    ns = {
        "state": state,
        "get_account": _get_account,
        "BridgeError": bot_mod.BridgeError,
        "log": _log,
        "datetime": datetime,
        "timezone": timezone,
    }
    exec(compile(_load_reset_block(), str(BOT_PATH), "exec"), ns)
    return {"state": state, "logs": logs}


def _today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _base_state(**over):
    s = {
        "session_date": _today(),
        "daily_start_balance": 1000.0,
        "daily_pnl": 5.0,
        "trade_count": 3,
        "last_trade_at": 123.0,
        "last_reject_at": 456.0,
    }
    s.update(over)
    return s


def test_same_day_no_reset():
    """session_date = hari ini -> baseline & daily_pnl tidak berubah."""
    st = _base_state()
    res = _run_reset(st, account={"balance": 990.0})
    assert res["state"]["session_date"] == _today()
    assert res["state"]["daily_start_balance"] == 1000.0, "baseline TIDAK boleh berubah"
    assert res["state"]["daily_pnl"] == 5.0, "daily_pnl tidak direset di hari yang sama"
    assert res["state"]["trade_count"] == 3
    assert not any(t == "DAILY_RESET" for t, _ in res["logs"])


def test_day_rollover_resets_baseline():
    """session_date kemarin -> baseline = balance HARI INI, daily_pnl ->
    daily_pnl_prev, trade_count = 0. last_trade_at/last_reject_at tetap."""
    st = _base_state(session_date="2000-01-01", daily_pnl=12.0, trade_count=7)
    res = _run_reset(st, account={"balance": 990.0})
    assert res["state"]["session_date"] == _today()
    assert res["state"]["daily_start_balance"] == 990.0, "baseline = balance hari ini"
    assert res["state"]["daily_pnl"] == 0.0
    assert res["state"]["daily_pnl_prev"] == 12.0, "nilai lama pindah ke daily_pnl_prev"
    assert res["state"]["trade_count"] == 0
    assert res["state"]["last_trade_at"] == 123.0, "last_trade_at tidak direset"
    assert res["state"]["last_reject_at"] == 456.0, "last_reject_at tidak direset"
    assert any(t == "DAILY_RESET" for t, _ in res["logs"])


def test_backward_compat_old_state():
    """State lama tanpa session_date/daily_start_balance tidak crash; reset
    berjalan, dan basis breaker fallback ke starting_balance bila field kosong."""
    st = {"starting_balance": 500.0, "daily_pnl": 2.0, "trade_count": 1}
    res = _run_reset(st, account={"balance": 480.0})
    assert res["state"]["session_date"] == _today()
    assert res["state"]["daily_start_balance"] == 480.0
    assert res["state"]["daily_pnl_prev"] == 2.0
    # Basis breaker: daily_start_balance bila terisi, else starting_balance.
    basis = res["state"].get("daily_start_balance") or res["state"]["starting_balance"]
    assert basis == 480.0


def test_bridge_down_skips_reset():
    """Bridge mati saat rollover: baseline lama dipertahankan, tanggal tidak
    maju (coba lagi iterasi berikutnya) — bukan reset ke 0."""
    st = _base_state(session_date="2000-01-01", daily_pnl=3.0, trade_count=2)
    res = _run_reset(st, bridge_down=True)
    assert res["state"]["daily_start_balance"] == 1000.0, "baseline lama dipertahankan"
    assert res["state"]["session_date"] == "2000-01-01", "tanggal tidak maju"
    assert res["state"]["daily_pnl"] == 3.0
    assert any(t == "RESET_SKIP" for t, _ in res["logs"])