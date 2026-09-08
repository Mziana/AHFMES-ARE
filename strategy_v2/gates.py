"""P1 — Pure Gate Engine (Layer A + Layer B). ZERO I/O, ZERO now(), zero MT5/DB/UI.

Kontrak (desain v2.3 §1-§2, Pagar 2/3/5):
- SEMUA fungsi murni. Engine menerima bars yang SUDAH di-slice ≤ T
  (evaluation-time slicing oleh replay) — tidak ada fungsi di sini yang
  menerima timestamp > T, dan tidak ada satu pun pemanggilan now()/time().
- Layer A (data integrity) = syarat masuk Layer B. DATA_INVALID → Layer B
  tidak dijalankan (gate values = DISABLED), statistik terpisah (Pagar 3).
- evaluate_all menilai SEMUA gate (full diagnostic); decide menghasilkan
  first_veto_reason + decision (operational). Keduanya terpisah dan keduanya
  dicatat (desain §2).
- Reason codes B1 news: 4 kode terpisah (koreksi review #2).
"""
from __future__ import annotations

import math

from . import zones as Z
from .registry import TRIGGER_TIMEFRAME, REGIME_TIMEFRAME

BAR_SECONDS = {TRIGGER_TIMEFRAME: 300, REGIME_TIMEFRAME: 900}

VETO_ORDER = [
    ("b1_news", "B1"),
    ("b2_session", "B2"),
    ("b3_regime", "B3"),
    ("b4_location", "B4"),
    ("b5_trigger", "B5"),
    ("b6_volume", "B6"),
    ("b7_risk", "B7"),
]

# ─── helpers ─────────────────────────────────────────────────────────────────

def _is_finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


# ─── LAYER A — data integrity (bukan bagian strategi) ────────────────────────

def layer_a_data_integrity(bars: list, ticks_meta: dict | None, config: dict) -> str:
    """Return 'DATA_VALID' atau 'DATA_INVALID:<reason>' (kontrak data_integrity.md).

    bars = M5 slice ≤ T. Urutan cek deterministik (reason pertama yang gagal).
    """
    bar_seconds = config.get("bar_seconds", BAR_SECONDS[TRIGGER_TIMEFRAME])
    prof_a = config.get("layer_a", {})
    max_stale_bars = prof_a.get("max_staleness_bars", 3)
    spread_cap = prof_a.get("spread_cap_points", 200)

    return _layer_a_check_bars(bars, ticks_meta, bar_seconds, max_stale_bars,
                               spread_cap, now_ts=config["now_ts"])


def layer_a_m15_integrity(m15: list, config: dict) -> str:
    """P0-04 — Layer A atas M15 (regime/location timeframe).

    M15 dipakai b3_regime + b4_location → keputusan bergantung timeframe ini,
    jadi wajib tervalidasi sama seperti M5. Tanpa spread check (tick spread
    adalah properti M5 trigger). Return 'DATA_VALID' atau 'DATA_INVALID:m15:<reason>'.

    Gap ≥ 3600 dtk (≥ 1 jam) diizinkan: itu break sesi pasar (maintenance
    harian broker ~75 menit, weekend ~49 jam — terukur nyata di dataset),
    BUKAN korupsi data. Gap 1–3 bar (900–2700 dtk) tetap ditolak sebagai
    missing_bar — kehilangan data intra-sesi. Konsisten dengan qualify_dataset
    yang menghitung gap tapi tidak meng-invalidate dataset.
    """
    prof_a = config.get("layer_a", {})
    max_stale_bars = prof_a.get("max_staleness_bars", 3)
    base = _layer_a_check_bars(m15, None, 900, max_stale_bars,
                               spread_cap=None, now_ts=config["now_ts"],
                               min_gap_seconds=3600)
    if base == "DATA_VALID":
        return base
    # prefix per-timeframe: DATA_INVALID:m15:<reason> (audit P0-04)
    return "DATA_INVALID:m15:" + base.split(":", 1)[1]


