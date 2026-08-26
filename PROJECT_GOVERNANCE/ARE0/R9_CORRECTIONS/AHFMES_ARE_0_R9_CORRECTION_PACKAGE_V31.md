# AHFMES ARE-0 — R9 Correction Package V31

Status: **NORMATIVE / EXT2-081-01 R9-05 ROLLBACK CAUSE-AVAILABILITY CLOSURE / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Inheritance / exact failed subject

```text
BASE_CORRECTION_V30_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_CORRECTION_PACKAGE_V30.md
BASE_CORRECTION_V30_GIT_BLOB_SHA = 33e683d714cc6f678958f539a94df2b8da12a976
FAILED_EXTERNAL_SUBJECT = 081e0472a4322a83af148ee0b60e01a655b0fcbd
EXTERNAL_FINDING = EXT2-081-01
ROOT = R9-05
NEW_R9_ROOT = NO
```

V30 and all inherited corrections remain in force. V31 closes one externally reproduced R9-05 gap. The failed external subject remains immutable and receives no closure credit from this successor.

Current successor components for this correction wave are Matrix V26 / Inventory V26 / Protocol V32 under the successor manifest. Policy V5 remains unchanged.

## 1. Failure statement

A genuine allowed rollback cause can be created outcome-independently and stored immutably while the current Champion outcome controls whether an otherwise independent attester searches for, admits, finalizes, or attests that cause.

Without a consequence-blind availability theorem, two worlds may share identical genuine cause facts:

```text
Champion favorable   -> do not query clean cause R -> Champion remains B
Champion unfavorable -> query same clean cause R   -> cause enters R9-05 -> rollback B -> A
```

Existing cause provenance and separation of duties do not stop this path. Once R is queried, every inherited factual/lineage predicate may be known and valid. When R is not queried, inherited R9-05 has no complete expected observation opportunity against which suppression can be detected.

This is hidden fallback strategy selection through observation control.

## 2. Correction principle

For `A-ROLLBACK`, clean cause content is necessary where inherited rules require it but is not sufficient.

```text
CLEAN / GENUINE CAUSE
!=
CONSEQUENCE-BLIND ROLLBACK AVAILABILITY
```

Any control decision that can change whether the cause becomes legally available to select the displaced incumbent fallback is authority-relevant information flow.

The V25 refinement lesson is reused rather than duplicated as a new subsystem:

```text
content provenance
+
control / availability influence closure
+
counterfactual noninterference
```

must be satisfied for the rollback-selection privilege.

## 3. Frozen authority-conferring observation semantics

The inherited pre-outcome `ROLLBACK_POLICY_ROOT[T]` now semantically binds exact `ROLLBACK_CAUSE_OBSERVATION_POLICY_ROOT[T,C]` for each allowed cause class `C`.

At minimum it binds:

```text
governed authority-conferring source/opportunity universe
source/producer identity or governed source class
frozen event-driven push / subscription / probe / query / cadence semantics
canonical discovery-opportunity identity/order
monitor scope and scope-change rule
admission/suppression/exclusion rule
finality/currentness/completeness rule
attestation trigger/availability rule
missing/late/unavailable/access-denied/error/retry/UNKNOWN semantics
timeout/freshness/expiry semantics
cause eligibility for the rollback-selection path
```

This is a projection of the existing rollback policy. It is not an additional writable policy registry.

The source universe is intentionally **authority-conferring**, not omniscient. A real defect found outside it may still create factual/Safety consequences, but cannot become a strategy selector until a governed consequence-blind path makes it eligible.

## 4. Complete influence closure

The exact rollback cause-selection influence graph must include both content and control/availability paths capable of changing:

```text
monitor/source/scope selection
push/subscription/probe/query/discovery activation
retry/error/absence handling
source/method selection
admission/suppression
finality/currentness/completeness
attestation availability/completion
cause canonicalization/eligibility
semantic timing boundaries
legal availability of the cause to R9-05
legal availability of A-ROLLBACK
```

