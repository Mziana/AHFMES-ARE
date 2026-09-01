"""
AHFMES-ARE Autopilot Runner
============================
Tick-by-tick live trading brain. Connects to MT5, feeds live data
into RSI Compass + Divergence strategy, and executes trades.

Usage:
    python -m are.trading.runner                     # XAUUSD default
    python -m are.trading.runner --symbol XAUUSD     # explicit
    python -m are.trading.runner --lot 0.02 --tp 500 --sl 300
    python -m are.trading.runner --dry-run            # paper mode
"""
import argparse
import sys
import time
import signal
from datetime import datetime, timezone

import MetaTrader5 as mt5

from .autopilot import AutopilotBrain


def main():
    parser = argparse.ArgumentParser(description="AHFMES Autopilot")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--lot", type=float, default=0.01)
    parser.add_argument("--tp", type=int, default=600, help="TP in points")
    parser.add_argument("--sl", type=int, default=400, help="SL in points")
    parser.add_argument("--interval", type=float, default=0.5, help="Tick poll seconds")
    parser.add_argument("--max-hold", type=int, default=10800, help="Max hold seconds")
    parser.add_argument("--dry-run", action="store_true", help="No real trades")
    args = parser.parse_args()

    # Connect MT5
    if not mt5.initialize():
        print(f"MT5 init failed: {mt5.last_error()}")
        sys.exit(1)

    acct = mt5.account_info()
    if acct is None:
        print("No MT5 account info")
        sys.exit(1)

    print(f"{'='*60}")
    print(f"  AHFMES-ARE AUTOPILOT")
    print(f"  Symbol:    {args.symbol}")
    print(f"  Account:   #{acct.login}")
    print(f"  Balance:   ${acct.balance:.2f}")
    print(f"  Equity:    ${acct.equity:.2f}")
    print(f"  Lot:       {args.lot}")
    print(f"  TP:        {args.tp} pts")
    print(f"  SL:        {args.sl} pts")
    print(f"  Dry Run:   {args.dry_run}")
    print(f"  Strategy:  RSI(14,Close) + H1 Compass + Divergence")
    print(f"{'='*60}")

    brain = AutopilotBrain(
        symbol=args.symbol,
        lot=args.lot,
        sl_points=args.sl,
        tp_points=args.tp,
        max_hold_s=args.max_hold,
    )
    if args.dry_run:
        brain._open = lambda d: print(f"[DRY] Would open {d}") or None
        brain._close = lambda t: print(f"[DRY] Would close {t}")

    brain.init()

    # Graceful shutdown
    running = True

    def stop(sig, frame):
        nonlocal running
        print(f"\n[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Stopping...")
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Autopilot RUNNING — Ctrl+C to stop")
    cycle = 0
    while running:
        try:
            tick = mt5.symbol_info_tick(args.symbol)
            if tick is None:
                time.sleep(1)
                continue

            sig = brain.on_tick(tick.bid, tick.ask, int(tick.time))
            cycle += 1

            if cycle % 120 == 0:  # Every ~60 seconds at 0.5s interval
                s = brain.status()
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] "
                      f"Tick#{s['ticks']} Sig#{s['sigs']} Trades#{s['trades']} "
                      f"Pos={s['pos']} Bal=${s['bal']:.2f} Eq=${s['eq']:.2f} PnL={s['pnl']:.2f}")

            time.sleep(args.interval)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)

    # Shutdown
    brain.status()
    mt5.shutdown()
    print("Autopilot STOPPED.")


if __name__ == "__main__":
    main()
