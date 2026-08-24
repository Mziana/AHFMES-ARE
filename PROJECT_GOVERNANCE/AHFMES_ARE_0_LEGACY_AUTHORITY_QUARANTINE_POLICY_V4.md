# AHFMES ARE-0 — Legacy Authority Quarantine Policy V4

Status: **NORMATIVE CLOSURE / WHOLE-BLOB LEGACY QUARANTINE / SELF-REFERENCE-FREE QUALIFICATION / NO MACHINE-RIGHT GRANT / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable base:

```text
BASE_QUARANTINE_POLICY_V3_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_LEGACY_AUTHORITY_QUARANTINE_POLICY_V3.md
BASE_QUARANTINE_POLICY_V3_GIT_BLOB_SHA = 1708f9cd5bc7806f9506d9fc9ad0dba1df890937
```

V3 QIF/QAO separation remains conceptually valid, but V3 §§3-8 trigger/claim inspection is replaced by the stronger whole-blob theorem below. V2/V1 trigger vocabulary is no longer a qualification primitive.

## 1. IA-E03 correction theorem — no detector dependence

A finite trigger vocabulary can miss semantically equivalent authority claims. Qualification therefore must not depend on detecting individual phrases.

For exact pre-pass subject `S0`, let:

```text
G0 = every recursive Git blob under PROJECT_GOVERNANCE/ in S0
N0 = exact current Manifest V11 normative-member set in S0
U0 = G0 - N0
```

Then every exact path/blob instance in `U0` is unconditionally assigned:

```text
CURRENT_MACHINE_AUTHORITY = NONE
CURRENT_CLOSURE_AUTHORITY = NONE
CURRENT_AUDIT_RULE_AUTHORITY = NONE
CLASSIFICATION = WHOLE_BLOB_HISTORICAL_QUARANTINE
```

This disposition covers every byte and every claim in the blob, whether detected, missed, ambiguous, opaque, binary-looking, stylistically novel, or later reinterpreted. No per-claim exception exists.

An unlisted blob cannot repair, supplement, override or narrow missing current semantics. If a current normative member semantically depends on an unlisted path as authority, qualification fails; blanket quarantine cannot legalize that dependency.

## 2. Exact pre-pass subject

SA-11 is evaluated against one exact immutable pre-pass Git commit `S0` after the final normative correction and before any qualification-output write.

The whole recursive `PROJECT_GOVERNANCE` Git subtree of `S0` is the coverage commitment. Git subtree identity plus Manifest V11 membership determines `G0`, `N0` and therefore `U0` without content-sensitive classification.

Required positive evidence:

```text
exact S0 commit SHA
exact S0 root tree SHA
exact PROJECT_GOVERNANCE subtree SHA
Git reports each recursively enumerated inspected subtree as non-truncated
exact current stable-binding blob
exact Manifest V11 path/blob at S0
exact 38-member normative set N0
proof no current normative semantic dependency requires U0 authority
```

## 3. Exact finite qualification-audit-output set (QAO)

Only the following eight exact paths may be added or changed after `S0` without changing the inspected input subject:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_SA11_WHOLE_BLOB_QUARANTINE_LEDGER_V1.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_LEGACY_AUTHORITY_QUARANTINE_RECORD_V3.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_INTERNAL_IMPACT_AUDIT_RECORD_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_CLEAN_PASS_1_RECORD_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_CLEAN_PASS_2_RECORD_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_REGRESSION_R7_R8_R9_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_FINAL_CONSISTENCY_RECORD_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_QUALIFICATION_ROOT_RECORD_V2.md
```

These paths are evidence/status only and have zero machine/closure/audit-rule authority. No wildcard, prefix, suffix, version-family or similarly named path is exempt.

Any post-`S0` change outside these exact eight paths invalidates the qualification lineage. Any normative-member change additionally resets clean-pass credit to zero.

## 4. Whole-blob quarantine ledger

The SA-11 ledger need not reproduce every byte or every phrase in `U0`. It must bind the exact set by Git identity:

```text
S0 commit SHA
PROJECT_GOVERNANCE subtree SHA
Manifest V11 path/blob
normative-member count and root
WHOLE_BLOB_QUARANTINE applies universally to every G0-N0 member
no exception list
no detector vocabulary
no content-based downgrade/upgrade path
```

An auditor can independently enumerate `G0-N0` from `S0`; an omitted path in prose cannot escape the set theorem.

## 5. Post-S0 lineage theorem

A final internal qualification candidate `C` may descend from `S0` only through commits whose changed paths are a subset of the exact QAO set in §3.

Required final comparison:

```text
S0 is ancestor of C
all changed paths S0..C are exact QAO paths
current Manifest V11 member bytes at C == S0
current stable-binding bytes at C == S0
NORMATIVE_CANDIDATE_TREE_ROOT(C) == NORMATIVE_CANDIDATE_TREE_ROOT(S0)
no QAO output is referenced as machine/closure/audit-rule authority
```

This history-based proof replaces V3's need for an audit output to enter its own content-addressed input projection.

## 6. Anti-laundering

```text
unlisted file claims CURRENT/NORMATIVE/APPROVED/READY/AUTHORIZED -> still whole-blob quarantined
unlisted higher-version manifest -> still whole-blob quarantined
legacy implementation authority -> still whole-blob quarantined for ARE-0 current authority
historical clean-pass/audit record -> still whole-blob quarantined
QAO file attempts to create machine right -> invalid; zero authority
current normative document relies on quarantined blob as semantic authority -> qualification FAIL
post-S0 non-QAO governance edit -> qualification lineage FAIL
post-S0 non-governance edit -> candidate integrity FAIL unless separately and explicitly permitted by Protocol V12; default is deny
```

## 7. Static firewall

This policy grants no machine transition, writer, scientific privilege, capital privilege, ARE-0 closure, implementation, P001 substantive research, production, live/paper trading or PR-merge authority.
