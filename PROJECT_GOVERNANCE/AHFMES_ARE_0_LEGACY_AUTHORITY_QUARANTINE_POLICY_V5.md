# AHFMES ARE-0 — Legacy Authority Quarantine Policy V5

Status: **NORMATIVE CLOSURE / SUBJECT-BOUND WHOLE-BLOB QUARANTINE / STABLE-MANIFEST RESOLUTION / NO MACHINE-RIGHT GRANT / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Composition / replacement

Immutable base:

```text
BASE_QUARANTINE_POLICY_V4_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_LEGACY_AUTHORITY_QUARANTINE_POLICY_V4.md
BASE_QUARANTINE_POLICY_V4_GIT_BLOB_SHA = 980babdf448b89841e2bf964ac1cba3c7550a702
```

V4 whole-blob quarantine, exact finite QAO set, post-S0 lineage theorem and anti-laundering principles remain fully in force. V4's literal `Manifest V11`, `38-member`, and manifest-generation-specific routing references are **REPLACED IN FULL** by this V5 subject-bound resolver.

No current manifest generation number or member count is hard-coded in the quarantine theorem.

## 1. Sole current-manifest resolver

For exact repository subject `S`, define:

```text
CURRENT_MANIFEST_BINDING_PATH
= PROJECT_GOVERNANCE/AHFMES_ARE_0_CURRENT_NORMATIVE_MANIFEST_BINDING.md

M(S)
= SUBJECT_BOUND_CURRENT_NORMATIVE_MANIFEST(S)
```

`M(S)` is valid only through the exact stable binding and the current Protocol's binding-integrity rules. Policy V5 has **no independent manifest selector** and no fallback to a historical manifest.

Missing, ambiguous, stale, conflicting or non-current binding/manifest resolution => quarantine qualification FAIL CLOSED.

## 2. Subject-bound whole-blob theorem

For exact frozen pre-pass subject `S0` after all normative corrections and before qualification-output writes:

```text
G0 = every recursive Git blob under PROJECT_GOVERNANCE/ in S0
N0 = exact normative-member path set declared by M(S0)
U0 = G0 - N0
```

Every exact path/blob instance in `U0` is unconditionally assigned:

```text
CURRENT_MACHINE_AUTHORITY = NONE
CURRENT_CLOSURE_AUTHORITY = NONE
CURRENT_AUDIT_RULE_AUTHORITY = NONE
CLASSIFICATION = WHOLE_BLOB_HISTORICAL_QUARANTINE
```

This covers every byte/claim regardless of wording, format, status prose, version number, opacity or later interpretation. No per-claim exception exists.

An unlisted blob cannot repair/supplement/override/narrow missing current semantics. A current normative semantic dependency on `U0` as authority is a qualification blocker.

## 3. Exact S0 evidence

SA-11 must bind, for one exact `S0`:

```text
exact S0 commit SHA
exact S0 root tree SHA
exact recursive PROJECT_GOVERNANCE subtree SHA
Git recursive enumeration non-truncated
exact stable-binding path/blob at S0
exact resolved M(S0) path/blob
exact M(S0) member count
exact normative-member set N0
exact normative candidate tree root for N0
proof no current normative semantic dependency requires U0 authority
```

The quarantine policy never substitutes a remembered/historical manifest generation for `M(S0)`.

## 4. Exact qualification-audit-output set (QAO)

Only these eight exact paths may be added or changed after `S0` without changing the inspected input subject:

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

These are evidence/status outputs only and have zero machine/closure/audit-rule authority. No wildcard/prefix/suffix/version-family/similarly named path is exempt.

Any post-S0 change outside these exact eight paths invalidates qualification lineage. A normative-member change additionally resets clean-pass count to zero.

## 5. Whole-blob ledger requirement

The SA-11 whole-blob ledger must bind:

```text
S0
PROJECT_GOVERNANCE subtree SHA
stable-binding blob
M(S0) path/blob/member count
NORMATIVE_CANDIDATE_TREE_ROOT(S0)
WHOLE_BLOB_QUARANTINE universally applies to every G0-N0 member
no detector vocabulary / no exception list
```

An auditor can independently enumerate `G0-N0` from S0. Prose omission of a path cannot escape the set theorem.

## 6. Post-S0 candidate lineage theorem

A final internal candidate `C` qualifies only if:

```text
S0 is ancestor of C
all changed paths S0..C are exact QAO paths
M(C) path/blob/member set == M(S0)
stable-binding bytes at C == S0
all current normative member bytes at C == S0
NORMATIVE_CANDIDATE_TREE_ROOT(C) == NORMATIVE_CANDIDATE_TREE_ROOT(S0)
no QAO output is used as machine/closure/audit-rule authority
```

Any later normative correction requires a new S0 and complete qualification reset.

## 7. Manifest-generation change discipline

Before CP1, a new current manifest generation is legal only as part of an integrated normative correction and must be resolved by the stable binding in the same exact subject.

After CP1:

```text
binding change OR current manifest path/blob/member change
=> normative root changes
=> clean-pass count = 0
=> old S0/QAO qualification lineage invalid for dispatch
```

Policy V5 itself does not need editing merely because a future manifest generation changes; it always resolves current membership through the stable binding.

## 8. Anti-laundering

```text
historical manifest self-claims CURRENT -> U0 -> zero authority
higher-version unbound manifest -> U0 -> zero authority
old audit/PASS/READY/implementation authority -> U0 -> zero authority
QAO tries to grant current semantics -> invalid / zero authority
current normative document relies on quarantined blob -> qualification FAIL
post-S0 non-QAO edit -> qualification lineage FAIL
```

## 9. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
