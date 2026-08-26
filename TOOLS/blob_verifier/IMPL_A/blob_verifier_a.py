#!/usr/bin/env python3
"""
blob_verifier IMPL_A — cocokkan blob SHA-1 + byte length manifest vs worktree
- stdlib only
- exit 0 semua PASS, exit 3 minimal satu FAIL atau manifest tak terbaca
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys


def _blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def _parse_manifest(manifest_path: str):
    try:
        raw = open(manifest_path, "rb").read()
    except OSError as e:
        print(f"error: cannot read manifest: {e}", file=sys.stderr)
        sys.exit(3)
    if raw.startswith(b"\xef\xbb\xbf"):
        print("error: manifest has BOM", file=sys.stderr)
        sys.exit(3)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        print(f"error: manifest not utf-8: {e}", file=sys.stderr)
        sys.exit(3)
    if "\r" in text:
        print("error: manifest contains CR", file=sys.stderr)
        sys.exit(3)
    members = []
    seen = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        parts = line.split("|")
        if len(parts) < 4:
            continue
        path_col = parts[1].strip()
        sha_col = parts[2].strip()
        bytes_col = parts[3].strip()
        if path_col.lower() == "path" and sha_col.lower().startswith("git"):
            continue
        if path_col.startswith("---"):
            continue
        if path_col.startswith("`") and path_col.endswith("`"):
            path = path_col[1:-1].strip()
        else:
            if "`" in line:
                print(f"error: malformed member: {line}", file=sys.stderr)
                sys.exit(3)
            continue
        sha = sha_col
        bstr = bytes_col
        is_valid = (sha == "SELF") or (len(sha) == 40 and all(c in "0123456789abcdef" for c in sha.lower()) and sha == sha.lower())
        if not is_valid:
            if sha.lower().startswith("git"):
                continue
            print(f"error: malformed sha: {sha}", file=sys.stderr)
            sys.exit(3)
        if not bstr.isdigit():
            if bstr.lower().startswith("utf"):
                continue
            print(f"error: malformed bytes: {bstr}", file=sys.stderr)
            sys.exit(3)
        if "\0" in path:
            print(f"error: NUL in path: {path}", file=sys.stderr)
            sys.exit(3)
        if path in seen:
            print(f"error: duplicate path: {path}", file=sys.stderr)
            sys.exit(3)
        seen.add(path)
        members.append((path, sha, bstr))
    if not members:
        print("error: no members in manifest", file=sys.stderr)
        sys.exit(3)
    return members


def main():
    parser = argparse.ArgumentParser(description="blob_verifier")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--git-dir", required=False, default=None)
    args = parser.parse_args()

    manifest_path = args.manifest
    worktree = args.worktree
    # git_dir optional, ignored for stdlib but validated
    git_dir = args.git_dir

    if not os.path.isfile(manifest_path):
        print(f"error: manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(3)
    if not os.path.isdir(worktree):
        print(f"error: worktree not a directory: {worktree}", file=sys.stderr)
        sys.exit(3)
    if git_dir is not None and not os.path.isdir(git_dir):
        print(f"error: git-dir not a directory: {git_dir}", file=sys.stderr)
        sys.exit(3)

    members = _parse_manifest(manifest_path)
    # manifest file size for SELF
    try:
        manifest_len = os.path.getsize(manifest_path)
    except OSError:
        manifest_len = None

    # sort lexicographically byte-wise
    sorted_members = sorted(members, key=lambda x: x[0].encode("utf-8"))

    rows = []
    pass_cnt = 0
    fail_cnt = 0

    for path, expected_sha, bstr in sorted_members:
        expected_len = int(bstr)
        full = os.path.join(worktree, *path.split("/"))
        actual_sha = ""
        actual_bytes_str = ""
        status = "FAIL"
        # SELF handling
        if expected_sha == "SELF":
            # check existence
            if not os.path.isfile(full):
                # fallback to manifest file itself if path equals manifest relative path?
                # try manifest_path file
                if manifest_len is not None and expected_len == manifest_len:
                    actual_sha = "SELF"
                    actual_bytes_str = str(manifest_len)
                    status = "OK"
                    pass_cnt += 1
                else:
                    actual_sha = "MISSING"
                    actual_bytes_str = "MISSING"
                    status = "FAIL"
                    fail_cnt += 1
                rows.append((path, expected_sha, actual_sha, actual_bytes_str, status))
                continue
            try:
                data = open(full, "rb").read()
                actual_len = len(data)
                actual_bytes_str = str(actual_len)
                if actual_len == expected_len:
                    actual_sha = "SELF"
                    status = "OK"
                    pass_cnt += 1
                else:
                    actual_sha = "SELF"
                    status = "FAIL"
                    fail_cnt += 1
            except OSError:
                actual_sha = "UNREADABLE"
                actual_bytes_str = "UNREADABLE"
                status = "FAIL"
                fail_cnt += 1
            rows.append((path, expected_sha, actual_sha, actual_bytes_str, status))
            continue

        # non-SELF
        if not os.path.isfile(full):
            actual_sha = "MISSING"
            actual_bytes_str = "MISSING"
            status = "FAIL"
            fail_cnt += 1
            rows.append((path, expected_sha, actual_sha, actual_bytes_str, status))
            continue
        try:
            data = open(full, "rb").read()
        except OSError:
            actual_sha = "UNREADABLE"
            actual_bytes_str = "UNREADABLE"
            status = "FAIL"
            fail_cnt += 1
            rows.append((path, expected_sha, actual_sha, actual_bytes_str, status))
            continue
        actual_len = len(data)
        actual_bytes_str = str(actual_len)
        actual_sha = _blob_sha1(data)
        if actual_len != expected_len or actual_sha != expected_sha:
            status = "FAIL"
            fail_cnt += 1
        else:
            status = "OK"
            pass_cnt += 1
        rows.append((path, expected_sha, actual_sha, actual_bytes_str, status))

    # output table per anggota: PATH | EXPECTED_SHA | ACTUAL_SHA | BYTES | OK/FAIL
    # deterministic header
    out_lines = []
    out_lines.append("PATH | EXPECTED_SHA | ACTUAL_SHA | BYTES | STATUS")
    for path, exp, act, bstr, st in rows:
        out_lines.append(f"{path} | {exp} | {act} | {bstr} | {st}")
    out_lines.append(f"TOTAL: {len(rows)}")
    out_lines.append(f"PASS: {pass_cnt}")
    out_lines.append(f"FAIL: {fail_cnt}")
    sys.stdout.write("\n".join(out_lines) + "\n")
    if fail_cnt > 0:
        sys.exit(3)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
