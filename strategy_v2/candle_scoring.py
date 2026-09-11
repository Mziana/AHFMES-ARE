"""Candle Scoring System — otak keputusan demo V1/V2 (owner-approved spec).

DUA LAPIS:   Lapis 1 (konteks, biner): bias momentum M15 (EMA9/21 + RSI band 45/55)
  (MICRO: M15, SCALP: H4 via proxy bar 4xM15 bila H4 tak tersedia) — dilakukan
  di simple_variants.py. Modul ini hanya Lapis 2.

LAPIS 2 — SKOR CANDLE 0..10 (+1 bonus pola 3-candle, minus penalti):
  +3        pola inti (14 pola, wajib bar CLOSE, satu terkuat):
              1c: hammer/shooting-star/hanging-man, marubozu bull/bear
              2c: engulfing bull/bear, piercing/dark-cloud, tweezer bottom/top
              3c: morning/evening star, three white soldiers/black crows
  +1 (max3) kualitas eksekusi:
              a) close di sepertiga ujung range arah sinyal
              b) body >= rata2 body 5 bar sebelumnya
              c) close menembus high/low bar sebelumnya (break mikro)
  +2        konteks level: pola DI level eksekusi (jarak <= level_tol_atr*ATR)
  +1        volume > rata2 5 bar (wajib utk SCALP: minimal 1.2x)
  -1        penalti: 3 bar searah lawan sebelum pola; ATR > 1.5x median20

PURE: tidak ada I/O, tidak ada now(), tidak ada random — semua dari bar.
"""
from __future__ import annotations

from typing import Optional

# ── Threshold entri (owner: 6 micro, 7 scalp) ────────────────────────────────
ENTRY_THRESHOLD = {"MICRO": 6.0, "SCALP": 7.0}

LEVEL_TOL_ATR = 0.75          # dari Arm A (zona emas diagnostik bucket)
TWEEZER_TOL_ATR = 0.10        # tweezer: high/low nyaris sama
MARUBOZU_BODY_RATIO = 0.85    # body >= 85% range
REJECT_WICK_RATIO = 2.0       # wick penolak >= 2x body
OPP_WICK_MAX_RATIO = 0.30     # wick lawan <= 30% range
VOL_MULT_SCALP = 1.2          # SCALP wajib 1.2x rata2 volume
ATR_SPIKE_MULT = 1.5          # penalti volatilitas liar

# Momentum-habis (owner rule, M5 — M1 terlalu volatile utk aturan ini):
# rally searah lalu koreksi. Rally TIDAK selalu 2 candle — bisa 3, 4, 5 — jadi
# diukur dari RETRACE (% koreksi dari puncak run), bukan jumlah candle.
RETRACE_EXHAUST = 0.618       # koreksi > 61.8% dari run → momentum habis
RETRACE_SHALLOW = 0.382       # koreksi <= 38.2% → sehat, entry tetap boleh
EXHAUST_WINDOW = 12           # window bar utk mencari puncak run
MARUBOZU_BODY_RATIO = 0.85    # (dipakai juga di sini: koreksi berbadan penuh)


# ── Util bar (dict: open/high/low/close/volume/time) ─────────────────────────
def _body(b): return abs(b["close"] - b["open"])
def _range(b): return max(b["high"] - b["low"], 1e-9)
def _upper(b): return b["high"] - max(b["close"], b["open"])
def _lower(b): return min(b["close"], b["open"]) - b["low"]
def _is_bull(b): return b["close"] > b["open"]
def _is_bear(b): return b["close"] < b["open"]


def ema(values, period):
    if len(values) < period:
        return None
    k = 2.0 / (period + 1)
    e = sum(values[:period]) / period
    for v in values[period:]:
        e = v * k + e * (1 - k)
    return e


def rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    ag = sum(gains[:period]) / period
    al = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        ag = (ag * (period - 1) + gains[i]) / period
        al = (al * (period - 1) + losses[i]) / period
    if al <= 0:
        return 100.0
    rs = ag / al
    return 100.0 - 100.0 / (1.0 + rs)


def atr(bars, period=14):
    if len(bars) < period + 1:
        return None
    trs = []
    for i in range(1, len(bars)):
        h, l, pc = bars[i]["high"], bars[i]["low"], bars[i - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs[-period:]) / period


def median(vals):
    s = sorted(vals)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


