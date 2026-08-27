"""
Unit Tests for AHFMES P001 CLI Command Center (ACC-503, ACC-506)
"""

import io
import json
import os
import sys
import tempfile
import unittest

from are.cli import main


class TestP001CLI(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "cli_test.db")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_cli_status_json(self):
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            code = main(["--db-path", self.db_path, "status", "--json"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        self.assertEqual(code, 0)
        data = json.loads(output)
        self.assertIn("active_champion", data)
        self.assertIn("streams", data)

    def test_cli_run_cycle(self):
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            code = main(["--db-path", self.db_path, "run-cycle", "--symbol", "ETHUSDT"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        self.assertEqual(code, 0)
        self.assertIn("Status = PROMOTED", output)

    def test_cli_champion_history_and_rollback(self):
        # 1. Run a cycle first so there is a champion
        main(["--db-path", self.db_path, "run-cycle", "--symbol", "BTCUSDT"])

        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            code_hist = main(["--db-path", self.db_path, "champion", "history"])
            hist_out = sys.stdout.getvalue()

            sys.stdout = io.StringIO()
            code_roll = main(["--db-path", self.db_path, "champion", "rollback"])
            roll_out = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        self.assertEqual(code_hist, 0)
        self.assertIn("CHAMPION SUCCESSION HISTORY", hist_out)
        self.assertEqual(code_roll, 0)
        self.assertIn("Rolled back champion", roll_out)

    def test_cli_safety_kill_and_dashboard(self):
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            code_kill = main(["--db-path", self.db_path, "safety-kill"])
            kill_out = sys.stdout.getvalue()

            sys.stdout = io.StringIO()
            code_dash = main(["--db-path", self.db_path, "dashboard"])
            dash_out = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        self.assertEqual(code_kill, 0)
        self.assertIn("Kill Switch Activated", kill_out)
        self.assertEqual(code_dash, 0)
        self.assertIn("AHFMES-ARE RECURSIVE AUTONOMOUS ENGINE", dash_out)

    def test_cli_run_daemon_short(self):
        # Promote base champion first
        main(["--db-path", self.db_path, "run-cycle", "--symbol", "BTCUSDT"])

        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            code = main(["--db-path", self.db_path, "run-daemon", "--ticks", "3", "--interval", "0.0"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        self.assertEqual(code, 0)
        self.assertIn("Operational Daemon completed. Processed 3 ticks.", output)


if __name__ == "__main__":
    unittest.main()
