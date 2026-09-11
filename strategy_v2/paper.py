"""C1 wiring — Paper simulator driver (Analyst Desk v2.5).

Menjawab open question plan §1: tier PAPER dijalankan OTOMATIS di research
plane (tanpa biaya) — approval manual hanya untuk live. Semua angka eksekusi
dari simulator kontrak F1b yang SAMA (run_execution_replay — next-bar-open,
BID/ASK, cost model, state machine) → journal = truth yang konsisten dengan
backtest; TIDAK ada simulator kedua (anti cost-soup).

Deterministik (Pagar 4): input sama → journal byte-identik. Layer separation:
modul ini HANYA MEMBACA records — decision gate tidak dipanggil/diubah.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import broker_meta as bm
from .journal import (close_paper_trade, journal_path, open_paper_trade,
                      read_journal, review, review_by_tier)
from .replay import BAR_SECONDS, run_execution_replay
from .review_report import build_review_report

PAPER_TIERS = ("PAPER", "TRADE")   # tier yang di-paper-trade otomatis


def _cooldown_ok(prev_signal_ts: int | None, ts: int, cooldown_minutes: int) -> bool:
    if prev_signal_ts is None:
        return True
    return (ts - prev_signal_ts) >= cooldown_minutes * 60


def run_paper_desk(records: list[dict], m5: list, profile: dict,
                   spread_points: float | None = None,
                   broker_meta: dict | None = None,
                   spread_label: str = "ESTIMATED_COST_MODEL",
                   out_dir: str | Path | None = None,
                   tiers: tuple = PAPER_TIERS,
                   with_full_execution_metrics: bool = True) -> dict:
    """PAPER tier → simulator eksekusi yang sama → journal append-only.

    Return: {papered, opened, closed, trades_preview, review, review_by_tier,
    journal_path, execution_metrics}.
    """
    profile_id = profile.get("profile_id", "?")
    meta = broker_meta if broker_meta is not None else bm.load_broker_meta({})
    pv = bm.point_value_usd_per_lot(meta)
    cooldown = (profile.get("risk") or {}).get("cooldown_minutes", 0)

    # 0) sinyal PAPER-tier (keputusan gate tetap sumber arah — B3 bias/decision)
    signals = [r for r in records
               if (r.get("setup_score") or {}).get("tier") in tiers
               and (r.get("decision") in ("BUY", "SELL")
                    or (r.get("bias") in ("BUY_ONLY", "SELL_ONLY") and r.get("risk_calc")))]

    # 1) jalankan simulator kontrak F1b atas sinyal terpilih (SALINAN record —
    #    asli tak disentuh) → trades & metrik konsisten dgn backtest.
    sig_ts = {s["evaluation_timestamp"] for s in signals}
    sim_records: list[dict] = []
    for r in records:
        if r["evaluation_timestamp"] not in sig_ts:
            continue
        direction = r.get("decision")
        if direction not in ("BUY", "SELL"):
            direction = "BUY" if r.get("bias") == "BUY_ONLY" else "SELL"
        rr = r.get("risk_calc") or {}
        sim_records.append({**r, "decision": direction,
                            "sl_points": float(rr.get("sl_points") or 0.0),
                            "tp_points": float(rr.get("tp_points") or 0.0)})
    # cooldown antar sinyal PAPER (aturan B7 yang sama, diterapkan eksplisit)
    last_ts = None
    spaced: list[dict] = []
    for s in sim_records:
        if _cooldown_ok(last_ts, s["evaluation_timestamp"], cooldown):
            spaced.append(s)
            last_ts = s["evaluation_timestamp"]
    execution = run_execution_replay(
        spaced, m5, profile, spread_points=spread_points, broker_meta=meta,
        spread_label=spread_label) if spaced else None

    # 2) tulis journal (append-only) dari trades simulator
    by_time = {int(b["time"]): b for b in m5}
    n_open = n_close = 0
    for t in (execution or {}).get("trades", []):
        sig = next((s for s in spaced if s["evaluation_timestamp"] == t["signal_ts"]), None)
        if sig is None or not sig.get("trade_plan"):
            continue
        plan = sig["trade_plan"]
        fill_ts = int(t["entry_ts"])
        entry = open_paper_trade(plan, fill_ts, float(t["entry"]),
                                 profile=profile_id, out_dir=out_dir)
        n_open += 1
        close_paper_trade(entry, int(t["exit_ts"]), float(t["exit"]), t["exit_reason"],
                          point_value_usd_per_lot=pv, lot=float(t["lot"]),
                          out_dir=out_dir)
        n_close += 1

    jp = journal_path(profile_id, out_dir)
    return {
        "papered": len(spaced),   # setelah filter cooldown (bukan jumlah sinyal mentah)
        "opened": n_open,
        "closed": n_close,
        "journal_path": str(jp),
        "review": review(jp),
        "review_by_tier": review_by_tier(jp),
        "execution_metrics": ({k: v for k, v in execution.items() if k != "trades"}
                              if (execution and with_full_execution_metrics) else None),
    }
