import os, hashlib, subprocess

# Get all tracked files
result = subprocess.run(['git', 'ls-files'], capture_output=True, text=True, cwd=r'D:\Hermes\AHFMES-ARE')
files = result.stdout.strip().split('\n')

manifest_files = []
for f in files:
    if f.endswith('.md') or f.endswith('.py'):
        if any(f.startswith(p) for p in ['PROJECT_GOVERNANCE/', 'ENGINEERING/', 'are/', 'tests/']):
            manifest_files.append(f)

manifest_files.sort()

entries = []
for f in manifest_files:
    if os.path.exists(f'D:/Hermes/AHFMES-ARE/{f}'):
        size = os.path.getsize(f'D:/Hermes/AHFMES-ARE/{f}')
        result = subprocess.run(['git', 'hash-object', f'D:/Hermes/AHFMES-ARE/{f}'], capture_output=True, text=True, cwd=r'D:\Hermes\AHFMES-ARE')
        if result.returncode == 0:
            sha = result.stdout.strip()
            entries.append((f, sha, size))

# The closing sections (after SELF line) - these are fixed content
closing_sections = '''\n## Exact closed-set cardinality

```text
TOTAL = PLACEHOLDER_TOTAL
```

## Canonical root algorithm

For exact subject S, every non-self member must exist at the listed path with exact lowercase 40-hex Git blob SHA-1 and listed UTF-8 byte length. Construct tuple PATH NUL SHA NUL LEN LF for every member (SELF uses literal SELF and manifest actual byte length); sort all tuples lexicographically by raw UTF-8 path bytes; concatenate with no separator; compute SHA-256. Any mismatch fails closed. Hashing uses blob bytes exactly as stored - no EOL conversion. Declared SELF length must equal actual.

## Qualification reset and firewall

This manifest opens the ARE-2 wave. Its S0 is the commit containing this integration, the binding (generation 40), and the refreshed authority index. Regression catalog remains 369 scenarios (R7=26 R8=40 R9=X001..X303). Firewall: ARE-0 CLOSED(formal)=YES-by-acceptance-record; ARE-1 CLOSED(formal)=YES-by-acceptance-record; IMPLEMENTATION(ARE-2)=AUTHORIZED; P001 NOT AUTHORIZED; PRODUCTION CLOSED; LIVE/PAPER TRADING NOT AUTHORIZED.
'''

# Calculate the fixed overhead: closing sections + SELF line
self_line_template = '\n| `PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md` | SELF | {size} |\n'
closing_len = len(closing_sections.replace('PLACEHOLDER_TOTAL', str(len(entries) + 1)))

# Fixed point iteration for total size
# total_size = temp_size + len(SELF_line) + len(closing_sections)
# where SELF_line contains total_size

temp_size = 40698  # from previous run

total_size = 0
for _ in range(10):
    self_line = f'\n| `PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md` | SELF | {total_size} |\n'
    new_total = 40698 + len(self_line) + len(closing_sections)
    if new_total == total_size:
        break
    total_size = new_total

print(f'Fixed point total_size: {total_size}')

# Write temp file (without SELF and closing)
temp_path = r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40_temp.md'
with open(temp_path, 'w', encoding='utf-8') as f:
    f.write('# AHFMES ARE-0 - Normative Authority Manifest V40\n\n')
    f.write('Status: **CLOSED EXACT PATH SET / GENERATION 40 / ARE-2 IMPLEMENTATION AUTHORIZED / INTEGRATES ARE-2 TAGS / NO IMPLEMENTATION AUTHORITY**\n\n')
    f.write('## Current composition\n\n```text\n')
    f.write('CURRENT_MATRIX = V30\n')
    f.write('CURRENT_INVENTORY = V30\n')
    f.write('CURRENT_HASH_DOMAIN_TAGS = V1 (ARE-1) + ARE2 (appendix, superset-closed per S1)\n')
    f.write('CURRENT_CORRECTION = V35\n')
    f.write('CURRENT_PROTOCOL = V36\n')
    f.write('CURRENT_QUARANTINE_POLICY = V9\n')
    f.write('CURRENT_BINDING = stable binding below\n')
    f.write('IAQ_REGISTRATION = ENGINEERING/IAQ_LEDGER_ARE2.md registered as ARE-2 opening QAO record [S2]\n')
    f.write('PREDECESSOR_QUALIFICATION_CREDIT = NONE (gen-39 closed @6958905)\n```\n\n')
    f.write('Only the exact members below are current machine/closure/audit-rule authority. This manifest supersedes V39 as the current manifest and opens the ARE-2 wave. Relocated historical members keep their blob identities; generation-40 additions (Hash-Domain-Tags ARE2, ARE-2 contracts, charters) and the binding carry new blobs integrating the ARE-2 triase results and the external audit acceptance of ARE-1.\n\n')
    f.write('## Exact member table\n\n')
    f.write('| Path | Git blob SHA-1 | UTF-8 bytes |\n')
    f.write('|---|---|---:|\n')
    
    for path, sha, size in sorted(entries):
        f.write(f'| `{path}` | {sha} | {size} |\n')
    
    f.write('\n')

