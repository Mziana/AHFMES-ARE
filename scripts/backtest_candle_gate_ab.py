"""
Backtest A/B — Gate Candle V2 (READY/WAITING/BLOCKED) vs Tanpa Gate
Micro & Scalp — data lokal XAUUSD (M1 + M5 + M15 parquet), tanpa MT5.

Sinyal arah (PROXY, identik untuk kedua varian):
    BUY  = EMA9>EMA21 pada M5 DAN M15 (2 TF setuju) & RSI(M5) < 75
    SELL = EMA9<EMA21 pada M5 DAN M15 & RSI(M5) > 25
    (Proxy trend 2-TF — BUKAN replikasi penuh analyzeMarket 13-indikator;
     valid untuk mengukur EFEK RELATIF gate karena sinyal identik antar varian.)

Varian:
  A. TANPA GATE : entry begitu sinyal aktif (bot lama menunggu MTF 2/2 saja).
  B. GATE V2    : entry hanya saat candle setup READY (rubrik: streak M1/M5,
                  body lawan besar M15, pola pembalikan). WAITING/BLOCKED -> tunggu
                  sampai READY; bila sinyal hilang dulu -> batal.
Exit: SL/TP intrabar (konservatif: SL didahulukan bila satu bar kena dua-duanya),
      reversal saat sinyal berlawanan setelah min-hold, cooldown 120 dtk antar entry.

SL/TP per style: micro SL=1xATR(M5) TP=150 tetap; scalp SL=1xATR(M5)
TP=max(150,2xATR). $ = poin x lot; lot = min(maxLot, riskUSD/SLpts),
risk 1%. Net = gross - 35 poin spread per trade (2 sisi, spread rata2).
"""
import json, math, os, sys, glob
import polars as pl

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "market_data")
MEM_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "learning")

T0 = 1733011200      # 2024-12-01 — biarkan warmup indikator 3 bulan pertama file 2024-09-01
T1 = 1787875200      # 2026-08-31 00:00 UTC (M15 berakhir 2026-08-31 23:55 -> pakai batas ini)

SPREAD_PTS = float(os.environ.get("BT_SPREAD", "35"))  # 35 = rata2 hist; set 18 utk spread Finex hari ini

# ─── INDIKATOR (port numpy cepat) ─────────────────────────────────────────────

def ema(arr, period):
    import numpy as np
    a = np.asarray(arr, dtype=float)
    out = np.full(len(a), np.nan)
    if len(a) < period: return out
    k = 2.0 / (period + 1)
    prev = a[:period].mean()
    out[period - 1] = prev
    for i in range(period, len(a)):
        prev = a[i] * k + prev * (1 - k)
        out[i] = prev
    return out

def rsi_series(closes, period=14):
    import numpy as np
    c = np.asarray(closes, dtype=float)
    n = len(c); out = np.full(n, np.nan)
    if n <= period: return out
    gains = np.maximum(np.diff(c), 0.0); losses = np.maximum(-np.diff(c), 0.0)
    ag = gains[:period].mean(); al = losses[:period].mean()
    for i in range(period, n):
        ag = (ag * (period - 1) + gains[i - 1]) / period
        al = (al * (period - 1) + losses[i - 1]) / period
        out[i] = 100.0 if al <= 0 else 100 - 100 / (1 + ag / al)
    return out

def atr_series(h, l, c, period=14):
    import numpy as np
    h = np.asarray(h, float); l = np.asarray(l, float); c = np.asarray(c, float)
    n = len(c); out = np.full(n, np.nan)
    if n <= period: return out
    pc = c[:-1]
    tr = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - pc), np.abs(l[1:] - pc)))
    a = tr[:period].mean()
    out[period] = a
    for i in range(period, n - 1):
        a = (a * (period - 1) + tr[i]) / period
        out[i + 1] = a
    return out

import numpy as np
from datetime import datetime, timezone

MAX_LOT = 0.10
MIN_LOT = 0.01
RISK_PCT = 1.0
EQUITY = 2000.0
COOLDOWN_S = 120.0
REV_MIN_HOLD_M5 = 3      # minimal 3 bar M5 (15 mnt) sebelum boleh exit reversal
HOLD_CAP_M5 = 144        # 12 jam: tutup paksa di close bar (agar simulasi terbatas)
TICK_USD = 1.0           # XAUUSD: 1 lot x 1 poin (0.01) = $1

