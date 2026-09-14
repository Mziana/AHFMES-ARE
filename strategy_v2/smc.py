"""SMC/ICT v3 — mesin kandidat pengganti MICRO (owner rencana 2026-09-11).

Sumber: rencana-trading-scalping-xauusd.md (owner). Filosofi top-down:
"HTF memberi peta, LTF memberi pemicu". Obat dua penyakit terdiagnosis
11 Sep (entri terlalu cepat mengejar pola & terlalu lambat setelah harga
jalan): TUNGGU DI ZONA (POI), lalu tuntut BUKTI (liquidity sweep + CHoCH
mikro + pola candle) sebelum entry.

Lapisan (rencana §0-7):
  Bias    : H4 (+D1 bila ada) struktur swing HH/HL-LH/LL + EMA50/200 filter
  Setup   : M15/M5 trend, BOS/CHoCH, Order Block fresh, FVG, EQH/EQL,
            premium/discount
  Entry   : M1 sweep mikro + CHoCH mikro + pola candle (engine pola lama)
  Scorer  : confluence 12 poin (rencana §7) + gate RR>=1.3 (rencana §5)

Exit (rencana §4): SL di luar POI/extrem sweep + buffer 0.15xATR-M5 +
topup spread; TP1 = likuiditas minor terdekat searah (partial 50% + BE
dihandalkan trade-manager di fase berikutnya); TP2 = likuiditas mayor
berlawanan di TF atas. RR dihitung ke TP1.

PURE: tanpa I/O, tanpa now() — semua dari bar. Import di-whitelist
(dijaga test struktural): candle_scoring, simple_variants, micro_v2.
"""
from __future__ import annotations

from typing import Optional

from strategy_v2 import candle_scoring as CS
from strategy_v2 import simple_variants as SV
from strategy_v2 import micro_v2 as MV

POINT = MV.POINT  # 0.01 USD/pt

# ── Parameter default (dikalibrasi dari replay sebelum live; registry Pagar 1)
SWING_K = 2               # fractal k kiri/kanan (rencana §1.1)
EQ_TOL_ATR = 0.15         # toleransi EQH/EQL (rencana §1.2: 0.1-0.2 xATR)
OB_DISP_MULT = 1.2        # displacement minimal leg pembentuk OB (x ATR TF)
FVG_MIN_GAP = 0.05        # FVG diabaikan bila gap < ini xATR (noise)
SWEEP_MIN_WICK = 0.05     # wick menembus level minimal (x ATR TF level)
SWEEP_TOL_ATR = 0.20      # seberapa dekat sweep harus ke level (x ATR)
SWEEP_MAX_AGE = 12        # sweep hanya dihitung bila terjadi N bar terakhir
POI_REACH_ATR = 1.50      # jarak harga ke POI masih dianggap "di POI" (x ATR)
# Mode jangkauan POI (sensitivity prio-7 review):
#   "reach" = legacy — jarak harga ke zona <= POI_REACH xATR (termasuk 0 = di dalam)
#   "strict" = desain §3.1 literal — harga WAJIB di dalam zona (touch), jarak 0
POI_REACH_MODE = "reach"
PD_WINDOW = 60            # window bar premium/discount (H4)
SCORE_THRESHOLD = 8       # rencana §7: threshold 8/12
MIN_RR = 1.3              # rencana §5 (setelah spread/komisi)
SL_BUFFER_ATR = 0.15      # SL di luar POI/extrem sweep (rencana §4)
SL_TOPUP_PTS = 30.0       # topup spread/komisi (pts) — diukur dari data demo

# ── Gate item-8 §7 (WAJIB utk live parity; OPT-IN via gates=True) ──────────
# Desain §6/§7.8: "tidak dalam window berita high-impact & spread normal"
# = gate, bukan skor. Berita historis tidak tersedia (policy
# NEWS_CALENDAR_UNAVAILABLE fail-closed, P0-01) → di replay hanya spread &
# volatilitas yang bisa digate; news gate = jalur live saja. Default OFF
# supaya fixture test tetap deterministik (jendela fixture ATR-nya kecil).
GATE_MAX_SPREAD_PTS = 35.0    # skip bila spread > ini (poin broker, §6)
GATE_ATR_M5_MIN_PTS = 120.0   # ATR-M5 terlalu rendah = pasar sepi (§6)
GATE_ATR_M5_MAX_PTS = 2500.0  # ATR-M5 ekstrem = risiko slippage berita (§6)