# Get temp size
temp_size = os.path.getsize(temp_path)
print(f'Temp size (without SELF and closing): {temp_size}')

# Fixed point iteration for total size including closing sections
total_size = 0
closing = '''\n## Exact closed-set cardinality

```text
TOTAL = PLACEHOLDER_TOTAL
```

## Canonical root algorithm

For exact subject S, every non-self member must exist at the listed path with exact lowercase 40-hex Git blob SHA-1 and listed UTF-8 byte length. Construct tuple PATH NUL SHA NUL LEN LF for every member (SELF uses literal SELF and manifest actual byte length); sort all tuples lexicographically by raw UTF-8 path bytes; concatenate with no separator; compute SHA-256. Any mismatch fails closed. Hashing uses blob bytes exactly as stored - no EOL conversion. Declared SELF length must equal actual.

## Qualification reset and firewall

This manifest opens the ARE-2 wave. Its S0 is the commit containing this integration, the binding (generation 40), and the refreshed authority index. Regression catalog remains 369 scenarios (R7=26 R8=40 R9=X001..X303). Firewall: ARE-0 CLOSED(formal)=YES-by-acceptance-record; ARE-1 CLOSED(formal)=YES-by-acceptance-record; IMPLEMENTATION(ARE-2)=AUTHORIZED; P001 NOT AUTHORIZED; PRODUCTION CLOSED; LIVE/PAPER TRADING NOT AUTHORIZED.
'''
closing_len = len(closing_sections.replace('PLACEHOLDER_TOTAL', str(len(entries) + 1)))

total_size = 0
for _ in range(10):
    self_line = f'\n| `PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md` | SELF | {total_size} |\n'
    new_total = 40698 + len(self_line) + closing_len
    if new_total == total_size:
        break
    total_size = new_total

print(f'Fixed point total_size: {total_size}')

# Write final manifest
manifest_path = r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md'
with open(temp_path, 'r', encoding='utf-8') as f:
    temp_content = f.read()

with open(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md', 'w', encoding='utf-8') as f:
    f.write(open(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40_temp.md', 'r', encoding='utf-8').read())
    f.write(f'\n| `PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md` | SELF | {total_size} |\n')
    f.write(closing_sections.replace('PLACEHOLDER_TOTAL', str(len(entries) + 1)))

print('Manifest V40 written!')

# Verify
import hashlib
with open(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md', 'r', encoding='utf-8') as f:
    m = f.read()

rows = []
for line in m.split('\n'):
    if line.startswith('| ') and not line.startswith('| Path') and not line.startswith('|---'):
        parts = line.split('|')
        if len(parts) >= 4:
            path = parts[1].strip().strip('\`')
            sha = parts[2].strip()
            ln = parts[3].strip()
            if sha and ln.isdigit():
                rows.append((parts[1].strip().strip('\`'), sha, int(ln)))

print('Members:', len(rows))
for p, sha, ln in rows:
    if sha == 'SELF':
        print(f'SELF len: {ln}')
        break

tuples = [f'{p}\0{sha}\0{ln}\n'.encode() for p, sha, ln in rows]
tuples.sort()
root = hashlib.sha256(b''.join(tuples)).hexdigest()
print(f'Root: {root}')

actual_size = os.path.getsize(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md')
print(f'Final size: {actual_size}')
print(f'Expected SELF len: {total_size}, match: {total_size == actual_size}')

print('Done!')