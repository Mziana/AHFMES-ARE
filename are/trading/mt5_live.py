"""MT5 Live Data Feed - tick by tick connection."""
import MetaTrader5 as mt5
import time
from dataclasses import dataclass
from typing import Optional, Callable, List


@dataclass
class Tick:
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    timestamp: int
    spread: int


@dataclass
class Bar:
    symbol: str
    timeframe: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: int


class MT5LiveFeed:
    """Live tick and bar data from MT5."""

    def __init__(self, symbol="XAUUSD"):
        self.symbol = symbol
        self.connected = False
        self.tick_callbacks: List[Callable] = []

    def connect(self) -> bool:
        if not mt5.initialize():
            print(f"MT5 init failed: {mt5.last_error()}")
            return False
        info = mt5.terminal_info()
        if info is None or not info.trade_allowed:
            print("MT5 auto trading not allowed")
            return False
        self.connected = True
        acct = mt5.account_info()
        print(f"Connected: {self.symbol} | Account: {acct.login} | Balance: ${acct.balance:.2f}")
        return True

    def disconnect(self):
        mt5.shutdown()
        self.connected = False

    def get_tick(self) -> Optional[Tick]:
        if not self.connected:
            return None
        t = mt5.symbol_info_tick(self.symbol)
        if t is None:
            return None
        return Tick(
            symbol=self.symbol,
            bid=t.bid, ask=t.ask, last=t.last,
            volume=t.volume_real, timestamp=int(t.time),
            spread=mt5.symbol_info(self.symbol).spread
        )

    def get_bars(self, timeframe: int, count: int = 100) -> List[Bar]:
        """Get recent bars. timeframe: mt5.TIMEFRAME_M1, _M5, _H1, etc."""
        if not self.connected:
            return []
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, count)
        if rates is None:
            return []
        return [Bar(
            symbol=self.symbol, timeframe=timeframe,
            open=r["open"], high=r["high"], low=r["low"], close=r["close"],
            volume=r["tick_volume"], timestamp=int(r["time"])
        ) for r in rates]

    def get_position(self) -> Optional[dict]:
        """Get current open position for this symbol."""
        if not self.connected:
            return None
        positions = mt5.positions_get(symbol=self.symbol)
        if not positions:
            return None
        p = positions[0]
        return {
            "ticket": p.ticket,
            "type": "BUY" if p.type == 0 else "SELL",
            "volume": p.volume,
            "open_price": p.price_open,
            "current_price": p.price_current,
            "sl": p.sl,
            "tp": p.tp,
            "pnl": p.profit,
            "swap": p.swap,
        }

    def open_position(self, direction: str, sl_points: int, tp_points: int, lot: float = 0.01) -> Optional[int]:
        """Open a position. Returns ticket or None."""
        if not self.connected:
            return None
        sym = mt5.symbol_info(self.symbol)
        if sym is None:
            return None
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None:
            return None

        point = sym.point
        if direction == "BUY":
            price = tick.ask
            sl = price - sl_points * point
            tp = price + tp_points * point
            order_type = mt5.ORDER_TYPE_BUY
        else:
            price = tick.bid
            sl = price + sl_points * point
            tp = price - tp_points * point
            order_type = mt5.ORDER_TYPE_SELL

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "sl": round(sl, sym.digits),
            "tp": round(tp, sym.digits),
            "deviation": 20,
            "magic": 20260901,
            "comment": f"AUTO-{direction}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"OPENED {direction}: {result.volume} lot @ {result.price} | SL={sl:.2f} TP={tp:.2f} | Ticket={result.order}")
            return result.order
        else:
            err = result.comment if result else "No result"
            print(f"FAILED {direction}: {err}")
            return None

    def close_position(self, ticket: int) -> bool:
        """Close a specific position."""
        if not self.connected:
            return False
        position = mt5.positions_get(ticket=ticket)
        if not position:
            return False
        p = position[0]
        close_type = mt5.ORDER_TYPE_SELL if p.type == 0 else mt5.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(self.symbol)
        price = tick.bid if p.type == 0 else tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": p.volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 20260901,
            "comment": "AUTO-CLOSE",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"CLOSED ticket={ticket} @ {result.price} PnL={p.profit:.2f}")
            return True
        return False

    def get_account_info(self) -> dict:
        if not self.connected:
            return {}
        a = mt5.account_info()
        return {
            "balance": a.balance,
            "equity": a.equity,
            "margin": a.margin,
            "free_margin": a.margin_free,
            "profit": a.profit,
        }

