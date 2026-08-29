"""
Evidence RAG Copilot & Hallucination Detector Invariant Tests (DELEGASI_035B)
100% Python Standard Library.
"""

import unittest

from are.copilot import ConversationalCopilot


class TestCopilotRAGInvariants(unittest.TestCase):
    def setUp(self):
        self.copilot = ConversationalCopilot()

    def test_build_evidence_context_returns_structured_string(self):
        """
        Invariant 1: Evidence context returns a structured string starting with
        [EVIDENCE CONTEXT] and ending with [END SYSTEM INSTRUCTION].
        """
        ctx = self.copilot._build_evidence_context(event_store=None)
        self.assertIsInstance(ctx, str)
        self.assertTrue(ctx.startswith("[EVIDENCE CONTEXT"))
        self.assertIn("[END EVIDENCE CONTEXT]", ctx)
        self.assertIn("[SYSTEM INSTRUCTION]", ctx)
        self.assertIn("[END SYSTEM INSTRUCTION]", ctx)

    def test_build_evidence_context_truncates_to_2000_chars(self):
        """
        Invariant 2: Evidence context is bounded and never exceeds 2000 characters.
        """
        ctx = self.copilot._build_evidence_context(event_store=None)
        self.assertLessEqual(len(ctx), 2000)

    def test_build_prompt_includes_evidence_before_user_message(self):
        """
        Invariant 3: Prompt builder places [EVIDENCE CONTEXT] before User: {message}.
        """
        prompt = self.copilot.build_prompt("Berapa slippage terakhir?")
        self.assertIn("[EVIDENCE CONTEXT", prompt)
        self.assertIn("User: Berapa slippage terakhir?", prompt)
        idx_evidence = prompt.find("[EVIDENCE CONTEXT")
        idx_user = prompt.find("User:")
        self.assertLess(idx_evidence, idx_user, "Evidence context must precede user message")

    def test_ollama_prompt_contains_evidence_hash(self):
        """
        Invariant 4: Prompt contains cryptographic Evidence Hash.
        """
        prompt = self.copilot.build_prompt("Halo")
        self.assertIn("Evidence Hash:", prompt)
        # Verify hash format (64 hex characters)
        import re
        match = re.search(r"Evidence Hash:\s*([a-f0-9]{64})", prompt)
        self.assertIsNotNone(match, "Evidence Hash must be a valid 64-char SHA256 hex string")

    def test_hallucination_detector_exact_match_pass(self):
        """
        Invariant 5: Exact match between Ollama response claims and Evidence context passes.
        """
        evidence_ctx = "Recent executions: EURUSD slippage: 3.8 pips, latency: 120.0ms"
        ollama_resp = "Slippage pada EURUSD adalah 3.8 pips dengan latensi 120.0ms."
        ok, res = self.copilot._verify_factual_consistency(ollama_resp, evidence_ctx)
        self.assertTrue(ok)
        self.assertEqual(res, ollama_resp)

    def test_hallucination_detector_tolerance_match_pass(self):
        """
        Invariant 6: Floating-point value within 0.1% tolerance passes without blocking.
        """
        evidence_ctx = "EURUSD slippage: 3.8 pips"
        ollama_resp = "Slippage tercatat sebesar 3.8001 pips."
        ok, res = self.copilot._verify_factual_consistency(ollama_resp, evidence_ctx)
        self.assertTrue(ok)
        self.assertEqual(res, ollama_resp)

    def test_hallucination_detector_mismatch_block(self):
        """
        Invariant 7: Quantitative claims conflicting with Evidence are blocked (Fail-Closed).
        """
        evidence_ctx = "EURUSD slippage: 3.8 pips"
        ollama_resp = "Slippage tercatat sebesar 4.2 pips."
        ok, res = self.copilot._verify_factual_consistency(ollama_resp, evidence_ctx)
        self.assertFalse(ok)
        self.assertIn("DATA TIDAK TERSEDIA", res)

    def test_hallucination_detector_conversational_number_ignored(self):
        """
        Invariant 8: General conversational numbers (years, items) not tied to metrics are ignored.
        """
        evidence_ctx = "EURUSD slippage: 3.8 pips"
        ollama_resp = "Pada tahun 2026 ada 5 anomali tercatat dengan slippage 3.8 pips."
        ok, res = self.copilot._verify_factual_consistency(ollama_resp, evidence_ctx)
        self.assertTrue(ok)
        self.assertEqual(res, ollama_resp)

    def test_hallucination_detector_field_not_in_evidence_pass(self):
        """
        Invariant 9: Metrics not present in evidence context pass through without false positive rejection.
        """
        evidence_ctx = "EURUSD slippage: 3.8 pips"
        ollama_resp = "Sharpe ratio strategi ini adalah 1.85."
        ok, res = self.copilot._verify_factual_consistency(ollama_resp, evidence_ctx)
        self.assertTrue(ok)
        self.assertEqual(res, ollama_resp)


if __name__ == "__main__":
    unittest.main()