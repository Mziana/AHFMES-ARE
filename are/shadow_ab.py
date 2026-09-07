"""Shadow A/B — evaluasi keputusan TANPA gate candle secara paper pada bot live.

Bot nyata tetap pakai gate candle V2 (READY/WAITING/BLOCKED). Setiap kali gate
mem-BLOKIR entri padahal arah TA sudah lolos (scenario 'seandainya tanpa gate'),
modul ini membuka posisi SHADOW (tidak dikirim ke broker) dengan harga & SL/TP
yang sama persis dengan yang akan dipakai engine tanpa gate, lalu melacaknya
tiap poll sampai TP/SL/reversal/time-cap. Hasil dicatat ke
data/learning/shadow_ab.jsonl (append-only) untuk dibandingkan dengan trade
nyata (gate ON) via scripts/report_shadow_ab.py.

Catatan jujur:
- Resolusi harga = 1 tick/detik dari decision engine (bukan intrabar M1),
  sedikit mengabaikan ekstrem intrabar — konservatif utk kedua sisi.
- Shadow tidak tunduk max_positions bot (1 posisi per style, sekuensial).
- Biaya spread 18 poin tidak dikurangi di field pts (laporan menghitung
  varian net 18 secara terpisah).
"""

import json
import os
import time

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "learning")
LOG_FILE = os.path.join(DATA_DIR, "shadow_ab.jsonl")
OPEN_FILE = os.path.join(DATA_DIR, "shadow_ab_open.json")
CONFIG_FILE = os.path.join(DATA_DIR, "..", "bot_config.json")

STYLES = ("micro", "scalp")
MIN_HOLD_S = 15 * 60      # minimal 15 mnt sebelum boleh exit reversal (sama dgn bot)
HOLD_CAP_S = 12 * 3600    # tutup paksa 12 jam
COOLDOWN_S = 120          # jeda antar shadow entry


def _cfg_sl_tp(style):
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            cfg = json.load(f)
        st = (cfg.get("sl_tp") or {}).get(style) or {}
        sl = int(st.get("sl_points") or 0)
        tp = int(st.get("tp_points") or 0)
        if sl > 0 or tp > 0:
            return sl, tp
    except Exception:
        pass
    return None


def _load_open():
    try:
        with open(OPEN_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_open(o):
    try:
        with open(OPEN_FILE, "w", encoding="utf-8") as f:
            json.dump(o, f, indent=1)
    except Exception:
        pass


def _append(rec):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def tick(style, dec, now):
    """Dipanggil tiap poll bot. dec = respons decision engine (dict) atau None."""
    if style not in STYLES:
        return
    if not dec or not isinstance(dec, dict):
        return
    price = dec.get("price")
    if not price:
        return
    ts = dec.get("taSnapshot") or {}
    candle = ts.get("candle") or {}
    final = dec.get("finalSignal")
    decision = dec.get("decision")

    open_pos = _load_open()
    sh = open_pos.get(style)
    if sh:
        _advance(style, sh, dec, price, now)
        return

    # Tanpa posisi shadow: buka bila gate MEMBLOKIR padahal TA sudah lolos.
    want = (decision == "WAIT") and candle.get("block") is True \
        and final in ("BUY", "SELL") and dec.get("inSession", True)
    if not want:
        return
    last = open_pos.get("_last_open", {})
    if now - float(last.get(style, 0)) < COOLDOWN_S:
        return

    atr = ((dec.get("timeframeSignals") or {}).get("M5") or {}).get("atr") or 0
    ov = _cfg_sl_tp(style)
    if ov:
        sl_pts, tp_pts = ov
    else:
        sl_pts = round(max(8.0, atr * 100))
        if style == "micro":
            tp_pts = 150
        else:
            tp_pts = max(150, round(2 * atr * 100))
    sh = {
        "style": style, "dir": final, "entry": price,
        "sl": sl_pts, "tp": tp_pts, "ts": now,
    }
    open_pos[style] = sh
    open_pos.setdefault("_last_open", {})[style] = now
    _save_open(open_pos)
    _append({"evt": "open", "ts": now, "style": style, "dir": final,
             "entry": price, "sl": sl_pts, "tp": tp_pts,
             "reason": "nogate_shadow"})


def _close(style, sh, now, reason, pts, exit_price):
    open_pos = _load_open()
    open_pos.pop(style, None)
    _save_open(open_pos)
    _append({"evt": "close", "ts": now, "style": style, "dir": sh["dir"],
             "pts": round(pts, 1), "win": 1 if pts > 0 else 0, "reason": reason,
             "entry": sh["entry"], "exit": exit_price,
             "sl": sh["sl"], "tp": sh["tp"], "open_ts": sh["ts"],
             "held_s": round(now - sh["ts"], 1)})


def _advance(style, sh, dec, price, now):
    buy = sh["dir"] == "BUY"
    slv = sh["entry"] - sh["sl"] * 0.01 if buy else sh["entry"] + sh["sl"] * 0.01
    tpv = sh["entry"] + sh["tp"] * 0.01 if buy else sh["entry"] - sh["tp"] * 0.01
    held = now - sh["ts"]
    # SL didahulukan bila harga sudah melewati dua-duanya (konservatif).
    if (buy and price <= slv) or (not buy and price >= slv):
        _close(style, sh, now, "sl", -sh["sl"], slv)
    elif (buy and price >= tpv) or (not buy and price <= tpv):
        _close(style, sh, now, "tp", sh["tp"], tpv)
    elif held >= HOLD_CAP_S:
        pts = (price - sh["entry"]) * (1 if buy else -1) * 100
        _close(style, sh, now, "time", pts, price)
    elif held >= MIN_HOLD_S:
        final = dec.get("finalSignal")
        if final and final != "NEUTRAL" and ((buy and final == "SELL") or (not buy and final == "BUY")):
            pts = (price - sh["entry"]) * (1 if buy else -1) * 100
            _close(style, sh, now, "reversal", pts, price)
