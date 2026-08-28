"""
AHFMES Cryptographic Hasher Utility
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Union


def compute_sha256(data: Union[str, bytes, dict, list]) -> str:
    """Computes SHA-256 hash of string, bytes, or JSON-serializable object."""
    if isinstance(data, str):
        raw = data.encode("utf-8")
    elif isinstance(data, bytes):
        raw = data
    else:
        raw = json.dumps(data, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
