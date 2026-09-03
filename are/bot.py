"""
ARE Trading Bot Daemon — Server-side auto-trading.

Runs as: python -m are.bot --style DAY --risk 1
Or: python are/bot.py --style DAY --risk 1

Reads decisions from the Next.js decision engine API.
Opens/closes positions via the MT5 bridge.
Persists state to data/bot_state_<style>.json.
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

# ─── EXCEPTIONS ──────────────────────────────────────────────────────────────

class BridgeError(Exception):
    """Base exception for MT5 bridge communication failures."""

class BridgeConnectionError(BridgeError):
    """Bridge is unreachable (connection refused, DNS, etc.)."""

class BridgeTimeoutError(BridgeError):
    """Bridge request timed out."""

class BridgeResponseError(BridgeError):
    """Bridge returned an error response (HTTP 500, invalid JSON, etc.)."""

class OrderRejected(Exception):
    """MT5 rejected the order (insufficient margin, invalid price, etc.)."""

# ─── PATHS ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOG_FILE = DATA_DIR / "bot_logs.jsonl"

# ─── DEFAULTS ─────────────────────────────────────────────────────────────────

DECISION_API = "http://localhost:4028/api/are/decision"
MT5_BRIDGE = "http://127.0.0.1:18888"
POLL_INTERVAL = 5  # seconds
COOLDOWN_SECONDS = 60  # jeda antar entri (multi-entry) — 1 menit
DAILY_LOSS_PCT = 5.0  # percent of starting balance

MIN_HOLD_SECONDS = {
    "micro": 300,       # 5 minutes
    "scalp": 600,       # 10 minutes
    "day": 1800,        # 30 minutes
    "swing": 3600,      # 1 hour
    "position": 7200,   # 2 hours
}

# Per-style minimum SL in points (enforced by bot when sending order)
MIN_SL_PER_STYLE = {
    "micro": 3,         # 3 points ($3) — tight for M1 scalping
    "scalp": 8,         # 8 points ($8) — moderate for M5
    "day": 20,          # 20 points ($20) — wide for H1 intraday
    "swing": 60,        # 60 points ($60) — wide for multi-day
    "position": 150,    # 150 points ($150) — very wide for long-term
}

# Per-style MT5 magic numbers for position ownership
MAGIC_NUMBERS = {
    "micro": 2001,
    "scalp": 2002,
    "day": 2003,
    "swing": 2004,
    "position": 2005,
}

# Maksimum posisi terbuka bersamaan per style (multi-entry).
# Scalp: 5 posisi — untuk uji akurasi metode. Style lain tetap 1.
MAX_POSITIONS = {
    "micro": 1,
    "scalp": 5,
    "day": 1,
    "swing": 1,
    "position": 1,
}

# ─── GLOBAL STATE ─────────────────────────────────────────────────────────────

running = True


def signal_handler(signum, frame):
    global running
    log("SHUTDOWN", f"Received signal {signum}")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ─── PATH HELPERS ─────────────────────────────────────────────────────────────

def get_state_file(style: str) -> Path:
    """Return per-style state file path."""
    return DATA_DIR / f"bot_state_{style}.json"

def get_pid_file(style: str) -> Path:
    """Return per-style PID file path."""
    return DATA_DIR / f"bot_{style}.pid"


def load_state(style: str) -> dict:
    try:
        with open(get_state_file(style)) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state: dict, style: str):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(get_state_file(style), "w") as f:
        json.dump(state, f, indent=2)


# ─── HTTP HELPERS (typed exceptions) ──────────────────────────────────────────

def http_get(url: str, timeout: int = 10) -> dict:
    """GET request. Returns parsed JSON. Raises BridgeError on failure."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        if isinstance(e.reason, TimeoutError):
            raise BridgeTimeoutError(f"Timeout: {url}") from e
        raise BridgeConnectionError(f"Connection failed: {url} — {e.reason}") from e
    except json.JSONDecodeError as e:
        raise BridgeResponseError(f"Invalid JSON from: {url}") from e
    except Exception as e:
        raise BridgeResponseError(f"Bridge error: {url} — {e}") from e


def http_post(url: str, data: dict, timeout: int = 10) -> dict:
    """POST request. Returns parsed JSON. Raises BridgeError on failure."""
    try:
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        if isinstance(e.reason, TimeoutError):
            raise BridgeTimeoutError(f"Timeout: {url}") from e
        raise BridgeConnectionError(f"Connection failed: {url} — {e.reason}") from e
    except json.JSONDecodeError as e:
        raise BridgeResponseError(f"Invalid JSON from: {url}") from e
    except Exception as e:
        raise BridgeResponseError(f"Bridge error: {url} — {e}") from e


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


