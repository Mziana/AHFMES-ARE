# -*- coding: utf-8 -*-
"""Regression test P2-16: decision engine punya provenance versi + hash config.

Kontrak (diverifikasi terhadap server UI yang hidup; skip bila tidak jalan):
- /api/are/decision selalu menyertakan engineVersion & strategyConfigHash.
- Hash STABIL antar poll (konfigurasi sama -> hash sama) dan BERBEDA antar
  style (config berbeda -> hash berbeda).
"""
import urllib.request
import urllib.error

import pytest

UI = 'http://127.0.0.1:4028'


def _get(url, timeout=40):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:
        return None


import json  # noqa: E402


@pytest.fixture(scope='module')
def ui_up():
    if _get(f'{UI}/api/are/system', timeout=8) is None:
        pytest.skip('UI dev server not running')
    return True


def test_decision_has_provenance(ui_up):
    d = _get(f'{UI}/api/are/decision?symbol=XAUUSD&style=micro&risk=1')
    assert d and d.get('success'), 'decision engine harus merespons'
    assert d.get('engineVersion'), 'engineVersion wajib ada (P2-16)'
    assert d.get('strategyConfigHash'), 'strategyConfigHash wajib ada (P2-16)'


def test_hash_stable_across_polls(ui_up):
    h1 = _get(f'{UI}/api/are/decision?symbol=XAUUSD&style=micro&risk=1').get('strategyConfigHash')
    h2 = _get(f'{UI}/api/are/decision?symbol=XAUUSD&style=micro&risk=1').get('strategyConfigHash')
    assert h1 == h2, 'hash config sama harus stabil antar poll'


def test_hash_differs_between_styles(ui_up):
    h_micro = _get(f'{UI}/api/are/decision?symbol=XAUUSD&style=micro&risk=1').get('strategyConfigHash')
    h_day = _get(f'{UI}/api/are/decision?symbol=XAUUSD&style=day&risk=1').get('strategyConfigHash')
    assert h_micro and h_day and h_micro != h_day, 'style berbeda -> hash berbeda'