# ── Struktur HH/HL vs LH/LL (swing sederhana, fraktal 2 kiri/2 kanan) ────────
def _swings(bars):
    highs, lows = [], []
    for i in range(2, len(bars) - 2):
        if bars[i]["high"] >= max(bars[i - 1]["high"], bars[i - 2]["high"],
                                  bars[i + 1]["high"], bars[i + 2]["high"]):
            highs.append(bars[i]["high"])
        if bars[i]["low"] <= min(bars[i - 1]["low"], bars[i - 2]["low"],
                                 bars[i + 1]["low"], bars[i + 2]["low"]):
            lows.append(bars[i]["low"])
    return highs, lows


def structure_direction(bars, margin_atr: float = 0.25, lookback: int = 3) -> Optional[str]:
    """HH+HL -> 'BULL', LH+LL -> 'BEAR', else None.

    Rev 2026-09-10 (owner: kombinasi opsi 1+2) — dua pengaman agar struktur
    tidak dibalik oleh noise microstructure (kasus nyata: "HH" +0.91 poin
    dari bounce 75 menit membalik bacaan BEAR ke BULL):
      1. MARGIN 0.25xATR: swing hanya dihitung HH/HL/LH/LL bila melampaui
         swing sebelumnya LEBIH dari margin — selisih kecil = suara netral.
      2. MAYORITAS 3-SWING: arah butuh >= 2 dari 3 perbandingan swing
         terakhir searah; butuh minimal 3 swing utk bisa dinilai sama
         sekali (data lebih pendek = None, belum cukup bukti).
    """
    highs, lows = _swings(bars)
    if len(highs) < 3 or len(lows) < 3:
        return None
    a = atr(bars) or 0.0
    margin = margin_atr * a

    def votes(seq) -> tuple:
        up = dn = 0
        for i in range(max(1, len(seq) - lookback), len(seq)):
            if seq[i] > seq[i - 1] + margin:
                up += 1
            elif seq[i] < seq[i - 1] - margin:
                dn += 1
        return up, dn

    h_up, h_dn = votes(highs)
    l_up, l_dn = votes(lows)
    if h_up >= 2 and l_up >= 2:
        return "BULL"
    if h_dn >= 2 and l_dn >= 2:
        return "BEAR"
    return None


# ── Momentum-habis: rally lalu koreksi (owner rule, diterapkan di M5) ────────
def momentum_exhausted(bars, direction: str) -> tuple:
    """Rally searah lalu koreksi — kapan momentum dianggap habis?

    Rally TIDAK diukur dari jumlah candle (bisa 2, 3, 4, 5 candle lalu baru
    koreksi) melainkan dari RETRACE: seberapa dalam harga mundur dari puncak
    run, relatif ke tinggi run.
      retrace >= 61.8%                    → habis (blok)
      retrace <= 38.2%                    → koreksi sehat (lanjut)
      38.2% < retrace < 61.8% (zona emas) → habis HANYA bila ada candle
          koreksi marubozu-grade (body >= 85% range) MELAWAN arah dengan
          volume > rata2 5 bar sebelumnya — koreksi berbadan penuh + volume
          = distribusi, bukan sekadar breathing room.

    Return (exhausted: bool, info: dict) — info untuk checklist UI.
    PURE: hanya dari bar.
    """
    info = {"run_high": None, "run_low": None, "retrace": None,
            "retracement_pct": None, "zone": "n/a", "note": ""}
    if len(bars) < 5:
        return False, info
    window = bars[-EXHAUST_WINDOW:]
    offset = len(bars) - len(window)

    # RUN = dari extremum TERBARU di window ke puncak/lantai SETELAHNYA.
    # Kalau extremum justru bar terakhir (belum ada rally) → tidak ada
    # momentum yang bisa habis → sehat. Puncak stale (sebelum extremum)
    # TIDAK dipakai — itu sebabnya retrace bisa >100% pada versi lama.
    if direction == "BULL":
        lo_rel = min(range(len(window)), key=lambda i: window[i]["low"])
        lo_abs = offset + lo_rel
        run_low = bars[lo_abs]["low"]
        after = bars[lo_abs:]
        hi_rel = max(range(len(after)), key=lambda i: after[i]["high"])
        abs_hi = lo_abs + hi_rel
        run_high = after[hi_rel]["high"]
        if len(after) < 2 or run_high <= run_low:
            info["note"] = "belum ada rally di window"
            return False, info
        retrace = (run_high - window[-1]["close"]) / (run_high - run_low)
    else:
        hi_rel = max(range(len(window)), key=lambda i: window[i]["high"])
        hi_abs = offset + hi_rel
        run_high = bars[hi_abs]["high"]
        after = bars[hi_abs:]
        lo_rel = min(range(len(after)), key=lambda i: after[i]["low"])
        abs_lo = hi_abs + lo_rel
        run_low = after[lo_rel]["low"]
        if len(after) < 2 or run_high <= run_low:
            info["note"] = "belum ada rally di window"
            return False, info
        retrace = (window[-1]["close"] - run_low) / (run_high - run_low)
    info.update({"run_high": run_high, "run_low": run_low,
                 "retrace": retrace, "retracement_pct": round(retrace * 100, 1)})
    if retrace <= RETRACE_SHALLOW:
        info["zone"] = "sehat"
        info["note"] = f"koreksi {retrace*100:.0f}% <= 38.2% — sehat"
        return False, info
    if retrace >= RETRACE_EXHAUST:
        info["zone"] = "habis"
        info["note"] = f"koreksi {retrace*100:.0f}% >= 61.8% dari run — momentum habis"
        return True, info
    # zona emas: habis hanya bila koreksi marubozu-grade + volume
    after = bars[(abs_hi if direction == "BULL" else abs_lo) + 1:]
    avg_vol5 = sum(int(b.get("volume", 0)) for b in window[-6:-1]) / 5.0
    for b in after:
        body, rng = _body(b), _range(b)
        opp = _is_bear(b) if direction == "BULL" else _is_bull(b)
        vol = int(b.get("volume", 0))
        if opp and body >= MARUBOZU_BODY_RATIO * rng and avg_vol5 > 0 and vol > avg_vol5:
            info["zone"] = "habis (marubozu+volume)"
            info["note"] = (f"koreksi {retrace*100:.0f}% + candle marubozu lawan "
                            f"(vol {vol} > avg {avg_vol5:.0f}) — momentum habis")
            return True, info
    info["zone"] = "emas-sehat"
    info["note"] = f"koreksi {retrace*100:.0f}% di zona emas, tanpa marubozu+volume — masih sehat"
    return False, info