# ── G3: freshness BOS (rencana §7 item 4: "BOS sebelum retrace ke POI") ───
# BOS hanya dihitung OK bila event BOS searah TERBARU berumur <= N bar M5.
# None = legacy (tanpa freshness — audit 12 Sep: umur median 129 bar M5,
# item jadi duplikat bias). Angka final dari sweep replay {24, 36, 48}.
BOS_FRESH_M5_BARS = None
PATTERN_TFS = ("M1",)     # pola trigger di M1 (rencana §3.2)

WEIGHTS = {  # rencana §7 (non-gate max 12)
    "bias_h4": 2,        # bias H4 searah (struktur swing)
    "discount": 1,       # premium/discount terhadap range H4
    "poi_fresh": 2,      # POI (OB/FVG) fresh & searah
    "bos": 1,            # BOS searah di M15/M5 sebelum retrace
    "sweep": 2,          # liquidity sweep sebelum reaksi
    "choch_micro": 2,    # CHoCH mikro M1/M5 setelah sweep
    "pattern": 2,        # pola candle valid di POI
}


# ── util ────────────────────────────────────────────────────────────────────
def _o(b): return float(b["open"])
def _h(b): return float(b["high"])
def _l(b): return float(b["low"])
def _c(b): return float(b["close"])
def _t(b): return int(b["time"])


def _violated(bars, from_idx, ztype: str, top: float, bottom: float) -> bool:
    """Zona (OB/FVG) dianggap habis bila CLOSE menembus sisi jauh (bull: close
    < bottom; bear: close > top). Sentuhan wick TIDAK memitigasi — wick di
    zona justru liquidity grab yang ingin kita react-kan (rencana §2.3/§3.1)."""
    for i in range(from_idx + 1, len(bars)):
        c = _c(bars[i])
        if ztype == "bull" and c < bottom:
            return True
        if ztype == "bear" and c > top:
            return True
    return False


def swings_seq(bars, k: int = SWING_K):
    """Swing terindeks kronologis: [(idx, 'H'|'L', price)] — fraktal k kiri/
    kanan (rencana §1.1). Dedupe: swing searah beruntun ambil yang ekstrem."""
    out = []
    for i in range(k, len(bars) - k):
        win = bars[i - k:i + k + 1]
        if _h(bars[i]) >= max(_h(x) for x in win):
            if out and out[-1][1] == "H":
                if _h(bars[i]) >= out[-1][2]:
                    out[-1] = (i, "H", _h(bars[i]))
                continue
            out.append((i, "H", _h(bars[i])))
        if _l(bars[i]) <= min(_l(x) for x in win):
            if out and out[-1][1] == "L":
                if _l(bars[i]) <= out[-1][2]:
                    out[-1] = (i, "L", _l(bars[i]))
                continue
            out.append((i, "L", _l(bars[i])))
    return out


def structure_trend(bars, k: int = SWING_K) -> Optional[str]:
    """BULL bila HH+HL mayoritas; BEAR bila LH+LL; None bila campur/range
    (rencana §1.1: ranging = kurangi ukuran/tunggu breakout).
    Perbandingan antar-swing SEJENIS (high vs high, low vs low) — bukan
    antar-transisi."""
    sw = swings_seq(bars, k)
    highs = [p for _, t, p in sw if t == "H"][-4:]
    lows = [p for _, t, p in sw if t == "L"][-4:]
    up = dn = 0
    for a, b in zip(highs, highs[1:]):
        if b > a:
            up += 1
        elif b < a:
            dn += 1
    for a, b in zip(lows, lows[1:]):
        if b > a:
            up += 1
        elif b < a:
            dn += 1
    if up >= 2 and up > dn:
        return "BULL"
    if dn >= 2 and dn > up:
        return "BEAR"
    return None


