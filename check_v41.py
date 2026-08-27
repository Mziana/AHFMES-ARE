import os, re

manifest_path = r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V41.md'

with open(manifest_path, 'r', encoding='utf-8') as f:
    content = f.read()

for line in content.split('\n'):
    if 'ARE3' in line and '|' in line:
        parts = line.split('|')
        if len(parts) >= 4:
            path = parts[1].strip().strip('`')
            sha = parts[2].strip()
            size = parts[3].strip()
            if 'ARE3' in path:
                print(f'{path} | {sha} | {size}')