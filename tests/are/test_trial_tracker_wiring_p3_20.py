# -*- coding: utf-8 -*-
"""Regression test P3-20: CumulativeTrialTracker ter-wire ke CLI `backtest wfo`.

Akar bug (2026-09-07, bukti empiris): CumulativeTrialTracker ada di
are/backtest_enhanced.py:294 tetapi TIDAK dipanggil dari mana pun — trial di
data/cumulative_trials.json tetap 100 sebelum/sesudah `backtest wfo` (grid
per-run = 8, tapi total lintas sesi tidak pernah bertambah).

Perbaikan: CLI `backtest wfo` menginstantiate tracker di awal branch dan
mencatat SATU sesi di titik sukses (setelah run_walk_forward_optimization,
sebelum print ringkasan) dengan schema yang sama: total_trials, sessions[],
symbol_trials. Ini lapisan pelaporan lintas-sesi — effective_trial_count
per-run (== parameter_family_size) dan perhitungan DSR tidak diubah.
"""
import json
from pathlib import Path

import are.cli

TRACKER_FILE = Path("data/cumulative_trials.json")
WFO_ARGS = ["backtest", "wfo", "--symbol", "XAUUSD", "--folds", "2"]
# Grid otomatis CLI: range(10, 50, 5) = 8 kombinasi == parameter_family_size
AUTO_GRID_SIZE = len(range(10, 50, 5))


def _load_tracker():
    if not TRACKER_FILE.exists():
        return {"total_trials": 0, "sessions": [], "symbol_trials": {}}
    with open(TRACKER_FILE) as f:
        return json.load(f)


def test_cli_wfo_updates_tracker():
    """`are.cli.main(['backtest','wfo',...])` harus menambah total_trials
    >= effective_trial_count run tsb dan mencatat session baru utk XAUUSD."""
    before = _load_tracker()
    before_total = before.get("total_trials", 0)

    rc = are.cli.main(WFO_ARGS)
    assert rc == 0, "CLI backtest wfo harus rc=0"

    after = _load_tracker()
    assert after.get("total_trials", 0) > before_total, \
        "tracker harus bertambah setelah run WFO"
    assert after["sessions"][-1]["symbol"] == "XAUUSD", \
        "session terakhir harus untuk XAUUSD"
    assert after["sessions"][-1]["trials"] >= 1


def test_tracker_counts_match_grid():
    """trials session terakhir == parameter_family_size dari WFO run tsb
    (effective_trial_count == |grid| auto = 8 kombinasi)."""
    are.cli.main(WFO_ARGS)
    data = _load_tracker()
    sessions = data.get("sessions") or []
    assert sessions, "tracker harus punya session tercatat"
    last = sessions[-1]
    assert last["trials"] == AUTO_GRID_SIZE, \
        f"trials={last['trials']} harus == parameter_family_size {AUTO_GRID_SIZE}"


def test_tracker_backward_compat():
    """Schema lama (total_trials, sessions, symbol_trials) tetap utuh."""
    data = _load_tracker()
    assert {"total_trials", "sessions", "symbol_trials"} <= set(data.keys()), \
        "schema keys lama harus tetap ada"
    for s in data.get("sessions") or []:
        assert {"symbol", "trials", "best_sharpe", "timestamp"} <= set(s.keys()), \
            "tiap session harus punya symbol/trials/best_sharpe/timestamp"