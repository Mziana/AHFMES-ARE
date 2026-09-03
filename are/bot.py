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
STATE_FILE = DATA_DIR / "bot_state.json"
LOG_FILE = DATA_DIR / "bot_logs.jsonl"
PID_FILE = DATA_DIR / "bot.pid"

# ─── DEFAULTS ─────────────────────────────────────────────────────────────────

DECISION_API = "http://localhost:4028/api/are/decision"
MT5_BRIDGE = "http://127.0.0.1:18888"
POLL_INTERVAL = 5  # seconds
COOLDOWN_SECONDS = 30
DAILY_LOSS_PCT = 5.0  # percent of starting balance

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

def load_state() -> dict:
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_positions() -> list:
    data = http_get(f"{MT5_BRIDGE}/positions")
    return data.get("positions", []) if data else []


def get_account() -> dict:
    data = http_get(f"{MT5_BRIDGE}/account")
    return data.get("account", {}) if data else {}


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


# ─── MAIN BOT LOOP ───────────────────────────────────────────────────────────

def run_bot(symbol: str, style: str, risk: float, max_daily_loss: float):
    global running

    log("START", f"symbol={symbol} style={style} risk={risk}% max_daily_loss={max_daily_loss}%")

    # Write PID
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))

    # Load or initialize state
    state = load_state()
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
        }

    # Get starting balance
    account = get_account()
    state["starting_balance"] = account.get("balance", 0)
    state["pid"] = os.getpid()
    save_state(state)

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
            my_pos = next((p for p in positions if p.get("comment", "").startswith("ARE-")), None)

            if my_pos:
                # ── HOLDING ──
                ticket = my_pos["ticket"]
                direction = my_pos["type"]
                pnl = my_pos.get("profit", 0)

                if state["active_ticket"] != ticket:
                    state["active_ticket"] = ticket
                    state["active_direction"] = direction
                    log("HOLDING", f"#{ticket} {direction} P&L: ${pnl:.2f}")

                # Check if signal reversed
                if (dec["decision"] != "WAIT"
                        and dec["finalSignal"] != direction
                        and dec["mtfConfirmed"]):
                    log("REVERSAL", f"Signal reversed {direction} -> {dec['finalSignal']}")
                    result = close_position(ticket)
                    if result and result.get("success"):
                        state["daily_pnl"] += pnl
                        state["trade_count"] += 1
                        state["active_ticket"] = None
                        state["active_direction"] = None
                        state["last_trade_at"] = time.time()
                        log("CLOSED", f"#{ticket} P&L: ${pnl:.2f} daily: ${state['daily_pnl']:.2f}")
                    else:
                        log("CLOSE_FAILED", f"#{ticket}: {result}")

            else:
                # ── MONITORING ──
                if state["active_ticket"] is not None:
                    # Position was closed (TP/SL hit)
                    state["trade_count"] += 1
                    log("TP_SL", f"Position #{state['active_ticket']} closed (TP/SL hit)")
                    state["active_ticket"] = None
                    state["active_direction"] = None
                    state["last_trade_at"] = time.time()

                # Check cooldown
                if state["last_trade_at"] and (time.time() - state["last_trade_at"]) < COOLDOWN_SECONDS:
                    time.sleep(POLL_INTERVAL)
                    continue

                # Check daily loss circuit breaker
                balance = get_account().get("balance", state["starting_balance"])
                if state["starting_balance"] > 0:
                    loss_pct = abs(min(0, state["daily_pnl"])) / state["starting_balance"] * 100
                    if loss_pct >= max_daily_loss:
                        log("CIRCUIT_BREAKER", f"Daily loss {loss_pct:.1f}% >= {max_daily_loss}% — stopping")
                        state["status"] = "circuit_breaker"
                        save_state(state)
                        break

                # Check entry conditions
                if (dec["decision"] != "WAIT"
                        and dec["mtfConfirmed"]
                        and dec["inSession"]
                        and dec["rr"] >= 1.5
                        and dec["lotSize"] >= 0.01):
                    log("ENTRY", f"{dec['decision']} lot={dec['lotSize']} R:R={dec['rr']}")
                    result = open_position(
                        dec["decision"],
                        dec["lotSize"],
                        dec["slPoints"],
                        dec["tpPoints"],
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

            save_state(state)

        except Exception as e:
            log("ERROR", str(e))

        time.sleep(POLL_INTERVAL)

    # Cleanup
    state["status"] = "stopped"
    state["pid"] = None
    save_state(state)
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
    args = parser.parse_args()

    run_bot(args.symbol, args.style, args.risk, args.max_daily_loss)


if __name__ == "__main__":
    main()
