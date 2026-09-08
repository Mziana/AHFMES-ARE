"""P2a — Deterministic Replay Engine (Decision Replay + Execution Replay).

Pagar yang diimplementasikan:
- Pagar 2 (no-lookahead): evaluation loop per bar M5 CLOSED memotong slice
  bars[0..T] SEBELUM memanggil gate engine — engine tidak pernah melihat > T.
- Pagar 3 (tiga truth): Layer A (DATA_INVALID) dipisah; Decision Replay TIDAK
  menghitung PnL; Execution Replay (next-bar-open + cost model) terpisah.
- Pagar 4 (determinism): sumber waktu semantic = market timestamp dari data;
  TIDAK ada now()/time.time() di jalur decision → run sama ×2 = JSONL identik.
- Pagar 6 (diagnostic completeness): funnel report lengkap.

I/O hanya di level CLI (load dataset, tulis JSONL) — gate engine tetap pure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from bisect import bisect_right
from pathlib import Path

from . import broker_meta as bm
from . import gates, registry
from .costs import compute_cost

PKG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PKG_DIR.parent
DEFAULT_OUT = PROJECT_ROOT / "data" / "research" / "v2_replay"

BAR_SECONDS = 300  # M5


# ─── Dataset & qualification ─────────────────────────────────────────────────

def load_candles(path: str | Path) -> list:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return d["candles"] if isinstance(d, dict) else d


def qualify_dataset(m5: list, m15: list) -> dict:
    """Data qualification ringan (mandat P2a): gaps, duplicate, OHLC, volume."""
    def check(bars, tf_seconds, name):
        rep = {"name": name, "bars": len(bars), "duplicate_ts": 0, "gaps": 0,
               "gaps_session_break": 0, "gaps_intra_day": 0,
               "ohlc_invalid": 0, "volume_missing": 0, "nan": 0}
        seen = set()
        prev = None
        for b in bars:
            t = b.get("time")
            if t in seen:
                rep["duplicate_ts"] += 1
            seen.add(t)
            if prev is not None and int(t) - int(prev) != tf_seconds:
                rep["gaps"] += 1
                # klasifikasi selaras policy Layer A (gates.layer_a_m15_integrity):
                # gap >= 3600 dtk = break sesi pasar (maintenance/weekend), bukan
                # korupsi data; gap lebih kecil = kehilangan data intra-sesi.
                if int(t) - int(prev) >= 3600:
                    rep["gaps_session_break"] += 1
                else:
                    rep["gaps_intra_day"] += 1
            prev = t
            o, h, l, c = b.get("open"), b.get("high"), b.get("low"), b.get("close")
            if any(x is None or x != x for x in (o, h, l, c)):
                rep["nan"] += 1
            elif h < max(o, c) or l > min(o, c) or min(o, h, l, c) <= 0:
                rep["ohlc_invalid"] += 1
            v = b.get("volume")
            if v is None or v != v or v < 0:
                rep["volume_missing"] += 1
        rep["valid"] = rep["duplicate_ts"] == 0 and rep["ohlc_invalid"] == 0 and rep["nan"] == 0
        return rep

    return {"m5": check(m5, BAR_SECONDS, "M5"), "m15": check(m15, 900, "M15")}


def load_calendar(path: str | Path | None, staleness_hours: int = 4) -> dict | None:
    """Load kalender ekonomi nyata (ForexFactory JSON). Tidak ada file → None
    (B1 → NEWS_PROVIDER_DOWN, fail-closed).

    Temporal provenance (P0-01): setiap event membawa DUA timestamp terpisah —
    `ts` = event_timestamp (waktu rilis data ekonomi) dan
    `information_available_at` = waktu snapshot kalender ini diambil (epoch UTC
    saat fetch). Staleness B1 diukur dari `information_available_at`, BUKAN
    heuristic max(event.ts): replay historis tidak boleh menganggap snapshot
    now sebagai pengetahuan yang tersedia di masa lalu.
    """
    if path is None or not Path(path).exists():
        return None
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    events = []
    for e in raw if isinstance(raw, list) else raw.get("events", []):
        date_s = str(e.get("date", ""))
        try:
            from datetime import datetime
            ts = int(datetime.fromisoformat(date_s).timestamp())
        except Exception:
            continue
        events.append({"ts": ts, "currency": e.get("country", e.get("currency", "")),
                       "impact": str(e.get("impact", "low")).lower(), "title": e.get("title", "")})
    # information_available_at: HANYA dari field eksplisit artifact. Bila artifact
    # tidak mencatatnya → None → b1_news fail-closed NEWS_DATA_STALE (jujur, bukan
    # heuristic karangan). Snapshot yang ditulis via save_calendar_artifact selalu
    # mencatatnya.
    info_at = raw.get("information_available_at") if isinstance(raw, dict) else None
    if info_at is not None:
        try:
            info_at = int(info_at)
        except Exception:
            info_at = None
    # archived: HANYA dari field eksplisit artifact (ditulis save_calendar_artifact).
    # File kalender mentah (snapshot provider) TIDAK dianggap arsip — age-check
    # tetap jalan di jalur live.
    archived = bool(raw.get("archived")) if isinstance(raw, dict) else False
    return {"status": "ok" if events else "empty",
            "information_available_at": info_at, "events": events,
            "archived": archived}


def save_calendar_artifact(raw: dict | list, src_path: str | Path,
                           out_dir: str | Path, fetched_at: int) -> Path:
    """P1-01 — snapshot kalender ke artifact deterministik + provenance.

    Menulis data/research/calendar/calendar_<sha8>.json berisi events +
    information_available_at (= fetched_at epoch UTC). Return path artifact;
    hash artifact (SHA-256 konten) dipakai compute_config_hash (P0-02/P1-02).
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    artifact = {"information_available_at": int(fetched_at),
                "archived": True,  # satu-satunya jalur yang boleh menandai arsip
                "source": str(src_path),
                "events": (raw if isinstance(raw, list) else raw.get("events", []))}
    blob = json.dumps(artifact, sort_keys=True, ensure_ascii=True)
    h = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    path = out / f"calendar_{h[:8]}.json"
    path.write_text(blob, encoding="utf-8")
    return path


