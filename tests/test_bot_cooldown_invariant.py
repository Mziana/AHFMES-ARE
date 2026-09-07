# -*- coding: utf-8 -*-
"""Regression test: invariant fix COOLDOWN hantu di are/bot.py.

Kasus lama (bug): saat SEMUA kriteria entri lolos lalu order DITOLAK broker
(OrderRejected/BridgeError), state["last_trade_at"] ikut di-set seolah trade
sukses -> UI menampilkan 'COOLDOWN' padahal tidak ada posisi.

Invariant yang dijamin kode saat ini:
  1) OrderRejected  -> state["last_reject_at"] ter-set + rejection kategori
     'order' tercatat; state["last_trade_at"] TIDAK berubah (tetap None).
  2) BridgeError    -> sama seperti OrderRejected.
  3) Open sukses    -> state["last_trade_at"] ter-set (cooldown antar-trade
     sah), posisi masuk, tanpa rejection 'order'.

Region try/except INLINE di loop run_bot (bukan fungsi) tidak bisa diimpor.
Seperti test_bot_sltp_clamp.py, test ini mengeksekusi TEKS region nyata yang
dibaca dari source are/bot.py
(di-dedent) dalam namespace tiruan. record_entry_rejection dipakai dari
modul NYATA (are.bot); hanya open_position + learning yang di-stub supaya
tidak menyentuh broker/bridge maupun data/learning live.
"""
import textwrap
import time as time_mod
from pathlib import Path

import are.bot as bot_mod

BOT_PATH = Path(__file__).resolve().parent.parent / "are" / "bot.py"


def _load_entry_region():
    """Region nyata: log ENTRY .. (sebelum) save_state pertama — isi try/except order."""
    lines = BOT_PATH.read_text(encoding="utf-8").splitlines()
    start = next(
        i for i, l in enumerate(lines)
        if l.strip().startswith('log("ENTRY"')
    )
    end = next(
        i for i, l in enumerate(lines[start + 1:], start + 1)
        if l.strip().startswith("save_state(state, style)")
    )
    block = textwrap.dedent("\n".join(lines[start:end]))
    assert "last_reject_at" in block, "region tidak memuat last_reject_at"
    assert "last_trade_at" in block, "region tidak memuat last_trade_at"
    assert "OrderRejected" in block and "BridgeError" in block
    return block


def _fresh_state():
    return {
        "status": "running",
        "positions": [],
        "active_ticket": None,
        "active_direction": None,
        "trade_count": 0,
        "last_trade_at": None,
        "last_reject_at": None,
        "rejections": {"total": 0, "by_reason": {}, "last": None},
    }


def _run_entry(open_result_or_exc, state=None, sl_pts=22, tp_pts=22):
    """Eksekusi region ENTRY..reject nyata; kembalikan (state, captured, logs)."""
    logs = []
    captured = {}

    def _log(tag, msg):
        logs.append((tag, msg))

    def _open_position(symbol, direction, lot, sl_points, tp_points, magic, comment):
        captured.update(symbol=symbol, direction=direction, lot=lot,
                        sl=sl_points, tp=tp_points, magic=magic, comment=comment)
        if isinstance(open_result_or_exc, Exception):
            raise open_result_or_exc
        return open_result_or_exc

    def _fp(style, dec):  # stub learning — jangan sentuh data/learning
        return {"style": style, "signal": dec["decision"]}

    def _rec_open(*args, **kwargs):  # stub learning
        return None

    state = state if state is not None else _fresh_state()
    dec = {"decision": "BUY", "lotSize": 0.02, "entry": 4383.5, "rr": 1.5,
           "finalSignal": "BUY"}
    ns = {
        "log": _log,
        "time": time_mod,
        "symbol": "XAUUSD",
        "dec": dec,
        "magic": 2001,
        "sl_pts": sl_pts,
        "tp_pts": tp_pts,
        "open_position": _open_position,
        "OrderRejected": bot_mod.OrderRejected,
        "BridgeError": bot_mod.BridgeError,
        "learning_fp_from_dec": _fp,
        "learning_record_open": _rec_open,
        "record_entry_rejection": bot_mod.record_entry_rejection,
        "style": "micro",
        "state": state,
        # konstanta backoff dipakai region reject (streak/ORDER_HALT)
        "ORDER_REJECT_RETRY_S": bot_mod.ORDER_REJECT_RETRY_S,
        "ORDER_REJECT_STREAK_HALT": bot_mod.ORDER_REJECT_STREAK_HALT,
        "ORDER_REJECT_HALT_S": bot_mod.ORDER_REJECT_HALT_S,
    }
    exec(compile(_load_entry_region(), str(BOT_PATH), "exec"), ns)
    return ns["state"], captured, logs