# ─── PROCESS LOCK (single instance per style) ─────────────────────────────────

def is_process_alive(pid: int) -> bool:
    """Check if a process is alive (works on Windows via os.kill(pid, 0))."""
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def acquire_single_instance_lock(style: str) -> bool:
    """
    Ensure only ONE bot process runs per style.
    Returns True if this process owns the style, False if another bot is alive.
    """
    pid_file = get_pid_file(style)
    if pid_file.exists():
        try:
            old_pid = int(pid_file.read_text().strip() or 0)
        except ValueError:
            old_pid = 0
        if old_pid and old_pid != os.getpid() and is_process_alive(old_pid):
            log("ALREADY_RUNNING", f"Bot [{style}] already running (PID {old_pid}) — refusing duplicate instance")
            return False
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()))
    return True


# ─── MT5 BRIDGE WRAPPERS (fail-closed) ────────────────────────────────────────

def get_positions(symbol: str = "XAUUSD") -> list:
    """Get open positions from MT5. Raises BridgeError on failure."""
    data = http_get(f"{MT5_BRIDGE}/positions")
    if not data or not data.get("connected"):
        raise BridgeError("MT5 positions unavailable")
    return data.get("positions", [])


def get_account() -> dict:
    """Get account data from MT5. Raises BridgeError on failure."""
    data = http_get(f"{MT5_BRIDGE}/account")
    if not data or not data.get("connected"):
        raise BridgeError("MT5 account unavailable")
    # Bridge returns flat JSON: { connected, balance, equity, ... }
    return data.get("account", data)


def open_position(symbol: str, direction: str, lot: float, sl_points: float,
                  tp_points: float, magic: int, comment: str) -> dict:
    """Open position via MT5 bridge. Raises BridgeError or OrderRejected."""
    result = http_post(f"{MT5_BRIDGE}/order", {
        "symbol": symbol,
        "direction": direction,
        "lot": lot,
        "sl_points": sl_points,
        "tp_points": tp_points,
        "magic": magic,
        "comment": comment,
    })
    if not result:
        raise BridgeError("Order: no response from bridge")
    if not result.get("success"):
        raise OrderRejected(result.get("error", "order rejected"))
    return result


def close_position(ticket: int) -> dict:
    """Close position via MT5 bridge. Raises BridgeError on failure."""
    result = http_post(f"{MT5_BRIDGE}/close", {"ticket": ticket})
    if not result:
        raise BridgeError(f"Close #{ticket}: no response from bridge")
    if not result.get("success"):
        raise OrderRejected(result.get("error", f"close #{ticket} rejected"))
    return result


def get_decision(symbol: str, style: str, risk: float) -> dict:
    """Get trading decision from engine. Raises BridgeError on failure."""
    data = http_get(f"{DECISION_API}?symbol={symbol}&style={style}&risk={risk}", timeout=30)
    if not data or not data.get("success"):
        raise BridgeError("Decision engine unavailable")
    return data


def modify_position(ticket: int, sl: float = None, tp: float = None) -> dict:
    """Modify SL/TP on existing position. Raises BridgeError on failure."""
    result = http_post(f"{MT5_BRIDGE}/modify", {"ticket": ticket, "sl": sl, "tp": tp})
    if not result:
        raise BridgeError(f"Modify #{ticket}: no response from bridge")
    if not result.get("success"):
        # Position might have been closed — not an error, just stale
        raise BridgeError(f"Modify #{ticket} failed: {result.get('error', 'unknown')}")
    return result


def get_candles(symbol: str, timeframe: str, count: int = 200) -> list:
    """Get candle data from MT5. Raises BridgeError on failure."""
    data = http_get(f"{MT5_BRIDGE}/candles?symbol={symbol}&timeframe={timeframe}&count={count}", timeout=15)
    if not data or not data.get("connected"):
        raise BridgeError(f"Candles unavailable for {symbol} {timeframe}")
    return data.get("candles", [])


# ─── POSITION RECONCILIATION (multi-entry aware) ──────────────────────────────

def my_positions_from(positions: list, style: str, symbol: str) -> list:
    """All broker positions owned by this bot style (magic + comment prefix)."""
    magic = MAGIC_NUMBERS.get(style, 0)
    prefix = f"ARE-{style.upper()}"
    return [p for p in positions
            if p.get("symbol") == symbol
            and p.get("magic", 0) == magic
            and p.get("comment", "").startswith(prefix)]


