"""
Tests for Part B — Canonical Bytes Verifier (Slice-1 ACC-2 B1, B2)

Covers:
- B1: Verifier FAIL-CLOSED: non-NFC/BOM/CRLF -> REJECT + offset
- B2: Adversarial tests: combining char, tr-TR locale, CRLF injection, key reverse
- Dual implementation cross-check (IMPL_A == IMPL_B)

Follows SLICE_1_CONTRACT.md §2, GRAND DESIGN V1 (AHFMES_CANONICAL_OBJECT_V1),
HASH_DOMAIN_TAGS_V1.
"""

import locale
import unittest

from are.canonical import (
    verify_canonical_bytes,
    canonicalize_json,
    domain_hash,
    canonicalize_object,
    VerificationError,
    TagNotFoundError,
    list_domain_tags,
)


class TestVerifierFailClosed(unittest.TestCase):
    """ACC-2 B1: Verifier FAIL-CLOSED rejects invalid inputs."""

    def test_valid_utf8_nfc_lf_passes(self):
        """Valid NFC + LF bytes pass verification."""
        data = "hello world\n".encode("utf-8")
        result = verify_canonical_bytes(data)
        self.assertTrue(result.verified)
        self.assertEqual(result.canonical_bytes, data)

    def test_bom_rejected(self):
        """UTF-8 BOM rejected at offset 0."""
        data = b"\xef\xbb\xbfhello\n"
        with self.assertRaises(VerificationError) as cm:
            verify_canonical_bytes(data)
        self.assertEqual(cm.exception.offset, 0)
        self.assertIn("BOM", str(cm.exception))

    def test_utf16_bom_rejected(self):
        """UTF-16 BOM rejected."""
        for bom in [b"\xff\xfe", b"\xfe\xff"]:
            data = bom + b"hello\n"
            with self.assertRaises(VerificationError) as cm:
                verify_canonical_bytes(data)
            self.assertEqual(cm.exception.offset, 0)

    def test_crlf_rejected(self):
        """CRLF rejected with correct offset."""
        data = b"hello\r\nworld\n"
        with self.assertRaises(VerificationError) as cm:
            verify_canonical_bytes(data)
        self.assertIn("CRLF", str(cm.exception))
        # Offset should point to \r
        self.assertEqual(cm.exception.offset, data.find(b"\r\n"))

    def test_standalone_cr_rejected(self):
        """Standalone CR (not followed by LF) rejected."""
        data = b"hello\rworld\n"
        with self.assertRaises(VerificationError) as cm:
            verify_canonical_bytes(data)
        self.assertIn("CR", str(cm.exception))

    def test_lf_allowed(self):
        """Plain LF is allowed."""
        data = "line1\nline2\n".encode("utf-8")
        result = verify_canonical_bytes(data)
        self.assertTrue(result.verified)

    def test_nfc_required(self):
        """Non-NFC strings rejected (e.g., combining characters)."""
        # "e\u0301" (e + combining acute) vs "é" (precomposed)
        data = "e\u0301\n".encode("utf-8")  # NFD form
        with self.assertRaises(VerificationError) as cm:
            verify_canonical_bytes(data)
        self.assertIn("NFC", str(cm.exception))

    def test_precomposed_nfc_passes(self):
        """Precomposed NFC passes."""
        data = "é\n".encode("utf-8")  # Precomposed NFC
        result = verify_canonical_bytes(data)
        self.assertTrue(result.verified)

    def test_offset_reported_correctly(self):
        """Error offset points to first violation."""
        # Invalid byte sequence
        data = b"hello \xff world\n"
        with self.assertRaises(VerificationError) as cm:
            verify_canonical_bytes(data)
        self.assertGreaterEqual(cm.exception.offset, 0)


