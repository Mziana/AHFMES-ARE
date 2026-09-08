"""P1-03 — Validator decision log terhadap JSON Schema (stdlib only).

Subset draft-07 yang dipakai decision_log.schema.json: type (incl. list),
required, properties, enum, pattern, minimum, minLength, additionalProperties.
Dipakai test + CI untuk memvalidasi seluruh record JSONL replay.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "decision_log.schema.json"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _type_ok(value, t) -> bool:
    types = t if isinstance(t, list) else [t]
    for name in types:
        if name == "object" and isinstance(value, dict):
            return True
        if name == "string" and isinstance(value, str):
            return True
        if name == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if name == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if name == "boolean" and isinstance(value, bool):
            return True
        if name == "null" and value is None:
            return True
        if name == "array" and isinstance(value, list):
            return True
    return False


def validate_record(rec: dict, schema: dict, path: str = "$") -> list[str]:
    """Return daftar pelanggaran (kosong = valid). Subset draft-07."""
    errs: list[str] = []
    t = schema.get("type")
    if t is not None and not _type_ok(rec, t):
        return [f"{path}: expected type {t}, got {type(rec).__name__}"]

    if isinstance(rec, dict):
        for req in schema.get("required", []):
            if req not in rec:
                errs.append(f"{path}: missing required field '{req}'")
        props = schema.get("properties", {})
        addl = schema.get("additionalProperties", True)
        if addl is False:
            for k in rec:
                if k not in props:
                    errs.append(f"{path}: additional property '{k}' not allowed")
        elif isinstance(addl, dict):
            for k in rec:
                if k not in props:
                    errs.extend(validate_record(rec[k], addl, f"{path}.{k}"))
        for k, sub in props.items():
            if k in rec:
                errs.extend(validate_record(rec[k], sub, f"{path}.{k}"))

    if "enum" in schema and rec not in schema["enum"]:
        errs.append(f"{path}: value {rec!r} not in enum {schema['enum']}")
    if isinstance(rec, str):
        pat = schema.get("pattern")
        if pat is not None and not re.search(pat, rec):
            errs.append(f"{path}: {rec!r} does not match pattern {pat!r}")
        ml = schema.get("minLength")
        if ml is not None and len(rec) < ml:
            errs.append(f"{path}: string shorter than minLength {ml}")
    if isinstance(rec, (int, float)) and not isinstance(rec, bool):
        mn = schema.get("minimum")
        if mn is not None and rec < mn:
            errs.append(f"{path}: value {rec} < minimum {mn}")
    return errs


def validate_jsonl(path: str | Path, schema: dict | None = None) -> tuple[int, list[str]]:
    """Validasi seluruh record satu file JSONL. Return (n_records, errors)."""
    schema = schema or load_schema()
    n, errs = 0, []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            n += 1
            rec = json.loads(line)
            for e in validate_record(rec, schema, f"line{i}"):
                errs.append(e)
    return n, errs
