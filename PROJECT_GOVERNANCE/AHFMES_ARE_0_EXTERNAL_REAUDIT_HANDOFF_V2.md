# AHFMES ARE-0 — External Re-Audit Handoff V2

Status: **READY FOR EXTERNAL RE-AUDIT / NO SELF-ACCEPTANCE / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

## 1. Exact corrected subject

Audit this exact repository tree as the corrected ARE-0 subject:

```text
fdde608d36be7d31748665c056f0a8a831909219
```

This subject is descended from the prior externally-audited package but contains only governance/formalization corrections after that point; it does not authorize or implement ARE runtime code.

## 2. Prior external disposition

The previous subject `5eb148bf8a7aa554e3a762df44247e8c739a4064` received two independent:

```text
CHANGES_REQUIRED
```

reviews.

Canonical summary:

`PROJECT_GOVERNANCE/AHFMES_ARE_0_EXTERNAL_AUDIT_PASS1_RECORD.md`

Correction tracker:

`Issue #22 — ARE-0 external audit pass 1: bounded blocker corrections`

## 3. Reading order

Read the original architecture first, then the corrections with explicit precedence:

1. `PROJECT_GOVERNANCE/AHFMES_ARE_FORMAL_ARCHITECTURE_MASTER_V2.md`
2. `PROJECT_GOVERNANCE/AHFMES_ARE_0A_STATE_MACHINES_AND_INVARIANTS_V3.md`
3. `PROJECT_GOVERNANCE/AHFMES_ARE_0B_AUTHORITY_NON_FORGEABILITY_V3.md`
4. `PROJECT_GOVERNANCE/AHFMES_ARE_0C_EVIDENCE_LEDGER_AND_HOLDOUT_CONSUMPTION_V2.md`
5. `PROJECT_GOVERNANCE/AHFMES_ARE_0D_SEARCH_GENEALOGY_BUDGET_MULTIPLICITY_V2.md`
6. `PROJECT_GOVERNANCE/AHFMES_ARE_0E_CRITIC_GOVERNOR_PROMOTION_V2.md`
7. `PROJECT_GOVERNANCE/AHFMES_ARE_0_EXTERNAL_AUDIT_CORRECTION_PACKAGE_V1.md`
8. `PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V1.md`
9. `PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V1.md`
10. `PROJECT_GOVERNANCE/AHFMES_ARE_0_EXTERNAL_AUDIT_CORRECTION_AMENDMENT_001.md`
11. `PROJECT_GOVERNANCE/AHFMES_ARE_0_EXTERNAL_AUDIT_CORRECTION_INTERNAL_REVIEW_V1.md`
12. `PROJECT_GOVERNANCE/AHFMES_ARE_0_EXTERNAL_AUDIT_PASS1_RECORD.md`

Precedence:

```text
Correction Amendment 001
> Correction Package / Total Matrix / State Totality Register
> earlier 0A/0B/0C/0D/0E wording on corrected subjects
```

The internal review is evidence of our own attack process, not normative authority and not closure.

## 4. Re-attack EC-01 — state-machine totality

Try to produce:

```text
unlisted legal edge
implicit "obvious" transition
object type with authority but absent from totality register
Candidate reactivation after adjudication
same-content new Candidate ID that resets proof/debt
Experiment integrity PASS becoming hypothesis PASS
Research Episode old result overwritten by new result
```

Also attack repeated evaluation:

```text
same Candidate
new evidence
without new CandidateProofEpisode / ResearchEpisode / debt linkage
```

Any surviving path is blocking.

## 5. Re-attack EC-02 — scientific/promotion/deployment orthogonality

Try to make any intrinsic scientific object retain an unconditional field equivalent to:

```text
PROMOTION_ELIGIBLE
PRODUCTION_ELIGIBLE
PROMOTED
```

after Champion/context/gate/freshness changes.

Try to make Capital Safety veto create scientific `REJECTED` when the scientific claim itself remains valid.

Try to erase prior scientific result through deployment/rollback/retirement.

## 6. Re-attack EC-03 — Problem root semantics

Try to cause a later Research Episode to mutate historical Program identity.

Check that:

```text
problem_definition_root = immutable
problem_history_root/revision = append-only
Program binds explicit history cutoff
```

Try to substitute a mutable episode list behind an old Program root.

## 7. Re-attack EC-04 — authority ownership

Attempt privilege escalation through every authority class, especially:

```text
A-PROGRAM-CREATE
A-PROGRAM-BUDGET
A-PROGRAM-RENEW
A-RESEARCH-EVAL
A-ADJUDICATE
A-PROMOTE
A-ROLLBACK
A-CAPABILITY-DESIGN
A-CAPABILITY-PROOF
A-CAPABILITY-PRODUCTION-ACTIVATE
A-CAPABILITY-RETIRE
A-CAPITAL-ACTIVATE
A-CAPITAL-DEACTIVATE
A-EMERGENCY-FLAT
A-AUTHORITY-REVOKE
```

