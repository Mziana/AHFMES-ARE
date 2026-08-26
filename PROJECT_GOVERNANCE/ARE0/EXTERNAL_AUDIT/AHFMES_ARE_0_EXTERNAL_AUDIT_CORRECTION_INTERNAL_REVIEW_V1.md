# AHFMES ARE-0 — External Audit Correction Internal Review V1

Status: **INTERNAL ARCHITECT -> RED-TEAM -> SCIENTIFIC-GOVERNOR REVIEW COMPLETE / EXTERNAL RE-AUDIT REQUIRED / NOT CLOSURE**  
Effective date: **2026-08-20**

## 1. Purpose

This record documents the internal re-attack performed after two external adversarial audits returned `CHANGES_REQUIRED` against the prior normative ARE-0 package.

It is not external acceptance and cannot close ARE-0.

## 2. External blocker normalization

Two audits overlapped heavily. The correction pass normalized them into:

```text
EC-01 state-machine totality and repeatable proof episodes
EC-02 scientific/promotion/deployment orthogonality
EC-03 Problem definition root vs history root
EC-04 total authority ownership + Program/Family authorities
EC-05 family lifetime meta-budget / cross-Program renewal
EC-06 trusted outcome-access closure + search instrumentation
EC-07 EvidenceSnapshot vs attestation / prospective isolation
EC-08 positive unrelatedness theorem
EC-09 decision-relevant mutable state boundary
EC-10 re-audit package integrity
```

## 3. Architect pass

Architect produced:

- `AHFMES_ARE_0_EXTERNAL_AUDIT_CORRECTION_PACKAGE_V1.md`
- `AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V1.md`
- `AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V1.md`

The intent was to correct only external blockers without broadening ARE scope.

## 4. Red-Team pass 1 — authority matrix was only asserted, not total

Attack:

```text
write invariant: "all authority classes must be registered"
but do not actually register every class
```

Result:

```text
BLOCKER FOUND
```

Correction:

- total authority ownership matrix added;
- Program/Family authorities became explicit;
- `A-CAPABILITY` deprecated and split into design/proof/production activation;
- emergency-flat and rollback ownership were bound away from Research.

## 5. Red-Team pass 2 — anonymous authority phrases

Attack searched for phrases equivalent to:

```text
independent authority
execution authority
governance decision
record authority
close-only authority
```

that could let implementation invent a permission class.

Result:

```text
BLOCKER FOUND
```

Correction:

Added/standardized explicit classes including:

```text
A-INTEGRITY-AUDIT
A-ADJUDICATE
A-RECORD-CLOSE
A-CAPABILITY-RETIRE
A-RETIRE
```

and required transition tables to cite registered authority classes.

## 6. Red-Team pass 3 — unregistered authority-sensitive object types

Attack:

Even if Candidate/Experiment/Shadow transitions are exhaustive, an implementation could invent authority-bearing lifecycle semantics in:

```text
ResearchFamilyCharter
ResearchProgram
EvidenceReservation
RelationDecision
SearchNode
PromotionTransaction
DeploymentActivationEpisode
...
```

Result:

```text
BLOCKER FOUND
```

Correction:

Created a closed-world `Authority-Sensitive Object State Totality Register`.

Unregistered object types are data-only and have no transition rights.

## 7. Red-Team pass 4 — capital deactivation and authority revocation remained anonymous

Attack:

```text
ACTIVE deployment -> "explicit deactivation authority"
ISSUED authority -> REVOKED / STALE / EXPIRED
```

without exact semantics.

Result:

```text
BLOCKER FOUND
```

Correction Amendment 001:

```text
A-CAPITAL-DEACTIVATE
A-AUTHORITY-REVOKE
```

and:

```text
EXPIRED/STALE = derived usability predicates
not discretionary authority transitions
```

Program authorization and Family exhaustion semantics were also tightened.

## 8. Red-Team pass 5 — invisible p-hacking

Attack:

```text
Research reads outcome-bearing evidence outside ledger
runs 100,000 private trials
logs only winner
```

Correction now requires:

```text
OUTCOME_ACCESS_CLOSURE_PROOF
TD-SEARCH-INSTRUMENTATION
A-RESEARCH-EVAL
Search Node durable before result disclosure
budget charge durable before result disclosure
unmediated outcome access -> SEARCH_DEBT=UNKNOWN
SEARCH_DEBT=UNKNOWN -> independent promotion-grade proof denied
```

Internal disposition:

```text
ARCHITECTURAL SIDE-CHANNEL RULE = PRESENT
```

Exact OS/process enforcement remains implementation/audit work, but architecture no longer permits self-reported completeness.

## 9. Red-Team pass 6 — Program reset through future data

Attack:

```text
Program P1 fails
future data arrives
Program P2 gets fresh budget
repeat forever until false positive
```

Correction now requires:

```text
ResearchFamilyCharter
FamilyLifetimeLedger
family-level error/evidence spending
A-PROGRAM-RENEW
precommitted renewal mechanism
no statistical fresh slate from new calendar data
```

Internal disposition:

```text
PROGRAM RESET LOOP = ARCHITECTURALLY DENIED
```

Exact numerical error-control method is contract-specific but must be frozen before outcome exposure.

## 10. Red-Team pass 7 — claim relabeling / unrelatedness appeal

Attack:

```text
Claim A contaminates holdout
rename/reframe to Claim B
seek new gate version
obtain UNRELATED_SUPPORTED
reuse old holdout
```

Correction:

`UNRELATED_SUPPORTED` now requires a pre-exposure frozen positive-proof contract and immutable exact-context relation decision.

Outcome-driven appeal cannot clean prior evidence.

Internal disposition:

```text
CLAIM RELABEL HOLDOUT RESET = DENIED BY CONTRACT
```

## 11. Red-Team pass 8 — state adaptation disguises policy mutation

Attack:

```text
source/model artifact unchanged
adaptive_state.weights change after outcomes
DecisionValue consumes weights
capital behavior changes immediately
```

Correction:

`DECISION_RELEVANT_MUTABLE_STATE` is now governed.

The validated Candidate closure must contain the entire online update algorithm, input classes, objective, bounds, state schema, checkpoint/recovery, telemetry and rollback semantics.

Changing those semantics requires descendant proof.

Internal disposition:

```text
UNVALIDATED ONLINE POLICY MUTATION DISGUISED AS STATE = PROHIBITED
```

## 12. Red-Team pass 9 — scientific reject versus deployment veto

Attack:

Candidate has valid bounded scientific claim but current Capital Safety envelope forbids deployment.

Correction:

```text
ScientificDisposition = VALIDATED_BOUNDED
GovernorDisposition   = NO_PROMOTION_SAFETY
```

unless safety feasibility was explicitly part of the primary scientific claim.

Internal disposition:

```text
SAFETY VETO NO LONGER IMPLIES SCIENTIFIC REJECTION
```

## 13. Red-Team pass 10 — emergency authority as hidden strategy

Attack:

Give Research `A-EMERGENCY-FLAT` and let it invoke safety exit whenever its unvalidated model dislikes a trade.

Correction:

`A-EMERGENCY-FLAT` is exclusively Safety/manual-external triggered; Research opinion alone is explicitly insufficient.

Likewise `A-ROLLBACK` is not Research-owned.

Internal disposition:

```text
THINK -> EMERGENCY-FLAT -> ACT BYPASS = DENIED BY AUTHORITY OWNERSHIP
```

## 14. Scientific-Governor internal review

The internal Scientific-Governor checked for scope creep and false closure.

Confirmed:

```text
no P001 hypothesis was introduced
no G2/G1.1 rescue was introduced
no W2/W3 evidence opened
no strategy parameter was selected
no Python implementation authority was granted
no broker/production authority was granted
no PR merge authority was granted
```

The correction remains architecture/governance only.

## 15. Residuals deliberately NOT claimed solved by prose

These are implementation or contract-instance obligations, not reasons to pretend the architecture is already operational:

```text
R1 exact OS/process mechanism implementing outcome-access closure
R2 exact storage transaction implementation for append/CAS atomicity
R3 exact cryptographic/process realization of Governance Root and capabilities
R4 exact numerical family-level error/evidence-spending method per Research Family Charter
R5 exact numerical PromotionGateSpec for a future scientific claim
R6 exact physical embargo/isolation implementation for STRICT_BLIND prospective evidence
R7 exact runtime checkpoint/persistence implementation for DECISION_RELEVANT_MUTABLE_STATE
```

External re-audit must decide whether any of these require more architecture-level specification before ARE-0 closure.

## 16. Internal disposition

```text
INTERNAL CORRECTION REVIEW
= READY FOR EXTERNAL RE-AUDIT

ARE-0 CLOSED
= NO

ARE IMPLEMENTATION
= NOT AUTHORIZED
```

No self-acceptance is claimed.
