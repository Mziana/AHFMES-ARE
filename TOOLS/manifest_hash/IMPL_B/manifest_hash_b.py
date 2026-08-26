#!/usr/bin/env python3
"""
manifest_hash IMPL_B — normative root SHA-256 (alternative code path)
Same contract as IMPL_A but via different implementation style.
"""
from __future__ import annotations

import hashlib
import os
import sys


def _blob_sha1_bytes(data: bytes) -> str:
    h = hashlib.sha1()
    header = ("blob %d\0" % len(data)).encode("utf-8")
    h.update(header)
    h.update(data)
    return h.hexdigest()


def _die(code: int, msg: str):
    print(msg, file=sys.stderr)
    sys.exit(code)


def _parse_manifest_b(manifest_path: str):
    try:
        f = open(manifest_path, "rb")
        raw = f.read()
        f.close()
    except OSError as e:
        _die(2, f"error: cannot read manifest: {e}")
    if raw[:3] == b"\xef\xbb\xbf":
        _die(3, "error: manifest has UTF-8 BOM (not allowed)")
    try:
        txt = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        _die(3, f"error: manifest not valid UTF-8: {e}")
    if "\r" in txt:
        _die(3, "error: manifest contains CR (must use LF)")
    members = []
    seen = set()
    # manual line split without str.splitlines to differ from IMPL_A
    start = 0
    line_no = 0
    # iterate using while to differ code path
    while True:
        nl = txt.find("\n", start)
        if nl == -1:
            line = txt[start:]
            ended = True
        else:
            line = txt[start:nl]
            ended = False
        line_no += 1
        # process line
        s = line.strip()
        if s.startswith("|"):
            # find '|' positions
            # need at least 4 pipes for 3 columns
            # use split manually
            # count pipes
            if line.count("|") >= 3:
                # extract columns between pipes
                # we locate first and last pipe
                # simpler: split
                cols = []
                # manual split by '|'
                cur = ""
                for ch in line:
                    if ch == "|":
                        cols.append(cur)
                        cur = ""
                    else:
                        cur += ch
                cols.append(cur)
                # cols[0] before first |, cols[1] path, cols[2] sha, cols[3] bytes
                if len(cols) >= 4:
                    path_col = cols[1].strip()
                    sha_col = cols[2].strip()
                    bytes_col = cols[3].strip()
                    # header detection
                    if path_col.lower() == "path" and "git" in sha_col.lower():
                        pass
                    elif path_col.startswith("---"):
                        pass
                    else:
                        if path_col.startswith("`") and path_col.endswith("`"):
                            p = path_col[1:-1].strip()
                        else:
                            if "`" in line:
                                _die(3, f"error: malformed member at line {line_no}: {line}")
                            else:
                                p = None
                        if p is not None:
                            if p == "":
                                pass
                            else:
                                sha = sha_col
                                bstr = bytes_col
                                # validate sha
                                ok = False
                                if sha == "SELF":
                                    ok = True
                                elif len(sha) == 40:
                                    ok = True
                                    for c in sha:
                                        if c not in "0123456789abcdef":
                                            ok = False
                                            break
                                    if sha != sha.lower():
                                        ok = False
                                if not ok:
                                    if sha.lower().startswith("git") or sha == "":
                                        pass
                                    else:
                                        _die(3, f"error: malformed blob sha at line {line_no}: {sha}")
                                else:
                                    if not bstr.isdigit():
                                        if bstr.lower().startswith("utf"):
                                            pass
                                        else:
                                            _die(3, f"error: malformed bytes at line {line_no}: {bstr}")
                                    else:
                                        if "\0" in p:
                                            _die(3, f"error: path contains NUL at line {line_no}")
                                        if p in seen:
                                            _die(3, f"error: duplicate path: {p}")
                                        seen.add(p)
                                        members.append((p, sha, bstr))
        if ended:
            break
        start = nl + 1
        if start > len(txt):
            break
    if len(members) == 0:
        _die(3, "error: no members found in manifest")
    return members


def _verify_b(members, manifest_path: str, worktree: str | None):
    if worktree is None:
        return
    if not os.path.isdir(worktree):
        _die(2, f"error: worktree not a directory: {worktree}")
    try:
        m_len = os.path.getsize(manifest_path)
    except OSError:
        m_len = None
    for path, sha, bstr in members:
        exp_len = int(bstr)
        if sha == "SELF":
            if m_len is None:
                _die(3, f"error: cannot stat manifest for SELF check: {path}")
            if exp_len != m_len:
                _die(3, f"error: SELF byte length mismatch for {path}: expected {exp_len} actual {m_len}")
            full_self = os.path.join(worktree, *path.split("/"))
            if os.path.isfile(full_self):
                try:
                    data = open(full_self, "rb").read()
                except OSError as e:
                    _die(3, f"error: cannot read SELF file {path}: {e}")
                if len(data) != exp_len:
                    _die(3, f"error: SELF file length mismatch {path}: expected {exp_len} actual {len(data)}")
            continue
        full = os.path.join(worktree, *path.split("/"))
        if not os.path.isfile(full):
            _die(3, f"error: missing file in worktree: {path}")
        try:
            data = open(full, "rb").read()
        except OSError as e:
            _die(3, f"error: cannot read file {path}: {e}")
        actual_len = len(data)
        if actual_len != exp_len:
            _die(3, f"error: byte length mismatch for {path}: expected {exp_len} actual {actual_len}")
        actual_sha = _blob_sha1_bytes(data)
        if actual_sha != sha:
            _die(3, f"error: blob sha mismatch for {path}: expected {sha} actual {actual_sha}")


def main():
    # manual arg parsing instead of argparse
    argv = sys.argv[1:]
    manifest = None
    worktree = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--manifest":
            if i + 1 >= len(argv):
                _die(2, "error: --manifest requires value")
            manifest = argv[i + 1]
            i += 2
        elif a.startswith("--manifest="):
            manifest = a.split("=", 1)[1]
            i += 1
        elif a == "--worktree":
            if i + 1 >= len(argv):
                _die(2, "error: --worktree requires value")
            worktree = argv[i + 1]
            i += 2
        elif a.startswith("--worktree="):
            worktree = a.split("=", 1)[1]
            i += 1
        elif a in ("-h", "--help"):
            print("usage: manifest_hash_b.py --manifest <file> [--worktree <dir>]", file=sys.stderr)
            sys.exit(2)
        else:
            _die(2, f"error: unknown argument: {a}")
    if manifest is None:
        _die(2, "error: --manifest is required")
    if not os.path.isfile(manifest):
        _die(2, f"error: manifest not found: {manifest}")

    members = _parse_manifest_b(manifest)
    _verify_b(members, manifest, worktree)

    # sort byte-wise
    # use key = bytes to ensure same as IMPL_A
    sorted_members = sorted(members, key=lambda t: t[0].encode("utf-8"))
    # build concatenated via incremental sha256 to differ but same result
    h = hashlib.sha256()
    for path, sha, bstr in sorted_members:
        # encode each tuple exactly as "<path>\0<sha>\0<bstr>\n"
        # do manual byte building
        pb = path.encode("utf-8")
        sb = sha.encode("utf-8")
        bb = bstr.encode("utf-8")
        h.update(pb)
        h.update(b"\x00")
        h.update(sb)
        h.update(b"\x00")
        h.update(bb)
        h.update(b"\n")
    root_hex = h.hexdigest()

    # output identical to IMPL_A
    sys.stdout.write(f"{root_hex}\n")
    sys.stdout.write(f"members: {len(sorted_members)}\n")
    sys.stdout.write(f"status: OK\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
