"""
Autopilot Brain v2 — Multi-Timeframe RSI Trading Engine
=========================================================
Supports all 7 timeframes: M1, M5, M15, M30, H1, H4, D1

Architecture:
  D1/H4    → Macro trend direction (very slow, daily/4h RSI)
  H1       → Trend compass (RSI 50 = pivot, >50 bull, <50 bear)
  M30/M15  → Intermediate confirmation (momentum alignment)
  M5/M1    → Entry execution (cross 30/70, divergence detection)

Every tick:
  1. Update all timeframe buffers
  2. Compute RSI(14,Close) for each TF
  3. Check macro trend → compass → momentum → entry signal
  4. Execute if all layers agree
"""
import time, json, os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple
import MetaTrader5 as mt5


# ──────────────────────────────────────────────────────────────
# TIMEFRAME CONFIGURATION
# ──────────────────────────────────────────────────────────────

TIMEFRAMES = {
    "M1":  mt5.TIMEFRAME_M1,
    "M5":  mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1":  mt5.TIMEFRAME_H1,
    "H4":  mt5.TIMEFRAME_H4,
    "D1":  mt5.TIMEFRAME_D1,
}

# How many bars to keep in memory per TF
TF_BUFFER_SIZE = {
    "M1":  300,   # 5 hours of M1
    "M5":  300,   # 25 hours of M5
    "M15": 200,   # 50 hours of M15
    "M30": 200,   # 100 hours of M30
    "H1":  200,   # 200 hours of H1
    "H4":  150,   # 25 days of H4
    "D1":  100,   # 100 days of D1
}

# Bar duration in seconds for each TF
TF_SECONDS = {
    "M1": 60, "M5": 300, "M15": 900, "M30": 1800,
    "H1": 3600, "H4": 14400, "D1": 86400,
}

# Trend layers: which TFs determine what
LAYER_MACRO    = ["D1", "H4"]       # Macro trend
LAYER_COMPASS  = ["H1"]              # Compass (50 pivot)
LAYER_MOMENTUM = ["M30", "M15"]      # Momentum confirmation
LAYER_ENTRY    = ["M5", "M1"]        # Entry execution


# ──────────────────────────────────────────────────────────────
# INDICATOR FUNCTIONS
# ──────────────────────────────────────────────────────────────

def compute_rsi(closes: List[float], period: int = 14) -> List[Optional[float]]:
    """EMA-smoothed RSI(14) — Wilder's method."""
    if len(closes) < period + 1:
        return [None] * len(closes)
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
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


def detect_divergence(prices: List[float], rsi_vals: List[Optional[float]],
                      lookback: int = 20) -> float:
    """
    Detect bullish/bearish divergence.
    +1.0 = bullish (price LL + RSI HL → BUY)
    -1.0 = bearish (price HH + RSI LH → SELL)
     0.0 = none
    """
    if len(prices) < lookback:
        return 0.0
    wp = prices[-lookback:]
    wr = [r for r in rsi_vals[-lookback:] if r is not None]
    if len(wp) < 10 or len(wr) < 10:
        return 0.0
    h = len(wp) // 2
    # Bullish: price makes lower low, RSI makes higher low
    ppl, cpl = min(wp[:h]), min(wp[h:])
    prl, crl = min(wr[:h]), min(wr[h:])
    if cpl < ppl and crl > prl and abs(cpl - ppl) / ppl * 100 > 1.0:
        return 1.0
    # Bearish: price makes higher high, RSI makes lower high
    pph, cph = max(wp[:h]), max(wp[h:])
    prh, crh = max(wr[:h]), max(wr[h:])
    if cph > pph and crh < prh and abs(cph - pph) / pph * 100 > 1.0:
        return -1.0
    return 0.0


def compute_atr(highs: List[float], lows: List[float], closes: List[float],
                period: int = 14) -> Optional[float]:
    """Average True Range for volatility filter."""
    if len(closes) < period + 1:
        return None
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]),
                 abs(lows[i] - closes[i - 1]))
        trs.append(tr)
    if len(trs) < period:
        return None
    atr = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr = (atr * (period - 1) + trs[i]) / period
    return atr


# ──────────────────────────────────────────────────────────────
# MULTI-TIMEFRAME STATE
# ──────────────────────────────────────────────────────────────