# ─── LOAD & ALIGN ────────────────────────────────────────────────────────────
def load_ohlc(tf):
    files = sorted(glob.glob(os.path.join(DATA_DIR, f"XAUUSD_{tf}_*.parquet")))
    if not files:
        raise SystemExit(f"tidak ada parquet XAUUSD_{tf}")
    df = pl.read_parquet(files[0]).sort("timestamp")
    ts = df["timestamp"].to_numpy()
    return (ts, df["open"].to_numpy(), df["high"].to_numpy(),
            df["low"].to_numpy(), df["close"].to_numpy())

(m1t, m1o, m1h, m1l, m1c) = load_ohlc("M1")
(m5t, m5o, m5h, m5l, m5c) = load_ohlc("M5")
(m15t, m15o, m15h, m15l, m15c) = load_ohlc("M15")

# Simulasi hanya pada bar M5 dalam jendela [T0,T1); indikator di-warmup sejak file mulai.
w = (m5t >= T0) & (m5t < T1)
grid = np.nonzero(w)[0]
n = len(grid)
gts = m5t[grid]

ema9_5 = ema(m5c, 9); ema21_5 = ema(m5c, 21)
ema9_15 = ema(m15c, 9); ema21_15 = ema(m15c, 21)
rsi5 = rsi_series(m5c, 14)
atr5 = atr_series(m5h, m5l, m5c, 14)

# Proxy arah 2-TF (M5 & M15 setuju, RSI filter) — IDENTIK untuk kedua varian.
# Map M15 -> ruang indeks M5 (nilai M15 terakhir yg <= waktu bar M5)
j15_at_m5 = np.searchsorted(m15t, m5t, "right") - 1
j15_at_m5 = np.clip(j15_at_m5, 0, len(m15c) - 1)
m15up = (ema9_15 > ema21_15)[j15_at_m5]
dir_full = np.zeros(len(m5c), dtype=np.int8)
up5 = (ema9_5 > ema21_5) & (rsi5 < 75) & m15up
dn5 = (ema9_5 < ema21_5) & (rsi5 > 25) & ~m15up
dir_full[up5] = 1
dir_full[dn5] = -1
dir_g = dir_full[grid]

close_g = m5c[grid]
atr_g = atr5[grid]
ema21_g = ema21_5[grid]
up  = ema21_g > 0

# ─── RUBRIK CANDLE V2 (port persis dari UI/src/app/api/are/decision/route.ts) ─
# streak M1 dibatasi 3 di engine (live) — replikasi sama.
def streak(c, o, k, up_dir, maxn=3):
    cnt = 0
    j = k
    while j >= 0:
        if (c[j] > o[j]) == up_dir:
            cnt += 1
            if cnt >= maxn:
                break
            j -= 1
        else:
            break
    return cnt

def body_ratio_big(c, o, h, l, bear):
    rng = (h - l) or 1e-9
    body = abs(c - o)
    return (bear == (c < o)) and body / rng > 0.6

def mini_pattern_dir(c, o, h, l, k):
    """Pola pembalikan sederhana pada bar terakhir (indeks k) + bar sebelumnya.
    Kembali: tuple (nama, arah) atau None. (Subset kecil dari pustaka TS:
    engulfing, hammer, shooting star — cukup untuk membuka kunci WAITING/BLOCKED.)"""
    if k < 1:
        return None
    oc, oo, oh, ol = c[k - 1], o[k - 1], h[k - 1], l[k - 1]
    cc, co, ch, cl = c[k], o[k], h[k], l[k]
    if co < cc and oo > oc and cc >= oo and co <= oc:
        return ("engulfing_bull", "BUY")
    if co > cc and oo < oc and cc <= oo and co >= oc:
        return ("engulfing_bear", "SELL")
    rng = ch - cl or 1e-9
    body = abs(cc - co)
    up_wick = ch - max(cc, co)
    dn_wick = min(cc, co) - cl
    if cc > co and dn_wick >= 2 * body and up_wick <= body and body > 0:
        return ("hammer", "BUY")
    if cc < co and up_wick >= 2 * body and dn_wick <= body and body > 0:
        return ("shooting_star", "SELL")
    return None

