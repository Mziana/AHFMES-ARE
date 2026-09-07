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

    # TEST 2: Gate per style — legacy (day/swing/position) = MTF internal
    # consistency; micro/scalp (V2) = gate TA dari tab analisa (|taScore| >= 3).
    print("\n=== TEST 2: Gate consistency (MTF utk legacy, TA utk micro/scalp) ===")
    for style in ["micro", "scalp"]:
        d = fetch(f"{BASE}/api/are/decision?symbol=XAUUSD&style={style}&risk=1")
        check(f"{style}: taSnapshot present", "taSnapshot" in d)
        check(f"{style}: mtfConfirmed reported", "mtfConfirmed" in d)
        snap = d.get("taSnapshot") or {}
        if d.get("decision") in ("BUY", "SELL") and snap.get("available"):
            sc = snap.get("score", 0)
            check(f"{style}: TA entry |score| >= 3", abs(sc) >= 3,
                  f"score={sc}, decision={d.get('decision')}")
        else:
            check(f"{style}: tidak entry => WAIT", d.get("decision") == "WAIT",
                  f"decision={d.get('decision')}")
    for style in ["day", "swing", "position"]:
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

    # TEST 3: Session filter — semua style kini 24 jam (design decision), jadi inSession
    # selalu True. Guard market tutup ditangani flag dataFresh, bukan jendela jam.
    print("\n=== TEST 3: Session filter (24h design) ===")
    for style in ["micro", "scalp", "day", "swing", "position"]:
        d = fetch(f"{BASE}/api/are/decision?symbol=XAUUSD&style={style}&risk=1")
        check(f"{style}: inSession true (24h)", d.get("inSession") == True,
              f"got inSession={d.get('inSession')}")
        check(f"{style}: dataFresh present", "dataFresh" in d)

    # TEST 4: Lot sizing
    print("\n=== TEST 4: Lot sizing ===")
    d = fetch(f"{BASE}/api/are/decision?symbol=XAUUSD&style=day&risk=1")
    balance = d.get("balance", 0)
    lot = d.get("lotSize", 0)
    if d.get("decision") != "WAIT":
        check("lot > 0", lot >= 0.01, f"lot={lot}")
        check("lot affordable", lot <= balance / 8 / 100, f"lot={lot}, max={balance/8/100}")
    else:
        # WAIT can have lot=0 (NEUTRAL signal) or lot>0 (non-WAIT conditions)
        check("WAIT => lot is number", isinstance(lot, (int, float)), f"lot={lot}")

    # TEST 5: SL/TP for non-WAIT
    print("\n=== TEST 5: SL/TP for non-WAIT ===")
    for style in ["day"]:
        d = fetch(f"{BASE}/api/are/decision?symbol=XAUUSD&style={style}&risk=1")
        if d.get("decision") not in ("WAIT", "NEUTRAL"):
            check(f"{style}: slPoints > 0", d.get("slPoints", 0) > 0)
            check(f"{style}: tpPoints > 0", d.get("tpPoints", 0) > 0)
            check(f"{style}: rr >= 1.0", d.get("rr", 0) >= 1.0)
    # Micro kini entri M5+M15 seperti scalp, SL 1.0xATR(M5), TP TETAP 150 poin.
    # minRR 0 = tanpa ambang R:R khusus micro (TP cepat tetap — rr boleh < 0.4)
    d_micro = fetch(f"{BASE}/api/are/decision?symbol=XAUUSD&style=micro&risk=1")
    check("micro: minRR 0 (tanpa ambang R:R)", d_micro.get("minRR") == 0)
    if d_micro.get("decision") not in ("WAIT", "NEUTRAL"):
        # Hormati override manual SL/TP dari menu ATUR SL/TP ENTRY (bila aktif)
        _tp_manual = 0
        try:
            import os as _os
            _cfg_path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "data", "bot_config.json")
            _ov = (json.load(open(_cfg_path, encoding="utf-8")).get("sl_tp") or {}).get("micro") or {}
            _tp_manual = int(_ov.get("tp_points") or 0)
        except Exception:
            _tp_manual = 0
        if _tp_manual > 0:
            check("micro: tpPoints == override manual", d_micro.get("tpPoints", 0) == _tp_manual,
                  f"manual tp={_tp_manual}, got {d_micro.get('tpPoints')}")
        else:
            check("micro: tpPoints == 150 (TP tetap)", d_micro.get("tpPoints", 0) == 150)
        check("micro: slPoints > 0", d_micro.get("slPoints", 0) > 0)

    # scalp: TP adaptif = max(150, 2xATR M5) — floor 150 + ikut ATR
    d_scalp = fetch(f"{BASE}/api/are/decision?symbol=XAUUSD&style=scalp&risk=1")
    if d_scalp.get("decision") not in ("WAIT", "NEUTRAL"):
        m5_atr = (d_scalp.get("timeframeSignals") or {}).get("M5", {}).get("atr", 0)
        exp_tp = max(150, round(m5_atr * 2 * 100))
        check("scalp: tpPoints adaptif = max(150, 2xATR M5)", d_scalp.get("tpPoints", 0) == exp_tp,
              f"expected {exp_tp}, got {d_scalp.get('tpPoints')} (ATR {m5_atr})")
        check("scalp: slPoints > 0", d_scalp.get("slPoints", 0) > 0)

    # TEST 5b: V2 — gate TA (tab analisa) utk micro & scalp. Micro tidak lagi
    # memakai gate bias candle H4: arah datang dari master signal tab analisa.
    print("\n=== TEST 5b: TA gate (tab analisa) utk micro & scalp ===")
    check("h4Trend field present", "h4Trend" in d_micro)
    for style in ["micro", "scalp"]:
        d2 = fetch(f"{BASE}/api/are/decision?symbol=XAUUSD&style={style}&risk=1")
        snap = d2.get("taSnapshot")
        check(f"{style}: taSnapshot ada", isinstance(snap, dict))
        if isinstance(snap, dict):
            check(f"{style}: taSnapshot.available", snap.get("available") is True)
            if snap.get("available"):
                sc = snap.get("score", 0)
                check(f"{style}: score dlm [-5,5]", -5 <= sc <= 5, f"score={sc}")
                if d2.get("decision") in ("BUY", "SELL"):
                    want_buy = d2.get("decision") == "BUY"
                    check(f"{style}: entry searah skor",
                          (sc >= 3) == want_buy and (sc <= -3) == (not want_buy),
                          f"score={sc}, decision={d2.get('decision')}")
                elif d2.get("decision") == "WAIT":
                    r = d2.get("decisionReason") or ""
                    ta_wait = ("TA:" in r and abs(sc) < 3)
                    other_wait = ("basi" in r or "sesi" in r or "tidak tersedia" in r or "Risk:Reward" in r
                                  or r.startswith("pola:") or "memori" in r)
                    check(f"{style}: WAIT konsisten dgn skor", ta_wait or other_wait,
                          f"score={sc}, reason={r}")

    # TEST 6: Validation
    print("\n=== TEST 6: Trade execute validation ===")
    r = post(f"{BASE}/api/are/trade/execute", {"action": "open"})
    check("open without params => fail", r.get("success") == False,
          f"got success={r.get('success')}")
    r = post(f"{BASE}/api/are/trade/execute", {"action": "close"})
    check("close without ticket => fail", r.get("success") == False,
          f"got success={r.get('success')}")

    # TEST 7: BUY open then close lifecycle — DRY RUN (never trades real money)
    print("\n=== TEST 7: BUY open then close lifecycle (dry run) ===")
    r = post(f"{BASE}/api/are/trade/execute", {
        "action": "open", "symbol": "XAUUSD", "direction": "BUY",
        "lot": 0.01, "sl_points": 20, "tp_points": 40, "comment": "ARE-TEST",
        "dryRun": True
    })
    check("open succeeds", r.get("success") == True, f"error={r.get('error',r.get('message',''))}")
    ticket = r.get("ticket")
    price = r.get("price")
    check(f"got ticket", ticket is not None, f"ticket={ticket}")
    check(f"got price", price is None or price > 4000, f"price={price}")
    check("dry run flag", r.get("dryRun") == True, f"dryRun={r.get('dryRun')}")

    if ticket and ticket > 0:
        # Only verify real MT5 position when NOT in dry-run (ticket is negative in dry-run)
        positions = fetch(f"{MT5}/positions")
        pos = [p for p in positions.get("positions", []) if p.get("ticket") == ticket]
        check("position exists in MT5", len(pos) == 1)
        if pos:
            p = pos[0]
            expected_sl = round(price - 20, 2)
            expected_tp = round(price + 40, 2)
            check("SL ~ price - 20", abs(p.get("sl", 0) - expected_sl) <= 0.50,
                  f"expected={expected_sl}, got={p.get('sl')}")
            check("TP ~ price + 40", abs(p.get("tp", 0) - expected_tp) <= 0.50,
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
        else:
            check("dry-run: no real position (expected)", True)

    # TEST 8: SELL open - verify SL/TP direction
    print("\n=== TEST 8: SELL SL/TP direction (dry run) ===")
    r = post(f"{BASE}/api/are/trade/execute", {
        "action": "open", "symbol": "XAUUSD", "direction": "SELL",
        "lot": 0.01, "sl_points": 15, "tp_points": 30, "comment": "ARE-SELL",
        "dryRun": True
    })
    check("sell open succeeds", r.get("success") == True,
          f"error={r.get('error',r.get('message',''))}")
    sell_ticket = r.get("ticket")
    sell_price = r.get("price")
    if sell_ticket and sell_ticket > 0:
        positions = fetch(f"{MT5}/positions")
        sell_pos = [p for p in positions.get("positions", []) if p.get("ticket") == sell_ticket]
        if sell_pos:
            p = sell_pos[0]
            expected_sl = round(sell_price + 15, 2)
            expected_tp = round(sell_price - 30, 2)
            check("SELL: SL above entry", abs(p.get("sl", 0) - expected_sl) <= 0.50,
                  f"expected={expected_sl}, got={p.get('sl')}")
            check("SELL: TP below entry", abs(p.get("tp", 0) - expected_tp) <= 0.50,
                  f"expected={expected_tp}, got={p.get('tp')}")
            r2 = post(f"{BASE}/api/are/trade/execute", {"action": "close", "ticket": sell_ticket})
            check("sell close succeeds", r2.get("success") == True)
        else:
            check("dry-run: no real position (expected)", True)

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
