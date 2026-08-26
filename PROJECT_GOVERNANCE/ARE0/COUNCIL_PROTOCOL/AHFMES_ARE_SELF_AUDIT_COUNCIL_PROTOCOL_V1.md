# AHFMES ARE — Self-Audit Council Protocol V1

Status: **MANDATORY PRE-EXTERNAL-AUDIT GOVERNANCE / LOGICAL MULTI-AUDITOR REVIEW / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

## 1. Purpose

This protocol strengthens the internal audit stage before any exact closure-candidate SHA is frozen.

It does **not** claim cryptographic, model, or process independence between auditors when one underlying model/service is reused. It creates role-separated logical audit functions with isolated attack briefs, explicit evidence, independent first-pass findings, cross-auditor challenge, and a hard no-freeze gate.

Goal:

```text
FIND MORE DEFECTS INTERNALLY
BEFORE
EXTERNAL CLOSURE ADJUDICATION
```

The council cannot close ARE-0, authorize implementation, open P001, access W2/W3, authorize production, or merge PR #20.

## 2. Hard rule

Before a major-layer external audit:

```text
SELF_AUDIT_COUNCIL_REQUIRED = TRUE
```

A closure candidate may not be frozen merely because Architect + generic Red-Team + internal Governor report no blocker.

The mandatory path becomes:

```text
ARCHITECTURE INTEGRATED
        ↓
SPECIALIST SELF-AUDIT WAVE A
        ↓
CROSS-DOMAIN SELF-AUDIT WAVE B
        ↓
META-ADVERSARIAL CLOSURE SKEPTIC
        ↓
CONSOLIDATED CORRECTION
        ↓
RE-RUN ALL IMPACTED AUDITORS
        ↓
FULL COUNCIL PASS #1 — NO NEW REPRODUCIBLE BLOCKER
        ↓
FULL COUNCIL PASS #2 — NO NEW REPRODUCIBLE BLOCKER
        ↓
END-TO-END SCENARIO SUITE
        ↓
FREEZE EXACT SUBJECT
        ↓
EXTERNAL AUDIT
```

Any new reproducible blocker resets the consecutive-pass count to zero.

## 3. Council size

Baseline council = **12 logical auditors**.

The number is not fixed as an upper bound. A new recurring external finding class creates a dedicated temporary or permanent specialist auditor until the class survives at least two later full closure cycles without reopening.

```text
MINIMUM = 12
MAXIMUM = AS NEEDED
```

## 4. Independence discipline

To reduce groupthink:

1. each Wave-A auditor receives the same frozen subject but a different attack charter;
2. Wave-A first-pass findings are produced before seeing other Wave-A conclusions;
3. every finding must include an executable/concrete exploit, deadlock, privilege, ambiguity or proof-laundering path;
4. auditors may not mark another auditor's finding fixed merely because prose says so;
5. Wave-B auditors attack both architecture and proposed corrections;
6. the Closure Skeptic sees the whole set only after specialist findings are frozen;
7. one auditor's `PASS` never overrides another reproducible blocker;
8. consensus is not evidence;
9. duplicate findings are merged only after root-cause reproduction.

## 5. Wave A — specialist auditors

### SA-01 — State-Machine Totality Auditor

Attack:

```text
missing genesis
multiple genesis
missing terminal
illegal revival
edge without authority
authority without edge
ambiguous guarded transition key
state reachable but not drainable
atomic-group partial commit
```

Special attention:

```text
ProtectiveDependencyPlan genesis
CapitalSafetyContract first generation
manifest embedded-vs-independent roots
Family/Program/Proof/Shadow/Deployment drains
```

### SA-02 — Authority / Principal SoD Auditor

Attack:

```text
same principal wearing two legitimate roles
self-issuance
self-attestation
self-witnessing
privilege-granting governance performed by interested Research principal
issuer/executor collapse
role re-identification
scope aliasing
```

Mandatory pairs include at least:

```text
RESEARCH != VALIDATION
RESEARCH != AUDIT
RESEARCH != SEARCH_INSTRUMENTATION
RESEARCH != PROGRAM_GOVERNANCE for related Family privilege
OPERATIONAL_DECISION != CAPITAL_SAFETY
CAPITAL_SAFETY != EXECUTION
CAPITAL_SAFETY != GOVERNANCE_WITNESS for SafetyContract generation
RUNTIME_ATTESTATION != DECISION/SAFETY/EXECUTION principals whose runtime is attested
```

