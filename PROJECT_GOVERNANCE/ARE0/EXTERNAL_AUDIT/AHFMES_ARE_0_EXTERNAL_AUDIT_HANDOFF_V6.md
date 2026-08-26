# AHFMES ARE-0 — External Audit Handoff V6

Status: **BINDER-ONLY EXTERNAL RE-AUDIT HANDOFF / ZERO MACHINE-CLOSURE-AUDIT-RULE AUTHORITY / NO IMPLEMENTATION AUTHORITY**
Effective date: **2026-08-22**

## Exact immutable audit subject

```text
AUDIT_SUBJECT_CANDIDATE_SHA = 63ca962729facb6aaed322a97689fb890b6dac66
QUALIFICATION_S0_SHA = 91d5d06045f37c50dfdbcb51a7aa6fc58ad4db03
NORMATIVE_ROOT = 5fe526ab4438abb4233e527873f79f99e28e06445424b0b2399e421b94ce7b8e
CURRENT_MANIFEST = V17
NORMATIVE_MEMBER_COUNT = 61
CURRENT_MATRIX = V13
CURRENT_INVENTORY = V13
CURRENT_POLICY = V5
CURRENT_PROTOCOL = V18
CURRENT_CORRECTION = V17
```

External auditors must audit the exact immutable candidate SHA above, not this binder commit and not a moving branch head.

## Candidate construction proof

Independent Git comparison from S0 to candidate returned:

```text
S0_IS_ANCESTOR = YES
S0_TO_CANDIDATE_COMMITS = exactly 6
CHANGED_PATH_COUNT = exactly 8
ALL_CHANGED_PATHS = exact Policy-V5 QAO set
NON_QAO_PATH_CHANGED = NO
NORMATIVE_PATH_CHANGED = NO
```

The eight changed QAO paths are:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_SA11_WHOLE_BLOB_QUARANTINE_LEDGER_V1.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_LEGACY_AUTHORITY_QUARANTINE_RECORD_V3.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_INTERNAL_IMPACT_AUDIT_RECORD_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_QUALIFICATION_ROOT_RECORD_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_CLEAN_PASS_1_RECORD_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_CLEAN_PASS_2_RECORD_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_REGRESSION_R7_R8_R9_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_FINAL_CONSISTENCY_RECORD_V2.md
```

Final consistency construction is self-reference-free: the final QAO record does not contain the candidate commit SHA that contains it; candidate validity was established afterward through Git ancestry/diff.

## Internal qualification evidence

```text
SUBJECT_BOUND_SA11_QUARANTINE = PASS
NORMATIVE_ROOT_RECOMPUTED_INDEPENDENTLY_TWICE = MATCH
CLEAN_PASS_1 = PASS
CLEAN_PASS_2 = PASS
SAME_NORMATIVE_ROOT = YES
FORMAL_PERMANENT_REGRESSION = 240 / 240 PASS
  R7 = 26 / 26
  R8 = 40 / 40
  R9 = 174 / 174
NEW_INTERNAL_REPRODUCIBLE_BLOCKER = NONE FOUND
NEW_R9_ROOT = NONE
```

Historical external candidate `cbb7907...` remains `CHANGES_REQUIRED`; no historical acceptance credit is transferred automatically to this successor candidate.

## Material correction surfaces for external attack

External re-audit should independently attack at minimum:

```text
1. target-instance-scoped bootstrap authorization and sealed issuance slot
2. static-vs-final-derived generation-0 field partition
3. late pregenesis reconciliation -> drainable SystemGenesis
4. materiality / one semantic coverage opportunity
5. Bootstrap-Import vs Bootstrap-Coverage-Audit independence
6. frozen source/capture contract and omission resistance
7. LOCAL_CAS vs EXTERNAL_FINALIZABLE vs EXTERNAL_NONFINALIZABLE source treatment
8. canonical multi-source finalized cut vector / <=cut correction / >cut advance / causal closure
9. Challenge / revalidation / rollback adverse-history resistance
10. capital mutation boundary / broker-native mutation / uncertainty reservation
11. subject-bound stable manifest routing and whole-blob quarantine
12. S0->candidate six-commit/eight-QAO construction and candidate self-reference freedom
```

One reproducible legal exploit/deadlock is sufficient for `CHANGES_REQUIRED`.

## External adjudication boundary

This binder requests independent whole-architecture external adjudication only. Neither internal clean passes, regression, candidate construction nor this binder grants downstream authority.

Required project firewall remains:

```text
ARE-0 CLOSED = NO pending required external adjudication
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```

PR #20 must remain OPEN / DRAFT / UNMERGED while external re-audit is pending.

## Future Human–ARE interface

Preserve the future conversational Human–ARE operator/research interface for explanation, status, research requests, hypotheses, simulation, audit inspection and governed intent capture. Chat has no ambient broker/capital authority and cannot bypass proof, Safety, scientific, selection, mutation-boundary, reconciliation or execution gates.
