"""MICRO Shadow A/B (ops-rev7, owner 2026-09-11).

Kandidat konfigurasi MICRO dievaluasi tiap close M1 DI SAMPING arm live,
TANPA pernah mengirim order. Entry = keputusan kandidat pada bar M1 close
(parity timing live); exit = simulasi first-touch TP/SL pada bar M1
sesudahnya (metode studi scripts/micro_v2_study.py). State persisten ->
posisi pending & statistik selamat driver restart.

Kandidat terdaftar (owner 2026-09-11):
  A. baseline v2.1.1 : mirror arm live (volume 1.1x, RSI 65/35, 0.9/1.4) -
     kontrol; harus cocok dgn hasil live (sanity check shadow runner).
  B. london-sell-only: AKTIF HANYA sesi London (07:00-11:59 UTC, kontrak R1)
     dan HANYA SELL (WR 48.5% vs BUY 37.9% di London; SELL juga satu-satunya
     sel london dgn gross/tr positif +0.8 pts). Parameter lain parity live.
  C. london-all      : aktif hanya sesi London, semua arah (uji apakah
     pembeda utamanya sesi atau arah) - data pembanding utk B.

Shadow tidak pernah POST ke bridge; ia hanya MEMBACA bar. Journal shadow:
data/research/r1/demo/shadow_ab_journal.jsonl (evt: open/close/eval_sinyal).
Ringkasan (WR, n, gross pts) ditulis ke driver_state agar tampil di UI.

PURE layer + persistence; driver memanggil on_m1_close(m1, m5, now_epoch).
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from strategy_v2 import candle_scoring as CS
from strategy_v2 import micro_v2 as MV
from strategy_v2 import simple_variants as SV

ROOT = Path(__file__).resolve().parents[1]  # repo root (strategy_v2/..)
OUT = ROOT / "data" / "research" / "r1" / "demo"
STATE_FILE = OUT / "shadow_ab_state.json"
JOURNAL_FILE = OUT / "shadow_ab_journal.jsonl"

# kontrak blok sesi R1 Stage 1 (UTC)
SESSIONS = (("asia", 0, 7), ("london", 7, 12), ("overlap", 12, 16), ("ny_late", 16, 24))


def session_of_epoch(ts: int) -> str:
    h = datetime.fromtimestamp(ts, tz=timezone.utc).hour
    for name, a, b in SESSIONS:
        if a <= h < b:
            return name
    return "?"


CANDIDATES = {
    "A_base": {"vol_min": MV.VOL_MIN, "rsi": (MV.RSI_STOP_BUY, MV.RSI_STOP_SELL),
               "sltp": (MV.SL_MULT, MV.TP_MULT), "sess": None, "dirs": None},
    "B_london_sell": {"vol_min": MV.VOL_MIN, "rsi": (MV.RSI_STOP_BUY, MV.RSI_STOP_SELL),
                      "sltp": (MV.SL_MULT, MV.TP_MULT), "sess": "london", "dirs": ("SELL",)},
    "C_london_all": {"vol_min": MV.VOL_MIN, "rsi": (MV.RSI_STOP_BUY, MV.RSI_STOP_SELL),
                     "sltp": (MV.SL_MULT, MV.TP_MULT), "sess": "london", "dirs": None},
}

COOLDOWN_S = SV.MICRO_COOLDOWN_S  # parity live (5 menit)
MIN_BARS = 30


def _score(m1_bars: list, level, vol_min: float) -> dict:
    """Skor profil SCALP dgn veto vol_min, bonus dicabut di [vol_min, 1.2)."""
    orig = CS.VOL_MULT_SCALP
    CS.VOL_MULT_SCALP = vol_min
    try:
        res = CS.score_candle(m1_bars, level, "SCALP", require_volume=True)
    finally:
        CS.VOL_MULT_SCALP = orig
    if vol_min < MV.VOL_BONUS and res.get("ok"):
        avg5 = sum(int(b.get("volume", 0)) for b in m1_bars[-6:-1]) / 5.0
        vol = int(m1_bars[-1].get("volume", 0))
        if avg5 > 0 and vol_min * avg5 <= vol < MV.VOL_BONUS * avg5:
            res = dict(res)
            res["score"] = res.get("score", 0) - 1.0
            res["ok"] = res["score"] >= MV.THRESHOLD
    return res


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"pending": {}, "last_entry": {}, "stats": {}, "last_m1_t": 0}


def _save_state(st: dict) -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _journal(evt: dict) -> None:
    try:
        with open(JOURNAL_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=True) + "\n")
    except Exception:
        pass


def _exit_first_touch(direction: str, entry: float, sl: float, tp: float,
                      t0: int, m1_by_time: dict, m1_times: list) -> dict:
    """First-touch TP/SL pada bar M1 setelah t0 (parity metode studi)."""
    import bisect
    i = bisect.bisect_right(m1_times, t0)
    for tt in m1_times[i:]:
        b = m1_by_time[tt]
        hi, lo = float(b["high"]), float(b["low"])
        gap = (tt - t0) > 300 * 3
        if direction == "SELL":
            if lo <= tp:
                return {"outcome": "TP", "exit": tp, "exit_time": tt, "gap": gap}
            if hi >= sl:
                return {"outcome": "SL", "exit": sl, "exit_time": tt, "gap": gap}
        else:
            if hi >= tp:
                return {"outcome": "TP", "exit": tp, "exit_time": tt, "gap": gap}
            if lo <= sl:
                return {"outcome": "SL", "exit": sl, "exit_time": tt, "gap": gap}
    return {"outcome": "OPEN", "exit": None, "exit_time": None, "gap": False}


def on_m1_close(m1: list, m5: list, now_epoch: int) -> None:
    """Hook driver: dipanggil tiap bar M1 close. Tanpa order, tanpa block."""
    try:
        _on_m1_close_impl(m1, m5, now_epoch)
    except Exception:
        pass  # shadow tidak boleh pernah mengganggu arm live


def _on_m1_close_impl(m1: list, m5: list, now_epoch: int) -> None:
    if not m1 or len(m1) < MIN_BARS or not m5 or len(m5) < MIN_BARS:
        return
    bar = m1[-1]
    t = int(bar["time"])
    st = _load_state()
    if t <= st.get("last_m1_t", 0):
        return  # bar sama / replay ulang
    st["last_m1_t"] = t

    m1_by_time = {int(b["time"]): b for b in m1}
    m1_times = sorted(m1_by_time)

    # 1) selesaikan posisi pending shadow (evaluasi di bar close berikutnya)
    for cid, p in list(st["pending"].items()):
        out = _exit_first_touch(p["dir"], p["entry"], p["sl"], p["tp"],
                                p["entry_t"], m1_by_time, m1_times)
        outcome, exit_px = out["outcome"], out["exit"]
        if outcome == "OPEN" and (t - p["entry_t"]) > 2 * 86400:
            # posisi nyangkut >2 hari (mis. driver mati saat weekend & bar
            # exit sudah lewat jendela) - expire dgn P&L close terakhir
            outcome = "EXPIRE"
            sign = 1 if p["dir"] == "BUY" else -1
            exit_px = float(bar["close"])
        if outcome == "OPEN":
            continue
        if outcome == "EXPIRE":
            pts = round(sign * (exit_px - p["entry"]) / MV.POINT, 1)
        else:
            pts = (p["tp_pts"] if outcome == "TP" else -p["sl_pts"])
        s = st["stats"].setdefault(cid, {"n": 0, "w": 0, "gross_pts": 0.0, "by_sess": {}})
        s["n"] += 1
        s["w"] += 1 if out["outcome"] == "TP" else 0
        s["gross_pts"] = round(s["gross_pts"] + pts, 1)
        bs = s["by_sess"].setdefault(p["sess"], [0, 0, 0.0])
        bs[0] += 1
        bs[1] += 1 if out["outcome"] == "TP" else 0
        bs[2] = round(bs[2] + pts, 1)
        _journal({"evt": "shadow_close", "cand": cid, "dir": p["dir"],
                  "entry_t": p["entry_t"], "exit_t": out["exit_time"],
                  "outcome": outcome, "pts": round(pts, 1),
                  "sess": p["sess"], "gap": out["gap"], "ts": now_epoch})
        del st["pending"][cid]

    # 2) konteks pasar (sama utk semua kandidat)
    mb = SV.momentum_bias(m5)
    atr_m5 = CS.atr(m5)
    closes5 = [b["close"] for b in m5]
    e9, e21 = CS.ema(closes5, 9), CS.ema(closes5, 21)
    r_m5 = CS.rsi(closes5, 14)
    r_m1 = CS.rsi([b["close"] for b in m1], 14)
    if mb is None or atr_m5 is None:
        _save_state(st)
        return
    direction = mb
    dir_str = "BUY" if direction == "BULL" else "SELL"
    entry_px = float(bar["close"])
    level = MV.nearest_ema_level(direction, e9, e21, entry_px)
    sess = session_of_epoch(t)

    # 3) evaluasi kandidat
    for cid, cfg in CANDIDATES.items():
        if cid in st["pending"]:
            continue  # satu posisi per kandidat (parity live per-arm)
        if cfg["sess"] and sess != cfg["sess"]:
            continue
        if cfg["dirs"] and dir_str not in cfg["dirs"]:
            continue
        last_e = st["last_entry"].get(cid, 0)
        if last_e and t - last_e < COOLDOWN_S:
            continue
        sb, ss = cfg["rsi"]
        guard = any(rv is not None and ((direction == "BULL" and rv >= sb) or
                                        (direction == "BEAR" and rv <= ss))
                    for rv in (r_m5, r_m1))
        if guard:
            continue
        res = _score(m1, level, cfg["vol_min"])
        if not res.get("ok"):
            continue
        slm, tpm = cfg["sltp"]
        sl_d, tp_d = slm * atr_m5, tpm * atr_m5
        sl = entry_px - sl_d if direction == "BULL" else entry_px + sl_d
        tp = entry_px + tp_d if direction == "BULL" else entry_px - tp_d
        st["pending"][cid] = {"dir": dir_str, "entry": entry_px, "sl": sl,
                              "tp": tp, "sl_pts": round(sl_d / MV.POINT, 1),
                              "tp_pts": round(tp_d / MV.POINT, 1),
                              "entry_t": t, "entry_epoch": now_epoch,
                              "sess": sess, "pattern": res.get("pattern"),
                              "score": res.get("score")}
        st["last_entry"][cid] = t
        _journal({"evt": "shadow_open", "cand": cid, "dir": dir_str,
                  "pattern": res.get("pattern"), "score": res.get("score"),
                  "entry": entry_px, "sess": sess, "bar_t": t, "ts": now_epoch})

    _save_state(st)


def summary() -> dict:
    """Ringkasan utk UI/driver_state: WR & n per kandidat."""
    st = _load_state()
    out = {}
    for cid in CANDIDATES:
        s = st.get("stats", {}).get(cid, {"n": 0, "w": 0, "gross_pts": 0.0})
        n, w = s["n"], s["w"]
        out[cid] = {"n": n, "wins": w, "wr": round(w / n * 100, 1) if n else None,
                    "gross_pts": s["gross_pts"],
                    "open": 1 if cid in st.get("pending", {}) else 0}
    return out
