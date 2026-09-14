"""Exit Geometry MICRO — paket doktrin exit owner 2026-09-11 (shadow-first).

Latar (jurnal live 11 Sep): geometri 0.9/1.4×ATR-M5 memberi TP yang tidak
terjangkau karakter M1 — ticket 431035015 TP 923.9 pts, harga balik dalam $5;
MICRO v2.1.1 hari ini 1W/7L (−37.52$), kill switch 4× memotong streak 7.
Doktrin exit (owner, 7 butir): TP terjangkau TF eksekusi, TP berhenti di
struktur, RSI-burn → TP pendek, early exit saat momen habis, RR fleksibel
(hasil struktur, bukan hardcode), SL anti-hunt (dikalifikasi dari data).

DUA KANDIDAT SHADOW (owner pilih keduanya, 11 Sep sore):
  EXIT-D-01 (D_exit)  : entry parity A_base; exit diganti D1+D2+D4 (+D5 saat
                        manajemen posisi). SL tetap 0.9×ATR-M5 — satu variabel
                        besar diubah (TP), SL disengaja tidak.
  EXIT-E-01 (E_atr_m1): SL/TP 0.9/1.4 × ATR-M1 — skala ikut karakter TF
                        eksekusi; jawaban fundamental utk "ATR-M5 membesar".

ATURAN D (identitas di registry, Pagar 1 — semua angka di sini/registry):
  D1  TP cap 600 pts           — M1 fast-in-fast-out; 500–600 pts cukup.
  D2  clamp struktur           — TP berhenti 0.25×ATR-M5 sebelum swing
                                 berlawanan terdekat M5/M15 (swing = fraktal
                                 CS._swings pada CLOSED bars, anti-lookahead);
                                 sisa TP < 100 pts dari entry → REJECT entry
                                 (fail-closed, tanpa order).
  D4  RSI-burn                 — pola M1 searah bias DAN RSI-M1 > 60 (BULL) /
                                 < 40 (BEAR) → TP × 0.7 (sisa-bakar RSI sedikit).
  D5  early exit               — posisi profit + pembalikan (pola lawan ATAU
                                 momentum habis CS.momentum_exhausted) +
                                 konfirmasi momentum (EMA9/21 M1 cross ATAU
                                 RSI-M1 patah 50) → tutup. Diterapkan hanya
                                 pada posisi kandidat D (manajemen posisi).
  D6  RR fleksibel             — bukan rule: konsekuensi D1/D2/D4 (tanpa RR
                                 hardcoded).
  D7  SL anti-hunt             — bukan rule: studi data (SL live sekarang murni
                                 ATR, bukan nempel pola). Diukur terpisah dari
                                 jurnal demo sebelum buffer sl_buffer_pts
                                 dipakai (default 0).

PURE: tanpa I/O, tanpa now() — semua dari bar + argumen. Import di-whitelist
(dijaga test struktural): candle_scoring, simple_variants, micro_v2.
"""
from __future__ import annotations

from typing import Optional

from strategy_v2 import candle_scoring as CS
from strategy_v2 import simple_variants as SV
from strategy_v2 import micro_v2 as MV

POINT = MV.POINT  # 0.01 USD/pt

# ── EXIT-D-01 (shadow D_exit) ────────────────────────────────────────────────
PARAMS_D = {
    "tp_cap_pts": 600.0,        # D1 — doktrin 1: 500–600 pts cukup utk M1
    "clamp_buffer_atr": 0.25,   # D2 — TP berhenti 0.25×ATR sebelum swing
    "min_tp_pts": 100.0,        # D2 — sisa TP < ini → REJECT entry (fail-closed)
    "burn_rsi": 60.0,           # D4 — BULL: RSI-M1 > 60; BEAR: < 100−60 = 40
    "burn_tp_factor": 0.7,      # D4 — TP × 0.7 saat burn
    "early_exit": True,         # D5 — manajemen posisi aktif utk kandidat D
    "sl_mult": MV.SL_MULT,      # SL tetap 0.9×ATR-M5 (tidak diubah di paket D)
    "tp_mult": MV.TP_MULT,      # 1.4×ATR-M5 = TP dasar sebelum cap/clamp/burn
}