def calendar_artifact_hash(path: str | Path | None) -> str | None:
    """SHA-256 konten artifact kalender (untuk config_hash). None bila tak ada."""
    if path is None or not Path(path).exists():
        return None
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ─── Evaluation loop (Decision Replay) ───────────────────────────────────────

def run_decision_replay(m5: list, m15: list, profile: dict, registry_dict: dict,
                        calendar: dict | None, config: dict,
                        disable_gates: tuple = ()) -> list[dict]:
    """Satu record JSONL per M5 CLOSED bar T. Slice bars[0..T] dulu → gates.

    Deterministik: tidak ada now(); urutan & konten hanya fungsi input.

    disable_gates: nama gate Layer B yang di-DISABLE untuk P4 ablation
    ("b3_regime", "b4_location", "b5_trigger", "b6_volume") — gate dinonaktifkan
    via profile VIRTUAL (bukan edit file kontrak), hasil tercatat eksplisit.
    """
    prof_a = profile["layer_a"]
    if disable_gates:
        profile = dict(profile)
        if "b6_volume" in disable_gates:
            profile["volume_gate"] = {**profile.get("volume_gate", {}), "enabled": False}
        if "b3_regime" in disable_gates:
            prof_a = {**prof_a, "b3_enabled": False}
        if "b4_location" in disable_gates:
            prof_a = {**prof_a, "b4_enabled": False}
        if "b5_trigger" in disable_gates:
            prof_a = {**prof_a, "b5_enabled": False}
    cfg = {
        "now_ts": 0,
        "rsi_bias_threshold": registry.hypothesis(registry_dict, "H-RSI-BIAS-01")["value"]["rsi_threshold"],
        "min_bars_m15_warmup": registry.hypothesis(registry_dict, "H-Q1")["value"]["min_bars_m15_warmup"],
        # H-REGIME-SLOPE-02 (revisi P6 iter-1): param B3 slope — None = mode classic
        "b3_slope": registry.hypothesis(registry_dict, "H-REGIME-SLOPE-02")["value"],
        # H-SCORE-01 (Cognitive Layer v2.1): param scorer BQ
        "h_score": registry.hypothesis(registry_dict, "H-SCORE-01")["value"],
        "layer_a": prof_a,
        "calendar": calendar or {"status": "down", "events": []},
        "ticks_meta": {"spread_points": config.get("spread_points")},  # None → cek spread dilewati
        "risk_state": {},   # diupdate oleh eksekusi (dipakai saat gabungan)
    }
    records: list[dict] = []
    # P4: bisect index — slice bars[0..T] O(log n) + list-build terbatas, bukan
    # komprehensi O(n) per bar atas seluruh dataset (identik secara semantik:
    # tetap HANYA bar dengan close <= T yang masuk slice).
    m5_close_ts = [int(b["time"]) + BAR_SECONDS for b in m5]
    m15_close_ts = [int(b["time"]) + 900 for b in m15]

    for bar in m5:
        T = int(bar["time"]) + BAR_SECONDS          # evaluation time = bar CLOSE
        k5 = bisect_right(m5_close_ts, T)
        k15 = bisect_right(m15_close_ts, T)
        m5_slice = m5[:k5]
        m15_slice = m15[:k15]
        if int(m5_slice[-1]["time"]) + BAR_SECONDS != T:
            continue  # bar T belum closed pada T (tidak mungkin utk loop ini)
        c = dict(cfg)
        c["now_ts"] = T
        if disable_gates:
            c["disabled_gates"] = set(disable_gates)
            if "b3_regime" in disable_gates:
                c["ablation_forced_bias"] = "BUY_ONLY"
        diag = gates.evaluate_all({"m5": m5_slice, "m15": m15_slice}, profile, c, {})
        first_veto, decision = gates.decide(diag)

        sl_calc = diag.get("sl_calc") or {}
        sl_points = sl_calc.get("sl_points", 0.0) if decision in ("BUY", "SELL") else 0.0
        tp_points = sl_calc.get("tp_points", 0.0) if decision in ("BUY", "SELL") else 0.0
        balance = config.get("balance", 0.0)
        lot = 0.0
        if decision in ("BUY", "SELL") and sl_points > 0:
            lot = round(config.get("risk_percent", profile["risk"]["risk_percent"]) / 100.0
                        * balance / sl_points, 2)

        records.append({
            "evaluation_timestamp": T,
            "data_available_until": T,
            "strategy_version": registry.STRATEGY_VERSION,
            "profile_id": profile["profile_id"],
            "hypothesis_registry_id": registry.registry_id(registry_dict),
            "config_hash": config["config_hash"],
            "dataset_hash": config["dataset_hash"],
            "layer_a": diag["layer_a"],
            "layer_b_ran": diag["layer_b_ran"],
            "all_gate_results": diag["all_gate_results"],
            "first_veto_reason": first_veto,
            "bias": diag["bias"],
            "setup": diag.get("setup"),
            "trigger": diag.get("trigger"),
            "quality_score": diag.get("quality_score"),
            "decision": decision,
            "sl_points": sl_points,
            "tp_points": tp_points,
            "lot": lot,
            "market_snapshot": diag["market_snapshot"],
        })
    return records