def _layer_a_check_bars(bars: list, ticks_meta: dict | None, bar_seconds: int,
                        max_stale_bars: int, spread_cap: float | None,
                        now_ts: int, min_gap_seconds: int = 0) -> str:
    """Core integrity check (dipakai M5 dan M15). Urutan deterministik.

    min_gap_seconds=0 → strict gap (M5). min_gap_seconds>0 → gap >= nilai itu
    dianggap break sesi pasar (M15), bukan korupsi data."""

    if spread_cap is None:
        spread_cap = float("inf")  # M15: tanpa spread check

    seen = set()
    prev_t = None
    for b in bars:
        t = b.get("time")
        if t is None:
            return "DATA_INVALID:missing_bar"
        if t in seen:
            return "DATA_INVALID:duplicate_ts"
        seen.add(t)
        delta = int(t) - int(prev_t) if prev_t is not None else bar_seconds
        # min_gap_seconds=0 → strict (M5): delta != bar_seconds = missing_bar.
        # min_gap_seconds>0 (M15): gap >= min_gap_seconds = break sesi (allowed),
        # gap lebih kecil = kehilangan data intra-sesi (missing_bar).
        if delta != bar_seconds and (min_gap_seconds == 0 or delta < min_gap_seconds):
            return "DATA_INVALID:missing_bar"
        prev_t = t
        o, h, l, c = b.get("open"), b.get("high"), b.get("low"), b.get("close")
        if not (_is_finite(o) and _is_finite(h) and _is_finite(l) and _is_finite(c)):
            return "DATA_INVALID:nan"
        if h < max(o, c) or l > min(o, c) or min(o, h, l, c) <= 0:
            return "DATA_INVALID:ohlc"
        v = b.get("volume")
        if not _is_finite(v) or v < 0:
            return "DATA_INVALID:volume_missing"

    if not bars:
        return "DATA_INVALID:missing_bar"

    last_close = int(bars[-1]["time"]) + bar_seconds
    if now_ts - last_close > max_stale_bars * bar_seconds:
        return "DATA_INVALID:stale"

    if ticks_meta:
        sp = ticks_meta.get("spread_points")
        if sp is not None:
            if not _is_finite(sp) or sp <= 0 or sp > spread_cap:
                return "DATA_INVALID:spread_extreme"

    return "DATA_VALID"


# ─── LAYER B — strategy gates ────────────────────────────────────────────────

def b1_news(now_ts: int, calendar: dict | None, policy: dict) -> str:
    """FAIL-CLOSED, 4 reason code terpisah (desain §B1).

    calendar: {'status': 'ok'|'down'|'empty',
               'information_available_at': epoch|None,   # P0-01 provenance
               'events': [{'ts', 'impact': 'high'|..., 'currency': 'USD', ...}]}
    policy dari profil: {'window_minutes', 'staleness_hours', 'impacts'}

    P0-01: staleness diukur dari `information_available_at` (kapan informasi
    kalender tersedia) — BUKAN heuristic dari event timestamp. Tiga fail-closed:
    - field provenance tidak ada → NEWS_DATA_STALE (jujur, bukan heuristic)
    - information_available_at > now_ts → NEWS_DATA_STALE (look-ahead guard:
      snapshot dari masa depan TIDAK tersedia pada T)
    - usia > staleness_hours → NEWS_DATA_STALE (freshness provider, jalur live)
    Calendar artifact arsip (replay) menandai 'archived': True — availability
    sudah dinyatakan artifact; age-check dilewati (jadwal mingguan memang
    berumur > staleness_hours saat direplay).
    """
    if not calendar or calendar.get("status") == "down":
        return "NEWS_PROVIDER_DOWN"
    events = calendar.get("events")
    if calendar.get("status") == "empty" or not events:
        return "NEWS_CALENDAR_UNAVAILABLE"
    info_at = calendar.get("information_available_at")
    if info_at is None:
        return "NEWS_DATA_STALE"
    info_at = int(info_at)
    if info_at > now_ts:  # look-ahead guard: informasi belum tersedia pada T
        return "NEWS_DATA_STALE"
    if not calendar.get("archived") and now_ts - info_at > policy.get("staleness_hours", 4) * 3600:
        return "NEWS_DATA_STALE"
    win = policy.get("window_minutes", 30) * 60
    impacts = set(policy.get("impacts", ["high"]))
    for ev in events:
        if ev.get("currency") == "USD" and ev.get("impact") in impacts:
            if abs(now_ts - int(ev["ts"])) <= win:
                return "NEWS_EVENT_ACTIVE"
    return "PASS"


