"""A3 attack-surface regression tests (P0-01/P0-02/A3 follow-up).

Checks the LIVE surfaces when they are running (skips otherwise, so CI on a
bare runner stays green):
  1. MT5 bridge rejects token-less requests (401).
  2. UI mutating API route rejects cross-origin POST (403, CSRF middleware).
  3. UI mutating API route accepts server-style POST (no Origin header).
  4. UI rejects bogus Host header (DNS-rebinding defense).
"""
import json
import urllib.error
import urllib.request

import pytest

BRIDGE = 'http://127.0.0.1:18888'
UI = 'http://127.0.0.1:4028'


def _post(url, body, headers=None, timeout=8):
    h = {'Content-Type': 'application/json'}
    h.update(headers or {})
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None


def _get(url, timeout=5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status
    except Exception:
        return None


@pytest.fixture(scope='module')
def ui_up():
    if _get(f'{UI}/api/are/system') != 200:
        pytest.skip('UI dev server not running')
    return True


def test_bridge_requires_token():
    try:
        urllib.request.urlopen(f'{BRIDGE}/health', timeout=5)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return  # contract already satisfied: GET /health w/o token = 401
    except Exception:
        pytest.skip('bridge not running')
    status = _post(f'{BRIDGE}/close', {'ticket': 0})
    assert status == 401, 'bridge must reject token-less POST (P0-01)'


def test_ui_blocks_cross_origin_mutation(ui_up):
    # /api/are/risk POST is a pure computation endpoint — safe to use as probe.
    status = _post(f'{UI}/api/are/risk', {'balance': 10000, 'riskPercent': 1, 'slPoints': 100},
                   headers={'Origin': 'http://evil.example'})
    assert status == 403, 'cross-origin mutation must be denied (A3)'


def test_ui_allows_server_style_mutation(ui_up):
    # /api/are/trade/modify with ticket 0 reaches the route (HTTP 200,
    # success=false "position not found") — proves middleware passed the
    # server-style request through without side effects.
    status = _post(f'{UI}/api/are/trade/modify', {'ticket': 0})
    assert status == 200, 'server-side clients (no Origin) must pass middleware'


def test_ui_blocks_bogus_host(ui_up):
    status = _post(f'{UI}/api/are/risk', {'balance': 10000},
                   headers={'Host': 'rebound.example:4028'})
    assert status == 403, 'DNS-rebinding style Host must be denied'