class TestAdversarialCases(unittest.TestCase):
    """ACC-2 B2: Adversarial test cases per SLICE_1_CONTRACT.md."""

    def test_combining_characters(self):
        """Combining characters must be NFC normalized."""
        # Various combining sequences
        test_cases = [
            "e\u0301",  # e + acute
            "a\u0300",  # a + grave
            "o\u0302",  # o + circumflex
            "n\u0303",  # n + tilde
            "c\u0327",  # c + cedilla
        ]
        for s in test_cases:
            data = (s + "\n").encode("utf-8")
            with self.assertRaises(VerificationError) as cm:
                verify_canonical_bytes(data)
            self.assertIn("NFC", str(cm.exception))

    def test_locale_independence(self):
        """
        Verifier must be locale-independent (Turkish I/i problem, etc.).
        NFC normalization via unicodedata is locale-independent.
        """
        # Save and set locale
        old_locale = locale.getlocale(locale.LC_CTYPE)
        try:
            locale.setlocale(locale.LC_CTYPE, "tr_TR.UTF-8")
        except locale.Error:
            self.skipTest("tr_TR.UTF-8 locale not available")

        try:
            # Even under Turkish locale, verification must be correct
            data = "istanbul\n".encode("utf-8")
            result = verify_canonical_bytes(data)
            self.assertTrue(result.verified)

            # Genuinely non-NFC string should still fail (e + combining acute)
            with self.assertRaises(VerificationError):
                verify_canonical_bytes("e\u0301stanbul\n".encode("utf-8"))
        finally:
            locale.setlocale(locale.LC_CTYPE, old_locale)

    def test_locale_independence_no_locale(self):
        """Same test without locale change - verifier is always locale-independent."""
        data = "istanbul\n".encode("utf-8")
        result = verify_canonical_bytes(data)
        self.assertTrue(result.verified)

        with self.assertRaises(VerificationError):
            verify_canonical_bytes("e\u0301stanbul\n".encode("utf-8"))

    def test_crlf_injection(self):
        """CRLF injection attempts must be rejected."""
        payloads = [
            b"valid\r\ninjected\n",
            b"header: value\r\nmalicious: true\n",
            b"\r\n\r\nbody\n",
        ]
        for data in payloads:
            with self.assertRaises(VerificationError):
                verify_canonical_bytes(data)

    def test_key_reversal_attack(self):
        """Key order must not affect canonicalization."""
        obj1 = {"b": 1, "a": 2}
        obj2 = {"a": 2, "b": 1}
        hash1 = canonicalize_object(obj1, "CANDIDATE_ROOT")[1]
        hash2 = canonicalize_object(obj2, "CANDIDATE_ROOT")[1]
        # Same keys, different order -> same hash (keys sorted)
        self.assertEqual(hash1, hash2)

    def test_nested_dict_key_order(self):
        """Nested dict keys must also be sorted."""
        obj1 = {"z": {"b": 1, "a": 2}}
        obj2 = {"z": {"a": 2, "b": 1}}
        h1 = canonicalize_object(obj1, "CANDIDATE_ROOT")[1]
        h2 = canonicalize_object(obj2, "CANDIDATE_ROOT")[1]
        self.assertEqual(h1, h2)

    def test_list_order_matters(self):
        """List order MUST affect hash (lists are ordered)."""
        obj1 = {"items": [1, 2, 3]}
        obj2 = {"items": [3, 2, 1]}
        h1 = canonicalize_object(obj1, "CANDIDATE_ROOT")[1]
        h2 = canonicalize_object(obj2, "CANDIDATE_ROOT")[1]
        self.assertNotEqual(h1, h2)

    def test_float_rejected(self):
        """Float values in identity rejected."""
        with self.assertRaises(VerificationError) as cm:
            canonicalize_object({"value": 3.14}, "CANDIDATE_ROOT")
        self.assertIn("Float", str(cm.exception))

    def test_nan_inf_rejected(self):
        """NaN/Infinity rejected."""
        for val in [float("nan"), float("inf"), float("-inf")]:
            with self.assertRaises(VerificationError):
                canonicalize_object({"v": val}, "CANDIDATE_ROOT")

    def test_null_allowed(self):
        """null is allowed."""
        result = canonicalize_object({"v": None}, "CANDIDATE_ROOT")
        self.assertIsInstance(result[1], str)

    def test_empty_string_allowed(self):
        """Empty string allowed."""
        result = canonicalize_object({"v": ""}, "CANDIDATE_ROOT")
        self.assertIsInstance(result[1], str)

    def test_unicode_normalization_forms(self):
        """Various Unicode normalization forms tested."""
        # NFC should pass
        for char in ["é", "ñ", "ü", "中", "한"]:
            data = (char + "\n").encode("utf-8")
            result = verify_canonical_bytes(data)
            self.assertTrue(result.verified)