def b2_session(now_ts: int, session_windows: list) -> str:
    """UTC hour ∈ session_windows. windows = [[start_hour, end_hour), ...]"""
    from datetime import datetime, timezone
    hour = datetime.fromtimestamp(int(now_ts), tz=timezone.utc).hour
    for start, end in session_windows:
        if start <= hour < end:
            return "PASS"
    return "FAIL:outside"


def b3_regime(m15_closed_bars: list, config: dict) -> str:
    """BUY_ONLY / SELL_ONLY / NO_TRADE dari M15 CLOSED bars ≤ T."""
    warmup = int(config.get("min_bars_m15_warmup", 50))
    if len(m15_closed_bars) < warmup:
        return "FAIL:NO_TRADE"
    closes = [b["close"] for b in m15_closed_bars]
    e20 = Z.ema(closes, 20)[-1]
    e9 = Z.ema(closes, 9)[-1]
    e21 = Z.ema(closes, 21)[-1]
    r = Z.rsi(closes, Z.RSI_PERIOD)
    thr = float(config.get("rsi_bias_threshold", 50))
    close = closes[-1]
    if r is None:
        return "FAIL:NO_TRADE"
    if close > e20 and e9 > e21 and r > thr:
        return "PASS:BUY_ONLY"
    if close < e20 and e9 < e21 and r < thr:
        return "PASS:SELL_ONLY"
    return "FAIL:NO_TRADE"


def b4_location(profile: dict, m15_zones: dict, m5_bars: list, config: dict) -> str:
    """SCALP: dekat zona S/R searah (≤ 0.5×ATR M15). MICRO: pullback EMA9/21 M5
    (≤ 0.25×ATR M5). Zona dari zones.py (anti-lookahead)."""
    bias = config.get("bias")
    if bias not in ("BUY_ONLY", "SELL_ONLY"):
        return "FAIL:far"
    loc = profile["location"]
    last = m5_bars[-1]
    price = last["close"]

    if loc["kind"] == "sr_zone":
        if not m15_zones or m15_zones.get("atr_m15") in (None, 0):
            return "FAIL:far"
        res = Z.nearest_zone_distance(m15_zones, price, bias)
        if res is None:
            return "FAIL:far"
        dist, ref = res
        if dist <= loc["sr_distance_atr"] * m15_zones["atr_m15"]:
            return f"PASS:{ref}|dist_atr={dist / m15_zones['atr_m15']:.3f}"
        return "FAIL:far"

    if loc["kind"] == "ema_pullback":
        a = Z.atr(m5_bars)
        if a is None or a <= 0:
            return "FAIL:far"
        closes = [b["close"] for b in m5_bars]
        e9 = Z.ema(closes, 9)[-1]
        e21 = Z.ema(closes, 21)[-1]
        d9, d21 = abs(price - e9), abs(price - e21)
        if d9 <= d21 and d9 <= loc["ema_pullback_distance_atr"] * a:
            return f"PASS:ema9@{e9:.2f}|dist_atr={d9 / a:.3f}"
        if d21 < d9 and d21 <= loc["ema_pullback_distance_atr"] * a:
            return f"PASS:ema21@{e21:.2f}|dist_atr={d21 / a:.3f}"
        return "FAIL:far"

    return "FAIL:far"


# ── B5 candle patterns (closed bars only, deterministic) ────────────────────

def _body(b): return abs(b["close"] - b["open"])
def _range(b): return b["high"] - b["low"]


