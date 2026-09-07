"""P0-01 regression tests — MT5 bridge authentication.

Verifies the runtime contract that closes the unauthenticated order endpoint:
  1. Token file bootstrap: bridge creates data/bridge_token.txt on first run.
  2. Fail-closed: any request without the token => HTTP 401 (all endpoints).
  3. Correct token + no Origin => 200 (server-side clients like are.bot).
  4. Browser-like request: correct token but foreign Origin => 401.
  5. do_OPTIONS never returns Access-Control-Allow-Origin: *.

These tests run the REAL ThreadingHTTPServer from are.mt5_server on an
ephemeral port, with MetaTrader5 absent (auth layer does not need it).
"""
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import are.mt5_server as srv  # noqa: E402


@pytest.fixture()
def bridge_server(tmp_path, monkeypatch):
    """Run the real bridge server with an isolated token file."""
    token_file = tmp_path / "bridge_token.txt"
    monkeypatch.setattr(srv, 'BRIDGE_TOKEN', '')            # reset module state
    monkeypatch.setattr(srv, 'BRIDGE_TOKEN_FILE', str(token_file))
    monkeypatch.setattr(srv, 'ALLOWED_ORIGINS',
                        {'http://127.0.0.1:4028', 'http://localhost:4028'})
    token = srv.load_or_create_token()                       # bootstrap like main()
    assert token, "token bootstrap must produce a non-empty token"
    assert token_file.exists(), "token file must be created on bootstrap"

    httpd = ThreadingHTTPServer(('127.0.0.1', 0), srv.MT5Handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield {'port': port, 'token': token, 'token_file': token_file}
    httpd.shutdown()
    httpd.server_close()


def _get(port, path, headers=None):
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, dict(r.headers), json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), {}


def _post(port, path, body, headers=None):
    h = {'Content-Type': 'application/json'}
    h.update(headers or {})
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}',
                                 data=json.dumps(body).encode(), headers=h)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, dict(r.headers), json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), {}


def test_token_bootstrap_creates_file(bridge_server):
    ctx = bridge_server
    tok = open(ctx['token_file'], encoding='utf-8').read().strip()
    assert tok == ctx['token']


def test_no_token_is_401_on_all_endpoints(bridge_server):
    port = bridge_server['port']
    for path in ('/health', '/account', '/positions', '/ticks', '/candles?symbol=XAUUSD&count=5'):
        status, _, _ = _get(port, path)
        assert status == 401, f'{path} must reject requests without token'
    status, _, _ = _post(port, '/order', {'symbol': 'XAUUSD', 'direction': 'BUY', 'lot': 0.01})
    assert status == 401, '/order without token must be rejected (THE regression)'


def test_wrong_token_is_401(bridge_server):
    port = bridge_server['port']
    status, _, _ = _get(port, '/health', headers={'X-Bridge-Token': 'wrong-token'})
    assert status == 401


def test_valid_token_no_origin_is_200(bridge_server):
    """Server-side clients (are.bot) send no Origin header."""
    port, token = bridge_server['port'], bridge_server['token']
    status, _, body = _get(port, '/health', headers={'X-Bridge-Token': token})
    assert status == 200
    assert body.get('status') == 'ok'
    # POST path passes auth gate. NOTE: use a harmless endpoint — /close with a
    # nonexistent ticket — NEVER /order, because the live bridge may be
    # connected and a successful auth here would place a REAL order.
    status, _, body = _post(port, '/close', {'ticket': 0},
                            headers={'X-Bridge-Token': token})
    assert status == 200
    assert body.get('success') is False  # 'position not found', nothing executed


def test_valid_token_foreign_origin_is_401(bridge_server):
    """Browser-like cross-origin request: even a valid token is not enough."""
    port, token = bridge_server['port'], bridge_server['token']
    status, _, _ = _get(port, '/health',
                        headers={'X-Bridge-Token': token, 'Origin': 'http://evil.example'})
    assert status == 401


def test_options_never_allows_wildcard(bridge_server):
    port, token = bridge_server['port'], bridge_server['token']
    req = urllib.request.Request(f'http://127.0.0.1:{port}/order', method='OPTIONS',
                                 headers={'Origin': 'http://evil.example',
                                          'Access-Control-Request-Method': 'POST',
                                          'X-Bridge-Token': token})
    with urllib.request.urlopen(req, timeout=5) as r:
        acao = r.headers.get('Access-Control-Allow-Origin', '')
    assert acao != '*', 'CORS wildcard must never appear (P0-01)'
    assert acao in srv.ALLOWED_ORIGINS, 'CORS fallback must be an allowlisted UI origin'


def test_empty_token_state_fails_closed(bridge_server, monkeypatch):
    """If token state is somehow empty, every request is denied (no fail-open)."""
    port = bridge_server['port']
    monkeypatch.setattr(srv, 'BRIDGE_TOKEN', '')
    status, _, _ = _get(port, '/health')
    assert status == 401
