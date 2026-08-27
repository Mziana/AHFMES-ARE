import os, re

path = r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md'

# Get actual file size
actual_size = os.path.getsize(path)
print(f'Actual file size: {actual_size}')

# Read manifest
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix SELF line with correct size
new_content = re.sub(
    r'\| `PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40\.md` \| SELF \| \d+ \|',
    f'| `PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md` | SELF | {actual_size} |',
    content
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Fixed SELF line')
print(f'New file size: {os.path.getsize(path)}')