# AHFMES ARE-0 — Authority-Sensitive Object Inventory V2

Status: **CLOSED-WORLD IDENTITY / GENESIS COMPANION / R9 CORRECTED FORMAL DESIGN / STATELESS CLOSURE SUBJECT / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 1. Role / precedence

Identity/genesis inventory only. Machine rights exist only in:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V2.md
```

This inventory cannot add a state, writer, transition or privilege. Any mismatch with Matrix V2 blocks formal freeze; Matrix V2 controls.

`CURRENT_AUTHORITY_INDEX.md` is non-normative orientation/status and cannot add rights.

## 2. Exogenous pre-system premises — NOT ARE objects

```text
BOOTSTRAP_TRUST_ANCHOR_ROOT
BOOTSTRAP_EPOCH_KEY
pre-system one-slot bootstrap CAS primitive
```

These are explicit pre-system trust/persistence premises. They are not ordinary ARE authority objects and have no post-SystemGenesis privilege.

## 3. Independent authority-sensitive object universe

The current closed-world universe is the incorporated R8 universe plus R9 additions marked below.

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
ChampionRelianceRegistry                 # R9
ChampionRevalidationRecord               # R9

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
CapitalMutationBoundaryRegistry          # R9
CapitalMutationBoundaryManifest          # R9

DeploymentActivationEpisode
DeploymentRegistry
ActivationIntent
```

Aliases in Matrix V2 are aliases only, not second types.

## 4. Embedded immutable subobjects / derived identities

### SystemGenesis records

```text
GenesisCapitalSafetyContainmentSpec
GenesisSafetyChangePolicy
GENESIS_SAFETY_CHANGE_POLICY_ROOT
CONSTITUTIONAL_SAFETY_INTEGRITY_TRIGGER_SET_ROOT
BOOTSTRAP_TRUST_ANCHOR_ROOT used
BOOTSTRAP_EPOCH_KEY consumed
bootstrap Genesis / Bootstrap-Audit control roots
bootstrap terminal-consumption root
```

### Existing research / proof identities

All incorporated R8 claim/risk/admissibility, Candidate runtime/action, evidence, planned-proof, narrowing, final comparative, proof-reliance and selection-reliance identities remain.

### Champion lifecycle / Challenge identities

```text
CHAMPION_LIFECYCLE_POLICY_DERIVATION_ROOT
CHAMPION_LIFECYCLE_POLICY_BUNDLE_ROOT
REVALIDATION_POLICY_ROOT
REVALIDATION_ORDER_RULE_ROOT
REVALIDATION_RECOVERY_RULE_ROOT
ROLLBACK_POLICY_ROOT

CHALLENGE_SEMANTIC_OPPORTUNITY_ROOT
CHALLENGE_ALLOCATION_ORDER_KEY
PREVALIDATION_BLOCKED_ACCOUNTING_RULE_ROOT
POSTACCESS_BLOCKED_ACCOUNTING_RULE_ROOT
CHALLENGE_SELECTION_DEBT_CHARGE_ROOT
CHALLENGE_ERROR_SPEND_ALLOCATION_ROOT
PROMOTION_ERROR_CONTROL_INSTANCE_ROOT where applicable
POSTACCESS_EXPOSURE_LINEAGE_ROOT where applicable
```

### Revalidation identities

```text
REVALIDATION_ORDER_KEY
REVALIDATION_OPPORTUNITY_KEY
NEXT_CANONICAL_REVALIDATION_SLOT
REVALIDATION_OPPORTUNITY_COVERAGE_CURRENT
REVALIDATION_SCIENTIFIC_DISPOSITION_ROOT
current reliance frontier/expiry root
```

`ChampionRelianceRegistry` state is exactly:

```text
CURRENT
SUSPENDED
REVOKED
```

Historical proof truth is not a mutable state of this registry.

### Rollback identities

```text
FALLBACK_ROLLBACK_ELIGIBILITY_VALID
ROLLBACK_CAUSE_EVENT_KEY
ROLLBACK_CAUSE_LINEAGE_ROOT
ROLLBACK_CAUSE_LINEAGE_VALID
historical CHAMPION_SELECTION_RELIANCE_ROOT_AT_DISPLACEMENT
exact displaced-incumbent target root
```

### Mutation-boundary identities

```text
NEXT_MUTATION_BOUNDARY_GENERATION
MUTATION_BOUNDARY_INPUT_FRONTIER_ROOT
MUTATION_BOUNDARY_GENERATION_SLOT_KEY
MATERIAL_MUTATION_SOURCE_COVERAGE_ROOT
MUTATION_BOUNDARY_GENERATION
```

`CapitalMutationBoundaryManifest` binds protected scope, complete material mutation-source set, source classifications/control roots, fencing/exclusivity, shared reservation/reconciliation topology, broker-native mutation semantics, standing conditional/protective interaction model, observation/reconciliation contract and exact input frontier/generation.

### Completeness identities

Each `OperationalCompletenessRecord` has one surface:

