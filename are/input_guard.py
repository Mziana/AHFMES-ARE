"""
AHFMES Input Guard (§45)

Security hardening for all external inputs:
- Path traversal prevention
- Malicious JSON detection
- Oversized input limits
- Parameter grid validation
- Numeric sanity checks
"""

import json
import os
from typing import Any, Dict, List

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_PARAM_GRID_SIZE = 10000  # Max parameter combinations
MAX_BARS = 1_000_000  # Max bars in dataset
SAFE_DATA_DIR = os.path.join(os.getcwd(), "data")


def validate_path(path: str, base_dir: str = SAFE_DATA_DIR) -> str:
    """Prevent path traversal attacks.
    
    Returns the resolved path if safe, raises ValueError if not.
    """
    resolved = os.path.normpath(os.path.abspath(path))
    base_resolved = os.path.normpath(os.path.abspath(base_dir))
    if not resolved.startswith(base_resolved):
        raise ValueError(
            f"PATH_TRAVERSAL_BLOCKED: '{path}' resolves outside '{base_dir}'"
        )
    return resolved


def validate_json_input(data: Any, max_depth: int = 10, max_items: int = 10000) -> Any:
    """Reject malicious/oversized JSON.
    
    Checks: nesting depth, array sizes, string lengths.
    """
    if max_depth <= 0:
        raise ValueError("JSON_DEPTH_EXCEEDED")

    if isinstance(data, dict):
        if len(data) > max_items:
            raise ValueError(f"JSON_OBJECT_TOO_LARGE: {len(data)} > {max_items}")
        return {k: validate_json_input(v, max_depth - 1, max_items)
                for k, v in data.items()
                if isinstance(k, str) and len(k) < 1000}
    elif isinstance(data, list):
        if len(data) > max_items:
            raise ValueError(f"JSON_ARRAY_TOO_LARGE: {len(data)} > {max_items}")
        return [validate_json_input(v, max_depth - 1, max_items) for v in data]
    elif isinstance(data, str):
        if len(data) > 100000:
            raise ValueError(f"JSON_STRING_TOO_LONG: {len(data)} > 100000")
        return data
    elif isinstance(data, (int, float)):
        if not _is_finite(data):
            raise ValueError(f"JSON_NON_FINITE: {data}")
        return data
    else:
        return data


def validate_param_grid(grid: List[Dict[str, Any]], max_combos: int = MAX_PARAM_GRID_SIZE) -> List[Dict[str, Any]]:
    """Validate parameter grid for security and sanity."""
    if not grid or not isinstance(grid, list):
        raise ValueError("PARAM_GRID_EMPTY")
    if len(grid) > max_combos:
        raise ValueError(f"PARAM_GRID_TOO_LARGE: {len(grid)} > {max_combos}")
    for i, combo in enumerate(grid):
        if not isinstance(combo, dict):
            raise ValueError(f"PARAM_GRID[{i}]_NOT_DICT")
        for k, v in combo.items():
            if not isinstance(k, str):
                raise ValueError(f"PARAM_GRID[{i}]_KEY_NOT_STRING")
            if isinstance(v, (int, float)) and not _is_finite(v):
                raise ValueError(f"PARAM_GRID[{i}][{k}]_NON_FINITE: {v}")
    return grid


def validate_dataset(df_columns: List[str], bar_count: int, max_bars: int = MAX_BARS) -> None:
    """Validate dataset shape and required columns."""
    required = {"timestamp", "price"}
    missing = required - set(df_columns)
    if missing:
        raise ValueError(f"DATASET_MISSING_COLUMNS: {missing}")
    if bar_count <= 0:
        raise ValueError("DATASET_EMPTY")
    if bar_count > max_bars:
        raise ValueError(f"DATASET_TOO_LARGE: {bar_count} > {max_bars}")


def validate_file_size(filepath: str, max_size: int = MAX_FILE_SIZE) -> None:
    """Reject oversized files."""
    size = os.path.getsize(filepath)
    if size > max_size:
        raise ValueError(f"FILE_TOO_LARGE: {filepath} ({size} > {max_size})")


def validate_numeric(value: Any, name: str = "value",
                     min_val: float = -1e15, max_val: float = 1e15) -> float:
    """Validate numeric value is finite and within bounds."""
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name}_NOT_NUMERIC: {type(value).__name__}")
    fval = float(value)
    if not _is_finite(fval):
        raise ValueError(f"{name}_NON_FINITE: {fval}")
    if fval < min_val or fval > max_val:
        raise ValueError(f"{name}_OUT_OF_RANGE: {fval} not in [{min_val}, {max_val}]")
    return fval


def _is_finite(value: float) -> bool:
    """Check if value is finite (not NaN, Inf, or -Inf)."""
    import math
    return math.isfinite(value)
