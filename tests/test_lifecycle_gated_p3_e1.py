# -*- coding: utf-8 -*-
"""Regression test E-1: integration test live-trading di-gate secara eksplisit.

Akar masalah (bukti runtime 2026-09-07): tests/test_bot_lifecycle.py men-place
order demo RIIL via UI API — menjalankan suite = men-trading-kan akun demo
(tiap run pindah balance ±beberapa dolar). Perbaikan: marker pytest
`integration` terdaftar di pyproject.toml + skip module-level kecuali env
ARE_LIVE_ITEST=1. Test ini memverifikasi gerbangnya, BUKAN menjalankan
lifecycle itu sendiri (tidak men-place order apa pun).
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _env_without_live_flag():
    env = dict(os.environ)
    env.pop("ARE_LIVE_ITEST", None)
    return env


def test_lifecycle_skipped_by_default():
    """Tanpa ARE_LIVE_ITEST, collect tests/test_bot_lifecycle.py harus
    menampilkan 'skipped' — tidak boleh ada kode lifecycle yang jalan."""
    # -rs: ringkasan skipped hanya tampil dengan flag ini (addopts -q
    # menekan ringkasan skips di plugin suite ini).
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only",
         "tests/test_bot_lifecycle.py", "-q", "-rs"],
        cwd=str(ROOT),
        env=_env_without_live_flag(),
        capture_output=True, text=True, timeout=60,
    )
    merged = (out.stdout + out.stderr).lower()
    assert "skipped" in merged, \
        f"test lifecycle harus skipped by default; output:\n{merged[-800:]}"


def test_marker_registered():
    """pytest --markers harus memuat marker `integration` (pyproject.toml)."""
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "--markers"],
        cwd=str(ROOT),
        capture_output=True, text=True, timeout=60,
    )
    assert "integration" in (out.stdout + out.stderr).lower(), \
        "marker 'integration' harus terdaftar (pyproject.toml [tool.pytest.ini_options].markers)"