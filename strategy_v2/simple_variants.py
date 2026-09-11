"""Simple Variants — bias + level + SL/TP untuk 2 arm demo (owner spec final).

MICRO (rev3 2026-09-10, owner rules):
  ARAH     = momentum M15 (EMA9/21 + RSI band 45/55) — SATU-SATUNYA penentu
             arah. Band menggantikan RSI-50 keras (bukti 48 jam: RSI-50
             memblok 8% waktu di momen EMA fresh-cross; band membuka +10%
             waktu arah tanpa mengizinkan zona jenuh — RSI guard 65/35 tetap).
  struktur = VETO saja: menolak HANYA bila JELAS BERTENTANGAN (mayoritas
             2/3 swing, margin 0.25xATR — aturan margin+mayoritas tetap).
             Struktur CAMPUR (None) → tetap boleh entry (bukti replay 5 jam:
             aturan searah = 0 entri; campur-boleh = 14 entri 10W/4L).
  cooldown = 5 menit antar entri MICRO (terbukti buang entri sampah:
             28→14 entri, win rate 60%→71%).
  eksekusi = bar close M1 — pola & skor inti di M1 (threshold 6)
  multi-TF = skor konteks M5 & M15 (pola+kualitas): searah >=3 -> +1,
             melawan >=3 -> -1 (tampil per-TF di UI, owner request)
  RSI guard = M15 + M5 + M1 (stop buy >=70, stop sell <=30 — rev3)
  momentum-habis = diukur di M5 (M1 terlalu volatile utk aturan ini),
             rally-aware: retrace >61.8% ATAU marubozu+volume (owner: rally
             bisa 2,3,4,5 candle — diukur dari % koreksi run, bukan jumlah)
  H4 soft  = candle H4 terakhir melawan arah -> penalti -1 (tidak pernah blok)
  SL/TP    = ATR M1, clamp SL 130-210 pts, TP 200-300 pts (rasio ~1:1.47;
             owner: sekitar 170/250, ikut ATR, jangan beku & jangan liar)
  TP guard = TP tidak boleh melintasi swing M15/M5 berlawanan terdekat
             (buffer 0.25xATR) — entry ditolak bila jarak jadi terlalu kecil
SCALP (rev2 2026-09-10, owner: struktur HH/HL H4 DIHAPUS — tidak berguna):
  bias = momentum M15 saja; level = pullback EMA9/21 M5;
  volume wajib 1.2x; SL 1.25xATR / TP 2.0xATR; threshold 7

REV3 2026-09-10 (owner — paket perbaikan setelah audit 5 jam MICRO 0 entri):
  - POLA WAJIB SEARAH bias momentum — MICRO SAJA. (Awalnya kedua arm;
    owner membatalkan utk SCALP sore hari ini setelah 3 win beruntun yang
    salah satunya justru pola-vs-bias: BUY dgn three_black_crows +$.
    Bukti replay MICRO: 12/16 entri hipotetis pola berlawanan; dgn gate
    searah 9 entri 9W/0L — gate tetap utk MICRO.)
  - RSI guard 65/35 → 70/30: 65/35 bertentangan dengan band bias 45/55
    (koridor efektif tinggal 45-65) dan memblok trend kuat — 130/369 bar M1
    terblok guard di window replay (35%), jadi pemblokir terbesar bersama TP.
  - TP minimum 200 → 100 pts: TP-vs-swing memotong 123/369 bar (33%) sampai
    di bawah 200 → entry DITOLAK (bukan dipendekkan). Pemotongan-vs-swing
    tetap jalan; hanya ambang penolaknya diturunkan (replay: 16 entri 15W/1L).

Lot tetap: balance > 150 -> 0.02, else 0.01 (tanpa risk persen).
News gate: blok entry bila big-news dalam +/-30 menit.
PURE: semua perhitungan dari bar; tidak ada I/O / now() / random.
"""
from __future__ import annotations

from typing import Optional

from strategy_v2 import candle_scoring as CS

