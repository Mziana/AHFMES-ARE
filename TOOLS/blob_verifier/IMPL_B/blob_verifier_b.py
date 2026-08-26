#!/usr/bin/env python3
"""
blob_verifier IMPL_B — alternative path, same output
"""
from __future__ import annotations

import hashlib
import os
import sys


def _blob_sha(data: bytes) -> str:
    h = hashlib.sha1()
    hdr = ("blob %d\0" % len(data)).encode("utf-8")
    h.update(hdr)
    h.update(data)
    return h.hexdigest()


def _die3(msg: str):
    print(msg, file=sys.stderr)
    sys.exit(3)


def _parse_b(manifest_path: str):
    try:
        raw = open(manifest_path, "rb").read()
    except OSError as e:
        _die3(f"error: cannot read manifest: {e}")
    if raw[:3] == b"\xef\xbb\xbf":
        _die3("error: manifest has BOM")
    try:
        txt = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        _die3(f"error: manifest not utf-8: {e}")
    if "\r" in txt:
        _die3("error: manifest contains CR")
    members = []
    seen = set()
    # manual split via find, differ from impl A
    pos = 0
    line_no = 0
    n = len(txt)
    while pos <= n:
        nxt = txt.find("\n", pos)
        if nxt == -1:
            line = txt[pos:]
            pos = n + 1
        else:
            line = txt[pos:nxt]
            pos = nxt + 1
        line_no += 1
        if pos > n + 1:
            break
        s = line.strip()
        if not s.startswith("|"):
            if nxt == -1:
                break
            continue
        # split manually by '|'
        cols = []
        cur = ""
        for ch in line:
            if ch == "|":
                cols.append(cur)
                cur = ""
            else:
                cur += ch
        cols.append(cur)
        if len(cols) < 4:
            if nxt == -1:
                break
            continue
        path_col = cols[1].strip()
        sha_col = cols[2].strip()
        b_col = cols[3].strip()
        if path_col.lower() == "path" and "git" in sha_col.lower():
            if nxt == -1:
                break
            continue
        if path_col.startswith("---"):
            if nxt == -1:
                break
            continue
        if path_col.startswith("`") and path_col.endswith("`"):
            p = path_col[1:-1].strip()
        else:
            if "`" in line:
                _die3(f"error: malformed member: {line}")
            if nxt == -1:
                break
            continue
        sha = sha_col
        bstr = b_col
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
            if sha.lower().startswith("git"):
                if nxt == -1:
                    break
                continue
            _die3(f"error: malformed sha: {sha}")
        if not bstr.isdigit():
            if bstr.lower().startswith("utf"):
                if nxt == -1:
                    break
                continue
            _die3(f"error: malformed bytes: {bstr}")
        if "\0" in p:
            _die3(f"error: NUL in path: {p}")
        if p in seen:
            _die3(f"error: duplicate path: {p}")
        seen.add(p)
        members.append((p, sha, bstr))
        if nxt == -1:
            break
    if not members:
        _die3("error: no members in manifest")
    return members


def main():
    argv = sys.argv[1:]
    manifest = None
    worktree = None
    git_dir = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--manifest":
            if i + 1 >= len(argv):
                print("error: --manifest requires value", file=sys.stderr)
                sys.exit(3)
            manifest = argv[i + 1]
            i += 2
        elif a.startswith("--manifest="):
            manifest = a.split("=", 1)[1]
            i += 1
        elif a == "--worktree":
            if i + 1 >= len(argv):
                print("error: --worktree requires value", file=sys.stderr)
                sys.exit(3)
            worktree = argv[i + 1]
            i += 2
        elif a.startswith("--worktree="):
            worktree = a.split("=", 1)[1]
            i += 1
        elif a == "--git-dir":
            if i + 1 >= len(argv):
                print("error: --git-dir requires value", file=sys.stderr)
                sys.exit(3)
            git_dir = argv[i + 1]
            i += 2
        elif a.startswith("--git-dir="):
            git_dir = a.split("=", 1)[1]
            i += 1
        else:
            print(f"error: unknown arg {a}", file=sys.stderr)
            sys.exit(3)
    if manifest is None or worktree is None:
        print("error: --manifest and --worktree required", file=sys.stderr)
        sys.exit(3)
    if not os.path.isfile(manifest):
        _die3(f"error: manifest not found: {manifest}")
    if not os.path.isdir(worktree):
        _die3(f"error: worktree not a directory: {worktree}")
    if git_dir is not None and not os.path.isdir(git_dir):
        _die3(f"error: git-dir not a directory: {git_dir}")

    members = _parse_b(manifest)
    try:
        mlen = os.path.getsize(manifest)
    except OSError:
        mlen = None
    # sort byte-wise
    sorted_members = sorted(members, key=lambda t: t[0].encode("utf-8"))

    rows = []
    pcnt = 0
    fcnt = 0
    for path, exp_sha, bstr in sorted_members:
        exp_len = int(bstr)
        full = os.path.join(worktree, *path.split("/"))
        act_sha = ""
        act_bytes = ""
        st = "FAIL"
        if exp_sha == "SELF":
            if not os.path.isfile(full):
                if mlen is not None and exp_len == mlen:
                    act_sha = "SELF"
                    act_bytes = str(mlen)
                    st = "OK"
                    pcnt += 1
                else:
                    act_sha = "MISSING"
                    act_bytes = "MISSING"
                    st = "FAIL"
                    fcnt += 1
                rows.append((path, exp_sha, act_sha, act_bytes, st))
                continue
            try:
                data = open(full, "rb").read()
                alen = len(data)
                act_bytes = str(alen)
                if alen == exp_len:
                    act_sha = "SELF"
                    st = "OK"
                    pcnt += 1
                else:
                    act_sha = "SELF"
                    st = "FAIL"
                    fcnt += 1
            except OSError:
                act_sha = "UNREADABLE"
                act_bytes = "UNREADABLE"
                st = "FAIL"
                fcnt += 1
            rows.append((path, exp_sha, act_sha, act_bytes, st))
            continue
        if not os.path.isfile(full):
            act_sha = "MISSING"
            act_bytes = "MISSING"
            st = "FAIL"
            fcnt += 1
            rows.append((path, exp_sha, act_sha, act_bytes, st))
            continue
        try:
            data = open(full, "rb").read()
        except OSError:
            act_sha = "UNREADABLE"
            act_bytes = "UNREADABLE"
            st = "FAIL"
            fcnt += 1
            rows.append((path, exp_sha, act_sha, act_bytes, st))
            continue
        alen = len(data)
        act_bytes = str(alen)
        act_sha = _blob_sha(data)
        if alen != exp_len or act_sha != exp_sha:
            st = "FAIL"
            fcnt += 1
        else:
            st = "OK"
            pcnt += 1
        rows.append((path, exp_sha, act_sha, act_bytes, st))

    # build output identical to IMPL_A
    lines = []
    lines.append("PATH | EXPECTED_SHA | ACTUAL_SHA | BYTES | STATUS")
    for path, exp, act, bstr2, st in rows:
        lines.append(f"{path} | {exp} | {act} | {bstr2} | {st}")
    lines.append(f"TOTAL: {len(rows)}")
    lines.append(f"PASS: {pcnt}")
    lines.append(f"FAIL: {fcnt}")
    sys.stdout.write("\n".join(lines) + "\n")
    if fcnt > 0:
        sys.exit(3)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
