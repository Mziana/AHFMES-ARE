#!/usr/bin/env python3
"""
path_router IMPL_B — alternative implementation, same contract
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import sys


def _blob_sha(data: bytes) -> str:
    h = hashlib.sha1()
    h.update(("blob %d\0" % len(data)).encode("utf-8"))
    h.update(data)
    return h.hexdigest()


def _die(code: int, msg: str):
    print(msg, file=sys.stderr)
    sys.exit(code)


def _parse_manifest_b(p):
    try:
        raw = open(p, "rb").read()
    except OSError as e:
        _die(3, f"error: cannot read manifest: {e}")
    if raw[:3] == b"\xef\xbb\xbf":
        _die(3, "error: manifest has BOM")
    try:
        txt = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        _die(3, f"error: manifest not utf-8: {e}")
    if "\r" in txt:
        _die(3, "error: manifest contains CR")
    members = []
    seen = set()
    pos = 0
    n = len(txt)
    while pos <= n:
        nxt = txt.find("\n", pos)
        if nxt == -1:
            line = txt[pos:]
            done = True
        else:
            line = txt[pos:nxt]
            done = False
        if line.strip().startswith("|"):
            cols = []
            cur = ""
            for ch in line:
                if ch == "|":
                    cols.append(cur)
                    cur = ""
                else:
                    cur += ch
            cols.append(cur)
            if len(cols) >= 4:
                pat_col = cols[1].strip()
                sha_col = cols[2].strip()
                b_col = cols[3].strip()
                if pat_col.lower() == "path" and "git" in sha_col.lower():
                    pass
                elif pat_col.startswith("---"):
                    pass
                else:
                    if pat_col.startswith("`") and pat_col.endswith("`"):
                        path = pat_col[1:-1].strip()
                    else:
                        if "`" in line:
                            _die(3, f"error: malformed manifest line: {line}")
                        path = None
                    if path is not None and path != "":
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
                                pass
                            else:
                                _die(3, f"error: malformed sha: {sha}")
                        else:
                            if not bstr.isdigit():
                                if bstr.lower().startswith("utf"):
                                    pass
                                else:
                                    _die(3, f"error: malformed bytes: {bstr}")
                            else:
                                if "\0" in path:
                                    _die(3, f"error: NUL in path: {path}")
                                if path in seen:
                                    _die(3, f"error: duplicate path: {path}")
                                seen.add(path)
                                members.append((path, sha, bstr))
        if done:
            break
        pos = nxt + 1
        if pos > n:
            break
    if not members:
        _die(3, "error: no members in manifest")
    return members


def _parse_routing_b(rp):
    try:
        raw = open(rp, "rb").read()
    except OSError as e:
        _die(2, f"error: cannot read routing table: {e}")
    if raw[:3] == b"\xef\xbb\xbf":
        _die(2, "error: routing table has BOM")
    try:
        txt = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        _die(2, f"error: routing table not utf-8: {e}")
    # normalize CRLF -> LF
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    stripped = txt.strip()
    if rp.endswith(".json") or stripped.startswith("{") or stripped.startswith("["):
        try:
            obj = json.loads(txt)
            pairs = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    pairs.append((k.strip(), v.strip()))
                if pairs:
                    return pairs
            elif isinstance(obj, list):
                for it in obj:
                    if isinstance(it, dict):
                        pat = it.get("pattern") or it.get("Pattern") or it.get("name")
                        folder = it.get("folder") or it.get("Folder") or it.get("destination") or it.get("tujuan")
                        if pat and folder:
                            pairs.append((str(pat).strip(), str(folder).strip()))
                    elif isinstance(it, (list, tuple)) and len(it) == 2:
                        pairs.append((str(it[0]).strip(), str(it[1]).strip()))
                if pairs:
                    return pairs
        except json.JSONDecodeError:
            pass
    pairs = []
    # manual line iteration
    start = 0
    while True:
        nl = txt.find("\n", start)
        if nl == -1:
            line = txt[start:]
            fin = True
        else:
            line = txt[start:nl]
            fin = False
        s = line.strip()
        if s and not s.startswith("#"):
            if "|" in line:
                # split by |
                parts = []
                cur = ""
                for ch in line:
                    if ch == "|":
                        parts.append(cur)
                        cur = ""
                    else:
                        cur += ch
                parts.append(cur)
                if len(parts) >= 3:
                    pat_col = parts[1].strip()
                    fol_col = parts[2].strip()
                    if pat_col.lower().startswith("pattern") and "folder" in fol_col.lower():
                        pass
                    elif pat_col.startswith("---"):
                        pass
                    else:
                        if pat_col.startswith("`") and pat_col.endswith("`"):
                            pat = pat_col[1:-1].strip()
                        else:
                            pat = pat_col.strip().strip("`").strip()
                        if fol_col.startswith("`") and fol_col.endswith("`"):
                            folder = fol_col[1:-1].strip()
                        else:
                            folder = fol_col.strip().strip("`").strip()
                        if pat and folder and not pat.startswith("---"):
                            pairs.append((pat, folder))
            elif "->" in line:
                left, right = line.split("->", 1)
                pat = left.strip().strip("`").strip()
                folder = right.strip().strip("`").strip()
                if pat and folder:
                    pairs.append((pat, folder))
            else:
                toks = s.split()
                if len(toks) >= 2:
                    pat = toks[0].strip("`")
                    folder = toks[1].strip("`")
                    pairs.append((pat, folder))
        if fin:
            break
        start = nl + 1
    if not pairs:
        _die(2, "error: no routing patterns found")
    return pairs


def main():
    argv = sys.argv[1:]
    src = None
    routing = None
    worktree = None
    out = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--source-manifest":
            if i + 1 >= len(argv):
                _die(2, "error: --source-manifest requires value")
            src = argv[i + 1]
            i += 2
        elif a.startswith("--source-manifest="):
            src = a.split("=", 1)[1]
            i += 1
        elif a == "--routing-table":
            if i + 1 >= len(argv):
                _die(2, "error: --routing-table requires value")
            routing = argv[i + 1]
            i += 2
        elif a.startswith("--routing-table="):
            routing = a.split("=", 1)[1]
            i += 1
        elif a == "--worktree":
            if i + 1 >= len(argv):
                _die(2, "error: --worktree requires value")
            worktree = argv[i + 1]
            i += 2
        elif a.startswith("--worktree="):
            worktree = a.split("=", 1)[1]
            i += 1
        elif a == "--out":
            if i + 1 >= len(argv):
                _die(2, "error: --out requires value")
            out = argv[i + 1]
            i += 2
        elif a.startswith("--out="):
            out = a.split("=", 1)[1]
            i += 1
        else:
            _die(2, f"error: unknown arg {a}")
    if not src or not routing or not worktree or not out:
        _die(2, "error: --source-manifest --routing-table --worktree --out all required")
    if not os.path.isfile(src):
        _die(2, f"error: source manifest not found: {src}")
    if not os.path.isfile(routing):
        _die(2, f"error: routing table not found: {routing}")
    if not os.path.isdir(worktree):
        _die(2, f"error: worktree not a directory: {worktree}")
    out_dir = os.path.dirname(os.path.abspath(out))
    if out_dir and not os.path.isdir(out_dir):
        _die(2, f"error: out directory not exist: {out_dir}")

    members = _parse_manifest_b(src)
    routing_pairs = _parse_routing_b(routing)
    sorted_members = sorted(members, key=lambda t: t[0].encode("utf-8"))

    results = []
    has_unmatched = False
    has_missing = False
    has_mutated = False
    has_ambiguous = False

    for old_path, old_sha, bstr in sorted_members:
        exp_len = int(bstr)
        basename = old_path.split("/")[-1]
        matched = []
        for pat, fol in routing_pairs:
            if fnmatch.fnmatch(basename, pat):
                matched.append((pat, fol))
        if len(matched) == 0:
            results.append({
                "old_path": old_path,
                "new_path": "",
                "matched_pattern": "",
                "old_blob_sha": old_sha,
                "new_blob_sha": "",
                "byte_length_equal": False,
                "status": "UNMATCHED"
            })
            has_unmatched = True
            continue
        if len(matched) > 1:
            pats = ", ".join(p for p, _ in matched)
            print(f"error: ambiguous routing for {old_path}: matches {pats}", file=sys.stderr)
            results.append({
                "old_path": old_path,
                "new_path": "",
                "matched_pattern": pats,
                "old_blob_sha": old_sha,
                "new_blob_sha": "",
                "byte_length_equal": False,
                "status": "UNMATCHED"
            })
            has_ambiguous = True
            continue
        pat, folder = matched[0]
        folder = folder.strip()
        if not folder.endswith("/"):
            folder += "/"
        folder = folder.lstrip("/")
        if folder.startswith("PROJECT_GOVERNANCE/"):
            folder = folder[len("PROJECT_GOVERNANCE/"):]
        if old_path.startswith("PROJECT_GOVERNANCE/"):
            new_path = "PROJECT_GOVERNANCE/" + folder + basename
        else:
            new_path = folder + basename
        full_new = os.path.join(worktree, *new_path.split("/"))
        full_new = os.path.abspath(full_new)
        if not full_new.startswith(os.path.abspath(worktree) + os.sep):
            results.append({
                "old_path": old_path,
                "new_path": new_path,
                "matched_pattern": pat,
                "old_blob_sha": old_sha,
                "new_blob_sha": "TRAVERSAL",
                "byte_length_equal": False,
                "status": "UNMATCHED"
            })
            has_ambiguous = True
            continue
        if old_sha == "SELF":
            if not os.path.isfile(full_new):
                results.append({
                    "old_path": old_path,
                    "new_path": new_path,
                    "matched_pattern": pat,
                    "old_blob_sha": old_sha,
                    "new_blob_sha": "MISSING",
                    "byte_length_equal": False,
                    "status": "MISSING"
                })
                has_missing = True
                continue
            try:
                data = open(full_new, "rb").read()
            except OSError:
                results.append({
                    "old_path": old_path,
                    "new_path": new_path,
                    "matched_pattern": pat,
                    "old_blob_sha": old_sha,
                    "new_blob_sha": "UNREADABLE",
                    "byte_length_equal": False,
                    "status": "MISSING"
                })
                has_missing = True
                continue
            bl_equal = (len(data) == exp_len)
            if bl_equal:
                new_sha = "SELF"
                status = "RELOCATED_IDENTICAL"
            else:
                new_sha = _blob_sha(data)
                status = "MUTATED"
                has_mutated = True
            results.append({
                "old_path": old_path,
                "new_path": new_path,
                "matched_pattern": pat,
                "old_blob_sha": old_sha,
                "new_blob_sha": new_sha,
                "byte_length_equal": bl_equal,
                "status": status
            })
            if status == "MUTATED":
                has_mutated = True
            continue
        if not os.path.isfile(full_new):
            results.append({
                "old_path": old_path,
                "new_path": new_path,
                "matched_pattern": pat,
                "old_blob_sha": old_sha,
                "new_blob_sha": "MISSING",
                "byte_length_equal": False,
                "status": "MISSING"
            })
            has_missing = True
            continue
        try:
            data = open(full_new, "rb").read()
        except OSError:
            results.append({
                "old_path": old_path,
                "new_path": new_path,
                "matched_pattern": pat,
                "old_blob_sha": old_sha,
                "new_blob_sha": "UNREADABLE",
                "byte_length_equal": False,
                "status": "MISSING"
            })
            has_missing = True
            continue
        new_sha = _blob_sha(data)
        bl_equal = (len(data) == exp_len)
        if new_sha != old_sha:
            status = "MUTATED"
            has_mutated = True
        elif not bl_equal:
            status = "MUTATED"
            has_mutated = True
        else:
            status = "RELOCATED_IDENTICAL"
        results.append({
            "old_path": old_path,
            "new_path": new_path,
            "matched_pattern": pat,
            "old_blob_sha": old_sha,
            "new_blob_sha": new_sha,
            "byte_length_equal": bl_equal,
            "status": status
        })

    results_sorted = sorted(results, key=lambda x: x["old_path"].encode("utf-8"))
    json_text = json.dumps(results_sorted, indent=2, sort_keys=True, ensure_ascii=False)
    # write with LF only
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(json_text + "\n")

    if has_ambiguous or has_unmatched or has_missing:
        if has_mutated:
            sys.exit(4)
        sys.exit(3)
    if has_mutated:
        sys.exit(4)
    sys.exit(0)


if __name__ == "__main__":
    main()
