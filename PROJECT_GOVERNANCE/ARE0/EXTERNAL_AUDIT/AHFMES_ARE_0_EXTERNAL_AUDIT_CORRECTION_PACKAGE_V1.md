# AHFMES ARE-0 — Consolidated Scientific & Governance Invariants V1

Status: **R8 EXTERNAL CHANGES_REQUIRED CORRECTED / R8-01..R8-03 + IA8-01..IA8-64 IN MATRIX / TWO CLEAN PASSES / R7+R8 REGRESSION PASS / READY FOR CANDIDATE FREEZE / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 1. Precedence

Machine rights exist only in:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V1.md
```

This file summarizes invariants and correction intent. It cannot widen the Matrix. Detailed internal finding/reproduction lineage is maintained in:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_SELF_AUDIT_COUNCIL_RUN_R8.md
```

```text
THINK -> PROVE -> ACT
THINK MAY EXPLORE HIGH-RISK / WEAK / UNPROVEN IDEAS
PROVE MAY ONLY CLAIM WHAT GOVERNED EVIDENCE IDENTIFIES
ACT MAY ONLY RECEIVE AUTHORITY AFTER SCIENTIFIC + SELECTION + SAFETY GATES
```

## 2. External R8 corrections

### R8-01 — scientific / promotion admissibility

```text
PRECOMMITTED != SCIENTIFICALLY_ADMISSIBLE
SCIENTIFIC_METHOD_ADMISSIBILITY_VALID = REQUIRED
PROMOTION_ADMISSIBILITY_VALID = REQUIRED
```

Claim/intended-use/risk class is mechanically derived; interested callers cannot downgrade it. Applicable admissibility dimensions are frozen prospectively. Promotion requires positive incremental decision utility versus the exact incumbent/bootstrap comparator under one accounting convention, one valid comparative population and an admissible error-control instance that reflects false-promotion loss plus search/Challenge multiplicity.

No universal trading-specific alpha/threshold is constitutionalized. Material UNKNOWN => no Promotion.

### R8-02 — endogenous DGP / counterfactual identification

Production Evidence binds complete data-generating policy, deployment/action-selection, censoring/observability and intervention/co-intervention context.

```text
PREDICTIVE/DESCRIPTIVE != CAUSAL/POLICY_VALUE/ACTION_COMPARISON
```

Causal/policy-value/action-comparison claims—including action-changing Champion replacement—require frozen counterfactual identification semantics and adequate `COUNTERFACTUAL_QUALITY`. `CF_UNOBSERVABLE` cannot support policy/action Promotion. Predictive results cannot be silently upcast.

### R8-03 — ongoing Safety for existing-risk drift

Risk-bearing footprint creates Safety opportunity obligations independently of a new Decision/CapitalAction. `CapitalSafetyObservationRegistry` has one canonical disposition per `SAFETY_OPPORTUNITY_KEY`:

```text
WITHIN_ENVELOPE
REDUCE
DEACTIVATE
EMERGENCY_FLAT
BLOCKED_UNKNOWN
```

Missing/stale/late/UNKNOWN observation denies new risk and creates deterministic existing-risk response. Existing exposure cannot wait for a new Champion Decision.

## 3. R8 scientific hardenings IA8-01..IA8-64

### 3.1 Comparator / admissibility / proof scope

```text
exact PROMOTION_COMPARATOR_ROOT
exact DECISION_UTILITY_ACCOUNTING_ROOT
exact COMPARATIVE_EVALUATION_POPULATION_ROOT
mechanical claim/risk derivation
admissible bootstrap comparator
PROMOTION_ERROR_CONTROL_POLICY_ROOT prospectively frozen
CHALLENGE_ERROR_SPEND_ALLOCATION_ROOT + PROMOTION_ERROR_CONTROL_INSTANCE_ROOT pre-validation
PROOF_AUTHORITY_NARROWING_RULE_ROOT frozen before validation
final proof-authorized population/action envelope <= planned envelope
FINAL_COMPARATIVE_DECISION_UTILITY_VALID on exact final population/action semantics
```

A broad proof cannot authorize a narrow post-outcome cherry-picked subgroup without the frozen narrowing rule; a narrow/small-scale proof cannot authorize broader or materially different live semantics.

### 3.2 Challenger allocation / multiplicity

```text
CHALLENGE_ALLOCATION_ORDER_RULE_ROOT frozen before challenger outcomes
FIRST_ELIGIBLE_INFORMATION_TIME mechanically derived
CHALLENGE_ALLOCATION_ORDER_KEY independent of thread/CAS order
historical first-eligible opportunity creates monotone allocation obligation
only NEXT_CANONICAL_CHALLENGE_ALLOCATION_SLOT may settle
REGISTERED or PREVALIDATION_BLOCKED retain selection/error debt
```