### SA-03 — Evidence / Holdout / Legacy Provenance Auditor

Attack:

```text
pre-genesis omission
legacy cutoff gap
late-discovered legacy history
renamed/copied evidence reset
exposure not propagated to descendants
prospective evidence contaminated by side channel
holdout oracle through bounded repeated queries
```

Must test:

```text
legacy manifest cutoff T0
scientific activity during (T0, genesis]
late discovery after genesis
legacy debt head advancement
proof/selection/deployment staleness propagation
```

### SA-04 — Search-Debt / Multiplicity Auditor

Attack:

```text
new IDs resetting debt
hidden adaptive generation
winner-only logging
Family split
Problem reformulation
metric/horizon/subgroup rescue
prospective epoch treated as fresh multiplicity wealth
selection opportunity hidden outside Research Family accounting
```

### SA-05 — Champion Selection / Promotion / Rollback Auditor

Attack:

```text
post-outcome challenger-universe definition
nominate winner after non-promotion proofs
Champion-generation reset
promotion without full opportunity coverage
rollback used as performance-driven strategy switching
A↔B adaptive switching under rollback label
stale Champion comparator
```

Hard distinction:

```text
SAFETY/INTEGRITY ROLLBACK
!=
PERFORMANCE-DRIVEN STRATEGY SELECTION
```

### SA-06 — Temporal / Information-Time / Replay Auditor

Attack:

```text
wall-clock used as nonce
caller-selectable information cutoff
same semantic opportunity -> multiple canonical decision keys
input transport replay
state input re-consumption
crash/retry windows
out-of-order broker acceptance
stale proof between authorize/send/accept/fill
```

Hard theorem to test:

```text
NO NEW CANONICAL EVENT
=
NO NEW DECISION OPPORTUNITY
```

### SA-07 — Capital Safety / Concurrency Auditor

Attack:

```text
parallel risk authorization
cross-symbol/account/portfolio overbooking
activation bypassing risk ledger
pending + market combined risk
partial-fill reservation leakage
uncertain exposure omission
Safety-contract migration losing old risk
orphan pending orders
```

Must recompute worst-case aggregate risk from:

```text
ACTUAL
+ BROKER-LIVE CONDITIONAL
+ AUTHORIZED RESERVED
+ EXECUTING RESERVED
+ UNCERTAIN UPPER BOUND
+ NEW ACTION WORST CASE
```

### SA-08 — Protective / Recovery / Broker Semantics Auditor

Attack:

```text
protective order becomes risk-increasing after state change
cancel/replace race
protection choreography created after Safety approval
blind resend of emergency flat
reduce-only capability assumed but not proven
partial fill + timeout + reconnect
broker-native conditional order outliving authority
```

### SA-09 — Genesis / Bootstrap / Migration Auditor

Attack every first-generation special case:

```text
SystemGenesisManifest
PreGenesisScientificState
Family bootstrap reservation
FamilyLifetimeLedger #0
EvidenceGovernanceHead #0
CapitalSafetyContract initial generation
DecisionState #0
registry generation zero
```

Then attack later-generation migration separately. No null-old-root implementation invention is allowed unless an explicit bootstrap mode exists.

## 6. Wave B — cross-domain auditors

### SA-10 — Scientific-Capital Boundary Auditor

Trace every possible route from:

```text
Research / Problem / Hypothesis / Search / Critic / Governor
```

toward:

```text
DecisionInput / DecisionState / DecisionRecord / CapitalAction / broker
```

Attempt direct and indirect `THINK -> ACT` paths through registries, rollback, capability activation, runtime metadata, caches, aliases, Safety migration and recovery channels.

### SA-11 — Cross-Document Consistency Auditor

Compare Matrix, Object Inventory, invariants, workflow, handoff, Authority Index and tracker semantics.

Attack:

```text
Matrix strict / prose loose
prose strict / Matrix missing edge
duplicate authority definitions
object listed but no genesis
genesis listed but object missing
different terminology for same privilege
stale audit subject or stale status
```