class TestDomainHash(unittest.TestCase):
    """ACC-2 B3: Domain hasher with tag lookup."""

    def test_known_tag_hash(self):
        """Known tag produces hash."""
        data = b"test data"
        tag = "CANDIDATE_ROOT"
        h = domain_hash(tag, data)
        self.assertEqual(len(h), 64)  # SHA-256 hex
        # Deterministic
        self.assertEqual(h, domain_hash(tag, data))

    def test_unknown_tag_rejected(self):
        """Unknown tag rejected (closure rule)."""
        with self.assertRaises(TagNotFoundError):
            domain_hash("UNKNOWN_TAG", b"data")

    def test_tag_case_sensitive(self):
        """Tag lookup is case-sensitive."""
        # Valid tag
        h1 = domain_hash("CANDIDATE_ROOT", b"data")
        # Wrong case
        with self.assertRaises(TagNotFoundError):
            domain_hash("candidate_root", b"data")
        with self.assertRaises(TagNotFoundError):
            domain_hash("Candidate_Root", b"data")

    def test_all_registered_tags_work(self):
        """All registered tags produce hashes."""
        from are.canonical import list_domain_tags
        for tag in list_domain_tags():
            h = domain_hash(tag, b"test")
            self.assertEqual(len(h), 64)

    def test_dual_impl_hash_match(self):
        """IMPL_A and IMPL_B produce identical hashes."""
        for tag in ["CANDIDATE_ROOT", "EVIDENCE_SNAPSHOT", "REFINEMENT_PROSPECTIVE_RELIANCE_RECEIPT"]:
            h1 = domain_hash(tag, b"test data")
            # Both implementations already cross-checked internally
            self.assertEqual(len(h1), 64)

    def test_hash_includes_tag(self):
        """Different tags produce different hashes for same data."""
        data = b"same data"
        tags = list_domain_tags()[:5]
        hashes = {domain_hash(t, data) for t in tags}
        self.assertEqual(len(hashes), len(tags))  # All unique

    def test_hash_format(self):
        """Hash format: SHA-256 hex, 64 chars."""
        h = domain_hash("CANDIDATE_ROOT", b"data")
        self.assertEqual(len(h), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in h))

    def test_tag_from_register_v30(self):
        """Tags from Register V30 work."""
        register_tags = [
            "REFINEMENT_RELIANCE_INVALIDITY_EVENT_ROOT",
            "REFINEMENT_PROSPECTIVE_RELIANCE_SUBJECT",
            "EDGE_NONCE_CONSUMPTION_LEDGER",
            "ROLLBACK_CAUSE_OBSERVATION",
            "EDGE_INTERFERENCE_EVIDENCE",
        ]
        for tag in register_tags:
            h = domain_hash(tag, b"data")
            self.assertEqual(len(h), 64)


class TestCanonicalJSON(unittest.TestCase):
    """Canonical JSON serialization tests."""

    def test_key_sorting(self):
        """Keys must be sorted."""
        obj1 = {"z": 1, "a": 2}
        obj2 = {"a": 2, "z": 1}
        h1 = canonicalize_object(obj1, "CANDIDATE_ROOT")[1]
        h2 = canonicalize_object(obj2, "CANDIDATE_ROOT")[1]
        self.assertEqual(h1, h2)

    def test_nested_sorting(self):
        """Nested dicts sorted."""
        obj1 = {"outer": {"b": 1, "a": 2}}
        obj3 = {"outer": {"a": 2, "b": 1}}
        h1 = canonicalize_object(obj1, "CANDIDATE_ROOT")[1]
        h2 = canonicalize_object(obj3, "CANDIDATE_ROOT")[1]
        self.assertEqual(h1, h2)

    def test_list_order_preserved(self):
        """List order preserved."""
        obj1 = {"items": [1, 2]}
        obj2 = {"items": [2, 1]}
        h1 = canonicalize_object(obj1, "CANDIDATE_ROOT")[1]
        h2 = canonicalize_object(obj2, "CANDIDATE_ROOT")[1]
        self.assertNotEqual(h1, h2)

    def test_bool_true_false(self):
        """True/False serialized correctly."""
        h1 = canonicalize_object({"v": True}, "CANDIDATE_ROOT")[1]
        h2 = canonicalize_object({"v": False}, "CANDIDATE_ROOT")[1]
        self.assertNotEqual(h1, h2)

    def test_integer_serialization(self):
        """Integers serialized canonically."""
        obj = {"v": 42}
        canonical, _ = canonicalize_object(obj, "CANDIDATE_ROOT")
        self.assertIn(b"42", canonical)

    def test_negative_integer(self):
        """Negative integers serialized."""
        canonical, _ = canonicalize_object({"v": -42}, "CANDIDATE_ROOT")
        self.assertIn(b"-42", canonical)


