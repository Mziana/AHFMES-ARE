import os, re, subprocess

manifest_path = r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V41.md'

with open(manifest_path, 'r', encoding='utf-8') as f:
    content = f.read()

files_to_update = {
    'PROJECT_GOVERNANCE/ARE3/DIARY/2026-08-28-ARE3-OPENING-JURNAL.md': ('bbf731b53cbad3d81392d8bcf211a94e7880598c', 2893),
    'PROJECT_GOVERNANCE/ARE3/README.md': ('09ec65aefda280029e1347985db6241f4d4218b2', 3483),
    'PROJECT_GOVERNANCE/ARE3/RESIDUAL_REGISTER.md': ('97a3e9085646385bd0930cbcb7fa4f9e590509db', 1927),
}

with open(manifest_path, 'r', encoding='utf-8') as f:
    content = f.read()

for path, (sha, size) in files_to_update.items():
    # More permissive regex
    old_pattern = r'\| `PROJECT_GOVERNANCE/ARE3/' + re.escape(path.split('/')[-1]) + r'` \| [0-9a-f]{40} \| \d+ \|'
    new_line = f'| `{path}` | {sha} | {size} |'
    content = re.sub(old_pattern, new_line, content)

with open(manifest_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated manifest V41')