# peta M1 -> posisi grid M5 terakhir (utk periksa exit & reversal per bar M1)
gidx_m1 = np.searchsorted(gts, m1t, "right") - 1
gidx_m1 = np.clip(gidx_m1, 0, n - 1)
dir_m1 = dir_g[gidx_m1]          # arah pada boundary terakhir yg sudah lewat

def m1_idx_at(gpos):
    """indeks bar M1 terakhir yang TUTUP tepat di boundary grid[gpos]."""
    return int(np.searchsorted(m1t, gts[gpos], "right") - 1)

def candle_setup(gpos, want_buy):
    """Rubrik V2: setup READY/WAITING/BLOCKED + skor 0-10. Miriplah route.ts."""
    k = m1_idx_at(gpos)               # bar M1 penutup boundary ini (== candle terakhir closed)
    k5 = int(grid[gpos])              # indeks penuh bar M5 ini
    up_dir = want_buy
    oppStreak = streak(m1c, m1o, k, not up_dir)
    sameStreak = streak(m1c, m1o, k, up_dir)
    m5OppStreak = streak(m5c, m5o, k5, not up_dir)
    m5SameStreak = streak(m5c, m5o, k5, up_dir)
    j15 = int(np.searchsorted(m15t, gts[gpos], "right") - 1)
    m15OppBig = j15 >= 0 and body_ratio_big(m15c[j15], m15o[j15], m15h[j15], m15l[j15], not up_dir)
    lastSame = k >= 0 and (m1c[k] > m1o[k]) == up_dir
    # pola pembalikan searah pada M1 atau M5
    p1 = mini_pattern_dir(m1c, m1o, m1h, m1l, k) if k >= 0 else None
    p5 = mini_pattern_dir(m5c, m5o, m5h, m5l, k5)
    want_s = 'BUY' if up_dir else 'SELL'
    rev = (p1 is not None and p1[1] == want_s) or (p5 is not None and p5[1] == want_s)
    # posisi vs EMA21 M5 + struktur pecah
    atEma = False
    if ema21_g[gpos] > 0:
        atEma = abs(close_g[gpos] - ema21_g[gpos]) / ema21_g[gpos] < 0.002
    breakOut = False
    if k5 >= 3:
        if up_dir:
            ref = max(m5h[k5 - 3], m5h[k5 - 2], m5h[k5 - 1])
            breakOut = m5c[k5] > ref
        else:
            ref = min(m5l[k5 - 3], m5l[k5 - 2], m5l[k5 - 1])
            breakOut = m5c[k5] < ref
    # skor 0-10
    sc = 0
    if sameStreak >= 1: sc += 3
    if m5SameStreak >= 1: sc += 2
    if sameStreak >= 2 and m5SameStreak >= 1: sc += 1
    if atEma: sc += 2
    if breakOut: sc += 2
    if rev: sc += 2
    if m15OppBig: sc -= 1
    if m5OppStreak >= 2: sc -= 2
    if oppStreak >= 2: sc -= 1
    sc = max(0, min(10, sc))
    hardContra = (oppStreak >= 4) or (m15OppBig and m5OppStreak >= 2 and not lastSame)
    contraWait = (oppStreak >= 2) or (m5OppStreak >= 2 and oppStreak >= 1) or (m15OppBig and oppStreak >= 1)
    if hardContra and not rev and not lastSame:
        return {"setup": "BLOCKED", "block": True, "score": sc}
    if contraWait and not rev and not lastSame:
        return {"setup": "WAITING", "block": True, "score": sc}
    return {"setup": "READY", "block": False, "score": sc,
            "at_ema": atEma, "break": breakOut, "rev": rev,
            "same1": sameStreak, "m5same": m5SameStreak}

