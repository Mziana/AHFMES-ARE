"""Rotasi log data/logs/*.log — E-4. Stdlib only, tanpa dependency.

Pola: file > 5 MB digeser ke `.1` (lalu `.1`->`.2`->`.3`), versi tertua
(> keep=3) dibuang. Gagal rotasi satu file TIDAK menghentikan yang lain.

Dipanggil dari ARELauncher.bat (MODE START ALL) sebelum service start;
gagal rotasi tidak boleh memblok startup (launcher memakai `>nul 2>&1`).
"""
import os
import sys
from pathlib import Path

MAX_BYTES = 5_000_000  # sama dgn _rotate_own_log di are/mt5_server.py (mandat E-4)
KEEP = 3


def _rotate(path: Path, max_bytes: int, keep: int) -> None:
    try:
        if not path.exists() or path.stat().st_size <= max_bytes:
            return
        oldest = Path(f"{path}.{keep}")
        if oldest.exists():
            oldest.unlink()
        for i in range(keep - 1, 0, -1):
            src = Path(f"{path}.{i}")
            dst = Path(f"{path}.{i + 1}")
            if src.exists():
                os.replace(str(src), str(dst))
        os.replace(str(path), f"{path}.1")
        print(f"rotated: {path} -> {path}.1")
    except Exception as e:
        print(f"warning: rotate {path} gagal: {e}", file=sys.stderr)


def main() -> int:
    log_dir = Path(__file__).resolve().parent.parent / "data" / "logs"
    if not log_dir.exists():
        return 0
    for f in sorted(log_dir.glob("*.log")):
        _rotate(f, MAX_BYTES, KEEP)
    return 0


if __name__ == "__main__":
    sys.exit(main())