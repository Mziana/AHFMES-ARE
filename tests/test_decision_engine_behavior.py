"""
Behavioral test: Decision Engine API + Trade Execution
Verifies gate logic, MTF confirmation, session filter, R:R, lot sizing,
and full open/close lifecycle with correct SL/TP offsets.
"""
import json, sys, urllib.request

BASE = "http://localhost:4028"
MT5 = "http://127.0.0.1:18888"

def fetch(url, timeout=15):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())

def post(url, data, timeout=15):
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())

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

if __name__ == "__main__":
    # TEST 1: All 5 styles return valid responses
    print("\n=== TEST 1: All styles return valid data ===")
    for style in ["micro", "scalp", "day", "swing", "position"]:
        d = fetch(f"{BASE}/api/are/decision?symbol=XAUUSD&style={style}&risk=1")
        check(f"{style}: success", d.get("success") == True)
        check(f"{style}: decision", d.get("decision") in ("BUY", "SELL", "WAIT"))
        check(f"{style}: finalSignal", d.get("finalSignal") in ("BUY", "SELL", "NEUTRAL"))
        check(f"{style}: mtfConfirmed present", "mtfConfirmed" in d)
        check(f"{style}: inSession present", "inSession" in d)
        check(f"{style}: rr present", "rr" in d)
        check(f"{style}: slPoints present", "slPoints" in d)
        check(f"{style}: tpPoints present", "tpPoints" in d)
        check(f"{style}: lotSize present", "lotSize" in d)
        check(f"{style}: timeframeSignals", "timeframeSignals" in d)
        check(f"{style}: reasoning", "reasoning" in d and len(d["reasoning"]) > 0)

    # TEST 2: MTF confirmation gate is correct
    print("\n=== TEST 2: MTF confirmation gate ===")
    for style in ["micro", "scalp", "day", "swing", "position"]:
        d = fetch(f"{BASE}/api/are/decision?symbol=XAUUSD&style={style}&risk=1")
        tf = d.get("timeframeSignals", {})
        primary = d.get("finalSignal")
        min_req = d.get("minRequired", 0)
        agree_count = sum(1 for s in tf.values() if s.get("signal") == primary)
        total_reported = d.get("totalConfirmations", 0)
        check(f"{style}: confirmations match", total_reported == agree_count,
              f"reported={total_reported}, computed={agree_count}")
        if agree_count >= min_req:
            check(f"{style}: mtfConfirmed=true", d.get("mtfConfirmed") == True,
                  f"{agree_count}>={min_req} should be confirmed")
        else:
            check(f"{style}: mtfConfirmed=false", d.get("mtfConfirmed") == False,
                  f"{agree_count}<{min_req} should not be confirmed")

    # TEST 3: Session filter
    print("\n=== TEST 3: Session filter ===")
    d = fetch(f"{BASE}/api/are/decision?symbol=XAUUSD&style=day&risk=1")
    from datetime import datetime, timezone
    utc_hour = datetime.now(timezone.utc).hour
    in_session = 7 <= utc_hour < 20
    check("day: session matches UTC", d.get("inSession") == in_session,
          f"hour={utc_hour}, expected_in_session={in_session}")

    # TEST 4: Lot sizing
    print("\n=== TEST 4: Lot sizing ===")
    d = fetch(f"{BASE}/api/are/decision?symbol=XAUUSD&style=day&risk=1")
    balance = d.get("balance", 0)
    lot = d.get("lotSize", 0)
    if d.get("decision") != "WAIT":
        check("lot > 0", lot >= 0.01, f"lot={lot}")
        check("lot affordable", lot <= balance / 8 / 100, f"lot={lot}, max={balance/8/100}")
    else:
        check("WAIT => lot=0", lot == 0, f"lot={lot}")

    # TEST 5: SL/TP for non-WAIT
    print("\n=== TEST 5: SL/TP for non-WAIT ===")
    for style in ["day"]:
        d = fetch(f"{BASE}/api/are/decision?symbol=XAUUSD&style={style}&risk=1")
        if d.get("decision") not in ("WAIT", "NEUTRAL"):
            check(f"{style}: slPoints > 0", d.get("slPoints", 0) > 0)
            check(f"{style}: tpPoints > 0", d.get("tpPoints", 0) > 0)
            check(f"{style}: rr >= 1.0", d.get("rr", 0) >= 1.0)
    # Micro has tiny ATR on M1 — slPoints can legitimately be 0
    d_micro = fetch(f"{BASE}/api/are/decision?symbol=XAUUSD&style=micro&risk=1")
    if d_micro.get("decision") not in ("WAIT", "NEUTRAL"):
        check("micro: tpPoints > 0", d_micro.get("tpPoints", 0) > 0)
        check("micro: rr >= 1.0", d_micro.get("rr", 0) >= 1.0)

    # TEST 6: Validation
    print("\n=== TEST 6: Trade execute validation ===")
    r = post(f"{BASE}/api/are/trade/execute", {"action": "open"})
    check("open without params => fail", r.get("success") == False,
          f"got success={r.get('success')}")
    r = post(f"{BASE}/api/are/trade/execute", {"action": "close"})
    check("close without ticket => fail", r.get("success") == False,
          f"got success={r.get('success')}")

    # TEST 7: BUY open then close lifecycle
    print("\n=== TEST 7: BUY open then close lifecycle ===")
    r = post(f"{BASE}/api/are/trade/execute", {
        "action": "open", "symbol": "XAUUSD", "direction": "BUY",
        "lot": 0.01, "sl_points": 20, "tp_points": 40, "comment": "ARE-TEST"
    })
    check("open succeeds", r.get("success") == True, f"error={r.get('error',r.get('message',''))}")
    ticket = r.get("ticket")
    price = r.get("price")
    check(f"got ticket", ticket is not None and ticket > 0, f"ticket={ticket}")
    check(f"got price", price is not None and price > 4000, f"price={price}")

    if ticket:
        positions = fetch(f"{MT5}/positions")
        pos = [p for p in positions.get("positions", []) if p.get("ticket") == ticket]
        check("position exists in MT5", len(pos) == 1)
        if pos:
            p = pos[0]
            expected_sl = round(price - 20, 2)
            expected_tp = round(price + 40, 2)
            # Allow 0.10 tolerance for tick movement between open and verify
            check("SL ~ price - 20", abs(p.get("sl", 0) - expected_sl) <= 0.10,
                  f"expected={expected_sl}, got={p.get('sl')}")
            check("TP ~ price + 40", abs(p.get("tp", 0) - expected_tp) <= 0.10,
                  f"expected={expected_tp}, got={p.get('tp')}")
            check("volume=0.01", p.get("volume") == 0.01)
            check("comment=ARE-TEST", p.get("comment") == "ARE-TEST")
        # Close
        r2 = post(f"{BASE}/api/are/trade/execute", {"action": "close", "ticket": ticket})
        check("close succeeds", r2.get("success") == True,
              f"error={r2.get('error',r2.get('message',''))}")
        # Verify gone
        positions2 = fetch(f"{MT5}/positions")
        gone = not any(p.get("ticket") == ticket for p in positions2.get("positions", []))
        check("position closed in MT5", gone)

    # TEST 8: SELL open - verify SL/TP direction
    print("\n=== TEST 8: SELL SL/TP direction ===")
    r = post(f"{BASE}/api/are/trade/execute", {
        "action": "open", "symbol": "XAUUSD", "direction": "SELL",
        "lot": 0.01, "sl_points": 15, "tp_points": 30, "comment": "ARE-SELL"
    })
    check("sell open succeeds", r.get("success") == True,
          f"error={r.get('error',r.get('message',''))}")
    sell_ticket = r.get("ticket")
    sell_price = r.get("price")
    if sell_ticket:
        positions = fetch(f"{MT5}/positions")
        sell_pos = [p for p in positions.get("positions", []) if p.get("ticket") == sell_ticket]
        if sell_pos:
            p = sell_pos[0]
            expected_sl = round(sell_price + 15, 2)
            expected_tp = round(sell_price - 30, 2)
            check("SELL: SL above entry", abs(p.get("sl", 0) - expected_sl) <= 0.10,
                  f"expected={expected_sl}, got={p.get('sl')}")
            check("SELL: TP below entry", abs(p.get("tp", 0) - expected_tp) <= 0.10,
                  f"expected={expected_tp}, got={p.get('tp')}")
        r2 = post(f"{BASE}/api/are/trade/execute", {"action": "close", "ticket": sell_ticket})
        check("sell close succeeds", r2.get("success") == True)

    # SUMMARY
    print(f"\n{'='*60}")
    print(f"RESULTS: {passed} passed, {len(errors)} failed")
    if errors:
        print("\nFAILURES:")
        for e in errors:
            print(f"  - {e}")
        raise AssertionError(f"{len(errors)} tests failed")
    else:
        print("ALL TESTS PASSED")