# ─── SIMULASI ────────────────────────────────────────────────────────────────
def run_forward(entry_gpos, want_buy, sl_pts, tp_pts, rev_allowed, hold_cap_m5):
    """Scan bar M1 ke depan dari entri di boundary entry_gpos.
    SL/TP intrabar (SL didahulukan bila satu bar kena dua-duanya), reversal
    di boundary M5 setelah min-hold bila arah berlawanan, tutup paksa bila
    hold_cap_m5 tercapai. Kembali dict {pts, win, reason, ts, gpos_close}."""
    k = m1_idx_at(entry_gpos) + 1          # bar M1 pertama SETELAH entri
    if k >= len(m1t) - 1:
        return {"pts": 0, "win": 0, "reason": "end", "ts": gts[entry_gpos], "gpos": entry_gpos}
    slv = close_g[entry_gpos] - sl_pts * 0.01 if want_buy else close_g[entry_gpos] + sl_pts * 0.01
    tpv = close_g[entry_gpos] + tp_pts * 0.01 if want_buy else close_g[entry_gpos] - tp_pts * 0.01
    last_g = entry_gpos
    held = 0
    m = k
    while m < len(m1t) - 1 and m1t[m] < T1:
        hit = None
        if want_buy:
            if m1l[m] <= slv: hit = "SL"
            elif m1h[m] >= tpv: hit = "TP"
        else:
            if m1h[m] >= slv: hit = "SL"
            elif m1l[m] <= tpv: hit = "TP"
        if hit:
            pts = -sl_pts if hit == "SL" else tp_pts
            return {"pts": pts, "win": 1 if hit == "TP" else 0, "reason": hit,
                    "ts": float(m1t[m]), "gpos": int(gidx_m1[m])}
        g2 = int(gidx_m1[m])
        if g2 > last_g:
            last_g = g2
            held += 1
            if held >= hold_cap_m5:
                # tutup paksa: exit di close boundary
                delta = (close_g[g2] - close_g[entry_gpos]) * (1 if want_buy else -1)
                pts = delta * 100  # harga -> poin
                return {"pts": pts, "win": 1 if pts > 0 else 0, "reason": "time",
                        "ts": float(gts[g2]), "gpos": g2}
            if rev_allowed and held >= REV_MIN_HOLD_M5:
                d = dir_g[g2]
                if (want_buy and d < 0) or (not want_buy and d > 0):
                    delta = (close_g[g2] - close_g[entry_gpos]) * (1 if want_buy else -1)
                    pts = delta * 100
                    return {"pts": pts, "win": 1 if pts > 0 else 0, "reason": "reversal",
                            "ts": float(gts[g2]), "gpos": g2}
        m += 1
    return {"pts": 0, "win": 0, "reason": "end", "ts": float(m1t[-1]),
            "gpos": int(gidx_m1[len(m1t) - 1])}

def simulate(use_gate, style):
    """style: 'micro' => TP tetap 150; 'scalp' => TP max(150, 2xATR M5)."""
    trades = []
    i = 0
    cd_until = 0.0
    tp_fixed = (style == "micro")
    while i < n:
        ts = float(gts[i])
        d = int(dir_g[i])
        if d == 0 or ts < cd_until:
            i += 1
            continue
        want_buy = d == 1
        st = None
        if use_gate:
            st = candle_setup(i, want_buy)
            if st["block"]:
                i += 1
                continue
        atr = float(atr_g[i])
        sl_pts = round(atr * 100)
        if sl_pts < 20:
            sl_pts = 20
        tp_pts = 150 if tp_fixed else max(150, round(2 * atr * 100))
        # entry di close boundary
        lot = max(MIN_LOT, min(MAX_LOT, (EQUITY * RISK_PCT / 100.0) / sl_pts))
        lot = round(lot, 2)
        res = run_forward(i, want_buy, sl_pts, tp_pts, rev_allowed=True, hold_cap_m5=HOLD_CAP_M5)
        gross = res["pts"]
        net = gross - SPREAD_PTS
        rec = {"dir": "BUY" if want_buy else "SELL", "sl": sl_pts, "tp": tp_pts,
               "pts": net, "win": res["win"], "reason": res["reason"],
               "ts_in": ts, "ts_out": res["ts"], "lot": lot}
        if st is not None:
            rec["setup"] = st["setup"]; rec["score"] = st["score"]
        trades.append(rec)
        cd_until = res["ts"] + COOLDOWN_S
        i = max(i + 1, res["gpos"] + 1)
    return trades

