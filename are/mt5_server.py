"""
AHFMES ARE — Persistent MT5 Server
Runs as background process, maintains MT5 connection, serves data via HTTP.

Usage:
    python -m are.mt5_server --port 18888

Endpoints:
    GET /account   — account info + ticks + positions
    GET /positions — positions only (fast)
    GET /ticks     — ticks only (fast)
    POST /order    — send order
"""
from __future__ import annotations
import json
import sys
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

MT5_CONNECTED = False
MT5_ACCOUNT = None

def connect_mt5():
    global MT5_CONNECTED, MT5_ACCOUNT
    if mt5 is None:
        return False, "MetaTrader5 not installed"
    if MT5_CONNECTED:
        return True, "already connected"
    if not mt5.initialize():
        return False, str(mt5.last_error())
    acc = mt5.account_info()
    if acc is None:
        mt5.shutdown()
        return False, "no account info"
    MT5_CONNECTED = True
    MT5_ACCOUNT = acc
    return True, f"connected: {acc.login} @ {acc.server}"

def disconnect_mt5():
    global MT5_CONNECTED, MT5_ACCOUNT
    if MT5_CONNECTED and mt5:
        mt5.shutdown()
    MT5_CONNECTED = False
    MT5_ACCOUNT = None

def get_account_data():
    if not MT5_CONNECTED or not mt5:
        return {'connected': False}
    try:
        acc = mt5.account_info()
        if acc is None:
            return {'connected': False, 'error': 'account_info returned None'}
        
        ticks = {}
        for sym in ['XAUUSD','EURUSD','GBPUSD','USDJPY','BTCUSD']:
            try:
                t = mt5.symbol_info_tick(sym)
                if t:
                    decimals = 3 if 'JPY' in sym else (2 if sym == 'XAUUSD' else 5)
                    ticks[sym] = {
                        'bid': round(t.bid, decimals),
                        'ask': round(t.ask, decimals),
                        'spread': round((t.ask - t.bid) * (100 if 'JPY' in sym else 10000), 1)
                    }
            except Exception:
                pass
        
        positions = []
        for p in (mt5.positions_get() or []):
            positions.append({
                'ticket': p.ticket, 'symbol': p.symbol,
                'type': 'BUY' if p.type == 0 else 'SELL',
                'volume': p.volume, 'price_open': p.price_open,
                'price_current': p.price_current,
                'profit': round(p.profit, 2), 'swap': round(p.swap, 2),
                'sl': p.sl, 'tp': p.tp, 'comment': p.comment, 'time': p.time,
                'pnl_pct': round(((p.price_current - p.price_open) / p.price_open * 100) * (1 if p.type == 0 else -1), 2),
            })
        
        return {
            'connected': True,
            'login': acc.login, 'server': acc.server, 'name': acc.name,
            'balance': round(acc.balance, 2), 'equity': round(acc.equity, 2),
            'margin': round(acc.margin, 2), 'free_margin': round(acc.margin_free, 2),
            'margin_level': round(acc.margin_level, 2) if acc.margin_level else 0,
            'leverage': acc.leverage, 'currency': acc.currency,
            'profit': round(acc.profit, 2),
            'ticks': ticks, 'positions': positions, 'position_count': len(positions),
        }
    except Exception as e:
        return {'connected': False, 'error': str(e)}

def send_order(symbol, direction, lot, sl=0, tp=0, comment="ARE"):
    if not MT5_CONNECTED or not mt5:
        return {'success': False, 'error': 'MT5 not connected'}
    try:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {'success': False, 'error': f'no tick for {symbol}'}
        price = tick.ask if direction == 'BUY' else tick.bid
        req = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol, 'volume': lot,
            'type': mt5.ORDER_TYPE_BUY if direction == 'BUY' else mt5.ORDER_TYPE_SELL,
            'price': price, 'sl': sl, 'tp': tp,
            'comment': comment,
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(req)
        if result is None:
            return {'success': False, 'error': 'order_send returned None'}
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {'success': False, 'error': result.comment, 'retcode': result.retcode}
        return {'success': True, 'ticket': result.ticket, 'price': result.price}
    except Exception as e:
        return {'success': False, 'error': str(e)}


class MT5Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress logs

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        
        if path == '/account':
            data = get_account_data()
        elif path == '/positions':
            d = get_account_data()
            data = {
                'connected': d.get('connected', False),
                'positions': d.get('positions', []),
                'position_count': d.get('position_count', 0),
                'profit': d.get('profit', 0),
            }
        elif path == '/ticks':
            d = get_account_data()
            data = {
                'connected': d.get('connected', False),
                'ticks': d.get('ticks', {}),
            }
        elif path == '/health':
            data = {'status': 'ok', 'mt5_connected': MT5_CONNECTED}
        else:
            data = {'error': 'unknown endpoint'}
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}
        
        if path == '/order':
            data = send_order(
                body.get('symbol', 'XAUUSD'),
                body.get('direction', 'BUY'),
                body.get('lot', 0.01),
                body.get('sl', 0),
                body.get('tp', 0),
                body.get('comment', 'ARE'),
            )
        elif path == '/connect':
            ok, msg = connect_mt5()
            data = {'success': ok, 'message': msg}
        elif path == '/disconnect':
            disconnect_mt5()
            data = {'success': True, 'message': 'disconnected'}
        else:
            data = {'error': 'unknown endpoint'}
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def main():
    port = 18888
    if '--port' in sys.argv:
        idx = sys.argv.index('--port')
        port = int(sys.argv[idx + 1])
    
    ok, msg = connect_mt5()
    print(f"MT5 Server starting on port {port}")
    print(f"MT5: {msg}")
    
    server = HTTPServer(('127.0.0.1', port), MT5Handler)
    print(f"Listening on http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        disconnect_mt5()
        server.shutdown()
        print("MT5 Server stopped")


if __name__ == '__main__':
    main()
