"""
AHFMES Wave 2 — Numerical Robustness + Security + Infrastructure Tests

Covers §29 (numerical), §30 (test architecture), §40 (error taxonomy),
§43 (atomic writes), §42 (crash recovery), §45 (security).
"""

import json
import math
import os
import shutil
import tempfile
import unittest


# ─── §29: Numerical Robustness ───────────────────────────────

class TestNumericalRobustness(unittest.TestCase):
    """Edge cases for all metric computations."""

    def setUp(self):
        from are.numerical_safety import (
            safe_div, safe_sqrt, clean_returns, compute_returns_safe,
            compute_max_drawdown, compute_sortino_ratio, compute_cvar,
            validate_metric,
        )
        self.safe_div = safe_div
        self.safe_sqrt = safe_sqrt
        self.clean_returns = clean_returns
        self.compute_returns_safe = compute_returns_safe
        self.compute_max_drawdown = compute_max_drawdown
        self.compute_sortino_ratio = compute_sortino_ratio
        self.compute_cvar = compute_cvar
        self.validate_metric = validate_metric

    def test_safe_div_zero(self):
        self.assertEqual(self.safe_div(1.0, 0.0), 0.0)
        self.assertEqual(self.safe_div(1.0, 0.0, default=99.0), 99.0)

    def test_safe_div_normal(self):
        self.assertAlmostEqual(self.safe_div(10.0, 2.0), 5.0)

    def test_safe_sqrt_negative(self):
        self.assertEqual(self.safe_sqrt(-1.0), 0.0)

    def test_clean_returns_nan(self):
        result = self.clean_returns([1.0, float("nan"), 3.0])
        self.assertEqual(result, [1.0, 3.0])

    def test_clean_returns_inf(self):
        result = self.clean_returns([1.0, float("inf"), float("-inf")])
        self.assertEqual(result, [1.0])

    def test_clean_returns_none(self):
        result = self.clean_returns([1.0, None, 3.0])
        self.assertEqual(result, [1.0, 3.0])

    def test_clean_returns_empty(self):
        self.assertEqual(self.clean_returns([]), [])
        self.assertEqual(self.clean_returns([float("nan")]), [])

    def test_returns_from_equity_empty(self):
        self.assertEqual(self.compute_returns_safe([]), [])

    def test_returns_from_equity_single(self):
        self.assertEqual(self.compute_returns_safe([100.0]), [])

    def test_returns_from_equity_zero(self):
        result = self.compute_returns_safe([0.0, 100.0])
        self.assertEqual(result, [0.0])

    def test_max_drawdown_empty(self):
        dd, dur = self.compute_max_drawdown([])
        self.assertEqual(dd, 0.0)

    def test_max_drawdown_no_loss(self):
        dd, dur = self.compute_max_drawdown([100, 110, 120])
        self.assertEqual(dd, 0.0)

    def test_max_drawdown_100pct(self):
        dd, dur = self.compute_max_drawdown([100, 50, 0])
        self.assertEqual(dd, 1.0)  # Capped at 100%

    def test_sortino_empty(self):
        self.assertEqual(self.compute_sortino_ratio([]), 0.0)

    def test_sortino_all_positive(self):
        result = self.compute_sortino_ratio([0.01, 0.02, 0.03])
        self.assertGreaterEqual(result, 0.0)

    def test_cvar_empty(self):
        self.assertEqual(self.compute_cvar([], 0.05), 0.0)

    def test_validate_metric_nan(self):
        self.assertFalse(self.validate_metric("sharpe_ratio", float("nan")))

    def test_validate_metric_inf(self):
        self.assertFalse(self.validate_metric("max_drawdown", float("inf")))

    def test_validate_drawdown_over_100(self):
        self.assertFalse(self.validate_metric("max_drawdown", 1.5))

    def test_validate_win_rate_over_1(self):
        self.assertFalse(self.validate_metric("win_rate", 1.5))


# ─── §40: Error Taxonomy ─────────────────────────────────────

class TestErrorTaxonomy(unittest.TestCase):
    """Verify error classes carry correct severity and can be classified."""

    def test_data_error_severity(self):
        from are.errors import DataError, ErrorSeverity
        err = DataError("bad data", stage="data")
        self.assertEqual(err.severity, ErrorSeverity.INVALID_EVIDENCE)
        self.assertEqual(err.stage, "data")

    def test_timeout_severity(self):
        from are.errors import TimeoutError_, ErrorSeverity
        err = TimeoutError_("timed out", stage="wfo")
        self.assertEqual(err.severity, ErrorSeverity.FATAL)

    def test_classify_exception(self):
        from are.errors import classify_exception, TimeoutError_, ValidationError
        err = classify_exception(TimeoutError("request timed out"))
        self.assertIsInstance(err, TimeoutError_)

    def test_classify_nan_error(self):
        from are.errors import classify_exception, ValidationError
        err = classify_exception(ValueError("NaN detected"))
        self.assertIsInstance(err, ValidationError)


# ─── §43: Atomic Writes ──────────────────────────────────────

