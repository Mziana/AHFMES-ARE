"""
Invariant Tests for Isolated High-Performance Vectorized Backtest Engine (DELEGASI_028, ACC-901..ACC-905)
"""

import ast
import json
import math
import os
import tempfile
import time
import unittest

import polars as pl

from are.backtest import BacktestResult, IsolatedBacktestEngine
from are.evidence import EvidenceLedger
from are.hasher import compute_sha256
from are.storage import EventStore


class TestBacktestInvariants(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "backtest_test.db")
        self.ledger = EvidenceLedger(self.db_path)
        self.engine = IsolatedBacktestEngine()

    def tearDown(self):
        if hasattr(self.ledger, "close"):
            self.ledger.close()
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def test_vectorized_backtest_deterministic_performance(self):
        """
        Invariant 1: Backtesting 100,000 rows of market data MUST execute in < 1.5 seconds.
        """
        n_rows = 100_000
        timestamps = [1700000000 + i * 60 for i in range(n_rows)]
        prices = [65000.0 + (math.sin(i * 0.01) * 500.0) + (i * 0.01) for i in range(n_rows)]

        df = pl.DataFrame({
            "timestamp": timestamps,
            "price": prices,
        })

        t_start = time.perf_counter()
        result = self.engine.run_backtest(historical_data=df)
        elapsed = time.perf_counter() - t_start

        self.assertIsInstance(result, BacktestResult)
        self.assertIsInstance(result.equity_curve, pl.DataFrame)
        self.assertIsInstance(result.trade_log, pl.DataFrame)
        self.assertEqual(len(result.equity_curve), n_rows)

        # Performance Assertion (< 1.5s)
        self.assertLess(
            elapsed, 1.5, f"Vectorized backtest of {n_rows} rows took {elapsed:.4f}s (must be < 1.5s)"
        )

        # Metrics Assertion
        self.assertIn("total_return", result.metrics)
        self.assertIn("max_drawdown", result.metrics)
        self.assertIn("sharpe_ratio", result.metrics)
        self.assertIn("profit_factor", result.metrics)
        self.assertEqual(result.metrics["total_bars"], n_rows)

    def test_isolation_invariant_ast_scan(self):
        """
        Invariant 2: are/backtest.py MUST NEVER import production execution modules
        or utilize dynamic import bypasses (AST verification).
        """
        backtest_path = os.path.join(os.path.dirname(__file__), "..", "..", "are", "backtest.py")
        backtest_path = os.path.abspath(backtest_path)

        with open(backtest_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        tree = ast.parse(source_code, filename="are/backtest.py")

        forbidden_modules = {
            "mt5_gateway",
            "mt5_feed",
            "mt5_runner",
            "safety",
            "operational",
            "p001_program",
            "web_ui",
            "copilot",
            "importlib",
        }

        for node in ast.walk(tree):
            # Check import ...
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]
                    self.assertNotIn(
                        module_name,
                        forbidden_modules,
                        f"Architectural Firewall Breach: '{alias.name}' imported in are/backtest.py",
                    )
            # Check from ... import ...
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    parts = node.module.split(".")
                    for part in parts:
                        self.assertNotIn(
                            part,
                            forbidden_modules,
                            f"Architectural Firewall Breach: 'from {node.module}' imported in are/backtest.py",
                        )

            # Check calls to __import__ or dynamic imports
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    self.assertNotEqual(
                        node.func.id,
                        "__import__",
                        "Architectural Firewall Breach: '__import__' call detected in are/backtest.py",
                    )

    def test_evidence_artifact_immutability_and_serialization(self):
        """
        Invariant 3: Converting Polars DataFrame to JSON and saving to EvidenceLedger
        executes cleanly without TypeError and produces verifiable cryptographic proof.
        """
        # Run small backtest (synthetic=True for testing only)
        result = self.engine.run_backtest(synthetic=True)

        # Save artifact to Evidence Ledger
        proof_hash = self.engine.save_artifact(result=result, evidence_ledger=self.ledger)

        self.assertIsInstance(proof_hash, str)
        self.assertEqual(len(proof_hash), 64, "SHA-256 proof hash must be 64 hex characters")

        # Fetch stored event from EventStore and verify hash integrity
        head = self.ledger._store.get_head("research_proofs")
        self.assertIsNotNone(head)

        last_event = self.ledger._store.get_event("research_proofs", head[0])
        self.assertIsNotNone(last_event)
        self.assertEqual(last_event.var_ref, proof_hash)

        # Re-compute hash from payload JSON string
        payload_str = last_event.event_data.decode("utf-8")
        recomputed_hash = compute_sha256(payload_str)
        self.assertEqual(proof_hash, recomputed_hash, "Proof hash mismatch on serialized payload")


if __name__ == "__main__":
    unittest.main()