# D5 — early exit (manajemen posisi, hanya kandidat D)
PARAMS_EARLY = {
    "profit_buffer_pts": 0.0,   # "profit" = masih > entry (buffer dikalifikasi
                                # dari data demo sebelum diketatkan — D7 style)
    "confirm_ema_cross": True,  # EMA9/21 M1 sudah cross melawan posisi
    "confirm_rsi_cross": True,  # ATAU RSI-M1 patah 50 melawan posisi
    "exhaust_window": 12,       # window retrace = parity CS.EXHAUST_WINDOW
}

# ── EXIT-E-01 (shadow E_atr_m1) ──────────────────────────────────────────────
PARAMS_E = {
    "sl_mult": 0.9,             # × ATR-M1
    "tp_mult": 1.4,             # × ATR-M1
}


# ── util kecil ───────────────────────────────────────────────────────────────
def _pts(x: float) -> float:
    return round(abs(x) / POINT, 1)


def _pattern_aligned(direction: str, m1: list) -> bool:
    """Bar close terakhir punya pola searah arah posisi (D4: momentum/burn)."""
    for name, d, _three in CS.detect_patterns(m1):
        if d == direction:
            return True
    return False


def _pattern_opposite(direction: str, m1: list) -> bool:
    for name, d, _three in CS.detect_patterns(m1):
        if d != direction:
            return True
    return False


# ── plan exit D (D1+D2+D4) — dipanggil saat sinyal shadow D terbentuk ───────
def plan_exit_d(direction: str, entry: float, m1: list, m5: list,
                m15: Optional[list]) -> dict:
    """Return {ok, sl, tp, sl_pts, tp_pts, burned, clamp, reject_reason}.

    Urutan deterministik: TP dasar ATR-M5 → D1 cap (langit-langit) → D4 burn
    (× 0.7 atas jarak yang SUDAH di-cap — burn harus tetap terlihat efektifnya
    di rezim ATR besar) → D2 clamp (SELALU terakhir — struktur batas mutlak).
    ok=False berarti entry DITOLAK (fail-closed) — penelepon TIDAK boleh
    membuka posisi.
    """
    p = PARAMS_D
    atr5 = CS.atr(m5)
    if not atr5 or atr5 <= 0 or entry <= 0:
        return {"ok": False, "reject_reason": "DATA_INVALID:atr_m5",
                "sl": None, "tp": None, "sl_pts": None, "tp_pts": None,
                "burned": False, "clamp": "none"}
    sign = 1.0 if direction == "BULL" else -1.0
    sl_d, tp_d = p["sl_mult"] * atr5, p["tp_mult"] * atr5
    sl = entry - sign * sl_d
    notes = []

    # D1 — cap (langit-langit atas jarak TP)
    cap_px = p["tp_cap_pts"] * POINT
    capped = min(tp_d, cap_px)
    if capped < tp_d:
        notes.append(f"TP cap {p['tp_cap_pts']:.0f} pts")

    # D4 — RSI burn (pola searah + RSI-M1 jenuh searah momentum) → × 0.7
    burned = False
    r1 = CS.rsi([b["close"] for b in m1], 14) if len(m1) >= 16 else None
    rsi_hot = (r1 is not None and
               ((direction == "BULL" and r1 > p["burn_rsi"]) or
                (direction == "BEAR" and r1 < 100.0 - p["burn_rsi"])))
    if rsi_hot and _pattern_aligned(direction, m1):
        capped *= p["burn_tp_factor"]
        burned = True
        notes.append(f"burn RSI-M1 {r1:.0f} → TP × {p['burn_tp_factor']}")
    tp = entry + sign * capped

    # D2 — clamp struktur (swings M15 + M5, CLOSED bars — CS._swings fraktal)
    clamp = "none"
    opps = []
    for bars in (m15, m5):
        if not bars:
            continue
        highs, lows = CS._swings(bars)
        opps += highs if direction == "BULL" else lows
    ahead = ([x for x in opps if x > entry] if direction == "BULL"
             else [x for x in opps if x < entry])
    if ahead:
        nearest = min(ahead) if direction == "BULL" else max(ahead)
        limit = nearest - sign * p["clamp_buffer_atr"] * atr5
        crossed = (limit < tp) if direction == "BULL" else (limit > tp)
        if crossed:
            tp = limit
            clamp = "swing"
            notes.append(f"clamp swing {nearest:.2f} − {p['clamp_buffer_atr']}×ATR")
    sisa_pts = abs(tp - entry) / POINT
    if sisa_pts < p["min_tp_pts"]:
        return {"ok": False,
                "reject_reason": f"tp_after_structure:{sisa_pts:.0f}pts<"
                                 f"{p['min_tp_pts']:.0f}",
                "sl": sl, "tp": tp, "sl_pts": _pts(sl - entry),
                "tp_pts": round(sisa_pts, 1), "burned": burned,
                "clamp": clamp}
    return {"ok": True, "reject_reason": None, "sl": round(sl, 2),
            "tp": round(tp, 2), "sl_pts": _pts(sl - entry),
            "tp_pts": round(sisa_pts, 1), "burned": burned, "clamp": clamp,
            "notes": notes}


