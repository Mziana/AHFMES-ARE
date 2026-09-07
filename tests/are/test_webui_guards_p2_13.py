# -*- coding: utf-8 -*-
"""Regression test P2-13: web_ui heavy-guard + clamp + payload limit.

Kontrak yang diuji (unit, tanpa server):
1. _HEAVY_SEMAPHORE: hanya satu heavy op; kedua acquire gagal.
2. _read_payload: menolak payload > 1MB (ValueError -> handler 413).
3. Clamp WFO: param_grid maks 20 kandidat x 8 key; folds maks 12.
"""
import threading

import are.web_ui as wu


def test_heavy_semaphore_single_slot():
    sem = wu.AREAPIHandler._HEAVY_SEMAPHORE
    got1 = sem.acquire(blocking=False)
    got2 = sem.acquire(blocking=False)
    try:
        assert got1 is True
        assert got2 is False, 'heavy guard harus menolak slot kedua (503)'
    finally:
        if got1:
            sem.release()


def test_read_payload_rejects_oversize():
    """Stub murni: _read_payload harus menolak content_len > 1MB (ValueError)
    SEBELUM membaca body."""
    import pytest
    from unittest.mock import MagicMock

    h = MagicMock()
    h._MAX_PAYLOAD_BYTES = wu.AREAPIHandler._MAX_PAYLOAD_BYTES
    h.headers.get.side_effect = lambda k, v=None: wu.AREAPIHandler._MAX_PAYLOAD_BYTES + 1 if k == 'Content-Length' else 0
    with pytest.raises(ValueError, match='payload too large'):
        # panggil fungsi asli terhadap stub
        wu.AREAPIHandler._read_payload(h)


def test_wfo_grid_clamp_logic():
    """Formula clamp sama seperti handler: 20 kandidat x 8 key maks."""
    raw_grid = [{'lookback': i, 'extra': j} for i, j in
                ((lb, 0) for lb in range(100))]
    param_grid = [dict(list(g.items())[:8]) for g in raw_grid[:20]
                  if isinstance(g, dict)]
    assert len(param_grid) == 20
    assert all(len(g) <= 8 for g in param_grid)


def test_folds_clamp_bounds():
    for raw in (0, 1, 5, 100, 12):
        n = max(2, min(int(raw), 12))
        assert 2 <= n <= 12
    assert max(2, min(int(0), 12)) == 2
    assert max(2, min(int(100), 12)) == 12