def pos_to_record(p: dict) -> dict:
    """Convert a broker position dict to a tracked-state record."""
    return {
        "ticket": p.get("ticket"),
        "direction": p.get("type"),
        "entry": p.get("price_open", 0),
        "lot": p.get("volume", 0),
        "sl": p.get("sl", 0),
        "tp": p.get("tp", 0),
        "opened_at": time.time(),  # unknown for adopted positions — conservative
        "last_pnl": p.get("profit", 0),
    }


def reconcile_positions(state: dict, positions: list, style: str, symbol: str):
    """
    Reconcile tracked positions with broker truth (multi-position).

    Returns (open_records, closed_list):
      open_records — records still open at the broker (kept in state["positions"])
      closed_list  — tracked records no longer at the broker (closed by TP/SL
                     or externally) with their last known P&L.
    """
    broker = my_positions_from(positions, style, symbol)
    broker_by_ticket = {p["ticket"]: p for p in broker}

    tracked = state.get("positions") or []
    open_records: list = []
    closed_list: list = []
    seen = set()

    for rec in tracked:
        ticket = rec.get("ticket")
        bp = broker_by_ticket.get(ticket)
        if bp is None:
            # Gone from broker — TP/SL hit or closed externally.
            closed_list.append({
                "ticket": ticket,
                "direction": rec.get("direction"),
                "entry": rec.get("entry", 0),
                "exit": 0,
                "lot": rec.get("lot", 0),
                "pnl": rec.get("last_pnl", 0),
            })
            continue
        # Still open — refresh live fields.
        rec["entry"] = bp.get("price_open", rec.get("entry", 0))
        rec["lot"] = bp.get("volume", rec.get("lot", 0))
        rec["sl"] = bp.get("sl", rec.get("sl", 0))
        rec["tp"] = bp.get("tp", rec.get("tp", 0))
        rec["last_pnl"] = bp.get("profit", rec.get("last_pnl", 0))
        open_records.append(rec)
        seen.add(ticket)

    # Adopt broker positions not yet tracked (bot restarted while holding,
    # or opened externally with our magic).
    for p in broker:
        if p["ticket"] not in seen:
            rec = pos_to_record(p)
            log("ADOPT", f"#{rec['ticket']} {rec['direction']} {rec['lot']} lots (untracked)")
            open_records.append(rec)

    state["positions"] = open_records

    # Backward-compatible single-position mirrors.
    if open_records:
        last = open_records[-1]
        state["active_ticket"] = last["ticket"]
        state["active_direction"] = last["direction"]
        state["last_known_pnl"] = last["last_pnl"]
    else:
        state["active_ticket"] = None
        state["active_direction"] = None
        state["last_known_pnl"] = 0.0

    return open_records, closed_list


def record_closed_trade(state: dict, ticket, direction, entry, exit_, lot, pnl, reason):
    """Update counters + history for a closed position."""
    state["daily_pnl"] += pnl
    state["trade_count"] += 1
    state.setdefault("trade_history", []).append({
        "ticket": ticket,
        "direction": direction,
        "entry": entry,
        "exit": exit_,
        "lot": lot,
        "pnl": round(pnl, 2),
        "close_reason": reason,
        "closed_at": datetime.now(timezone.utc).isoformat(),
    })
    state["last_trade_at"] = time.time()


# ─── TRAILING STOP ────────────────────────────────────────────────────────────

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
    return sum(trs[-period:]) / period


def _try_trailing_stop(pos: dict, atr_multiplier: float, state: dict, symbol: str):
    """Move SL if price has moved favorably beyond ATR trailing distance."""
    ticket = pos["ticket"]
    direction = pos["type"]
    entry = pos["price_open"]
    current_sl = pos["sl"]

    try:
        candles = get_candles(symbol, "M15", 50)
    except BridgeError:
        return

    if len(candles) < 20:
        return

    atr_val = compute_atr(candles)
    if atr_val <= 0:
        return

    trailing_distance = atr_val * atr_multiplier
    current_price = candles[-1]["close"]

    new_sl = None
    if direction == "BUY":
        candidate = round(current_price - trailing_distance, 2)
        if candidate > current_sl and candidate > entry:
            new_sl = candidate
    else:
        candidate = round(current_price + trailing_distance, 2)
        if candidate < current_sl and candidate < entry:
            new_sl = candidate

    if new_sl is not None:
        try:
            modify_position(ticket, sl=new_sl)
            state["last_trailing_sl"] = new_sl
            state["last_atr"] = round(atr_val, 2)
            log("TRAILING", f"#{ticket} SL {current_sl} -> {new_sl} (ATR={atr_val:.1f})")
        except (BridgeError, OrderRejected) as e:
            log("TRAILING_FAILED", f"#{ticket}: {e}")