def _bullish_patterns(bars: list) -> list:
    """Pola bullish dari CLOSED bars. bars[-1] = signal bar. Deterministik."""
    out = []
    if len(bars) < 3:
        return out
    s, p1, p2 = bars[-1], bars[-2], bars[-3]
    body = _body(s)
    rng = _range(s)
    if rng > 0:
        lower = min(s["open"], s["close"]) - s["low"]
        upper = s["high"] - max(s["open"], s["close"])
        if body > 0 and lower >= 2 * body and upper <= 0.35 * body and s["close"] > s["open"]:
            out.append("hammer")
        if body > 0 and upper >= 2 * body and lower <= 0.35 * body and s["close"] < s["open"]:
            out.append("shooting_star")  # bearish pattern, tetap dihitung di sini lalu difilter
    # engulfing
    if _body(p1) > 0 and _body(s) > 0:
        if s["close"] > s["open"] and p1["close"] < p1["open"] and \
           s["close"] >= p1["open"] and s["open"] <= p1["close"]:
            out.append("bullish_engulfing")
        if s["close"] < s["open"] and p1["close"] > p1["open"] and \
           s["open"] >= p1["close"] and s["close"] <= p1["open"]:
            out.append("bearish_engulfing")
    # 3-bar stars
    if p2["close"] < p2["open"] and _body(p2) > 0:
        mid_small = _body(p1) < 0.5 * _body(p2)
        if mid_small and s["close"] > s["open"] and s["close"] > (p2["open"] + p2["close"]) / 2:
            out.append("morning_star")
    if p2["close"] > p2["open"] and _body(p2) > 0:
        mid_small = _body(p1) < 0.5 * _body(p2)
        if mid_small and s["close"] < s["open"] and s["close"] < (p2["open"] + p2["close"]) / 2:
            out.append("evening_star")
    # three soldiers / crows
    if len(bars) >= 3:
        a, b, c = bars[-3], bars[-2], bars[-1]
        if all(x["close"] > x["open"] for x in (a, b, c)) and \
           a["close"] < b["close"] < c["close"] and all(_body(x) > 0 for x in (a, b, c)):
            out.append("three_white_soldiers")
        if all(x["close"] < x["open"] for x in (a, b, c)) and \
           a["close"] > b["close"] > c["close"] and all(_body(x) > 0 for x in (a, b, c)):
            out.append("three_black_crows")
    return out


BULLISH = {"hammer", "bullish_engulfing", "morning_star", "three_white_soldiers"}
BEARISH = {"shooting_star", "bearish_engulfing", "evening_star", "three_black_crows"}


def b5_trigger(m5_closed_bars: list, bias: str, config: dict) -> str:
    """Pola dari CLOSED bars searah mode B3. Sinyal @ close T, entry @ open T+1."""
    now_ts = config["now_ts"]
    last_close = int(m5_closed_bars[-1]["time"]) + config.get("bar_seconds", BAR_SECONDS[TRIGGER_TIMEFRAME])
    if last_close > now_ts:
        return "FAIL:forming_bar"
    patterns = _bullish_patterns(m5_closed_bars)
    if bias == "BUY_ONLY":
        matched = [p for p in patterns if p in BULLISH]
    elif bias == "SELL_ONLY":
        matched = [p for p in patterns if p in BEARISH]
    else:
        return "FAIL:none"
    if matched:
        return f"PASS:{matched[0]}"
    return "FAIL:none"