Try concrete `THINK -> ACT` paths:

```text
Research-triggered emergency flat
Research-triggered rollback
Research activation of capability
Research minting fresh Program budget
Research revoking inconvenient authority
Governor activating capital
Promotion service submitting broker mutation
```

Any unregistered/anonymous authority phrase should be treated as a blocker.

## 8. Re-attack EC-05 — family lifetime meta-budget

Try:

```text
Program P1 fail
prospective epoch arrives
P2 fresh slate
P3 fresh slate
...
until lucky pass
```

Try family relabeling/new IDs/new charter wording to reset:

```text
program birth count
validation families
error/evidence spending
promotion attempts
search debt
```

Fresh data may renew information but must not erase family lifetime multiplicity.

## 9. Re-attack EC-06 — hidden search / outcome side channel

Assume Research Brain is adversarial.

Try to obtain outcome information from:

```text
filesystem
copied artifact
notebook
alternate process
raw log
telemetry
network cache
human/auditor summary
unmediated Python evaluation
```

then self-report only a winner.

The corrected contract should force:

```text
OUTCOME_ACCESS_CLOSURE_PROOF required
or independent proof denied
```

For mediated search, verify order:

```text
Search Node committed
-> budget atomically charged
-> evaluation executed
-> result identity logged
-> Exposure event durable
-> result disclosed
```

Attempt any early disclosure or failed-budget rollback that still leaks result.

## 10. Re-attack EC-07 — Evidence identity and attestation

Try to mutate an EvidenceSnapshot from `UNVERIFIED` to `VERIFIED`.

It should be impossible because verification is a separate attestation.

Try to claim `STRICT_BLIND` from temporal origin alone.

Attack the Embargo Information-Flow Manifest with unknown side channels.

Unknown material isolation must fail closed/downgrade, not be treated as strict blind.

## 11. Re-attack EC-08 — unrelatedness privilege

Attempt:

```text
Claim A contaminates evidence E
Claim B is semantically reframed
new gate/version/argument
RELATED -> UNRELATED_SUPPORTED
reuse E
```

Positive unrelatedness must require the frozen pre-exposure theorem and exact context.

Unknown must behave as RELATED.

## 12. Re-attack EC-09 — mutable state as hidden policy

Keep source/model artifact hash fixed but change live behavior through:

```text
weights
calibration
memory
online priors
exit bias
retrieval state
adaptive thresholds
```

Check whether every decision-relevant mutable update mechanism is included in Candidate transitive closure and reproducible state provenance.

Any unvalidated update rule/input/objective that changes capital mapping is a `THINK -> ACT` bypass.

## 13. Re-attack authority/state residuals found internally

Specifically challenge:

```text
A-CAPITAL-DEACTIVATE
A-AUTHORITY-REVOKE
EXPIRED/STALE derived authority usability
Family exhaustion adjudication
Program create vs budget reservation prerequisite
closed-world object register
```

Do not trust them merely because internal Red-Team found them.

## 14. Implementation-specific residuals

The corrected architecture deliberately does not claim implementation proof for:

```text
OS/process enforcement of outcome-access closure
atomic storage/CAS realization
Governance Root cryptographic/process implementation
physical embargo implementation
runtime adaptive-state persistence/checkpoint mechanism
future contract-specific numerical promotion thresholds
future contract-specific numerical family error/evidence spending
```

Auditor must decide whether architecture-level contracts are sufficiently specific to close ARE-0 while leaving realization to ARE-1, or whether any item still exposes an architectural loophole.

## 15. Required finding format

For every finding:

```text
finding_id
severity
exact subject document/section
attack precondition
concrete exploit path
which current invariant fails to block it
required correction
whether finding blocks ARE-0 closure
```

Do not return prose-only discomfort without an exploit path for a blocking finding.

## 16. Allowed final dispositions

Exactly one:

```text
CHANGES_REQUIRED
ACCEPT_ARE0_FORMAL_DESIGN_CLOSED
ARE0_FORMALIZATION_INVALID
```

No partial `mostly pass` state should silently become closure.

## 17. Hard firewall

Regardless of re-audit outcome:

```text
ARE implementation = NOT AUTHORIZED by this handoff
P001 substantive research = NOT AUTHORIZED
G1 rerun/retune = PROHIBITED
G2 = NOT AUTHORIZED
W2/W3 = CLOSED
production = CLOSED
AHFMES-NEW = CLOSED
PR #20 merge = NOT AUTHORIZED
```

Even `ACCEPT_ARE0_FORMAL_DESIGN_CLOSED` would require a separate implementation authority before coding.
