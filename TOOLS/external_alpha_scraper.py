"""
AHFMES TOOLS — Multimodal External Alpha Scraper & Pipeline (DELEGASI_032, Organ 7)

Ingests quantitative trading hypotheses from external research articles, blogs, or transcripts,
extracts structured parameters using local LLM, and enforces strict schema validation.
Strictly parameter-only with zero dynamic code generation or execution (No exec/eval).
100% Python Standard Library.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import asdict
from typing import Any, Dict, Optional

from are.hypothesis_schema import AlphaSeed, InvalidHypothesisError, validate_alpha_seed


class ExtractionError(Exception):
    """Dilempar saat LLM gagal menghasilkan JSON valid atau scraping gagal."""


def clean_json_response(raw_resp: str) -> str:
    """
    Strips markdown code fences, surrounding backticks, and whitespace.
    """
    text = raw_resp.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
        text = text[start_idx : end_idx + 1]
    return text.strip()


def fetch_text_from_source(url: str, timeout: float = 10.0) -> str:
    """
    Fetches raw text content from a web URL using standard urllib.
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AHFMES-External-Alpha-Bot/1.0 (Autonomous Quantitative Research Engine)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                raise ExtractionError(f"HTTP error fetching source: status code {response.status}")
            raw_bytes = response.read()
            return raw_bytes.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise ExtractionError(f"HTTP Error {e.code} while fetching {url}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise ExtractionError(f"URL Error connecting to {url}: {e.reason}") from e
    except Exception as e:
        raise ExtractionError(f"Unexpected error fetching {url}: {e}") from e


def extract_parameters_via_llm(
    text: str,
    ollama_url: Optional[str] = None,
    model: Optional[str] = None,
    mock_response: Optional[str] = None,
    timeout_sec: float = 10.0,
) -> Dict[str, Any]:
    """
    Extracts structured AlphaSeed parameters from text using Ollama or mock response.
    """
    if mock_response is not None:
        cleaned = clean_json_response(mock_response)
        try:
            parsed = json.loads(cleaned)
            if not isinstance(parsed, dict):
                raise ExtractionError("Mock LLM response is not a valid JSON object/dictionary")
            return parsed
        except json.JSONDecodeError as e:
            raise ExtractionError(f"Failed to parse mock response as JSON: {e}") from e

    url = ollama_url or os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
    model_name = model or os.environ.get("OLLAMA_MODEL", "qwen2.5-coder")

    prompt = (
        "Ekstrak parameter strategi trading dari teks berikut ke dalam format JSON yang ketat. "
        "JANGAN tulis kode Python. JANGAN berikan penjelasan atau pengantar. "
        "Hanya kembalikan objek JSON dengan kunci:\n"
        "- strategy_id (str)\n"
        "- asset_class ('FOREX' | 'CRYPTO' | 'COMMODITY' | 'EQUITY' | 'INDICES')\n"
        "- indicators (list of {'name': str, 'period': int})\n"
        "- entry_conditions (list of str)\n"
        "- exit_conditions (list of str)\n"
        "- risk_params ({'stop_loss_pips': float, 'take_profit_pips': float})\n\n"
        f"Teks Sumber:\n{text}\n"
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


def process_and_ingest_external_source(
    url: str,
    output_jsonl_path: str,
    ollama_url: Optional[str] = None,
    model: Optional[str] = None,
    mock_fetch: Optional[str] = None,
    mock_llm_response: Optional[str] = None,
) -> str:
    """
    Coordinates end-to-end fetching, parameter extraction, strict validation, and audit recording.
    Fails-closed if any extraction, network, or schema validation check fails.
    """
    # 1. Fetch text
    if mock_fetch is not None:
        raw_text = mock_fetch
    else:
        raw_text = fetch_text_from_source(url)

    # 2. Extract JSON parameters
    raw_dict = extract_parameters_via_llm(
        text=raw_text,
        ollama_url=ollama_url,
        model=model,
        mock_response=mock_llm_response,
    )

    # 3. Strict Schema Validation (Raises InvalidHypothesisError if invalid)
    seed: AlphaSeed = validate_alpha_seed(raw_dict)

    # 4. Convert to dict and attach metadata
    record = asdict(seed)
    record["source_url"] = url
    record["timestamp"] = time.time()

    # 5. Append-Only JSONL Write
    parent_dir = os.path.dirname(output_jsonl_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    json_line = json.dumps(record, sort_keys=True)
    with open(output_jsonl_path, "a", encoding="utf-8") as f:
        f.write(json_line + "\n")
        f.flush()
        os.fsync(f.fileno())

    return seed.strategy_id