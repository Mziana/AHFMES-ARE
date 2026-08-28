"""
AHFMES TOOLS — Isolated LLM Alpha Seed Extractor & Ingestion Engine (DELEGASI_031)

Extracts structured AlphaSeed parameters from natural language research papers / trading ideas.
Strictly parameter-only with zero dynamic code generation or execution (No exec/eval).
100% Python Standard Library.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import asdict
from typing import Any, Dict, Optional

from are.hypothesis_schema import AlphaSeed, InvalidHypothesisError, validate_alpha_seed


class ExtractionError(Exception):
    """Dilempar saat ekstraksi LLM gagal atau format rusak."""


def clean_json_response(raw_resp: str) -> str:
    """
    Strips markdown code fences, surrounding backticks, and whitespace.
    """
    text = raw_resp.strip()
    # Remove ```json ... ``` or ``` ... ```
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    # Find outer JSON boundaries if noise exists
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
        text = text[start_idx : end_idx + 1]
    return text.strip()


def extract_seed_from_text(
    raw_text: str,
    ollama_url: Optional[str] = None,
    model: Optional[str] = None,
    timeout_sec: float = 5.0,
) -> Dict[str, Any]:
    """
    Sends natural language hypothesis to local Ollama and extracts structured JSON parameters.
    """
    url = ollama_url or os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
    model_name = model or os.environ.get("OLLAMA_MODEL", "qwen2.5-coder")

    prompt = (
        "Extract quantitative trading strategy parameters from the text into pure JSON with keys: "
        "'strategy_id' (str), 'asset_class' ('FOREX'|'CRYPTO'|'COMMODITY'|'EQUITY'|'INDICES'), "
        "'indicators' (list of {'name': str, 'period': int}), "
        "'entry_conditions' (list of str), 'exit_conditions' (list of str), "
        "'risk_params' ({'stop_loss_pips': float, 'take_profit_pips': float}).\n"
        "Return ONLY pure valid JSON without commentary or markdown code blocks.\n\n"
        f"Input Text:\n{raw_text}\n"
    )

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    try:
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as response:
            if response.status != 200:
                raise ExtractionError(f"Ollama returned HTTP status {response.status}")
            data = json.loads(response.read().decode("utf-8"))
            raw_output = data.get("response", "")
    except Exception as e:
        raise ExtractionError(f"LLM extraction request failed: {e}") from e

    cleaned_json = clean_json_response(raw_output)
    try:
        parsed = json.loads(cleaned_json)
        if not isinstance(parsed, dict):
            raise ExtractionError("Parsed JSON response is not an object/dictionary")
        return parsed
    except json.JSONDecodeError as e:
        raise ExtractionError(f"Malformed JSON returned by LLM: {e}") from e


def ingest_and_validate_seed(
    raw_text: str,
    output_jsonl_path: str,
    ollama_url: Optional[str] = None,
    model: Optional[str] = None,
    mock_response: Optional[str] = None,
) -> str:
    """
    Extracts, strictly validates, and appends an AlphaSeed into the destination JSONL audit file.
    Fails-closed without writing to file if extraction or schema validation fails.
    """
    # 1. Extraction step
    if mock_response is not None:
        cleaned_json = clean_json_response(mock_response)
        try:
            raw_dict = json.loads(cleaned_json)
            if not isinstance(raw_dict, dict):
                raise ExtractionError("Parsed mock response is not a dictionary")
        except json.JSONDecodeError as e:
            raise ExtractionError(f"Malformed mock JSON: {e}") from e
    else:
        raw_dict = extract_seed_from_text(raw_text, ollama_url=ollama_url, model=model)

    # 2. Strict Schema Validation (Raises InvalidHypothesisError if invalid)
    seed: AlphaSeed = validate_alpha_seed(raw_dict)

    # 3. Append to JSONL Storage (Only reachable if 100% valid)
    seed_dict = asdict(seed)
    json_line = json.dumps(seed_dict, sort_keys=True)

    parent_dir = os.path.dirname(output_jsonl_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    with open(output_jsonl_path, "a", encoding="utf-8") as f:
        f.write(json_line + "\n")
        f.flush()
        os.fsync(f.fileno())

    return seed.strategy_id