class TFState:
    """State buffer for a single timeframe."""
    def __init__(self, name: str, max_bars: int = 200):
        self.name = name
        self.max_bars = max_bars
        self.opens: List[float] = []
        self.highs: List[float] = []
        self.lows: List[float] = []
        self.closes: List[float] = []
        self.volumes: List[float] = []
        self.rsi: List[Optional[float]] = []
        self.last_bar_time: int = 0

    def update_from_mt5(self, symbol: str, tf_key: str) -> int:
        """Fetch latest bars from MT5, return new bar count."""
        tf = TIMEFRAMES[tf_key]
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, self.max_bars)
        if rates is None:
            return 0
        new_opens = [float(r["open"]) for r in rates]
        new_highs = [float(r["high"]) for r in rates]
        new_lows = [float(r["low"]) for r in rates]
        new_closes = [float(r["close"]) for r in rates]
        new_vols = [float(r["tick_volume"]) for r in rates]
        new_time = int(rates[-1]["time"])

        if new_time == self.last_bar_time:
            # Same bar — just update close and volume
            if self.closes:
                self.closes[-1] = new_closes[-1]
                self.highs[-1] = max(self.highs[-1], new_highs[-1])
                self.lows[-1] = min(self.lows[-1], new_lows[-1])
                self.volumes[-1] = new_vols[-1]
                self.rsi = compute_rsi(self.closes, 14)
                return 0
            return 0

        # New bar — append and trim
        self.opens = new_opens
        self.highs = new_highs
        self.lows = new_lows
        self.closes = new_closes
        self.volumes = new_vols
        self.last_bar_time = new_time
        self.rsi = compute_rsi(self.closes, 14)
        return 1

    def rsi_current(self) -> Optional[float]:
        return self.rsi[-1] if self.rsi and self.rsi[-1] is not None else None

    def rsi_prev(self) -> Optional[float]:
        return self.rsi[-2] if self.rsi and len(self.rsi) >= 2 and self.rsi[-2] is not None else None

    def status_str(self) -> str:
        r = self.rsi_current()
        return f"RSI={r:.1f}" if r is not None else "RSI=N/A"


# ──────────────────────────────────────────────────────────────
# AUTOPILOT BRAIN
# ──────────────────────────────────────────────────────────────