SL_TP = {
    "SCALP": {"sl_mult": 1.25, "tp_mult": 2.0},
}
# MICRO: SL/TP = ATR M1 di-clamp ke range owner (sekitar 170/250 pts).
MICRO_SL_CLAMP = (130.0, 210.0)   # poin (0.01 USD/pt)
MICRO_TP_CLAMP = (200.0, 300.0)
MICRO_TP_MIN_POINTS = 100.0       # rev3 (dulu 200): bila TP-vs-resistance memotong di bawah ini -> tolak
TP_OPP_BUFFER_ATR = 0.25          # TP berhenti 0.25xATR sebelum swing berlawanan
LOT_ABOVE = 0.02
LOT_BELOW = 0.01
LOT_THRESHOLD_BALANCE = 150.0
NEWS_BUFFER_MIN = 30
# Owner decision 2026-09-10: news gate DIMATIKAN. Kalender yang tersedia masih
# simulasi (jadwal statis) dan memblokir entry berjam-jam dengan jadwal yang
# salah (window ±30 menit di sekitar event = total 60 menit). Fungsi
# news_block() dipertahankan + tetap dites — tinggal set True saat kalender
# real (ForexFactory dkk.) terpasang.
NEWS_GATE_ENABLED = False
KILL_STREAK = 3
KILL_COOLDOWN_S = 30 * 60
# Band momentum (owner rev3): RSI 50 keras → band 45/55. BULL butuh RSI >= 45,
# BEAR butuh RSI <= 55 — EMA9/21 tetap penentu arah utama; RSI di sini hanya
# memastikan tidak mengikuti EMA di zona ekstrem sekalipun.
MOM_RSI_BULL_MIN = 45.0
MOM_RSI_BEAR_MAX = 55.0
H4_SOFT_PENALTY = -1.0            # candle H4 terakhir melawan arah (owner: lembut)
CONTEXT_TF_MIN = 3.0              # skor konteks TF besar utk dianggap "searah kuat"
MICRO_COOLDOWN_S = 5 * 60         # owner rev2: jeda antar entri MICRO (5 menit)

# RSI ekstrem guard (owner rev3, dulu 65/35): RSI >= 70 → stop BUY;
# RSI <= 30 → stop SELL. 65/35 bertentangan dengan band bias 45/55 dan
# memblok trend kuat (35% bar M1 di replay). 70/30 = jenuh sejati.
# MICRO: berlaku di M15 + M5 + M1 (ketiganya harus netral-dari-jenuh).
RSI_STOP_BUY = 70.0
RSI_STOP_SELL = 30.0


# ── Bias ─────────────────────────────────────────────────────────────────────
def momentum_bias(m15_bars) -> Optional[str]:
    """EMA9 >= EMA21 dan RSI >= 45 -> BULL; EMA9 < EMA21 dan RSI <= 55 -> BEAR;
    else None. Band 45/55 (owner rev3) — EMA tetap penentu utama, RSI tidak
    lagi memblokir momen EMA fresh-cross di zona 45-55."""
    closes = [b["close"] for b in m15_bars]
    e9, e21 = CS.ema(closes, 9), CS.ema(closes, 21)
    r = CS.rsi(closes, 14)
    if e9 is None or e21 is None or r is None:
        return None
    if e9 >= e21 and r >= MOM_RSI_BULL_MIN:
        return "BULL"
    if e9 < e21 and r <= MOM_RSI_BEAR_MAX:
        return "BEAR"
    return None


def structure_bias(bars) -> Optional[str]:
    return CS.structure_direction(bars)


# ── Level eksekusi ───────────────────────────────────────────────────────────
def m15_execution_levels(m15_bars):
    """Swing high/low M15 terakhir (fraktal)."""
    highs, lows = CS._swings(m15_bars)
    return (lows[-1] if lows else None, highs[-1] if highs else None)


def m5_ema_levels(m5_bars):
    e9 = CS.ema([b["close"] for b in m5_bars], 9)
    e21 = CS.ema([b["close"] for b in m5_bars], 21)
    return e9, e21


def nearest_level(direction: str, profile: str, m5_bars, m15_bars,
                  m1_bars=None) -> Optional[float]:
    """Level eksekusi utk arah sinyal.

    MICRO (rev): swing TERDEKAT searah trend dari M5 ATAU M1 — support
    terdekat di bawah utk BUY, resistance terdekat di atas utk SELL.
    SCALP: EMA9/21 M5 terdekat (pullback).
    """
    px = m1_bars[-1]["close"] if m1_bars else m5_bars[-1]["close"]
    if profile == "MICRO":
        cands = []
        for bars in (m1_bars or [], m5_bars):
            highs, lows = CS._swings(bars)
            if direction == "BULL":
                below = [l for l in lows if l <= px]
                if below:
                    cands.append(max(below))
            else:
                above = [h for h in highs if h >= px]
                if above:
                    cands.append(min(above))
        return min(cands, key=lambda v: abs(px - v)) if cands else None
    e9, e21 = m5_ema_levels(m5_bars)
    opts = [x for x in (e9, e21) if x is not None]
    if not opts:
        return None
    if direction == "BULL":
        below = [v for v in opts if v <= px]
        return max(below) if below else max(opts)
    above = [v for v in opts if v >= px]
    return min(above) if above else min(opts)


