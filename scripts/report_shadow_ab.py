"""Laporan perbandingan A/B LIVE: GATE ON (trade nyata) vs TANPA GATE (shadow).

Membaca:
  - data/learning/trade_memory.jsonl  -> trade nyata (gate candle V2 ON)
  - data/learning/shadow_ab.jsonl     -> shadow 'tanpa gate' (paper)
Menampilkan per style: n, win rate, poin gross, poin net (spread 18),
ekspektasi/trade, break-down alasan exit. Tanpa MT5.

Pemakaian: python scripts/report_shadow_ab.py
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEM = os.path.join(BASE, "data", "learning")
SPREAD = 18.0

def load_lines(path):
    out = []
    if not os.path.exists(path):
        return out
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except Exception:
            pass
    return out

def actual_stats():
    """Trade nyata dari trade_memory.jsonl (open+close dipasangkan)."""
    rows = load_lines(os.path.join(MEM, "trade_memory.jsonl"))
    opens = {}
    closes = []
    for r in rows:
        if r.get("evt") == "open":
            opens[r["ticket"]] = r
        elif r.get("evt") == "close" and r["ticket"] in opens:
            o = opens[r["ticket"]]
            lot = o.get("lot") or 0.01
            closes.append({
                "style": o.get("style"), "win": r.get("win"),
                "pts": (r.get("pnl") or 0) / lot,   # $ / lot = poin (XAUUSD)
                "reason": r.get("close_reason"),
            })
    return closes

def shadow_stats():
    rows = load_lines(os.path.join(MEM, "shadow_ab.jsonl"))
    opens = {}
    closes = []
    for r in rows:
        if r.get("evt") == "open":
            opens.setdefault(r["style"], []).append(r)
        elif r.get("evt") == "close":
            closes.append(r)
    # pasangkan berurutan per style (FIFO) utk statistik (open punya entry/sl/tp)
    return closes

def summarize(rows, spread):
    n = len(rows)
    if not n:
        return {"n": 0}
    wins = sum(1 for r in rows if r.get("win"))
    gross = sum(r.get("pts") or 0 for r in rows)
    net = gross - spread * n
    reasons = {}
    for r in rows:
        reasons[r.get("reason") or "?"] = reasons.get(r.get("reason") or "?", 0) + 1
    return {"n": n, "winrate": wins / n * 100, "gross": gross, "net": net,
            "expect": net / n, "reasons": reasons}

def fmt(tag, s):
    if not s["n"]:
        print("  %-16s n=0 (belum ada sampel)" % tag)
        return
    print("  %-16s n=%-5d winrate=%6.1f%%  gross=%+9.0f pt  net18=%+9.0f pt  expect/trade=%+7.1f pt  exit=%s"
          % (tag, s["n"], s["winrate"], s["gross"], s["net"], s["expect"], s["reasons"]))

def main():
    actual = actual_stats()
    shadow = shadow_stats()
    print("=" * 100)
    print("A/B LIVE — GATE CANDLE V2 (nyata) vs TANPA GATE (shadow).")
    print("Nyata: poin sudah NET (pnl/lot, termasuk spread). Shadow: gross; net18 = gross - 18 pt.")
    print("=" * 100)
    for style in ("micro", "scalp"):
        print("── %s ──" % style.upper())
        fmt("GATE ON (nyata)", summarize([r for r in actual if r["style"] == style], 0))
        fmt("TANPA GATE (shadow)", summarize([r for r in shadow if r.get("style") == style], SPREAD))
    print("=" * 100)
    print("Catatan: shadow dibuka hanya saat gate MEMBLOKIR (TA lolos, candle belum siap);")
    print("resolusi harga 1 detik; shadow tdk kena max_positions; hasil awal bisa bias rendah")
    print("karena shadow yang masih terbuka belum dihitung.")

if __name__ == "__main__":
    main()
