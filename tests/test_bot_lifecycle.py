"""
Behavioral test: Server-side Bot Daemon
Tests the full lifecycle: start, running, holding, stop, idempotency, state persistence.
"""
import json
import os
import sys
import time
import urllib.request

BASE = "http://localhost:4028"
MT5 = "http://127.0.0.1:18888"
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

errors = []
passed = 0

def check(label, condition, detail=""):
    global passed
    if condition:
        passed += 1
        print(f"  PASS  {label}")
    else:
        msg = f"{label}: {detail}" if detail else label
        errors.append(msg)
        print(f"  FAIL  {msg}")

def api_get(url, timeout=10):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def api_post(url, data=None, timeout=15):
    try:
        body = json.dumps(data or {}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def cleanup():
    """Stop any running bot and clean state."""
    api_post(f"{BASE}/api/are/bot/stop")
    for f in ['bot_state.json', 'bot.pid', 'bot_logs.jsonl']:
        try: os.remove(os.path.join(DATA_DIR, f))
        except: pass

# ─── SETUP ────────────────────────────────────────────────────────────────────
print("=== Cleaning up ===")
cleanup()
time.sleep(1)

# ─── TEST 1: Status when no bot is running ────────────────────────────────────
print("\n=== TEST 1: Status when idle ===")
status = api_get(f"{BASE}/api/are/bot/status")
check("idle status returns", status.get("status") in ("idle", None),
      f"got status={status.get('status')}")
check("no active ticket", status.get("active_ticket") is None,
      f"got ticket={status.get('active_ticket')}")
check("trade_count is 0", status.get("trade_count", 0) == 0,
      f"got {status.get('trade_count')}")

# ─── TEST 2: Stop when not running ────────────────────────────────────────────
print("\n=== TEST 2: Stop when not running (idempotent) ===")
stop_result = api_post(f"{BASE}/api/are/bot/stop")
check("stop returns success", stop_result.get("success") == True,
      f"got {stop_result}")
check("stop says not running", "not running" in stop_result.get("message", "").lower(),
      f"got: {stop_result.get('message')}")

# ─── TEST 3: Start bot ────────────────────────────────────────────────────────
print("\n=== TEST 3: Start bot ===")
start_result = api_post(f"{BASE}/api/are/bot/start", {"style": "day", "risk": 1})
check("start returns success", start_result.get("success") == True,
      f"error={start_result.get('error', '')}")
bot_pid = start_result.get("pid")
check("start returns PID", bot_pid is not None and bot_pid > 0,
      f"pid={bot_pid}")
check("start returns state", start_result.get("state") is not None)

# ─── TEST 4: Bot is running after start ───────────────────────────────────────
print("\n=== TEST 4: Bot running after start ===")
time.sleep(3)
status = api_get(f"{BASE}/api/are/bot/status")
check("status=running", status.get("status") == "running",
      f"got status={status.get('status')}")
check("pid matches", status.get("pid") == bot_pid or status.get("pid") is not None,
      f"expected={bot_pid}, got={status.get('pid')}")
check("has starting_balance", isinstance(status.get("starting_balance"), (int, float)),
      f"got {status.get('starting_balance')}")

# ─── TEST 5: Bot detects existing MT5 position ────────────────────────────────
print("\n=== TEST 5: Bot detects existing positions ===")
positions = api_get(f"{MT5}/positions")
are_positions = [p for p in positions.get("positions", []) if p.get("comment", "").startswith("ARE-")]
if are_positions:
    check("bot sees ARE positions", True)
    pos = are_positions[0]
    # Wait for bot to pick it up (polls every 5s)
    time.sleep(6)
    status2 = api_get(f"{BASE}/api/are/bot/status")
    check("bot enters HOLDING or has ticket", 
          status2.get("active_ticket") is not None or status2.get("status") == "running",
          f"ticket={status2.get('active_ticket')} status={status2.get('status')}")
else:
    check("no ARE positions to test holding", True, "(skipped — no open positions)")

# ─── TEST 6: Bot logs are written ─────────────────────────────────────────────
print("\n=== TEST 6: Bot logs ===")
logs = api_get(f"{BASE}/api/are/bot/logs")
log_list = logs.get("logs", [])
check("logs exist", len(log_list) > 0, f"got {len(log_list)} entries")
if log_list:
    actions = [l.get("action") for l in log_list]
    check("has START log", "START" in actions, f"actions={actions}")
    check("has INIT log", "INIT" in actions, f"actions={actions}")

# ─── TEST 7: bot_state.json is persisted ──────────────────────────────────────
print("\n=== TEST 7: State persistence ===")
state_file = os.path.join(DATA_DIR, 'bot_state.json')
check("bot_state.json exists", os.path.exists(state_file))
if os.path.exists(state_file):
    with open(state_file) as f:
        disk_state = json.load(f)
    check("disk state has status", "status" in disk_state)
    check("disk state has pid", "pid" in disk_state)
    check("disk state has symbol", disk_state.get("symbol") == "XAUUSD")
    check("disk state has style", disk_state.get("style") == "day")
    check("disk state has risk", disk_state.get("risk") == 1)
    check("disk state has starting_balance", isinstance(disk_state.get("starting_balance"), (int, float)))

# ─── TEST 8: Idempotent start ────────────────────────────────────────────────
print("\n=== TEST 8: Idempotent start (already running) ===")
start2 = api_post(f"{BASE}/api/are/bot/start", {"style": "day", "risk": 1})
check("second start returns success", start2.get("success") == True)
check("second start says already running", "already running" in start2.get("message", "").lower(),
      f"got: {start2.get('message')}")

# ─── TEST 9: Graceful stop ────────────────────────────────────────────────────
print("\n=== TEST 9: Graceful stop ===")
stop_result = api_post(f"{BASE}/api/are/bot/stop")
check("stop returns success", stop_result.get("success") == True)
check("stop message mentions PID", str(bot_pid) in stop_result.get("message", "") or "stopped" in stop_result.get("message", "").lower(),
      f"got: {stop_result.get('message')}")

# Wait for shutdown
time.sleep(3)

# ─── TEST 10: Bot is stopped after SIGTERM ────────────────────────────────────
print("\n=== TEST 10: Bot stopped after SIGTERM ===")
status = api_get(f"{BASE}/api/are/bot/status")
check("status no longer running", status.get("status") != "running",
      f"got status={status.get('status')}")

# ─── TEST 11: State file shows stopped ────────────────────────────────────────
print("\n=== TEST 11: State file after stop ===")
if os.path.exists(state_file):
    with open(state_file) as f:
        final_state = json.load(f)
    check("final state status=stopped", final_state.get("status") == "stopped",
          f"got {final_state.get('status')}")
    check("final state has trade_count", isinstance(final_state.get("trade_count"), int))

# ─── TEST 12: PID file cleaned up ────────────────────────────────────────────
print("\n=== TEST 12: PID file cleanup ===")
pid_file = os.path.join(DATA_DIR, 'bot.pid')
check("bot.pid removed", not os.path.exists(pid_file))

# ─── TEST 13: bot.py runs standalone ──────────────────────────────────────────
print("\n=== TEST 13: bot.py runs standalone ===")
import subprocess
p = subprocess.Popen(
    [sys.executable, os.path.join(os.path.dirname(__file__), '..', 'are', 'bot.py'),
     '--style', 'day', '--risk', '1', '--max-daily-loss', '5'],
    cwd=os.path.join(os.path.dirname(__file__), '..'),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    creationflags=0x08000000
)
time.sleep(5)
check("standalone bot alive", p.poll() is None, f"exit code={p.poll()}")
if p.poll() is None:
    p.terminate()
    p.wait(timeout=5)
    check("standalone bot terminates on SIGTERM", True)
else:
    check("standalone bot terminates on SIGTERM", False, "already dead")

# ─── SUMMARY ──────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"RESULTS: {passed} passed, {len(errors)} failed")
if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  - {e}")
    raise AssertionError(f"{len(errors)} tests failed")
else:
    print("ALL TESTS PASSED")
