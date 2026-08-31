"""
AHFMES Atomic I/O (§43)

Safe artifact writes using temp file + fsync + atomic rename.
Prevents half-written files from being interpreted as valid artifacts.
"""

import json
import os
import tempfile
from typing import Any


def atomic_write_json(filepath: str, data: Any, indent: int = 2) -> None:
    """Write JSON atomically: temp file -> fsync -> rename.
    
    If the process crashes mid-write, only the temp file exists,
    never a half-written target file.
    """
    target_dir = os.path.dirname(filepath)
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)

    # Write to temp file in same directory (same filesystem for atomic rename)
    fd, tmp_path = tempfile.mkstemp(
        suffix=".tmp", prefix=".atomic_", dir=target_dir or "."
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
            f.flush()
            os.fsync(f.fileno())
        # Atomic rename (same filesystem)
        os.replace(tmp_path, filepath)
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def atomic_write_text(filepath: str, content: str) -> None:
    """Write text file atomically."""
    target_dir = os.path.dirname(filepath)
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(
        suffix=".tmp", prefix=".atomic_", dir=target_dir or "."
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, filepath)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def verify_file_exists(filepath: str) -> bool:
    """Check that file exists and is non-empty."""
    try:
        return os.path.isfile(filepath) and os.path.getsize(filepath) > 0
    except OSError:
        return False
