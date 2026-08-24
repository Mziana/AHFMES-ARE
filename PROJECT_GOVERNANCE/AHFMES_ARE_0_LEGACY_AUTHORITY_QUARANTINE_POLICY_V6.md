# AHFMES ARE-0 — Legacy Authority Quarantine Policy V6

Status: **NORMATIVE CLOSURE / SUBJECT-BOUND WHOLE-BLOB QUARANTINE / EXACT JOURNAL-COMPATIBLE QAO / NO MACHINE-RIGHT GRANT / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Composition / replacement

Immutable base:

```text
BASE_QUARANTINE_POLICY_V5_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_LEGACY_AUTHORITY_QUARANTINE_POLICY_V5.md
BASE_QUARANTINE_POLICY_V5_GIT_BLOB_SHA = efea8681e95f3945ddf1e75ef9c1044f2d5d4205
```

V5 subject-bound whole-blob quarantine, stable-manifest resolution, anti-laundering and post-S0 lineage semantics remain in force except the exact post-S0 qualification-output set is narrowed/replaced below to reconcile mandatory project-journal continuity with qualification immutability.

No wildcard, directory exemption, journal-family exemption, session-log exemption or implementation-defined path class is created.

## 1. Sole current-manifest resolver

Unchanged from V5.

For exact repository subject `S`:

```text
CURRENT_MANIFEST_BINDING_PATH
= PROJECT_GOVERNANCE/AHFMES_ARE_0_CURRENT_NORMATIVE_MANIFEST_BINDING.md

M(S)
= SUBJECT_BOUND_CURRENT_NORMATIVE_MANIFEST(S)
```

Missing, ambiguous, stale, conflicting or non-current binding/manifest resolution => qualification FAIL CLOSED. No historical manifest fallback exists.

## 2. Subject-bound whole-blob theorem

Unchanged from V5.

For exact frozen pre-pass subject `S0` after all normative corrections and before qualification-output writes:

```text
G0 = every recursive Git blob under PROJECT_GOVERNANCE/ in S0
N0 = exact normative-member path set declared by M(S0)
U0 = G0 - N0
```

Every exact `U0` path/blob instance has:

```text
CURRENT_MACHINE_AUTHORITY = NONE
CURRENT_CLOSURE_AUTHORITY = NONE
CURRENT_AUDIT_RULE_AUTHORITY = NONE
CLASSIFICATION = WHOLE_BLOB_HISTORICAL_QUARANTINE
```

No current normative semantic dependency may require `U0` as authority.

## 3. Exact S0 evidence

SA-11 remains required to bind one exact S0, exact S0/tree/governance subtree, non-truncated recursive enumeration, exact binding, exact resolved manifest, exact member set/count, exact normative candidate tree root and proof that no current normative semantic dependency requires U0 authority.

## 4. Exact post-S0 qualification-output set — nine paths only