Machine source wins, but inconsistency that could cause implementation ambiguity is still a blocker before freeze.

### SA-12 — Adversarial Integrator / Closure Skeptic

This auditor is intentionally broad and pessimistic.

It receives the integrated correction after SA-01..SA-11 and asks:

```text
What can still be done legally that defeats the intended invariant?
What can be renamed to bypass accounting?
What can be retried to mint a second authority/action?
What first-generation object has no legal bootstrap?
What later-discovered fact cannot be reconciled?
What outcome-aware choice is still caller-selectable?
What recovery/rollback path secretly performs policy selection?
What concurrent actions are safe individually but unsafe together?
What same-principal role combination is still self-approval?
```

SA-12 cannot issue ARE closure. Its only positive result is:

```text
NO NEW REPRODUCIBLE BLOCKER FOUND IN THIS PASS
```

## 7. Mandatory finding format

Every blocker must contain:

```text
finding_id
specialist auditor id
severity
preconditions
exact legal exploit/deadlock/replay path
canonical clause/absence that permits it
why fail-closed does not already stop it
scientific/authority/capital consequence
minimal correction class
which other auditors must be re-run
```

A vague concern is not a blocker. A concrete legal exploit is.

## 8. Correction impact graph

Every correction declares impacted domains.

Example:

```text
Decision identity correction
-> re-run SA-01
-> re-run SA-06
-> re-run SA-07 if CapitalAction genesis changes
-> re-run SA-10
-> re-run SA-11
-> always re-run SA-12
```

No correction may be accepted without attacking the correction itself.

## 9. Two-consecutive-pass freeze gate

A candidate is not freeze-eligible after one clean council run.

Required:

```text
FULL COUNCIL PASS N
= no new reproducible blocker

FULL COUNCIL PASS N+1
= no new reproducible blocker
```

Both passes must use the same candidate tree except audit records that do not alter normative semantics.

If normative content changes:

```text
consecutive clean-pass count = 0
```

## 10. Scenario mutation requirement

Each external blocker class becomes a permanent regression scenario.

The current mandatory regression seeds include:

```text
legacy cutoff activity between import and genesis
late legacy discovery after valid proof/deployment
post-outcome challenger coverage-policy choice
same semantic decision with different wall-clock cutoff
ProtectiveDependencyPlan created after Safety authorization
first CapitalSafetyContract with no old root
Safety principal self-witnessing SafetyContract
Research principal self-granting unrelated Family privilege
discretionary performance-driven rollback A↔B
```

Future external findings append to this suite; they are never deleted merely because the current patch passes.

## 11. Council output

Each full run produces one immutable review artifact containing:

```text
exact subject tree/root
council version
auditor roster
per-auditor disposition
findings and exploit paths
duplicate/root-cause normalization
corrections applied
impact re-run map
scenario results
clean-pass sequence number
remaining known unknowns
```

Allowed internal dispositions:

```text
BLOCKED_INTERNAL
CORRECTION_REQUIRED
FULL_COUNCIL_PASS_1
READY_TO_FREEZE_AFTER_PASS_2
READY_TO_FREEZE_FOR_EXTERNAL_AUDIT
```

Never:

```text
ARE0_CLOSED
IMPLEMENTATION_AUTHORIZED
```

## 12. Relationship to external audit

Self-audit exists to reduce external discoveries, not replace independent external adjudication.

External audit remains stronger evidence because a fresh auditor may possess different failure modes and reasoning paths.

Therefore:

```text
SELF AUDIT PASS
!=
EXTERNAL CLOSURE
```

The intended outcome is that external audit mostly revalidates known attack classes instead of discovering basic omitted privilege, temporal, genesis, replay or concurrency mechanics.

## 13. Current hard firewall

```text
ARE-0 CLOSED = NO
ARE implementation = NOT AUTHORIZED
P001 substantive research = NOT AUTHORIZED / ANSWER UNKNOWN
G1 rerun/retune = PROHIBITED
G2 = NOT AUTHORIZED
W2/W3 = CLOSED
production = CLOSED
AHFMES-NEW = CLOSED
PR #20 merge = NOT AUTHORIZED
```
