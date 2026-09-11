"""R1 S0.2b — engine eksekusi M1 (H-EXEC-M1-01 + H-IBREAK-01).

Kontrak eksekusi identik dengan run_execution_replay (F1/F2, basis BID, spread
tepat satu kali per arah, SL-priority intrabar), dengan DUA perbedaan terdaftar:

1. EKSEKUSI M1 (H-EXEC-M1-01):
   - Market entry: bar M1 PERTAMA DENGAN time >= T (aturan first-AVAILABLE,
     disetujui owner 2026-09-09 untuk 5 gap 120s terdokumentasi; fail-closed
     bila tidak ada bar).
   - Scan SL/TP posisi terbuka pada SEMUA bar M1 dalam (start, T] tiap record —
     resolusi 5x lebih halus dari M5.
2. PENDING STOP (H-IBREAK-01, config-gated):
   - Record berisi pending_order (placement_ts, order_type BUY_STOP/SELL_STOP,
     stop_price, expiry_bars, trigger_tier) — dari gate b5_inside_bar_signal.
   - PLACEMENT: open bar M1 pertama >= placement_ts + 300 (sinyal valid di close).
   - TRIGGER: bar M1 pertama dengan high >= stop (BUY) / low <= stop (SELL),
     bar PERTAMA yang di-scan adalah bar SETELAH bar placement (market may not
     touch sebelum order live; aturan di-beh di registry H-IBREAK-01).
   - FILL: harga stop + sel slippage. BUY: fill = stop + slip; SELL: fill =
     stop - slip. Kontrak spread satu-kali-per-arah (F1/F2) dipertahankan:
     BUY cost = exit spread + comm; SELL cost = entry spread + comm.
   - EXPIRY: N bar M1 sejak placement (N=12, beku); cancel saat posisi market
     terbuka; cancel saat REVERSAL.
   - ONE_POSITION_ONLY + cooldown + REGIME_CHANGE exit: identik M5 engine.

Scan internal pending loop: selalu M1 (file ini). Saat scan_m1 flag OFF
(default), SL/TP exit di-scan pada bar M5-champion (M1 hanya menentukan entry)
agar identitas numerik vs run_execution_replay bisa diverifikasi eksak
(S0.4 parity); flag ON digunakan untuk run penelitian sesungguhnya.
"""
from __future__ import annotations

from . import broker_meta as bm
from .costs import compute_cost

M1_BAR = 60
M5_BAR = 300