# ── Poin konteks per-TF (owner: sistem point candle per timeframe di UI) ─────
def _quality_points(bars, direction: str) -> tuple:
    """Poin kualitas eksekusi bar close (max +3). Return (points, list note)."""
    b3, prev = bars[-1], bars[-2]
    r3, body3 = _range(b3), _body(b3)
    pts, notes = 0, []
    third = 1 if (b3["close"] - b3["low"]) >= (2.0 / 3.0) * r3 else (
        -1 if (b3["high"] - b3["close"]) >= (2.0 / 3.0) * r3 else 0)
    if (direction == "BULL" and third == 1) or (direction == "BEAR" and third == -1):
        pts += 1
        notes.append("Close ujung range")
    avg_body5 = sum(_body(b) for b in bars[-6:-1]) / 5.0
    if body3 >= avg_body5 > 0:
        pts += 1
        notes.append("Body >= avg5")
    if (direction == "BULL" and b3["close"] > prev["high"]) or \
       (direction == "BEAR" and b3["close"] < prev["low"]):
        pts += 1
        notes.append("Break mikro")
    return pts, notes


def context_points(bars) -> dict:
    """Pembacaan candle SATU timeframe utk konfirmasi antar-TF (tanpa level/
    volume/penalti — murni pola + kualitas). Deterministik.

    Return {"pattern": name|None, "direction": "BULL"|"BEAR"|None,
            "points": 0|3|4..7, "quality": [notes]}"""
    pats = detect_patterns(bars)
    if not pats:
        return {"pattern": None, "direction": None, "points": 0, "quality": []}
    pats.sort(key=lambda x: (x[2], True))
    name, direction, is3 = pats[-1]
    q, notes = _quality_points(bars, direction)
    return {"pattern": name, "direction": direction,
            "points": (4 if is3 else 3) + q, "quality": notes}


