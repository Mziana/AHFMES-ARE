"""B7 — Genealogy hipotesis (WAJIB #4): DNA penelitian ARE.

Setiap hipotesis harus menjawab: kenapa diciptakan, kenapa diubah, bukti apa
yang mendukung, keputusan apa yang mengikuti. Schema (kontrak final):
  id, parent_id, status, reason_for_change, hypothesis_statement,
  data_used, data_period, author, timestamp, config_hash, result, decision
Retro-link hipotesis lama ditandai jujur: retroactive=true, confidence=inferred.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

REGISTRY_PATH = os.path.join(_ROOT, "strategy_v2", "contracts", "hypothesis_registry.json")

GENEALOGY_FIELDS = (
    "id", "parent_id", "status", "reason_for_change", "hypothesis_statement",
    "data_used", "data_period", "author", "timestamp", "config_hash",
    "result", "decision",
)

# ── Retro-link rantai hipotesis lama (inferred dari provenance 'source' yang ada)
RETRO_LINKS: List[Dict[str, Any]] = [
    {
        "id": "H-SCORE-01",
        "parent_id": ["H-REGIME-SLOPE-02", "H-LOC-02", "H-ATR-01"],
        "reason_for_change": (
            "Ablation P4: B4 binary perusak nilai; B5 satu-satunya gate konsisten. "
            "Cognitive Layer v2.1 mengganti seleksi binary dengan skor kontinu 8 komponen; "
            "threshold dikalibrasi dari data (C1), bukan a priori."),
        "hypothesis_statement": (
            "Skor kontinu 0-100 (8 komponen deterministik) dengan threshold T* "
            "terkalibrasi menghasilkan expectancy net lebih tinggi daripada gate binary."),
        "data_used": ["C1 calibration sweep (12 threshold, dataset P3 86014edf)"],
        "data_period": "2026-07-28 .. 2026-09-08 (training P3)",
        "author": "buffy+owner (siklus C)",
        "timestamp": "2026-09-08",
        "decision": "ADOPTED as frozen champion T*=60.1 (C2/C3 lulus; C4 GAGAL_STATISTIK)",
        "result": "C2: +2.64 vs binary +0.69 (base); C3 must-cell +0.20; C4 GAGAL_STATISTIK",
        "confidence": "inferred",
        "retroactive": True,
    },
    {
        "id": "H-REGIME-SLOPE-02",
        "parent_id": ["H-Q1"],
        "reason_for_change": (
            "P6 iter-1 GAGAL_STATISTIK: long-only paksa rentan rezim (fold 5-6 downtrend). "
            "Revisi B3 = trend-strength dua-arah via slope EMA20 M15; |slope| < threshold = NO_TRADE."),
        "hypothesis_statement": (
            "Filter chop slope EMA20 M15 (min_abs_slope_points) memperbaiki expectancy "
            "lintas rezim dibanding long-only paksa."),
        "data_used": ["P6 iter-1 fold 5-6 (downtrend)"],
        "data_period": "2026-07-28 .. 2026-09-08 (training P3)",
        "author": "buffy (revisi P6 iter-1)",
        "timestamp": "2026-09-08",
        "decision": "ADOPTED into engine (b3_slope mode)",
        "result": "P4 iter-3 arm champion",
        "confidence": "inferred",
        "retroactive": True,
    },
    {
        "id": "H-SPREADCAP-03",
        "parent_id": [],
        "reason_for_change": "P5: edge mati di spread ~21 poin; cap live 34 poin (x2.0).",
        "hypothesis_statement": "Cap spread live 34 poin mencegah eksekusi pada biaya yang membunuh edge.",
        "data_used": ["P5 grid 18 sel"],
        "data_period": "2026-07-28 .. 2026-09-08 (training P3)",
        "author": "buffy (P5/P6)",
        "timestamp": "2026-09-08",
        "decision": "ADOPTED into live guard",
        "result": "gate spread live aktif",
        "confidence": "inferred",
        "retroactive": True,
    },
]


class GenealogyValidationError(Exception):
    pass


def build_genealogy_entry(hyp: Dict[str, Any]) -> Dict[str, Any]:
    """Entry registry lama -> entry genealogy penuh (retro-link jujur)."""
    known = {r["id"]: r for r in RETRO_LINKS}
    hid = hyp.get("id") or hyp.get("ID")
    retro = known.get(hid, {})
    return {
        "id": hid,
        "parent_id": retro.get("parent_id", []) if not retro else retro["parent_id"],
        "status": hyp.get("status", "UNKNOWN"),
        "reason_for_change": retro.get("reason_for_change",
                                       "LEGACY (pra-genealogy): source='" + str(hyp.get("source", "?")) + "'"),
        "hypothesis_statement": retro.get("hypothesis_statement",
                                          str(hyp.get("value"))[:180]),
        "data_used": retro.get("data_used", ["LEGACY — tidak terdokumentasi (pra-genealogy)"]),
        "data_period": retro.get("data_period", "LEGACY"),
        "author": retro.get("author", "LEGACY"),
        "timestamp": retro.get("timestamp", "LEGACY"),
        "config_hash": None,   # config hash per-era tidak tersimpan di registry lama
        "result": retro.get("result", None),
        "decision": retro.get("decision", None),
        "retroactive": True,
        "confidence": retro.get("confidence", "inferred"),
    }


def genealogy_view(registry_path: str = REGISTRY_PATH) -> Dict[str, Any]:
    """Seluruh registry dalam kacamata genealogy (idempotent, read-only)."""
    reg = json.load(open(registry_path, encoding="utf-8"))
    entries = {}
    for k, h in reg["hypotheses"].items():
        e = build_genealogy_entry(h)
        e["id"] = k
        entries[k] = e
    return {
        "registry_id": reg.get("registry_id"),
        "strategy_version": reg.get("strategy_version"),
        "genealogy_entries": entries,
        "schema_fields": list(GENEALOGY_FIELDS),
    }


def new_hypothesis(id_: str, parent_ids: List[str], statement: str,
                   reason: str, data_used: List[str], data_period: str,
                   config_hash: str, author: str = "buffy",
                   status: str = "HYPOTHESIS") -> Dict[str, Any]:
    """Hipotesis BARU lahir dengan genealogy penuh — tanpa field kosong."""
    if not parent_ids:
        raise GenealogyValidationError(
            "hipotesis baru wajib punya minimal satu parent (kontrak WAJIB #4)")
    missing = [p for p in parent_ids if not p]
    if missing:
        raise GenealogyValidationError("parent_ids tidak boleh kosong (kontrak WAJIB #4)")
    return {
        "id": id_, "parent_id": list(parent_ids), "status": status,
        "reason_for_change": reason, "hypothesis_statement": statement,
        "data_used": list(data_used), "data_period": data_period,
        "author": author, "timestamp": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        "config_hash": config_hash, "result": None, "decision": None,
        "retroactive": False, "confidence": "exact",
    }


import time  # noqa: E402  (dipakai new_hypothesis)