class TestAtomicWrites(unittest.TestCase):
    """Verify atomic writes create temp file + rename, no half-written targets."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_atomic_write_json(self):
        from are.atomic_io import atomic_write_json
        path = os.path.join(self.tmpdir, "test.json")
        atomic_write_json(path, {"key": "value", "num": 42})
        self.assertTrue(os.path.isfile(path))
        with open(path) as f:
            data = json.load(f)
        self.assertEqual(data["key"], "value")
        self.assertEqual(data["num"], 42)

    def test_atomic_write_no_temp_left(self):
        from are.atomic_io import atomic_write_json
        path = os.path.join(self.tmpdir, "test.json")
        atomic_write_json(path, {"x": 1})
        # No .tmp files should remain
        files = os.listdir(self.tmpdir)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0], "test.json")

    def test_atomic_write_creates_dirs(self):
        from are.atomic_io import atomic_write_json
        path = os.path.join(self.tmpdir, "sub", "dir", "test.json")
        atomic_write_json(path, {"nested": True})
        self.assertTrue(os.path.isfile(path))


# ─── §42: Crash Recovery ────────────────────────────────────

class TestCrashRecovery(unittest.TestCase):
    """Verify run state machine transitions and persistence."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_state_transitions(self):
        from are.run_state import RunStateManager, RunPhase
        mgr = RunStateManager(self.tmpdir)
        self.assertEqual(mgr.phase, RunPhase.CREATED)

        mgr.transition(RunPhase.RUNNING)
        self.assertEqual(mgr.phase, RunPhase.RUNNING)

        mgr.transition(RunPhase.COMPLETED)
        self.assertEqual(mgr.phase, RunPhase.COMPLETED)

        mgr.transition(RunPhase.VERIFIED)
        self.assertEqual(mgr.phase, RunPhase.VERIFIED)

    def test_invalid_transition_blocked(self):
        from are.run_state import RunStateManager, RunPhase
        mgr = RunStateManager(self.tmpdir)
        with self.assertRaises(ValueError):
            mgr.transition(RunPhase.COMPLETED)  # Can't skip RUNNING

    def test_persistence_survives_reload(self):
        from are.run_state import RunStateManager, RunPhase
        mgr = RunStateManager(self.tmpdir)
        mgr.transition(RunPhase.RUNNING)
        mgr.mark_stage_completed("data")

        # Reload
        mgr2 = RunStateManager(self.tmpdir)
        self.assertEqual(mgr2.phase, RunPhase.RUNNING)
        self.assertIn("data", mgr2.get_completed_stages())

    def test_failed_is_terminal(self):
        from are.run_state import RunStateManager, RunPhase
        mgr = RunStateManager(self.tmpdir)
        mgr.transition(RunPhase.RUNNING)
        mgr.transition(RunPhase.FAILED)
        with self.assertRaises(ValueError):
            mgr.transition(RunPhase.RUNNING)  # Can't recover from FAILED


# ─── §45: Security / Input Hardening ─────────────────────────

class TestInputHardening(unittest.TestCase):
    """Verify path traversal, oversized input, malicious JSON are blocked."""

    def test_path_traversal_blocked(self):
        from are.input_guard import validate_path
        with self.assertRaises(ValueError) as ctx:
            validate_path("../../etc/passwd")
        self.assertIn("PATH_TRAVERSAL", str(ctx.exception))

    def test_path_safe(self):
        from are.input_guard import validate_path
        result = validate_path("data/market_data/test.parquet")
        self.assertTrue(result.endswith("test.parquet"))

    def test_json_oversized_array(self):
        from are.input_guard import validate_json_input
        with self.assertRaises(ValueError) as ctx:
            validate_json_input(list(range(20000)), max_items=1000)
        self.assertIn("TOO_LARGE", str(ctx.exception))

    def test_json_deep_nesting(self):
        from are.input_guard import validate_json_input
        with self.assertRaises(ValueError):
            # 20 levels of nesting, limit is 5
            data = {"a": 1}
            for _ in range(20):
                data = {"a": data}
            validate_json_input(data, max_depth=5)

    def test_param_grid_empty(self):
        from are.input_guard import validate_param_grid
        with self.assertRaises(ValueError) as ctx:
            validate_param_grid([])
        self.assertIn("EMPTY", str(ctx.exception))

    def test_param_grid_too_large(self):
        from are.input_guard import validate_param_grid
        grid = [{"x": i} for i in range(20000)]
        with self.assertRaises(ValueError) as ctx:
            validate_param_grid(grid, max_combos=100)
        self.assertIn("TOO_LARGE", str(ctx.exception))

    def test_numeric_nan(self):
        from are.input_guard import validate_numeric
        with self.assertRaises(ValueError):
            validate_numeric(float("nan"), "test")

    def test_numeric_inf(self):
        from are.input_guard import validate_numeric
        with self.assertRaises(ValueError):
            validate_numeric(float("inf"), "test")


# ─── §29: Sharpe with edge cases ─────────────────────────────

class TestSharpeEdgeCases(unittest.TestCase):
    """Verify Sharpe ratio handles all §29 edge cases."""

    def test_sharpe_empty(self):
        from are.backtest import calculate_sharpe_ratio
        self.assertEqual(calculate_sharpe_ratio([]), 0.0)

    def test_sharpe_single(self):
        from are.backtest import calculate_sharpe_ratio
        self.assertEqual(calculate_sharpe_ratio([0.01]), 0.0)

    def test_sharpe_all_same(self):
        from are.backtest import calculate_sharpe_ratio
        self.assertEqual(calculate_sharpe_ratio([0.01, 0.01, 0.01]), 0.0)

    def test_sharpe_with_nan(self):
        from are.backtest import calculate_sharpe_ratio
        result = calculate_sharpe_ratio([0.01, float("nan"), 0.02])
        self.assertTrue(math.isfinite(result))

    def test_sharpe_with_inf(self):
        from are.backtest import calculate_sharpe_ratio
        result = calculate_sharpe_ratio([0.01, float("inf"), 0.02])
        self.assertTrue(math.isfinite(result))

    def test_sharpe_100pct_loss(self):
        from are.backtest import calculate_sharpe_ratio
        result = calculate_sharpe_ratio([-0.5, -0.3, -0.2])
        self.assertTrue(math.isfinite(result))


if __name__ == "__main__":
    unittest.main()