def summarize(trades, tag):
    ntr = len(trades)
    if not ntr:
        return {"tag": tag, "n": 0}
    wins = sum(1 for t in trades if t["win"])
    gross = sum(t["pts"] for t in trades)
    pnl_usd = sum(t["pts"] * t["lot"] * TICK_USD for t in trades)
    reasons = {}
    for t in trades:
        reasons[t["reason"]] = reasons.get(t["reason"], 0) + 1
    return {"tag": tag, "n": ntr, "winrate": wins / ntr * 100,
            "net_pts": gross, "expect_pts": gross / ntr,
            "pnl_usd": pnl_usd, "reasons": reasons}

# ─── MAIN: A/B + laporan setup/pola ─────────────────────────────────────────
def fmt(d, s):
    return "  %-28s n=%-6d winrate=%6.1f%%  net_pts=%+9.0f  expect_pts=%+6.1f  pnl_usd(risk1%% eq2000)=%+9.2f  exit=%s" % (
        s, d["n"], d.get("winrate", 0), d.get("net_pts", 0), d.get("expect_pts", 0),
        d.get("pnl_usd", 0), d.get("reasons", {}))

def main():
    t0str = datetime.fromtimestamp(T0, timezone.utc).strftime("%Y-%m-%d")
    t1str = datetime.fromtimestamp(T1, timezone.utc).strftime("%Y-%m-%d")
    print("=" * 100)
    print("BACKTEST A/B GATE CANDLE V2 — XAUUSD M5/M15, jendela %s s.d. %s UTC (%d bar M5)"
          % (t0str, t1str, n))
    print("Sinyal arah = PROXY 2-TF identik antar varian; SL=1xATR(M5); cost %g poin/trade."
          % SPREAD_PTS)
    print("=" * 100)
    results = {}
    for style in ("micro", "scalp"):
        for gate in (False, True):
            tag = ("%s | GATE %s" % (style.upper(), "ON (V2)" if gate else "OFF"))
            tr = simulate(gate, style)
            results[(style, gate)] = tr
            s = summarize(tr, tag)
            print(fmt(s, tag))
            if gate:
                # distribusi setup & skor utk arm GATE-ON
                by = {}
                for t in tr:
                    key = t.get("setup", "?")
                    b = by.setdefault(key, [0, 0, 0.0])
                    b[0] += 1; b[1] += t["win"]; b[2] += t["pts"]
                for k, b in sorted(by.items()):
                    wr = b[1] / b[0] * 100 if b[0] else 0
                    print("      setup %-8s n=%-6d winrate=%6.1f%%  net_pts=%+9.0f"
                          % (k, b[0], wr, b[2]))
                # bucket skor (band lebar: 0-3, 4-6, 7-10)
                bands = {"skor0-3": (0, 3), "skor4-6": (4, 6), "skor7-10": (7, 10)}
                for bn, (lo, hi) in bands.items():
                    sel = [t for t in tr if lo <= t.get("score", -1) <= hi]
                    if not sel:
                        continue
                    w = sum(1 for t in sel if t["win"])
                    print("      %-8s n=%-6d winrate=%6.1f%%  net_pts=%+9.0f  expect_pts=%+6.1f"
                          % (bn, len(sel), w / len(sel) * 100, sum(t["pts"] for t in sel),
                             sum(t["pts"] for t in sel) / len(sel)))
    # Δ kesimpulan
    print("-" * 100)
    for style in ("micro", "scalp"):
        off = summarize(results[(style, False)], style + " OFF")
        on = summarize(results[(style, True)], style + " ON")
        if off["n"] and on["n"]:
            dpts = on["expect_pts"] - off["expect_pts"]
            dwr = on["winrate"] - off["winrate"]
            print("%s: gate ON vs OFF => winrate %+.1f pp, expect/trade %+.1f poin"
                  % (style.upper(), dwr, dpts))
    return results


