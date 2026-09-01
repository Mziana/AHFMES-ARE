
"""Autopilot Brain - Live tick-by-tick trading."""
import time, json, os
from datetime import datetime, timezone
from typing import Optional, List
import MetaTrader5 as mt5

def compute_rsi(closes, period=14):
    if len(closes) < period + 1:
        return [None] * len(closes)
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [max(d, 0) for d in deltas]
    losses = [max(-d, 0) for d in deltas]
    ag = sum(gains[:period]) / period
    al = sum(losses[:period]) / period
    rsi = [None] * period
    rsi.append(100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al))
    for i in range(period, len(deltas)):
        ag = (ag * (period - 1) + gains[i]) / period
        al = (al * (period - 1) + losses[i]) / period
        rsi.append(100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al))
    return rsi

def detect_divergence(prices, rsi_vals, lookback=20):
    if len(prices) < lookback:
        return 0.0
    wp = prices[-lookback:]
    wr = [r for r in rsi_vals[-lookback:] if r is not None]
    if len(wp) < 10 or len(wr) < 10:
        return 0.0
    h = len(wp) // 2
    ppl, cpl = min(wp[:h]), min(wp[h:])
    prl, crl = min(wr[:h]), min(wr[h:])
    if cpl < ppl and crl > prl and abs(cpl - ppl) / ppl * 100 > 1.0:
        return 1.0
    pph, cph = max(wp[:h]), max(wp[h:])
    prh, crh = max(wr[:h]), max(wr[h:])
    if cph > pph and crh < prh and abs(cph - pph) / pph * 100 > 1.0:
        return -1.0
    return 0.0

class AutopilotBrain:
    def __init__(self, symbol="XAUUSD", lot=0.01, sl_points=400, tp_points=600, max_hold_s=10800):
        self.symbol = symbol
        self.lot = lot
        self.sl = sl_points
        self.tp = tp_points
        self.max_hold = max_hold_s
        self.magic = 20260901
        self.m5 = []
        self.h1 = []
        self.last_bar = 0
        self.ticket = None
        self.open_time = 0
        self.log = []
        self.ticks = 0
        self.signals = 0
        self.trades = 0

    def init(self):
        r5 = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M5, 0, 100)
        if r5 is not None:
            self.m5 = [float(r["close"]) for r in r5]
            self.last_bar = int(r5[-1]["time"])
        r1 = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H1, 0, 100)
        if r1 is not None:
            self.h1 = [float(r["close"]) for r in r1]
        pos = mt5.positions_get(symbol=self.symbol)
        if pos:
            self.ticket = pos[0].ticket
            self.open_time = int(pos[0].time)
        print(f"Init: M5={len(self.m5)} H1={len(self.h1)} Pos={'OPEN' if self.ticket else 'FLAT'}")

    def on_tick(self, bid, ask, ts):
        self.ticks += 1
        price = (bid + ask) / 2.0
        bar = ts - ts % 300
        if bar > self.last_bar:
            self.last_bar = bar
            self.m5.append(price)
            if len(self.m5) > 200:
                self.m5 = self.m5[-200:]
            hr = ts - ts % 3600
            if not self.h1 or hr > ts - 3600:
                self.h1.append(price)
                if len(self.h1) > 100:
                    self.h1 = self.h1[-100:]
            return self._eval(price, ts)
        if self.ticket:
            self._manage(price, ts)
        return None

    def _eval(self, price, ts):
        if len(self.m5) < 20 or len(self.h1) < 20 or self.ticket:
            return None
        h1r = compute_rsi(self.h1, 14)
        if not h1r or h1r[-1] is None:
            return None
        trend = 1 if h1r[-1] > 50 else -1
        m5r = compute_rsi(self.m5, 14)
        if not m5r or m5r[-1] is None or m5r[-2] is None:
            return None
        rn, rp = m5r[-1], m5r[-2]
        div = detect_divergence(self.m5, m5r, 20)
        sig = None
        if rp < 30 and rn >= 30 and trend > 0:
            sig = "BUY"
        elif div > 0 and trend > 0:
            sig = "BUY"
        elif rp > 70 and rn <= 70 and trend < 0:
            sig = "SELL"
        elif div < 0 and trend < 0:
            sig = "SELL"
        if sig:
            self.signals += 1
            t = self._open(sig)
            if t:
                self.ticket = t
                self.open_time = ts
                self.trades += 1
                tstr = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M:%S")
                print(f"[{tstr}] {sig} @ {price:.2f} RSI5={rn:.1f} RSI1={h1r[-1]:.1f} Div={div:.0f}")
                self._log(sig, price, ts, rn, rp, h1r[-1], div)
                return sig
        return None

    def _manage(self, price, ts):
        if self.ticket and ts - self.open_time >= self.max_hold:
            self._close(self.ticket)
            self.ticket = None
            tstr = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M:%S")
            print(f"[{tstr}] TIME EXIT")

    def _open(self, d):
        s = mt5.symbol_info(self.symbol)
        t = mt5.symbol_info_tick(self.symbol)
        if not s or not t:
            return None
        pt = s.point
        if d == "BUY":
            p, sl, tp, ot = t.ask, round(t.ask - self.sl * pt, s.digits), round(t.ask + self.tp * pt, s.digits), mt5.ORDER_TYPE_BUY
        else:
            p, sl, tp, ot = t.bid, round(t.bid + self.sl * pt, s.digits), round(t.bid - self.tp * pt, s.digits), mt5.ORDER_TYPE_SELL
        r = mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": self.symbol, "volume": self.lot, "type": ot, "price": p, "sl": sl, "tp": tp, "deviation": 20, "magic": self.magic, "comment": f"AUTO-{d}", "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC})
        return r.order if r and r.retcode == mt5.TRADE_RETCODE_DONE else None

    def _close(self, ticket):
        pos = mt5.positions_get(ticket=ticket)
        if not pos:
            return
        p = pos[0]
        ct = mt5.ORDER_TYPE_SELL if p.type == 0 else mt5.ORDER_TYPE_BUY
        t = mt5.symbol_info_tick(self.symbol)
        px = t.bid if p.type == 0 else t.ask
        mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": self.symbol, "volume": p.volume, "type": ct, "position": ticket, "price": px, "deviation": 20, "magic": self.magic, "comment": "AUTO-CLOSE", "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC})

    def _log(self, d, price, ts, rn, rp, rh, div):
        self.log.append({"time": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(), "dir": d, "price": price, "sl": self.sl, "tp": self.tp, "lot": self.lot, "rsi5": round(rn,2), "rsi5p": round(rp,2), "rsi1": round(rh,2), "div": div, "ticket": self.ticket})
        d2 = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "autopilot")
        os.makedirs(d2, exist_ok=True)
        with open(os.path.join(d2, "trade_log.json"), "w") as f:
            json.dump(self.log, f, indent=2)

    def status(self):
        a = mt5.account_info()
        return {"bal": a.balance, "eq": a.equity, "pnl": a.profit, "ticks": self.ticks, "sigs": self.signals, "trades": self.trades, "pos": "OPEN" if self.ticket else "FLAT"}
