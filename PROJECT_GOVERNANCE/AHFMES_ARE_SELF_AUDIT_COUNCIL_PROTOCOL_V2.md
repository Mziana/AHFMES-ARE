# AHFMES ARE — Self-Audit Council Protocol V2

Status: **MANDATORY PRE-EXTERNAL-AUDIT GOVERNANCE / WHOLE-TREE FREEZE DISCIPLINE / STATELESS NORMATIVE PROTOCOL / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 1. Purpose

This protocol governs ARE-0 closure review. It preserves the 12-role adversarial council, concrete exploit requirement, correction-impact re-runs and two-consecutive-clean-pass rule, and requires integrated corrections plus exact whole-tree identity.

It contains no mutable clean-pass/candidate/external-audit progress state. Those facts are recorded in non-normative audit/orientation records.

The council cannot itself close ARE-0, authorize implementation, open P001, authorize production or merge PR #20.

## 2. Hard sequencing — large integrated design, then audit

```text
FINDINGS NORMALIZED
        ↓
ONE COHERENT INTEGRATED SEMANTIC CORRECTION WAVE
        ↓
ALL NORMATIVE AUTHORITY BYTES SYNCHRONIZED
        ↓
IMPACT ATTACK AGAINST EXACT INTEGRATED BYTES
        ↓
IF BLOCKED:
  clean count remains external-state 0
  normalize all findings
  next correction is another integrated wave

IF IMPACT-CLEAN:
  freeze exact NORMATIVE_CANDIDATE_TREE_ROOT R
        ↓
FULL COUNCIL CLEAN PASS #1 ON R
        ↓
NO NORMATIVE WRITE
        ↓
FULL COUNCIL CLEAN PASS #2 ON SAME R
        ↓
R7 + R8 + R9 REGRESSION ON SAME R
        ↓
CROSS-DOCUMENT CONSISTENCY ON SAME R
        ↓
FREEZE SELF-REFERENCE-FREE CANDIDATE
        ↓
ONE BINDER-ONLY CHILD
        ↓
EXTERNAL WHOLE-ARCHITECTURE AUDIT
```

Forbidden closure workflow:

```text
patch root A -> audit -> patch root B -> audit -> patch root C -> audit
```

Reasoning/drafting may occur before the integrated commit; closure evidence attaches only to complete integrated bytes.

## 3. Council roles

```text
SA-01 State-Machine Totality
SA-02 Authority / Principal SoD
SA-03 Evidence / Holdout / Legacy Provenance
SA-04 Search-Debt / Multiplicity
SA-05 Champion Selection / Promotion / Rollback
SA-06 Temporal / Information-Time / Replay
SA-07 Capital Safety / Concurrency
SA-08 Protective / Recovery / Broker Semantics
SA-09 Genesis / Bootstrap / Migration
SA-10 Scientific-Capital Boundary
SA-11 Cross-Document Consistency
SA-12 Adversarial Integrator / Closure Skeptic
```

Independent first-pass briefs, common-control skepticism, concrete paths and “one reproducible blocker overrides PASS” remain mandatory.

## 4. R9 attack overlays

### SA-01 / SA-09

```text
bootstrap trust depending on generation-#0 authority
same epoch conflicting payload
partial import crash / concurrent bootstrap / post-genesis reuse
Challenge guard non-totality under UNKNOWN
POSTACCESS wrapper revival / debt laundering / queue deadlock
revalidation opportunity state not drainable
mutation-boundary generation conflict/reuse
```

### SA-05

```text
winner known before lifecycle bundle
vacuous revalidation policy
multiple outstanding revalidation triggers / scheduler ordering
missing proof without terminal settlement
Governor choosing scientific revalidation result
FAIL/NEGATIVE followed by routine PASS revival
UNKNOWN/expiry recovery used as regime-switching
stale displaced fallback
manufactured rollback cause / outcome-aware maintenance timing
rollback loops / fallback absence
```

### SA-07 / SA-08

Attack boundary validity at:

```text
before authorization
after authorization before send
after send before accept
after accept before partial/fill
after partial before terminal settlement
after settlement before local observation
```

Test manual/concurrent/broker-native sources, exact input-frontier CAS, standing protective polarity and worst-case reservation retention.

### SA-06 / SA-11

```text
source-origin / capture / canonicalization gaps
same-key completeness retry laundering
successor PASS laundering prior required gap
DecisionInput PASS substituted for broker/exposure/Safety completeness
common-controlled capture self-attestation
imported historical status leaking current authority
normative document carrying dynamic gate status after Pass #1
non-Matrix normative-tree drift
root serialization ambiguity / manifest self-reference
orientation record accidentally supplying authority
```

## 5. Mandatory finding format

Every blocker must include:

```text
finding_id
auditor role
severity
preconditions
exact legal exploit/deadlock/replay path
canonical clause/absence
why fail-closed does not already stop it
scientific/authority/capital consequence
minimal correction class
impacted roots/domains
required re-auditors/regression scenarios
```

Concern without a reproducible legal path is not a blocker.

## 6. Normative authority path set