class AutopilotBrain:
    """
    Multi-timeframe RSI autopilot.

    Layer hierarchy:
      D1/H4  → MACRO trend (RSI >50 = bullish, <50 = bearish)
      H1     → COMPASS (RSI >50 = favor BUY, <50 = favor SELL)
      M30/M15 → MOMENTUM (RSI direction agrees with entry direction)
      M5/M1  → ENTRY (cross 30/70, divergence detection)
    """

    def __init__(self, symbol="XAUUSD", lot=0.01, sl_points=400,
                 tp_points=600, max_hold_s=10800):
        self.symbol = symbol
        self.lot = lot
        self.sl = sl_points
        self.tp = tp_points
        self.max_hold = max_hold_s
        self.magic = 20260901

        # Multi-TF state
        self.tf: Dict[str, TFState] = {}
        for name in TIMEFRAMES:
            self.tf[name] = TFState(name, TF_BUFFER_SIZE[name])

        # Position tracking
        self.ticket: Optional[int] = None
        self.open_time: int = 0
        self.open_price: float = 0.0
        self.open_direction: str = ""

        # Statistics
        self.ticks: int = 0
        self.signals: int = 0
        self.trades: int = 0
        self.log: List[dict] = []

    def init(self):
        """Load initial bars for all timeframes."""
        print(f"Initializing {self.symbol} with {len(TIMEFRAMES)} timeframes...")
        for name in TIMEFRAMES:
            count = self.tf[name].update_from_mt5(self.symbol, name)
            r = self.tf[name].rsi_current()
            r_str = f"{r:.1f}" if r is not None else "N/A"
            print(f"  {name:>4s}: {len(self.tf[name].closes):>4d} bars | RSI(14)={r_str}")

        # Check existing position
        pos = mt5.positions_get(symbol=self.symbol)
        if pos:
            self.ticket = pos[0].ticket
            self.open_time = int(pos[0].time)
            self.open_price = pos[0].price_open
            self.open_direction = "BUY" if pos[0].type == 0 else "SELL"
            print(f"Existing position: {self.open_direction} @ {self.open_price:.2f} ticket={self.ticket}")
        else:
            print("No open position — FLAT")

    def on_tick(self, bid: float, ask: float, ts: int) -> Optional[str]:
        """
        Process one tick. Returns signal string if trade opened, else None.
        This is the main "heartbeat" — called every tick from MT5.
        """
        self.ticks += 1
        price = (bid + ask) / 2.0

        # 1. Update all timeframes
        new_bars = {}
        for name in TIMEFRAMES:
            new_bars[name] = self.tf[name].update_from_mt5(self.symbol, name)

        # 2. Manage open position (check time exit)
        if self.ticket:
            self._manage(price, ts)
            return None

        # 3. Evaluate entry — only when M5 gets a new bar
        if new_bars.get("M5", 0) > 0 or new_bars.get("M1", 0) > 0:
            return self._eval(price, ts)

        return None

    def _eval(self, price: float, ts: int) -> Optional[str]:
        """
        Multi-layer signal evaluation.

        Layer 1: MACRO — D1/H4 RSI determines overall bias
        Layer 2: COMPASS — H1 RSI 50 pivot confirms direction
        Layer 3: MOMENTUM — M30/M15 RSI agrees
        Layer 4: ENTRY — M5/M1 cross 30/70 or divergence
        """
        # ── Layer 1: MACRO TREND (D1 + H4) ──
        d1_rsi = self.tf["D1"].rsi_current()
        h4_rsi = self.tf["H4"].rsi_current()
        if d1_rsi is None or h4_rsi is None:
            return None

        # Both D1 and H4 must agree on direction
        macro_bias = 0
        if d1_rsi > 50 and h4_rsi > 50:
            macro_bias = 1    # BULLISH
        elif d1_rsi < 50 and h4_rsi < 50:
            macro_bias = -1   # BEARISH
        else:
            return None       # D1 and H4 disagree → no trade

        # ── Layer 2: COMPASS (H1) ──
        h1_rsi = self.tf["H1"].rsi_current()
        if h1_rsi is None:
            return None

        compass = 0
        if h1_rsi > 51:
            compass = 1       # Bullish compass
        elif h1_rsi < 49:
            compass = -1      # Bearish compass
        else:
            return None       # H1 in no-man's land (49-51)

        # Compass must agree with macro
        if compass != macro_bias:
            return None

        # ── Layer 3: MOMENTUM (M30 + M15) ──
        m30_rsi = self.tf["M30"].rsi_current()
        m15_rsi = self.tf["M15"].rsi_current()
        if m30_rsi is None or m15_rsi is None:
            return None

        # At least one momentum TF must agree
        momentum_agree = False
        if macro_bias == 1:
            momentum_agree = m30_rsi > 45 or m15_rsi > 45
        else:
            momentum_agree = m30_rsi < 55 or m15_rsi < 55

        if not momentum_agree:
            return None

        # ── Layer 4: ENTRY (M5 + M1) ──
        m5_rsi = self.tf["M5"].rsi_current()
        m5_prev = self.tf["M5"].rsi_prev()
        m1_rsi = self.tf["M1"].rsi_current()
        m1_prev = self.tf["M1"].rsi_prev()

        if m5_rsi is None or m5_prev is None:
            return None

        signal = None

        # ── ENTRY TYPE 1: RSI Cross 30/70 ──
        if macro_bias == 1:
            # BUY: M5 RSI crosses UP through 30
            if m5_prev < 30 and m5_rsi >= 30:
                signal = "BUY"
            # Alternative: M1 also crosses 30 for extra confirmation
            elif m1_rsi is not None and m1_prev is not None:
                if m1_prev < 30 and m1_rsi >= 30:
                    signal = "BUY"
        else:
            # SELL: M5 RSI crosses DOWN through 70
            if m5_prev > 70 and m5_rsi <= 70:
                signal = "SELL"
            elif m1_rsi is not None and m1_prev is not None:
                if m1_prev > 70 and m1_rsi <= 70:
                    signal = "SELL"

        # ── ENTRY TYPE 2: DIVERGENCE (strongest signal) ──
        if signal is None:
            m5_div = detect_divergence(self.tf["M5"].closes, self.tf["M5"].rsi, 20)
            if m5_div > 0 and macro_bias == 1:
                signal = "BUY"
            elif m5_div < 0 and macro_bias == -1:
                signal = "SELL"

        if signal is None:
            return None

        # ── FINAL CHECK: Time filter (skip dead hours) ──
        from datetime import datetime as dt
        hour = dt.fromtimestamp(ts, tz=timezone.utc).hour
        # Skip Asian session low-vol hours (22-01 UTC)
        if hour in (0, 22, 23):
            return None

        # ── EXECUTE ──
        ticket = self._open(signal)
        if ticket:
            self.ticket = ticket
            self.open_time = ts
            self.open_price = price
            self.open_direction = signal
            self.trades += 1
            self.signals += 1
            tstr = dt.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M:%S")
            print(f"[{tstr}] {signal} @ {price:.2f} | "
                  f"D1={d1_rsi:.1f} H4={h4_rsi:.1f} H1={h1_rsi:.1f} "
                  f"M30={m30_rsi:.1f} M15={m15_rsi:.1f} M5={m5_rsi:.1f} "
                  f"M1={m1_rsi if m1_rsi else 'N/A'}")
            self._log(signal, price, ts, {
                "d1": d1_rsi, "h4": h4_rsi, "h1": h1_rsi,
                "m30": m30_rsi, "m15": m15_rsi, "m5": m5_rsi, "m1": m1_rsi,
            })
            return signal
        return None

    def _manage(self, price: float, ts: int):
        """Manage open position: time exit."""
        if self.ticket and ts - self.open_time >= self.max_hold:
            self._close(self.ticket)
            tstr = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M:%S")
            pnl = self._get_pnl(self.ticket)
            print(f"[{tstr}] TIME EXIT @ {price:.2f} PnL={pnl:.2f}")
            self.ticket = None

    def _get_pnl(self, ticket: int) -> float:
        pos = mt5.positions_get(ticket=ticket)
        return pos[0].profit if pos else 0.0

    def _open(self, direction: str) -> Optional[int]:
        """Open a position. Returns ticket or None."""
        s = mt5.symbol_info(self.symbol)
        t = mt5.symbol_info_tick(self.symbol)
        if not s or not t:
            return None
        pt = s.point
        if direction == "BUY":
            p = t.ask
            sl = round(t.ask - self.sl * pt, s.digits)
            tp = round(t.ask + self.tp * pt, s.digits)
            ot = mt5.ORDER_TYPE_BUY
        else:
            p = t.bid
            sl = round(t.bid + self.sl * pt, s.digits)
            tp = round(t.bid - self.tp * pt, s.digits)
            ot = mt5.ORDER_TYPE_SELL

        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": self.lot,
            "type": ot,
            "price": p,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": self.magic,
            "comment": f"AUTO-{direction}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        r = mt5.order_send(req)
        if r and r.retcode == mt5.TRADE_RETCODE_DONE:
            return r.order
        return None

    def _close(self, ticket: int):
        """Close a specific position."""
        pos = mt5.positions_get(ticket=ticket)
        if not pos:
            return
        p = pos[0]
        ct = mt5.ORDER_TYPE_SELL if p.type == 0 else mt5.ORDER_TYPE_BUY
        t = mt5.symbol_info_tick(self.symbol)
        px = t.bid if p.type == 0 else t.ask
        mt5.order_send({
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": p.volume,
            "type": ct,
            "position": ticket,
            "price": px,
            "deviation": 20,
            "magic": self.magic,
            "comment": "AUTO-CLOSE",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        })

    def _log(self, direction: str, price: float, ts: int, rsi_data: dict):
        entry = {
            "time": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
            "dir": direction,
            "price": price,
            "sl": self.sl,
            "tp": self.tp,
            "lot": self.lot,
            "rsi": rsi_data,
            "ticket": self.ticket,
        }
        self.log.append(entry)
        d2 = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "autopilot"
        )
        os.makedirs(d2, exist_ok=True)
        with open(os.path.join(d2, "trade_log.json"), "w") as f:
            json.dump(self.log, f, indent=2)

    def status(self) -> dict:
        """Return current brain status for monitoring."""
        a = mt5.account_info()
        tf_rsi = {}
        for name in TIMEFRAMES:
            r = self.tf[name].rsi_current()
            tf_rsi[name] = round(r, 1) if r is not None else None

        return {
            "bal": a.balance,
            "eq": a.equity,
            "pnl": a.profit,
            "ticks": self.ticks,
            "sigs": self.signals,
            "trades": self.trades,
            "pos": self.open_direction if self.ticket else "FLAT",
            "rsi": tf_rsi,
        }

    def print_dashboard(self):
        """Print a formatted dashboard to terminal."""
        s = self.status()
        print(f"\n{'='*70}")
        print(f"  AUTOPILOT DASHBOARD — {self.symbol}")
        print(f"{'='*70}")
        print(f"  Balance: ${s['bal']:.2f}  |  Equity: ${s['eq']:.2f}  |  PnL: ${s['pnl']:.2f}")
        print(f"  Ticks: {s['ticks']}  |  Signals: {s['sigs']}  |  Trades: {s['trades']}")
        print(f"  Position: {s['pos']}")
        print(f"{'-'*70}")
        print(f"  TIMEFRAME RSI(14,Close):")
        for name in ["D1", "H4", "H1", "M30", "M15", "M5", "M1"]:
            r = s["rsi"].get(name)
            if r is not None:
                bar = "=" * int(r / 2)
                zone = "BULL" if r > 50 else "BEAR" if r < 50 else "NEUTRAL"
                print(f"    {name:>4s}: {r:>5.1f} |{bar:<50s}| {zone}")
            else:
                print(f"    {name:>4s}:   N/A")
        print(f"{'='*70}")
