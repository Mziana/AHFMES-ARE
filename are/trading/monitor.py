"""
AHFMES-ARE Live Monitor Dashboard
===================================
Real-time monitoring of autopilot status, signals, and trades.

Usage:
    python -m are.trading.monitor
"""
import time
import json
import os
from datetime import datetime, timezone

import MetaTrader5 as mt5


LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "autopilot")


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def load_trade_log():
    path = os.path.join(LOG_DIR, "trade_log.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


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


def monitor():
    if not mt5.initialize():
        print(f"MT5 init failed: {mt5.last_error()}")
        return

    acct = mt5.account_info()
    if acct is None:
        print("No MT5 account")
        return

    symbol = "XAUUSD"
    while True:
        try:
            clear_screen()
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            acct = mt5.account_info()
            tick = mt5.symbol_info_tick(symbol)
            pos = mt5.positions_get(symbol=symbol)

            # Compute M5 RSI
            m5_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 100)
            m5_rsi = compute_rsi([float(r["close"]) for r in m5_rates]) if m5_rates is not None else []

            # Compute H1 RSI
            h1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
            h1_rsi = compute_rsi([float(r["close"]) for r in h1_rates]) if h1_rates is not None else []

            m5_val = m5_rsi[-1] if m5_rsi and m5_rsi[-1] is not None else 0
            h1_val = h1_rsi[-1] if h1_rsi and h1_rsi[-1] is not None else 0
            trend = "BULLISH" if h1_val > 50 else "BEARISH"
            trend_emoji = "🟢" if h1_val > 50 else "🔴"

            spread = mt5.symbol_info(symbol).spread if mt5.symbol_info(symbol) else 0

            # Trade log
            trades = load_trade_log()
            recent = trades[-5:] if trades else []

            print(f"{'='*65}")
            print(f"  AHFMES-ARE LIVE MONITOR  |  {now}")
            print(f"{'='*65}")
            print(f"  Account: #{acct.login}  |  Balance: ${acct.balance:.2f}  |  Equity: ${acct.equity:.2f}")
            print(f"{'='*65}")
            print(f"  {symbol}")
            print(f"  Bid: {tick.bid:.2f}  |  Ask: {tick.ask:.2f}  |  Spread: {spread}")
            print(f"  RSI M5: {m5_val:.1f}  |  RSI H1: {h1_val:.1f}  |  Trend: {trend_emoji} {trend}")
            print(f"{'-'*65}")

            if pos:
                p = pos[0]
                dir_str = "BUY" if p.type == 0 else "SELL"
                print(f"  POSITION: {dir_str} {p.volume} lot @ {p.price_open:.2f}")
                print(f"  Current: {p.price_current:.2f}  |  PnL: ${p.profit:.2f}  |  SL: {p.sl:.2f}  |  TP: {p.tp:.2f}")
            else:
                print(f"  POSITION: FLAT (no open trades)")
            print(f"{'-'*65}")

            if recent:
                print(f"  RECENT TRADES:")
                for t in reversed(recent):
                    print(f"    {t['time'][:19]}  {t['dir']:4s} @ {t['price']:.2f}  "
                          f"RSI5={t['rsi5']:.1f} RSI1={t['rsi1']:.1f} Div={t['div']}")
            else:
                print(f"  No trades yet.")

            print(f"{'='*65}")
            print(f"  Refreshing in 5s...  |  Ctrl+C to exit")
            time.sleep(5)

        except KeyboardInterrupt:
            print("\nMonitor stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)

    mt5.shutdown()


if __name__ == "__main__":
    monitor()
