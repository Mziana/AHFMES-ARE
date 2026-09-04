"""
AHFMES ARE — Persistent MT5 Server
Runs as background process, maintains MT5 connection, serves data via HTTP.

Usage:
    python -m are.mt5_server --port 18888

Endpoints:
    GET  /account    — account info + ticks + positions
    GET  /positions  — positions only (fast)
    GET  /ticks      — ticks only (fast)
    GET  /candles    — OHLCV candle data
    GET  /health     — health check
    POST /order      — send order (direction/type, lot/volume)
    POST /close      — close position by ticket
    POST /close_all  — close all positions
    POST /connect    — connect MT5
    POST /disconnect — disconnect MT5
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

TIMEFRAME_MAP = {
    'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30,
    'H1': 16385, 'H4': 16388, 'D1': 16408, 'W1': 32769, 'MN1': 49153,
}

# Durasi 1 bar per timeframe (menit) untuk jendela copy_rates_range.
TF_MINUTES = {
    'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30,
    'H1': 60, 'H4': 240, 'D1': 1440, 'W1': 10080, 'MN1': 43200,
}

def get_candles(symbol: str, timeframe_str: str = 'H1', count: int = 200,
                frm: int = 0, to: int = 0):
    """
    Candle data. Tanpa frm/to: count bar terakhir (termasuk bar forming),
    sama seperti sebelumnya. Dengan frm/to (epoch detik): rentang historis
    via copy_rates_range — untuk backtest. Read-only.
    """
    if not MT5_CONNECTED or not mt5:
        return {'connected': False, 'error': 'not connected'}
    try:
        tf = TIMEFRAME_MAP.get(timeframe_str.upper(), 16385)
        from datetime import datetime, timedelta
        import time as _time
        offset = 0  # selisih jam server (epoch bar) vs UTC real — dinormalisasi
        if frm and to:
            rates = mt5.copy_rates_range(symbol, tf,
                                         datetime.fromtimestamp(frm),
                                         datetime.fromtimestamp(to))
        else:
            # Jalur DEFAULT: copy_rates_from_pos. Pada terminal ini (Finex demo)
            # copy_rates_range TERBUKTI beku (history berhenti walau tick hidup),
            # sedangkan copy_rates_from_pos selalu segar. Epoch bar dari jalur ini
            # memakai jam server (UTC+3) — dinormalisasi ke UTC real agar
            # freshness engine (Date.now) dan sumbu waktu chart tetap benar.
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
            tick = mt5.symbol_info_tick(symbol)
            if tick is not None:
                offset = int(tick.time - _time.time())
        if rates is None or len(rates) == 0:
            return {'connected': True, 'symbol': symbol, 'candles': [], 'error': 'no data'}
        candles = []
        for r in rates:
            candles.append({
                'time': int(r['time']) - offset,
                'open': round(r['open'], 5),
                'high': round(r['high'], 5),
                'low': round(r['low'], 5),
                'close': round(r['close'], 5),
                'volume': int(r['tick_volume']),
            })
        return {'connected': True, 'symbol': symbol, 'timeframe': timeframe_str, 'candles': candles}
    except Exception as e:
        return {'connected': True, 'error': str(e), 'candles': []}

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
            except Exception as e:
                import logging
                logging.warning(f"MT5 tick error for {sym}: {e}")
        
        positions = []
        for p in (mt5.positions_get() or []):
            positions.append({
                'ticket': p.ticket, 'symbol': p.symbol,
                'type': 'BUY' if p.type == 0 else 'SELL',
                'volume': p.volume, 'price_open': p.price_open,
                'price_current': p.price_current,
                'profit': round(p.profit, 2), 'swap': round(p.swap, 2),
                'sl': p.sl, 'tp': p.tp, 'comment': p.comment, 'time': p.time,
                'magic': p.magic,
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

def send_order(symbol, direction, lot, sl=0, tp=0, sl_points=0, tp_points=0, comment="ARE", magic=0):
    if not MT5_CONNECTED or not mt5:
        return {'success': False, 'error': 'MT5 not connected'}
    try:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {'success': False, 'error': f'no tick for {symbol}'}
        price = tick.ask if direction == 'BUY' else tick.bid

        # Konversi offset POIN ke harga: 1 poin = point symbol (XAUUSD 0.01)
        si = mt5.symbol_info(symbol)
        point = si.point if si else 0.01
        digits = si.digits if si else 2

        # Calculate SL/TP from live price using points offsets
        if sl_points and sl_points > 0:
            sl = (price - sl_points * point) if direction == 'BUY' else (price + sl_points * point)
        if tp_points and tp_points > 0:
            tp = (price + tp_points * point) if direction == 'BUY' else (price - tp_points * point)

        # Round ke digits symbol
        sl = round(sl, digits) if sl and sl > 0 else 0
        tp = round(tp, digits) if tp and tp > 0 else 0

        req = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol, 'volume': lot,
            'type': mt5.ORDER_TYPE_BUY if direction == 'BUY' else mt5.ORDER_TYPE_SELL,
            'price': price,
            'comment': comment,
            'magic': magic,
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
        }
        # Only include SL/TP if > 0 — MT5 rejects sl=0 as invalid
        if sl > 0:
            req['sl'] = sl
        if tp > 0:
            req['tp'] = tp
        result = mt5.order_send(req)
        if result is None:
            return {'success': False, 'error': f'order_send returned None — last_error: {mt5.last_error()}'}
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {'success': False, 'error': result.comment, 'retcode': result.retcode}
        return {'success': True, 'ticket': result.order, 'deal': result.deal, 'price': result.price}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def close_position(ticket):
    if not MT5_CONNECTED or not mt5:
        return {'success': False, 'error': 'MT5 not connected'}
    try:
        positions = mt5.positions_get(ticket=ticket)
        if not positions or len(positions) == 0:
            return {'success': False, 'error': f'position {ticket} not found'}
        pos = positions[0]
        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(pos.symbol)
        if tick is None:
            return {'success': False, 'error': f'no tick for {pos.symbol}'}
        price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
        req = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': pos.symbol, 'volume': pos.volume,
            'type': close_type,
            'position': ticket,
            'price': price,
            'comment': 'ARE-CLOSE',
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(req)
        if result is None:
            return {'success': False, 'error': 'close_order returned None'}
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {'success': False, 'error': result.comment, 'retcode': result.retcode}
        return {'success': True, 'ticket': result.order, 'deal': result.deal, 'message': f'position {ticket} closed'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def close_all_positions(symbol=None):
    if not MT5_CONNECTED or not mt5:
        return {'success': False, 'error': 'MT5 not connected'}
    try:
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        if not positions:
            return {'success': True, 'message': 'no positions to close', 'closed': 0}
        closed = 0
        errors = []
        for pos in positions:
            r = close_position(pos.ticket)
            if r.get('success'):
                closed += 1
            else:
                errors.append(f'{pos.ticket}: {r.get("error", "unknown")}')
        return {'success': closed > 0, 'closed': closed, 'errors': errors}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def modify_position(ticket, sl=None, tp=None):
    """Modify SL/TP on an existing open position."""
    if not MT5_CONNECTED or not mt5:
        return {'success': False, 'error': 'MT5 not connected'}
    try:
        positions = mt5.positions_get(ticket=ticket)
        if not positions or len(positions) == 0:
            return {'success': False, 'error': f'position {ticket} not found'}
        pos = positions[0]
        req = {
            'action': mt5.TRADE_ACTION_SLTP,
            'symbol': pos.symbol,
            'position': ticket,
            'sl': sl if sl is not None else pos.sl,
            'tp': tp if tp is not None else pos.tp,
        }
        result = mt5.order_send(req)
        if result is None:
            return {'success': False, 'error': 'modify returned None'}
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {'success': False, 'error': result.comment, 'retcode': result.retcode}
        return {'success': True, 'ticket': ticket, 'sl': req['sl'], 'tp': req['tp']}
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
        elif path == '/candles':
            params = parse_qs(parsed.query)
            symbol = params.get('symbol', ['XAUUSD'])[0]
            timeframe_str = params.get('timeframe', ['H1'])[0]
            count = int(params.get('count', ['200'])[0])
            frm = int(params.get('from', ['0'])[0])
            to = int(params.get('to', ['0'])[0])
            data = get_candles(symbol, timeframe_str, count, frm, to)
        elif path == '/health':
            data = {'status': 'ok', 'mt5_connected': MT5_CONNECTED}
        elif path == '/deals':
            days = int(parse_qs(parsed.query).get('days', ['7'])[0])
            try:
                from datetime import datetime, timedelta
                since = datetime.now() - timedelta(days=days)
                deals = mt5.history_deals_get(since, datetime.now())
                data = {'deals': [
                    {
                        'ticket': d.ticket, 'order': d.order, 'time': d.time,
                        'type': d.type, 'entry': d.entry, 'magic': d.magic,
                        'volume': d.volume, 'price': d.price,
                        'profit': d.profit, 'swap': d.swap, 'commission': d.commission,
                        'symbol': d.symbol, 'comment': d.comment,
                    } for d in (deals or [])
                ]} if deals else {'deals': []}
            except Exception as e:
                data = {'deals': [], 'error': str(e)}
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
                body.get('direction', body.get('type', 'BUY')),
                body.get('lot', body.get('volume', 0.01)),
                body.get('sl', 0),
                body.get('tp', 0),
                body.get('sl_points', 0),
                body.get('tp_points', 0),
                body.get('comment', 'ARE'),
                body.get('magic', 0),
            )
        elif path == '/close':
            ticket = body.get('ticket', 0)
            data = close_position(int(ticket)) if ticket else {'success': False, 'error': 'missing ticket'}
        elif path == '/close_all':
            symbol = body.get('symbol')
            data = close_all_positions(symbol)
        elif path == '/modify':
            ticket = body.get('ticket', 0)
            sl = body.get('sl')
            tp = body.get('tp')
            data = modify_position(int(ticket), sl=sl, tp=tp) if ticket else {'success': False, 'error': 'missing ticket'}
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
