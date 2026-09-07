# -*- coding: utf-8 -*-
"""Regression test C1: provenance exit price posisi bot.

Akar bug (audit 2026-09-07, bot_state_micro.json): semua trade_history bot
tercatat "exit": 0. Penyebab: record posisi buatan bot (new_rec) tidak pernah
memiliki field last_price — hanya posisi ADOPT yang diisi pos_to_record().
Saat posisi hilang dari broker (TP/SL), reconcile_positions memakai
rec["last_price"] sebagai exit -> 0 untuk posisi buatan sendiri.

Perbaikan: reconcile me-refresh rec["last_price"] = price_current tiap siklus
untuk SEMUA posisi terlacak, dan new_rec mengisi last_price = harga entry.
"""
import are.bot as bot_mod


def _run_reconcile(state, broker_positions, monkeypatch):
    monkeypatch.setattr(bot_mod, "log", lambda *a, **k: None)
    open_recs, closed = bot_mod.reconcile_positions(state, broker_positions, "micro", "XAUUSD")
    return open_recs, closed


def _broker_pos(ticket=111, price_current=4402.5, profit=-5.0):
    return {"ticket": ticket, "symbol": "XAUUSD", "type": "SELL", "volume": 0.02,
            "price_open": 4400.0, "price_current": price_current, "profit": profit,
            "sl": 0, "tp": 0, "magic": 2001, "comment": "ARE-MICRO", "time": 100}


def test_bot_made_position_gets_last_price_refreshed(monkeypatch):
    """Record gaya-lama (tanpa last_price) harus mendapat harga live broker."""
    state = {"positions": [{"ticket": 111, "direction": "SELL", "entry": 4400.0,
                            "lot": 0.02, "sl": 150, "tp": 150, "opened_at": 1.0,
                            "last_pnl": -1.0}]}  # TANPA last_price (posisi buatan bot)
    open_recs, _ = _run_reconcile(state, [_broker_pos()], monkeypatch)
    assert open_recs[0]["last_price"] == 4402.5


def test_vanished_position_records_nonzero_exit(monkeypatch):
    """THE regression: posisi hilang (TP/SL) -> exit = harga last known, bukan 0."""
    state = {"positions": [{"ticket": 111, "direction": "SELL", "entry": 4400.0,
                            "lot": 0.02, "opened_at": 1.0, "last_pnl": -2.0,
                            "last_price": 4401.0}]}
    open_recs, closed = _run_reconcile(state, [], monkeypatch)
    assert open_recs == []
    assert closed[0]["ticket"] == 111
    assert closed[0]["exit"] == 4401.0, "exit price harus last known price"
    assert closed[0]["pnl"] == -2.0


def test_adopted_positions_still_tracked(monkeypatch):
    """Perilaku adopt tidak berubah (regression guard)."""
    state = {"positions": []}
    open_recs, closed = _run_reconcile(state, [_broker_pos(ticket=222)], monkeypatch)
    assert len(open_recs) == 1
    assert open_recs[0]["ticket"] == 222
    assert open_recs[0]["last_price"] == 4402.5
    assert closed == []