The complete current machine-authority path set is declared by:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V1.md
```

The manifest is itself normative. It lists paths/roles, not its own object ID, avoiding self-reference.

`CURRENT_AUTHORITY_INDEX.md`, audit records, PR/Issue metadata, handoffs and journals are outside the machine-authority set and cannot add/widen rights.

Before any Clean Pass #1, SA-11 must prove no unlisted file materially claims current authority; any such claim must be either added to the manifest before root freeze or explicitly downgraded to historical/orientation status.

## 7. Exact normative tree-root serialization

At final normative-byte freeze, obtain for every manifest-declared path:

```text
path_bytes = exact UTF-8 repository path bytes
blob_id_bytes = lowercase ASCII Git blob object ID returned by repository
length_bytes = lowercase decimal ASCII exact file-byte length, no leading zero except "0"
```

Sort tuples by raw `path_bytes` lexicographic byte order.

For each tuple serialize exactly:

```text
"P" + decimal_ascii(len(path_bytes)) + ":" + path_bytes
+ "S" + decimal_ascii(len(blob_id_bytes)) + ":" + blob_id_bytes
+ "L" + decimal_ascii(len(length_bytes)) + ":" + length_bytes
+ "\n"
```

No whitespace, Unicode normalization, path normalization, JSON reserialization or alternate newline is permitted beyond the exact grammar above.

Then:

```text
NORMATIVE_CANDIDATE_TREE_ROOT = SHA-256(concatenation of all serialized tuple records)
```

The manifest itself is included through its actual Git blob ID discovered from the frozen tree; it need not contain its own ID.

The resulting tuple list and root are written to a whitelisted non-normative root record outside R. Pass #1, Pass #2, regression and final consistency bind the exact same R.

## 8. Post-Pass-#1 write discipline

```text
ANY byte/path change in the Normative Authority Manifest set after Pass #1
= clean-pass sequence reset to 0
```

Matrix V2 byte change is always a reset. No editorial/status/semantic-equivalence exception exists.

The normative files are intentionally **stateless with respect to audit progress**, so they do not need status edits after Pass #1.

Whitelisted non-normative result/orientation surfaces may change without changing R only because they cannot add machine authority. Examples:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_NORMATIVE_ROOT_RECORD.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_SELF_AUDIT_COUNCIL_RUN_R9.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_REGRESSION_RECORD.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_FINAL_CONSISTENCY_RECORD.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V1.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_IMPACT_ATTACK_RECORD_V2.md
CURRENT_AUTHORITY_INDEX.md
PR / Issue metadata
later external audit/binder metadata
```

If such a record attempts to define a new object, edge, writer, predicate authority, scientific privilege or capital privilege, that attempted privilege is invalid.

## 9. Clean-pass semantics

```text
FULL COUNCIL PASS #1 ON R = no new reproducible blocker
FULL COUNCIL PASS #2 ON SAME R = no new reproducible blocker
```

Any new blocker or normative-root change resets the sequence externally to zero.

No pass result is written into the normative set.

## 10. Permanent regression set

All historical R7/R8 permanent families remain mandatory.

R9-X01..R9-X33 remain mandatory from earlier R9 correction/impact work.

Additional exact scenarios:

```text
R9-X34 ACCESS_UNKNOWN at next Challenge slot -> conservative POSTACCESS terminal; queue can advance; no proof authority
R9-X35 NO_ACCESS_PROVEN + ELIGIBILITY_UNKNOWN -> conservative PREVALIDATION terminal; no queue deadlock
R9-X36 two revalidation triggers outstanding -> frozen canonical order; later slot cannot leapfrog earlier
R9-X37 revalidation FAIL/NEGATIVE -> REVOKED; later routine PASS cannot restore same selection generation
R9-X38 SUSPENDED for UNKNOWN/expiry -> only prospectively authorized recovery opportunity may restore CURRENT
R9-X39 Governor receives negative/unknown ScientificAdjudication -> cannot choose PASS; deterministic disposition root controls
R9-X40 successor completeness PASS on later interval -> unresolved prior required gap remains adverse
R9-X41 exact authoritative backfill/removal of dependency -> only then prior completeness defect may be positively resolved
R9-X42 mutation-boundary source/control head advances after audit read but before registry CAS -> stale transaction loses
R9-X43 after Clean Pass #1, progress status changes only in non-normative record; normative bytes stay identical
R9-X44 two independent root calculators using exact length-prefixed grammar -> identical NORMATIVE_CANDIDATE_TREE_ROOT
```

No scenario is deleted merely because a later wave passes.

## 11. Mandatory cross-root composition

At minimum:

```text
R9-01 x R9-03 bootstrap premises / authority-manifest inclusion
R9-02 x R9-04 postaccess evidence lineage interacting with later revalidation evidence
R9-04 x R9-05 revalidation revoke/suspend interacting with rollback
R9-04 x R9-06 live exposure after reliance loss with mutation-boundary uncertainty
R9-05 x R9-06 rollback selection while external state changes
R9-06 x R9-07 boundary source coverage relying on broker/exposure completeness
```

Root-isolated correctness is insufficient.

## 12. Council output

Each run records in non-normative immutable evidence:

```text
exact subject commit/tree
exact NORMATIVE_CANDIDATE_TREE_ROOT when frozen
manifest/blob tuple list
council version/roster
per-auditor dispositions
findings/reproductions
root normalization
impact graph
regression results
clean-pass sequence
known unknowns
```

Allowed internal dispositions:

```text
BLOCKED_INTERNAL
CORRECTION_REQUIRED
FULL_COUNCIL_PASS_1
READY_TO_FREEZE_AFTER_PASS_2
READY_TO_FREEZE_FOR_EXTERNAL_AUDIT
```

Never `ARE0_CLOSED` or `IMPLEMENTATION_AUTHORIZED`.

## 13. Static protocol boundary

This protocol grants no:

```text
ARE-0 closure
implementation authority
P001 substantive research authority
production authority
PR merge authority
```

Current clean-pass count, exact correction-wave SHA, candidate SHA and external-audit state are deliberately outside this normative protocol.