# ─── LAPORAN MEMORI LIVE (data/learning) ────────────────────────────────────
def memory_report():
    path = os.path.join(MEM_DIR, "trade_memory.jsonl")
    if not os.path.exists(path):
        print("\n[memori] file belum ada:", path)
        return
    opens, closes = {}, []
    for ln in open(path, encoding="utf-8"):
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if r.get("evt") == "open":
            opens[r["ticket"]] = r
        elif r.get("evt") == "close" and r["ticket"] in opens:
            o = opens[r["ticket"]]
            closes.append({"style": o.get("style"), "dir": o.get("direction"),
                           "master": (o.get("fp") or {}).get("master"),
                           "m5_rsi": (o.get("fp") or {}).get("m5_rsi"),
                           "m5_atr": (o.get("fp") or {}).get("m5_atr"),
                           "pattern": (o.get("fp") or {}).get("patterns"),
                           "sl": o.get("sl_points"), "tp": o.get("tp_points"),
                           "pts": round(r.get("pnl", 0) / (o.get("lot") or 0.01), 1),
                           "pnl": r.get("pnl"), "win": r.get("win"),
                           "reason": r.get("close_reason")})
    print("\n" + "=" * 100)
    print("LAPORAN MEMORI LIVE — data/learning/trade_memory.jsonl (%d trade tertutup)" % len(closes))
    print("=" * 100)
    if closes:
        hdr = "  %-6s %-4s %-6s %7s %7s %-28s %5s %5s %8s %5s %-9s" % (
            "style", "dir", "master", "m5_rsi", "m5_atr", "pattern", "sl", "tp", "pts", "win", "reason")
        print(hdr)
        for c in closes:
            pat = ",".join(c["pattern"]) if c["pattern"] else "-"
            print("  %-6s %-4s %-6s %7.1f %7.1f %-28s %5s %5s %8.1f %5s %-9s" % (
                c["style"], c["dir"], c["master"] or "-", c["m5_rsi"] or 0, c["m5_atr"] or 0,
                pat[:28], c["sl"], c["tp"], c["pts"], c["win"], c["reason"]))
        by = {}
        for c in closes:
            k = "%s|%s|%s|%s" % (c["style"], c["dir"], c["master"], ",".join(c["pattern"]) if c["pattern"] else "none")
            b = by.setdefault(k, [0, 0, 0.0])
            b[0] += 1; b[1] += c["win"]; b[2] += c["pnl"] or 0
        print("  -- grup kondisi (bucket) --")
        for k, b in sorted(by.items()):
            wr = b[1] / b[0] * 100
            print("    %-70s n=%d win=%d wr=%.0f%% pnl=%+.2f" % (k, b[0], b[1], wr, b[2]))

# ─── FORWARD-RETURN PER POLA (parquet 2 tahun, konteks arah setuju) ─────────
def pattern_forward_report(sample=3000):
    print("\n" + "=" * 100)
    print("FORWARD-RETURN PER POLA M5 (micro-style: TP 150, SL 1xATR M5, exit SL/TP/reversal)")
    print("Konteks: arah proxy 2-TF SETUJU dengan arah pola. Sampel acak <= %d per pola." % sample)
    print("=" * 100)
    import random
    rng = random.Random(7)
    pats = {}
    step = max(1, n // (sample * 4))   # ambang sampling: batasi iterasi grid
    for gpos in range(200, n, step):
        k5 = int(grid[gpos])
        pp = mini_pattern_dir(m5c, m5o, m5h, m5l, k5)
        d = int(dir_g[gpos])
        if not pp or d == 0:
            continue
        name, pdir = pp
        want = (pdir == "BUY")
        if (d == 1) != want:
            continue
        atr = float(atr_g[gpos])
        sl_pts = max(20, round(atr * 100))
        res = run_forward(gpos, want, sl_pts, 150, rev_allowed=True, hold_cap_m5=72)
        rec = pats.setdefault("%s:%s" % (name, pdir), [0, 0, 0.0, want])
        rec[0] += 1
        rec[1] += res["win"]
        rec[2] += res["pts"] - SPREAD_PTS
    if not pats:
        print("  (tidak ada sampel)")
        return
    print("  %-8s %-6s %9s %9s %12s" % ("pola", "arah", "n", "winrate", "expect_pts"))
    for k, (cnt, wins, pts, want) in sorted(pats.items()):
        if cnt < 50:
            continue
        print("  %-8s %-6s %9d %8.1f%% %12.1f" % (k, "BUY" if want else "SELL", cnt, wins / cnt * 100, pts / cnt))

if __name__ == "__main__":
    only = os.environ.get("BT_ONLY", "")
    if only != "pattern":
        main()
        memory_report()
    if only in ("", "pattern"):
        pattern_forward_report()
