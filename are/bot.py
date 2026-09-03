"""
ARE Trading Bot Daemon — Server-side auto-trading.

Runs as: python -m are.bot --style DAY --risk 1
Or: python are/bot.py --style DAY --risk 1

Reads decisions from the Next.js decision engine API.
Opens/closes positions via the MT5 bridge.
Persists state to data/bot_state.json.
Logs to data/bot_logs.jsonl.

Handles SIGINT/SIGTERM for graceful shutdown.
"""

import argparse
import json
import os
import signal
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ─── PATHS ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATE_FILE = DATA_DIR / "bot_state.json"  # default, overridden per style
LOG_FILE = DATA_DIR / "bot_logs.jsonl"
PID_FILE = DATA_DIR / "bot.pid"

# ─── DEFAULTS ─────────────────────────────────────────────────────────────────

DECISION_API = "http://localhost:4028/api/are/decision"
MT5_BRIDGE = "http://127.0.0.1:18888"
POLL_INTERVAL = 5  # seconds
COOLDOWN_SECONDS = 30
DAILY_LOSS_PCT = 5.0  # percent of starting balance

MIN_HOLD_SECONDS = {
    "micro": 300,       # 5 minutes
    "scalp": 600,       # 10 minutes
    "day": 1800,        # 30 minutes
    "swing": 3600,      # 1 hour
    "position": 7200,   # 2 hours
}

# ─── GLOBAL STATE ─────────────────────────────────────────────────────────────

running = True


def signal_handler(signum, frame):
    global running
    log("SHUTDOWN", f"Received signal {signum}")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ─── HTTP HELPERS ─────────────────────────────────────────────────────────────

def http_get(url: str, timeout: int = 10) -> dict | None:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def http_post(url: str, data: dict, timeout: int = 10) -> dict | None:
    try:
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


# ─── LOGGING ──────────────────────────────────────────────────────────────────

def log(action: str, details: str = ""):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "details": details,
    }
    line = json.dumps(entry)
    print(f"[{entry['timestamp'][:19]}] {action}: {details}", flush=True)
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ─── STATE PERSISTENCE ───────────────────────────────────────────────────────

def get_state_file(style: str = "day") -> Path:
    """Return per-style state file path."""
    return DATA_DIR / f"bot_state_{style}.json"

def load_state(style: str = "day") -> dict:
    try:
        with open(get_state_file(style)) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state: dict, style: str = "day"):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(get_state_file(style), "w") as f:
        json.dump(state, f, indent=2)


def get_positions() -> list:
    data = http_get(f"{MT5_BRIDGE}/positions")
    return data.get("positions", []) if data else []


def get_account() -> dict:
    data = http_get(f"{MT5_BRIDGE}/account")
    # Bridge returns flat JSON: { connected, balance, equity, ... }
    if not data:
        return {}
    # If nested under 'account' key, use it; otherwise use top-level
    return data.get("account", data)


def open_position(direction: str, lot: float, sl_points: float, tp_points: float, comment: str) -> dict | None:
    return http_post(f"{MT5_BRIDGE}/order", {
        "symbol": "XAUUSD",
        "direction": direction,
        "lot": lot,
        "sl_points": sl_points,
        "tp_points": tp_points,
        "comment": comment,
    })


def close_position(ticket: int) -> dict | None:
    return http_post(f"{MT5_BRIDGE}/close", {"ticket": ticket})


def get_decision(symbol: str, style: str, risk: float) -> dict | None:
    return http_get(f"{DECISION_API}?symbol={symbol}&style={style}&risk={risk}", timeout=30)


def modify_position(ticket: int, sl: float = None, tp: float = None) -> dict | None:
    return http_post(f"{MT5_BRIDGE}/modify", {"ticket": ticket, "sl": sl, "tp": tp})


def get_candles(symbol: str, timeframe: str, count: int = 200) -> list:
    data = http_get(f"{MT5_BRIDGE}/candles?symbol={symbol}&timeframe={timeframe}&count={count}", timeout=15)
    return data.get("candles", []) if data else []# ─── TRAILING STOP ──────────────────────────────────────────────────────────

