# AHFMES ARE-0 — Authority-Sensitive Object Inventory V1

Status: **CLOSED-WORLD INVENTORY / R8-01..R8-03 + IA8-01..IA8-64 SYNCHRONIZED / TWO CLEAN PASSES / R7+R8 REGRESSION PASS / READY FOR CANDIDATE FREEZE / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 1. Role / precedence

Identity/genesis inventory only. Machine rights exist only in:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V1.md
```

This file cannot add a state, writer, transition or privilege. Any mismatch with the Matrix blocks freeze; the Matrix controls.

## 2. Independent authority-sensitive roots / records

The current closed-world object universe includes:

```text
PreGenesisScientificStateManifest
SystemGenesisManifest
LegacyCutoffClosureRecord
LegacyScientificStateHead
LegacyScientificStateCorrectionRecord

RoleManifest
PrincipalRoleBindingRecord
VerifiedAuthorityRecord
TrustedAuthorityRegistry
IntegrityDefectRecord
GovernanceRootRotationPolicy
GovernanceRootKernelCapabilities

ResearchFamilyRegistry
ResearchFamilyCharter
FamilyBootstrapReservationSlot
FamilyRelationPolicyRegistry
FamilyRelationPolicy
RelationCoverageManifest
RelationGateSpec
RelationDecision
RelationRegistry
DebtGroupReconciliationRecord
ResearchProgram
ProgramBudgetReservation
FamilyLifetimeLedger

Problem
ResearchEpisode
Hypothesis
ResearchContract
Candidate
Experiment
ShadowEpisode

EvidenceSnapshot
EvidenceExposureEvent
ExposureLedger
EvidenceGovernanceHead
EvidenceReservation
ProvenanceAttestation
ProspectiveIsolationAttestation
ProofDependencyInvalidationRecord
CandidateProofEpisode
ProofBundle

SearchGenerationBatchManifest
SearchActionEvent
SearchNode
SearchCompletenessProof

CriticRecord
ScientificAdjudicationRecord
GovernorRecord

ChampionChallengeLedger
ChampionChallengePolicy
ChampionChallengeAttempt
PromotionTransaction
ChampionRegistry
ChampionRollbackPlan
RollbackTransaction

CapabilityArtifact
CapabilityActivationEpisode
CapabilityRegistry

RuntimeIdentityManifest
RuntimeReconciliationRecord
OperationalCompletenessRecord
OperationalFidelityLedger

DecisionInputRegistry
DecisionInputRecord
DecisionStateRegistry
DecisionStateRevision
DecisionRegistry
DecisionRecord

CapitalSafetyContractRegistry
SafetyContractChangeProposalRecord
CapitalSafetyContract
CapitalSafetyObservationRegistry
CapitalSafetyObservationRecord
CapitalRiskReservationLedger
CapitalRiskReservation
CapitalActionEpisode
ExecutionIntent
ExecutionSettlementRecord
RecoveryExecutionIntent
CapitalActionRecoveryRecord
EmergencyFlatEvent
BrokerMutationRegistry
BrokerMutationRecord

