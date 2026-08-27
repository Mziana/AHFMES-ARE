import pathlib, re
md = pathlib.Path('PROJECT_GOVERNANCE/ARE0/MACHINE/AHFMES_ARE_HASH_DOMAIN_TAGS_V1.md').read_text(encoding='utf-8')
tags_md = re.findall(r'^[A-Z_]+$', md, re.MULTILINE)
print('Tags from MD:', len(tags_md))
for t in tags_md:
    print(t)
print('---')
canon = pathlib.Path('are/canonical.py').read_text(encoding='utf-8')
m = re.search(r'DOMAIN_TAGS\s*=\s*frozenset\(\{([^}]+)\}', canon, re.DOTALL)
if m:
    block = m.group(1)
    tags_py = re.findall(r'"([A-Z_]+)"', block)
    print('Tags from canonical.py:', len(tags_py))
    for t in sorted(tags_py):
        print(t)
    print('---')
    print('MD set == PY set ?', set(tags_md) == set(tags_py))
    print('Missing in PY:', set(tags_md)-set(tags_py))
    print('Extra in PY:', set(tags_py)-set(tags_md))
    print('Counts: MD', len(set(tags_md)), 'PY', len(set(tags_py)))
    print('MD duplicates?', len(tags_md) != len(set(tags_md)))
    print('PY duplicates?', len(tags_py) != len(set(tags_py)))