# ─── Execution Replay (next-bar-open + cost model) ───────────────────────────

def run_execution_replay(records: list[dict], m5: list, profile: dict,
                         spread_points: float | None = None,
                         slippage_points: float | None = None,
                         delay_bars: int | None = None,
                         commission_usd_per_lot: float | None = None,
                         broker_meta: dict | None = None,
                         spread_label: str | None = None) -> dict:
    """Decision → simulator next-bar-open + cost model → trades + PnL.

    Kontrak eksekusi v2.4 (F1b, desain §10.1 E-1) — `candle_price_basis = BID`:
    - BUY:  entry = open(BID) + spread + slippage_adverse  (fill di ASK)
            exit (SL/TP/EOD) = level pada basis BID (tanpa spread di harga exit)
    - SELL: entry = open(BID) − slippage_adverse           (dijual di BID)
            exit (SL/TP/EOD) = level + spread (tutup di ASK)
    Spread muncul TEPAT SATU KALI per arah per trade (dilarang double-count):
    BUY  → spread entry dalam path harga; cost_usd = spread exit + commission
    SELL → spread exit dalam path harga;  cost_usd = spread entry + commission
    Round-trip flat (slippage=0, delay=0): net = -(entry+exit+comm)*pv*lot
    PERSIS untuk BUY & SELL (invariant round-trip, test_round_trip_invariant).

    ONE_POSITION_ONLY (desain §10.1 E-3): state FLAT|LONG|SHORT. Sinyal searah
    saat terbuka → REJECTED:position_open; berlawanan → exit_then_reverse
    (posisi lama tutup pada bar sinyal, posisi baru fill next-bar-open + delay).
    Scan SL/TP KRONOLOGIS: posisi terbuka di-scan pada SETIAP record (cursor
    per posisi), bukan hanya saat sinyal berikutnya — posisi yang hit SL/TP
    di tengah dataset tutup pada bar hit-nya, dan sinyal setelahnya melihat
    state FLAT yang benar. EOD_MARK (akhir dataset) tetap ada, dilabeli.
    Intrabar ambiguity (SL & TP kena bar yang sama) → SL dulu (konservatif).
    """
    meta = broker_meta if broker_meta is not None else bm.load_broker_meta({})
    pv = bm.point_value_usd_per_lot(meta)
    point_price = meta["point"]
    meta_hash = bm.broker_meta_hash(meta)

    cost = compute_cost(spread_points, spread_points,
                        commission=commission_usd_per_lot,
                        slippage=slippage_points, delay=delay_bars,
                        spread_label=spread_label)
    spread_pts = cost["entry_spread_points"]
    slip_pts = cost["slippage_points"]
    delay_bars = cost["delay_bars"]
    comm = cost["commission_usd_per_lot"]
    spread_px = spread_pts * point_price
    slip_px = slip_pts * point_price

    by_time = {int(b["time"]): b for b in m5}
    ordered = sorted(by_time.keys())
    trades = []
    rejected = []
    risk = profile["risk"]
    cooldown_sec = risk["cooldown_minutes"] * 60
    last_entry_ts = None
    state = "FLAT"
    open_pos: dict | None = None
    n_reversals = 0
    n_eod = 0

    def make_trade(pos: dict, exit_ts: int, exit_price: float,
                   exit_reason: str, state_after: str) -> dict:
        direction = pos["direction"]
        if direction == "BUY":
            pts = (exit_price - pos["entry"]) / point_price
            cost_usd = (spread_pts * pv + comm) * pos["lot"]  # exit spread + comm
            entry_side, exit_side = "ASK", "BID"
        else:
            pts = (pos["entry"] - exit_price) / point_price
            cost_usd = (spread_pts * pv + comm) * pos["lot"]  # entry spread + comm
            entry_side, exit_side = "BID", "ASK"
        gross_usd = pts * pv * pos["lot"]
        net_usd = gross_usd - cost_usd
        return {
            "entry_ts": pos["entry_ts"], "exit_ts": exit_ts,
            "direction": direction, "signal_ts": pos["signal_ts"],
            "delay_bars": delay_bars, "slippage_points": slip_pts,
            "entry": pos["entry"], "exit": exit_price,
            "exit_reason": exit_reason,
            "sl_points": pos["sl_points"], "tp_points": pos["tp_points"],
            "lot": pos["lot"], "gross_points": round(pts, 2),
            "gross_usd": round(gross_usd, 4),
            "cost_usd": round(cost_usd, 4),
            "net_usd": round(net_usd, 4),
            "cost_label": cost["label"],
            "price_basis": "BID",
            "entry_side": entry_side, "exit_side": exit_side,
            "broker_meta_hash": meta_hash,
            "state_before": pos["state_label"], "state_after": state_after,
        }

    def close_scan(pos: dict, up_to_ts: int) -> dict | None:
        """Scan KRONOLOGIS dari cursor pos (scan_from) sampai up_to_ts
        (inclusive) — SL/TP hit → trade closed (SL priority). None → posisi
        masih terbuka; cursor maju ke bar setelah yang terakhir di-scan agar
        scan berikutnya tidak mengulang bar lama."""
        start = pos.get("scan_from", pos["entry_ts"])
        last_t = None
        for t in ordered:
            if t < start:
                continue
            if t > up_to_ts:
                break
            last_t = t
            b = by_time[t]
            if pos["direction"] == "BUY":
                hit_sl = b["low"] <= pos["sl_price"]
                hit_tp = b["high"] >= pos["tp_price"]
            else:
                # SELL exit di ASK = level + spread → trigger saat ASK mencapai
                # level; ASK = BID + spread → ekuivalen BID: level − spread.
                hit_sl = b["high"] >= pos["sl_price"] - spread_px
                hit_tp = b["low"] <= pos["tp_price"] - spread_px
            if hit_sl:
                return make_trade(pos, t + BAR_SECONDS, pos["sl_price"], "SL", "FLAT")
            if hit_tp:
                return make_trade(pos, t + BAR_SECONDS, pos["tp_price"], "TP", "FLAT")
        if last_t is not None:
            pos["scan_from"] = last_t + BAR_SECONDS
        return None

    def mark_to_market(pos: dict, ts: int, reason: str) -> dict:
        """Close posisi pada bar ts (close price; SELL exit di ASK = close + spread)."""
        b = by_time[ts]
        exit_px = b["close"] + (spread_px if pos["direction"] == "SELL" else 0.0)
        return make_trade(pos, ts + BAR_SECONDS, exit_px, reason, "FLAT")

    for rec in records:
        T = rec["evaluation_timestamp"]

        # 0) KRONOLOGIS: posisi terbuka di-scan sampai bar T pada SETIAP record
        #    (bukan hanya record sinyal) — SL/TP hit di tengah dataset menutup
        #    posisi pada bar hit-nya; sinyal setelahnya melihat FLAT yang benar.
        if open_pos is not None:
            closed = close_scan(open_pos, T)
            if closed is not None:
                trades.append(closed)
                open_pos = None
                state = "FLAT"

        if rec["decision"] not in ("BUY", "SELL"):
            continue
        direction = rec["decision"]

        # 1) position gate (ONE_POSITION_ONLY)
        if open_pos is not None:
            if direction == open_pos["direction"]:
                rejected.append({"ts": T, "reason": "position_open",
                                 "decision": direction})
                continue
            # exit_then_reverse: posisi lama tutup pada bar sinyal (aturan exit
            # normal — SL/TP sudah di-scan sampai bar itu; else mark-to-market)
            trades.append(mark_to_market(open_pos, T, "REVERSAL"))
            n_reversals += 1
            open_pos = None
            state = "FLAT"

        # 2) REGIME CHANGE EXIT: bias flips -> close position
        #    Extract bias from current record's diagnostic
        current_bias = rec.get("bias")
        if open_pos is not None and current_bias is not None:
            pos_direction = open_pos["direction"]
            # Long position + bias flips to SELL_ONLY -> close
            # Short position + bias flips to BUY_ONLY -> close
            if (pos_direction == "BUY" and current_bias == "SELL_ONLY") or \
               (pos_direction == "SELL" and current_bias == "BUY_ONLY"):
                trades.append(mark_to_market(open_pos, T, "REGIME_CHANGE"))
                open_pos = None
                state = "FLAT"

        # 2) cooldown (untuk setiap entry baru, incl. reversal) -- tanpa cap
        #    frekuensi harian (keputusan owner 2026-09-08)
        if last_entry_ts is not None and T - last_entry_ts < cooldown_sec:
            rejected.append({"ts": T, "reason": "cooldown", "decision": direction})
            continue

        # 4) fill next-bar-open + delay (P0-03 opsi A). Bila bar hasil geser
        #    tidak ada (akhir dataset) → rejection eksplisit.
        fill_T = T + delay_bars * BAR_SECONDS
        fill_bar = by_time.get(fill_T)
        if fill_bar is None:
            rejected.append({"ts": T, "reason": "delay_no_bar", "decision": direction})
            continue
        entry_bar = fill_bar
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
            "direction": direction, "entry_ts": fill_T, "entry": entry,
            "sl_price": sl_price, "tp_price": tp_price,
            "sl_points": rec["sl_points"], "tp_points": rec["tp_points"],
            "lot": rec["lot"], "signal_ts": T,
            "state_label": "LONG" if direction == "BUY" else "SHORT",
            "scan_from": fill_T,
        }
        state = open_pos["state_label"]
        last_entry_ts = T

    # Final sweep: scan sisa bar setelah record terakhir, lalu EOD_MARK bila
    # masih terbuka (dilabeli).
    if open_pos is not None:
        closed = close_scan(open_pos, ordered[-1])
        if closed is not None:
            trades.append(closed)
        else:
            trades.append(mark_to_market(open_pos, ordered[-1], "EOD_MARK"))
            n_eod += 1
        open_pos = None
        state = "FLAT"

    executed = len(trades)
    gross = sum(t["gross_usd"] for t in trades)
    costs = sum(t["cost_usd"] for t in trades)
    net = sum(t["net_usd"] for t in trades)
    return {
        "cost_label": cost["label"],
        "spread_model": {"entry_spread_points": cost["entry_spread_points"],
                         "exit_spread_points": cost["exit_spread_points"],
                         "slippage_points": cost["slippage_points"],
                         "delay_bars": cost["delay_bars"],
                         "commission_usd_per_lot": comm,
                         "point_value_usd_per_lot": pv,
                         "point_price": point_price,
                         "broker_meta_hash": meta_hash},
        "state_machine": "ONE_POSITION_ONLY",
        "position_state": state,
        "state_transitions": {"reversals": n_reversals, "eod_marks": n_eod},
        "executed_trades": executed,
        "rejected_executions": rejected,
        "trades": trades,
        "gross_usd": round(gross, 4),
        "total_costs_usd": round(costs, 4),
        "net_usd": round(net, 4),
        "expectancy_gross_usd": round(gross / executed, 4) if executed else 0.0,
        "expectancy_net_usd": round(net / executed, 4) if executed else 0.0,
    }


