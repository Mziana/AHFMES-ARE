import os, hashlib, subprocess

# Get all tracked files
result = subprocess.run(['git', 'ls-files'], capture_output=True, text=True, cwd=r'D:\Hermes\AHFMES-ARE')
files = result.stdout.strip().split('\n')

# Filter for manifestable files
manifest_files = []
for f in files:
    if f.endswith('.md') or f.endswith('.py'):
        if any(f.startswith(p) for p in ['PROJECT_GOVERNANCE/', 'ENGINEERING/', 'are/', 'tests/']):
            manifest_files.append(f)

manifest_files.sort()

# Generate manifest entries
entries = []
for f in sorted(manifest_files):
    if os.path.exists(f'D:/Hermes/AHFMES-ARE/{f}'):
        size = os.path.getsize(f'D:/Hermes/AHFMES-ARE/{f}')
        result = subprocess.run(['git', 'hash-object', f'D:/Hermes/AHFMES-ARE/{f}'], capture_output=True, text=True, cwd=r'D:\Hermes\AHFMES-ARE')
        if result.returncode == 0:
            sha = result.stdout.strip()
            entries.append((f, sha, size))

# Write manifest V40
manifest_path = r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md'

with open(manifest_path, 'w', encoding='utf-8') as f:
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
    
    # SELF entry
    self_size = os.path.getsize(r'D:\Hermes\AHFMES-ARE\PROJECT_GOVERNANCE\ARE0\MANIFEST\AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md')
    f.write(f'| `PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V40.md` | SELF | {self_size} |\n')
    
    f.write('\n## Exact closed-set cardinality\n\n```text\n')
    f.write(f'TOTAL = {len(entries) + 1}\n```\n\n')
    f.write('## Canonical root algorithm\n\nFor exact subject S, every non-self member must exist at the listed path with exact lowercase 40-hex Git blob SHA-1 and listed UTF-8 byte length. Construct tuple PATH NUL SHA NUL LEN LF for every member (SELF uses literal SELF and manifest actual byte length); sort all tuples lexicographically by raw UTF-8 path bytes; concatenate with no separator; compute SHA-256. Any mismatch fails closed. Hashing uses blob bytes exactly as stored - no EOL conversion. Declared SELF length must equal actual.\n\n')
    f.write('## Qualification reset and firewall\n\nThis manifest opens the ARE-2 wave. Its S0 is the commit containing this integration, the binding (generation 40), and the refreshed authority index. Regression catalog remains 369 scenarios (R7=26 R8=40 R9=X001..X303). Firewall: ARE-0 CLOSED(formal)=YES-by-acceptance-record; ARE-1 CLOSED(formal)=YES-by-acceptance-record; IMPLEMENTATION(ARE-2)=AUTHORIZED; P001 NOT AUTHORIZED; PRODUCTION CLOSED; LIVE/PAPER TRADING NOT AUTHORIZED.\n')

print('Manifest V40 written!')