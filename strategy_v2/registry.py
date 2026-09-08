"""P0 — Experiment contract freeze (PAGAR 1).

config_hash = SHA-256 atas seluruh konten yang menentukan identitas
experiment: profile + hypothesis registry + cost model + execution timing +
timeframe + timezone + session calendar + indicator definitions.
Satu byte berubah → hash berubah → experiment identity BARU.

Pure stdlib. Tanpa I/O kecuali pembacaan file kontrak saat load eksplisit.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
CONTRACTS_DIR = PKG_DIR / "contracts"

# ─── Konstanta identitas experiment (bagian dari config_hash) ────────────────

STRATEGY_VERSION = "strategy_v2/0.1.0-p0"
EXECUTION_TIMING = "next_bar_open"          # sinyal @ close T, fill @ open T+1
TRIGGER_TIMEFRAME = "M5"                    # bar_seconds 300
REGIME_TIMEFRAME = "M15"                    # bar_seconds 900
TIMEZONE = "UTC"                            # semua epoch detik UTC

# Cost model (desain §4) — komponen, bukan angka statis. Nilai default =
# ESTIMATED_COST_MODEL bila spread historis tidak tersedia di dataset.
COST_MODEL = {
    "model": "component",
    "components": ["entry_spread", "exit_spread", "commission", "slippage", "delay"],
    "fallback_entry_spread_points": 20.0,   # XAUUSD Finex demo ≈ 0.20 USD
    "fallback_exit_spread_points": 20.0,
    "commission_per_lot_usd": 1.0,
    "slippage_points": 0.0,
    "delay_bars": 0,
    "label_when_fallback": "ESTIMATED_COST_MODEL",
    "label_when_historical": "HISTORICAL",
}

# Indicator definitions — identitas definisi ikut hash (Pagar 1).
INDICATOR_DEFS = {
    "ema": "recursive ewm alpha=2/(n+1)",
    "rsi": "wilder smoothing period 14",
    "atr": "true range mean period 14",
    "swing": "swing = extreme vs 5 bars kiri+kanan CONFIRMED (needs closed bars)",
    "zones": {
        "cluster_distance_atr": 0.75,
        "band_atr": 0.5,
        "max_zones_per_side": 5,
        "window_bars": 200,
        "timeframe": "M15",
    },
}


def _canonical(obj) -> str:
    """JSON deterministik: sort_keys + separators rapat (untuk hashing)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_profile(profile_id: str) -> dict:
    fname = "profile_scalp.json" if profile_id.upper().startswith("SCALP") else "profile_micro.json"
    return load_json(CONTRACTS_DIR / fname)


def load_hypothesis_registry() -> dict:
    return load_json(CONTRACTS_DIR / "hypothesis_registry.json")


def hypothesis(registry: dict, hyp_id: str) -> dict:
    """Ambil hipotesis dari registry — satu-satunya sumber parameter eksperimen."""
    try:
        return registry["hypotheses"][hyp_id]
    except KeyError as e:  # pragma: no cover
        raise KeyError(f"Hipotesis '{hyp_id}' tidak terdaftar — mining di luar registry dilarang") from e


# ─── Identity / hashing ──────────────────────────────────────────────────────

def dataset_hash(candles: list) -> str:
    """SHA-256 atas canonical candle list (sort_keys, rapat)."""
    return hashlib.sha256(_canonical(candles).encode("utf-8")).hexdigest()


def compute_config_hash(profile: dict, registry: dict,
                        dataset_sha: str | None = None,
                        calendar_artifact_hash: str | None = None,
                        broker_meta_hash: str | None = None) -> str:
    """Pagar 1 — SHA-256 atas seluruh konten yang menentukan identitas.

    dataset_sha ikut dalam hash bila diberikan (dataset identity per replay
    run disimpan terpisah sebagai `dataset_hash` di record; config_hash
    menjawab 'aturan main', jadi dataset tidak wajib ikut — tapi bila
    dimasukkan via dataset_sha, identity makin ketat).

    P0-02/P1-02: news calendar identity ikut hash via calendar_artifact_hash
    (SHA-256 konten artifact kalender). Dua replay dengan kalender berbeda →
    config_hash berbeda → experiment identity berbeda (tidak ada collision).

    F1b/E-2: broker metadata (contract_size, point, tick_value, unit spread
    bridge) ikut hash via broker_meta_hash — broker spec berubah → identity
    eksperimen baru (dilarang replay menyatakan kontrak sama)."""
    identity = {
        "strategy_version": STRATEGY_VERSION,
        "profile": profile,
        "hypothesis_registry": registry,
        "cost_model": COST_MODEL,
        "execution_timing": EXECUTION_TIMING,
        "trigger_timeframe": TRIGGER_TIMEFRAME,
        "regime_timeframe": REGIME_TIMEFRAME,
        "timezone": TIMEZONE,
        "session_calendar": profile.get("session_windows_utc"),
        "indicator_defs": INDICATOR_DEFS,
        "news_calendar_artifact": calendar_artifact_hash,
        "broker_meta": broker_meta_hash,
    }
    if dataset_sha is not None:
        identity["dataset_sha"] = dataset_sha
    return hashlib.sha256(_canonical(identity).encode("utf-8")).hexdigest()


def registry_id(registry: dict) -> str:
    return str(registry.get("registry_id", "UNKNOWN"))
