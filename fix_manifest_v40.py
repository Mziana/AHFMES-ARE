import os, hashlib

# Read the manifest
with open(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find SELF line index
self_idx = None
for i, line in enumerate(lines):
    if 'SELF' in line and '|' in line:
        self_idx = i
        break

# Write temp manifest without SELF line
temp_path = r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40_temp.md'
with open(temp_path, 'w', encoding='utf-8') as f:
    for i, line in enumerate(lines):
        if i != self_idx:
            f.write(line)

# Get size of manifest without SELF line
temp_size = os.path.getsize(temp_path)
print(f'Temp size (without SELF): {temp_size}')

# Now the SELF line should have this length
self_line = f'| `PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md` | SELF | {temp_size} |\n'

# Write final manifest
with open(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md', 'w', encoding='utf-8') as f:
    for i, line in enumerate(open(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md', 'r', encoding='utf-8').readlines()):
        if i != self_idx:
            f.write(line)
        else:
            f.write(f'| `PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md` | SELF | {temp_size} |\n')

# Verify
actual_size = os.path.getsize(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md')
print(f'Final manifest size: {actual_size}')
print(f'Expected SELF len: {temp_size}, match: {temp_size == actual_size}')

# Verify root
import hashlib
with open(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md', 'r', encoding='utf-8') as f:
    m = f.read()

rows = []
for line in open(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md', 'r', encoding='utf-8').read().split('\n'):
    if line.startswith('| ') and not line.startswith('| Path') and not line.startswith('|---'):
        parts = line.split('|')
        if len(parts) >= 4:
            path = parts[1].strip().strip('`')
            sha = parts[2].strip()
            ln = parts[3].strip()
            if sha and ln.isdigit():
                p = parts[1].strip().strip('`')
                rows.append((p, parts[2].strip(), int(parts[3].strip())))

print('Members:', len(rows))
for p, sha, ln in rows:
    if sha == 'SELF':
        print(f'SELF len: {ln}')
        break

tuples = [f'{p}\0{sha}\0{ln}\n'.encode() for p, sha, ln in rows]
tuples.sort()
root = hashlib.sha256(b''.join(tuples)).hexdigest()
print(f'Root: {root}')

# Clean up temp file
os.remove(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40_temp.md')

print('Done!')