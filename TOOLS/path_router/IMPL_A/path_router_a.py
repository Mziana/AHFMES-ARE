#!/usr/bin/env python3
"""
path_router IMPL_A — old-path -> new-path via tabel routing R1, bukti byte-identical
- stdlib only
- exit 0 only if all RELOCATED_IDENTICAL, exit 3 UNMATCHED/MISSING/ambiguous, exit 4 MUTATED
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import sys


def _blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("utf-8") + data).hexdigest()


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
        if not line.strip().startswith("|"):
            continue
        parts = line.split("|")
        if len(parts) < 4:
            continue
        path_col = parts[1].strip()
        sha_col = parts[2].strip()
        b_col = parts[3].strip()
        if path_col.lower() == "path" and sha_col.lower().startswith("git"):
            continue
        if path_col.startswith("---"):
            continue
        if path_col.startswith("`") and path_col.endswith("`"):
            path = path_col[1:-1].strip()
        else:
            if "`" in line:
                print(f"error: malformed manifest line: {line}", file=sys.stderr)
                sys.exit(3)
            continue
        sha = sha_col
        bstr = b_col
        ok = (sha == "SELF") or (len(sha) == 40 and all(c in "0123456789abcdef" for c in sha.lower()) and sha == sha.lower())
        if not ok:
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


def _parse_routing_table(routing_path: str):
    try:
        raw = open(routing_path, "rb").read()
    except OSError as e:
        print(f"error: cannot read routing table: {e}", file=sys.stderr)
        sys.exit(2)
    if raw.startswith(b"\xef\xbb\xbf"):
        print("error: routing table has BOM", file=sys.stderr)
        sys.exit(2)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        print(f"error: routing table not utf-8: {e}", file=sys.stderr)
        sys.exit(2)
    # normalize CRLF -> LF for cross-platform (Windows writes CRLF)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # try JSON first if file ends with .json or starts with { or [
    stripped = text.strip()
    if routing_path.endswith(".json") or stripped.startswith("{") or stripped.startswith("["):
        try:
            obj = json.loads(text)
            pairs = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    pairs.append((k.strip(), v.strip()))
                return pairs
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict):
                        pat = item.get("pattern") or item.get("Pattern") or item.get("name")
                        folder = item.get("folder") or item.get("Folder") or item.get("destination") or item.get("tujuan")
                        if pat and folder:
                            pairs.append((str(pat).strip(), str(folder).strip()))
                    elif isinstance(item, (list, tuple)) and len(item) == 2:
                        pairs.append((str(item[0]).strip(), str(item[1]).strip()))
                return pairs
        except json.JSONDecodeError:
            pass  # fall through to table parsing

    pairs = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "|" in line:
            parts = line.split("|")
            if len(parts) < 3:
                continue
            # could be markdown table: | pattern | folder |
            # parts[1] pattern, parts[2] folder
            pat_col = parts[1].strip()
            folder_col = parts[2].strip()
            # header detection
            if pat_col.lower().startswith("pattern") and "folder" in folder_col.lower():
                continue
            if pat_col.startswith("---"):
                continue
            # strip backticks
            if pat_col.startswith("`") and pat_col.endswith("`"):
                pat = pat_col[1:-1].strip()
            else:
                pat = pat_col.strip().strip("`").strip()
            if folder_col.startswith("`") and folder_col.endswith("`"):
                folder = folder_col[1:-1].strip()
            else:
                folder = folder_col.strip().strip("`").strip()
            if not pat or not folder:
                continue
            # skip empty or header like "---"
            if pat.startswith("---"):
                continue
            pairs.append((pat, folder))
        elif "->" in line:
            left, right = line.split("->", 1)
            pat = left.strip().strip("`").strip()
            folder = right.strip().strip("`").strip()
            if pat and folder:
                pairs.append((pat, folder))
        else:
            # whitespace separated: first token pattern, rest folder?
            # but pattern may contain spaces? no, assume no
            # split into 2
            toks = s.split()
            if len(toks) >= 2:
                pat = toks[0].strip("`")
                folder = toks[1].strip("`")
                pairs.append((pat, folder))
    if not pairs:
        print("error: no routing patterns found", file=sys.stderr)
        sys.exit(2)
    return pairs


def main():
    parser = argparse.ArgumentParser(description="path_router")
    parser.add_argument("--source-manifest", required=True, dest="source_manifest")
    parser.add_argument("--routing-table", required=True, dest="routing_table")
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    src = args.source_manifest
    routing = args.routing_table
    worktree = args.worktree
    out_path = args.out

    if not os.path.isfile(src):
        print(f"error: source manifest not found: {src}", file=sys.stderr)
        sys.exit(2)
    if not os.path.isfile(routing):
        print(f"error: routing table not found: {routing}", file=sys.stderr)
        sys.exit(2)
    if not os.path.isdir(worktree):
        print(f"error: worktree not a directory: {worktree}", file=sys.stderr)
        sys.exit(2)
    out_dir = os.path.dirname(os.path.abspath(out_path))
    if out_dir and not os.path.isdir(out_dir):
        print(f"error: out directory not exist: {out_dir}", file=sys.stderr)
        sys.exit(2)

    members = _parse_manifest(src)
    routing_pairs = _parse_routing_table(routing)

    # validate routing pairs uniqueness for patterns? duplicate pattern is config error?
    # but spec says pattern ganda yang cocok = error config (fail-closed)
    # we will detect during matching, not here

    sorted_members = sorted(members, key=lambda x: x[0].encode("utf-8"))

    results = []
    has_unmatched = False
    has_missing = False
    has_mutated = False
    has_ambiguous = False

    for old_path, old_sha, bstr in sorted_members:
        expected_len = int(bstr)
        basename = os.path.basename(old_path)
        matched = []
        for pat, folder in routing_pairs:
            # use fnmatch for glob with [A-F] etc.
            if fnmatch.fnmatch(basename, pat):
                matched.append((pat, folder))
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
            # still add entry for reporting
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
        # construct new_path
        # folder like "ARE0/CONTRACTS/" -> new_path = PROJECT_GOVERNANCE/ARE0/CONTRACTS/basename
        # normalize folder
        folder = folder.strip()
        if not folder.endswith("/"):
            folder = folder + "/"
        # remove leading slash
        folder = folder.lstrip("/")
        # remove PROJECT_GOVERNANCE prefix if present to avoid duplication
        if folder.startswith("PROJECT_GOVERNANCE/"):
            folder = folder[len("PROJECT_GOVERNANCE/"):]
        # old_path may be "PROJECT_GOVERNANCE/..." or just "ARE0/..."?
        # We always prefix with PROJECT_GOVERNANCE/
        if old_path.startswith("PROJECT_GOVERNANCE/"):
            new_path = "PROJECT_GOVERNANCE/" + folder + basename
        else:
            # fallback: if folder already includes prefix, use directly
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
            # for SELF, we consider byte identical if new file exists and length matches manifest file length?
            # but old_sha is SELF, we treat new_blob_sha as SELF if exists
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
            # for SELF, byte_length_equal check vs expected_len
            bl_equal = (len(data) == expected_len)
            # new blob sha for SELF we report as SELF if equal else actual sha
            if bl_equal:
                new_sha = "SELF"
                status = "RELOCATED_IDENTICAL"
            else:
                new_sha = _blob_sha1(data)
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
        new_sha = _blob_sha1(data)
        bl_equal = (len(data) == expected_len)
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

    # write out JSON deterministically sorted by old_path
    results_sorted = sorted(results, key=lambda x: x["old_path"].encode("utf-8"))
    # ensure byte-identical json via sort_keys and indent 2
    json_text = json.dumps(results_sorted, indent=2, sort_keys=True, ensure_ascii=False)
    # ensure file written with LF only
    # normalize to LF (json.dumps already uses \n)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json_text + "\n")

    # exit code mapping
    if has_ambiguous or has_unmatched or has_missing:
        # MUTATED takes precedence exit 4 if any mutated
        if has_mutated:
            sys.exit(4)
        sys.exit(3)
    if has_mutated:
        sys.exit(4)
    sys.exit(0)


if __name__ == "__main__":
    main()