DeploymentActivationEpisode
DeploymentRegistry
ActivationIntent
```

Canonical aliases in the Matrix are aliases only, not second object types.

## 3. Embedded immutable subobjects / projections

These do not obtain independent authority by being loaded from config. They exist only through the parent genesis/transition defined in the Matrix.

### SystemGenesisManifest embeds

```text
GenesisCapitalSafetyContainmentSpec
GenesisSafetyChangePolicy
GENESIS_SAFETY_CHANGE_POLICY_ROOT
CONSTITUTIONAL_SAFETY_INTEGRITY_TRIGGER_SET_ROOT
```

### ResearchContract LOCK embeds / freezes where applicable

```text
CONTRACT_CLAIM_CLASS_FLOOR
CONTRACT_RISK_FLOOR
ClaimAdmissibilitySpec
ADMISSIBILITY_DIMENSION_APPLICABILITY_ROOT
CounterfactualIdentificationSpec
ValidationFamilyManifest
ValidationDisclosurePlan
MultiplicityPlan / SearchTreeBudget
CriticSpec
PromotionGateSpec
EmbargoInformationFlowManifest
```

### Candidate FROZEN embeds / freezes

```text
ExecutionContract
DecisionInputProducerManifest
trigger/cadence/opportunity-input closure
CANONICAL_STATE_ADVANCE_SCHEDULE_ROOT
state initializer/updater/RNG semantics
execution/activation derivation
runtime/capability/deployment-control specs
LIVE_BEHAVIOR_SEMANTICS_ROOT
CANDIDATE_CLAIM_CLASS
CANDIDATE_RISK_CLASS
DEPLOYMENT_TARGET_POPULATION_ROOT
CANDIDATE_ACTION_ENVELOPE_ROOT
CANDIDATE_RESULT_ACCESS_CUTOFF_RULE_ROOT
```

### CandidateProof / Challenge / adjudication projections

```text
PROOF_RESERVATION_ROOT
PLANNED_PROOF_TARGET_POPULATION_ROOT
PLANNED_PROOF_ACTION_ENVELOPE_ROOT
PROOF_AUTHORITY_NARROWING_RULE_ROOT
CHALLENGE_ALLOCATION_ORDER_KEY
CHALLENGE_SELECTION_DEBT_CHARGE_ROOT
CHALLENGE_ERROR_SPEND_ALLOCATION_ROOT
PROMOTION_ERROR_CONTROL_INSTANCE_ROOT
PROOF_AUTHORIZED_DEPLOYMENT_POPULATION_ROOT
PROOF_AUTHORIZED_ACTION_ENVELOPE_ROOT
FINAL_COMPARATIVE_EVALUATION_ROOT
FINAL_COMPARATIVE_DECISION_UTILITY_ROOT
PROOF_RELIANCE_ROOT
CHAMPION_SELECTION_RELIANCE_ROOT
```

### Champion policy projections

```text
PROMOTION_COMPARATOR_ROOT
DECISION_UTILITY_ACCOUNTING_ROOT
COMPARATIVE_EVALUATION_POPULATION_ROOT
PROMOTION_ERROR_CONTROL_POLICY_ROOT
CHALLENGE_ALLOCATION_ORDER_RULE_ROOT
```

### Capital Safety embedded / derived identities

```text
SafetyContractBootstrapManifest
SafetyContractMigrationManifest
SafetyMonitoringSpec
SafetyChangePolicy
ProtectiveDependencyPlan / NO_PLAN_REQUIRED
SAFETY_CHANGE_ROOT_KEY
SAFETY_CHANGE_ATTEMPT_KEY
SAFETY_CONTRACT_FREEZE_ELIGIBILITY_KEY
SAFETY_OPPORTUNITY_KEY
SAFETY_RESPONSE_KEY
PRE_RISK_AUTHORIZATION_INPUT_FRONTIER_ROOT
```

The keys/roots above are immutable identities/projections, not independent object types unless explicitly listed in §2.

## 4. R8 closed-world additions and responsibility justification

R8 added only responsibilities that could not safely be represented by the R7 object set:

```text
CapitalSafetyObservationRegistry
CapitalSafetyObservationRecord
```

They provide an ongoing World-3 Safety opportunity/disposition surface independent of creation of a new CapitalAction, closing R8-03 existing-risk drift.

R8 also materialized:

```text
SafetyContractChangeProposalRecord
```

as the durable one-slot CAS anchor between a canonical Safety-change opportunity and `CapitalSafetyContract` freeze. This prevents proposal retry/timing ambiguity and supports remediation/supersession without inventing another Safety registry.

R8-01 and R8-02 otherwise extend existing Contract/Evidence/Proof/Challenge/Promotion objects rather than create duplicate scientific registries.

## 5. Closed-world invariants

```text
OBJECT TYPE ABSENT FROM MATRIX = NO AUTHORITY
GENESIS MODE ABSENT FROM MATRIX = INVALID OBJECT AUTHORITY
WRITER ABSENT FROM MATRIX = WRITE DENIED
ALIAS != SECOND TYPE
CONTENT-ADDRESSED PROPOSED ROOT != AUTHORITY OBJECT
NEW ID != NEW SCIENTIFIC / SELECTION / SAFETY SLATE
```

Every mutable type in §2 must have exact genesis plus exact legal writer/transition coverage in the Matrix. Embedded items in §3 may only be created by their parent transition.

## 6. R8 lifecycle-specific inventory checks

```text
Challenge allocation obligation = derived expected obligation under frozen ChampionChallengePolicy;
                                  settlement is represented by ChampionChallengeAttempt + ChampionChallengeLedger.

Safety change expected root      = derived expected opportunity at canonical trigger frontier;
                                  settlement is represented by SafetyContractChangeProposalRecord / SafetyContract.

PREVALIDATION_BLOCKED            = terminal ChampionChallengeAttempt disposition for a historical allocation obligation
                                  that became invalid before validation/result access; debt accounting remains.

SATISFIED_BY_SUPERSEDING_CHANGE  = Safety root terminal accounting disposition only after positive proof that a valid
                                  superseding current Safety generation resolved the exact original cause.
```

No derived expected obligation may disappear merely because the responsible service failed to materialize its settlement record.

## 7. Gate result

Formal Self-Audit Council subject:

```text
da18adafffa9c2f4142488cc153b4495a0dc0a4a
```

Results on identical normative semantics with no intervening writes:

```text
FULL COUNCIL CLEAN PASS #1 = CLEAN
FULL COUNCIL CLEAN PASS #2 = CLEAN
CONSECUTIVE CLEAN PASS COUNT = 2
END-TO-END R7 + R8 REGRESSION = PASS
NEW REPRODUCIBLE INTERNAL FORMAL BLOCKER = NONE CURRENTLY FOUND
```

These are internal gates, not external closure.

## 8. Current boundary

```text
R8-01..R8-03 = INTEGRATED
IA8-01..IA8-64 = INTEGRATED IN MATRIX
FULL COUNCIL CLEAN PASS #1 = CLEAN
FULL COUNCIL CLEAN PASS #2 = CLEAN
CONSECUTIVE CLEAN PASS COUNT = 2
END_TO_END R8 REGRESSION = PASS
CANDIDATE FREEZE = NEXT
NEW FROZEN EXTERNAL SUBJECT = NONE UNTIL FREEZE
ARE-0 CLOSED = NO
ARE implementation = NOT AUTHORIZED
production = CLOSED
PR #20 merge = NOT AUTHORIZED
```