# ─── MAIN BOT LOOP ───────────────────────────────────────────────────────────

def run_bot(symbol: str, style: str, risk: float, max_daily_loss: float, trailing_atr: float = 0):
    global running

    magic = MAGIC_NUMBERS.get(style, 0)
    pid_file = get_pid_file(style)

    # Single-instance lock: refuse to run if another bot for this style is alive.
    if not acquire_single_instance_lock(style):
        log("EXIT", f"Duplicate bot for style={style} — exiting")
        return

    log("START", f"symbol={symbol} style={style} risk={risk}% magic={magic} trailing_atr={trailing_atr}x")

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
            "magic": magic,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "active_ticket": None,
            "active_direction": None,
            "positions": [],
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

    # Get starting balance (fail-closed)
    try:
        account = get_account()
        state["starting_balance"] = account.get("balance", 0)
    except BridgeError as e:
        log("INIT_FAILED", f"Cannot read account: {e}")
        state["status"] = "error"
        save_state(state, style)
        return

    state["pid"] = os.getpid()
    save_state(state, style)
    log("INIT", f"Balance: ${state['starting_balance']:.2f}, PID: {os.getpid()}, Magic: {magic}")

    while running:
        try:
            # 0. Check for style change from UI
            current_state = load_state(style)
            new_style = current_state.get("pending_style")
            if new_style and new_style != style:
                log("STYLE_CHANGE", f"{style} -> {new_style}")
                # Close all positions of this style before switching
                for rec in list(state.get("positions") or []):
                    try:
                        close_position(rec["ticket"])
                        log("CLOSED", f"#{rec['ticket']} closed for style switch")
                    except (BridgeError, OrderRejected) as e:
                        log("CLOSE_FAILED", f"Style switch #{rec['ticket']}: {e}")
                style = new_style
                magic = MAGIC_NUMBERS.get(style, 0)
                state["style"] = style
                state["magic"] = magic
                state["positions"] = []
                state["active_ticket"] = None
                state["active_direction"] = None
                state["pending_style"] = None
                save_state(state, style)

            # 1. Get decision
            dec = get_decision(symbol, style, risk)

            # 1b. Persist the latest decision snapshot so the UI can show
            #     per-timeframe votes without polling the engine again.
            state["last_decision"] = {
                "decision": dec.get("decision"),
                "decisionReason": dec.get("decisionReason"),
                "finalSignal": dec.get("finalSignal"),
                "totalConfirmations": dec.get("totalConfirmations", 0),
                "minRequired": dec.get("minRequired", 0),
                "mtfConfirmed": dec.get("mtfConfirmed", False),
                "inSession": dec.get("inSession", False),
                "dataFresh": dec.get("dataFresh", True),
                "rr": dec.get("rr", 0),
                "slPoints": dec.get("slPoints", 0),
                "tpPoints": dec.get("tpPoints", 0),
                "lotSize": dec.get("lotSize", 0),
                "timeframeSignals": dec.get("timeframeSignals") or {},
            }

            # 2. Get positions from broker (fail-closed)
            positions = get_positions(symbol)

            # 3. Reconcile local state with broker (multi-position)
            open_pos, closed_list = reconcile_positions(state, positions, style, symbol)

            # 3b. Positions that vanished → TP/SL hit or external close
            for c in closed_list:
                record_closed_trade(state, c["ticket"], c["direction"], c["entry"], c["exit"],
                                    c["lot"], c["pnl"], "tp_sl")
                log("TP_SL", f"Position #{c['ticket']} closed P&L: ${c['pnl']:.2f}")

            # 4. Manage each open position: trailing stop + reversal exit
            remaining: list = []
            broker_map = {p["ticket"]: p for p in my_positions_from(positions, style, symbol)}
            for rec in open_pos:
                p = broker_map.get(rec["ticket"])
                if p is None:
                    continue  # vanished mid-cycle — next poll records it
                pnl = p.get("profit", 0)
                rec["last_pnl"] = pnl

                if trailing_atr > 0:
                    _try_trailing_stop(p, trailing_atr, state, symbol)

                # Reversal exit (per position, respect per-position minimum hold)
                if (dec["decision"] != "WAIT"
                        and dec["finalSignal"] != rec["direction"]
                        and dec["mtfConfirmed"]):
                    hold_time = time.time() - rec.get("opened_at", time.time())
                    min_hold = MIN_HOLD_SECONDS.get(style, 300)
                    if hold_time < min_hold:
                        if int(hold_time) % 60 == 0:
                            log("HOLD", f"#{rec['ticket']} reversal blocked — held {int(hold_time)}s, min {min_hold}s")
                        remaining.append(rec)
                        continue
                    log("REVERSAL", f"#{rec['ticket']} {rec['direction']} -> {dec['finalSignal']}")
                    try:
                        close_position(rec["ticket"])
                        record_closed_trade(state, rec["ticket"], rec["direction"],
                                            rec.get("entry", 0), p.get("price_current", 0),
                                            rec.get("lot", 0), pnl, "reversal")
                        log("CLOSED", f"#{rec['ticket']} P&L: ${pnl:.2f}")
                    except (BridgeError, OrderRejected) as e:
                        log("CLOSE_FAILED", f"#{rec['ticket']}: {e}")
                        remaining.append(rec)
                else:
                    remaining.append(rec)

            state["positions"] = remaining
            state["active_ticket"] = remaining[-1]["ticket"] if remaining else None
            state["active_direction"] = remaining[-1]["direction"] if remaining else None
            state["last_known_pnl"] = remaining[-1]["last_pnl"] if remaining else 0.0

            # 5. ENTRY — only if slots remain for this style (multi-entry)
            if len(remaining) < MAX_POSITIONS.get(style, 1):
                # Cooldown between trade actions (entry/exit) — 1 menit
                if not (state.get("last_trade_at")
                        and (time.time() - state["last_trade_at"]) < COOLDOWN_SECONDS):
                    # Daily loss circuit breaker
                    try:
                        account = get_account()
                        current_balance = account.get("balance", state["starting_balance"])
                    except BridgeError:
                        current_balance = state["starting_balance"]

                    if state["starting_balance"] > 0:
                        realized_loss = state["starting_balance"] - current_balance
                        loss_pct = (realized_loss / state["starting_balance"]) * 100
                        if loss_pct >= max_daily_loss:
                            log("CIRCUIT_BREAKER", f"Balance dropped {loss_pct:.1f}% — stopping")
                            state["status"] = "circuit_breaker"
                            save_state(state, style)
                            break

                    # Check entry conditions
                    if (dec["decision"] != "WAIT"
                            and dec["mtfConfirmed"]
                            and dec["inSession"]
                            and dec["rr"] >= 1.5
                            and dec["lotSize"] >= 0.01):
                        style_min_sl = MIN_SL_PER_STYLE.get(style, 5)
                        sl_pts = max(dec["slPoints"], style_min_sl)
                        tp_pts = max(dec["tpPoints"], style_min_sl)
                        log("ENTRY", f"{dec['decision']} lot={dec['lotSize']} sl={sl_pts} tp={tp_pts} R:R={dec['rr']}")
                        try:
                            result = open_position(
                                symbol, dec["decision"], dec["lotSize"],
                                sl_pts, tp_pts, magic, f"ARE-{style.upper()}",
                            )
                            new_rec = {
                                "ticket": result.get("ticket"),
                                "direction": dec["decision"],
                                "entry": result.get("price", dec.get("entry", 0)),
                                "lot": dec["lotSize"],
                                "sl": sl_pts, "tp": tp_pts,
                                "opened_at": time.time(),
                                "last_pnl": 0.0,
                            }
                            state["positions"].append(new_rec)
                            state["active_ticket"] = new_rec["ticket"]
                            state["active_direction"] = dec["decision"]
                            state["last_trade_at"] = time.time()
                            log("OPENED", f"#{result['ticket']} {dec['decision']} {dec['lotSize']} lots (magic={magic})")
                        except OrderRejected as e:
                            log("OPEN_FAILED", f"{e}")
                            state["last_trade_at"] = time.time()
                        except BridgeError as e:
                            log("OPEN_FAILED", f"Bridge: {e}")
                            state["last_trade_at"] = time.time()

            save_state(state, style)

        except BridgeError as e:
            log("BRIDGE_ERROR", str(e))
        except Exception as e:
            log("ERROR", str(e))

        time.sleep(POLL_INTERVAL)

    # Cleanup
    state["status"] = "stopped"
    state["pid"] = None
    save_state(state, style)
    pid_file.unlink(missing_ok=True)
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
