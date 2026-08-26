# AHFMES ARE-0 — Qualification Root Record V2

Status: **QAO EVIDENCE ONLY / ZERO MACHINE-CLOSURE-AUDIT-RULE AUTHORITY**  
Effective date: **2026-08-22**

## Frozen normative subject

```text
S0 = 435f9dd975a0b7f3548085884afaff2a483e5546
S0_ROOT_TREE = ed48aadf0932b7fbf8118a35ddee58fa413982ed
PROJECT_GOVERNANCE_SUBTREE = 584b29c36c89e6dc8c64b890ca21a964fe2b035c
RECURSIVE_ENUMERATION_TRUNCATED = false
STABLE_BINDING_BLOB = 8492584e7bf981fbabec40217cd6b83f9e8d2c18
MANIFEST_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V31.md
MANIFEST_BLOB = 6eb1e30d1d756a871653b645747f8daa99478a10
MANIFEST_MEMBER_COUNT = 111
MANIFEST_SELF_BYTE_LENGTH = 16249
```

## Mandatory pre-root object-identity gate

```text
DECLARED_MEMBER_COUNT = 111
UNIQUE_PATH_COUNT = 111
NON_SELF_COUNT = 110
NON_SELF_CANONICAL_LOWERCASE_40HEX = 110/110
NON_SELF_PATH_EXISTS_AT_EXACT_S0 = 110/110
NON_SELF_DECLARED_SHA_EQUALS_EXACT_S0_BLOB_SHA = 110/110
SELF_IDENTITY = literal SELF
PREFIX_EXPANSION = NOT USED
UI_TRUNCATION_REPAIR = NOT USED
CROSS_REF_OR_MOVING_REF_SUBSTITUTION = NOT USED
```

Any malformed, abbreviated, case-mutated, prefix-only, missing, cross-subject or non-matching member identity fails before root construction.

## Exact V31 serialization

```text
for each non-self member:
  <UTF-8 path>\0<exact lowercase Git blob SHA>\0<decimal UTF-8 byte length>\n

for manifest self member:
  <UTF-8 manifest path>\0SELF\0<decimal manifest UTF-8 byte length>\n
```

All 111 tuples are sorted lexicographically by raw UTF-8 path bytes, concatenated without additional separators, then SHA-256 hashed.

## Independent recomputation

Two independent implementations over the exact S0 path/object/length evidence returned:

```text
COMPUTATION_A_METHOD = materialize canonical tuples -> raw-byte sort -> one-shot SHA256
COMPUTATION_A = 2279eb5ede41eb91b587387f0e9d2b1981b43afd500d9cb12dd8c3ad18e56db5

COMPUTATION_B_METHOD = raw-byte path sort -> incremental tuple streaming -> SHA256
COMPUTATION_B = 2279eb5ede41eb91b587387f0e9d2b1981b43afd500d9cb12dd8c3ad18e56db5

MATCH = YES
SERIALIZED_BYTE_LENGTH = 12647
```

Therefore:

```text
NORMATIVE_CANDIDATE_TREE_ROOT = 2279eb5ede41eb91b587387f0e9d2b1981b43afd500d9cb12dd8c3ad18e56db5
```

## Qualification invariant

All current 111 member identities/bytes are frozen at S0 for clean-pass continuation. Policy V5 QAO-only writes do not change the normative root because QAO outputs have zero current machine/closure/audit-rule authority and are not Manifest V31 members.

Any stable-binding byte change, current-manifest path/blob/member change, normative-member change, same-subject object mismatch or post-S0 non-QAO branch write invalidates this qualification lineage and resets clean-pass credit as applicable.

At creation of this record:

```text
IMPACT = CLEAN
SA11 = PASS
CP1 = NOT STARTED
CP2 = NOT STARTED
PERMANENT_REGRESSION = 0/344
NORMATIVE_WRITE_AFTER_S0 = NO
READY_TO_EXTERNAL_AUDIT = NO
```

This record grants no ARE-0 closure, implementation, P001, production, broker/capital execution, live/paper trading or PR-merge authority.