def test_order_rejected_records_reject_and_keeps_last_trade_at_none():
    """INVARIANT 1: OrderRejected -> last_reject_at + kategori 'order', TANPA last_trade_at."""
    state, captured, logs = _run_entry(bot_mod.OrderRejected("Invalid stops"))
    assert state["last_reject_at"] is not None and state["last_reject_at"] > 0
    assert state["last_trade_at"] is None, "COOLDOWN hantu: last_trade_at berubah saat ditolak!"
    assert state["rejections"]["by_reason"].get("order") == 1
    assert state["rejections"]["total"] == 1
    assert state["order_reject_streak"] == 1  # deret penolakan bertambah
    assert state["positions"] == [] and state["active_ticket"] is None
    assert any(t == "OPEN_FAILED" for t, _ in logs)
    assert captured["sl"] == 22 and captured["tp"] == 22  # order benar2 dikirim dgn clamp


def test_bridge_error_records_reject_and_keeps_last_trade_at_none():
    """INVARIANT 2: BridgeError -> last_reject_at + kategori 'order', TANPA last_trade_at."""
    state, _, logs = _run_entry(bot_mod.BridgeError("connection refused"))
    assert state["last_reject_at"] is not None and state["last_reject_at"] > 0
    assert state["last_trade_at"] is None, "COOLDOWN hantu: last_trade_at berubah saat bridge mati!"
    assert state["rejections"]["by_reason"].get("order") == 1
    assert state["order_reject_streak"] == 1  # deret penolakan bertambah
    assert state["positions"] == [] and state["active_ticket"] is None
    assert any(t == "OPEN_FAILED" for t, _ in logs)


def test_success_sets_last_trade_at_and_adds_position():
    """INVARIANT 3: open sukses -> last_trade_at ter-set + posisi masuk, tanpa rejection."""
    state, captured, logs = _run_entry({"ticket": 555, "price": 4385.0})
    assert state["last_trade_at"] is not None and state["last_trade_at"] > 0
    assert state["last_reject_at"] is None
    assert state["rejections"]["total"] == 0
    assert state["order_reject_streak"] == 0  # sukses me-reset deret
    assert state["active_ticket"] == 555
    assert len(state["positions"]) == 1
    assert state["positions"][0]["ticket"] == 555
    assert state["positions"][0]["sl"] == 22 and state["positions"][0]["tp"] == 22
    assert any(t == "OPENED" for t, _ in logs)
    assert captured["direction"] == "BUY" and captured["lot"] == 0.02


def test_reject_then_success_same_state_sequence():
    """Urutan reject lalu sukses: hanya sukses yang men-set last_trade_at (cooldown sah)."""
    state = _fresh_state()
    # 1) order ditolak
    state, _, _ = _run_entry(bot_mod.OrderRejected("Invalid stops"), state=state)
    assert state["last_trade_at"] is None
    assert state["rejections"]["by_reason"].get("order") == 1
    # 2) percobaan berikutnya sukses (state sama, rejections tidak di-reset)
    state, _, _ = _run_entry({"ticket": 777, "price": 4385.0}, state=state)
    assert state["last_trade_at"] is not None, "trade sukses harus memicu cooldown normal"
    assert state["active_ticket"] == 777
    assert len(state["positions"]) == 1
    assert state["rejections"]["by_reason"].get("order") == 1  # riwayat tetap tercatat


def test_rejections_reset_only_on_new_state():
    """State segar (bot start) tidak membawa last_trade_at/rejections sisa sesi lama."""
    st = _fresh_state()
    assert st["last_trade_at"] is None and st["last_reject_at"] is None
    assert st["rejections"]["total"] == 0 and st["rejections"]["by_reason"] == {}
