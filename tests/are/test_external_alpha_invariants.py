"""
Multimodal External Alpha Pipeline Invariant Tests (DELEGASI_032)
"""

import json
import os
import tempfile
import unittest

from are.hypothesis_schema import InvalidHypothesisError
from TOOLS.external_alpha_scraper import ExtractionError, process_and_ingest_external_source


class TestExternalAlphaInvariants(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.output_jsonl = os.path.join(self.tmp_dir.name, "external_alphas.jsonl")

    def tearDown(self):
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def test_valid_external_extraction_and_storage(self):
        """
        Invariant 1: Valid external article hypothesis is extracted, strictly validated,
        and appended to JSONL with source_url metadata.
        """
        mock_article = """
        Quantitative Research Note:
        Strategy: Momentum Crossover on EURUSD Forex pair.
        We utilize RSI with 14 periods and 50-period EMA.
        Long entry when RSI < 35 and price above EMA 50.
        Exit when RSI > 65.
        Risk management: Stop loss at 45 pips, Take profit at 90 pips.
        """

        mock_llm = """```json
        {
            "strategy_id": "EXT_RSI_EMA_MOMENTUM_01",
            "asset_class": "FOREX",
            "indicators": [
                {"name": "RSI", "period": 14},
                {"name": "EMA", "period": 50}
            ],
            "entry_conditions": ["RSI < 35", "PRICE > EMA_50"],
            "exit_conditions": ["RSI > 65"],
            "risk_params": {
                "stop_loss_pips": 45.0,
                "take_profit_pips": 90.0
            }
        }
        ```"""

        strat_id = process_and_ingest_external_source(
            url="https://quantpedia.com/strategies/rsi-ema-crossover",
            output_jsonl_path=self.output_jsonl,
            mock_fetch=mock_article,
            mock_llm_response=mock_llm,
        )

        self.assertEqual(strat_id, "EXT_RSI_EMA_MOMENTUM_01")
        self.assertTrue(os.path.exists(self.output_jsonl))

        with open(self.output_jsonl, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]

        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["strategy_id"], "EXT_RSI_EMA_MOMENTUM_01")
        self.assertEqual(record["asset_class"], "FOREX")
        self.assertEqual(record["source_url"], "https://quantpedia.com/strategies/rsi-ema-crossover")
        self.assertIn("timestamp", record)
        self.assertEqual(record["risk_params"]["stop_loss_pips"], 45.0)

    def test_code_generation_rejection_fail_closed(self):
        """
        Invariant 2: When LLM outputs Python executable code instead of pure JSON,
        the system MUST raise ExtractionError and write zero bytes to JSONL (Fail-Closed).
        """
        mock_code_response = """
        def execute_alpha(prices):
            import os
            os.system('calc.exe')
            return "BUY"
        """

        with self.assertRaises(ExtractionError):
            process_and_ingest_external_source(
                url="https://github.com/malicious/repo",
                output_jsonl_path=self.output_jsonl,
                mock_fetch="Some untrusted text",
                mock_llm_response=mock_code_response,
            )

        if os.path.exists(self.output_jsonl):
            with open(self.output_jsonl, "r", encoding="utf-8") as f:
                lines = [ln.strip() for ln in f if ln.strip()]
            self.assertEqual(len(lines), 0, "Code generation payload was erroneously written to JSONL")

    def test_invalid_schema_rejection_from_external(self):
        """
        Invariant 3: External parameters with negative periods or invalid asset class
        MUST raise InvalidHypothesisError and write zero bytes to JSONL.
        """
        invalid_external_json = """{
            "strategy_id": "EXT_INVALID_01",
            "asset_class": "INVALID_ASSET_CLASS",
            "indicators": [{"name": "ATR", "period": -10}],
            "entry_conditions": ["ATR > 10"],
            "exit_conditions": ["ATR < 5"],
            "risk_params": {"stop_loss_pips": -50.0, "take_profit_pips": 100.0}
        }"""

        with self.assertRaises(InvalidHypothesisError):
            process_and_ingest_external_source(
                url="https://arxiv.org/abs/2401.0001",
                output_jsonl_path=self.output_jsonl,
                mock_fetch="Paper text",
                mock_llm_response=invalid_external_json,
            )

        if os.path.exists(self.output_jsonl):
            with open(self.output_jsonl, "r", encoding="utf-8") as f:
                lines = [ln.strip() for ln in f if ln.strip()]
            self.assertEqual(len(lines), 0, "Invalid schema payload was erroneously written to JSONL")


if __name__ == "__main__":
    unittest.main()