# ── SL/TP + lot ──────────────────────────────────────────────────────────────
def compute_sl_tp(profile: str, direction: str, bars, entry: float) -> Optional[dict]:
    """SL/TP murni dari ATR (owner: "SL/TP berdasarkan ATR saja").

    MICRO: ATR M1 — sl_dist = 1.5*ATR di-clamp 130-210 pts, tp_dist =
    1.47*ATR di-clamp 200-300 pts (owner: sekitar 170/250, ikut ATR, jangan
    beku & jangan liar). Tanpa penyetelan wick — bug RR trade#1 (SL wick
    sempit 170p vs TP 546p) lahir dari proteksi wick; sudah dihapus.
    SCALP: rasio 1.25/2.0 xATR.
    """
    a = CS.atr(bars)
    if not a or entry <= 0:
        return None
    point = 0.01
    if profile == "MICRO":
        sl_dist = min(max(1.5 * a / point, MICRO_SL_CLAMP[0]), MICRO_SL_CLAMP[1]) * point
        tp_dist = min(max(1.47 * a / point, MICRO_TP_CLAMP[0]), MICRO_TP_CLAMP[1]) * point
    else:
        m = SL_TP["SCALP"]
        sl_dist, tp_dist = m["sl_mult"] * a, m["tp_mult"] * a
    if direction == "BULL":
        sl, tp = entry - sl_dist, entry + tp_dist
    else:
        sl, tp = entry + sl_dist, entry - tp_dist
    return {"sl": round(sl, 2), "tp": round(tp, 2),
            "sl_points": round(abs(entry - sl) / point, 1),
            "tp_points": round(abs(tp - entry) / point, 1)}


def clamp_tp_to_structure(profile: str, direction: str, entry: float,
                          tp: float, m5_bars, m15_bars) -> tuple:
    """TP tidak boleh melintasi swing berlawanan terdekat (owner setuju).

    Return (tp_baru, info). Bila hasil pemotongan < MICRO_TP_MIN_POINTS dari
    entry (MICRO) → pemanggil menolak entry ("TP menabrak struktur").
    """
    point = 0.01
    a = CS.atr(m5_bars) or CS.atr(m15_bars) or 20 * point
    opps = []
    highs, lows = CS._swings(m15_bars)
    opps += highs if direction == "BULL" else lows
    highs5, lows5 = CS._swings(m5_bars)
    opps += highs5 if direction == "BULL" else lows5
    if not opps:
        return tp, "tidak ada swing berlawanan — TP ATR penuh"
    if direction == "BULL":
        ahead = [x for x in opps if x > entry]
        if not ahead:
            return tp, "tidak ada resistance di atas — TP ATR penuh"
        limit = min(ahead) - TP_OPP_BUFFER_ATR * a
        if limit < tp:
            return round(limit, 2), f"TP dipotong di swing berlawanan {min(ahead):.2f} (−buffer)"
        return tp, "TP sebelum swing berlawanan — ATR penuh"
    ahead = [x for x in opps if x < entry]
    if not ahead:
        return tp, "tidak ada support di bawah — TP ATR penuh"
    limit = max(ahead) + TP_OPP_BUFFER_ATR * a
    if limit > tp:
        return round(limit, 2), f"TP dipotong di swing berlawanan {max(ahead):.2f} (+buffer)"
    return tp, "TP sebelum swing berlawanan — ATR penuh"


def fixed_lot(balance: float) -> float:
    return LOT_ABOVE if balance > LOT_THRESHOLD_BALANCE else LOT_BELOW


# ── News gate ────────────────────────────────────────────────────────────────
def news_block(events, now_epoch: int) -> Optional[str]:
    """events: list {time:'HH:MM', impact} (UTC). Return nama event bila big news
    dalam +/- NEWS_BUFFER_MIN menit, else None."""
    if not events:
        return None
    import datetime as _dt
    d = _dt.datetime.fromtimestamp(int(now_epoch), _dt.timezone.utc)
    now_min = d.hour * 60 + d.minute
    for ev in events:
        if str(ev.get("impact", "")).upper() != "HIGH":
            continue
        try:
            hh, mm = str(ev["time"]).split(":")
            ev_min = int(hh) * 60 + int(mm)
        except Exception:
            continue
        if abs(now_min - ev_min) <= NEWS_BUFFER_MIN:
            return str(ev["event"])
    return None