# ── Deteksi 14 pola (bull/bear) pada bar CLOSE = bars[-1] ────────────────────
def detect_patterns(bars):
    """Return list of (name, direction, is_3candle) — terkuat di akhir list."""
    pats = []
    if len(bars) < 3:
        return pats
    b1, b2, b3 = bars[-3], bars[-2], bars[-1]  # b3 = bar sinyal (close)
    r3, body3 = _range(b3), _body(b3)

    # ── 1-candle ──
    if body3 > 0:
        low_w, up_w = _lower(b3), _upper(b3)
        if low_w >= REJECT_WICK_RATIO * body3 and up_w <= OPP_WICK_MAX_RATIO * r3:
            pats.append(("hammer", "BULL", False))
        if up_w >= REJECT_WICK_RATIO * body3 and low_w <= OPP_WICK_MAX_RATIO * r3:
            pats.append(("shooting_star", "BEAR", False))
            if _is_bear(b3) or True:  # hanging man = hammer di puncak; arah bear
                pats.append(("hanging_man", "BEAR", False))
        if body3 >= MARUBOZU_BODY_RATIO * r3:
            pats.append(("marubozu_bull" if _is_bull(b3) else "marubozu_bear",
                         "BULL" if _is_bull(b3) else "BEAR", False))

    # ── 2-candle ──
    r2, body2 = _range(b2), _body(b2)
    if body2 > 0 and body3 > 0:
        if _is_bull(b3) and _is_bear(b2) and b3["close"] > b2["open"] and b3["open"] <= b2["close"]:
            pats.append(("bullish_engulfing", "BULL", False))
        if _is_bear(b3) and _is_bull(b2) and b3["close"] < b2["open"] and b3["open"] >= b2["close"]:
            pats.append(("bearish_engulfing", "BEAR", False))
        if _is_bear(b2) and _is_bull(b3):
            mid2 = (b2["open"] + b2["close"]) / 2.0
            if b3["open"] < b2["close"] and b3["close"] > mid2:
                pats.append(("piercing_line", "BULL", False))
        if _is_bull(b2) and _is_bear(b3):
            mid2 = (b2["open"] + b2["close"]) / 2.0
            if b3["open"] > b2["close"] and b3["close"] < mid2:
                pats.append(("dark_cloud_cover", "BEAR", False))
    if body2 > 0 and body3 > 0 and _is_bull(b3) != _is_bull(b2):
        tol = TWEEZER_TOL_ATR
        if abs(b2["low"] - b3["low"]) <= tol:
            pats.append(("tweezer_bottom", "BULL", False))
        if abs(b2["high"] - b3["high"]) <= tol:
            pats.append(("tweezer_top", "BEAR", False))

    # ── 3-candle ──
    body1 = _body(b1)
    small_mid = body3 < 0.5 * max(body1, 0) or body2 < 0.5 * max(body1, 0)
    if _is_bear(b1) and body1 > 0 and small_mid and _is_bull(b3):
        if b3["close"] > (b1["open"] + b1["close"]) / 2.0:
            pats.append(("morning_star", "BULL", True))
    if _is_bull(b1) and body1 > 0 and small_mid and _is_bear(b3):
        if b3["close"] < (b1["open"] + b1["close"]) / 2.0:
            pats.append(("evening_star", "BEAR", True))
    if all(_is_bull(b) for b in (b1, b2, b3)):
        if b3["close"] > b2["close"] > b1["close"] and b2["close"] > b2["open"]:
            pats.append(("three_white_soldiers", "BULL", True))
    if all(_is_bear(b) for b in (b1, b2, b3)):
        if b3["close"] < b2["close"] < b1["close"] and b2["close"] < b2["open"]:
            pats.append(("three_black_crows", "BEAR", True))
    return pats


