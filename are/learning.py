"""Learning Memory — Fase 1 (sisi daemon / penulisan).

Satu-satunya penulis data/learning/:
  - trade_memory.jsonl  : append-only, event OPEN & CLOSE per trade
  - open_fp.json        : fingerprint posisi yg masih terbuka (persist antar restart)
  - buckets.json        : agregat {key: {n, win, pts, pnl, updated}} — dibaca engine

Bucket key HARUS identik dgn buildBucketKey() di UI/src/lib/learning.ts:
  <style>|<DIRECTION>|m_<master>|r_<rsi_bucket>|a_<atr_bucket>|p_<pattern[:30]>
Fingerprint diambil dari respons decision engine (taSnapshot + timeframeSignals).

Win = pnl > 0 (TP kena, close manual profit, reversal profit). Loss = pnl <= 0.
Soft gate engine: demote bila n>=8 & WR<45%; boost bila n>=8 & WR>=60%.
"""
import json, os, threading, time

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "learning")
MEM_FILE = os.path.join(DATA_DIR, "trade_memory.jsonl")
OPEN_FP_FILE = os.path.join(DATA_DIR, "open_fp.json")
BUCKETS_FILE = os.path.join(DATA_DIR, "buckets.json")

_lock = threading.Lock()
_min_samples = 8
_demote_wr = 0.45
_boost_wr = 0.60


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _rsi_bucket(rsi):
    if rsi is None:
        return "na"
    try:
        rsi = float(rsi)
    except (TypeError, ValueError):
        return "na"
    if rsi < 35:
        return "r<35"
    if rsi < 50:
        return "r35-50"
    if rsi < 65:
        return "r50-65"
    return "r>65"


def _atr_bucket(atr):
    if atr is None:
        return "na"
    try:
        atr = float(atr)
    except (TypeError, ValueError):
        return "na"
    if atr < 3:
        return "a<3"
    if atr <= 4.5:
        return "a3-4.5"
    return "a>4.5"


def _top_pattern(patterns):
    """Pola pertama (urut array engine = urutan deteksi). NEUTRAL dianggap none
    karena tidak punya arah — konsisten dgn keputusan engine."""
    for p in (patterns or []):
        name, _, sig = p.partition(":")
        if sig in ("BUY", "SELL"):
            return p
    return "none"


def build_bucket_key(style, direction, master, m5_rsi, m5_atr, pattern):
    pat = _top_pattern(pattern) if pattern is None or isinstance(pattern, list) else pattern
    return "|".join([
        style or "?",
        direction or "?",
        "m_%s" % (master or "NA"),
        "r_%s" % _rsi_bucket(m5_rsi),
        "a_%s" % _atr_bucket(m5_atr),
        "p_%s" % str(pat or "none")[:30],
    ])


def _load_open_fp():
    try:
        with open(OPEN_FP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_open_fp(fp_map):
    _ensure_dir()
    try:
        with open(OPEN_FP_FILE, "w", encoding="utf-8") as f:
            json.dump(fp_map, f)
    except Exception:
        pass


def _load_buckets():
    try:
        with open(BUCKETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_buckets(buckets):
    _ensure_dir()
    tmp = BUCKETS_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(buckets, f)
        os.replace(tmp, BUCKETS_FILE)
    except Exception:
        pass


def fingerprint_from_decision(style, dec):
    """Bangun fingerprint kasar dari respons decision engine (dict).
    Dipanggil saat ENTRY — kondisi yang sama persis dgn yang dievaluasi engine."""
    snap = (dec or {}).get("taSnapshot") or {}
    tf = (dec or {}).get("timeframeSignals") or {}
    m5 = tf.get("M5") or {}
    m15 = tf.get("M15") or {}
    master = snap.get("master") or {}
    return {
        "style": style,
        "master": master.get("signal"),
        "master_conf": master.get("confidence"),
        "score": snap.get("score"),
        "m1": snap.get("m1"),
        "m5": snap.get("m5"),
        "m15": snap.get("m15"),
        "m5_rsi": m5.get("rsi"),
        "m5_atr": m5.get("atr"),
        "m5_conf": m5.get("confidence"),
        "m15_rsi": m15.get("rsi"),
        "m15_atr": m15.get("atr"),
        "patterns": snap.get("patterns"),
        "m5Volume": snap.get("m5Volume"),
        # Desain V2: setup candle + skor + sumber SL/TP + nilai SL/TP terpakai
        "candleSetup": snap.get("candleSetup"),
        "candleScore": snap.get("candleScore"),
        "slTpSource": snap.get("slTpSource"),
        "rrWarning": snap.get("rrWarning"),
        "sl_points": (dec or {}).get("slPoints"),
        "tp_points": (dec or {}).get("tpPoints"),
    }


def record_open(style, ticket, direction, fp, entry=None, lot=None, sl_points=None, tp_points=None, ts=None):
    """Catat OPEN ke JSONL + simpan fp posisi terbuka (utk outcome saat close)."""
    ts = ts or time.time()
    _ensure_dir()
    rec = {
        "evt": "open", "ts": ts, "ticket": ticket, "style": style,
        "direction": direction, "entry": entry, "lot": lot,
        "sl_points": sl_points, "tp_points": tp_points,
        "fp": fp,
    }
    with _lock:
        try:
            with open(MEM_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        except Exception:
            pass
        fp_map = _load_open_fp()
        fp_stored = dict(fp or {})
        fp_stored["_dir"] = direction
        fp_map[str(ticket)] = fp_stored
        _save_open_fp(fp_map)


def record_close(style, ticket, pnl, reason, exit_=None, closed_at=None):
    """Catat CLOSE + perbarui agregat bucket. Win = pnl > 0."""
    closed_at = closed_at or time.time()
    _ensure_dir()
    with _lock:
        fp_map = _load_open_fp()
        fp = fp_map.pop(str(ticket), None) or {}
        _save_open_fp(fp_map)

        win = 1 if (pnl or 0) > 0 else 0
        loss = 0 if win else 1
        rec = {
            "evt": "close", "ts": closed_at, "ticket": ticket, "style": style,
            "pnl": round(pnl or 0, 2), "win": win, "close_reason": reason,
            "exit": exit_,
        }
        try:
            with open(MEM_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        except Exception:
            pass

        key = build_bucket_key(
            style, fp.get("_dir") or (fp or {}).get("direction"),
            (fp or {}).get("master"), (fp or {}).get("m5_rsi"),
            (fp or {}).get("m5_atr"), (fp or {}).get("patterns"),
        )
        buckets = _load_buckets()
        b = buckets.get(key) or {"n": 0, "win": 0, "pts": 0.0, "pnl": 0.0, "updated": 0}
        b["n"] = b.get("n", 0) + 1
        b["win"] = b.get("win", 0) + win
        b["pnl"] = round(b.get("pnl", 0.0) + (pnl or 0), 2)
        b["updated"] = closed_at
        buckets[key] = b
        _save_buckets(buckets)
        return key
