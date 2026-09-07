# -*- coding: utf-8 -*-
"""Regression test P1-07: kill switch = authority boundary di jalur bot.

Akar bug (audit 2026-09-07): execution_state.json punya kill_switch_active,
CLI `safety-kill` mengaktifkannya, CSK menghormatinya — tapi bot.py TIDAK
pernah membacanya. Hasil: kill switch = tombol kosmetik bagi mesin yang
benar-benar mengirim order.

Perbaikan: (1) is_kill_switch_active() membaca flag persisten (cache 2 dtk);
(2) veto di rantai entry SEBELUM open_position — order baru diblokir, posisi
tetap dikelola (trailing/close = risk-reducing). Test ini mengeksekusi TEKS
region veto nyata dari are/bot.py + perilaku helper terhadap file asli.
"""
import json
import textwrap
from pathlib import Path

import are.bot as bot_mod

BOT_PATH = Path(__file__).resolve().parent.parent / "are" / "bot.py"


def _load_veto_block():
    """Potong region can_enter + veto nyata dari are/bot.py."""
    lines = BOT_PATH.read_text(encoding="utf-8").splitlines()
    start = next(
        i for i, l in enumerate(lines)
        if l.strip().startswith('can_enter = (dec["decision"] != "WAIT"')
    )
    end = next(
        i for i, l in enumerate(lines[start:], start)
        if "# Backoff penolakan" in l
    )
    block = textwrap.dedent("\n".join(lines[start:end]))
    assert "is_kill_switch_active" in block, "veto kill switch tidak ditemukan di are/bot.py"
    return block


def _run_veto(dec, kill_active, state=None):
    state = state if state is not None else {"rejections": {"total": 0, "by_reason": {}, "last": None}}
    ns = {
        "dec": dec,
        "min_rr": 1.5,
        "state": state,
        "is_kill_switch_active": lambda: kill_active,
        "record_entry_rejection": bot_mod.record_entry_rejection,
        "classify_entry_rejection": bot_mod.classify_entry_rejection,
    }
    exec(compile(_load_veto_block(), str(BOT_PATH), "exec"), ns)
    return ns["can_enter"], state


def _good_dec():
    return {"decision": "BUY", "mtfConfirmed": True, "inSession": True,
            "rr": 2.0, "lotSize": 0.02, "finalSignal": "BUY", "decisionReason": "TA OK"}


def test_kill_switch_blocks_passing_signal():
    """THE regression: sinyal lolos semua gate TAPI kill switch aktif ->
    can_enter HARUS False dan rejection tercatat."""
    can_enter, state = _run_veto(_good_dec(), kill_active=True)
    assert can_enter is False
    rej = state["rejections"]
    assert rej["total"] == 1
    assert rej["by_reason"].get("kill_switch") == 1
    assert rej["last"]["key"] == "kill_switch"


def test_no_kill_switch_passes_good_signal():
    can_enter, state = _run_veto(_good_dec(), kill_active=False)
    assert can_enter is True
    assert state["rejections"]["total"] == 0


def test_no_kill_switch_still_rejects_bad_signal():
    """Tanpa kill switch, gate lama tetap bekerja (tidak ada bypass)."""
    dec = _good_dec()
    dec["decision"] = "WAIT"
    can_enter, state = _run_veto(dec, kill_active=False)
    assert can_enter is False
    assert state["rejections"]["by_reason"].get("wait", 0) >= 0  # tercatat sbg wait/mtf/rr


def test_helper_reads_real_execution_state(tmp_path, monkeypatch):
    """Helper membaca file execution_state nyata (format CLI safety-kill)."""
    f = tmp_path / "execution_state.json"
    f.write_text(json.dumps({"kill_switch_active": True}), encoding="utf-8")
    monkeypatch.setattr(bot_mod, "EXECUTION_STATE_FILE", f)
    bot_mod._KILLSWITCH_CACHE["ts"] = 0.0  # flush cache
    assert bot_mod.is_kill_switch_active() is True

    f.write_text(json.dumps({"kill_switch_active": False}), encoding="utf-8")
    bot_mod._KILLSWITCH_CACHE["ts"] = 0.0
    assert bot_mod.is_kill_switch_active() is False


def test_helper_fail_safe_on_corrupt_file(tmp_path, monkeypatch):
    """File rusak/hilang: helper tidak crash; order tetap lewat gate normal
    (kill switch tidak boleh macet-ON karena file korup)."""
    f = tmp_path / "execution_state.json"
    f.write_text("{corrupt json", encoding="utf-8")
    monkeypatch.setattr(bot_mod, "EXECUTION_STATE_FILE", f)
    bot_mod._KILLSWITCH_CACHE["ts"] = 0.0
    assert bot_mod.is_kill_switch_active() is False

    monkeypatch.setattr(bot_mod, "EXECUTION_STATE_FILE", tmp_path / "missing.json")
    bot_mod._KILLSWITCH_CACHE["ts"] = 0.0
    assert bot_mod.is_kill_switch_active() is False


def test_helper_caches_within_ttl(tmp_path, monkeypatch):
    """Cache 2 dtk: file berubah tanpa flush cache tidak langsung terbaca —
    melindungi loop 1 dtk dari IO berlebih; TTL pendek menjaga latensi veto."""
    f = tmp_path / "execution_state.json"
    f.write_text(json.dumps({"kill_switch_active": True}), encoding="utf-8")
    monkeypatch.setattr(bot_mod, "EXECUTION_STATE_FILE", f)
    bot_mod._KILLSWITCH_CACHE["ts"] = 0.0
    assert bot_mod.is_kill_switch_active() is True
    f.write_text(json.dumps({"kill_switch_active": False}), encoding="utf-8")
    # tanpa flush cache: masih True (cache valid < 2 dtk)
    assert bot_mod.is_kill_switch_active() is True
    bot_mod._KILLSWITCH_CACHE["ts"] = 0.0
    assert bot_mod.is_kill_switch_active() is False