def b6_volume(m5_closed_bars: list, config: dict) -> str:
    """Tick-activity proxy. Baseline = mean volume 5 bar SEBELUM signal bar
    (exclude-self). Zero/missing baseline → FAIL:baseline_invalid (BUKAN PASS)."""
    if not config.get("volume_gate_enabled", False):
        return "DISABLED"
    n = int(config.get("vol_baseline_bars", 5))
    if len(m5_closed_bars) < n + 1:
        return "FAIL:baseline_invalid"
    sig = m5_closed_bars[-1]
    base = m5_closed_bars[-1 - n:-1]
    if not _is_finite(sig.get("volume")):
        return "FAIL:baseline_invalid"
    if any((not _is_finite(b.get("volume"))) or b["volume"] <= 0 for b in base):
        return "FAIL:baseline_invalid"
    mean_v = sum(b["volume"] for b in base) / n
    if mean_v <= 0:
        return "FAIL:baseline_invalid"
    ratio = float(config.get("vol_ratio", 1.2))
    if sig["volume"] > ratio * mean_v:
        return "PASS"
    return "FAIL:ratio"


def compute_sl_tp(profile: dict, atr_points: float, spread_points: float | None) -> dict:
    """SL/TP dari H-ATR-01 + min_stop formula + cap (SKIP eksplisit, bukan clamp)."""
    risk = profile["risk"]
    sl = risk["sl_atr_mult"] * atr_points
    tp = risk["tp_atr_mult"] * atr_points
    mp = risk["min_stop_params"]
    sp = spread_points if spread_points is not None else 0.0
    min_stop = max(sl, mp["spread_mult"] * sp + mp["stops_level_poin"] + mp["buffer_poin"])
    skip = min_stop > risk["max_stop_points"]
    return {"sl_points": min_stop, "tp_points": tp, "skip": skip,
            "sl_raw_points": sl, "max_stop_points": risk["max_stop_points"]}


def b7_risk(state: dict, profile: dict, sl_calc: dict) -> str:
    """Cooldown + stop bounds (desain §B7).

    Catatan keputusan owner (2026-09-08): batasan max_trades_per_day DIHAPUS —
    tidak ada cap frekuensi harian; kontrol risiko tetap dari cooldown,
    stop bounds (SKIP), dan sizing konstan-dolar.
    """
    risk = profile["risk"]
    let = state.get("last_entry_ts")
    if let is not None and state.get("now_ts") is not None:
        if state["now_ts"] - int(let) < risk["cooldown_minutes"] * 60:
            return "FAIL:cooldown"
    if sl_calc.get("skip"):
        return "FAIL:stop_bounds"
    return "PASS"


# ─── evaluate_all + decide ───────────────────────────────────────────────────

