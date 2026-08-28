import os, re, subprocess

manifest_path = r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md'

with open(manifest_path, 'r', encoding='utf-8') as f:
    content = f.read()

files_to_update = {
    'PROJECT_GOVERNANCE/CURRENT_AUTHORITY_INDEX.md': ('f22367a3fcdeedd9167eebf1e91a797a752a1182', 2834),
    'are/evidence.py': ('4e78053954d3f62c61080a9ab0109fdd59ea5f2b', 71535),
    'are/registry.py': ('dd644b828edcf9f0bd8808e14ce321fbaab0a96c', 65024),
    'are/storage.py': ('4be4c3052639a0f57722812472140adeb5944295', 35496),
}

with open(manifest_path, 'r', encoding='utf-8') as f:
    content = f.read()

for path, (sha, size) in files_to_update.items():
    old_pattern = rf'\| `{re.escape(path)}` \| [0-9a-f]{{40}} \| \d+ \|'
    new_line = f'| `{path}` | {sha} | {size} |'
    content = re.sub(old_pattern, new_line, content)

# Fix SELF line
actual_size = os.path.getsize(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md')
content = re.sub(
    r'\| `PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40\.md` \| SELF \| \d+ \|',
    f'| `PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md` | SELF | {actual_size} |',
    content
)

with open(manifest_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated manifest V40')