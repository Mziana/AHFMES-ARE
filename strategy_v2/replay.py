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
from pathlib import Path

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
    return {"status": "ok" if events else "empty",
            "information_available_at": info_at, "events": events,
            "archived": True}  # artifact arsip: availability dinyatakan eksplisit


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
                        calendar: dict | None, config: dict) -> list[dict]:
    """Satu record JSONL per M5 CLOSED bar T. Slice bars[0..T] dulu → gates.

    Deterministik: tidak ada now(); urutan & konten hanya fungsi input.
    """
    prof_a = profile["layer_a"]
    cfg = {
        "now_ts": 0,
        "rsi_bias_threshold": registry.hypothesis(registry_dict, "H-RSI-BIAS-01")["value"]["rsi_threshold"],
        "min_bars_m15_warmup": registry.hypothesis(registry_dict, "H-Q1")["value"]["min_bars_m15_warmup"],
        "layer_a": prof_a,
        "calendar": calendar or {"status": "down", "events": []},
        "ticks_meta": {"spread_points": config.get("spread_points")},  # None → cek spread dilewati
        "risk_state": {},   # diupdate oleh eksekusi (dipakai saat gabungan)
    }
    records: list[dict] = []
    m15_times = [b["time"] for b in m15]

    for bar in m5:
        T = int(bar["time"]) + BAR_SECONDS          # evaluation time = bar CLOSE
        m5_slice = [b for b in m5 if int(b["time"]) + BAR_SECONDS <= T]
        m15_slice = [b for b in m15 if int(b["time"]) + 900 <= T]
        if int(m5_slice[-1]["time"]) + BAR_SECONDS != T:
            continue  # bar T belum closed pada T (tidak mungkin utk loop ini)
        c = dict(cfg)
        c["now_ts"] = T
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
            "decision": decision,
            "sl_points": sl_points,
            "tp_points": tp_points,
            "lot": lot,
            "market_snapshot": diag["market_snapshot"],
        })
    return records


# ─── Execution Replay (next-bar-open + cost model) ───────────────────────────

