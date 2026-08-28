"""
Alpha Zoo Seed Ingestion & Strict Schema Validation Invariant Tests (DELEGASI_031)
"""

import json
import os
import tempfile
import unittest

from are.hypothesis_schema import AlphaSeed, InvalidHypothesisError, validate_alpha_seed
from TOOLS.alpha_seed_extractor import ExtractionError, ingest_and_validate_seed


class TestAlphaSeedInvariants(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.jsonl_path = os.path.join(self.tmp_dir.name, "alpha_seeds.jsonl")

    def tearDown(self):
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def test_valid_seed_extraction_and_storage(self):
        """
        Invariant 1: Valid strategy parameters are strictly validated and stored to JSONL.
        """
        valid_mock_json = """```json
        {
            "strategy_id": "ALPHA_RSI_MEAN_REV_001",
            "asset_class": "FOREX",
            "indicators": [
                {"name": "RSI", "period": 14},
                {"name": "EMA", "period": 200}
            ],
            "entry_conditions": ["RSI < 30", "PRICE > EMA_200"],
            "exit_conditions": ["RSI > 70"],
            "risk_params": {
                "stop_loss_pips": 50.0,
                "take_profit_pips": 100.0
            }
        }
        ```"""

        strat_id = ingest_and_validate_seed(
            raw_text="Test hypothesis paper content",
            output_jsonl_path=self.jsonl_path,
            mock_response=valid_mock_json,
        )

        self.assertEqual(strat_id, "ALPHA_RSI_MEAN_REV_001")
        self.assertTrue(os.path.exists(self.jsonl_path))

        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]

        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["strategy_id"], "ALPHA_RSI_MEAN_REV_001")
        self.assertEqual(record["asset_class"], "FOREX")
        self.assertEqual(record["indicators"][0]["period"], 14)
        self.assertEqual(record["risk_params"]["stop_loss_pips"], 50.0)

    def test_invalid_schema_rejection(self):
        """
        Invariant 2: Schema violations (negative period, negative risk params, invalid asset class, missing keys)
        MUST raise InvalidHypothesisError and write ZERO lines to JSONL (Fail-Closed).
        """
        invalid_cases = [
            # Case 1: Negative period
            {
                "strategy_id": "INV_1",
                "asset_class": "FOREX",
                "indicators": [{"name": "RSI", "period": -5}],
                "entry_conditions": ["RSI < 30"],
                "exit_conditions": ["RSI > 70"],
                "risk_params": {"stop_loss_pips": 50.0, "take_profit_pips": 100.0},
            },
            # Case 2: Negative stop loss
            {
                "strategy_id": "INV_2",
                "asset_class": "CRYPTO",
                "indicators": [{"name": "MACD", "period": 12}],
                "entry_conditions": ["MACD > 0"],
                "exit_conditions": ["MACD < 0"],
                "risk_params": {"stop_loss_pips": -10.0, "take_profit_pips": 100.0},
            },
            # Case 3: Invalid asset class
            {
                "strategy_id": "INV_3",
                "asset_class": "UNKNOWN_EQUITIES",
                "indicators": [{"name": "SMA", "period": 50}],
                "entry_conditions": ["PRICE > SMA"],
                "exit_conditions": ["PRICE < SMA"],
                "risk_params": {"stop_loss_pips": 20.0, "take_profit_pips": 40.0},
            },
            # Case 4: Missing required field (no indicators)
            {
                "strategy_id": "INV_4",
                "asset_class": "COMMODITY",
                "entry_conditions": ["PRICE > 100"],
                "exit_conditions": ["PRICE < 100"],
                "risk_params": {"stop_loss_pips": 20.0, "take_profit_pips": 40.0},
            },
        ]

        for idx, case_dict in enumerate(invalid_cases):
            # Direct validator check
            with self.assertRaises(InvalidHypothesisError, msg=f"Failed on case {idx}"):
                validate_alpha_seed(case_dict)

            # Ingestion pipeline check
            with self.assertRaises(InvalidHypothesisError, msg=f"Failed on case {idx}"):
                ingest_and_validate_seed(
                    raw_text="Invalid input",
                    output_jsonl_path=self.jsonl_path,
                    mock_response=json.dumps(case_dict),
                )

        # Ensure file was never created or has 0 bytes/lines
        if os.path.exists(self.jsonl_path):
            with open(self.jsonl_path, "r", encoding="utf-8") as f:
                lines = [ln.strip() for ln in f if ln.strip()]
            self.assertEqual(len(lines), 0, "Corrupt or invalid seed was erroneously written to JSONL")

    def test_malformed_json_fallback(self):
        """
        Invariant 3: Non-JSON LLM responses / raw Python code MUST raise ExtractionError cleanly.
        """
        malformed_responses = [
            "def calculate_strategy():\n    return {'signal': 'BUY'}",
            "I'm sorry, I cannot generate a strategy for you.",
            "{ 'strategy_id': 'BAD_QUOTES', asset_class: FOREX }",
            "",
        ]

        for malformed in malformed_responses:
            with self.assertRaises(ExtractionError):
                ingest_and_validate_seed(
                    raw_text="Research text",
                    output_jsonl_path=self.jsonl_path,
                    mock_response=malformed,
                )


if __name__ == "__main__":
    unittest.main()