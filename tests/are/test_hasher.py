"""
Tests for Part B — Domain Hasher Dual Implementation Cross-Check (Slice-1 ACC-2 B3)

Explicit cross-check: IMPL_A vs IMPL_B produce bit-for-bit identical results.
"""

import unittest
from are.canonical import (
    _domain_hash_impl_a,
    _domain_hash_impl_b,
    _canonicalize_json_impl_a,
    _canonicalize_json_impl_b,
    _verify_canonical_bytes_impl_a,
    _verify_canonical_bytes_impl_b,
    canonicalize_object,
    domain_hash,
    DOMAIN_TAGS,
)


class TestDualImplHashCrossCheck(unittest.TestCase):
    """Explicit IMPL_A vs IMPL_B cross-checks."""

    def test_hash_impl_equivalence_all_tags(self):
        """For every registered tag, IMPL_A hash == IMPL_B hash."""
        test_data = b"cross-check test data"
        for tag in sorted(DOMAIN_TAGS):
            with self.subTest(tag=tag):
                h_a = _domain_hash_impl_a(tag, test_data)
                h_b = _domain_hash_impl_b(tag, test_data)
                self.assertEqual(
                    h_a, h_b,
                    f"Hash mismatch for tag {tag}: A={h_a} B={h_b}"
                )

    def test_hash_impl_equivalence_various_data(self):
        """Hash equivalence across various input data."""
        test_cases = [
            b"",
            b"a",
            b"hello world",
            b"unicode: \u00e9\u00f1\u4e2d",
            b"x" * 1000,
            b"\x00\x01\x02\xff\xfe\xfd",
        ]
        for tag in ["CANDIDATE_ROOT", "EVIDENCE_SNAPSHOT", "EDGE_NONCE_CONSUMPTION_LEDGER"]:
            for data in test_cases:
                with self.subTest(tag=tag, data_len=len(data)):
                    h_a = _domain_hash_impl_a(tag, data)
                    h_b = _domain_hash_impl_b(tag, data)
                    self.assertEqual(h_a, h_b)

    def test_canonical_json_impl_equivalence(self):
        """IMPL_A and IMPL_B canonical JSON produce identical output."""
        test_objects = [
            {"a": 1, "b": 2},
            {"z": 1, "a": 2},
            {"nested": {"b": 1, "a": 2}},
            {"items": [1, 2, 3]},
            {"bool": True, "null": None, "int": -42},
            {"list": [{"a": 1}, {"b": 2}]},
        ]
        for obj in test_objects:
            with self.subTest(obj=obj):
                json_a = _canonicalize_json_impl_a(obj)
                json_b = _canonicalize_json_impl_b(obj)
                self.assertEqual(
                    json_a, json_b,
                    f"JSON mismatch for {obj}: A={json_a} B={json_b}"
                )

    def test_bytes_verifier_impl_equivalence(self):
        """Both verifiers accept/reject same inputs."""
        valid_cases = [
            b"valid\n",
            b"multi\nline\n",
            "hello \u00e9 world\n".encode("utf-8"),
        ]
        invalid_cases = [
            b"invalid\r\n",
            b"BOM\xef\xbb\xbfdata\n",
            "non-nfc\u0301\n".encode("utf-8"),
        ]
        for data in valid_cases:
            with self.subTest(data=data):
                a_canon, _ = _verify_canonical_bytes_impl_a(data)
                b_canon, _ = _verify_canonical_bytes_impl_b(data)
                self.assertEqual(a_canon, b_canon)

        for data in invalid_cases:
            with self.subTest(data=data):
                a_reject = False
                b_reject = False
                try:
                    _verify_canonical_bytes_impl_a(data)
                except Exception:
                    a_reject = True
                try:
                    _verify_canonical_bytes_impl_b(data)
                except Exception:
                    b_reject = True
                self.assertEqual(a_reject, b_reject, f"Reject mismatch for {data}")

    def test_canonical_object_hash_equivalence(self):
        """High-level canonicalize_object produces same hash via both paths."""
        test_objects = [
            {"type": "test", "value": 123},
            {"nested": {"key": "value"}},
            {"array": [1, 2, 3], "flag": True},
        ]
        for obj in test_objects:
            with self.subTest(obj=obj):
                # canonicalize_object internally cross-checks
                canon, hash_val = canonicalize_object(obj, "CANDIDATE_ROOT")
                self.assertIsInstance(canon, bytes)
                self.assertEqual(len(hash_val), 64)

    def test_dual_impl_determinism(self):
        """Both implementations deterministic across multiple runs."""
        data = b"determinism test"
        tag = "CANDIDATE_ROOT"
        for _ in range(10):
            h_a = _domain_hash_impl_a(tag, data)
            h_b = _domain_hash_impl_b(tag, data)
            self.assertEqual(h_a, h_b)

    def test_canonical_json_determinism(self):
        """JSON canonicalization deterministic."""
        obj = {"keys": ["a", "b", "c"], "nested": {"x": 1, "y": 2}}
        for _ in range(10):
            j1 = _canonicalize_json_impl_a(obj)
            j2 = _canonicalize_json_impl_b(obj)
            self.assertEqual(j1, j2)

    def test_empty_inputs(self):
        """Edge case: empty data/objects."""
        # Empty bytes
        h_a = _domain_hash_impl_a("CANDIDATE_ROOT", b"")
        h_b = _domain_hash_impl_b("CANDIDATE_ROOT", b"")
        self.assertEqual(h_a, h_b)

        # Empty object
        json_a = _canonicalize_json_impl_a({})
        json_b = _canonicalize_json_impl_b({})
        self.assertEqual(json_a, json_b)

    def test_large_object_equivalence(self):
        """Large nested object equivalence."""
        large_obj = {
            "level1": {
                f"key{i}": {
                    "sub": list(range(100)),
                    "data": "x" * 50
                }
                for i in range(20)
            }
        }
        h_a = _domain_hash_impl_a("CANDIDATE_ROOT", _canonicalize_json_impl_a(large_obj))
        h_b = _domain_hash_impl_b("CANDIDATE_ROOT", _canonicalize_json_impl_b(large_obj))
        self.assertEqual(h_a, h_b)


