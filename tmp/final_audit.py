#!/usr/bin/env python3
import pathlib, hashlib, subprocess, re, os, json, sys

workdir = pathlib.Path(r"D:\Hermes\AHFMES-ARE")
manifest_path = workdir / "PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V39.md"
# verify SELF length
actual_size = manifest_path.stat().st_size
print(f"MANIFEST actual size: {actual_size}")
raw = manifest_path.read_bytes()
hdr = ("blob %d\0" % len(raw)).encode()
print(f"MANIFEST blob sha: {hashlib.sha1(hdr+raw).hexdigest()}")

# git hash-object check
import subprocess
r = subprocess.run(["git","hash-object", str(manifest_path)], capture_output=True, text=True, cwd=str(workdir))
print(f"git hash-object: {r.stdout.strip()}")

# parse manifest members count from file
text = raw.decode()
members = []
for line in text.splitlines():
    if line.strip().startswith("|") and "`" in line:
        parts = line.split("|")
        if len(parts)>=4:
            path_col = parts[1].strip()
            if path_col.startswith("`") and path_col.endswith("`"):
                members.append(path_col[1:-1])
print(f"Members parsed from manifest table: {len(members)} (expected 136)")

# check git ls-tree for 9ca5289 manifest blob
r2 = subprocess.run(["git","ls-tree","-r","9ca5289", "--", "PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V39.md"], capture_output=True, text=True, cwd=str(workdir))
print(f"9ca5289 ls-tree manifest line: {r2.stdout.strip()}")

# check binding
binding = workdir / "PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_CURRENT_NORMATIVE_MANIFEST_BINDING.md"
bdata = binding.read_bytes()
bhdr = ("blob %d\0" % len(bdata)).encode()
print(f"Binding size: {binding.stat().st_size} sha: {hashlib.sha1(bhdr+bdata).hexdigest()}")

# hash domain tags
hdt = workdir / "PROJECT_GOVERNANCE/ARE0/MACHINE/AHFMES_ARE_HASH_DOMAIN_TAGS_V1.md"
hdata = hdt.read_bytes()
hhdr = ("blob %d\0" % len(hdata)).encode()
print(f"HDT size: {hdt.stat().st_size} sha: {hashlib.sha1(hhdr+hdata).hexdigest()}")

# quarantine
qp9 = workdir / "PROJECT_GOVERNANCE/ARE0/QUARANTINE/AHFMES_ARE_0_LEGACY_AUTHORITY_QUARANTINE_POLICY_V9.md"
qdata = qp9.read_bytes()
qhdr = ("blob %d\0" % len(qdata)).encode()
print(f"QP9 size: {qp9.stat().st_size} sha: {hashlib.sha1(qhdr+qdata).hexdigest()}")

# canonical tags
canon = workdir / "are/canonical.py"
m = re.search(r'DOMAIN_TAGS\s*=\s*frozenset\(\{([^}]+)\}', canon.read_text(encoding='utf-8'), re.DOTALL)
tags_py = re.findall(r'"([A-Z_]+)"', m.group(1))
print(f"canonical.py tags: {len(tags_py)}")
md_tags = re.findall(r'^[A-Z_]+$', hdt.read_text(encoding='utf-8'), re.MULTILINE)
print(f"HDT.md tags: {len(md_tags)}")
print(f"Tag sets equal? {set(tags_py)==set(md_tags)}")

# storage checks
storage = workdir / "are/storage.py"
stxt = storage.read_text(encoding='utf-8')
print(f"storage triggers: {stxt.count('CREATE TRIGGER')}")
print(f"storage heads_no_delete: {stxt.count('heads_no_delete')}")
print(f"storage receipts_no_replace: {stxt.count('receipts_no_replace')}")
print(f"storage heads_no_update (should be 0 after hygiene): {'heads_no_update' in stxt}")

# manifest_hash outputs already verified via tool calls, but recompute root independently
import hashlib as hl
# parse members with sha and bytes as tools do
members_tuples = []
for line in text.splitlines():
    if not line.strip().startswith("|"):
        continue
    parts = line.split("|")
    if len(parts)<4:
        continue
    path_col = parts[1].strip()
    sha_col = parts[2].strip()
    bytes_col = parts[3].strip()
    if path_col.lower()=="path" and sha_col.lower().startswith("git"):
        continue
    if path_col.startswith("---"):
        continue
    if path_col.startswith("`") and path_col.endswith("`"):
        path = path_col[1:-1].strip()
        sha = sha_col
        bstr = bytes_col
        if not path:
            continue
        if sha=="SELF" or (len(sha)==40 and all(c in "0123456789abcdef" for c in sha)):
            if not bstr.isdigit():
                continue
            members_tuples.append((path, sha, bstr))
# sort
sorted_members = sorted(members_tuples, key=lambda x: x[0].encode("utf-8"))
out = bytearray()
for p,s,b in sorted_members:
    tup = ("%s\0%s\0%s\n" % (p,s,b)).encode("utf-8")
    out.extend(tup)
root = hl.sha256(bytes(out)).hexdigest()
expected = "60bc573f5f540c56a19bf11a9d9788c652db37a7736e41097d1a90aadd64a55c"
print(f"Independently computed root: {root}")
print(f"Matches expected {expected} ? {root==expected}")
print(f"Members count for root: {len(sorted_members)}")

# verify each member file on disk matches sha/len (sample heavy check via tools already did, but quick independent)
fail = 0
for p,s,b in sorted_members:
    if s=="SELF":
        if int(b)!= actual_size:
            print(f"SELF mismatch {p}")
            fail+=1
        continue
    fp = workdir / p.replace("/", os.sep)
    if not fp.exists():
        print(f"MISSING {p}")
        fail+=1
        continue
    data = fp.read_bytes()
    if len(data)!= int(b):
        print(f"LEN mismatch {p} expected {b} actual {len(data)}")
        fail+=1
    hdr2 = ("blob %d\0" % len(data)).encode()
    h = hashlib.sha1(hdr2+data).hexdigest()
    if h!=s:
        print(f"SHA mismatch {p} expected {s} actual {h}")
        fail+=1
print(f"Independent blob verification FAIL count: {fail} / {len(sorted_members)}")
