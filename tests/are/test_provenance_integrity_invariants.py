"""
Provenance Integrity & Deterministic Hash Invariants (DELEGASI_041 / RES-RED-15)
"""

import os
import tempfile
import time
import unittest

from are.backtest import IsolatedBacktestEngine
from are.evidence import EvidenceLedger


class TestProvenanceIntegrityInvariants(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "provenance_test.db")
        self.ledger = EvidenceLedger(self.db_path)
        self.engine = IsolatedBacktestEngine()

    def tearDown(self):
        if hasattr(self.ledger, "close"):
            self.ledger.close()
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def test_save_artifact_same_result_produces_same_hash(self):
        """
        RES-RED-15: Komputasi identik WAJIB menghasilkan proof_hash identik
        meskipun disimpan pada waktu berbeda (content-addressed proof).
        """
        result = self.engine.run_backtest()

        # Save twice at different times
        hash_1 = self.engine.save_artifact(result, self.ledger)
        time.sleep(0.02)  # Ensure time.time() has advanced
        hash_2 = self.engine.save_artifact(result, self.ledger)

        self.assertEqual(hash_1, hash_2, "Same computation must produce same proof hash")

    def test_save_artifact_different_result_produces_different_hash(self):
        """
        RES-RED-15: Komputasi berbeda WAJIB menghasilkan proof_hash berbeda.
        """
        result_a = self.engine.run_backtest(initial_capital=10000.0)
        result_b = self.engine.run_backtest(initial_capital=20000.0)

        hash_a = self.engine.save_artifact(result_a, self.ledger)
        hash_b = self.engine.save_artifact(result_b, self.ledger)

        self.assertNotEqual(hash_a, hash_b, "Different computations must produce different proof hashes")


if __name__ == "__main__":
    unittest.main()