def bos_choch(bars, k: int = SWING_K):
    """Event struktur anti-lookahead (rencana §2.2): swing hanya "tahu" k bar
    SETELAH bar swing (konfirmasi fraktal). BOS = close menembus level swing
    searah break sebelumnya; CHoCH = break pertama yang BERLAWANAN arah break
    terakhir (perubahan karakter). Return list {type, dir, level, idx}.
    Konvensi: break pertama pada data dilabel BOS (belum ada karakter)."""
    sw = swings_seq(bars, k)
    events = []
    cur_h = cur_l = None
    last_dir = None
    si = 0
    for i in range(k + 1, len(bars)):
        # swing baru boleh dipakai hanya SETELAH window konfirmasinya (k bar
        # kanan) seluruhnya close — strict `<` mencegah lookahead 1 bar.
        while si < len(sw) and sw[si][0] + k < i:
            _, t, p = sw[si]
            if t == "H":
                cur_h = p
            else:
                cur_l = p
            si += 1
        c = _c(bars[i])
        d = None
        if cur_h is not None and c > cur_h:
            d, lvl = "BULL", cur_h
            cur_h = None  # level lama sudah dilanggar; tunggu swing high baru
        elif cur_l is not None and c < cur_l:
            d, lvl = "BEAR", cur_l
            cur_l = None
        if d:
            typ = "BOS" if (last_dir is None or last_dir == d) else "CHoCH"
            events.append({"type": typ, "dir": d, "level": lvl, "idx": i})
            last_dir = d
    return events


def equal_levels(bars, side: str, a: float, tol_mult: float = EQ_TOL_ATR):
    """EQH (side='H') / EQL ('L'): cluster swing yang hampir sama
    (rencana §1.2) → [(price, n_member, idx_terakhir)]."""
    sw = [s for s in swings_seq(bars) if s[1] == side]
    lv = sorted([p for _, _, p in sw])
    out = []
    tol = tol_mult * a
    i = 0
    while i < len(lv):
        j = i
        while j + 1 < len(lv) and lv[j + 1] - lv[i] <= tol:
            j += 1
        grp = lv[i:j + 1]
        if len(grp) >= 2:
            out.append((sum(grp) / len(grp), len(grp), 0))
        i = j + 1
    return out


def detect_sweep(bars, level: float, side: str, a: float,
                 t_from: int = 0) -> Optional[dict]:
    """Sweep (rencana §2.3/§3.1): wick menembus level (>=SWEEP_MIN_WICK xATR)
    lalu close MENGEMBALI ke sisi semula → SFP. Return {idx, extreme}."""
    min_wick = SWEEP_MIN_WICK * a
    for i in range(1, len(bars)):
        b = bars[i]
        if side == "H" and _h(b) > level + min_wick and _c(b) < level:
            return {"idx": i, "extreme": _h(b)}
        if side == "L" and _l(b) < level - min_wick and _c(b) > level:
            return {"idx": i, "extreme": _l(b)}
    return None


def order_blocks(bars, k: int = SWING_K):
    """OB (rencana §2.4): candle berlawanan TERAKHIR sebelum leg impulsif yang
    menghasilkan BOS. Fresh = harga belum kembali menyentuh zona sejak terbentuk
    (dihitung dari bar SESUDAH OB sampai akhir slice)."""
    sw = swings_seq(bars, k)
    obs = []
    for j in range(1, len(sw)):
        (i0, t0, p0), (i1, t1, p1) = sw[j - 1], sw[j]
        if t0 == t1:
            continue
        up = (t1 == "H" and p1 > p0) if t0 == "L" else False
        dn = (t1 == "L" and p1 < p0) if t0 == "H" else False
        if not (up or dn):
            continue
        leg = abs(p1 - p0)
        # displacement diukur vs ATR window penuh (satu sumber utk semua
        # kandidat OB; tanpa ATR terhitung (<15 bar) kita TIDAK bisa menilai
        # displacement → skip — fallback lama leg/3 membuat filter vakua)
        a = CS.atr(bars)
        if a is None or leg < OB_DISP_MULT * a:
            continue  # displacement kurang (rencana §2.4)
        # candle berlawanan terakhir sebelum mulai leg (dari i0 mundur)
        start = i0
        while start > 0 and ((up and _c(bars[start]) > _o(bars[start])) or
                             (dn and _c(bars[start]) < _o(bars[start]))):
            start -= 1
        b = bars[start]
        # zona = range PENUH candle (termasuk wick), bukan body — "SL di luar
        # POI" (rencana §4) berarti di belakang extrem wick; body-only bisa
        # menaruh SL di tengah wilayah wick yang justru jadi sasaran hunt.
        top, bot = _h(b), _l(b)
        obs.append({"type": "bull" if up else "bear", "top": top, "bottom": bot,
                    "idx": start, "leg_end": i1, "fresh": True})
    # fresh = zona belum dilanggar close setelah leg selesai (lihat _violated)
    for ob in obs:
        ob["fresh"] = not _violated(bars, ob["leg_end"], ob["type"],
                                    ob["top"], ob["bottom"])
    return obs


