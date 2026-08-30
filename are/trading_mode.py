"""
ARE Trading Mode System
Handles Live Trading, Paper Trading, and Off modes.
"""
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from enum import Enum


class TradingMode(Enum):
    OFF = "off"
    PAPER = "paper"
    LIVE = "live"


@dataclass
class Position:
    id: str
    symbol: str
    direction: str
    entry_price: float
    lot: float
    stop_loss: float
    take_profit: float
    opened_at: float
    status: str = "OPEN"
    close_price: Optional[float] = None
    close_time: Optional[float] = None
    pnl: float = 0.0
    rr_ratio: float = 0.0


@dataclass
class TradingAccount:
    mode: TradingMode = TradingMode.OFF
    balance: float = 100000.0
    equity: float = 100000.0
    margin_used: float = 0.0
    free_margin: float = 100000.0
    positions: List[Position] = field(default_factory=list)
    history: List[Position] = field(default_factory=list)
    total_pnl: float = 0.0
    win_count: int = 0
    loss_count: int = 0

    @property
    def open_positions(self):
        return [p for p in self.positions if p.status == "OPEN"]

    @property
    def win_rate(self):
        t = self.win_count + self.loss_count
        return (self.win_count / t * 100) if t > 0 else 0.0

    @property
    def profit_factor(self):
        gp = sum(p.pnl for p in self.history if p.pnl > 0)
        gl = abs(sum(p.pnl for p in self.history if p.pnl < 0))
        return (gp / gl) if gl > 0 else 0.0

    @property
    def max_drawdown(self):
        if not self.history: return 0.0
        peak, max_dd, eq = 100000.0, 0.0, 100000.0
        for t in self.history:
            eq += t.pnl
            peak = max(peak, eq)
            dd = (peak - eq) / peak * 100
            max_dd = max(max_dd, dd)
        return max_dd


class PaperTradingEngine:
    def __init__(self, initial_balance=100000.0):
        self.account = TradingAccount(mode=TradingMode.PAPER, balance=initial_balance, equity=initial_balance, free_margin=initial_balance)
        self.slippage_pips = 0.5
        self.commission_per_lot = 7.0

    def open_position(self, symbol, direction, price, lot=0.01, sl_pips=100, tp_pips=200):
        if self.account.mode == TradingMode.OFF:
            return {"success": False, "error": "Trading is OFF"}
        if len(self.account.open_positions) >= 5:
            return {"success": False, "error": "Max 5 positions"}
        pv = 0.01
        if direction == "BUY":
            entry = price + self.slippage_pips * pv
            sl, tp = entry - sl_pips * pv, entry + tp_pips * pv
        else:
            entry = price - self.slippage_pips * pv
            sl, tp = entry + sl_pips * pv, entry - tp_pips * pv
        pos = Position(id=str(uuid.uuid4())[:8], symbol=symbol, direction=direction, entry_price=entry, lot=lot, stop_loss=sl, take_profit=tp, opened_at=time.time(), rr_ratio=tp_pips/sl_pips if sl_pips>0 else 0)
        margin = entry * lot * 100 * 0.01
        self.account.positions.append(pos)
        self.account.margin_used += margin
        self.account.free_margin = self.account.equity - self.account.margin_used
        return {"success": True, "position": {"id": pos.id, "symbol": pos.symbol, "direction": pos.direction, "entry": pos.entry_price, "lot": pos.lot, "sl": pos.stop_loss, "tp": pos.take_profit, "rr_ratio": pos.rr_ratio}}

    def close_position(self, position_id, current_price):
        pos = next((p for p in self.account.positions if p.id == position_id and p.status == "OPEN"), None)
        if not pos: return {"success": False, "error": "Not found"}
        pv = 0.01
        pips = (current_price - pos.entry_price) / pv if pos.direction == "BUY" else (pos.entry_price - current_price) / pv
        pnl = pips * pos.lot * 10 - self.commission_per_lot * pos.lot
        pos.status, pos.close_price, pos.close_time, pos.pnl = "CLOSED", current_price, time.time(), pnl
        self.account.balance += pnl
        self.account.equity = self.account.balance
        self.account.total_pnl += pnl
        if pnl > 0: self.account.win_count += 1
        else: self.account.loss_count += 1
        self.account.positions.remove(pos)
        self.account.history.append(pos)
        return {"success": True, "closed": {"id": pos.id, "pnl": round(pnl, 2), "pips": round(pips, 1)}}

    def get_status(self):
        return {"mode": self.account.mode.value, "balance": round(self.account.balance, 2), "equity": round(self.account.equity, 2), "margin_used": round(self.account.margin_used, 2), "free_margin": round(self.account.free_margin, 2), "total_pnl": round(self.account.total_pnl, 2), "open_positions": len(self.account.open_positions), "total_trades": self.account.win_count + self.account.loss_count, "win_rate": round(self.account.win_rate, 1), "profit_factor": round(self.account.profit_factor, 2), "max_drawdown": round(self.account.max_drawdown, 1), "positions": [{"id": p.id, "symbol": p.symbol, "direction": p.direction, "entry": p.entry_price, "sl": p.stop_loss, "tp": p.take_profit, "lot": p.lot} for p in self.account.open_positions]}


