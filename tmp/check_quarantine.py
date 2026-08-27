import pathlib, re

q9 = pathlib.Path('PROJECT_GOVERNANCE/ARE0/QUARANTINE/AHFMES_ARE_0_LEGACY_AUTHORITY_QUARANTINE_POLICY_V9.md').read_text(encoding='utf-8')
print("=== V9 content ===")
print(q9)

# Extract Exact post-S0 output set block
import re
# find block between "Only these exact paths" and "```" end
m = re.search(r'Only these exact paths may change after S0.*?```text(.*?)```', q9, re.DOTALL)
if m:
    block = m.group(1)
    paths = [l.strip() for l in block.strip().splitlines() if l.strip()]
    print(f"\nPost-S0 exact paths count: {len(paths)}")
    for p in paths:
        print(f"  - {p}")
    print(f"\nQAO8 = first 8, etc. Total should be 10 literal paths")
    print(f"Expected 10 per QUARANTINE_POLICY_V9:10 tag (check if V9 claims 10)")
    
# Check the policy's own claim: it says 10 literal paths, let's verify manifest binding etc.
manifest = pathlib.Path('PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V39.md').read_text(encoding='utf-8')
# Find post-S0 set in manifest? No, that's separate.

# Verify that ENGINEERING/DELEGASI_003... is NOT in post-S0 set (quarantine violation check for 9ca5289..HEAD)
post_s0_set = set(paths) if m else set()
test_paths = ["ENGINEERING/DELEGASI_003_HYGIENE_EA0C595_RES02.md", "are/storage.py"]
for tp in test_paths:
    print(f"{tp} in post-S0 set? {tp in post_s0_set}")

# Also check what git diff shows as changed files between S0 (need to find S0 commit)
# From manifest: S0 is commit containing integration, binding generation 39
# Let's check what S0 is claimed to be - maybe need to find manifest binding file
binding = pathlib.Path('PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_CURRENT_NORMATIVE_MANIFEST_BINDING.md').read_text(encoding='utf-8')
print("\n=== BINDING ===")
print(binding)

# Check index file
idx = pathlib.Path('PROJECT_GOVERNANCE/CURRENT_AUTHORITY_INDEX.md')
if idx.exists():
    print("\n=== INDEX EXISTS ===")
    print(idx.read_text(encoding='utf-8')[:2000])

# Check diff from 9ca5289 to HEAD vs post-S0
print("\n=== HEAD diff check ===")
# This is informational - actual git diff already shown: only ENGINEERING file changed, which is outside post-S0 set
# Need to determine if that's a violation - but HEAD is after 9ca5289, not necessarily within same S0 wave?
# The policy says S0 is gen-39 opening; need to check what S0 commit is

# Let's also parse the ledger files if exist
import pathlib as pl
for p in pl.Path('PROJECT_GOVERNANCE/ARE0/QUALIFICATION').glob('*.md'):
    print(p)