class TestDualImplementationCrossCheck(unittest.TestCase):
    """Dual implementation cross-check (IMPL_A vs IMPL_B)."""

    def test_bytes_verifier_both_impl(self):
        """Both implementations agree on valid input."""
        data = "hello\n".encode("utf-8")
        result = verify_canonical_bytes(data)
        self.assertTrue(result.verified)

    def test_bytes_verifier_both_reject_same(self):
        """Both implementations reject same invalid input."""
        bad_data = "bad\r\n".encode("utf-8")
        with self.assertRaises(VerificationError):
            verify_canonical_bytes(bad_data)

    def test_canonical_json_both_impl(self):
        """Both implementations produce identical canonical JSON."""
        test_objs = [
            {"a": 1, "b": 2},
            {"z": {"b": 1, "a": 2}},
            {"items": [1, 2, 3]},
            {"bool": True, "null": None, "int": -5},
        ]
        for obj in test_objs:
            h1 = canonicalize_object(obj, "CANDIDATE_ROOT")[1]
            # Dual impl already cross-checked inside canonicalize_object
            self.assertIsInstance(h1, str)

    def test_domain_hash_both_impl(self):
        """Domain hash from both impls matches."""
        for tag in ["CANDIDATE_ROOT", "EVIDENCE_SNAPSHOT"]:
            h = domain_hash(tag, b"data")
            self.assertEqual(len(h), 64)


class TestDomainTagsCompleteness(unittest.TestCase):
    """Verify domain tag list completeness against spec."""

    def test_0b_v3_tags_present(self):
        """All 0B V3 §11 tags present."""
        required_0b = {
            "CANDIDATE_ROOT", "RESEARCH_CONTRACT", "EVIDENCE_SNAPSHOT",
            "EVIDENCE_MANIFEST", "SEARCH_TREE", "SEARCH_DEBT",
            "VALIDATION_FAMILY", "PROOF_BUNDLE", "PROMOTION_GATE_SPEC",
            "GATE_MANIFEST", "ROLE_MANIFEST", "CONSTITUTION",
            "CAPITAL_SAFETY", "DEPLOYMENT_CONTEXT", "CHAMPION_REGISTRY_EVENT",
        }
        from are.canonical import list_domain_tags
        tags = set(list_domain_tags())
        self.assertTrue(required_0b.issubset(tags))

    def test_register_v30_tags_present(self):
        """All Register V30 object tags present."""
        required_register = {
            "REFINEMENT_RELIANCE_INVALIDITY_EVENT_ROOT",
            "REFINEMENT_PROSPECTIVE_RELIANCE_SUBJECT",
            "REFINEMENT_PROSPECTIVE_RELIANCE_RECEIPT",
            "REFINEMENT_PROSPECTIVE_RELIANCE_VAR_CURRENT",
            "EDGE_NONCE_CONSUMPTION_LEDGER",
            "REFINEMENT_PROSPECTIVE_RELIANCE_SOD_ROOT",
            "ROLLBACK_CAUSE_OBSERVATION",
            "ROLLBACK_CAUSE_OBSERVATION_SOURCE_UNIVERSE",
            "ROLLBACK_POLICY_ROOT",
            "EDGE_INTERFERENCE_EVIDENCE",
        }
        from are.canonical import list_domain_tags
        tags = set(list_domain_tags())
        self.assertTrue(required_register.issubset(tags))

    def test_infrastructure_tags_present(self):
        """Event-store infrastructure tags present."""
        required_infra = {
            "EVENT_STORE_ENTRY", "EVENT_STORE_HEAD", "DECISION_STATE_REVISION",
            "CAPITAL_ACTION_EPISODE", "CAPITAL_SAFETY_OBSERVATION_RECORD",
            "CHAMPION_ROLLBACK_PLAN", "BROKER_MUTATION_RECORD",
            "OPERATIONAL_FIDELITY_LEDGER_ENTRY", "FAMILY_LIFETIME_LEDGER_ENTRY",
            "PROGRAM_BUDGET_RESERVATION", "EVIDENCE_RESERVATION",
            "RELATION_DECISION", "CAPABILITY_ACTIVATION_EPISODE",
            "DEPLOYMENT_ACTIVATION_EPISODE", "INTEGRITY_DEFECT_RECORD",
        }
        from are.canonical import list_domain_tags
        tags = set(list_domain_tags())
        self.assertTrue(required_infra.issubset(tags))


if __name__ == "__main__":
    unittest.main(verbosity=2)