"""
ARE Trading Engine -- The Living Brain
=======================================
This is NOT a script you run. This is a PART OF ARE.

ARE is the organism. Engine is its brain.
MT5 is its heartbeat. Config is its DNA.

Usage:
    from are import ARE
    are = ARE()
    are.live.start()     # Brain starts living
    are.live.status()    # Brain reports state
    are.live.stop()      # Brain sleeps

    # Or via CLI:
    # python -m are.cli live start
    # python -m are.cli live dashboard
    # python -m are.cli live status
"""
import os
import json
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None

from .ai_brain import HAS_ANTHROPIC, HAS_OPENAI
from .autopilot import (
    AutopilotBrain, TFState, TIMEFRAMES, TF_BUFFER_SIZE,
    compute_rsi, detect_divergence
)


class ARELiveEngine:
    """
    The living trading engine. Reads config.yaml, connects to MT5,
    and processes ticks as its heartbeat.

    NOT a script. A BEING.
    """

    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)
        self.brain = None
        self._running = False
        self._thread = None
        self._tick_count = 0
        self._start_time = None
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._pid_file = os.path.join(base, "data", "autopilot", "engine.pid")
        self._log_file = os.path.join(base, "data", "autopilot", "engine.log")

    def _load_config(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "config.yaml"
            )
        if yaml:
            try:
                with open(config_path) as f:
                    return yaml.safe_load(f)
            except Exception:
                pass
        # Fallback defaults
        return {
            "symbol": "XAUUSD", "lot": 0.01, "sl_points": 400,
            "tp_points": 600, "max_hold_bars": 36,
            "rsi": {"period": 14, "source": "close"},
            "execution": {"magic": 20260901, "deviation": 20, "mode": "live"},
        }

    def start(self, dry_run=False):
        if self._running:
            print("Engine already running.")
            return

        import MetaTrader5 as mt5
        if not mt5.initialize():
            print(f"MT5 init failed: {mt5.last_error()}")
            return False

        acct = mt5.account_info()
        if acct is None:
            print("No MT5 account")
            return False

        mode = "DRY-RUN" if dry_run else "LIVE"
        symbol = self.config.get("symbol", "XAUUSD")
        lot = self.config.get("lot", 0.01)
        tp = self.config.get("tp_points", 600)
        sl = self.config.get("sl_points", 400)

        self.brain = AutopilotBrain(
            symbol=symbol, lot=lot, sl_points=sl, tp_points=tp,
            max_hold_s=self.config.get("max_hold_bars", 36) * 300,
        )

        # Initialize AI brain from config
        ai_cfg = self.config.get("ai", {})
        if ai_cfg.get("enabled", False) and self.brain.ai_brain:
            provider = ai_cfg.get("provider", "anthropic")
            api_key = ai_cfg.get("api_key") or None
            model = ai_cfg.get("model")
            base_url = ai_cfg.get("base_url") or None
            self.brain.ai_brain.provider = provider
            if api_key:
                self.brain.ai_brain.api_key = api_key
            if model:
                self.brain.ai_brain.model = model
            if base_url:
                self.brain.ai_brain.base_url = base_url
            self.brain.ai_brain._min_interval = ai_cfg.get("min_interval_sec", 5)
            print(f"  AI Brain: {provider} ({self.brain.ai_brain.model})")
        else:
            print(f"  AI Brain: DISABLED (set ai.enabled=true in config.yaml to activate)")

        if dry_run:
            self.brain._open = lambda d: (print(f"[DRY] Would open {d}"), None)[1]
            self.brain._close = lambda t: (print(f"[DRY] Would close {t}"), None)[1]

        self.brain.init()
        self._running = True
        self._start_time = datetime.now(timezone.utc)

        os.makedirs(os.path.dirname(self._pid_file), exist_ok=True)
        with open(self._pid_file, "w") as f:
            f.write(str(os.getpid()))

        with open(self._log_file, "a") as f:
            f.write(f"[{self._start_time.isoformat()}] ENGINE START ({mode}) | "
                    f"Symbol={symbol} Lot={lot} TP={tp} SL={sl}\n")

        print(f"\n{'='*60}")
        print(f"  ARE ENGINE ALIVE -- {mode}")
        print(f"  Symbol: {symbol}")
        print(f"  Lot: {lot} | TP: {tp} pts | SL: {sl} pts")
        print(f"  Account: #{acct.login} | Balance: ${acct.balance:.2f}")
        print(f"  Strategy: RSI({self.config['rsi']['period']},{self.config['rsi']['source']})")
        print(f"  Layers: MACRO -> COMPASS -> MOMENTUM -> ENTRY")
        print(f"{'='*60}\n")

        self._thread = threading.Thread(target=self._heartbeat, daemon=True)
        self._thread.start()

        try:
            signal.signal(signal.SIGINT, self._handle_stop)
            signal.signal(signal.SIGTERM, self._handle_stop)
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
        finally:
            self.stop()

    def _heartbeat(self):
        import MetaTrader5 as mt5
        cycle = 0
        while self._running:
            try:
                tick = mt5.symbol_info_tick(self.config["symbol"])
                if tick is None:
                    time.sleep(1)
                    continue
                self._tick_count += 1
                sig = self.brain.on_tick(tick.bid, tick.ask, int(tick.time))
                cycle += 1
                if cycle % 120 == 0:
                    self._print_status_line()
                time.sleep(0.5)
            except Exception as e:
                with open(self._log_file, "a") as f:
                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] ERROR: {e}\n")
                time.sleep(2)

    def _print_status_line(self):
        if self.brain:
            s = self.brain.status()
            now = datetime.now(timezone.utc).strftime("%H:%M:%S")
            print(f"[{now}] Tick#{s['ticks']} Sig#{s['sigs']} "
                  f"Trades#{s['trades']} Pos={s['pos']} "
                  f"Bal=${s['bal']:.2f} Eq=${s['eq']:.2f}")

    def _handle_stop(self, sig, frame):
        print(f"\n[STOP] Signal {sig} received...")
        self.stop()

    def stop(self):
        self._running = False
        if self.brain:
            self.brain.status()
        try:
            os.remove(self._pid_file)
        except OSError:
            pass
        if self._start_time:
            duration = (datetime.now(timezone.utc) - self._start_time).total_seconds()
            with open(self._log_file, "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] ENGINE STOP "
                        f"(duration={duration:.0f}s ticks={self._tick_count})\n")
        try:
            import MetaTrader5 as mt5
            mt5.shutdown()
        except Exception:
            pass
        print("Engine STOPPED.")

    def status(self):
        if self.brain:
            s = self.brain.status()
            # Add AI/ML info
            if self.brain.ai_brain:
                s["ai"] = self.brain.ai_brain.get_stats()
            if self.brain.ml_trainer:
                s["ml"] = self.brain.ml_trainer.get_stats()
            return s
        return {"error": "Engine not started"}

    def is_running(self):
        return self._running

    def get_config(self):
        return self.config

    def update_config(self, **kwargs):
        self.config.update(kwargs)
        if self.brain:
            if "lot" in kwargs:
                self.brain.lot = kwargs["lot"]
            if "tp_points" in kwargs:
                self.brain.tp = kwargs["tp_points"]
            if "sl_points" in kwargs:
                self.brain.sl = kwargs["sl_points"]
            if "max_hold_bars" in kwargs:
                self.brain.max_hold = kwargs["max_hold_bars"] * 300

    def print_dashboard(self):
        """Print full dashboard -- works even when engine is stopped."""
        if self.brain:
            self.brain.print_dashboard()
            return

        import MetaTrader5 as mt5
        from .autopilot import TIMEFRAMES, compute_rsi

        if not mt5.initialize():
            print("MT5 not connected")
            return

        symbol = self.config.get("symbol", "XAUUSD")
        acct = mt5.account_info()
        tick = mt5.symbol_info_tick(symbol)

        print(f"\n{'='*70}")
        print(f"  ARE DASHBOARD -- {symbol} (Engine STOPPED)")
        print(f"{'='*70}")
        if acct:
            print(f"  Account: #{acct.login}  |  Balance: ${acct.balance:.2f}  |  Equity: ${acct.equity:.2f}")
        if tick:
            print(f"  Bid: {tick.bid:.2f}  |  Ask: {tick.ask:.2f}")
        print(f"{'-'*70}")
        print(f"  RSI(14,Close) -- ALL 7 TIMEFRAMES:")
        print(f"  {'TF':>4s}  {'RSI':>6s}  {'Zone':>8s}  {'Bar':>50s}  {'Layer':>10s}")
        print(f"  {'-'*66}")

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
                    zone = "BULL" if r > 50 else "BEAR" if r < 50 else "NEUTRAL"
                    layer = ("[MACRO]" if name in ("D1", "H4")
                             else "[COMPASS]" if name == "H1"
                             else "[MOMENTUM]" if name in ("M30", "M15")
                             else "[ENTRY]")
                    print(f"  {name:>4s}  {r:>6.1f}  {zone:>8s}  {bar:<50s}  {layer:>10s}")
                else:
                    print(f"  {name:>4s}    N/A")
            else:
                print(f"  {name:>4s}  (no data)")

        print(f"{'='*70}")
        print(f"  Config: lot={self.config.get('lot', 0.01)} "
              f"tp={self.config.get('tp_points', 600)} "
              f"sl={self.config.get('sl_points', 400)}")
        print(f"  AI Brain: {('AVAILABLE' if HAS_ANTHROPIC or HAS_OPENAI else 'SET API KEY to activate')}")
        print(f"  Start engine: python -m are.cli live start")
        print(f"{'='*70}\n")
        mt5.shutdown()
