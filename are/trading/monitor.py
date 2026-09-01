"""
AHFMES-ARE Live Monitor Dashboard
===================================
Real-time monitoring of autopilot across all 7 timeframes.

Usage:
    python -m are.trading.monitor
    python -m are.trading.monitor --symbol XAUUSD
"""
import argparse
import time
import json
import os
from datetime import datetime, timezone

import MetaTrader5 as mt5


LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "autopilot"
)

TIMEFRAMES = {
    "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30, "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}


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


def monitor(symbol="XAUUSD"):
    if not mt5.initialize():
        print(f"MT5 init failed: {mt5.last_error()}")
        return

    acct = mt5.account_info()
    if acct is None:
        print("No MT5 account")
        return

    while True:
        try:
            clear_screen()
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            acct = mt5.account_info()
            tick = mt5.symbol_info_tick(symbol)
            pos = mt5.positions_get(symbol=symbol)
            sym_info = mt5.symbol_info(symbol)

            print(f"{'='*72}")
            print(f"  AHFMES-ARE MULTI-TF MONITOR  |  {now}  |  {symbol}")
            print(f"{'='*72}")
            print(f"  Account: #{acct.login}  |  Balance: ${acct.balance:.2f}  |  Equity: ${acct.equity:.2f}  |  PnL: ${acct.profit:.2f}")
            print(f"{'='*72}")

            # ── ALL TIMEFRAME RSI ──
            print(f"  RSI(14,Close) — MULTI-TIMEFRAME:")
            print(f"  {'TF':>4s}  {'RSI':>6s}  {'Zone':>8s}  {'Bar':>50s}")
            print(f"  {'-'*68}")

            for name in ["D1", "H4", "H1", "M30", "M15", "M5", "M1"]:
                tf = TIMEFRAMES[name]
                rates = mt5.copy_rates_from_pos(symbol, tf, 0, 50)
                if rates is not None and len(rates) > 15:
                    closes = [float(r["close"]) for r in rates]
                    rsi = compute_rsi(closes, 14)
                    r = rsi[-1] if rsi and rsi[-1] is not None else None
                    if r is not None:
                        bar_len = int(r / 2)
                        bar = "=" * bar_len + ">" * 1
                        zone = "🟢 BULL" if r > 50 else "🔴 BEAR" if r < 50 else "⚪ NEUTRAL"
                        # Mark trend layer
                        layer = ""
                        if name in ("D1", "H4"):
                            layer = " [MACRO]"
                        elif name == "H1":
                            layer = " [COMPASS]"
                        elif name in ("M30", "M15"):
                            layer = " [MOMENTUM]"
                        elif name in ("M5", "M1"):
                            layer = " [ENTRY]"
                        print(f"  {name:>4s}  {r:>6.1f}  {zone:>8s}  {bar:<50s}{layer}")
                    else:
                        print(f"  {name:>4s}    N/A")
                else:
                    print(f"  {name:>4s}  (no data)")

            print(f"{'-'*72}")

            # ── TICK INFO ──
            spread = sym_info.spread if sym_info else 0
            print(f"  Bid: {tick.bid:.2f}  |  Ask: {tick.ask:.2f}  |  Spread: {spread} pts")

            # ── POSITION ──
            if pos:
                p = pos[0]
                dir_str = "BUY 🟢" if p.type == 0 else "SELL 🔴"
                hold = datetime.now(timezone.utc).timestamp() - p.time
                print(f"  POSITION: {dir_str} {p.volume} lot @ {p.price_open:.2f}")
                print(f"  Current: {p.price_current:.2f}  |  PnL: ${p.profit:.2f}  |  SL: {p.sl:.2f}  |  TP: {p.tp:.2f}")
                print(f"  Hold time: {int(hold)}s ({int(hold/60)}min)")
            else:
                print(f"  POSITION: FLAT — waiting for signal...")

            print(f"{'-'*72}")

            # ── RECENT TRADES ──
            trades = load_trade_log()
            recent = trades[-5:] if trades else []
            if recent:
                print(f"  RECENT TRADES:")
                for t in reversed(recent):
                    rsi_str = ""
                    if "rsi" in t:
                        r = t["rsi"]
                        rsi_str = (f"D1={r.get('d1',0):.0f} H4={r.get('h4',0):.0f} "
                                   f"H1={r.get('h1',0):.0f} M5={r.get('m5',0):.0f}")
                    print(f"    {t['time'][:19]}  {t['dir']:4s} @ {t['price']:.2f}  {rsi_str}")
            else:
                print(f"  No trades yet.")

            print(f"{'='*72}")
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD")
    args = parser.parse_args()
    monitor(args.symbol)