# ─── Funnel completeness (Pagar 6) ───────────────────────────────────────────

def build_funnel(records: list[dict], execution: dict | None) -> dict:
    """Ke mana semua kandidat trade hilang — harus terjawab penuh."""
    opp = len(records)
    invalid = [r for r in records if r["layer_a"] != "DATA_VALID"]
    valid = [r for r in records if r["layer_a"] == "DATA_VALID"]
    veto_by_gate = {}
    veto_combos = {}
    for r in valid:
        fv = r["first_veto_reason"]
        if fv:
            gate = fv.split(":")[0]
            veto_by_gate[gate] = veto_by_gate.get(gate, 0) + 1
            veto_combos[fv] = veto_combos.get(fv, 0) + 1
    # kombinasi veto penuh (semua gate gagal bersama)
    full_results = [tuple(sorted(r["all_gate_results"].items())) for r in valid]
    distinct_states = len(set(full_results))
    signals = [r for r in valid if r["decision"] in ("BUY", "SELL")]
    vetoed = sum(1 for r in valid if r["first_veto_reason"])
    funnel = {
        "evaluation_opportunities": opp,
        "data_invalid": len(invalid),
        "data_invalid_by_reason": _count([r["layer_a"] for r in invalid]),
        "layer_b_evaluated": len(valid),
        "veto_by_gate": veto_by_gate,
        "veto_by_first_reason": veto_combos,
        "distinct_gate_states": distinct_states,
        "final_signals": len(signals),
        "signals_by_direction": _count([r["decision"] for r in signals]),
        "wait": len(valid) - vetoed - len(signals),
    }
    if execution is not None:
        funnel.update({
            "executed_trades": execution["executed_trades"],
            "rejected_executions": len(execution["rejected_executions"]),
            "rejected_execution_reasons": _count([x["reason"] for x in execution["rejected_executions"]]),
            "gross_expectancy_usd": execution["expectancy_gross_usd"],
            "total_costs_usd": execution["total_costs_usd"],
            "net_expectancy_usd": execution["expectancy_net_usd"],
            "gross_usd": execution["gross_usd"],
            "net_usd": execution["net_usd"],
            "cost_label": execution["cost_label"],
        })
    return funnel


