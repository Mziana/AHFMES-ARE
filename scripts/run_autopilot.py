#!/usr/bin/env python3
"""Run Autopilot Brain - live tick-by-tick trading."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
from are.trading.autopilot import AutopilotBrain

def main():
    print("=== AUTOPILOT BRAIN STARTING ===")
    print("Strategy: RSI(14) + H1 Compass + Divergence")
    print("Symbol: XAUUSD | Lot: 0.01 | SL: 400 pts | TP: 600 pts")
    print()

    if not mt5.initialize():
        print(f"MT5 FAILED: {mt5.last_error()}")
        return

    brain = AutopilotBrain(symbol="XAUUSD", lot=0.01, sl_points=400, tp_points=600)
    brain.init()

    print()
    print("Listening for ticks...")
    print("Press Ctrl+C to stop")
    print()

    last_status = time.time()
    try:
        while True:
            tick = mt5.symbol_info_tick("XAUUSD")
            if tick:
                brain.on_tick(tick.bid, tick.ask, int(tick.time))

            # Status every 60 seconds
            if time.time() - last_status >= 60:
                s = brain.status()
                print(f"[STATUS] Bal={s['"bal"']:.2f} Eq={s['"eq"']:.2f} PnL={s['"pnl"']:.2f} Ticks={s['"ticks"']} Signals={s['"sigs"']} Trades={s['"trades"']} Pos={s['"pos"']}")
                last_status = time.time()

            time.sleep(0.1)  # 100ms tick rate

    except KeyboardInterrupt:
        print()
        print("=== AUTOPILOT STOPPED ===")
        s = brain.status()
        print(f"Final: {s}")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