def fvgs(bars):
    """FVG 3-candle (rencana §2.5): bullish = high[c1] < low[c3]; bearish =
    low[c1] > high[c3]. gap_min utk buang noise. Mitigated bila price
    kembali masuk gap setelah terbentuk."""
    a = CS.atr(bars) or 0.3
    out = []
    for i in range(2, len(bars)):
        c1, c3 = bars[i - 2], bars[i]
        if _h(c1) < _l(c3):
            top, bot = _l(c3), _h(c1)
            if top - bot >= FVG_MIN_GAP * a:
                out.append({"type": "bull", "top": top, "bottom": bot, "idx": i})
        elif _l(c1) > _h(c3):
            top, bot = _l(c1), _h(c3)
            if top - bot >= FVG_MIN_GAP * a:
                out.append({"type": "bear", "top": top, "bottom": bot, "idx": i})
    for f in out:
        f["fresh"] = not _violated(bars, f["idx"], f["type"],
                                   f["top"], f["bottom"])
    return out


def premium_discount(h4_bars, price: float) -> Optional[str]:
    """DISCOUNT bila harga di bawah 50% range window H4 (cari BUY),
    PREMIUM bila di atas (cari SELL) — rencana §1.3."""
    if len(h4_bars) < 10:
        return None
    w = h4_bars[-PD_WINDOW:] if len(h4_bars) >= PD_WINDOW else h4_bars
    hi, lo = max(_h(b) for b in w), min(_l(b) for b in w)
    if hi <= lo:
        return None
    eq = (hi + lo) / 2
    return "DISCOUNT" if price < eq else "PREMIUM"


def nearest_liquidity_target(bars, direction: str, price: float, a: float):
    """TP: likuiditas terdekat searah (old high/low + EQH/EQL, §2.6/§4)."""
    cands = [p for _, _, p in swings_seq(bars)]
    if direction == "BULL":
        cands += [p for p, _, _ in equal_levels(bars, "H", a)]
        ahead = [p for p in cands if p > price + 0.1 * a]
        return min(ahead) if ahead else None
    cands += [p for p, _, _ in equal_levels(bars, "L", a)]
    ahead = [p for p in cands if p < price - 0.1 * a]
    return max(ahead) if ahead else None


