#!/usr/bin/env python3
"""
manifest_hash IMPL_A — normative root SHA-256
SPEC: root = SHA-256( concat( "<path>\\0<blob-sha>\\0<bytes>\\n" sorted lexicographically by path ) )

STATUS = TOOL CONTRACT / ZERO AUTHORITY / DUAL-IMPLEMENTATION REQUIRED
- stdlib only
- exit 0 sukses, exit 2 input tidak valid, exit 3 mismatch verifikasi (fail-closed)
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
    # read raw bytes first to detect BOM
    try:
        raw = open(manifest_path, "rb").read()
    except OSError as e:
        print(f"error: cannot read manifest: {e}", file=sys.stderr)
        sys.exit(2)
    if raw.startswith(b"\xef\xbb\xbf"):
        print("error: manifest has UTF-8 BOM (not allowed)", file=sys.stderr)
        sys.exit(3)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        print(f"error: manifest not valid UTF-8: {e}", file=sys.stderr)
        sys.exit(3)
    # CRLF check — manifest itself must use LF; if contains CRLF it's malformed
    if "\r" in text:
        # allow but treat as malformed -> fail-closed
        # spec: encoding UTF-8 tanpa BOM; newline literal \n
        # we consider CRLF as malformed input
        print("error: manifest contains CR (must use LF)", file=sys.stderr)
        sys.exit(3)

    members = []
    seen_paths = set()
    lines = text.splitlines()
    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        # split by '|'
        parts = line.split("|")
        # expected: ['', ' `path` ', ' sha ', ' bytes ', '']
        if len(parts) < 4:
            continue
        # parts[1] is path column, parts[2] sha, parts[3] bytes
        path_col = parts[1].strip()
        sha_col = parts[2].strip()
        bytes_col = parts[3].strip()
        # header / separator detection
        if path_col.lower() == "path" and sha_col.lower().startswith("git"):
            continue
        if path_col.startswith("---") or sha_col.startswith("---"):
            continue
        # path must be inside backticks per spec example
        if path_col.startswith("`") and path_col.endswith("`"):
            path = path_col[1:-1].strip()
        else:
            # if not in backticks, try to use raw but trim
            # if it looks like a path, keep it; otherwise skip
            # fail-closed if line looks like member but malformed
            if "`" in line:
                # line contains backtick but not properly wrapped -> malformed
                print(f"error: malformed member at line {idx}: {line}", file=sys.stderr)
                sys.exit(3)
            continue
        sha = sha_col
        bytes_str = bytes_col
        # skip empty
        if not path:
            continue
        # validate sha: 40 hex lowercase or SELF, bytes digits
        is_sha_valid = (sha == "SELF") or (len(sha) == 40 and all(c in "0123456789abcdef" for c in sha.lower()) and sha == sha.lower())
        # sha must be lowercase if not SELF (spec says lowercase 40-hex)
        if not is_sha_valid:
            # check if sha looks like header then skip, else malformed
            if sha.lower() == "git blob sha-1":
                continue
            print(f"error: malformed blob sha at line {idx}: {sha}", file=sys.stderr)
            sys.exit(3)
        if not bytes_str.isdigit():
            # bytes column must be integer
            # if it's header skip
            if bytes_str.lower().startswith("utf"):
                continue
            print(f"error: malformed bytes at line {idx}: {bytes_str}", file=sys.stderr)
            sys.exit(3)
        # check no NUL in path
        if "\0" in path:
            print(f"error: path contains NUL at line {idx}", file=sys.stderr)
            sys.exit(3)
        # duplicate
        if path in seen_paths:
            print(f"error: duplicate path: {path}", file=sys.stderr)
            sys.exit(3)
        seen_paths.add(path)
        # validate byte length non-negative, already digits
        members.append((path, sha, bytes_str))
    if not members:
        print("error: no members found in manifest", file=sys.stderr)
        sys.exit(3)
    return members


def _verify_worktree(members, manifest_path: str, worktree: str | None):
    if worktree is None:
        return
    if not os.path.isdir(worktree):
        print(f"error: worktree not a directory: {worktree}", file=sys.stderr)
        sys.exit(2)
    # for SELF entries, actual bytes is manifest file size
    try:
        manifest_bytes_len = os.path.getsize(manifest_path)
    except OSError:
        manifest_bytes_len = None

    for path, sha, bytes_str in members:
        expected_len = int(bytes_str)
        if sha == "SELF":
            if manifest_bytes_len is None:
                print(f"error: cannot stat manifest for SELF check: {path}", file=sys.stderr)
                sys.exit(3)
            if expected_len != manifest_bytes_len:
                print(f"error: SELF byte length mismatch for {path}: expected {expected_len} actual {manifest_bytes_len}", file=sys.stderr)
                sys.exit(3)
            # also verify that the path file exists at worktree/path and its content length matches?
            # but SELF path should be manifest itself; verify if exists
            # we already checked length via manifest file, not worktree copy
            # additionally if worktree contains that path, verify it matches manifest file content
            full_self = os.path.join(worktree, *path.split("/"))
            full_self = os.path.abspath(full_self)
            if not full_self.startswith(os.path.abspath(worktree) + os.sep):
                print(f"error: path traversal detected: {path}", file=sys.stderr)
                sys.exit(3)
            if os.path.isfile(full_self):
                try:
                    data = open(full_self, "rb").read()
                except OSError as e:
                    print(f"error: cannot read SELF file {path}: {e}", file=sys.stderr)
                    sys.exit(3)
                if len(data) != expected_len:
                    print(f"error: SELF file length mismatch {path}: expected {expected_len} actual {len(data)}", file=sys.stderr)
                    sys.exit(3)
                # no sha check for SELF (literal)
            continue
        full = os.path.join(worktree, *path.split("/"))
        full = os.path.abspath(full)
        if not full.startswith(os.path.abspath(worktree) + os.sep):
            print(f"error: path traversal detected: {path}", file=sys.stderr)
            sys.exit(3)
        if not os.path.isfile(full):
            print(f"error: missing file in worktree: {path}", file=sys.stderr)
            sys.exit(3)
        try:
            data = open(full, "rb").read()
        except OSError as e:
            print(f"error: cannot read file {path}: {e}", file=sys.stderr)
            sys.exit(3)
        actual_len = len(data)
        if actual_len != expected_len:
            print(f"error: byte length mismatch for {path}: expected {expected_len} actual {actual_len}", file=sys.stderr)
            sys.exit(3)
        actual_sha = _blob_sha1(data)
        if actual_sha != sha:
            print(f"error: blob sha mismatch for {path}: expected {sha} actual {actual_sha}", file=sys.stderr)
            sys.exit(3)


def main() -> None:
    parser = argparse.ArgumentParser(description="manifest_hash normative root")
    parser.add_argument("--manifest", required=True, help="file manifest")
    parser.add_argument("--worktree", required=False, default=None, help="root working tree (optional)")
    args = parser.parse_args()

    manifest_path = args.manifest
    worktree = args.worktree

    if not os.path.isfile(manifest_path):
        print(f"error: manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(2)

    members = _parse_manifest(manifest_path)
    _verify_worktree(members, manifest_path, worktree)

    # sort lexicographically byte-wise by path
    sorted_members = sorted(members, key=lambda x: x[0].encode("utf-8"))

    # build concatenated bytes: "<path>\\0<sha>\\0<bytes>\\n"
    out = bytearray()
    for path, sha, bytes_str in sorted_members:
        tup = f"{path}\0{sha}\0{bytes_str}\n".encode("utf-8")
        out.extend(tup)

    root_hex = hashlib.sha256(bytes(out)).hexdigest()

    # output: root hex + jumlah member + status baris
    # format identical to IMPL_B
    sys.stdout.write(f"{root_hex}\n")
    sys.stdout.write(f"members: {len(sorted_members)}\n")
    sys.stdout.write(f"status: OK\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
