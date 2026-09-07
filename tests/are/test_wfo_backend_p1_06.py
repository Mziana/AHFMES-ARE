# -*- coding: utf-8 -*-
"""Regression test P1-06: /api/are/wfo tidak lagi mensimulasikan hasil.

Akar bug: runWFO() di route.ts mengisi isReturn/ootReturn dengan Math.random()
dan memberi verdict PASS/MARGINAL — angka fiktif di samping data nyata.

Perbaikan: backend python nyata (wfo_backend.py) menjalankan
run_walk_forward_optimization pada parquet riil. Test ini mengeksekusi
backend langsung (jalur yang sama dengan route) dan menguji kontrak:
- hasil deterministik (2 run sama),
- clamp fold & fail-honest,
- verdict diturunkan dari metrik nyata (bukan random).
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND = ROOT / "UI" / "src" / "app" / "api" / "are" / "wfo" / "wfo_backend.py"


def _run_backend(symbol="XAUUSD", timeframe="H1", windows=3):
    r = subprocess.run([sys.executable, str(BACKEND), symbol, timeframe, str(windows)],
                       capture_output=True, text=True, cwd=str(ROOT), timeout=240)
    assert r.returncode == 0, f"backend crash: {r.stderr[-400:]}"
    return json.loads(r.stdout)


def test_wfo_backend_real_deterministic():
    d1 = _run_backend()
    d2 = _run_backend()
    assert d1["ok"] and d2["ok"]
    assert d1["summary"]["pooledOosSharpe"] == d2["summary"]["pooledOosSharpe"], \
        "WFO nyata harus deterministik (bukan random)"
    assert d1["summary"]["verdict"] == d2["summary"]["verdict"]


def test_wfo_backend_contract():
    d = _run_backend(windows=3)
    s = d["summary"]
    assert s["totalWindows"] == len(d["windows"])
    for w in d["windows"]:
        assert set(w) >= {"id", "isReturn", "ootReturn", "ootSharpe", "passed"}
        assert isinstance(w["passed"], bool)
    # verdict berasal dari pooled metrik nyata
    pooled = s["pooledOosSharpe"]
    if pooled >= 1.0 and s["pooledOosReturn"] > 0 and s["totalWindows"] >= 3:
        assert s["verdict"] == "PASS"
    elif pooled >= 0.5:
        assert s["verdict"] == "MARGINAL"
    else:
        assert s["verdict"] == "FAIL"


def test_wfo_backend_honest_failure():
    """Simbol tanpa data harus gagal JUJUR (bukan angka acak)."""
    d = _run_backend(symbol="NOPEUSD")
    assert d["ok"] is False
    assert "error" in d


def test_wfo_fold_clamp():
    """windows > 8 di-clamp (proteksi kompleksitas)."""
    d = _run_backend(windows=50)
    assert d["ok"] is True
    assert d["params"]["windows"] == 8