def evaluate_all(bars_dict: dict, profile: dict, config: dict, market_snapshot: dict | None = None) -> dict:
    """FULL DIAGNOSTIC — menilai SEMUA gate (meski satu sudah veto).

    bars_dict: {'m5': [...≤T closed...], 'm15': [...≤T closed...]}
    config: {'now_ts', 'rsi_bias_threshold', 'calendar', 'risk_state',
             'ticks_meta', 'min_bars_m15_warmup', 'vol_*'}
    Return FullDiagnostic dict dengan all_gate_results + bias/setup/trigger/snapshot.
    """
    m5 = bars_dict.get("m5", [])
    m15 = bars_dict.get("m15", [])
    now_ts = config["now_ts"]

    layer_a = layer_a_data_integrity(m5, config.get("ticks_meta"), config)
    if layer_a == "DATA_VALID":
        # P0-04 — M15 dipakai b3/b4 → wajib tervalidasi juga (per-timeframe reason).
        m15_valid = layer_a_m15_integrity(m15, config)
        if m15_valid != "DATA_VALID":
            layer_a = m15_valid

    snap = dict(market_snapshot or {})
    results: dict = {}
    bias = None
    setup = None
    trigger = None

    if layer_a != "DATA_VALID":
        # Pagar 3: Layer B TIDAK dijalankan atas data invalid.
        results = {g: "DISABLED" for g, _ in VETO_ORDER}
        return {
            "layer_a": layer_a,
            "layer_b_ran": False,
            "all_gate_results": results,
            "first_veto_reason": f"A:{layer_a.split(':', 1)[1]}",
            "bias": None,
            "setup": None,
            "trigger": None,
            "market_snapshot": snap,
        }

    zone_cfg = profile.get("zones_window", {})
    zones15 = Z.build_zones(m15)

    # pre-compute untuk snapshot & b7
    atr5 = Z.atr(m5)
    rsi_m15 = Z.rsi([b["close"] for b in m15]) if m15 else None
    rsi_m5 = Z.rsi([b["close"] for b in m5]) if m5 else None
    spread_points = (config.get("ticks_meta") or {}).get("spread_points")

    results["b1_news"] = b1_news(now_ts, config.get("calendar"), profile["news"])
    results["b2_session"] = b2_session(now_ts, profile["session_windows_utc"])
    results["b3_regime"] = b3_regime(m15, config)
    bias = results["b3_regime"].replace("PASS:", "") if results["b3_regime"].startswith("PASS:") else None
    config = dict(config)
    config["bias"] = bias
    results["b4_location"] = b4_location(profile, zones15, m5, config)
    if results["b4_location"].startswith("PASS:"):
        ref = results["b4_location"][5:].split("|")
        dist = None
        if len(ref) > 1 and ref[1].startswith("dist_atr="):
            dist = float(ref[1].split("=")[1])
        setup = {"kind": profile["location"]["kind"], "ref": ref[0], "distance_atr": dist}
    results["b5_trigger"] = b5_trigger(m5, bias, config) if bias else "FAIL:none"
    if results["b5_trigger"].startswith("PASS:"):
        trigger = {"pattern": results["b5_trigger"][5:], "bar_ts": int(m5[-1]["time"])}
    vol_enabled = profile["volume_gate"].get("enabled", False)
    vol_ratio = None
    if vol_enabled and len(m5) >= int(config.get("vol_baseline_bars", 5)) + 1:
        n = int(config.get("vol_baseline_bars", 5))
        base = m5[-1 - n:-1]
        if all(_is_finite(b.get("volume")) and b["volume"] > 0 for b in base):
            vol_ratio = m5[-1]["volume"] / (sum(b["volume"] for b in base) / n)
    results["b6_volume"] = b6_volume(m5, {**config, "volume_gate_enabled": vol_enabled,
                                          "vol_ratio": profile["volume_gate"].get("ratio", 1.2),
                                          "vol_baseline_bars": profile["volume_gate"].get("baseline_bars", 5)})

    sl_calc = None
    if atr5 is not None and atr5 > 0:
        sl_calc = compute_sl_tp(profile, atr5 * 100.0, spread_points)  # ATR harga → poin (1 poin = 0.01)
    state = dict(config.get("risk_state") or {})
    state["now_ts"] = now_ts
    results["b7_risk"] = b7_risk(state, profile, sl_calc or {"skip": False})

    snap.setdefault("spread", spread_points)
    snap.setdefault("atr", atr5 * 100.0 if atr5 else None)
    snap.setdefault("vol_ratio", vol_ratio)
    snap.setdefault("rsi_m15", rsi_m15)
    snap.setdefault("rsi_m5", rsi_m5)

    return {
        "layer_a": layer_a,
        "layer_b_ran": True,
        "all_gate_results": results,
        "first_veto_reason": None,   # diisi decide()
        "bias": bias,
        "setup": setup,
        "trigger": trigger,
        "sl_calc": sl_calc,
        "market_snapshot": snap,
    }


def decide(diagnostic: dict) -> tuple[str | None, str]:
    """OPERATIONAL DECISION — first veto (B1→B7) + decision BUY/SELL/WAIT.

    Tidak mengubah all_gate_results (invariant #8: diagnostic ≠ operational).
    """
    for gate, prefix in VETO_ORDER:
        v = diagnostic["all_gate_results"].get(gate, "DISABLED")
        if v == "DISABLED":
            continue
        if v == "PASS" or v.startswith("PASS:"):
            continue
        return f"{prefix}:{v}", "WAIT"
    bias = diagnostic.get("bias")
    if bias == "BUY_ONLY" and diagnostic.get("trigger"):
        return None, "BUY"
    if bias == "SELL_ONLY" and diagnostic.get("trigger"):
        return None, "SELL"
    return None, "WAIT"