# ── Kill switch per arm: 3 lose streak -> cooldown 30 menit ─────────────────
class KillSwitch:
    def __init__(self, streak=KILL_STREAK, cooldown_s=KILL_COOLDOWN_S):
        self.streak_limit = streak
        self.cooldown_s = cooldown_s
        self.lose_streak = 0
        self.until = 0.0
        self.manual_override = False

    def record_loss(self, ts: float):
        self.lose_streak += 1
        if self.lose_streak >= self.streak_limit:
            self.until = ts + self.cooldown_s

    def record_win(self):
        self.lose_streak = 0

    def blocked(self, ts: float) -> bool:
        if self.manual_override:
            return False
        return ts < self.until

    def remaining_min(self, ts: float) -> int:
        return int(max(0.0, self.until - ts) // 60)

    def to_dict(self):
        return {"lose_streak": self.lose_streak, "until": self.until,
                "manual_override": self.manual_override}


# ── Keputusan satu arm ───────────────────────────────────────────────────────
def decide(profile: str, m5_bars, m15_bars, h4_bars, balance: float,
           news_events=None, now_epoch: int = 0, kill: KillSwitch = None,
           m1_bars=None, last_entry_ts: float = None) -> dict:
    """Return dict keputusan + checklist manusia-baca per aturan.

    MICRO rev2: ARAH dari momentum M15 saja; struktur M15 = VETO (menolak
    hanya bila jelas bertentangan; campur = boleh); cooldown 5 menit antar
    entri; sisanya seperti rev1 (skor M1 >=6, konteks M5/M15 ±1, RSI guard
    3 TF, momentum-habis M5, H4 soft −1, TP-vs-level, SL/TP ATR clamp).
    Transparansi: checklist skor M1 selalu dihitung bila ada pola, meski
    gate menolak — owner bisa audit "apa yang dilihat engine".
    """
    steps = []
    m1_bars = m1_bars or []
    h4_bars = h4_bars or []

    def reject(reason, checklist=None):
        return {"ok": False, "reason": reason, "steps": steps, "score": 0.0,
                "direction": None, "pattern": None, "sl": None, "tp": None,
                "lot": fixed_lot(balance), "checklist": checklist or []}

    # 0. kill switch per arm
    if kill and kill.blocked(now_epoch):
        return reject(f"kill switch: lose streak {kill.lose_streak}x — jeda {kill.remaining_min(now_epoch)} menit lagi")
    steps.append({"k": "Kill switch", "ok": True, "note": "aktif"})

    # 1. news gate (OFF per owner 2026-09-10 — kalender simulasi tak akurat;
    #    nyalakan kembali via NEWS_GATE_ENABLED = True saat kalender real ada)
    if NEWS_GATE_ENABLED:
        ev = news_block(news_events or [], now_epoch)
        if ev:
            return reject(f"news gate: {ev} (±30 menit big news)")
        steps.append({"k": "News gate", "ok": True, "note": "bebas big news"})
    else:
        steps.append({"k": "News gate", "ok": True, "note": "OFF (owner) — kalender simulasi"})

    # 2. bias momentum M15
    mb = momentum_bias(m15_bars)
    if not mb:
        return reject("bias momentum M15 netral (EMA/RSI tidak searah)")
    steps.append({"k": "Momentum M15 (EMA9/21+RSI45/55)", "ok": True, "note": mb})

    # 3. struktur: MICRO = VETO saja (rev2); SCALP = wajib searah (tetap)
    if profile == "MICRO":
        sb = structure_bias(m15_bars)
        tf = "M15"
        if sb and sb != mb:
            return reject(f"struktur {tf} ({sb}) bertentangan momentum ({mb}) — veto")
        note = (f"searah {mb}" if sb == mb else
                f"campur → momentum memutuskan ({mb})" if not sb else sb)
        steps.append({"k": f"Struktur {tf} (veto: tolak bila bertentangan)",
                      "ok": True, "note": note})
    else:
        # SCALP rev2: struktur HH/HL H4 DIHAPUS (owner — tidak berguna).
        # Arah murni dari momentum M15; H4 tak dipakai untuk bias.
        steps.append({"k": "Struktur H4", "ok": True,
                      "note": "dihapus (owner rev2) — arah dari momentum M15"})
    direction = "BULL" if mb == "BULL" else "BEAR"

    # 3a. cooldown antar entri MICRO (rev2, owner: buang entri sampah)
    if profile == "MICRO":
        if last_entry_ts is not None \
                and now_epoch - last_entry_ts < MICRO_COOLDOWN_S:
            return reject(f"cooldown MICRO: {MICRO_COOLDOWN_S // 60} menit antar entri "
                          f"(sisa {int(MICRO_COOLDOWN_S - (now_epoch - last_entry_ts))} detik)")
        steps.append({"k": "Cooldown antar entri", "ok": True,
                      "note": f"MICRO {MICRO_COOLDOWN_S // 60} menit"})

    # 3b. RSI ekstrem guard
    r_m15 = CS.rsi([b["close"] for b in m15_bars], 14)
    r_m5 = CS.rsi([b["close"] for b in m5_bars], 14)
    r_m1 = CS.rsi([b["close"] for b in m1_bars], 14) if len(m1_bars) >= 15 else None
    guards = [("M15", r_m15), ("M5", r_m5)] + ([("M1", r_m1)] if profile == "MICRO" else [])
    for tf_name, r_val in guards:
        if r_val is None:
            continue
        if direction == "BULL" and r_val >= RSI_STOP_BUY:
            return reject(f"RSI {tf_name} {r_val:.0f} >= 70 (jenuh beli) — stop BUY, tunggu pembalikan arah")
        if direction == "BEAR" and r_val <= RSI_STOP_SELL:
            return reject(f"RSI {tf_name} {r_val:.0f} <= 30 (jenuh jual) — stop SELL, tunggu pembalikan arah")

    def _fmt(v):
        return f"{v:.0f}" if v is not None else "—"
    guard_note = " · ".join(f"{n} {_fmt(v)}" for n, v in guards)
    steps.append({"k": "RSI ekstrem guard", "ok": True, "note":
                  f"{guard_note} · stop buy >=70, stop sell <=30"})

    # ── MICRO: multi-TF + M1 execution ──
    if profile == "MICRO":
        exec_bars = m1_bars if len(m1_bars) >= 3 else m5_bars
        exec_tf = "M1" if len(m1_bars) >= 3 else "M5(fallback)"

        # 4a. momentum-habis di M5 (rally-aware; M1 terlalu volatile utk aturan ini)
        exh, exh_info = CS.momentum_exhausted(m5_bars, direction)
        steps.append({"k": "Momentum-habis (M5, retrace-based)", "ok": not exh,
                      "note": exh_info.get("note") or "data kurang"})
        if exh:
            return reject(f"momentum habis: {exh_info.get('note')}")

        # 4b. skor konteks M5 & M15 (pola+kualitas per TF) → ±1
        ctx = {}
        adj = 0.0
        for tf_name, bars_tf in (("M5", m5_bars), ("M15", m15_bars)):
            ctf = CS.context_points(bars_tf)
            ctx[tf_name] = ctf
            if ctf["direction"] == direction and ctf["points"] >= CONTEXT_TF_MIN:
                adj += 1.0
            elif ctf["direction"] is not None and ctf["direction"] != direction \
                    and ctf["points"] >= CONTEXT_TF_MIN:
                adj -= 1.0
        parts = []
        for tf_name in ("M5", "M15"):
            ctf = ctx[tf_name]
            parts.append(f"{tf_name}: {ctf['pattern'] or '-'} {ctf['points']:.0f}pts"
                         + (f" ({', '.join(ctf['quality'])})" if ctf["quality"] else ""))
        steps.append({"k": "Konteks multi-TF (M5+M15)", "ok": True,
                      "note": f"{adj:+.0f} · " + " | ".join(parts)})

        # 4c. skor inti M1 (threshold 6) + penalti H4 soft + adj konteks
        level = nearest_level(direction, profile, m5_bars, m15_bars, m1_bars)
        res = CS.score_candle(exec_bars, level, "MICRO", require_volume=False)
        core_score = res.get("score", 0.0)

        h4_note = "H4 data tidak tersedia"
        if h4_bars:
            last_h4 = h4_bars[-1]
            h4_dir = "BULL" if last_h4["close"] > last_h4["open"] else "BEAR"
            if h4_dir != direction:
                core_score += H4_SOFT_PENALTY
                h4_note = f"H4 candle terakhir {h4_dir} (melawan) → penalti −1"
            else:
                h4_note = f"H4 candle terakhir {h4_dir} (searah) → tanpa penalti"
        final_score = core_score + adj

        # 4d. TP-vs-resistance pratinjau (entry = close M1) — tampil di checklist
        entry_px = float(exec_bars[-1]["close"])
        st = compute_sl_tp(profile, direction, exec_bars, entry_px)
        tp_info = "—"
        tp_cut = False
        if st:
            tp2, tp_info = clamp_tp_to_structure(profile, direction, entry_px,
                                                 st["tp"], m5_bars, m15_bars)
            dist = abs(tp2 - entry_px) / 0.01
            tp_cut = dist < MICRO_TP_MIN_POINTS
            st = dict(st, tp=tp2, tp_points=round(dist, 1))

        total_txt = (f"M1 {core_score:.0f}" + (f" {H4_SOFT_PENALTY:+.0f}(H4)" if "penalti" in h4_note else "")
                     + f" {adj:+.0f}(konteks) = {final_score:.0f} vs 6")
        steps.append({"k": "Skor candle (multi-TF total)", "ok": res.get("ok", False) and not tp_cut,
                      "note": f"{total_txt} · pola {res.get('pattern') or '-'} · H4: {h4_note}"})

        if not res.get("ok"):
            return reject(f"skor candle {exec_tf}: {res.get('reason')}",
                          checklist=res.get("checklist", []))
        # rev3: pola wajib searah bias momentum — pola berlawanan → reject
        # (bukti replay: 12/16 entri hipotetis pola-vs-bias berlawanan,
        #  termasuk BUY dengan pola three_black_crows; gate searah 9W/0L)
        if res.get("direction") and res["direction"] != direction:
            return reject(f"pola {res.get('pattern')} arah {res['direction']} "
                          f"berlawanan bias {direction} — pola wajib searah (rev3)",
                          checklist=res.get("checklist", []))
        if tp_cut:
            return reject(f"TP menabrak struktur: {tp_info} (jarak < {MICRO_TP_MIN_POINTS:.0f} pts)",
                          checklist=res.get("checklist", []))

        steps.append({"k": "SL/TP (ATR M1, clamp owner)", "ok": True,
                      "note": f"SL {st['sl_points']}p / TP {st['tp_points']}p · lot {fixed_lot(balance)} · {tp_info}"})
        return {"ok": True, "reason": "", "steps": steps, "score": final_score,
                "direction": "BUY" if direction == "BULL" else "SELL",
                "pattern": res.get("pattern"), "checklist": res.get("checklist", []),
                "entry": entry_px, "sl": st["sl"], "tp": st["tp"],
                "sl_points": st["sl_points"], "tp_points": st["tp_points"],
                "lot": fixed_lot(balance),
                "context": {"M1": CS.context_points(exec_bars), **ctx}}

    # ── SCALP: alur lama (skor di M5, threshold 7, volume wajib) ──
    level = nearest_level(direction, profile, m5_bars, m15_bars)
    res = CS.score_candle(m5_bars, level, "SCALP", require_volume=True)
    steps.append({"k": "Skor candle", "ok": res["ok"],
                  "note": f"{res.get('score', 0):.0f} pts — {res.get('pattern') or '-'}"})
    if not res["ok"]:
        return reject(res.get("reason") or "skor candle di bawah threshold",
                      checklist=res.get("checklist", []))
    # rev3 REV: gate pola-vs-bias TIDAK berlaku utk SCALP (owner 2026-09-10
    # sore: SCALP 3x win beruntun, salah satunya BUY dgn pola three_black_
    # crows — "jangan rubah logic entri scalp"). Pola boleh berlawanan bias;
    # seleksi kualitas tetap: threshold 7 + volume 1.2x + RSI guard.

    entry = float(m5_bars[-1]["close"])
    st = compute_sl_tp(profile, direction, m5_bars, entry)
    if not st:
        return reject("ATR tidak tersedia untuk SL/TP")
    lot = fixed_lot(balance)
    steps.append({"k": "SL/TP (ATR)", "ok": True,
                  "note": f"SL {st['sl_points']}p / TP {st['tp_points']}p · lot {lot}"})
    return {"ok": True, "reason": "", "steps": steps, "score": res["score"],
            "direction": "BUY" if direction == "BULL" else "SELL",
            "pattern": res.get("pattern"), "checklist": res.get("checklist", []),
            "entry": entry, "sl": st["sl"], "tp": st["tp"],
            "sl_points": st["sl_points"], "tp_points": st["tp_points"], "lot": lot,
            "context": {"M5": CS.context_points(m5_bars), "M15": CS.context_points(m15_bars)}}