After `S0`, only the following **nine exact paths** may be added or changed without changing the inspected input subject:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_SA11_WHOLE_BLOB_QUARANTINE_LEDGER_V1.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_LEGACY_AUTHORITY_QUARANTINE_RECORD_V3.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_INTERNAL_IMPACT_AUDIT_RECORD_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_CLEAN_PASS_1_RECORD_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_CLEAN_PASS_2_RECORD_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_REGRESSION_R7_R8_R9_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_FINAL_CONSISTENCY_RECORD_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_QUALIFICATION_ROOT_RECORD_V2.md
PROJECT_JOURNAL/DIARY/2026-08-22-ARE-EXT2-081-01-ROLLBACK-CORRECTION.md
```

Define:

```text
QAO8 = the first eight PROJECT_GOVERNANCE qualification evidence/status paths
JQO1 = the one exact PROJECT_JOURNAL path above
POST_S0_OUTPUT_SET = QAO8 union JQO1
```

No wildcard/prefix/suffix/version-family/date-family/similarly named journal path is exempt.

Any post-S0 repository change outside these exact nine paths invalidates qualification lineage. Any normative-member change requires a new S0 and resets clean-pass count to zero.

## 5. Journal qualification-output semantics

`JQO1` exists only to satisfy mandatory project continuity and chronology during qualification.

For every post-S0 state:

```text
JQO1_CURRENT_MACHINE_AUTHORITY = NONE
JQO1_CURRENT_CLOSURE_AUTHORITY = NONE
JQO1_CURRENT_AUDIT_RULE_AUTHORITY = NONE
JQO1_NORMATIVE_MEMBER = FALSE
JQO1_CAN_REPAIR_NORMATIVE_SEMANTICS = FALSE
JQO1_CAN_OVERRIDE_QAO_EVIDENCE = FALSE
JQO1_CAN_GRANT_PASS_OR_CLOSURE = FALSE
JQO1_CAN_CHANGE_S0_OR_NORMATIVE_ROOT = FALSE
```

Journal prose may record observed commits, tests, findings, blockers, dispositions, chronology and next action. It cannot be used as a prerequisite, fallback, resolver, proof-substitute or semantic completion mechanism for any current normative rule.

If any current normative member or qualification adjudication relies on journal prose as authority rather than independently verifiable Git/QAO evidence, qualification FAILS.

The journal may summarize QAO evidence but cannot replace it.

## 6. Journal update discipline

For every material repository qualification change after S0, the exact JQO1 path MUST be updated as a separate chronology/output write in the same qualification wave.

This requirement does not authorize any other journal path.

A missing required journal checkpoint is a project-process failure and blocks dispatch readiness, but it does not alter normative machine semantics or retroactively change S0.

Journal entries MUST identify, where applicable:

```text
exact branch
exact relevant commit/blob identities
changed paths
verification/audit performed
current disposition/blockers
firewall
next exact action
```

They MUST distinguish reported/internal status from external acceptance.

## 7. Whole-blob ledger requirement

Unchanged except Policy V6 is the current policy resolved through M(S0).

The SA-11 ledger must bind S0, governance subtree, stable binding, manifest path/blob/member count, normative candidate tree root, universal `G0-N0` quarantine and proof that no detector vocabulary or exception list weakens whole-blob quarantine.

The exact JQO1 path is outside `PROJECT_GOVERNANCE/`; its post-S0 exemption does not alter G0/N0/U0 and grants it no normative authority.

## 8. Post-S0 candidate lineage theorem

A final internal candidate `C` qualifies only if:

```text
S0 is ancestor of C
all changed repository paths S0..C are members of exact POST_S0_OUTPUT_SET
M(C) path/blob/member set == M(S0)
stable-binding bytes at C == S0
all current normative-member bytes at C == S0
NORMATIVE_CANDIDATE_TREE_ROOT(C) == NORMATIVE_CANDIDATE_TREE_ROOT(S0)
no QAO8 or JQO1 output is used as machine/closure/audit-rule authority
JQO1 has the required material-change chronology through C
```

A candidate may contain multiple sequential changes to the same exact allowed path. Path-set admissibility does not waive evidence correctness or chronology checks.

Any later normative correction requires a new S0 and complete qualification reset.

## 9. Clean-pass immutability

After CP1:

```text
binding change
OR current manifest path/blob/member change
OR any current normative-member byte change
=> normative root changes or inspected semantics change
=> clean-pass count = 0
=> old S0/QAO qualification lineage invalid for dispatch
```

Post-CP1 writes confined to QAO8/JQO1 do not change the inspected normative subject, provided neither is used as normative/audit-rule authority.

## 10. Anti-laundering

```text
historical manifest self-claims CURRENT -> U0 -> zero authority
higher-version unbound manifest -> U0 -> zero authority
old audit/PASS/READY/implementation authority -> U0 -> zero authority
QAO8 tries to grant current semantics -> invalid / zero authority
JQO1 tries to grant/repair/override current semantics -> invalid / zero authority
JQO1 path alias/sibling/date variant -> not exempt
current normative document relies on quarantined blob or JQO1 prose as authority -> qualification FAIL
post-S0 edit outside exact POST_S0_OUTPUT_SET -> qualification lineage FAIL
```

## 11. Minimality / no branch or journal proliferation

This V6 change authorizes no new branch and no new journal location. It reuses exactly the existing project journal checkpoint path already required by project continuity discipline.

Future qualification waves that require a different journal path MUST receive an explicit normative policy revision before S0; no date/session inference is permitted.

## 12. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
AHFMES-NEW = CLOSED
W2/W3 = CLOSED
```