# ── plan exit E — geometri ATR-M1 ────────────────────────────────────────────
def exit_plan_atr_m1(direction: str, entry: float, m1: list) -> dict:
    """SL/TP 0.9/1.4 × ATR-M1 — skala ikut karakter TF eksekusi (EXIT-E-01).
    Tanpa cap/clamp/burn: hipotesis E adalah "geometri yang benar cukup satu". """
    p = PARAMS_E
    atr1 = CS.atr(m1)
    if not atr1 or atr1 <= 0 or entry <= 0 or len(m1) < MV.MIN_M1:
        return {"ok": False, "reject_reason": "DATA_INVALID:atr_m1",
                "sl": None, "tp": None, "sl_pts": None, "tp_pts": None}
    sign = 1.0 if direction == "BULL" else -1.0
    sl_d, tp_d = p["sl_mult"] * atr1, p["tp_mult"] * atr1
    sl = entry - sign * sl_d
    tp = entry + sign * tp_d
    return {"ok": True, "reject_reason": None, "sl": round(sl, 2),
            "tp": round(tp, 2), "sl_pts": _pts(sl_d), "tp_pts": _pts(tp_d)}


# ── D5 — early exit (manajemen posisi, kandidat D) ───────────────────────────
def early_exit_check(direction: str, entry: float, m1: list) -> dict:
    """Return {exit: bool, reason: str}.

    Exit bila SEMUA terpenuhi (doktrin 5 — konfirmasi berlapis, bukan satu
    candle melawan):
      1. posisi PROFIT (close terakhir masih lebih baik dari entry);
      2. pembalikan terkonfirmasi di M1: pola berlawanan posisi ATAU
         momentum habis (CS.momentum_exhausted, retrace >= 61.8%);
      3. momentum patah: EMA9/21 M1 cross melawan posisi ATAU RSI-M1
         menembus 50 melawan posisi.

    direction menerima "BULL"/"BEAR" maupun "BUY"/"SELL" (parity pending
    shadow yang menyimpan BUY/SELL).
    """
    direction = {"BUY": "BULL", "SELL": "BEAR"}.get(direction, direction)
    ep = PARAMS_EARLY
    if len(m1) < 30:
        return {"exit": False, "reason": "data M1 kurang"}
    close = float(m1[-1]["close"])
    profit = (close - entry) if direction == "BULL" else (entry - close)
    if profit <= ep["profit_buffer_pts"]:
        return {"exit": False,
                "reason": "tidak profit — biarkan SL/TP bekerja"}
    reversal = _pattern_opposite(direction, m1)
    exhaust, ex_info = CS.momentum_exhausted(m1, direction)
    if not (reversal or exhaust):
        return {"exit": False, "reason": "profit tapi tanpa pembalikan"}
    closes = [b["close"] for b in m1]
    e9, e21 = CS.ema(closes, 9), CS.ema(closes, 21)
    r1 = CS.rsi(closes, 14)
    if direction == "BULL":
        ema_break = ep["confirm_ema_cross"] and e9 is not None and e21 is not None \
            and e9 < e21
        rsi_break = ep["confirm_rsi_cross"] and r1 is not None and r1 < 50.0
    else:
        ema_break = ep["confirm_ema_cross"] and e9 is not None and e21 is not None \
            and e9 > e21
        rsi_break = ep["confirm_rsi_cross"] and r1 is not None and r1 > 50.0
    if not (ema_break or rsi_break):
        return {"exit": False,
                "reason": "pembalikan terlihat tapi momentum belum patah"}
    why = []
    if reversal:
        why.append("pola berbalik")
    if exhaust:
        why.append(f"momentum habis ({ex_info.get('retracement_pct')}%)")
    if ema_break:
        why.append("EMA9/21 M1 cross")
    if rsi_break:
        why.append(f"RSI-M1 {r1:.0f} patah 50")
    return {"exit": True, "reason": "early-exit: " + " + ".join(why)}