def _count(seq: list) -> dict:
    out = {}
    for s in seq:
        out[str(s)] = out.get(str(s), 0) + 1
    return out


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _preflight_calendar_provenance(calendar: dict | None, m5: list) -> None:
    """Pre-flight (saran post-audit): gagal CEPAT bila snapshot kalender
    postdates window evaluasi — tanpa ini replay menghasilkan funnel 100%
    veto B1 yang valid secara formal tapi tidak informatif. archived artifact
    (availability dinyatakan sebelum window) dilewati."""
    if not calendar or calendar.get("archived"):
        return
    info_at = calendar.get("information_available_at")
    if info_at is None:
        return  # fail-closed di B1 per-bar; bukan kasus pre-flight
    last_eval = int(m5[-1]["time"]) + BAR_SECONDS if m5 else 0
    if int(info_at) > last_eval:
        raise ValueError(
            f"PRE-FLIGHT GAGAL: snapshot kalender di-fetch {int(info_at)} "
            f"(SETELAH window evaluasi berakhir {last_eval}) — replay historis "
            "akan 100% veto B1. Fetch kalender SEBELUM window, atau pakai "
            "artifact arsip ber-provenance (save_calendar_artifact).")


def run_profile(profile_id: str, m5_path: str, m15_path: str, calendar_path: str | None,
                out_dir: Path, balance: float = 1136.65, with_execution: bool = True,
                bridge_account: dict | None = None,
                disable_gates: tuple = ()) -> dict:
    m5 = load_candles(m5_path)
    m15 = load_candles(m15_path)
    qualification = qualify_dataset(m5, m15)
    dhash = registry.dataset_hash({"m5": m5, "m15": m15})
    profile_cfg = registry.load_profile(profile_id)
    reg_data = registry.load_hypothesis_registry()
    calendar = load_calendar(calendar_path)
    cal_hash = calendar_artifact_hash(calendar_path) if calendar else None
    # E-2: broker meta dari snapshot /account bridge (file, deterministik —
    # engine TIDAK memanggil bridge live). Tanpa snapshot → FALLBACK (lama).
    meta = bm.load_broker_meta(bridge_account or {})
    chash = registry.compute_config_hash(profile_cfg, reg_data,
                                         calendar_artifact_hash=cal_hash,
                                         broker_meta_hash=bm.broker_meta_hash(meta))
    _preflight_calendar_provenance(calendar, m5)

    # F1b/E-2: unit spread bridge = PRICE_1E4 (spread "1700" = 0.17 harga =
    # 17 poin 0.01). Unit dideklarasi EKSPLISIT di sini — satu-satunya tempat
    # normalisasi; replay menerima poin yang SUDAH dinormalisasi.
    # Fallback broker meta (bridge belum expose symbol_info) → label FALLBACK
    # tercatat di broker_meta + hash masuk config_hash (Pagar 1).
    cfg = {"config_hash": chash, "dataset_hash": dhash, "balance": balance,
           "risk_percent": profile_cfg["risk"]["risk_percent"],
           "spread_points": bm.normalize_spread(1700.0, bm.PRICE_1E4)}
    records = run_decision_replay(m5, m15, profile_cfg, reg_data, calendar, cfg,
                                  disable_gates=disable_gates)
    execution = (run_execution_replay(records, m5, profile_cfg,
                                      spread_points=cfg["spread_points"],
                                      broker_meta=meta,
                                      spread_label="ESTIMATED_COST_MODEL")
                 if with_execution else None)

    funnel = build_funnel(records, execution)

    out_dir.mkdir(parents=True, exist_ok=True)
    dec_path = out_dir / f"decision_{profile_id.lower()}.jsonl"
    with open(dec_path, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True, ensure_ascii=True) + "\n")

    summary = {
        "profile_id": profile_cfg["profile_id"],
        "strategy_version": registry.STRATEGY_VERSION,
        "config_hash": chash,
        "dataset_hash": dhash,
        "broker_meta": {**meta, "hash": bm.broker_meta_hash(meta)},
        "qualification": qualification,
        "calendar_source": "ff_calendar_thisweek.json (real)" if calendar else "unavailable (B1 fail-closed)",
        "calendar_artifact_hash": cal_hash,
        "information_available_at": (calendar or {}).get("information_available_at"),
        "funnel": funnel,
        "execution": {k: v for k, v in (execution or {}).items() if k != "trades"},
    }
    with open(out_dir / f"summary_{profile_id.lower()}.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True, ensure_ascii=True)
    return {"records": records, "execution": execution, "summary": summary,
            "decision_log_path": str(dec_path)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Strategy v2 deterministic replay (P0-P2)")
    ap.add_argument("--profile", required=True, choices=["scalp", "micro"])
    ap.add_argument("--m5", required=True)
    ap.add_argument("--m15", required=True)
    ap.add_argument("--calendar", default=None)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--balance", type=float, default=1136.65)
    ap.add_argument("--bridge-account", default=None,
                    help="Snapshot JSON GET /account bridge (deterministik; "
                         "tanpa ini → broker meta FALLBACK)")
    ap.add_argument("--validate", action="store_true",
                    help="Validasi seluruh record JSONL terhadap decision_log.schema.json (P1-03)")
    args = ap.parse_args(argv)
    bridge_account = None
    if args.bridge_account:
        bridge_account = json.loads(Path(args.bridge_account).read_text(encoding="utf-8"))
    res = run_profile(args.profile, args.m5, args.m15, args.calendar, Path(args.out),
                      args.balance, bridge_account=bridge_account)
    s = res["summary"]
    print(json.dumps(s["funnel"], indent=2))
    print(f"decision log: {res['decision_log_path']}")
    if args.validate:
        from . import schema_check
        n, errs = schema_check.validate_jsonl(res["decision_log_path"])
        if errs:
            print(f"SCHEMA VIOLATIONS: {len(errs)} (contoh: {errs[:3]})")
            return 1
        print(f"schema validation: {n} records OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