Scheduler/CAS order cannot decide error wealth. An opportunity that later becomes invalid cannot disappear from selection accounting. Missing earlier obligation blocks later registration rather than silently skipping it.

### 3.3 Candidate / Contract temporal protection

Candidate remains researchable even when production-ineligible. Production eligibility is a Candidate↔Contract relation, not mutable Candidate status. A child Contract may qualify a Candidate only if the result-access boundary is positively proven and the child Contract commits before any relevant result access. Absence of a log is not proof of no access.

### 3.4 Evidence / DGP / identification

```text
POLICY_GENERATED vs EXOGENOUS mechanically derived
INTERVENTION_CONTEXT_ROOT complete
mixed-policy segmentation explicit
Evidence attestation one-slot; retry/time/session cannot mint PASS lottery
holdout/reservation consumption relational and debt-aware
counterfactual identification mandatory only for applicable claim classes
```

## 4. R8 Capital Safety hardenings IA8-01..IA8-64

### 4.1 Safety model / opportunity / response

```text
SAFETY_RISK_MODEL_ADMISSIBILITY_VALID
SAFETY_TRIGGER_COVERAGE_COMPLETE
SAFETY_MONITORING_LATENCY_ADMISSIBLE
SAFETY_EMERGENCY_RESPONSE_FEASIBILITY_VALID/CURRENT
PRE_RISK_AUTHORIZATION_INPUT_FRONTIER_CURRENT
SAFETY_INPUT_FRONTIER_CURRENT
SAFETY_OBSERVATION_COMPLETENESS_CURRENT
SAFETY_RESPONSE_OBLIGATION_CURRENT
```

Every material driver capable of changing the protected envelope must be observed by event trigger or admissible bounded cadence. Constant-zero/non-conservative risk models and unbounded monitoring gaps are invalid.

### 4.2 Genesis containment

`GenesisCapitalSafetyContainmentSpec` is constitutionally bounded and grants **no new-risk/deployment authority**. It can reconcile, conservatively account, cancel risk-increasing conditionals and monotonically reduce/close pre-existing/orphan risk.

`INITIAL_SAFETY_REQUIRED_KEY` makes transition to the first normal SafetyContract mandatory at the first canonical bootstrap readiness frontier; containment cannot become permanent pseudo-production Safety.

### 4.3 Safety change control

Every canonical Safety-change trigger creates a derived expected `SAFETY_CHANGE_ROOT_KEY` before proposal materialization. Missing `PREPARE` cannot erase the obligation or create a pre-decision risk window.

```text
SAFETY_CHANGE_EXPECTED_ROOT_COVERAGE_CURRENT
UNRESOLVED_SAFETY_CHANGE_OPPORTUNITY_PRESENT
SAFETY_CHANGE_REMEDIATION_CURRENT
SUCCESSOR_POLICY_COMPATIBILITY_VALID
```

Normal new risk is denied from root appearance until terminal resolution.

One `SafetyContractChangeProposalRecord` provides the durable CAS anchor. Proposal content is deterministic from the cause/policy; favorable retry is denied. PREPARED blocks new risk and must consume the first canonical freeze-eligibility frontier or follow the exact material-staleness successor protocol.

Invalid/UNKNOWN SafetyChangePolicy cannot be required to authorize its own repair: constitutional Safety-integrity triggers exist independently. Concurrent roots may be terminally `SATISFIED_BY_SUPERSEDING_CHANGE` only after positive proof that a valid superseding Safety generation resolved the exact original cause. Old roots cannot use obsolete/weaker policy to overwrite stronger current Safety.

### 4.4 Broker / pending / existing risk

All-scope risk includes actual, live conditional, authorized reserved, executing reserved, uncertain upper bound and candidate worst case. Pending orders remain `PENDING_LIVE` / `CONDITIONAL_LIVE` while fillable. Partial-fill remainder remains risk. Protective privilege is current-polarity dependent. Broker ambiguity is reconciled before retry unless a new reduction is independently proven monotonic-safe.

## 5. Preserved R7 invariants

R8 narrows but may not delete:

```text
legacy continuity / retrospective invalidation
Family/debt/search/holdout/selection non-reset
whole adaptive-search capture and stopping discipline
Evidence exposure/attestation one-slot semantics
historical principal SoD
proof reliance and Champion selection reliance
behavior-lineage anti-fake-novelty
selected != deployed
Input/State/Decision/Deployment idempotency and completeness
operational Fidelity history
all-scope capital reservation
pending/partial/cancel-fill accounting
protective polarity
broker mutation idempotency/reconciliation
ancestor invalidation
Capability catalog-only production boundary
ACT->THINK governed feedback
```

