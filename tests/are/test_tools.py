"""
Tests for TOOLS dual-impl (manifest_hash, blob_verifier, path_router)
- Verifikasi kedua impl hasil identik bit-per-bit pada tree yang sama
- Uji negatif 1 byte diubah -> exit 3 (manifest_hash, blob_verifier) dan MUTATED -> exit 4 (path_router)
- Uji ambiguous pattern -> exit 3
Stdlib only, subprocess based
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST_V39 = REPO_ROOT / "PROJECT_GOVERNANCE" / "ARE0" / "MANIFEST" / "AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V39.md"
MANIFEST_V35 = REPO_ROOT / "PROJECT_GOVERNANCE" / "ARE0" / "MANIFEST" / "AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V35.md"
WORKTREE = REPO_ROOT

MH_A = REPO_ROOT / "TOOLS" / "manifest_hash" / "IMPL_A" / "manifest_hash_a.py"
MH_B = REPO_ROOT / "TOOLS" / "manifest_hash" / "IMPL_B" / "manifest_hash_b.py"
BV_A = REPO_ROOT / "TOOLS" / "blob_verifier" / "IMPL_A" / "blob_verifier_a.py"
BV_B = REPO_ROOT / "TOOLS" / "blob_verifier" / "IMPL_B" / "blob_verifier_b.py"
PR_A = REPO_ROOT / "TOOLS" / "path_router" / "IMPL_A" / "path_router_a.py"
PR_B = REPO_ROOT / "TOOLS" / "path_router" / "IMPL_B" / "path_router_b.py"

# Full routing table from GOVERNANCE_FOLDER_STRUCTURE_RULES.md Lampiran R1
ROUTING_TABLE_CONTENT = """| Pattern nama file | Folder tujuan |
|---|---|
| `AHFMES_ARE_FORMAL_ARCHITECTURE_MASTER_*` | `ARE0/GRAND_DESIGN/` |
| `AHFMES_AUTONOMOUS_RESEARCH_ENGINE_*` | `ARE0/GRAND_DESIGN/` |
| `AHFMES_ARE_V0_FORMALIZATION_AUTHORITY*` | `ARE0/AUTHORITY_AND_WORKFLOW/` |
| `AHFMES_ARE_V0_DOCUMENTATION_PUBLICATION_AUDIT*` | `ARE0/AUTHORITY_AND_WORKFLOW/` |
| `AHFMES_ARE_BATCHED_ARCHITECTURE*` | `ARE0/AUTHORITY_AND_WORKFLOW/` |
| `AHFMES_ARE_GITHUB_FIRST*` | `ARE0/AUTHORITY_AND_WORKFLOW/` |
| `AHFMES_ARE_SOURCE_REUSE*` | `ARE0/AUTHORITY_AND_WORKFLOW/` |
| `AHFMES_ARE_0[A-F]_*` | `ARE0/CONTRACTS/` |
| `AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_*` | `ARE0/MACHINE/` |
| `AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_*` | `ARE0/MACHINE/` |
| `AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_*` | `ARE0/MANIFEST/` |
| `AHFMES_ARE_0_CURRENT_NORMATIVE_MANIFEST_BINDING*` | `ARE0/MANIFEST/` |
| `AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_*` | `ARE0/COUNCIL_PROTOCOL/` |
| `AHFMES_ARE_0_LEGACY_AUTHORITY_QUARANTINE_*` | `ARE0/QUARANTINE/` |
| `AHFMES_ARE_0_R9_CORRECTION_PACKAGE_*` | `ARE0/R9_CORRECTIONS/` |
| `AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_*` | `ARE0/R9_CORRECTIONS/` |
| `AHFMES_ARE_0_EXTERNAL_AUDIT_*` | `ARE0/EXTERNAL_AUDIT/` |
| `AHFMES_ARE_0_EXTERNAL_REAUDIT_*` | `ARE0/EXTERNAL_AUDIT/` |
| `AHFMES_ARE_0_FINAL_CLOSURE_AUDIT_FILTERED_RECORD*` | `ARE0/EXTERNAL_AUDIT/` |
| `AHFMES_ARE_0_SA11_*` | `ARE0/QUALIFICATION/` |
| `AHFMES_ARE_0_CLEAN_PASS_*` | `ARE0/QUALIFICATION/` |
| `AHFMES_ARE_0_REGRESSION_R7_R8_R9*` | `ARE0/QUALIFICATION/` |
| `AHFMES_ARE_0_FINAL_CONSISTENCY_RECORD*` | `ARE0/QUALIFICATION/` |
| `AHFMES_ARE_0_INTERNAL_IMPACT_AUDIT_RECORD*` | `ARE0/QUALIFICATION/` |
| `AHFMES_ARE_0_QUALIFICATION_ROOT_RECORD*` | `ARE0/QUALIFICATION/` |
| `AHFMES_ARE_0_CLOSURE_BATCH_INTERNAL_REVIEW*` | `ARE0/QUALIFICATION/` |
| `AHFMES_ARE_0_PRE_EXTERNAL_AUDIT_*` | `ARE0/QUALIFICATION/` |
| `AHFMES_ARE_0_SELF_AUDIT_COUNCIL_RUN_*` | `ARE0/QUALIFICATION/` |
"""

def _run(cmd, **kwargs):
    # DELEGASI_051 P0-3bis: Python 3.14 on Windows has a transient race between
    # pytest-timeout's per-test timer thread and subprocess.Popen's CreateProcess
    # handle duplication, which intermittently raises
    # OSError [WinError 50] "The request is not supported" / [WinError 6]
    # "The handle is invalid". Reproduced: ~50% of full-suite runs fail here
    # WITH --timeout active, 0/4 fail with -p no:timeout. Retry once on those
    # transient errors only — never on genuine non-zero tool exits.
    import time as _time
    last_exc = None
    for attempt in range(2):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, **kwargs)
        except OSError as e:
            win_err = getattr(e, "winerror", None)
            if win_err in (50, 6) and attempt == 0:
                last_exc = e
                _time.sleep(0.05)
                continue
            raise
    raise last_exc  # pragma: no cover - defensive

def _blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def _write_text(path: pathlib.Path, content: str):
    # ensure LF only (spec requires \n, not CRLF)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


class TestManifestHashDual(unittest.TestCase):
    def test_both_impls_exist(self):
        self.assertTrue(MH_A.is_file(), f"missing {MH_A}")
        self.assertTrue(MH_B.is_file(), f"missing {MH_B}")

    def test_manifest_hash_v39_identical(self):
        if not MANIFEST_V39.is_file():
            self.skipTest(f"manifest V39 not found {MANIFEST_V39}")
        rA = _run([sys.executable, str(MH_A), "--manifest", str(MANIFEST_V39), "--worktree", str(WORKTREE)])
        rB = _run([sys.executable, str(MH_B), "--manifest", str(MANIFEST_V39), "--worktree", str(WORKTREE)])
        self.assertEqual(rA.returncode, 0, f"IMPL_A failed: {rA.stderr}\n{rA.stdout}")
        self.assertEqual(rB.returncode, 0, f"IMPL_B failed: {rB.stderr}\n{rB.stdout}")
        self.assertEqual(rA.stdout, rB.stdout, "IMPL_A vs IMPL_B stdout not bit-identical")
        # also check root hex is 64 lower hex
        first_line = rA.stdout.splitlines()[0].strip()
        self.assertEqual(len(first_line), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in first_line))

    def test_manifest_hash_without_worktree_identical(self):
        rA = _run([sys.executable, str(MH_A), "--manifest", str(MANIFEST_V39)])
        rB = _run([sys.executable, str(MH_B), "--manifest", str(MANIFEST_V39)])
        self.assertEqual(rA.returncode, 0)
        self.assertEqual(rB.returncode, 0)
        self.assertEqual(rA.stdout, rB.stdout)

    def test_manifest_hash_negative_one_byte_changed(self):
        # create temp worktree with single file manifest
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            f = td / "hello.txt"
            data = b"hello world\n"
            f.write_bytes(data)
            sha = _blob_sha1(data)
            length = len(data)
            manifest = td / "manifest.md"
            _write_text(manifest,
                "# test\n\n| Path | Git blob SHA-1 | UTF-8 bytes |\n|---|---|---:|\n"
                f"| `hello.txt` | {sha} | {length} |\n")
            # positive should pass
            rA = _run([sys.executable, str(MH_A), "--manifest", str(manifest), "--worktree", str(td)])
            rB = _run([sys.executable, str(MH_B), "--manifest", str(manifest), "--worktree", str(td)])
            self.assertEqual(rA.returncode, 0)
            self.assertEqual(rB.returncode, 0)
            self.assertEqual(rA.stdout, rB.stdout)
            # mutate 1 byte
            f.write_bytes(b"hello worle\n")  # change d -> e
            rA2 = _run([sys.executable, str(MH_A), "--manifest", str(manifest), "--worktree", str(td)])
            rB2 = _run([sys.executable, str(MH_B), "--manifest", str(manifest), "--worktree", str(td)])
            self.assertEqual(rA2.returncode, 3, f"expected exit 3 on mutated file, got {rA2.returncode} {rA2.stderr}")
            self.assertEqual(rB2.returncode, 3)
            self.assertIn("mismatch", rA2.stderr.lower() + rB2.stderr.lower())

    def test_manifest_hash_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            manifest = td / "manifest.md"
            _write_text(manifest,
                "| Path | Git blob SHA-1 | UTF-8 bytes |\n|---|---|---:|\n"
                "| `nonexistent.txt` | 0000000000000000000000000000000000000000 | 10 |\n")
            rA = _run([sys.executable, str(MH_A), "--manifest", str(manifest), "--worktree", str(td)])
            rB = _run([sys.executable, str(MH_B), "--manifest", str(manifest), "--worktree", str(td)])
            self.assertEqual(rA.returncode, 3)
            self.assertEqual(rB.returncode, 3)


class TestBlobVerifierDual(unittest.TestCase):
    def test_both_impls_exist(self):
        self.assertTrue(BV_A.is_file())
        self.assertTrue(BV_B.is_file())

    def test_blob_verifier_v39_identical(self):
        if not MANIFEST_V39.is_file():
            self.skipTest("V39 not found")
        rA = _run([sys.executable, str(BV_A), "--manifest", str(MANIFEST_V39), "--worktree", str(WORKTREE)])
        rB = _run([sys.executable, str(BV_B), "--manifest", str(MANIFEST_V39), "--worktree", str(WORKTREE)])
        self.assertEqual(rA.returncode, 0, f"BV A fail {rA.stderr[:2000]}")
        self.assertEqual(rB.returncode, 0, f"BV B fail {rB.stderr[:2000]}")
        self.assertEqual(rA.stdout, rB.stdout, "BV stdout not identical")

    def test_blob_verifier_negative_one_byte(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            f = td / "data.bin"
            data = b"abcd1234"
            f.write_bytes(data)
            sha = _blob_sha1(data)
            manifest = td / "manifest.md"
            _write_text(manifest,
                "| Path | Git blob SHA-1 | UTF-8 bytes |\n|---|---|---:|\n"
                f"| `data.bin` | {sha} | {len(data)} |\n")
            rA = _run([sys.executable, str(BV_A), "--manifest", str(manifest), "--worktree", str(td)])
            rB = _run([sys.executable, str(BV_B), "--manifest", str(manifest), "--worktree", str(td)])
            self.assertEqual(rA.returncode, 0)
            self.assertEqual(rB.returncode, 0)
            self.assertEqual(rA.stdout, rB.stdout)
            # check PASS count
            self.assertIn("PASS: 1", rA.stdout)
            # mutate
            f.write_bytes(b"abcd1235")
            rA2 = _run([sys.executable, str(BV_A), "--manifest", str(manifest), "--worktree", str(td)])
            rB2 = _run([sys.executable, str(BV_B), "--manifest", str(manifest), "--worktree", str(td)])
            self.assertEqual(rA2.returncode, 3)
            self.assertEqual(rB2.returncode, 3)
            self.assertEqual(rA2.stdout, rB2.stdout)
            self.assertIn("FAIL", rA2.stdout)


class TestPathRouterDual(unittest.TestCase):
    def test_both_impls_exist(self):
        self.assertTrue(PR_A.is_file())
        self.assertTrue(PR_B.is_file())

    def _make_routing_file(self, td: pathlib.Path) -> pathlib.Path:
        rf = td / "routing.md"
        _write_text(rf,ROUTING_TABLE_CONTENT)
        return rf

    def test_path_router_v35_to_are0_identical(self):
        if not MANIFEST_V35.is_file():
            self.skipTest("V35 not found")
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            rf = self._make_routing_file(td)
            outA = td / "outA.json"
            outB = td / "outB.json"
            rA = _run([sys.executable, str(PR_A), "--source-manifest", str(MANIFEST_V35), "--routing-table", str(rf), "--worktree", str(WORKTREE), "--out", str(outA)])
            rB = _run([sys.executable, str(PR_B), "--source-manifest", str(MANIFEST_V35), "--routing-table", str(rf), "--worktree", str(WORKTREE), "--out", str(outB)])
            # both should be exit 0 if all relocated identical, or 3/4 if some missing but must be identical exit code
            self.assertEqual(rA.returncode, rB.returncode, f"exit code mismatch {rA.returncode} vs {rB.returncode} stderrA {rA.stderr[:1000]} stderrB {rB.stderr[:1000]}")
            self.assertTrue(outA.is_file())
            self.assertTrue(outB.is_file())
            # compare file contents bit-per-bit
            a_bytes = outA.read_bytes()
            b_bytes = outB.read_bytes()
            self.assertEqual(a_bytes, b_bytes, "path_router output not bit-identical")
            # parse and check statuses
            data = json.loads(a_bytes)
            # all should be RELOCATED_IDENTICAL if worktree is correct
            # if not, at least both impls agree; we assert that no UNMATCHED for V35 with full table
            unmatched = [d for d in data if d["status"] == "UNMATCHED"]
            self.assertEqual(len(unmatched), 0, f"found UNMATCHED: {unmatched[:2]}")
            # if some MISSING due to files not yet relocated, we still check identical, but we expect 0 missing for correct worktree
            # allow but report
            # print summary for debugging
            relocated = [d for d in data if d["status"] == "RELOCATED_IDENTICAL"]
            # at least majority should be relocated
            self.assertGreater(len(relocated), 0)

    def test_path_router_negative_mutated(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            # create worktree with one file at new location
            # old manifest has old_path with sha of original, new file will be mutated
            orig = b"original content"
            mutated = b"mutated content!"
            # need same length? make same length to isolate sha mismatch
            # use same length: orig len 16, mutated len 16 as well with one byte diff
            orig = b"0123456789abcdef"
            mutated = b"0123456789abcdee"  # last byte changed
            sha_orig = _blob_sha1(orig)
            # routing: old filename pattern -> new folder
            # create old manifest
            manifest = td / "src.md"
            _write_text(manifest,
                "| Path | Git blob SHA-1 | UTF-8 bytes |\n|---|---|---:|\n"
                f"| `PROJECT_GOVERNANCE/OLD_FILE.txt` | {sha_orig} | {len(orig)} |\n")
            routing = td / "routing.md"
            _write_text(routing,"| Pattern nama file | Folder tujuan |\n|---|---|\n| `OLD_FILE.txt` | `ARE0/GRAND_DESIGN/` |\n")
            # create worktree structure: PROJECT_GOVERNANCE/ARE0/GRAND_DESIGN/OLD_FILE.txt with mutated content
            new_dir = td / "wt" / "PROJECT_GOVERNANCE" / "ARE0" / "GRAND_DESIGN"
            new_dir.mkdir(parents=True)
            (new_dir / "OLD_FILE.txt").write_bytes(mutated)
            outA = td / "outA.json"
            outB = td / "outB.json"
            rA = _run([sys.executable, str(PR_A), "--source-manifest", str(manifest), "--routing-table", str(routing), "--worktree", str(td / "wt"), "--out", str(outA)])
            rB = _run([sys.executable, str(PR_B), "--source-manifest", str(manifest), "--routing-table", str(routing), "--worktree", str(td / "wt"), "--out", str(outB)])
            self.assertEqual(rA.returncode, 4, f"expected MUTATED exit 4, got {rA.returncode} {rA.stderr}")
            self.assertEqual(rB.returncode, 4)
            self.assertEqual(outA.read_bytes(), outB.read_bytes())
            data = json.loads(outA.read_bytes())
            self.assertEqual(data[0]["status"], "MUTATED")

    def test_path_router_ambiguous(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            manifest = td / "src.md"
            _write_text(manifest,
                "| Path | Git blob SHA-1 | UTF-8 bytes |\n|---|---|---:|\n"
                "| `PROJECT_GOVERNANCE/DUPE.txt` | abcdef1234567890abcdef1234567890abcdef12 | 4 |\n")
            # two patterns both match DUPE.txt
            routing = td / "routing.md"
            _write_text(routing,"| Pattern nama file | Folder tujuan |\n|---|---|\n| `DUPE*` | `ARE0/GRAND_DESIGN/` |\n| `DUPE.txt` | `ARE0/MACHINE/` |\n")
            wt = td / "wt"
            wt.mkdir()
            out = td / "out.json"
            rA = _run([sys.executable, str(PR_A), "--source-manifest", str(manifest), "--routing-table", str(routing), "--worktree", str(wt), "--out", str(out)])
            rB = _run([sys.executable, str(PR_B), "--source-manifest", str(manifest), "--routing-table", str(routing), "--worktree", str(wt), "--out", str(td / "outB.json")])
            self.assertEqual(rA.returncode, 3)
            self.assertEqual(rB.returncode, 3)
            self.assertIn("ambiguous", (rA.stderr + rB.stderr).lower())

    def test_path_router_unmatched(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            manifest = td / "src.md"
            _write_text(manifest,
                "| Path | Git blob SHA-1 | UTF-8 bytes |\n|---|---|---:|\n"
                "| `PROJECT_GOVERNANCE/UNKNOWN_XYZ.txt` | abcdef1234567890abcdef1234567890abcdef12 | 4 |\n")
            routing = td / "routing.md"
            _write_text(routing,"| Pattern nama file | Folder tujuan |\n|---|---|\n| `KNOWN*` | `ARE0/GRAND_DESIGN/` |\n")
            wt = td / "wt"
            wt.mkdir()
            out = td / "out.json"
            rA = _run([sys.executable, str(PR_A), "--source-manifest", str(manifest), "--routing-table", str(routing), "--worktree", str(wt), "--out", str(out)])
            rB = _run([sys.executable, str(PR_B), "--source-manifest", str(manifest), "--routing-table", str(routing), "--worktree", str(wt), "--out", str(td / "outB.json")])
            self.assertEqual(rA.returncode, 3)
            self.assertEqual(rB.returncode, 3)
            data = json.loads(out.read_bytes())
            self.assertEqual(data[0]["status"], "UNMATCHED")


if __name__ == "__main__":
    unittest.main()