# ── evaluate end-to-end ─────────────────────────────────────────────────────
def evaluate(m1, m5, m15, h4, spread_pts: float = 0.0,
             bos_fresh_bars: Optional[int] = None, gates: bool = False,
             min_score: Optional[int] = None,
             poi_reach: Optional[float] = None,
             poi_mode: Optional[str] = None) -> dict:
    """Keputusan SMC lengkap (rencana §7-8). Return {take, reason, direction,
    score, checklist, sl, tp1, tp2, rr, sl_pts, tp1_pts, tp2_pts} +
    {components, bos_age_m5, atr_m5_pts} utk rescoring varian & audit.

    Path entry (rencana §3.3): harga di POI fresh (Model A continuation)
    ATAU baru melakukan sweep likuiditas (Model B reversal), lalu CHoCH mikro
    M1 searah + pola candle M1 searah. Semua searah bias H4.

    bos_fresh_bars: G3 — BOS hanya dihitung bila event searah terbaru
    berumur <= N bar M5 (None = legacy). gates: G1 — gate item-8
    (spread/ATR) aktif; spread_pts=0 + gates=False = perilaku legacy penuh.
    min_score: threshold skor (None = SCORE_THRESHOLD default 8) — utk
    kurva kalibrasi prio-4 review, tanpa menyentuh konfigurasi live.
    poi_reach/poi_mode: sensitivity POI (prio-7) — None = default modul
    (POI_REACH_ATR/POI_REACH_MODE); poi_mode="strict" = harga wajib di
    dalam zona (desain §3.1), abaikan poi_reach.
    """
    ch = []  # checklist manusia-baca
    # warmup minimum per TF: h4 utk struktur+EMA, m5/m1 utk ATR/pola/POI.
    # m15 hanya dipakai sebagai sumber POI/BOS opsional — tidak digate.
    if len(h4) < 25 or len(m5) < 30 or len(m1) < 30:
        return _no("data TF kurang", ch)
    price = _c(m1[-1])
    a15 = CS.atr(m15) or 0.0
    a5 = CS.atr(m5) or 0.0

    # Gate item-8 (desain §7.8/§6, opt-in): spread & volatilitas normal.
    if gates:
        if spread_pts > GATE_MAX_SPREAD_PTS:
            return _no(f"gate spread {spread_pts:.0f}p > "
                       f"{GATE_MAX_SPREAD_PTS:.0f}p — skip", ch)
        atr5_pts = a5 / POINT if a5 else 0.0
        if not (GATE_ATR_M5_MIN_PTS <= atr5_pts <= GATE_ATR_M5_MAX_PTS):
            return _no(f"gate ATR-M5 {atr5_pts:.0f}p di luar "
                       f"[{GATE_ATR_M5_MIN_PTS:.0f}, "
                       f"{GATE_ATR_M5_MAX_PTS:.0f}]p — skip", ch)

    # 1) bias H4 (struktur + EMA50/200 filter kedua, rencana §1.1)
    bias = structure_trend(h4)
    closes4 = [_c(b) for b in h4]
    e50, e200 = CS.ema(closes4, 50), CS.ema(closes4, 200)
    if bias == "BULL" and e50 and e200 and e50 < e200:
        ch.append({"k": "Filter EMA50/200 H4", "ok": False,
                   "note": "EMA50 < EMA200 melawan bias BULL"})
    ch.append({"k": "Bias H4 (HH/HL-LH/LL)", "ok": bias is not None,
               "note": bias or "ranging/campur — no trade"})
    if not bias:
        return _no("bias H4 netral/campur", ch)
    direction = "BUY" if bias == "BULL" else "SELL"

    score = WEIGHTS["bias_h4"]  # bias searah: 2

    # 2) premium/discount (rencana §1.3, skor 1)
    pd = premium_discount(h4, price)
    pd_ok = (pd == "DISCOUNT") if direction == "BUY" else (pd == "PREMIUM")
    if pd_ok:
        score += WEIGHTS["discount"]
    ch.append({"k": "Premium/Discount (range H4)", "ok": pd_ok,
               "note": f"{pd} vs bias {bias}"})

    # 3) POI: OB/FVG fresh di M15/M5 searah, harga dalam jangkauan (skor 2)
    pois = [o for o in order_blocks(m15) + fvgs(m15) + order_blocks(m5) + fvgs(m5)
            if o.get("fresh")]
    want = "bull" if direction == "BUY" else "bear"
    pois = [p for p in pois if p["type"] == want]
    a_sel = a15 if a15 else a5
    def _dist(p):
        top, bot = p["top"], p["bottom"]
        if bot <= price <= top:
            return 0.0
        return (bot - price) if price < bot else (price - top)
    reach = POI_REACH_ATR if poi_reach is None else poi_reach
    mode = POI_REACH_MODE if poi_mode is None else poi_mode
    if mode == "strict":   # desain §3.1: reaksi WAJIB terjadi di dalam zona
        pois = [p for p in pois if _dist(p) <= 0.0]
    else:                  # legacy "reach": jarak <= reach xATR
        pois = [p for p in pois if _dist(p) <= reach * a_sel]
    pois = sorted(pois, key=_dist)
    poi_ok = bool(pois)
    if poi_ok:
        score += WEIGHTS["poi_fresh"]
    poi = pois[0] if pois else None
    ch.append({"k": "POI fresh (OB/FVG M15/M5)", "ok": poi_ok,
               "note": (f"{poi['type']} {poi['bottom']:.2f}-{poi['top']:.2f} "
                        f"jarak {_dist(poi)/a_sel:.2f}xATR") if poi else
                       "tidak ada POI fresh searah dalam jangkauan"})

    # 4) BOS searah di M15/M5 (skor 1). G3: "BOS SEBELUM retrace ke POI"
    #    (rencana §7 item 4) → bila bos_fresh_bars di-set, item hanya OK
    #    bila event BOS searah TERBARU berumur <= N bar M5. Umur diukur dari
    #    waktu close bar break (anti-lookahead: bar closed saja).
    ev15, ev5 = bos_choch(m15), bos_choch(m5)
    bos_events = [e for e in ev15 + ev5
                  if e["dir"] == bias and e["type"] == "BOS"]
    bos_age_m5 = None
    if bos_events:
        t_new = None
        for e in ev5:
            if e["dir"] == bias and e["type"] == "BOS":
                t = int(m5[e["idx"]]["time"]) + 300  # close-time bar break
                t_new = t if t_new is None else max(t_new, t)
        for e in ev15:
            if e["dir"] == bias and e["type"] == "BOS":
                t = int(m15[e["idx"]]["time"]) + 900
                t_new = t if t_new is None else max(t_new, t)
        if t_new is not None:
            m5_ts = [int(_t(b)) for b in m5]
            pos = len(m5_ts)
            while pos > 0 and m5_ts[pos - 1] >= t_new:
                pos -= 1
            bos_age_m5 = len(m5_ts) - pos  # jumlah bar M5 close setelah break
    bos_ok = bool(bos_events) and (
        bos_fresh_bars is None or
        (bos_age_m5 is not None and bos_age_m5 <= bos_fresh_bars))
    if bos_ok:
        score += WEIGHTS["bos"]
    ch.append({"k": "BOS searah (M15/M5)", "ok": bos_ok,
               "note": (f"{len(bos_events)} event · umur terbaru "
                        f"{bos_age_m5}b M5") if bos_events else "0 event"})

    # 5) liquidity sweep (skor 2): Model B — sweep EQH/EQL M5/M15 ATAU
    #    sweep old high/low; dihitung di M1 (mikro) dan M5 (mayor)
    a1 = CS.atr(m1) or 0.0
    sweep_info = None
    for bars, side, a_tf in ((m5, "H" if direction == "SELL" else "L", a5),
                             (m15, "H" if direction == "SELL" else "L", a15),
                             (m1, "H" if direction == "SELL" else "L", a1)):
        levels = equal_levels(bars, side, a_tf)
        if not levels:  # fallback: old high/low TERETABLISH (rencana §1.2) —
            # level dari region yang sudah lama closing (bukan extremum segar
            # yang justru adalah sweep itu sendiri)
            est = bars[:-SWEEP_MAX_AGE] if len(bars) > SWEEP_MAX_AGE else bars
            if not est:
                continue
            lv0 = (max(_h(b) for b in est) if side == "H"
                   else min(_l(b) for b in est))
            levels = [(lv0, 1, 0)]
        win = bars[-40:]
        for lv, n, _ in levels:
            sw = detect_sweep(win, lv, side, a_tf)
            if sw and sw["idx"] >= len(win) - SWEEP_MAX_AGE:  # harus segar
                # sweep harus searah kontra lalu ditolak: utk BUY, sweep LOW
                sweep_info = {"side": side, "level": lv, "bars_tf": True,
                              "idx_rel": sw["idx"], "extreme": sw["extreme"]}
                break
        if sweep_info:
            break
    sweep_ok = sweep_info is not None
    if sweep_ok:
        score += WEIGHTS["sweep"]
    ch.append({"k": "Liquidity sweep (SFP)", "ok": sweep_ok,
               "note": (f"sweep {'EQH/old high' if sweep_info and sweep_info['side']=='H' else 'EQL/old low'} "
                        f"@{sweep_info['level']:.2f}" if sweep_info else
                       "tidak ada sweep segar")})

    # 6) CHoCH mikro di M1 setelah sweep (skor 2, rencana §3.1)
    ev1 = [e for e in bos_choch(m1) if e["idx"] >= len(m1) - 30]
    choch_ok = any(e["dir"] == bias for e in ev1)
    if choch_ok:
        score += WEIGHTS["choch_micro"]
    ch.append({"k": "CHoCH mikro M1 (30 bar terakhir)", "ok": choch_ok,
               "note": f"{len(ev1)} event mikro"})

    # 7) pola candle M1 searah (skor 2 — engine pola lama)
    pats = CS.detect_patterns(m1)
    pat = pats[-1] if pats else None
    pat_ok = bool(pat and pat[1] == bias)
    if pat_ok:
        score += WEIGHTS["pattern"]
    ch.append({"k": "Pola candle M1", "ok": pat_ok,
               "note": f"{pat[0]} {pat[1]}" if pat else "tidak ada pola"})

    # 8-9) gates: RR >= 1.3 (rencana §5); SL di luar POI/extrem sweep (§4)
    a_ref = a5 if a5 else a1
    sl_base = None
    if poi and ((direction == "BUY" and poi["type"] == "bull") or
                (direction == "SELL" and poi["type"] == "bear")):
        cand = poi["bottom"] if direction == "BUY" else poi["top"]
        if (direction == "BUY" and cand < price) or \
           (direction == "SELL" and cand > price):
            sl_base = cand  # POI hanya anchor SL bila di sisi yang benar
    if sweep_info:
        ext = sweep_info["extreme"]
        # anchor sweep HANYA bila extrem di sisi yang benar dari harga SEKARANG
        # (sweep lama yang sudah kedodoran harga tidak boleh jadi SL — dulu
        # `ext < (sl_base or 1e9)` selalu true saat sl_base None → SL terbalik
        # utk BUY: sl > entry → RR palsu & label SL dgn gross positif).
        if direction == "BUY" and ext < price and (sl_base is None or ext < sl_base):
            sl_base = ext
        if direction == "SELL" and ext > price and (sl_base is None or ext > sl_base):
            sl_base = ext
    if sl_base is None:
        return _no("tidak ada acuan SL struktural (POI/sweep)", ch, score=score)
    # guard fail-closed terakhir: SL wajib di sisi yang benar dari harga
    if ((direction == "BUY" and sl_base >= price) or
            (direction == "SELL" and sl_base <= price)):
        return _no("tidak ada acuan SL struktural (POI/sweep)", ch, score=score)
    buf = SL_BUFFER_ATR * a_ref + (SL_TOPUP_PTS + spread_pts) * POINT
    sl = sl_base - buf if direction == "BUY" else sl_base + buf
    tp1 = nearest_liquidity_target(m5, bias, price, a_ref)
    if tp1 is None:
        return _no("tidak ada target likuiditas searah", ch, score=score)
    risk = abs(price - sl)
    reward1 = abs(tp1 - price)
    rr = reward1 / risk if risk > 0 else 0
    rr_ok = rr >= MIN_RR
    ch.append({"k": f"RR ke TP1 >= {MIN_RR}", "ok": rr_ok,
               "note": f"RR {rr:.2f} · SL {abs(price-sl)/POINT:.0f}p · TP1 {reward1/POINT:.0f}p"})
    if not rr_ok:
        return _no(f"RR {rr:.2f} < {MIN_RR}", ch, score=score)

    thresh = SCORE_THRESHOLD if min_score is None else min_score
    take = score >= thresh
    reason = (f"skor {score}/{sum(WEIGHTS.values())} >= {thresh}"
              if take else f"skor {score} < {thresh} — wait")
    return {"take": take, "reason": reason, "direction": direction,
            "score": score, "max_score": sum(WEIGHTS.values()),
            "checklist": ch, "sl": round(sl, 2),
            "tp1": round(tp1, 2), "tp2": None,
            "sl_pts": round(abs(price - sl) / POINT, 1),
            "tp1_pts": round(reward1 / POINT, 1), "rr": round(rr, 2),
            "poi": ({"type": poi["type"], "top": poi["top"],
                     "bottom": poi["bottom"]} if poi else None),
            "pd": pd, "bias": bias,
            "bos_age_m5": bos_age_m5,
            "atr_m5_pts": round(a5 / POINT, 1) if a5 else None,
            "components": {"pd_ok": bool(pd_ok), "poi_ok": bool(poi_ok),
                           "bos_ok": bool(bos_ok), "sweep_ok": bool(sweep_ok),
                           "choch_ok": bool(choch_ok), "pattern_ok": bool(pat_ok)}}


def _no(reason, ch, score=0.0):
    return {"take": False, "reason": reason, "direction": None, "score": score,
            "max_score": sum(WEIGHTS.values()), "checklist": ch, "sl": None,
            "tp1": None, "tp2": None, "sl_pts": None, "tp1_pts": None,
            "rr": None, "poi": None, "pd": None, "bias": None,
            "bos_age_m5": None, "atr_m5_pts": None, "components": {}}