# ── D7 — studi SL anti-hunt (data, bukan rule) ───────────────────────────────
def sl_hunt_study(closed_trades: list) -> dict:
    """Ukur seberapa mepet SL yang tersentuh vs ekstrem bar exit (D7).

    closed_trades: list {dir:'BUY'/'SELL', sl, entry, exit_time, m1_by_time,
    m1_times} — dari jurnal demo. Return distribusi jarak ekstrem-bar ke SL;
    buffer sl_buffer_pts layak bila ekor distribusinya menolak SL berkali-
    kali dalam noise kecil. HANYA STUDI — tidak mengubah geometri.
    """
    import bisect
    gaps = []
    for t in closed_trades:
        sl, d = t.get("sl"), t.get("dir")
        if not sl or d not in ("BUY", "SELL"):
            continue
        times = t.get("m1_times") or []
        i = bisect.bisect_right(times, int(t.get("exit_time") or 0))
        if i == 0 or i > len(times):
            continue
        b = (t.get("m1_by_time") or {}).get(times[i - 1])
        if not b:
            continue
        extreme = float(b["low"] if d == "SELL" else b["high"])
        gap = abs(extreme - float(sl)) / POINT
        if gap <= 50.0:  # hanya SL-hit yang "mepet" (≤ 50 pts) relevan
            gaps.append(round(gap, 1))
    gaps.sort()
    n = len(gaps)
    if not n:
        return {"n": 0, "median_gap_pts": None, "p90_gap_pts": None,
                "min_gap_pts": None, "verdict": "data kurang — buffer belum bisa dikalifikasi"}
    def pct(p):
        return gaps[min(n - 1, int(p * n))]
    med, p90 = pct(0.5), pct(0.9)
    return {"n": n, "median_gap_pts": med, "p90_gap_pts": p90,
            "min_gap_pts": gaps[0],
            "verdict": (f"SL-hit mepet n={n}: median {med} pts, p90 {p90} pts — "
                        "kalau p90 kecil (<10 pts) SL sering tersentuh oleh "
                        "noise sesaat sebelum harga pulih → buffer layak diuji")}


# ── pilih plan per kandidat (dipakai shadow_ab) ─────────────────────────────
def exit_plan_for(kind: str, direction: str, entry: float, m1: list,
                  m5: list, m15: Optional[list]) -> dict:
    """Dispatch geometri exit per jenis kandidat: 'D' → plan D, 'E' → plan E,
    selain itu → parity dasar 0.9/1.4×ATR-M5 (A/B/C — tidak boleh berubah)."""
    if kind == "D":
        return plan_exit_d(direction, entry, m1, m5, m15)
    if kind == "E":
        return exit_plan_atr_m1(direction, entry, m1)
    atr5 = CS.atr(m5)
    if not atr5 or atr5 <= 0 or entry <= 0:
        return {"ok": False, "reject_reason": "DATA_INVALID:atr_m5",
                "sl": None, "tp": None, "sl_pts": None, "tp_pts": None,
                "burned": False, "clamp": "none"}
    sign = 1.0 if direction == "BULL" else -1.0
    sl_d, tp_d = MV.SL_MULT * atr5, MV.TP_MULT * atr5
    return {"ok": True, "reject_reason": None,
            "sl": round(entry - sign * sl_d, 2), "tp": round(entry + sign * tp_d, 2),
            "sl_pts": _pts(sl_d), "tp_pts": _pts(tp_d),
            "burned": False, "clamp": "none"}