def run_execution_replay(records: list[dict], m5: list, profile: dict,
                         spread_points: float | None = None) -> dict:
    """Decision → simulator next-bar-open + cost model → trades + PnL.

    Kontrak eksekusi: sinyal @ close T → fill paling awal = OPEN bar dengan
    open time == T (bar T+1 dari sisi sinyal). Eksekusi lebih awal = violation.
    Intrabar ambiguity (SL & TP kena bar yang sama) → SL dulu (konservatif).
    """
    cost = compute_cost(spread_points, spread_points)
    spread_pts = cost["entry_spread_points"]
    price_mult = 0.01  # 1 poin XAUUSD = 0.01 harga

    by_time = {int(b["time"]): b for b in m5}
    ordered = sorted(by_time.keys())
    trades = []
    rejected = []
    risk = profile["risk"]
    last_entry_ts = None

    for rec in records:
        T = rec["evaluation_timestamp"]
        if rec["decision"] not in ("BUY", "SELL"):
            continue
        # cooldown enforcement di sisi eksekusi (tanpa cap frekuensi harian —
        # keputusan owner 2026-09-08: max_trades_per_day dihapus)
        if last_entry_ts is not None and T - last_entry_ts < risk["cooldown_minutes"] * 60:
            rejected.append({"ts": T, "reason": "cooldown", "decision": rec["decision"]})
            continue
        entry_bar = by_time.get(T)
        if entry_bar is None:
            rejected.append({"ts": T, "reason": "no_next_bar", "decision": rec["decision"]})
            continue

        direction = rec["direction"] = rec["decision"]
        # BUY fill di ask = open + spread; SELL fill di bid = open − spread
        entry = entry_bar["open"] + (spread_pts * price_mult if direction == "BUY" else -spread_pts * price_mult)
        sl_d = rec["sl_points"] * price_mult
        tp_d = rec["tp_points"] * price_mult
        if direction == "BUY":
            sl_price, tp_price = entry - sl_d, entry + tp_d
        else:
            sl_price, tp_price = entry + sl_d, entry - tp_d

        # cari exit mulai bar ENTRY sendiri (fill di open, kelola sejak bar itu)
        exit_ts, exit_price, exit_reason = None, None, None
        idx = ordered.index(T)
        for t in ordered[idx:]:
            b = by_time[t]
            if direction == "BUY":
                hit_sl = b["low"] <= sl_price
                hit_tp = b["high"] >= tp_price
            else:
                hit_sl = b["high"] >= sl_price
                hit_tp = b["low"] <= tp_price
            if hit_sl:  # konservatif: SL dulu saat ambiguity
                exit_ts, exit_price, exit_reason = t + BAR_SECONDS, sl_price, "SL"
                break
            if hit_tp:
                exit_ts, exit_price, exit_reason = t + BAR_SECONDS, tp_price, "TP"
                break
        if exit_ts is None:
            # akhir dataset → mark-to-market pada close bar terakhir (dilabeli)
            b = m5[-1]
            exit_ts, exit_price, exit_reason = b["time"] + BAR_SECONDS, b["close"], "EOD_MARK"

        pts = (exit_price - entry) if direction == "BUY" else (entry - exit_price)
        pts *= 100.0  # harga → poin
        gross_usd = pts * rec["lot"] * 1.0
        total_cost_usd = cost["total_usd_per_lot"] * rec["lot"]
        net_usd = gross_usd - total_cost_usd
        trades.append({
            "entry_ts": T, "exit_ts": exit_ts, "direction": direction,
            "entry": entry, "exit": exit_price, "exit_reason": exit_reason,
            "sl_points": rec["sl_points"], "tp_points": rec["tp_points"],
            "lot": rec["lot"], "gross_points": round(pts, 2),
            "gross_usd": round(gross_usd, 4),
            "cost_usd": round(total_cost_usd, 4),
            "net_usd": round(net_usd, 4),
            "cost_label": cost["label"],
        })
        last_entry_ts = T

    executed = len(trades)
    gross = sum(t["gross_usd"] for t in trades)
    costs = sum(t["cost_usd"] for t in trades)
    net = sum(t["net_usd"] for t in trades)
    return {
        "cost_label": cost["label"],
        "spread_model": {"entry_spread_points": cost["entry_spread_points"],
                         "exit_spread_points": cost["exit_spread_points"],
                         "commission_usd_per_lot": cost["commission_usd_per_lot"]},
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

def run_profile(profile_id: str, m5_path: str, m15_path: str, calendar_path: str | None,
                out_dir: Path, balance: float = 1136.65, with_execution: bool = True) -> dict:
    m5 = load_candles(m5_path)
    m15 = load_candles(m15_path)
    qualification = qualify_dataset(m5, m15)
    dhash = registry.dataset_hash({"m5": m5, "m15": m15})
    profile_cfg = registry.load_profile(profile_id)
    reg_data = registry.load_hypothesis_registry()
    calendar = load_calendar(calendar_path)
    cal_hash = calendar_artifact_hash(calendar_path) if calendar else None
    chash = registry.compute_config_hash(profile_cfg, reg_data, calendar_artifact_hash=cal_hash)

    cfg = {"config_hash": chash, "dataset_hash": dhash, "balance": balance,
           "risk_percent": profile_cfg["risk"]["risk_percent"],
           "spread_points": None}
    records = run_decision_replay(m5, m15, profile_cfg, reg_data, calendar, cfg)
    execution = run_execution_replay(records, m5, profile_cfg) if with_execution else None
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
    args = ap.parse_args(argv)
    res = run_profile(args.profile, args.m5, args.m15, args.calendar, Path(args.out), args.balance)
    s = res["summary"]
    print(json.dumps(s["funnel"], indent=2))
    print(f"decision log: {res['decision_log_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