class LiveTradingBridge:
    def __init__(self):
        self.connected = False
        self.mt5 = None
        self.magic = 20260830

    def connect(self):
        try:
            import MetaTrader5 as mt5
            if not mt5.initialize(): return {"success": False, "error": "MT5 init failed"}
            info = mt5.account_info()
            self.connected, self.mt5 = True, mt5
            return {"success": True, "account": {"login": info.login, "server": info.server, "balance": info.balance, "equity": info.equity}}
        except ImportError: return {"success": False, "error": "pip install MetaTrader5"}
        except Exception as e: return {"success": False, "error": str(e)}

    def disconnect(self):
        if self.mt5: self.mt5.shutdown(); self.connected = False

    def send_order(self, symbol, direction, lot, price, sl, tp, comment=""):
        if not self.connected: return {"success": False, "error": "MT5 not connected"}
        try:
            mt5 = self.mt5
            req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": symbol, "volume": lot, "type": mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL, "price": mt5.symbol_info_tick(symbol).ask if direction == "BUY" else mt5.symbol_info_tick(symbol).bid, "sl": sl, "tp": tp, "magic": self.magic, "comment": f"ARE_{comment}", "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC}
            result = mt5.order_send(req)
            if result.retcode != mt5.TRADE_RETCODE_DONE: return {"success": False, "error": result.comment}
            return {"success": True, "order": {"ticket": result.ticket, "price": result.price}}
        except Exception as e: return {"success": False, "error": str(e)}

    def get_account_info(self):
        if not self.connected or not self.mt5: return {"connected": False}
        i = self.mt5.account_info()
        return {"connected": True, "login": i.login, "balance": i.balance, "equity": i.equity}


# Global instances
paper_engine = PaperTradingEngine()
live_bridge = LiveTradingBridge()
current_mode = TradingMode.OFF


def get_trading_status():
    return {"mode": current_mode.value, "mt5_connected": live_bridge.connected,
            "paper": paper_engine.get_status() if current_mode == TradingMode.PAPER else None,
            "live": live_bridge.get_account_info() if current_mode == TradingMode.LIVE and live_bridge.connected else None}


def set_trading_mode(mode):
    global current_mode
    if mode == "paper":
        current_mode = TradingMode.PAPER
        paper_engine.account.mode = TradingMode.PAPER
        return {"success": True, "mode": "paper", "message": "Paper trading ON. Virtual 100K."}
    elif mode == "live":
        if not live_bridge.connected:
            r = live_bridge.connect()
            if not r["success"]: return {"success": False, "error": r["error"]}
        current_mode = TradingMode.LIVE
        return {"success": True, "mode": "live", "message": "Live trading ON. Real money!"}
    elif mode == "off":
        current_mode = TradingMode.OFF
        return {"success": True, "mode": "off", "message": "Trading OFF."}
    return {"success": False, "error": f"Unknown: {mode}"}