Explicit preserved hard gates include:

```text
PROOF_RELIANCE_ACCESS_HISTORY_VALID
PROOF_RELIANCE_PRINCIPAL_SOD_VALID
LEGACY_STATE_RETROSPECTIVE_VALID_FOR_PROOF
DEPLOYMENT_CONTROL_POLICY_CURRENT
DEPLOYMENT_CONTROL_COMPLETENESS_CURRENT
OPERATIONAL_CAPTURE_WINDOW_CURRENT
OPERATIONAL_INPUT_OBSERVATION_BOUNDARY_PROVEN
DECISION_SOURCE_EVENT_CANONICAL
SAFETY_DISPOSITION_DETERMINISTIC
SAFETY_DISPOSITION_COMPLETENESS_CURRENT
SAFETY_MONITORING_SPEC_CURRENT
```

## 6. Cross-domain invariants

```text
PRECOMMITMENT != ADMISSIBILITY
PROVENANCE != IDENTIFIABILITY
IDENTIFIABILITY != POSITIVE DECISION VALUE
POSITIVE DECISION VALUE != CAPITAL SAFETY
RISKY IDEA != AUTHORIZED LIVE RISK
SAFETY AUTHORITY != SAFETY OBSERVATION COMPLETENESS
SAFETY OBSERVATION != SAFETY RESPONSE FEASIBILITY
VALID NEW SAFETY GENERATION != AUTOMATIC RESOLUTION OF EVERY OLD SAFETY CAUSE
NEW CHALLENGER SLOT != SCHEDULER-CHOSEN ERROR WEALTH
```

No downstream layer may relabel an upstream defect into validity.

## 7. Mandatory regression families and result

All R7 regression seeds remain permanent. R8 additionally attacks:

```text
XC-01 negative Champion-relative utility despite frozen gate
XC-01 permissive error criterion / wrong comparator / wrong population / weak bootstrap comparator
XC-01 post-outcome subgroup or action-scale authority expansion
XC-01 scheduler-ordered Challenge error allocation / disappearing pre-validation challenger

XC-02 policy-conditioned action comparison with missing counterfactual
XC-02 production data mislabeled exogenous / mixed-policy segment hidden
XC-02 predictive result silently upcast to policy value
XC-02 external/manual/co-intervention omitted
XC-02 post-result child Contract rescue

XC-03 existing risk unsafe with no new Decision/CapitalAction
XC-03 risk=0 model / slow cadence / omitted trigger / stale feasibility
XC-03 unresolved Safety change admits risk
XC-03 invalid Safety policy must repair itself
XC-03 stale/invalid proposal deadlock or retry lottery
XC-03 concurrent Safety-root collision / obsolete-policy successor
XC-03 Genesis containment never transitions to normal Safety
XC-03 pending/partial/protective/broker uncertainty failures
```

Formal regression against exact synchronized internal subject `da18adafffa9c2f4142488cc153b4495a0dc0a4a`:

```text
R7 HISTORICAL REGRESSION FAMILY REPLAY = PASS
R8 XC-01 / XC-02 / XC-03 = PASS
IA8 INTERACTION REGRESSION = PASS
NEW REPRODUCIBLE INTERNAL FORMAL BLOCKER = NONE CURRENTLY FOUND
```

## 8. Current gate

```text
LATEST NORMATIVE MATRIX COMMIT = 6f38c677637303975687b307bc1edcaf6ebd0242
FORMAL CLEAN-PASS SUBJECT = da18adafffa9c2f4142488cc153b4495a0dc0a4a
R8-01..R8-03 = INTEGRATED
IA8-01..IA8-64 = INTEGRATED
FULL COUNCIL CLEAN PASS #1 = CLEAN
FULL COUNCIL CLEAN PASS #2 = CLEAN
CONSECUTIVE CLEAN PASS COUNT = 2
END-TO-END R7+R8 REGRESSION = PASS
FINAL CROSS-DOCUMENT CONSISTENCY = NEXT
NEW FROZEN EXTERNAL SUBJECT = NONE UNTIL FREEZE
```

Internal PASS does not close ARE-0; external adjudication is still required.

## 9. Hard boundary

```text
ARE-0 CLOSED = NO
ARE implementation = NOT AUTHORIZED
P001 substantive research = NOT AUTHORIZED / UNKNOWN
G1 rerun/retune = PROHIBITED
G2 = NOT AUTHORIZED
W2/W3 = CLOSED
production = CLOSED
AHFMES-NEW = CLOSED
PR #20 merge = NOT AUTHORIZED
```