class TestDualImplFailureModes(unittest.TestCase):
    """Verify both implementations fail identically on invalid input."""

    def test_both_reject_crlf(self):
        data = b"bad\r\n"
        with self.assertRaises(Exception):
            _verify_canonical_bytes_impl_a(data)
        with self.assertRaises(Exception):
            _verify_canonical_bytes_impl_b(data)

    def test_both_reject_bom(self):
        data = b"\xef\xbb\xbfdata\n"
        with self.assertRaises(Exception):
            _verify_canonical_bytes_impl_a(data)
        with self.assertRaises(Exception):
            _verify_canonical_bytes_impl_b(data)

    def test_both_reject_non_nfc(self):
        data = "e\u0301\n".encode("utf-8")
        with self.assertRaises(Exception):
            _verify_canonical_bytes_impl_a(data)
        with self.assertRaises(Exception):
            _verify_canonical_bytes_impl_b(data)

    def test_both_reject_float_in_json(self):
        obj = {"value": 3.14}
        with self.assertRaises(Exception):
            _canonicalize_json_impl_a(obj)
        with self.assertRaises(Exception):
            _canonicalize_json_impl_b(obj)

    def test_both_reject_unknown_tag(self):
        with self.assertRaises(Exception):
            _domain_hash_impl_a("UNKNOWN_TAG", b"data")
        with self.assertRaises(Exception):
            _domain_hash_impl_b("UNKNOWN_TAG", b"data")


class TestImplementationIndependence(unittest.TestCase):
    """Verify implementations are truly independent (different code paths)."""

    def test_impl_a_uses_json_module(self):
        """IMPL_A uses json module."""
        import json
        import inspect
        source = inspect.getsource(_canonicalize_json_impl_a)
        # IMPL_A uses json.dumps
        self.assertIn("json.dumps", source)

    def test_impl_b_manual_json(self):
        """IMPL_B manually encodes JSON without json module."""
        import json
        import inspect
        source = inspect.getsource(_canonicalize_json_impl_b)
        # IMPL_B should NOT use json.dumps
        self.assertNotIn("json.dumps", source)
        self.assertNotIn("json.", source)

    def test_impl_a_uses_unicodedata_normalize(self):
        """IMPL_A uses unicodedata.normalize."""
        import inspect
        source = inspect.getsource(_verify_canonical_bytes_impl_a)
        self.assertIn("unicodedata.normalize", source)

    def test_impl_b_also_uses_unicodedata(self):
        """IMPL_B also uses unicodedata for NFC check (required)."""
        import inspect
        source = inspect.getsource(_verify_canonical_bytes_impl_b)
        self.assertIn("unicodedata.normalize", source)

    def test_impl_a_uses_hashlib_sha256(self):
        """Both use hashlib.sha256."""
        import inspect
        src_a = inspect.getsource(_domain_hash_impl_a)
        src_b = inspect.getsource(_domain_hash_impl_b)
        self.assertIn("sha256", src_a.lower())
        self.assertIn("sha256", src_b.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)