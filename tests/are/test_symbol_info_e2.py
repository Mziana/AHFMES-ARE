"""E-2 regression tests — /account exposes symbol_info (broker spec).

Runtime contract:
  1. GET /account menyertakan `symbol_info` per simbol (contract_size, point,
     tick_value, tick_size, digits, stops_level, spread_points, volume_*)
     — konsumen: strategy_v2/broker_meta.load_broker_meta (sumber
     BRIDGE_SYMBOL_INFO, menggantikan FALLBACK konstanta).
  2. Fail-closed: spec TIDAK valid (contract_size/point <= 0) atau symbol_info
     MT5 None → entry TIDAK di-emit (konsumen jatuh ke FALLBACK, bukan
     point_value = 0 yang mematikan PnL).
  3. Full chain: payload bridge → load_broker_meta → pv = contract_size ×
     point (dihitung, bukan hardcode) — guard $17/lot E-2.

Server nyata dipakai (ThreadingHTTPServer, port ephemeral); MetaTrader5
di-mock di level modul (srv.mt5) — pola sama dengan test_bridge_auth_p0_01.
"""
import json
import os
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import are.mt5_server as srv  # noqa: E402
from strategy_v2.broker_meta import load_broker_meta, point_value_usd_per_lot  # noqa: E402


class _FakeSI:
    """mt5.symbol_info namedtuple-like (field yang dipakai bridge saja)."""

    def __init__(self, name, contract_size=100.0, point=0.01, tick_value=1.0,
                 tick_size=0.01, digits=2, stops_level=10, spread=1700):
        self.name = name
        self.trade_contract_size = contract_size
        self.point = point
        self.trade_tick_value = tick_value
        self.trade_tick_size = tick_size
        self.digits = digits
        self.trade_stops_level = stops_level
        self.spread = spread
        self.volume_min = 0.01
        self.volume_max = 100.0
        self.volume_step = 0.01
        self.currency_profit = "USD"


class _FakeTick:
    def __init__(self, bid, ask):
        self.bid = bid
        self.ask = ask
        self.time = 1788739200


class _FakeAcc:
    login = 123456
    server = "Fake-Demo"
    name = "Tester"
    balance = 1136.65
    equity = 1136.65
    margin = 0.0
    margin_free = 1136.65
    margin_level = 0.0
    leverage = 500
    currency = "USD"
    profit = 0.0


class _FakeMT5:
    """Fake module MetaTrader5: XAUUSD spec valid, JPY valid, BTCUSD rusak."""

    SPECS = {
        "XAUUSD": dict(contract_size=100.0, point=0.01, tick_value=1.0,
                       tick_size=0.01, digits=2, stops_level=10, spread=1700),
        "USDJPY": dict(contract_size=100000.0, point=0.001, tick_value=0.65,
                       tick_size=0.001, digits=3, stops_level=15, spread=180),
        "BTCUSD": dict(contract_size=0.0, point=0.0),   # spec rusak → fail-closed
    }

    @staticmethod
    def account_info():
        return _FakeAcc()

    @staticmethod
    def positions_get(*_a, **_k):
        return []

    @classmethod
    def symbol_info(cls, sym):
        kw = cls.SPECS.get(sym)
        return None if kw is None else _FakeSI(sym, **kw)

    @classmethod
    def symbol_info_tick(cls, sym):
        if sym not in cls.SPECS:
            return None
        return _FakeTick(4401.38, 4401.55) if sym == "XAUUSD" else _FakeTick(100.0, 100.2)


@pytest.fixture()
def bridge_server(tmp_path, monkeypatch):
    token_file = tmp_path / "bridge_token.txt"
    monkeypatch.setattr(srv, "BRIDGE_TOKEN", "")
    monkeypatch.setattr(srv, "BRIDGE_TOKEN_FILE", str(token_file))
    monkeypatch.setattr(srv, "ALLOWED_ORIGINS",
                        {"http://127.0.0.1:4028", "http://localhost:4028"})
    token = srv.load_or_create_token()
    monkeypatch.setattr(srv, "MT5_CONNECTED", True)
    monkeypatch.setattr(srv, "mt5", _FakeMT5)

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.MT5Handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield {"port": port, "token": token}
    httpd.shutdown()
    httpd.server_close()


def _get_account(ctx):
    req = urllib.request.Request(
        f"http://127.0.0.1:{ctx['port']}/account",
        headers={"X-Bridge-Token": ctx["token"]})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def test_account_payload_contains_symbol_info(bridge_server):
    d = _get_account(bridge_server)
    assert d["connected"] is True
    assert "symbol_info" in d, "/account harus menyertakan symbol_info (E-2)"
    x = d["symbol_info"]["XAUUSD"]
    assert x["contract_size"] == pytest.approx(100.0)
    assert x["point"] == pytest.approx(0.01)
    assert x["tick_value"] == pytest.approx(1.0)
    assert x["digits"] == 2
    assert x["stops_level"] == 10
    assert x["spread_points"] == 1700
    assert x["source"] == "MT5_SYMBOL_INFO"
    # tick lama tetap utuh (tidak ada regresi konsumen lama)
    assert d["ticks"]["XAUUSD"]["spread"] == pytest.approx(1700.0)
    assert d["ticks"]["XAUUSD"]["stops_level"] == 10


def test_invalid_spec_not_emitted_fail_closed(bridge_server):
    """Spec rusak (contract_size=0/point=0) → TIDAK di-emit; simbol tanpa spec
    → juga tidak. Konsumen jatuh ke FALLBACK, bukan pv=0."""
    d = _get_account(bridge_server)
    assert "BTCUSD" not in d["symbol_info"], "spec nol tidak boleh lolos guard"


def test_full_chain_bridge_payload_to_broker_meta(bridge_server):
    """Payload bridge nyata (mocked MT5) → load_broker_meta → sumber
    BRIDGE_SYMBOL_INFO, pv dihitung dari contract_size × point."""
    d = _get_account(bridge_server)
    meta = load_broker_meta(d)
    assert meta["source"] == "BRIDGE_SYMBOL_INFO"
    assert meta["contract_size"] == pytest.approx(100.0)
    assert meta["point"] == pytest.approx(0.01)
    assert point_value_usd_per_lot(meta) == pytest.approx(1.0)  # $1/lot/poin


def test_full_chain_missing_symbol_info_falls_back(bridge_server):
    d = _get_account(bridge_server)
    broken = {k: v for k, v in d.items() if k != "symbol_info"}
    meta = load_broker_meta(broken)
    assert meta["source"] == "FALLBACK"
    assert point_value_usd_per_lot(meta) == pytest.approx(1.0)


def test_full_chain_tick_value_used_when_broker_reports_it(bridge_server):
    """tick_value riil broker (>0) dipakai apa adanya — bukan hasil hitung."""
    d = _get_account(bridge_server)
    meta = load_broker_meta(d)
    assert meta["tick_value"] == pytest.approx(1.0)  # dari _FakeSI XAUUSD