# ── Skor ─────────────────────────────────────────────────────────────────────
def score_candle(bars, level_price: Optional[float], profile: str,
                 require_volume: bool) -> dict:
    """Hitung skor 0..10(+bonus,−penalti) untuk bar close terakhir.

    bars        : list bar M5 (>= 25 bar ideal; minimal 3)
    level_price : level eksekusi aktif (None = tidak ada level dekat)
    profile     : "MICRO" | "SCALP"
    require_volume : True utk SCALP (volume < 1.2x avg → sinyal ditolak)
    """
    checklist = []
    if len(bars) < 3:
        return {"ok": False, "reason": "bar < 3", "score": 0.0, "checklist": checklist,
                "direction": None, "pattern": None}

    b3 = bars[-1]
    c = []

    # ── +3 pola inti ──
    pats = detect_patterns(bars)
    if not pats:
        return {"ok": False, "reason": "tidak ada pola pada bar close", "score": 0.0,
                "checklist": [{"k": "Pola", "pts": 0, "note": "tidak ada pola"}],
                "direction": None, "pattern": None}
    # ambil pola terkuat (3-candle didahulukan, lalu terakhir terdeteksi)
    pats.sort(key=lambda x: (x[2], True))
    name, direction, is3 = pats[-1]
    base = 3.0
    if is3:
        base += 1.0
        c.append({"k": f"Pola {name}", "pts": 4, "note": "pola 3-candle (+1 bonus)"})
    else:
        c.append({"k": f"Pola {name}", "pts": 3, "note": ""})
    score = base

    # arah pola vs konteks diperiksa pemanggil (bias) — di sini kualitas:
    q_pts, q_notes = _quality_points(bars, direction)
    for label in ("Close ujung range", "Body >= avg5", "Break mikro"):
        if label in q_notes:
            score += 1
            c.append({"k": label, "pts": 1, "note": ""})

    # ── +2 konteks level ──
    a = atr(bars[:-1]) or atr(bars)
    if level_price is not None and a:
        if abs(b3["close"] - level_price) <= LEVEL_TOL_ATR * a:
            score += 2
            c.append({"k": "Di level eksekusi", "pts": 2,
                      "note": f"jarak {abs(b3['close'] - level_price):.2f} <= 0.75xATR"})
        else:
            c.append({"k": "Di level eksekusi", "pts": 0,
                      "note": f"jarak {abs(b3['close'] - level_price):.2f} > 0.75xATR"})
    else:
        c.append({"k": "Di level eksekusi", "pts": 0, "note": "tidak ada level"})

    # ── +1 volume ──
    avg_vol5 = sum(int(b.get("volume", 0)) for b in bars[-6:-1]) / 5.0
    vol = int(b3.get("volume", 0))
    vol_ok = avg_vol5 > 0 and vol > avg_vol5
    if profile == "SCALP":
        vol_strong = avg_vol5 > 0 and vol >= VOL_MULT_SCALP * avg_vol5
        if not vol_strong:
            # owner-lock 2026-09-10: volume wajib SCALP TIDAK diubah — 3 win
            # beruntun sore itu terjadi pada bar bervolume (owner: "jangan
            # rubah logic entri untuk scalp"). ~14% bar M5 lolos — filter
            # memang ketat sesuai desain.
            return {"ok": False,
                    "reason": f"volume {vol} < {VOL_MULT_SCALP:.1f}x avg5 ({avg_vol5:.0f} → butuh "
                              f"{VOL_MULT_SCALP * avg_vol5:.0f}) — bar sinyal harus ada "
                              f"dorongan volume (aturan profil SCALP)",
                    "score": score, "checklist": c + [{"k": f"Volume >= {VOL_MULT_SCALP:.1f}x avg5", "pts": 0, "note": "WAJIB (owner-lock)"}],
                    "direction": None, "pattern": name}
        score += 1
        c.append({"k": f"Volume >= {VOL_MULT_SCALP:.1f}x avg5", "pts": 1, "note": f"{vol} vs {avg_vol5:.0f}"})
    else:
        if vol_ok:
            score += 1
            c.append({"k": "Volume > avg5", "pts": 1, "note": f"{vol} vs {avg_vol5:.0f}"})
        else:
            c.append({"k": "Volume > avg5", "pts": 0, "note": f"{vol} vs {avg_vol5:.0f}"})

    # ── penalti ──
    if len(bars) >= 4:
        last3 = bars[-4:-1]
        if all(_is_bear(b) for b in last3) and direction == "BULL":
            score -= 1
            c.append({"k": "Penalti 3-bear beruntun", "pts": -1, "note": "momentum lawan kuat"})
        if all(_is_bull(b) for b in last3) and direction == "BEAR":
            score -= 1
            c.append({"k": "Penalti 3-bull beruntun", "pts": -1, "note": "momentum lawan kuat"})
    med20 = median([_range(b) for b in bars[-21:-1]]) if len(bars) >= 21 else None
    if a and med20 and _range(b3) > ATR_SPIKE_MULT * med20:
        score -= 1
        c.append({"k": "Penalti volatilitas liar", "pts": -1, "note": "range > 1.5x median20"})

    thr = ENTRY_THRESHOLD.get(profile, 6.0)
    ok = score >= thr
    c.append({"k": f"TOTAL vs threshold {thr:.0f}", "pts": score, "note": "ENTRI" if ok else "WAIT"})
    return {"ok": ok, "reason": "" if ok else f"skor {score:.0f} < {thr:.0f}",
            "score": score, "checklist": c, "direction": direction, "pattern": name}
