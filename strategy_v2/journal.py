"""Step 7 — JournalLoop (Analyst Desk v2.5, plan C1).

plan → paper → outcome → review. Append-only JSONL: baris HANYA ditambah
(dilarang mengubah/menghapus baris lama — dilarang hard-replace file; ada test
yang membaca file antara operasi). Runtime path:
  data/research/v2_replay/journal_<profile>.jsonl

Format baris (deterministik; market timestamp saja — Pagar 4):
  open : {evt:"open",  plan_id, ts, price, direction, tier, paper:true, plan}
  close: {evt:"close", plan_id, ts, price, reason, pnl_points, pnl_usd,
          rr_realized, held_bars, bucket_key}

review() agregat per (profile, direction, pattern, score_band): n, win_rate,
avg_rr, expectancy — format kompatibel data/learning/buckets.json ({n, win, pts,
pnl, updated}) supaya dua sistem belajar dari satu format.

PURE terhadap keputusan: journal TIDAK PERNAH mengubah decision/gate (layer
separation — ia hanya pembaca record & penulis buku besar paper). Win =
pnl > 0 (kontrak are/learning.py).
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PKG_DIR.parent
DEFAULT_DIR = PROJECT_ROOT / "data" / "research" / "v2_replay"

_lock = threading.Lock()

# Skor band review (dari tiers H-SCORE-DESK-01; band = half-open [lo, hi))
SCORE_BANDS = (("PAST", 0, 40), ("WATCH", 40, 60), ("PAPER", 60, 75), ("TRADE", 75, 101))


def score_band(total) -> str:
    """Band skor deterministik utk grouping review."""
    t = float(total) if isinstance(total, (int, float)) and not isinstance(total, bool) else 0.0
    for name, lo, hi in SCORE_BANDS:
        if lo <= t < hi:
            return name
    return "PAST"


def bucket_key(entry: dict) -> str:
    """Kunci agregasi review: <profile>|<direction>|p_<pattern[:30]>|b_<band>.
    Format kompatibel gaya data/learning/buckets.json (pipe-separated)."""
    plan = entry.get("plan") or {}
    score = plan.get("setup_score") or {}
    pattern = str((plan.get("trigger") or {}).get("pattern") or "none")[:30]
    return "|".join([
        str(entry.get("profile") or plan.get("profile_id") or "?"),
        str(plan.get("direction") or "?"),
        "p_" + pattern,
        "b_" + score_band(score.get("total", 0)),
    ])


def journal_path(profile: str, out_dir: str | Path | None = None) -> Path:
    d = Path(out_dir) if out_dir else DEFAULT_DIR
    return d / f"journal_{str(profile).lower()}.jsonl"


def open_paper_trade(plan: dict, fill_ts: int, fill_price: float,
                     profile: str = "?", out_dir: str | Path | None = None) -> dict:
    """Catat OPEN paper trade (paper:true) — dipanggil execution replay saat
    tier PAPER/TRADE di paper mode. Append satu baris; return entry context."""
    if not isinstance(plan, dict) or not plan.get("plan_id"):
        raise ValueError("open_paper_trade: plan wajib dict dengan plan_id")
    entry = {
        "plan_id": str(plan["plan_id"]),
        "profile": str(profile),
        "direction": plan.get("direction"),
        "tier": plan.get("tier"),
        "score_total": (plan.get("setup_score") or {}).get("total", 0),
        "fill_ts": int(fill_ts),
        "fill_price": float(fill_price),
        "plan": plan,   # diperlukan close_paper_trade (stop, bucket, dsb.)
    }
    rec = {
        "evt": "open", "plan_id": entry["plan_id"], "ts": int(fill_ts),
        "price": float(fill_price), "direction": entry["direction"],
        "tier": entry["tier"], "paper": True, "profile": entry["profile"],
        "plan": plan,
    }
    _append(journal_path(profile, out_dir), rec)
    return entry


def close_paper_trade(entry: dict, exit_ts: int, exit_price: float, reason: str,
                      point_value_usd_per_lot: float = 1.0, lot: float = 0.01,
                      out_dir: str | Path | None = None) -> dict:
    """Catut CLOSE + outcome (pnl_points, rr_realized, held_bars) + update bucket
    agregat (baris agregat juga append-only: evt=close membawa bucket final)."""
    if not isinstance(entry, dict) or not entry.get("plan_id"):
        raise ValueError("close_paper_trade: entry wajib dari open_paper_trade")
    plan = entry.get("plan") or {}
    stop = plan.get("stop_points") or 0.0
    direction = entry.get("direction")
    pnl_points = (float(exit_price) - float(entry["fill_price"])) if direction == "BUY" \
        else (float(entry["fill_price"]) - float(exit_price))
    rr = round(pnl_points / stop, 4) if stop and stop > 0 else None
    pnl_usd = round(pnl_points * float(point_value_usd_per_lot) * float(lot), 4)
    win = 1 if pnl_usd > 0 else 0
    rec = {
        "evt": "close", "plan_id": entry["plan_id"], "ts": int(exit_ts),
        "price": float(exit_price), "reason": str(reason),
        "pnl_points": round(pnl_points, 2), "pnl_usd": pnl_usd,
        "rr_realized": rr, "held_bars": max(0, int(exit_ts) - int(entry["fill_ts"])),
        "bucket_key": bucket_key(entry), "win": win, "paper": True,
        "profile": entry.get("profile", "?"),
    }
    _append(journal_path(entry.get("profile", "?"), out_dir), rec)
    return rec


def _append(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, sort_keys=True, ensure_ascii=True)
    with _lock:
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write(line + "\n")


def read_journal(path: str | Path) -> list[dict]:
    out = []
    p = Path(path)
    if not p.exists():
        return out
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def review(journal_path_or_entries, min_n: int = 1) -> dict:
    """Agregat per bucket_key: n, win, win_rate, avg_rr, expectancy (avg net USD
    per trade) — format kompatibel data/learning/buckets.json:
    {key: {n, win, pts, pnl, updated, win_rate, avg_rr, expectancy, band}}.
    PURE: terima path journal ATAU list baris (untuk test & reuse)."""
    rows = journal_path_or_entries
    if isinstance(rows, (str, Path)):
        rows = read_journal(rows)
    buckets: dict[str, dict] = {}
    opens: dict[str, dict] = {}
    last_ts = 0
    for rec in rows or []:
        evt = rec.get("evt")
        if evt == "open":
            opens[rec.get("plan_id")] = rec
        elif evt == "close":
            key = rec.get("bucket_key") or "?"
            b = buckets.get(key) or {"n": 0, "win": 0, "pts": 0.0, "pnl": 0.0, "updated": 0}
            b["n"] += 1
            b["win"] += int(rec.get("win", 0))
            b["pts"] = round(b["pts"] + float(rec.get("pnl_points") or 0.0), 4)
            b["pnl"] = round(b["pnl"] + float(rec.get("pnl_usd") or 0.0), 4)
            b["updated"] = int(rec.get("ts") or 0)
            rr = rec.get("rr_realized")
            b.setdefault("_rr_sum", 0.0)
            b.setdefault("_rr_n", 0)
            if rr is not None:
                b["_rr_sum"] += float(rr)
                b["_rr_n"] += 1
            buckets[key] = b
            last_ts = max(last_ts, int(rec.get("ts") or 0))
    out: dict[str, dict] = {}
    for key, b in buckets.items():
        n = b.pop("_rr_n", 0)
        rr_sum = b.pop("_rr_sum", 0.0)
        b["win_rate"] = round(b["win"] / b["n"], 4) if b["n"] else 0.0
        b["avg_rr"] = round(rr_sum / n, 4) if n else None
        b["expectancy"] = round(b["pnl"] / b["n"], 4) if b["n"] else 0.0
        b["band"] = key.rsplit("b_", 1)[-1]
        if b["n"] >= min_n:
            out[key] = b
    return out


def review_by_tier(journal_path_or_entries) -> dict:
    """Expectancy per TIER (kontrak plan §Risiko-4): kalau PAPER expectancy <= 0,
    tier PAPER dinonaktifkan — keputusan owner dari data (review report)."""
    rows = journal_path_or_entries
    if isinstance(rows, (str, Path)):
        rows = read_journal(rows)
    per_tier: dict[str, dict] = {}
    for rec in rows or []:
        if rec.get("evt") != "close":
            continue
        t = str(rec.get("tier") or (rec.get("bucket_key") or "").rsplit("b_", 1)[-1] or "?")
        d = per_tier.get(t) or {"n": 0, "win": 0, "pnl": 0.0}
        d["n"] += 1
        d["win"] += int(rec.get("win", 0))
        d["pnl"] = round(d["pnl"] + float(rec.get("pnl_usd") or 0.0), 4)
        per_tier[t] = d
    for t, d in per_tier.items():
        d["win_rate"] = round(d["win"] / d["n"], 4) if d["n"] else 0.0
        d["expectancy"] = round(d["pnl"] / d["n"], 4) if d["n"] else 0.0
    return per_tier
