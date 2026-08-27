import os, hashlib

# Read the manifest
with open(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the SELF line and extract the current length
import re
self_line_pattern = r'\| `PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40\.md` \| SELF \| (\d+) \|'
match = re.search(self_line_pattern, content)
if match:
    old_len = int(match.group(1))
    print(f'Old SELF len: {old_len}')

# Compute the correct length by removing the SELF line and measuring
lines = content.split('\n')
new_lines = [line for line in lines if 'SELF' not in line or '| SELF |' not in line]

# Write temp file to get size
temp_content = '\n'.join(new_lines)
temp_path = r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40_temp.md'
with open(temp_path, 'w', encoding='utf-8') as f:
    f.write(temp_content)

temp_size = os.path.getsize(temp_path)
print(f'Temp size (without SELF line): {temp_size}')

# Now create the final content with correct SELF length
# Read the original content and replace the SELF line
import re
new_content = re.sub(
    r'\| `PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40\.md` \| SELF \| \d+ \|',
    f'| `PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md` | SELF | {os.path.getsize(r"D:/Hermes/AHFMES-ARE/PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md")} |',
    open(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md', 'r', encoding='utf-8').read()
)

# This is getting complex. Let me just write a clean script that computes the right size.
# The issue is circular: we need the final file size to write the SELF length, but the file size depends on the SELF length.

# The correct approach:
# 1. Write manifest without SELF line
# 2. Get its size
# 3. Write final with SELF = that size
# 3. Verify size matches

import os, hashlib, re

# Read current manifest
with open(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove SELF line
lines = content.split('\n')
new_lines = [line for line in lines if not ('SELF' in line and '|' in line and 'MANIFEST_V40' in line)]
temp_content = '\n'.join(new_lines)

# Write temp file
temp_path = r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40_temp.md'
with open(temp_path, 'w', encoding='utf-8') as f:
    f.write(temp_content)

temp_size = os.path.getsize(temp_path)
print(f'Temp size (without SELF): {temp_size}')

# Now create final content with correct SELF length
final_content = temp_content + f'\n| `PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md` | SELF | {temp_size} |\n'

# Write final manifest
manifest_path = r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md'
with open(manifest_path, 'w', encoding='utf-8') as f:
    f.write(final_content)

# Verify
actual_size = os.path.getsize(manifest_path)
print(f'Final manifest size: {actual_size}')
print(f'Expected SELF len: {temp_size}, match: {temp_size == actual_size}')

# Verify root
import hashlib
with open(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md', 'r', encoding='utf-8') as f:
    m = f.read()

rows = []
for line in m.split('\n'):
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

# Clean up
if os.path.exists(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40_temp.md'):
    os.remove(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40_temp.md')

print('Done!')