Human/LLM/operator knowledge and outcome presence/absence/access/error/latency/timing are included when they can act as selectors. Hidden or materially opaque influence means closure is incomplete.

## 5. Counterfactual theorem

Holding genuine non-performance cause facts and exogenous governance/integrity facts fixed, vary Champion/fallback consequence information and every descendant/proxy of it.

The following must remain invariant for the authority-conferring rollback path:

```text
which governed observation opportunities occur
whether the cause is queried/discovered/retried
whether it is admitted or suppressed
whether it becomes final/current/complete
whether attestation is requested/available/completed
whether the cause becomes legally available to R9-05
whether A-ROLLBACK fallback strategy selection becomes legally available
```

If any material variation changes one of these, or influence ancestry is materially UNKNOWN:

```text
ROLLBACK_CAUSE_SELECTION_NONINTERFERENCE_VALID = FALSE
A-ROLLBACK STRATEGY SELECTION = DENIED
```

## 6. Separation from Safety containment

This correction does not suppress facts and does not require an unsafe system to continue running a suspect Champion.

An outcome-tainted discovery of a genuine integrity/Safety defect may, when exact independent authority exists, support:

```text
factual defect/incident recording
increased observation/diagnosis
cancellation of pending risk increase
deactivation / no-new-risk
risk reduction / closure
other inherited fail-closed Safety containment
```

It cannot by itself authorize the separate selector:

```text
Champion B -> exact displaced incumbent A via A-ROLLBACK
```

Thus containment remains responsive while performance-conditioned strategy switching is denied.

## 7. Positive liveness

A valid rollback path remains possible, including immediate event-driven response:

```text
frozen rollback policy
-> frozen consequence-blind event-driven push/subscription or governed probe/cadence
-> genuine allowed cause observed independent of Champion outcome
-> complete influence closure
-> noninterference PASS
-> inherited first-information/provenance/SoD PASS
-> exact displaced incumbent and proof/selection/Safety/runtime predicates current
-> exact inherited rollback authority current
-> A-ROLLBACK legal
```

The mere fact that Champion outcome already exists elsewhere does not taint this path; only causal/control dependence on that outcome does.

## 8. Required adversarial attacks

Any successor qualification MUST attack at least:

```text
outcome -> clean cause query activation
outcome -> monitor scope expansion only after loss
outcome -> admission/suppression of already-visible cause
outcome -> finality/currentness request
outcome -> attestation completion/defer
outcome -> retry after archive/API error
outcome-presence/access/latency -> cause availability
human/LLM sees PnL -> requests clean cause search
transformed/thresholded outcome proxy -> query or attestation
same clean cause + outcome-independent push/cadence positive control
outcome-tainted cause -> factual/Safety containment positive control
unrelated monitor/CAS churn -> no semantic remint/starvation
stale displaced incumbent -> rollback remains denied
```

## 9. Permanent regressions added

```text
R9-X279 = OUTCOME_CONDITIONED_CLEAN_ROLLBACK_CAUSE_QUERY
R9-X280 = OUTCOME_CONDITIONED_ROLLBACK_ATTESTATION_SUPPRESSION
```

Protocol V32 defines the exact setups and expectations. A positive consequence-blind rollback liveness control is mandatory in the same audit wave.

## 10. Qualification reset

The previous external subject was blocked. This normative correction resets all predecessor qualification credit.

Before any new external handoff:

```text
freeze exact new S0
verify successor manifest exact same-subject object identities
recompute normative root by two independent implementations
subject-bound historical-authority quarantine verification
whole-architecture/outside-family impact audit from zero
Clean Pass 1
NO NORMATIVE WRITE
Clean Pass 2
permanent regression including R9-X279/X280
final cross-document consistency
self-reference-free candidate construction proof
binder-only child proof
```

Internal PASS is evidence for the next external auditor to attack, not external acceptance.

## 11. Firewall

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