def run_execution_m1(records: list, m5: list, m1: list, profile: dict,
                     spread_points: float | None = None,
                     slippage_points: float | None = None,
                     commission_usd_per_lot: float | None = None,
                     broker_meta: dict | None = None,
                     spread_label: str | None = None,
                     scan_m1_exits: bool = False) -> dict:
    meta = broker_meta if broker_meta is not None else bm.load_broker_meta({})
    pv = bm.point_value_usd_per_lot(meta)
    point_price = meta["point"]
    meta_hash = bm.broker_meta_hash(meta)

    cost = compute_cost(spread_points, spread_points,
                        commission=commission_usd_per_lot,
                        slippage=slippage_points, delay=0,
                        spread_label=spread_label)
    spread_pts = cost["entry_spread_points"]
    slip_pts = cost["slippage_points"]
    comm = cost["commission_usd_per_lot"]
    spread_px = spread_pts * point_price
    slip_px = slip_pts * point_price

    m1_by_time = {int(b["time"]): b for b in m1}
    m1_times = sorted(m1_by_time.keys())
    m5_by_time = {int(b["time"]): b for b in m5}
    m5_ordered = sorted(m5_by_time.keys())
    scan_times = m1_times if scan_m1_exits else None  # None → scan via M5 grid

    def next_available_m1(ts: int):
        """Bar M1 pertama dengan time >= ts (first-AVAILABLE; None = fail-closed)."""
        lo, hi, idx = 0, len(m1_times) - 1, None
        while lo <= hi:
            mid = (lo + hi) // 2
            if m1_times[mid] >= ts:
                idx = mid
                hi = mid - 1
            else:
                lo = mid + 1
        return m1_times[idx] if idx is not None else None

    trades: list = []
    rejected: list = []
    risk = profile["risk"]
    cooldown_sec = risk["cooldown_minutes"] * 60
    last_entry_ts = None
    open_pos: dict | None = None
    pending: dict | None = None
    n_reversals = 0
    n_eod = 0
    n_pending_placed = 0
    n_pending_triggered = 0
    n_pending_expired = 0
    n_pending_cancelled = 0
    last_pending_ts = None

    def make_trade(pos: dict, exit_ts: int, exit_price: float,
                   exit_reason: str) -> dict:
        direction = pos["direction"]
        if direction == "BUY":
            pts = (exit_price - pos["entry"]) / point_price
            cost_usd = (spread_pts * pv + comm) * pos["lot"]   # exit spread + comm
            entry_side, exit_side = "ASK", "BID"
        else:
            pts = (pos["entry"] - exit_price) / point_price
            cost_usd = (spread_pts * pv + comm) * pos["lot"]   # entry spread + comm
            entry_side, exit_side = "BID", "ASK"
        gross_usd = pts * pv * pos["lot"]
        return {
            "entry_ts": pos["entry_ts"], "exit_ts": exit_ts,
            "direction": direction, "signal_ts": pos["signal_ts"],
            "delay_bars": 0, "slippage_points": slip_pts,
            "entry": pos["entry"], "exit": exit_price,
            "exit_reason": exit_reason,
            "sl_points": pos["sl_points"], "tp_points": pos["tp_points"],
            "lot": pos["lot"], "gross_points": round(pts, 2),
            "gross_usd": round(gross_usd, 4),
            "cost_usd": round(cost_usd, 4),
            "net_usd": round(gross_usd - cost_usd, 4),
            "cost_label": cost["label"],
            "price_basis": "BID",
            "entry_side": entry_side, "exit_side": exit_side,
            "entry_kind": pos.get("entry_kind", "MARKET_M1"),
            "broker_meta_hash": meta_hash,
        }

    def scan_exits(pos: dict, up_to_excl: int) -> dict | None:
        """SL/TP scan window [scan_from, up_to_excl) — INKLUSIF bar entry/
        trigger (SL/TP bisa kena intrabar setelah open/fill; SL-priority).
        Record T memproses interval [T, T+300): pemanggil memakai
        up_to_excl = T + M5_BAR.
        scan_m1_exits=True: grid M1 60s (hit -> exit_ts = t + 60).
        False: grid M5 (identitas eksak vs run_execution_replay:
        window [scan_from, T] inklusif == [scan_from, T+300) eksklusif).
        """
        if scan_times is not None:
            for t in scan_times:
                if t < pos["scan_from"] or t >= up_to_excl:
                    continue
                b = m1_by_time[t]
                if pos["direction"] == "BUY":
                    hit_sl = b["low"] <= pos["sl_price"]
                    hit_tp = b["high"] >= pos["tp_price"]
                else:
                    hit_sl = b["high"] >= pos["sl_price"] - spread_px
                    hit_tp = b["low"] <= pos["tp_price"] - spread_px
                if hit_sl:
                    return make_trade(pos, t + M1_BAR, pos["sl_price"], "SL")
                if hit_tp:
                    return make_trade(pos, t + M1_BAR, pos["tp_price"], "TP")
            return None
        for t in m5_ordered:
            if t < pos["scan_from"] or t >= up_to_excl:
                continue
            b = m5_by_time[t]
            if pos["direction"] == "BUY":
                hit_sl = b["low"] <= pos["sl_price"]
                hit_tp = b["high"] >= pos["tp_price"]
            else:
                hit_sl = b["high"] >= pos["sl_price"] - spread_px
                hit_tp = b["low"] <= pos["tp_price"] - spread_px
            if hit_sl:
                return make_trade(pos, t + M5_BAR, pos["sl_price"], "SL")
            if hit_tp:
                return make_trade(pos, t + M5_BAR, pos["tp_price"], "TP")
        return None

    def mark_to_market(pos: dict, ts: int, reason: str) -> dict:
        b = m5_by_time[ts]
        exit_px = b["close"] + (spread_px if pos["direction"] == "SELL" else 0.0)
        return make_trade(pos, ts + M5_BAR, exit_px, reason)

    def close_pending(reason: str) -> None:
        nonlocal pending, n_pending_cancelled
        if pending is not None:
            n_pending_cancelled += 1
            rejected.append({"ts": int(pending["placement_ts"]), "reason": reason,
                             "decision": pending["order_type"],
                             "pending_cancelled": True})
            pending = None

    for rec in records:
        T = int(rec["evaluation_timestamp"])

        # 0) SL/TP scan posisi terbuka pada interval [T, T+300) — M1 resolusi
        #    penuh atau grid M5 (mode identitas)
        if open_pos is not None:
            closed = scan_exits(open_pos, T + M5_BAR)
            if closed is not None:
                trades.append(closed)
                open_pos = None

        # 1) PENDING lifecycle (sebelum sinyal baru): trigger → expiry.
        #    Window trigger = bar M1 dengan time di [cursor, T+300) ∧ ≤ expiry.
        #    Fill di harga stop (+slippage), scan exit SETELAH bar trigger
        #    di-handle via scan_from = trig (inklusif — SL bisa kena bar yang
        #    sama, konservatif, konsisten dengan entry-bar M5 engine).
        if pending is not None:
            pt = int(pending["trigger_scan_from"])
            exp_ts = int(pending["expiry_ts"])
            trig = next_available_m1(pt)
            while trig is not None and trig <= exp_ts and trig < T + M5_BAR:
                b = m1_by_time[trig]
                hit = (b["high"] >= pending["stop_price"]) if pending["order_type"] == "BUY_STOP" \
                    else (b["low"] <= pending["stop_price"])
                if hit:
                    if open_pos is not None:
                        # belt-and-braces: ONE_POSITION_ONLY — pending tidak boleh
                        # menimpa posisi yang ada (kontrak: cancel saat posisi terbuka)
                        rejected.append({"ts": trig, "reason": "pending_cancelled_position_open",
                                         "decision": pending["order_type"], "pending_cancelled": True})
                        n_pending_cancelled += 1
                        pending = None
                        break
                    direction = "BUY" if pending["order_type"] == "BUY_STOP" else "SELL"
                    fill = pending["stop_price"] + (slip_px if direction == "BUY" else -slip_px)
                    sl_d = pending["sl_points"] * point_price
                    tp_d = pending["tp_points"] * point_price
                    if direction == "BUY":
                        sl_price, tp_price = fill - sl_d, fill + tp_d
                    else:
                        sl_price, tp_price = fill + sl_d, fill - tp_d
                    open_pos = {
                        "direction": direction, "entry_ts": trig, "entry": fill,
                        "sl_price": sl_price, "tp_price": tp_price,
                        "sl_points": pending["sl_points"], "tp_points": pending["tp_points"],
                        "lot": pending["lot"], "signal_ts": pending["signal_ts"],
                        "entry_kind": "PENDING_STOP_M1",
                        "scan_from": trig,   # scan exit INKLUSIF bar trigger
                    }
                    n_pending_triggered += 1
                    last_entry_ts = trig   # cooldown ter-anchor di fill
                    pending = None
                    break
                pt = trig + M1_BAR
                trig = next_available_m1(pt)
            if pending is not None:
                pending["trigger_scan_from"] = pt   # cursor maju (anti re-scan)

        if pending is not None and T > pending["expiry_ts"]:
            rejected.append({"ts": int(pending["placement_ts"]), "reason": "pending_expired",
                             "decision": pending["order_type"], "expiry_ts": pending["expiry_ts"]})
            n_pending_expired += 1
            pending = None

        if rec["decision"] not in ("BUY", "SELL"):
            continue
        direction = rec["decision"]

        # 2) position gate — market sinyal; pending berlawanan di-cancel
        if open_pos is not None:
            if direction == open_pos["direction"]:
                close_pending("position_open_cancel_pending")
                rejected.append({"ts": T, "reason": "position_open", "decision": direction})
                continue
            trades.append(mark_to_market(open_pos, T, "REVERSAL"))
            n_reversals += 1
            open_pos = None
            close_pending("reversal_cancel_pending")

        # 3) REGIME CHANGE exit (identik M5 engine) + cancel pending berlawanan
        current_bias = rec.get("bias")
        if open_pos is not None and current_bias is not None:
            if (open_pos["direction"] == "BUY" and current_bias == "SELL_ONLY") or \
               (open_pos["direction"] == "SELL" and current_bias == "BUY_ONLY"):
                trades.append(mark_to_market(open_pos, T, "REGIME_CHANGE"))
                open_pos = None
        if pending is not None and current_bias is not None:
            pdir = "BUY" if pending["order_type"] == "BUY_STOP" else "SELL"
            if (pdir == "BUY" and current_bias == "SELL_ONLY") or \
               (pdir == "SELL" and current_bias == "BUY_ONLY"):
                close_pending("regime_change_cancel_pending")

        # 4) cooldown
        if last_entry_ts is not None and T - last_entry_ts < cooldown_sec:
            rejected.append({"ts": T, "reason": "cooldown", "decision": direction})
            continue

        # 5) Pasang intent baru: market-on-M1 (default) ATAU pending STOP (Arm D)
        po = rec.get("pending_order") or {}
        if rec.get("order_mode") == "PENDING_STOP" and po.get("order_type") in ("BUY_STOP", "SELL_STOP"):
            pending = {
                "order_type": po["order_type"], "stop_price": float(po["stop_price"]),
                "placement_ts": T, "signal_ts": T,
                "expiry_ts": T + int(po.get("expiry_bars", 12)) * M1_BAR,
                "trigger_scan_from": T + M1_BAR,   # order live mulai bar SETELAH sinyal
                "sl_points": rec["sl_points"], "tp_points": rec["tp_points"],
                "lot": rec["lot"],
            }
            n_pending_placed += 1
            last_pending_ts = T
            continue

        # market: bar M1 pertama dengan time >= T (T = close bar sinyal = open berikut)
        close_pending("market_entry_cancel_pending")   # kontrak H-IBREAK-01: cancel saat posisi market terbuka
        e_ts = next_available_m1(T)
        if e_ts is None:
            rejected.append({"ts": T, "reason": "no_m1_bar", "decision": direction})
            continue
        entry_bar = m1_by_time[e_ts]
        if direction == "BUY":
            entry = entry_bar["open"] + spread_px + slip_px
        else:
            entry = entry_bar["open"] - slip_px
        sl_d = rec["sl_points"] * point_price
        tp_d = rec["tp_points"] * point_price
        if direction == "BUY":
            sl_price, tp_price = entry - sl_d, entry + tp_d
        else:
            sl_price, tp_price = entry + sl_d, entry - tp_d
        open_pos = {
            "direction": direction, "entry_ts": e_ts, "entry": entry,
            "sl_price": sl_price, "tp_price": tp_price,
            "sl_points": rec["sl_points"], "tp_points": rec["tp_points"],
            "lot": rec["lot"], "signal_ts": T,
            "entry_kind": "MARKET_M1",
            "scan_from": e_ts,   # scan exit mulai SETELAH bar entry
        }
        last_entry_ts = T

    # Final sweep: scan sisa bar (hingga akhir data), lalu EOD_MARK bila terbuka
    if open_pos is not None:
        end_excl = (m1_times[-1] + M1_BAR) if scan_times is not None else (m5_ordered[-1] + M5_BAR)
        closed = scan_exits(open_pos, end_excl)
        if closed is not None:
            trades.append(closed)
        else:
            trades.append(mark_to_market(open_pos, m5_ordered[-1], "EOD_MARK"))
            n_eod += 1
    if pending is not None:
        rejected.append({"ts": int(pending["placement_ts"]), "reason": "pending_expired_eod",
                         "decision": pending["order_type"]})
        n_pending_expired += 1
        pending = None

    executed = len(trades)
    gross = sum(t["gross_usd"] for t in trades)
    costs = sum(t["cost_usd"] for t in trades)
    net = sum(t["net_usd"] for t in trades)
    return {
        "engine": "run_execution_m1",
        "scan_exits_resolution": "M1" if scan_m1_exits else "M5_grid (identitas-vs-replay mode)",
        "cost_label": cost["label"],
        "spread_model": {"entry_spread_points": cost["entry_spread_points"],
                         "exit_spread_points": cost["exit_spread_points"],
                         "slippage_points": cost["slippage_points"],
                         "delay_bars": 0,
                         "commission_usd_per_lot": comm,
                         "point_value_usd_per_lot": pv,
                         "point_price": point_price,
                         "broker_meta_hash": meta_hash},
        "state_machine": "ONE_POSITION_ONLY",
        "position_state": "LONG" if open_pos else "FLAT",
        "state_transitions": {"reversals": n_reversals, "eod_marks": n_eod},
        "pending_stats": {"placed": n_pending_placed, "triggered": n_pending_triggered,
                          "expired": n_pending_expired, "cancelled": n_pending_cancelled,
                          "last_pending_ts": last_pending_ts},
        "executed_trades": executed,
        "rejected_executions": rejected,
        "trades": trades,
        "gross_usd": round(gross, 4),
        "total_costs_usd": round(costs, 4),
        "net_usd": round(net, 4),
        "expectancy_gross_usd": round(gross / executed, 4) if executed else 0.0,
        "expectancy_net_usd": round(net / executed, 4) if executed else 0.0,
    }