```text
DECISION_INPUT_COMPLETENESS
EXECUTION_DISPATCH_SETTLEMENT_COMPLETENESS
CAPITAL_BROKER_EXPOSURE_COMPLETENESS
SAFETY_OBSERVATION_RESPONSE_COMPLETENESS
```

and binds:

```text
OPERATIONAL_COMPLETENESS_KEY
COMPLETENESS_ADVERSE_LINEAGE_ROOT
COMPLETENESS_DEFECT_RESOLUTION_ROOT where prior adverse state is positively resolved
source contract / event universe / coverage frontier
transport/capture / canonicalization / gap-detection roots
auditor/control identities
reconciliation semantics where applicable
```

## 5. R9 object-responsibility justification

### Bootstrap

No BootstrapTrustAnchor object is added; doing so would recreate circular genesis.

### Challenge

No new Challenge registry is needed. `ChampionChallengeAttempt` gains total terminal accounting classes. Semantic opportunity and later exposure payload are distinct derived identities.

### Current scientific reliance

`ChampionRelianceRegistry` + `ChampionRevalidationRecord` are required because immutable historical scientific proof and mutable current reliance are different responsibilities. Per-generation reliance is CURRENT/SUSPENDED/REVOKED.

### Rollback

No strategy-switch object is added. Rollback remains recovery machinery, constrained by pre-outcome policy, exact displaced target, current per-generation reliance, fresh deployment preflight and causal provenance.

### Mutation boundary

Boundary Registry/Manifest are independent mutable responsibilities because physical mutation-source coverage/fencing has its own generation and exact broker-lifecycle frontier.

### Completeness

Existing `OperationalCompletenessRecord` is sufficient when typed by surface, one-slot keyed and adverse-history preserving; no duplicate completeness registry is needed.

## 6. Closed-world invariants

```text
OBJECT TYPE ABSENT FROM MATRIX V2 = NO AUTHORITY
GENESIS MODE ABSENT FROM MATRIX V2 = INVALID OBJECT AUTHORITY
WRITER ABSENT FROM MATRIX V2 = WRITE DENIED
ALIAS != SECOND TYPE
CONTENT-ADDRESSED ROOT != MUTABLE AUTHORITY OBJECT
NEW ID != NEW SCIENTIFIC / SELECTION / SAFETY SLATE
EXOGENOUS BOOTSTRAP AXIOM != POST-GENESIS PRIVILEGE
HISTORICAL PROOF VALIDITY != CURRENT RELIANCE STATE
HISTORICAL SELECTION RELIANCE AT DISPLACEMENT != CURRENT SELECTED STATE
LATER EXPOSURE PAYLOAD != NEW CHALLENGE SEMANTIC OPPORTUNITY
REVALIDATION ROUTINE PASS != RECOVERY FROM REVOKED CLAIM
DECISION INPUT COMPLETENESS != BROKER/EXPOSURE COMPLETENESS
BROKER/EXPOSURE COMPLETENESS != SAFETY RESPONSE COMPLETENESS
SUCCESSOR COMPLETENESS PASS != ERASURE OF PRIOR ADVERSE GAP
RETRY/TIME/SESSION != NEW CHALLENGE / REVALIDATION / COMPLETENESS / BOUNDARY SLOT
```

Every mutable type in §3 has exact legal genesis/writer/transition coverage only through Matrix V2.

## 7. Lifecycle-specific checks

```text
Bootstrap epoch
= one pre-system semantic subject;
  identical retry idempotent;
  conflict invalid;
  SystemGenesis existence => consumed.

Challenge obligation
= stable first-eligibility semantic opportunity.
ACCESS_UNKNOWN => conservative POSTACCESS terminal accounting, not deadlock.
ELIGIBILITY_UNKNOWN under proven no-access => conservative PREVALIDATION terminal accounting.

Champion revalidation
= append-only ordered obligations under frozen REVALIDATION_ORDER_RULE_ROOT.
Later slot cannot leapfrog earlier unsettled slot.
Scientific disposition is sealed by ScientificAdjudication and cannot be chosen by Governor.
Missing/unavailable proof has adverse non-PASS terminal path.

Reliance
= CURRENT may refresh;
  recoverable insufficiency/expiry may SUSPEND;
  material FAIL/NEGATIVE REVOKES;
  REVOKED cannot return CURRENT through revalidation.

Rollback
= exact displaced incumbent + valid historical selection reliance at displacement
  + current per-generation reliance/preflight + valid cause lineage.

Mutation boundary
= deterministic next generation + exact CAS input frontier.
Known source/control-head advance makes stale update lose.

Completeness
= one semantic key/one result;
  unresolved adverse lineage remains part of current predicate;
  exact positive backfill/dependency-removal proof required for resolution.
```

## 8. Static formal boundary

This inventory supplies no current audit-progress state and grants no:

```text
ARE-0 closure
implementation authority
P001 substantive research authority
production authority
PR merge authority
```

Audit/clean-pass/candidate/external-subject status lives outside the normative authority root.