def compute_atr(candles: list, period: int = 14) -> float:
    """Compute ATR from candle data. Returns last ATR value."""
    if len(candles) < period + 1:
        return 0
    trs = []
    for i in range(1, len(candles)):
        h = candles[i]["high"]
        l = candles[i]["low"]
        pc = candles[i - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    if len(trs) < period:
        return 0
    # Simple moving average of TR
    atr_val = sum(trs[-period:]) / period
    return atr_val


def _try_trailing_stop(pos: dict, atr_multiplier: float, state: dict):
    """Move SL if price has moved favorably beyond ATR trailing distance."""
    ticket = pos["ticket"]
    direction = pos["type"]  # 'BUY' or 'SELL'
    entry = pos["price_open"]
    current_sl = pos["sl"]
    current_tp = pos["tp"]

    # Fetch candles for ATR computation
    candles = get_candles(pos["symbol"], "M15", 50)
    if len(candles) < 20:
        return

    atr_val = compute_atr(candles)
    if atr_val <= 0:
        return

    trailing_distance = atr_val * atr_multiplier
    current_price = candles[-1]["close"]

    new_sl = None
    if direction == "BUY":
        # For BUY: SL moves UP. New SL = current price - trailing distance.
        # Only move if new SL is higher than current SL (and above entry).
        candidate = round(current_price - trailing_distance, 2)
        if candidate > current_sl and candidate > entry:
            new_sl = candidate
    else:
        # For SELL: SL moves DOWN. New SL = current price + trailing distance.
        # Only move if new SL is lower than current SL (and below entry).
        candidate = round(current_price + trailing_distance, 2)
        if candidate < current_sl and candidate < entry:
            new_sl = candidate

    if new_sl is not None:
        result = modify_position(ticket, sl=new_sl)
        if result and result.get("success"):
            old_sl = state.get("last_trailing_sl")
            state["last_trailing_sl"] = new_sl
            state["last_atr"] = round(atr_val, 2)
            log("TRAILING", f"#{ticket} SL {current_sl} -> {new_sl} (ATR={atr_val:.1f}, dist={trailing_distance:.1f})")


# ─── MAIN BOT LOOP ───────────────────────────────────────────────────────────
def run_bot(symbol: str, style: str, risk: float, max_daily_loss: float, trailing_atr: float = 0):
    global running

    log("START", f"symbol={symbol} style={style} risk={risk}% max_daily_loss={max_daily_loss}% trailing_atr={trailing_atr}x")

    # Write PID
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))

    # Load or initialize state
    state = load_state(style)
    if state.get("status") == "running":
        log("ALREADY_RUNNING", f"Bot already running (PID {state.get('pid')}). Taking over.")
    else:
        state = {
            "status": "running",
            "pid": os.getpid(),
            "symbol": symbol,
            "style": style,
            "risk": risk,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "active_ticket": None,
            "active_direction": None,
            "trade_count": 0,
            "daily_pnl": 0.0,
            "starting_balance": 0.0,
            "last_trade_at": None,
            "trailing_atr": trailing_atr,
            "last_trailing_sl": None,
            "last_atr": None,
            "last_known_pnl": 0.0,
            "trade_history": [],
        }

    # Get starting balance
    account = get_account()
    state["starting_balance"] = account.get("balance", 0)
    state["pid"] = os.getpid()
    save_state(state, style)

    log("INIT", f"Balance: ${state['starting_balance']:.2f}, PID: {os.getpid()}")

    while running:
        try:
            # 1. Get decision
            dec = get_decision(symbol, style, risk)
            if not dec or not dec.get("success"):
                log("ERROR", "Decision engine unavailable")
                time.sleep(POLL_INTERVAL)
                continue

            # 2. Check existing position
            positions = get_positions()
            my_pos = next((p for p in positions if p.get("comment", "").startswith(f"ARE-{style.upper()}")), None)

            if my_pos:
                # ── HOLDING ──
                ticket = my_pos["ticket"]
                direction = my_pos["type"]
                pnl = my_pos.get("profit", 0)

                if state["active_ticket"] != ticket:
                    state["active_ticket"] = ticket
                    state["active_direction"] = direction
                    log("HOLDING", f"#{ticket} {direction} P&L: ${pnl:.2f}")
                # Always track latest P&L for circuit breaker on TP/SL close
                state["last_known_pnl"] = pnl

                # Trailing stop: move SL in favor of the trade
                if trailing_atr > 0:
                    _try_trailing_stop(my_pos, trailing_atr, state)

                # Check if signal reversed (with minimum hold time)
                if (dec["decision"] != "WAIT"
                        and dec["finalSignal"] != direction
                        and dec["mtfConfirmed"]):
                    hold_time = time.time() - state.get("last_trade_at", time.time())
                    min_hold = MIN_HOLD_SECONDS.get(style, 300)
                    if hold_time < min_hold:
                        # Too early to reverse — wait
                        if int(hold_time) % 60 == 0:  # log every minute
                            log("HOLD", f"Reversal blocked — held {int(hold_time)}s, min {min_hold}s")
                    else:
                        log("REVERSAL", f"Signal reversed {direction} -> {dec['finalSignal']} (held {int(hold_time)}s)")
                        result = close_position(ticket)
                        if result and result.get("success"):
                            state["daily_pnl"] += pnl
                            state["trade_count"] += 1
                            state["active_ticket"] = None
                            state["active_direction"] = None
                            state["last_trade_at"] = time.time()
                            state.setdefault("trade_history", []).append({
                                "ticket": ticket, "direction": direction,
                                "entry": my_pos.get("price_open", 0), "exit": my_pos.get("price_current", 0),
                                "lot": my_pos.get("volume", 0), "pnl": round(pnl, 2),
                                "close_reason": "reversal",
                                "closed_at": datetime.now(timezone.utc).isoformat(),
                            })
                            log("CLOSED", f"#{ticket} P&L: ${pnl:.2f} daily: ${state['daily_pnl']:.2f}")
                        else:
                            log("CLOSE_FAILED", f"#{ticket}: {result}")

            else:
                # ── MONITORING ──
                if state["active_ticket"] is not None:
                    # Position was closed (TP/SL hit)
                    # Capture P&L from last known state before it disappears
                    last_pnl = state.get("last_known_pnl", 0)
                    state["daily_pnl"] += last_pnl
                    state["trade_count"] += 1
                    # Record trade history
                    state.setdefault("trade_history", []).append({
                        "ticket": state["active_ticket"], "direction": state["active_direction"],
                        "entry": 0, "exit": 0,
                        "lot": 0, "pnl": round(last_pnl, 2),
                        "close_reason": "tp_sl",
                        "closed_at": datetime.now(timezone.utc).isoformat(),
                    })
                    log("TP_SL", f"Position #{state['active_ticket']} closed (TP/SL hit) P&L: ${last_pnl:.2f} daily: ${state['daily_pnl']:.2f}")
                    state["active_ticket"] = None
                    state["active_direction"] = None
                    state["last_trade_at"] = time.time()

                # Check cooldown
                if state["last_trade_at"] and (time.time() - state["last_trade_at"]) < COOLDOWN_SECONDS:
                    time.sleep(POLL_INTERVAL)
                    continue

                # Check daily loss circuit breaker (balance-based = most reliable)
                account = get_account()
                current_balance = account.get("balance", state["starting_balance"])
                if state["starting_balance"] > 0:
                    # Realized loss = how much balance dropped from start
                    realized_loss = state["starting_balance"] - current_balance
                    loss_pct = (realized_loss / state["starting_balance"]) * 100
                    if loss_pct >= max_daily_loss:
                        log("CIRCUIT_BREAKER", f"Balance dropped {loss_pct:.1f}% (${realized_loss:.2f}) >= {max_daily_loss}% — stopping")
                        state["status"] = "circuit_breaker"
                        save_state(state, style)
                        break

                # Check entry conditions
                if (dec["decision"] != "WAIT"
                        and dec["mtfConfirmed"]
                        and dec["inSession"]
                        and dec["rr"] >= 1.5
                        and dec["lotSize"] >= 0.01):
                    # Enforce minimum SL (must be > 2x spread = 10 points for XAUUSD)
                    MIN_SL = 10
                    sl_pts = max(dec["slPoints"], MIN_SL)
                    tp_pts = max(dec["tpPoints"], MIN_SL)
                    log("ENTRY", f"{dec['decision']} lot={dec['lotSize']} sl={sl_pts} tp={tp_pts} R:R={dec['rr']}")
                    result = open_position(
                        dec["decision"],
                        dec["lotSize"],
                        sl_pts,
                        tp_pts,
                        f"ARE-{style.upper()}",
                    )
                    if result and result.get("success"):
                        state["active_ticket"] = result.get("ticket")
                        state["active_direction"] = dec["decision"]
                        state["last_trade_at"] = time.time()
                        log("OPENED", f"#{result['ticket']} {dec['decision']} {dec['lotSize']} lots")
                    else:
                        err = result.get("error", result.get("message", "unknown")) if result else "no response"
                        log("OPEN_FAILED", err)
                        state["last_trade_at"] = time.time()  # cooldown after failure

            save_state(state, style)

        except Exception as e:
            log("ERROR", str(e))

        time.sleep(POLL_INTERVAL)

    # Cleanup
    state["status"] = "stopped"
    state["pid"] = None
    save_state(state, style)
    PID_FILE.unlink(missing_ok=True)
    log("STOPPED", f"Final P&L: ${state['daily_pnl']:.2f}, Trades: {state['trade_count']}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ARE Trading Bot Daemon")
    parser.add_argument("--symbol", default="XAUUSD", help="Trading symbol (default: XAUUSD)")
    parser.add_argument("--style", default="day", choices=["micro", "scalp", "day", "swing", "position"],
                        help="Trading style (default: day)")
    parser.add_argument("--risk", type=float, default=1.0, help="Risk percent per trade (default: 1)")
    parser.add_argument("--max-daily-loss", type=float, default=DAILY_LOSS_PCT,
                        help=f"Max daily loss %% of balance (default: {DAILY_LOSS_PCT})")
    parser.add_argument("--trailing-atr", type=float, default=0,
                        help="Trailing stop as ATR multiplier (0=disabled, 1.5=recommended)")
    args = parser.parse_args()

    run_bot(args.symbol, args.style, args.risk, args.max_daily_loss, args.trailing_atr)


if __name__ == "__main__":
    main()
