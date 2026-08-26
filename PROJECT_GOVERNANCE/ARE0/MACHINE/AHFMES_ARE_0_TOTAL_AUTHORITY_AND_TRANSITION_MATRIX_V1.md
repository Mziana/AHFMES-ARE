# AHFMES ARE-0 — Canonical Authority & Transition Matrix V1

Status: **SOLE CANONICAL MACHINE SOURCE / R8-01..R8-03 + IA8-01..IA8-64 INTEGRATED / TWO CLEAN PASSES + R7+R8 REGRESSION PASS / READY FOR CANDIDATE FREEZE / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 1. Closed-world / atomic theorem

This file is the only normative machine source for ARE-0 authority, authority-sensitive genesis, legal transitions, exact writer ownership, scientific consumption, principal separation, search/evidence/selection debt, scientific admissibility, claim identification, operational fidelity, Capital Safety, ongoing Safety observation, deployment, broker mutation and recovery.

```text
EDGE ABSENT HERE = DENIED
AUTHORITY ABSENT HERE = INVALID
GENESIS MODE ABSENT HERE = INVALID OBJECT AUTHORITY
WRITER ABSENT HERE = WRITE DENIED
OLDER/SUBORDINATE FILE MAY NOT ADD AUTHORITY
UNKNOWN MATERIAL AUTHORITY / CONTROL / RELATION / FRESHNESS / LINEAGE /
RECONCILIATION / SEARCH CLOSURE / SEARCH BUDGET / LEGACY DEBT /
EVIDENCE ATTESTATION / VALIDATION CONSUMPTION / SCIENTIFIC ADMISSIBILITY /
CLAIM CLASS / CLAIM RISK / DATA-GENERATING POLICY / INTERVENTION CONTEXT /
CLAIM IDENTIFICATION / COUNTERFACTUAL QUALITY / COMPARATOR /
COMPARATIVE POPULATION / PROMOTION ERROR CONTROL / CHALLENGE ALLOCATION ORDER /
PLANNED PROOF POPULATION / ACTION ENVELOPE / PROOF AUTHORITY NARROWING /
FINAL PROOF-AUTHORIZED POPULATION / ACTION ENVELOPE /
CAPITAL RISK / SAFETY RISK MODEL / SAFETY INPUT FRONTIER /
SAFETY CHANGE EXPECTED-ROOT COVERAGE / CHANGE POLICY / CHANGE COMPLETENESS /
CHANGE REMEDIATION / CHANGE SUPERSESSION / CHANGE TIMELINESS /
SAFETY OBSERVATION / SAFETY RESPONSE / SAFETY TIMELINESS /
SAFETY EMERGENCY FEASIBILITY / SELECTION / OPERATIONAL COMPLETENESS /
INFORMATION TIME
= FAIL CLOSED
NO AMBIENT PRIVILEGE
```

Every mutable authority-sensitive transition is an atomic compare-and-swap on exact predecessor object identity, generation and state. One-shot authority consumption and every explicitly listed local side effect commit in same local transaction. Concurrent loser gets no second legal transition.

External broker mutation cannot join local transaction. Every broker mutation requires durable canonical semantic intent + canonical `BrokerMutationRecord` claim before send, then settlement or conservative reconciliation. Partial local commit is never evidence broker mutated.

### 1.1 Canonical aliases

```text
Family:=ResearchFamilyCharter
BootstrapSlot:=FamilyBootstrapReservationSlot
Program:=ResearchProgram
Episode:=ResearchEpisode
Contract:=ResearchContract
CandidateProof:=CandidateProofEpisode
Shadow:=ShadowEpisode
CapabilityEpisode:=CapabilityActivationEpisode
ChallengeAttempt:=ChampionChallengeAttempt
RollbackPlan:=ChampionRollbackPlan
Deployment:=DeploymentActivationEpisode
StateRevision:=DecisionStateRevision
CapitalAction:=CapitalActionEpisode
RecoveryIntent:=RecoveryExecutionIntent
RecoveryRecord:=CapitalActionRecoveryRecord
SafetyRegistry:=CapitalSafetyContractRegistry
SafetyContract:=CapitalSafetyContract
SafetyProposal:=SafetyContractChangeProposalRecord
SafetyObservationRegistry:=CapitalSafetyObservationRegistry
SafetyObservation:=CapitalSafetyObservationRecord
VAR:=VerifiedAuthorityRecord
Ledger:=FamilyLifetimeLedger
EvidenceHead:=EvidenceGovernanceHead
LegacyHead:=LegacyScientificStateHead
FidelityLedger:=OperationalFidelityLedger
ChallengeLedger:=ChampionChallengeLedger
SearchGenerationBatch:=SearchGenerationBatchManifest
SearchAction:=SearchActionEvent
BrokerMutation:=BrokerMutationRecord
```

Aliases same canonical type. UUID/wall-clock/timestamp/process/session/transport/retry/re-serialization cannot mint semantic novelty.

`PROPOSED_FAMILY_ROOT`, `PROPOSED_SAFETY_CONTRACT_ROOT` are content-addressed payload roots only, not authority objects. Proposed Safety payload is usable pre-genesis only through canonical SafetyProposal record.

`SAFETY_CHANGE_ROOT_KEY` is a derived expected-opportunity identity, not separately mutable object. It exists semantically at canonical trigger frontier before a proposal record. Missing proposal cannot erase expected opportunity.

`CANDIDATE_CONTRACT_PRODUCTION_ELIGIBILITY(CandidateRoot,ContractRoot)` is derived relation, not mutable Candidate state. Any shorthand PRODUCTION_ELIGIBILITY means this exact relation for transaction-bound Candidate/Contract.

### 1.2 Transition key / authority usage

```text
TRANSITION_KEY=hash(canonical object identity+generation,exact from_state,exact to_state,immutable mode/cause guard)
ROOT=root-kernel only
ONE_SHOT=one exact semantic subject; successful use once
EPISODE=bounded pre-scoped multi-step episode
SERVICE=repeated only under canonical keys+completeness/idempotency
EDGE_NONCE=one exact object+generation+from+to+mode/cause transition
```

Each transition key has one authority. Multiple authorities on same state pair only under explicit disjoint mechanically decidable guards. Unknown overlap deny. Live-owner vs orphan authority disjoint.

Every VAR binds authority class, semantic subject/object/edge, issuer/holder control identities, prerequisite roots/generations, usage, freshness, expiry/revocation, episode/nonce. Changed prerequisite stales unused authority unless explicit projection. Fresh VAR cannot create second semantic transaction.

## 2. Constitutional boundary / principal separation

```text
WORLD 1 THINK -> WORLD 2 PROVE -> WORLD 3 ACT
THINK MAY EXPLORE HIGH-RISK / WEAK / UNPROVEN IDEAS
PROVE MAY ONLY CLAIM WHAT GOVERNED EVIDENCE IDENTIFIES
ACT MAY ONLY RECEIVE AUTHORITY AFTER SCIENTIFIC + SELECTION + SAFETY GATES
```

Research cannot control live input/state/decision/Safety/deployment/execution/broker authority.

Registered domains:

```text
GENESIS RESEARCH CONTRACT PROGRAM_GOVERNANCE EVIDENCE SEARCH_INSTRUMENTATION
VALIDATION CRITIC SCIENTIFIC_ADJUDICATION GOVERNOR PROMOTION CAPITAL_SAFETY
CHAMPION_REGISTRY CAPABILITY_REGISTRY DEPLOYMENT_REGISTRY OPERATIONAL_INPUT
OPERATIONAL_STATE OPERATIONAL_DECISION EXECUTION AUDIT GOVERNANCE_ROOT
```

RoleManifest binds principal/control-equivalence root/generation/domain/dependency scope. Common control collapses aliases. Unknown material common control where independence matters => deny. Historical SoD is dependency/time scoped; late-discovered conflict at relied time invalidates dependency.

Scientific SoD:

```text
GENESIS != bootstrap AUDIT
RESEARCH != PROGRAM_GOVERNANCE / SEARCH_INSTRUMENTATION / EVIDENCE / AUDIT / VALIDATION / CRITIC / SCIENTIFIC_ADJUDICATION / GOVERNOR / PROMOTION
VALIDATION != EVIDENCE / AUDIT / CRITIC / SCIENTIFIC_ADJUDICATION / GOVERNOR / PROMOTION
EVIDENCE != AUDIT
SEARCH_INSTRUMENTATION != AUDIT
SEARCH_INSTRUMENTATION != EVIDENCE where validation independence depends on search
AUDIT != CRITIC / SCIENTIFIC_ADJUDICATION / GOVERNOR / PROMOTION where relied
CRITIC != SCIENTIFIC_ADJUDICATION / GOVERNOR / PROMOTION
SCIENTIFIC_ADJUDICATION != GOVERNOR / PROMOTION
GOVERNOR != PROMOTION
relation prepare != relation adjudicator
relation prepare/adjudicator != interested RESEARCH
relation adjudicator control != interested relation-policy/Family-assignment ProgramGovernance control
```

Live/governance SoD:

```text
RESEARCH != OPERATIONAL_INPUT / OPERATIONAL_STATE / OPERATIONAL_DECISION / CAPITAL_SAFETY / EXECUTION
PROMOTION != CAPITAL_SAFETY / EXECUTION
OPERATIONAL_DECISION != CAPITAL_SAFETY
CAPITAL_SAFETY != EXECUTION
AUDIT != CAPITAL_SAFETY where Audit evidence/runtime/reconciliation consumed by Safety
RuntimeIdentity AUDIT != Decision/Safety/Execution attested
RuntimeReconciliation AUDIT != Safety/Execution reconciled
CapitalSafety != GovernanceRoot for SafetyContract prepare/freeze/change
Legacy-reconciliation AUDIT != GovernanceRoot
RelationPolicy ProgramGovernance != GovernanceRoot
GovernanceRoot witness != ordinary proposer/executor/beneficiary
rollback trigger producer/attester != rollback executor
```

ROOT transaction interest/topology/current SoD mandatory. Root rotation replacement-first. Authority administration performance-blind. Emergency intervention legal but Fidelity/intervention-marked.

## 3. Exact object universe / genesis

System genesis atomically creates exactly:

```text
SystemGenesisManifest
LegacyCutoffClosureRecord
LegacyScientificStateHead #0
ResearchFamilyRegistry #0
FamilyRelationPolicyRegistry #0 + FamilyRelationPolicy #0
RelationRegistry #0
ChampionRegistry #0 with bootstrap LEGACY_REFERENCE_ONLY Champion
ChampionChallengeLedger #0 + ChampionChallengePolicy #0
CapabilityRegistry #0
DeploymentRegistry #0 = EMPTY
TrustedAuthorityRegistry #0
ExposureLedger #0
EvidenceGovernanceHead #0
DecisionInputRegistry #0
DecisionStateRegistry #0
DecisionRegistry #0
OperationalFidelityLedger #0
CapitalRiskReservationLedger #0
BrokerMutationRegistry #0
CapitalSafetyContractRegistry #0 = EMPTY with empty Safety-change attempt-slot map
CapitalSafetyObservationRegistry #0
GovernanceRootRotationPolicy #0
GovernanceRootKernelCapabilities #0
initial RoleManifests
initial PrincipalRoleBindingRecords
```

SystemGenesisManifest embeds immutable:

```text
GenesisCapitalSafetyContainmentSpec
GenesisSafetyChangePolicy
GENESIS_SAFETY_CHANGE_POLICY_ROOT
CONSTITUTIONAL_SAFETY_INTEGRITY_TRIGGER_SET_ROOT
```

They are not independent mutable roots.

```text
GENESIS_CONTAINMENT_ADMISSIBILITY_VALID =
  containment catastrophic bounds are constitutional hard-Safety bounds independent of research/Champion/PnL;
  no new-risk/deployment authority exists;
  uncertainty about pre-existing broker footprint is conservatively upper-bounded;
  monitoring/response latency and emergency capability are at least as conservative as feasible before normal Safety exists;
  only reconcile/cancel-risk-increase/monotonic-reduce-or-close effects are legal;
  research/outcome cannot widen containment bounds or disable watchdog;
  UNKNOWN => containment stays fail-closed and normal new risk remains denied
```

`GenesisSafetyChangePolicy` must satisfy SAFETY_CHANGE_POLICY_ADMISSIBILITY_VALID at SystemGenesis.

Genesis ChallengePolicy #0 freezes bootstrap comparator, DECISION_UTILITY_ACCOUNTING_ROOT, COMPARATIVE_EVALUATION_POPULATION_ROOT, PROMOTION_ERROR_CONTROL_POLICY_ROOT, CHALLENGE_ALLOCATION_ORDER_RULE_ROOT and eligibility/universe/error-spending/stopping/renewal before challenger outcome.

```text
BOOTSTRAP_COMPARATOR_ADMISSIBILITY_VALID =
  real incumbent/deployed legacy policy -> actual reachable behavior;
  else SystemGenesis no-action/no-new-risk reference;
  no synthetic weak post-research comparator;
  unidentified common-population comparator utility => Promotion denied
```

Genesis containment grants no new-risk/deployment authority. With possible pre-existing/orphan footprint it mandates immediate bootstrap reconciliation/observation, conservative risk, cancel risk-increasing conditionals, monotonic reduce/close. No FamilyLifetimeLedger at genesis.

Other legal genesis exactly:

```text
PreGenesisScientificStateManifest=A-PREGENESIS-IMPORT
LegacyScientificStateCorrectionRecord=A-LEGACY-RECONCILE
root policy/kernel replacement=A-TRUST-ROLE-ROTATE[ROOT]
RoleManifest+PrincipalRoleBindingRecord=A-TRUST-ROLE-ROTATE[ROLE]
VerifiedAuthorityRecord=A-AUTHORITY-ISSUE
IntegrityDefectRecord=A-INTEGRITY-AUDIT[DEFECT_RECORD]
RuntimeIdentityManifest=A-RUNTIME-IDENTITY-ATTEST[RUNTIME_ATTESTATION_KEY]
RuntimeReconciliationRecord=A-RUNTIME-RECONCILE[BROKER_OBSERVATION_ID]
OperationalCompletenessRecord=A-INTEGRITY-AUDIT[OPERATIONAL_COMPLETENESS]
SafetyContractChangeProposalRecord=A-SAFETY-CONTRACT-PREPARE[SAFETY_CHANGE_ATTEMPT_KEY]
CapitalSafetyContract=A-SAFETY-CONTRACT-FREEZE[INITIAL|MIGRATION]
SafetyContractBootstrapManifest/SafetyContractMigrationManifest=embedded matching freeze
Problem/ResearchEpisode/Hypothesis/Candidate=A-CREATE
ResearchContract=A-CONTRACT-DRAFT
ResearchFamilyCharter+FamilyBootstrapReservationSlot=A-RESEARCH-FAMILY-ASSIGN
later FamilyRelationPolicy=A-RELATION-POLICY-FREEZE
RelationCoverageManifest=A-RELATION-COVERAGE-FREEZE
RelationGateSpec+RelationDecision=A-RELATION-SPEC-FREEZE
DebtGroupReconciliationRecord=A-FAMILY-DEBT-LINK
ResearchProgram+ProgramBudgetReservation=A-PROGRAM-BUDGET[PROGRAM_GENERATION_SLOT_KEY]
FamilyLifetimeLedger #0=A-PROGRAM-CREATE
EvidenceSnapshot=A-EVIDENCE-REGISTER[EVIDENCE_KEY]
EvidenceExposureEvent=A-EVIDENCE-EXPOSURE-RECORD
ProvenanceAttestation/ProspectiveIsolationAttestation=A-INTEGRITY-AUDIT[EVIDENCE_ATTESTATION_KEY]
ProofDependencyInvalidationRecord=A-INTEGRITY-AUDIT[PROOF_DEPENDENCY]
EvidenceReservation[VALIDATION]+CandidateProofEpisode+PROOF_RESERVATION_ROOT=A-EVIDENCE-RESERVE[VALIDATION]
EvidenceReservation[SHADOW]=A-EVIDENCE-RESERVE[SHADOW]
ShadowEpisode=A-SHADOW[SHADOW_GENESIS]
Experiment=A-LOCK[EXPERIMENT_GENESIS]
SearchGenerationBatchManifest/SearchActionEvent=A-RESEARCH-ACTION-ACCOUNT
SearchNode=A-RESEARCH-EVAL[SEARCH_GENESIS]
SearchCompletenessProof=A-SEARCH-CLOSURE[SEARCH_CLOSURE_OPPORTUNITY_KEY]
CriticRecord=A-CRITIC
ScientificAdjudicationRecord=A-ADJUDICATE
GovernorRecord=A-GOVERN
CapabilityArtifact+CapabilityActivationEpisode=A-CAPABILITY-DESIGN
ChampionChallengeAttempt=A-CHALLENGE-REGISTER[CHALLENGE_ATTEMPT_SLOT_KEY]
PromotionTransaction=A-PROMOTE[PROMOTED only]
RollbackTransaction=A-ROLLBACK
DeploymentActivationEpisode=A-SAFETY-PREFLIGHT[DEPLOYMENT_EPISODE_KEY]
CapitalSafetyObservationRecord=A-SAFETY-OBSERVE[SAFETY_OPPORTUNITY_KEY]
ActivationIntent=A-CAPITAL-ACTIVATE
DecisionInputRecord=A-DECISION-INPUT-PUBLISH
DecisionStateRevision=A-DECISION-STATE-INIT/UPDATE
DecisionRecord+conditional CapitalActionEpisode=A-ACTIVE-DECIDE
CapitalRiskReservation=A-CAPITAL-ACTION-AUTHORIZE/A-CAPITAL-AUTHORIZE[ACTIVATION]
ExecutionIntent+ExecutionSettlementRecord=A-CAPITAL-ORDER
RecoveryExecutionIntent=A-CAPITAL-ACTION-RECOVER
CapitalActionRecoveryRecord=A-CAPITAL-ACTION-RECOVER/A-RUNTIME-RECONCILE
EmergencyFlatEvent=A-EMERGENCY-FLAT
BrokerMutationRecord=owning broker authority before send
```

Embedded subobjects:

```text
GovernanceRoot generation -> GovernanceRootRotationPolicy
ResearchContract LOCK -> CONTRACT_CLAIM_CLASS_FLOOR, ClaimAdmissibilitySpec,
                         ADMISSIBILITY_DIMENSION_APPLICABILITY_ROOT,
                         CounterfactualIdentificationSpec where required,
                         CONTRACT_RISK_FLOOR, ValidationFamilyManifest,
                         ValidationDisclosurePlan, MultiplicityPlan/SearchTreeBudget,
                         CriticSpec, PromotionGateSpec, EmbargoInformationFlowManifest where claimed
Candidate FROZEN -> ExecutionContract, DecisionInputProducerManifest,
                    trigger/cadence/opportunity-input closure,
                    CANONICAL_STATE_ADVANCE_SCHEDULE_ROOT, state initializer/updater/RNG,
                    execution/activation derivation, runtime/capability/deployment-control specs,
                    LIVE_BEHAVIOR_SEMANTICS_ROOT, CANDIDATE_CLAIM_CLASS,
                    CANDIDATE_RISK_CLASS, DEPLOYMENT_TARGET_POPULATION_ROOT,
                    CANDIDATE_ACTION_ENVELOPE_ROOT, CANDIDATE_RESULT_ACCESS_CUTOFF_RULE_ROOT
CandidateProof VALIDATION_RESERVED -> PROOF_RESERVATION_ROOT,
                                      PLANNED_PROOF_TARGET_POPULATION_ROOT,
                                      PLANNED_PROOF_ACTION_ENVELOPE_ROOT,
                                      PROOF_AUTHORITY_NARROWING_RULE_ROOT
ChallengeAttempt REGISTERED/PREVALIDATION_BLOCKED -> CHALLENGE_ALLOCATION_ORDER_KEY,
                                                     CHALLENGE_SELECTION_DEBT_CHARGE_ROOT,
                                                     CHALLENGE_ERROR_SPEND_ALLOCATION_ROOT,
                                                     PROMOTION_ERROR_CONTROL_INSTANCE_ROOT where validation remains eligible
ScientificAdjudicationRecord -> PROOF_AUTHORIZED_DEPLOYMENT_POPULATION_ROOT,
                                PROOF_AUTHORIZED_ACTION_ENVELOPE_ROOT,
                                FINAL_COMPARATIVE_EVALUATION_ROOT,
                                FINAL_COMPARATIVE_DECISION_UTILITY_ROOT
CandidateProof VALIDATION_CLOSED -> ProofBundle
Governor accepted proof -> PROOF_RELIANCE_ROOT
PromotionTransaction -> CHAMPION_SELECTION_RELIANCE_ROOT
Champion generation -> ChampionChallengePolicy + ChampionRollbackPlan/NO_PLAN;
                       ChallengePolicy freezes PROMOTION_COMPARATOR_ROOT + DECISION_UTILITY_ACCOUNTING_ROOT + COMPARATIVE_EVALUATION_POPULATION_ROOT + PROMOTION_ERROR_CONTROL_POLICY_ROOT + CHALLENGE_ALLOCATION_ORDER_RULE_ROOT
Safety authorization -> deterministic ProtectiveDependencyPlan/NO_PLAN_REQUIRED
Safety PREPARE -> SafetyContractChangeProposalRecord binds expected root + attempt generation + NO_CHANGE/PREPARED/SATISFIED_BY_SUPERSEDING_CHANGE disposition
Safety INITIAL/MIGRATION -> matching Safety manifest + immutable SafetyMonitoringSpec + SafetyChangePolicy
```

Immutable specs cannot be replaced by config load.

## 4. Exact shared writers

```text
TrustedAuthorityRegistry -> A-AUTHORITY-ISSUE / A-AUTHORITY-REVOKE / A-TRUST-ROLE-ROTATE
ResearchFamilyRegistry -> A-RESEARCH-FAMILY-ASSIGN
FamilyRelationPolicyRegistry -> A-RELATION-POLICY-FREEZE after #0
RelationRegistry -> A-RELATION-ADJUDICATE
LegacyScientificStateHead -> A-LEGACY-RECONCILE after #0
ExposureLedger -> A-EVIDENCE-EXPOSURE-RECORD / A-LEGACY-RECONCILE[PROVEN_LATE_EXPOSURE]
EvidenceGovernanceHead -> A-EVIDENCE-REGISTER / A-EVIDENCE-RESERVE / A-EVIDENCE-RELEASE / A-EVIDENCE-EXPOSURE-RECORD / A-INTEGRITY-AUDIT[PROVENANCE|ISOLATION|PROOF_DEPENDENCY] / governed A-LEGACY-RECONCILE
ChampionRegistry -> A-PROMOTE[PROMOTED] / A-ROLLBACK
ChampionChallengeLedger -> A-CHALLENGE-REGISTER / A-PROMOTE[NO_PROMOTE|BLOCKED_INVALID|PROMOTED] / A-ROLLBACK
CapabilityRegistry -> A-CAPABILITY-PRODUCTION-ACTIVATE / A-CAPABILITY-RETIRE
DeploymentRegistry -> A-CAPITAL-ACTIVATE / A-CAPITAL-DEACTIVATE / A-EMERGENCY-FLAT / A-RUNTIME-RECONCILE
DecisionInputRegistry -> A-DECISION-INPUT-PUBLISH
DecisionStateRegistry -> A-DECISION-STATE-INIT / A-DECISION-STATE-UPDATE
DecisionRegistry -> A-ACTIVE-DECIDE
OperationalFidelityLedger -> A-INTEGRITY-AUDIT[OPERATIONAL_COMPLETENESS]
CapitalSafetyContractRegistry -> A-SAFETY-CONTRACT-PREPARE / A-SAFETY-CONTRACT-FREEZE / A-INTEGRITY-AUDIT[SAFETY_PROPOSAL_DEFECT]
CapitalSafetyObservationRegistry -> A-SAFETY-OBSERVE
```

FamilyLifetimeLedger writers only:

```text
A-PROGRAM-BUDGET A-PROGRAM-CREATE A-PROGRAM-RENEW
A-FAMILY-DEBT-LINK[LEDGER_OPEN] A-RESEARCH-FAMILY-ASSIGN[RELATED]
A-RESEARCH-ACTION-ACCOUNT A-RESEARCH-EVAL A-SEARCH-CLOSURE
A-EVIDENCE-RESERVE A-EVIDENCE-EXPOSURE-RECORD A-EVIDENCE-RELEASE
A-VALIDATE A-SHADOW A-LEGACY-RECONCILE A-RELATION-ADJUDICATE
A-FAMILY-CLOSE[SEAL] A-FAMILY-INVALIDATE[SEAL]
```

Sealed/absent Ledger retrospective debt link creates immutable DebtGroupReconciliationRecord/future ancestry, never reopens/fabricates Ledger. CapitalRiskReservationLedger writers only A-CAPITAL-ACTION-AUTHORIZE / A-CAPITAL-AUTHORIZE[ACTIVATION] / A-CAPITAL-ACTION-CANCEL / A-DEPLOYMENT-CANCEL / A-CAPITAL-ORDER / A-CAPITAL-ACTIVATE / A-CAPITAL-ACTION-RECOVER / A-CAPITAL-DEACTIVATE / A-EMERGENCY-FLAT / A-RUNTIME-RECONCILE. BrokerMutationRegistry writers only A-CAPITAL-ORDER / A-CAPITAL-ACTIVATE / A-CAPITAL-ACTION-RECOVER / A-CAPITAL-DEACTIVATE / A-EMERGENCY-FLAT / A-RUNTIME-RECONCILE. No generic writer.

## 5. Legacy / Family / Program / search multiplicity

Pre-genesis import captures known prior scientific/search/validation/selection history. Material unknown => LEGACY_SEARCH_DEBT=UNKNOWN. Genesis closes import cutoff to genesis completely or UNKNOWN. Late reconciliation append-only/conservative and may stale current reliance without rewriting history.

Family relation: genesis UNKNOWN/UNPROVEN => RELATED_FOR_PRIVILEGE, UNRELATED_SUPPORTED denied; first Family inherits legacy debt. `RELATION_KEY` one-slot canonical pair/policy/purpose. FULL unrelated privilege requires pre-outcome policy+coverage+gate+first adjudication+SoD+no unaccounted shared genealogy+current debt/selection ancestry. Post-outcome first relation cannot grant FULL. Future-evidence-only cannot reset prior budget/holdout/search/selection debt. Late invalid FULL conservatively links debt and stales affected privileges; sealed Ledger never reopens.

Program:

```text
NEXT_PROGRAM_GENERATION=1+max(all generations ever allocated including cancelled/invalidated)
PROGRAM_GENERATION_SLOT_KEY=hash(Family,target generation)
```

One Program+Reservation per slot; stale slot historical/not reused. INITIAL and LATER prerequisites remain exact; no new budget in QUIESCING/INVALIDATING/terminal Family.

Whole search tree: Contract locks MultiplicityPlan/SearchTreeBudget over all adaptive choices/generator calls/evaluations/stopping/validation/outcome-motivated governance. Outcome-aware adaptive generation claimed as bounded search occurs inside SearchInstrumentation. Private post-outcome reasoning outside capture => hidden alternatives UNKNOWN.

```text
SearchGenerationBatch PREAUTHORIZED=A-RESEARCH-ACTION-ACCOUNT[GENERATION_PREAUTH]
PREAUTHORIZED->GENERATING=A-RESEARCH-ACTION-ACCOUNT[GENERATION_START]
GENERATING->CAPTURE_CLOSED=A-RESEARCH-ACTION-ACCOUNT[GENERATION_CLOSE+CAPTURE_COMPLETE]
PREAUTHORIZED->CANCELLED=A-FAMILY-QUIESCE[not started]
PREAUTHORIZED->INVALIDATED=A-INTEGRITY-AUDIT[PRESTART_DEFECT|ANCESTRY_INVALIDATION]
GENERATING->INVALIDATED=A-INTEGRITY-AUDIT[OVERFLOW|PARTIAL|UNKNOWN|ANCESTRY_INVALIDATION]

SearchNode COMMITTED=A-RESEARCH-EVAL[SEARCH_ACTION_PREACCOUNTED]
COMMITTED->EXECUTING=A-RESEARCH-EVAL
COMMITTED->CANCELLED=A-FAMILY-QUIESCE[NOT_STARTED]
EXECUTING->RESULT_LOGGED=A-RESEARCH-EVAL[SEALED]
RESULT_LOGGED->RESULT_DISCLOSED=A-RESEARCH-EVAL[EXPOSURE_ACCOUNTED]
RESULT_DISCLOSED->CLOSED=A-RECORD-CLOSE
COMMITTED->INVALIDATED=A-INTEGRITY-AUDIT[PRESTART_DEFECT|ANCESTRY_INVALIDATION]
EXECUTING->INVALIDATED=A-INTEGRITY-AUDIT[EXECUTION_DEFECT|ANCESTRY_INVALIDATION]
RESULT_LOGGED->INVALIDATED=A-INTEGRITY-AUDIT[INTEGRITY_DEFECT|ANCESTRY_INVALIDATION]
```

Start durable before generator; all emitted alternatives captured before selection; failure after start retains debt; unprovable extent => UNKNOWN. Post-outcome privilege choice defaults outcome-motivated unless precommitted. Clean stopping only frozen rule/budget/precommitted non-outcome terminal.

```text
SEARCH_STOP_EVENT_KEY=hash(Contract,frozen stop/budget rule,first deterministic terminal event,Program/Family generation)
SEARCH_CLOSURE_OPPORTUNITY_KEY=hash(stop event,complete Action/Generation/Node set through stop,MultiplicityPlan/SearchTreeBudget)
```

One closure per opportunity; mutable post-stop heads payload not key.

## 6. Evidence / proof / admissibility / identification

### 6.1 Evidence DGP / intervention

```text
POLICY_GENERATED = material deployed policy/action/exposure/state dependency on inclusion,label,horizon,censoring,transform,availability,sampling/selection,terminal state
EXOGENOUS = absence positively proven
UNKNOWN => POLICY_GENERATED for causal/policy-value/action-comparison
```

Mixed-policy data binds complete policy/deployment set + segmentation.

```text
INTERVENTION_CONTEXT_ROOT=hash(own intervention/action lineage,
  external/manual/operator/co-intervention lineage,
  external broker/account mutations, material exogenous intervention/event lineage,
  information-time+segmentation, OR proven NO_MATERIAL_CO_INTERVENTION)
POLICY_GENERATED_EVIDENCE_PROVENANCE_ROOT=hash(complete DGP set,complete Champion/deployment set,
  segmentation,action-selection,censoring,INTERVENTION_CONTEXT_ROOT,own market impact/proven none,action/exposure/info-time)
```

Evidence key binds source/universe/content/transform/info-time+DGP/exogenous+intervention. Same key same payload existing; conflict defect. Provenance Audit verifies; Evidence cannot self-attest.

### 6.2 Attestation / consumption
One `EVIDENCE_ATTESTATION_KEY` per evidence/class/state/method-dependencies; retry/time/session cannot mint. Successor needs materially new state and explicit prior-adverse resolution. Unresolved FAIL/BLOCKED/UNKNOWN blocks. Validation allocation frozen; relevant access observed; no holdout double reserve; consumption eligibility derives complete ancestry/exposure/reservation/relation/multiplicity/Legacy.

### 6.3 Candidate↔Contract eligibility / access boundary
Candidate freeze is THINK and seals immutable Candidate semantics including `CANDIDATE_RESULT_ACCESS_CUTOFF_RULE_ROOT`, not production status.

```text
CANDIDATE_RESULT_ACCESS_BOUNDARY_PROVEN =
  cutoff rule is bound to governed Search/Evidence/Validation/Shadow/Disclosure access surfaces;
  applicable EmbargoInformationFlowManifest/access-control boundary is current where result isolation is claimed;
  known human/auditor access is represented;
  material unobserved/private access that cannot be ruled out => UNKNOWN/FALSE

FIRST_RELEVANT_CANDIDATE_RESULT_ACCESS_EVENT = minimum canonical matching event across governed histories
NO_RELEVANT_CANDIDATE_RESULT_ACCESS_YET = boundary proven AND no matching event exists at exact child-Contract lock CAS
```

Child Contract lock atomically compares relevant Search/Exposure/Validation/Disclosure heads and access-boundary root. If any advances before lock commit, upgrade transaction loses.

```text
CANDIDATE_CONTRACT_PRODUCTION_ELIGIBILITY(Candidate,Contract)=ELIGIBLE only if
  Contract current/in Candidate genealogy;
  effective claim/risk covered;
  mandatory admissibility/identification prospectively locked;
  Candidate-specific upgrade Contract locked with CANDIDATE_RESULT_ACCESS_BOUNDARY_PROVEN
     and NO_RELEVANT...YET;
  search/debt/selection ancestry includes Contract choice;
  no invalidation
```

High-risk/weak Candidate remains researchable. Prospectively adequate child Contract can qualify same Candidate without mutation; post-access cannot rescue. Promotion reservation binds exact eligible Contract.

### 6.4 Planned authority / narrowing / final comparative utility / Challenge allocation

```text
PLANNED_PROOF_TARGET_POPULATION_ROOT=prospective maximum deployment population
PLANNED_PROOF_ACTION_ENVELOPE_ROOT=prospective maximum action/resource/capital/economics envelope
PROOF_AUTHORITY_NARROWING_RULE_ROOT=hash(frozen support/overlap,identification/stability/feasibility rules,
  deterministic subset mapping,tie-break,subgroup/scale selection accounting,frozen transport/scaling relations)
```

No post-outcome invented subgroup. Enumerated alternatives prospectively search/selection-accounted.

`PROOF_RESERVATION_ROOT` binds exact Candidate+eligible Contract, effective class/risk, admissibility/applicability/identification, SearchClosure/multiplicity/debt, Evidence/DGP/intervention, comparator/accounting/comparative population, PROMOTION_ERROR_CONTROL_POLICY_ROOT, CHALLENGE_ALLOCATION_ORDER_RULE_ROOT, planned roots, narrowing rule, attestations, Legacy/SoD, promotion target/policy where applicable. Ordering reservation -> eligible opportunity -> canonical allocation obligation -> Attempt/accounting -> Validation if allowed.

For each ChallengePolicy:

```text
CHALLENGE_ALLOCATION_ORDER_RULE_ROOT=hash(
  canonical first-eligibility information-time definition,
  stable eligible-opportunity tie-break,
  batching rule,
  frozen error-spending/renewal order semantics,
  frozen pre-validation terminal debt/error-spend disposition rule)

CHALLENGE_ALLOCATION_ORDER_KEY=tuple(FIRST_ELIGIBLE_INFORMATION_TIME,
  canonical eligible-opportunity identity under frozen tie-break)
```

`FIRST_ELIGIBLE_INFORMATION_TIME` is first canonical frontier at which all pre-validation eligibility prerequisites are available to governed Promotion universe. Process scheduling/API/thread/CAS order are not key material; later knowability cannot backdate.

Once an opportunity first enters the eligible promotion universe it creates an append-only `CHALLENGE_ALLOCATION_OBLIGATION` under its order key. Later Candidate/Contract/incumbent/dependency invalidation cannot delete that historical obligation. It can only change its allowed accounting disposition.

```text
NEXT_CANONICAL_CHALLENGE_ALLOCATION_SLOT = minimum unsettled obligation under order key
CHALLENGE_ALLOCATION_OBLIGATION_COVERAGE_CURRENT = every obligation through registration frontier has canonical settlement state or is the exact next slot
```

A-CHALLENGE-REGISTER may settle the next slot in exactly one of two modes:

```text
REGISTERED = current validation/promotion eligibility still holds; atomically allocate Challenge error wealth + selection debt + exact error-control instance; validation may later start
PREVALIDATION_BLOCKED = obligation previously arose but validation is now deterministically unavailable before validation/outcome start due current incumbent/dependency/integrity/cancel cause; atomically apply the frozen selection-debt charge and frozen no-outcome error-spend disposition; no validation/Promotion authority
```

PREVALIDATION_BLOCKED cannot be chosen from PnL or validation outcome; no validation/result access may have started. If relevant outcome was accessed, conservative full selection/error-debt treatment applies. Missing registration cannot make the obligation disappear; later allocation slots are denied until earlier obligation receives canonical accounting.

Stable slot identity:

```text
CHALLENGE_ATTEMPT_SLOT_KEY=hash(Champion slot,incumbent,eligible opportunity,CHALLENGE_ALLOCATION_ORDER_KEY,
  PROOF_RESERVATION_ROOT,exact proof Contract,policy generation,
  comparator/accounting/population/error-policy,CHALLENGE_ALLOCATION_ORDER_RULE_ROOT,
  planned roots,narrowing rule)
```

For REGISTERED, A-CHALLENGE-REGISTER requires slot = NEXT_CANONICAL, slot absent, exact current ChallengeLedger pre-state and computes atomically:

```text
CHALLENGE_SELECTION_DEBT_CHARGE_ROOT
CHALLENGE_ERROR_SPEND_ALLOCATION_ROOT=hash(policy,ledger pre-state,order key,whole-search debt,frozen spending method,allocated share)
PROMOTION_ERROR_CONTROL_INSTANCE_ROOT=hash(error policy,Candidate+Contract,effective claim/risk,false-Promotion loss,
  whole-search debt,allocation root,required replication/prospective class)
ChampionChallengeAttempt[REGISTERED]
```

For PREVALIDATION_BLOCKED it atomically writes selection-debt charge + frozen no-outcome error-spend disposition + terminal Attempt state under the same stable slot. Concurrent different opportunities cannot reverse order. Concurrent loser on same slot gets existing canonical payload; conflict=>IntegrityDefect.

Adjudication applies exact frozen narrowing:

```text
final population <= planned population
final action envelope <= planned action envelope
PROOF_AUTHORITY_NARROWING_RULE_APPLIED_EXACTLY=true
```

Then seals:

```text
FINAL_COMPARATIVE_EVALUATION_ROOT=hash(final population,final action envelope,
  incumbent comparator,utility accounting,comparative-population projection,narrowing rule,
  multiplicity/selection adjustment,PROMOTION_ERROR_CONTROL_INSTANCE_ROOT)
FINAL_COMPARATIVE_DECISION_UTILITY_VALID = same accounting on exact final deployment population/action semantics,
  frozen selection adjustment + exact Attempt-bound risk-calibrated error instance,
  lower/decision-relevant incremental-utility bound > 0
```

Broad/planned utility cannot justify different final context. UNKNOWN=>no Promotion. Proof reliance seals exact Candidate+Contract/search/reservation/applicability/identification/comparator/accounting/error-policy+order+instance+allocation/planned/narrowing/final comparative/final authority/DGP/intervention/Legacy/SoD/behavior-runtime roots.

### 6.5 Scientific-method / Promotion admissibility and error control

Claim class/intended use/risk mechanically derived; caller cannot downgrade; material UNKNOWN=>highest plausible. Contract freezes class/risk floors, ClaimAdmissibilitySpec, applicability. Candidate derives stricter class/risk. Mandatory dimensions as applicable: target validity, uncertainty/calibration, support/overlap/sample adequacy, robustness/stability/concentration, downside/tail/failure risk, costs/frictions, OOD/regime/transfer, execution/deployment feasibility, prospective/shadow. Critic may verify precommitted N/A, not invent it.

```text
PROMOTION_ERROR_CONTROL_POLICY_ROOT=hash(deterministic mapping from effective claim/risk + false-Promotion loss + search/Challenge debt/spend state
  to uncertainty/robustness criterion + prospective/replication class, spending/renewal, tie-break, UNKNOWN rule)
PROMOTION_ERROR_CONTROL_ADMISSIBILITY_VALID = mapping frozen pre-outcome; allocation order frozen; exact instance derived pre-validation;
  tolerance justified by risk/decision loss; interested roles cannot weaken; whole-search+challenger multiplicity included;
  materially unresolved/negative utility cannot be successful; UNKNOWN=>no Promotion
```

`SCIENTIFIC_METHOD_ADMISSIBILITY_VALID` requires valid class/risk/applicability/error-control where relevant/every mandatory dimension resolved/no acceptance despite material failure.

ChallengePolicy freezes comparator/accounting/comparative population/error policy/allocation order before challenger outcomes. Action-changing Promotion is POLICY_VALUE/ACTION_COMPARISON.

```text
PROMOTION_ADMISSIBILITY_VALID = SCIENTIFIC_METHOD_ADMISSIBILITY_VALID
  AND PROMOTION_ERROR_CONTROL_ADMISSIBILITY_VALID
  AND CHALLENGE_ALLOCATION_ORDER_CURRENT
  AND CHALLENGE_ALLOCATION_OBLIGATION_COVERAGE_CURRENT
  AND exact Candidate↔Contract eligibility
  AND bootstrap comparator valid where applicable
  AND exact policy comparator/accounting/population/error-policy/order-rule = proof/Attempt/Promotion
  AND exact REGISTERED Attempt error allocation+instance
  AND final authority deterministic subset under narrowing
  AND FINAL_COMPARATIVE_DECISION_UTILITY_VALID
  AND deployment population/action match
  AND applicable counterfactual identification
  AND applicable cost/friction/support/stability/downside/execution/OOD/prospective/shadow requirements
```

No universal trading threshold. Frozen but substantively inadmissible gate invalid.

### 6.6 Counterfactual identification
For CAUSAL/POLICY_VALUE/ACTION_COMPARISON including action-changing Promotion, CounterfactualIdentificationSpec freezes alternatives/estimand/target, DGP/assignment, censoring, support, intervention context, interference/co-intervention/confounding, own impact, estimator/replay, independence, falsification/sensitivity, randomized/prospective/shadow requirements.

```text
COUNTERFACTUAL_QUALITY=RANDOMIZED_PROSPECTIVE|SHADOW_PARALLEL|REPLAYABLE_STRUCTURAL|OBSERVATIONAL_IDENTIFIED_BOUNDED|CF_UNOBSERVABLE
COUNTERFACTUAL_IDENTIFIABILITY_VALID=estimand identified from governed Evidence/DGP/intervention context under frozen method + assumptions resolved + quality adequate
```

CF_UNOBSERVABLE cannot support policy/action Promotion. Predictive/descriptive result cannot silently upcast.

## 7. Champion policy / selection / rollback

Candidate freeze seals LIVE_BEHAVIOR_SEMANTICS_ROOT. Packaging/build/time/UUID/logging do not create novelty. Material reachable behavior diff required; UNKNOWN=>same lineage/history.

Policy #0/successors freeze incumbent/comparator/accounting/comparative population/error policy/allocation order, eligibility universe/query, exclusions/normalization, error spending/renewal, nomination, decision/stopping/renewal, inherited Challenge debt/cutoff before challenger outcomes. Cross-Family independence does not remove slot multiplicity.

Every first-eligible opportunity creates monotone Challenge allocation obligation. A-CHALLENGE-REGISTER may occupy only NEXT_CANONICAL slot as REGISTERED or PREVALIDATION_BLOCKED; allocation/instance are payload, never scheduler key. Terminal PREVALIDATION_BLOCKED/CANCELLED/INVALIDATED/NO_PROMOTE/BLOCKED_INVALID/PROMOTED retain applicable selection debt. Missing earlier obligation settlement makes registration/selection completeness false; it cannot be skipped. First canonical policy decision mandatory; no market/PnL delay. PROMOTED requires REGISTERED Attempt, current incumbent, exact roots/order, final subsets, final comparative utility, Promotion admissibility/identification. Selection reliance seals all. Rollback exact displaced incumbent/current proof+selection/first-eligible/performance-blind/one-shot/no source-loop.

## 8. Operational identity / completeness / ACT->THINK

Selected != deployed. Selection change blocks old new-risk/stales old risk-increasing conditionals; new selection needs fresh DeploymentEpisode.

```text
INPUT_EVENT_KEY=hash(source_id,canonical event,revision,event-time)
STATE_REVISION_KEY=hash(Deployment generation,predecessor state,canonical batch,frozen updater,RNG)
DECISION_OPPORTUNITY_KEY=hash(Deployment generation,runtime semantics,canonical trigger/timer,required input closure,state frontier,action policy)
DEPLOYMENT_OPPORTUNITY_KEY=hash(selected Champion,deployment-control policy,canonical trigger/timer,runtime/Safety prerequisites,final proof population,final action envelope)
DEPLOYMENT_EPISODE_KEY=hash(deployment opportunity,Champion,Safety generation,runtime semantics)
RUNTIME_ATTESTATION_KEY=hash(runtime semantics,attestation trigger/cadence,dependency set)
```

Only cutoff-available info usable. Missing input/Decision/Deployment/Attestation marks Fidelity. Frozen ordering prevents replay/fork. Every deployment opportunity has NO_ACTIVATE/BLOCKED/PLANNED. Deployment inside final proof authority; Safety cannot widen science.

Every expected Input/State/Decision/SafetyObservation/Execution/Deployment/Attestation/Reconcile/broker/exposure event exists or marks Fidelity. External/manual exposure mutation is BROKEN. Champion operational-history coverage includes all same-lineage deployment/outcome/intervention/gaps.

Production outcome used for research traverses governed Evidence DGP+intervention/exposure/Contract/Search accounting/ancestry. Direct ACT->THINK bypass denied.

## 9. Proof/selection reliance to deployment

Deployment proof eligibility = valid proof reliance/no invalidation/behavior-runtime match/final authority current. Selection eligibility = valid selection reliance/no invalidation. Preflight/authorize/activate require selected Champion, current Safety/runtime/admissibility/identification/final population-action match.

Mandatory stale triggers: selected!=deployed; invalid proof/selection; outside final authority; Safety unusable including invalid change policy; runtime invalid; Fidelity/Completeness break; missing/unsafe Safety observation; emergency feasibility stale. New risk denied; pending risk increase cancel/reconcile; existing exposure deterministic reduction/deactivation. Timing performance-blind.

## 10. Capital Safety / ongoing observation / change control

### 10.1 Genesis containment + expected Safety-change roots / policy / remediation

Genesis containment only while SafetyRegistry EMPTY and possible pre-existing/orphan footprint. Reconcile, conservative accounting/monitoring, cancel risk-increasing conditionals, monotonic reduce/close. No new risk/Deployment.

```text
GENESIS_CONTAINMENT_TRIGGER_EVENT_KEY=hash(SystemGenesis,broker/account scope,canonical bootstrap observation/change or watchdog,trigger role)
```

Immediate bootstrap opportunity mandatory where footprint possible; unknown broker state=>BLOCKED_UNKNOWN/no new risk.

Current change policy = GenesisSafetyChangePolicy while registry EMPTY else current SafetyContract SafetyChangePolicy.

```text
SAFETY_CHANGE_POLICY_ADMISSIBILITY_VALID = covers every material invalidation/migration cause for scope/risk model/monitoring/latency/emergency feasibility/broker/runtime/native protection/governance/catastrophic bounds;
  each cause deterministic disposition+deadline; NO_CHANGE impossible when regime invalid/UNKNOWN;
  no performance preference except genuine Safety risk input; UNKNOWN coverage=>fail closed
```

`CONSTITUTIONAL_SAFETY_INTEGRITY_TRIGGER_SET_ROOT` is independent and covers broken/UNKNOWN change policy, contract governance/SoD/authority, monitoring/emergency machinery, Genesis containment. Such trigger forces repair; NO_CHANGE forbidden while defect remains; existing risk fails safe/new risk denied.

```text
EXPECTED_SAFETY_CHANGE_ROOT_SET(frontier)=deterministic projection of every canonical policy/Genesis/INITIAL/constitutional change trigger through governed trigger-information frontier
SAFETY_CHANGE_ROOT_KEY=hash(Safety generation or EMPTY at original trigger frontier,canonical trigger/cause lineage,protected-domain lineage,
  original admissible change-policy root OR constitutional repair root,GovernanceRootRotationPolicy generation)
```

Root exists semantically at trigger frontier even with no proposal record. Generation change does not mint a duplicate root for the same still-unresolved underlying cause lineage; the original root remains the accounting identity until terminally resolved. A materially distinct later cause event may create a distinct root.

`SAFETY_CHANGE_EXPECTED_ROOT_COVERAGE_CURRENT` requires every expected root through frontier has active attempt or timely terminal resolution. Missing proposal cannot erase root.

```text
UNRESOLVED_SAFETY_CHANGE_OPPORTUNITY_PRESENT = any expected root without terminal NO_CHANGE, CONSUMED, or SATISFIED_BY_SUPERSEDING_CHANGE
```

From root appearance to terminal resolution, normal new risk denied. With live footprint, trigger also creates Safety observation/response obligation.

Attempt g0 state frozen from root-trigger frontier:

```text
SAFETY_CHANGE_ATTEMPT_KEY[g0]=hash(root,0,canonical prerequisite/input/capability state at trigger frontier)
```

A-PREPARE may only fill expected slot; cannot choose later g0 state. NO_CHANGE only if regime admissible for exact cause and not prohibited cause. PREPARED mechanically derived and schedules handoff/deadlines; missing/late is Safety/Fidelity defect.

Freeze key:

```text
SAFETY_CONTRACT_FREEZE_ELIGIBILITY_KEY=hash(root,active attempt,proposed root,frozen freeze rule,
  first canonical frontier where mapping/readiness/handoff/attestations current)
```

First eligible frontier mandatory; no retry/time/PnL remint.

#### Stale/integrity remediation and concurrent-root interaction

A PREPARED attempt can become:

```text
INVALIDATED_STALE = objective prerequisite/current-generation state advance before freeze
INVALIDATED = governed proposal/integrity defect
```

Neither state silently releases the expected root. Both remain unresolved until one of the following canonical paths:

1. **Material successor attempt** — after positively material prerequisite/governance remediation state:

```text
next attempt generation=g+1
SAFETY_CHANGE_ATTEMPT_KEY[g+1]=hash(root,g+1,material remediation/successor state root,exact prior invalid/stale cause)
```

Creating g+1 and settling prior attempt as SUPERSEDED_BY_SUCCESSOR are atomic. For `INVALIDATED`, material remediation must include exact defect-resolution evidence and any required independent Audit/Root attestation. Same remediation state=>same key; conflict=>defect. No blind retry.

2. **Satisfied by another Safety generation** — if a different concurrently valid Safety root freezes first and the new current Safety generation positively proves that this root's exact cause is already resolved:

```text
SATISFIED_BY_SUPERSEDING_CHANGE_VALID =
  current Safety generation was independently validly frozen;
  exact original root cause is positively resolved under current scope/risk/monitoring/emergency/governance semantics;
  current SafetyChangePolicy + constitutional constraints are admissible;
  any independent Audit/Root proof required by the cause exists;
  no unresolved material aspect remains;
  INITIAL_REQUIRED may use this only if current SafetyContract satisfies every INITIAL requirement;
  constitutional repair may use it only if the constitutional defect is positively resolved
```

A-PREPARE atomically writes terminal `SATISFIED_BY_SUPERSEDING_CHANGE` for the expected root/active or absent attempt slot. This is not NO_CHANGE and cannot be used merely because a newer generation exists.

For every successor attempt after Safety generation/policy changed:

```text
SUCCESSOR_POLICY_COMPATIBILITY_VALID =
  successor proposal is based on current Safety generation as migration predecessor where applicable;
  satisfies current admissible SafetyChangePolicy and current catastrophic bounds;
  also preserves/fulfills the original root cause obligation;
  cannot widen or restore authority forbidden by either current or original safety constraints;
  UNKNOWN/conflict=>no freeze
```

Thus an old root cannot later use an obsolete/weaker policy to overwrite a stronger current Safety generation. If another migration already resolves it, terminal satisfaction is used; if not, successor uses current generation plus original obligation.

```text
SAFETY_CONTRACT_CHANGE_EXECUTION_TIMELINESS_VALID = first eligibility consumed without discretionary delay OR exact invalid/stale remediation/superseding-resolution path active; overdue unresolved root remains blocked
```

Genesis liveness:

```text
INITIAL_SAFETY_REQUIRED_KEY=hash(SystemGenesis,GENESIS_SAFETY_CHANGE_POLICY_ROOT,first canonical bootstrap readiness frontier,required initial inputs/capabilities available or conservatively bounded)
```

Once ready, INITIAL cause automatically enters expected root set; NO_CHANGE forbidden. Before readiness containment continues/no new risk. INITIAL freezes after footprint closed or atomic containment handoff. No zero-monitoring interval.

With live footprint, missing/late disposition/readiness/freeze/remediation creates BLOCKED_UNKNOWN/stronger deterministic response.

### 10.2 Safety model / monitoring / feasibility

Every change requires causality, expected-root coverage, policy/constitutional admissibility, deterministic proposal, remediation compatibility, completeness/timeliness. INITIAL hard bounds/scopes/distinct Safety-Root/anti-rescue; MIGRATION complete actual/conditional/reserved/executing/uncertain/protective mapping; no risk disappearance/widening rescue.

SafetyMonitoringSpec + SafetyChangePolicy freeze scope/risk/emergency/change dependency graphs, triggers/cadence, input/freshness, batching/frontier, risk formulas, protective validity, disposition/response/completion, missing rule, latency, emergency capabilities, change/freeze rules.

```text
SAFETY_RISK_MODEL_ADMISSIBILITY_VALID = complete material drivers + conservative uncertainty; nonconservative constant-like model invalid
SAFETY_TRIGGER_COVERAGE_COMPLETE = every material risk/emergency/change dependency has event trigger or admissible cadence
SAFETY_MONITORING_LATENCY_ADMISSIBLE = observation+response bounded by risk timescale/catastrophic envelope
SAFETY_EMERGENCY_RESPONSE_FEASIBILITY_VALID/CURRENT = required response feasible under current broker/runtime/native protection/reconciliation/monotonic semantics; capability change triggers recheck
```

Handoff observation requires exact active PREPARED/current proposed frontier while old Safety/Genesis containment remains authoritative. Handoff complete requires old monitoring through freeze, new topology/watchdog/feasibility ready, current proposed observation when live, no zero-monitoring interval.

### 10.3 Risk scope / direct frontier / ongoing observation

Capital risk scope includes every applicable broker/account/symbol/instrument/Champion/deployment/portfolio/strategy/correlation/concentration scope; unknown=>deny.

```text
RISK_BEARING_FOOTPRINT_PRESENT=actual/live-conditional/authorized/executing/uncertain risk, risk-mutating protective, active/activating Deployment
ONGOING_SAFETY_OBSERVATION_REQUIRED=RISK_BEARING_FOOTPRINT_PRESENT
```

Every new-risk action/activation has canonical PRE_RISK_AUTHORIZATION_INPUT_FRONTIER_ROOT over current Safety/spec, exact action, required revisions, broker/reconcile/capability/freshness. First risk needs current SafetyContract and all expected Safety roots terminally resolved; Genesis containment never suffices.

All-scope authorization atomically compares Safety, Deployment, all RiskLedger scope heads, proof/selection, pre-risk frontier, emergency feasibility, expected-root state, latest observation if ongoing, Runtime/reconcile.

```text
RECONCILED_ACTUAL + BROKER_LIVE_CONDITIONAL + AUTHORIZED_RESERVED + EXECUTING_RESERVED + UNCERTAIN_UPPER_BOUND + NEW_ACTION_WORST_CASE <= Safety envelope
```

Partial remainder stays conditional/reserved; ambiguity uncertain.

Every Safety/Genesis trigger creates canonical opportunity independent of Decision/CapitalAction:

```text
SAFETY_TRIGGER_EVENT_KEY=hash(source,canonical event/revision,event-time,trigger role)
EXPECTED_SAFETY_INPUT_SET_ROOT=deterministic producer/event-role set
SAFETY_OPPORTUNITY_KEY=hash(authoritative Safety OR active PREPARED handoff OR GENESIS_CONTAINMENT,
 monitoring/containment spec,scope,deployment/behavior-or-orphan lineage,trigger,expected input set)
```

Actual inputs payload not key; retry/time/session cannot remint. Incomplete/stale/unknown prevents WITHIN.

One record: WITHIN_ENVELOPE / REDUCE / DEACTIVATE / EMERGENCY_FLAT / BLOCKED_UNKNOWN. Non-WITHIN binds deterministic response semantics/key over target scopes/objective/quantity on fresh reconcile/broker semantics/deadline/completion. BLOCKED_UNKNOWN=RECONCILE_THEN_FAILSAFE; blind resend denied.

```text
SAFETY_OBSERVATION_COMPLETENESS_CURRENT=every required opportunity timely recorded
SAFETY_INPUT_FRONTIER_CURRENT=no required event lacks observation through frontier
SAFETY_RESPONSE_OBLIGATION_CURRENT=every non-WITHIN has one first-eligible response active/satisfied
LATEST_REQUIRED_SAFETY_DISPOSITION_PERMITS_RISK=latest timely WITHIN+frontier current+feasibility current+no unresolved response
```

Missing observation or unresolved/overdue expected Safety root with live risk => Fidelity + pending cancel/reconcile + BLOCKED_UNKNOWN/stronger response.

### 10.4 Pending / protective / broker

Risk-increasing pending order remains CapitalAction PENDING_LIVE and reservation CONDITIONAL_LIVE while fillable. Partial fill moves proved fill to actual, remainder stays conditional. Cancel/fill ambiguity UNCERTAIN until reconcile.

Protective plan deterministic; polarity against current exposure. Non-reduce-only standing protection requires governed exposure mutation or proved broker reduce-only/close-only/OCO.

Execution/activation/recovery/deactivation/emergency identities exclude retry/time/session/quote noise. Pre-send risk increase rechecks proof+selection/final action authority/selected-deployed/Safety/pre-risk/ongoing observation/all expected Safety roots resolved/emergency feasibility/Runtime/reconcile/reservation/broker bounds.

```text
BROKER_MUTATION_KEY=hash(authority,owning semantics,account/symbol,CANONICAL_MUTATION_LEG_ID)
BROKER_OBSERVATION_ID=hash(account/broker scope,broker-native observation identity)
```

Untrustworthy observation=>UNKNOWN. Ambiguous mutation reconcile before retry unless repeated reduction independently monotonic-safe. BROKER_FOOTPRINT_CLOSED requires no exposure/live mutating order/inflight ambiguity/committed-or-uncertain reservation/action + current reconciliation.

## 11. Canonical Authority Registry — exhaustive

| Authority | Issuer approval | Executor / holder | Usage | Exact scope / prerequisites | Capital |
|---|---|---|---|---|---|
| A-AUTHORITY-ISSUE | root kernel + target acceptance | root gate | ROOT | exact VAR | NO |
| A-AUTHORITY-REVOKE | root kernel | root gate | ROOT | revoke/continuity/admin | NO |
| A-TRUST-ROLE-ROTATE | root kernel + frozen policy | root gate | ROOT | replacement-first/SoD/admin | NO |
| A-PREGENESIS-IMPORT | Genesis + distinct Audit | bootstrap Audit | ONE_SHOT | Genesis!=Audit | NO |
| A-SYSTEM-GENESIS | Genesis + distinct Audit | Genesis | ONE_SHOT | exact §3 set + admissible Genesis containment/change policy + constitutional triggers + bootstrap comparator/error/order policy | NO |
| A-LEGACY-RECONCILE | Audit + root | Audit | ONE_SHOT | conservative impact | NO |
| A-RUNTIME-IDENTITY-ATTEST | Audit | Audit | ONE_SHOT | canonical attestation/SoD/non-alpha | NO |
| A-SAFETY-CONTRACT-PREPARE | Safety + root | Safety | ONE_SHOT per expected active attempt/terminal-accounting slot | expected root + attempt / deterministic NO_CHANGE, PREPARED, material remediation successor, or SATISFIED_BY_SUPERSEDING_CHANGE | NO |
| A-SAFETY-CONTRACT-FREEZE | Safety + root | Safety | ONE_SHOT | exact active PREPARED + current-generation/current-policy compatibility + first freeze key + handoff/model/latency/feasibility | NO |
| A-SAFETY-OBSERVE | Safety | Safety | SERVICE | CURRENT / ACTIVE_PREPARED_HANDOFF / GENESIS_CONTAINMENT; expected change-trigger completeness | NO |
| A-CREATE | Contract | Research | SERVICE | parent/ancestry/debt/causal | NO |
| A-CONTRACT-DRAFT | Contract | Contract | SERVICE | parent/debt/causal/derived claim semantics | NO |
| A-LOCK | Contract | Contract | EDGE_NONCE | Contract lock/Candidate freeze; child checks access boundary/heads | NO |
| A-RELATION-POLICY-FREEZE | ProgramGov + root | ProgramGov | ONE_SHOT | prospective/causal | NO |
| A-RELATION-COVERAGE-FREEZE | ProgramGov | relation prepare | ONE_SHOT | complete coverage | NO |
| A-RELATION-SPEC-FREEZE | ProgramGov | relation prepare | ONE_SHOT | key/mode/cutoff | NO |
| A-RELATION-ADJUDICATE | ProgramGov issuer | independent adjudicator | ONE_SHOT | positive theorem/controller separation | NO |
| A-RESEARCH-FAMILY-ASSIGN | ProgramGov | ProgramGov | ONE_SHOT | proposed root/relation/debt | NO |
| A-FAMILY-DEBT-LINK | ProgramGov | ProgramGov | ONE_SHOT | OPEN append or SEALED/ABSENT retrospective | NO |
| A-PROGRAM-BUDGET | ProgramGov | ProgramGov | ONE_SHOT | NEXT_PROGRAM_GENERATION + mode | NO |
| A-PROGRAM-CREATE | ProgramGov | ProgramGov | ONE_SHOT | INITIAL reservation/Ledger | NO |
| A-PROGRAM-RENEW | ProgramGov | ProgramGov | ONE_SHOT | LATER reservation/inherited debt | NO |
| A-PROGRAM-CLOSE | ProgramGov | ProgramGov | EDGE_NONCE | stopping/intervention/drain | NO |
| A-FAMILY-CANCEL | ProgramGov | ProgramGov | ONE_SHOT | early drain | NO |
| A-FAMILY-QUIESCE | ProgramGov | ProgramGov | ONE_SHOT | stop/stale new starts/drain | NO |
| A-FAMILY-CLOSE | ProgramGov | ProgramGov | ONE_SHOT | drain | NO |
| A-FAMILY-INVALIDATE | Audit | Audit | EPISODE | invalidation/drain | NO |
| A-DISCOVERY-START | Contract | Research | ONE_SHOT | current parent | NO |
| A-DISCOVERY | Contract | Research | EPISODE | budget/stopping | NO |
| A-RESEARCH-ACTION-ACCOUNT | SearchInstrumentation | SearchInstrumentation | SERVICE | generation/choice spend | NO |
| A-RESEARCH-EVAL | SearchInstrumentation | SearchInstrumentation | EPISODE | capture/budget/stopping | NO |
| A-SEARCH-CLOSURE | Audit | Audit | ONE_SHOT | canonical stop/full closure | NO |
| A-EVIDENCE-REGISTER | Evidence | Evidence | ONE_SHOT | Evidence key/head/DGP+intervention | NO |
| A-EVIDENCE-EXPOSURE-RECORD | Evidence | Evidence | SERVICE | access before/atomic | NO |
| A-EVIDENCE-RESERVE | Evidence | Evidence | ONE_SHOT | proof/head + eligible Contract + comparator/error/order/planned+narrowing | NO |
| A-EVIDENCE-RELEASE | Evidence | Evidence | EDGE_NONCE | settlement/head | NO |
| A-VALIDATE | Validation | Validation | EPISODE | exact REGISTERED Attempt if promotion | NO |
| A-SHADOW | Validation | Validation | EPISODE | frozen experiment/integrity | NO |
| A-INTEGRITY-AUDIT | Audit | Audit | ONE_SHOT | attestation/defect/dependency/proposal integrity/remediation evidence | NO |
| A-CRITIC | Critic | Critic | ONE_SHOT | proof/disclosure/classification/admissibility/no rescue | NO |
| A-ADJUDICATE | ScientificAdjudication | ScientificAdjudication | ONE_SHOT | estimand/identification/error instance/narrowing/final comparative | NO |
| A-GOVERN | Governor | Governor | ONE_SHOT | constitutional/admissibility/identification/error/final authority | NO |
| A-CHALLENGE-REGISTER | Promotion | ChampionRegistry | ONE_SHOT per canonical allocation obligation | only NEXT_CANONICAL slot; REGISTERED or PREVALIDATION_BLOCKED; atomic selection/error accounting | registry |
| A-PROMOTE | Promotion | ChampionRegistry | ONE_SHOT | REGISTERED Attempt + order/error/final comparative/authority/admissibility | registry |
| A-ROLLBACK | ChampionRegistry | ChampionRegistry | ONE_SHOT | proof+selection/trigger/target | registry |
| A-CAPABILITY-DESIGN | Contract | Research | ONE_SHOT | genealogy/debt/causal | NO |
| A-CAPABILITY-PROOF | Validation | Validation | EPISODE | governed proof/evidence/admissibility | NO |
| A-CAPABILITY-PRODUCTION-ACTIVATE | Promotion | CapabilityRegistry | ONE_SHOT | accepted proof/catalog | registry |
| A-CAPABILITY-RETIRE | CapabilityRegistry | CapabilityRegistry | ONE_SHOT | retirement | registry |
| A-RETIRE[PROBLEM_OR_CANDIDATE] | Contract | Contract | EDGE_NONCE | retention/drain | NO |
| A-RETIRE[FAMILY] | ProgramGov | ProgramGov | EDGE_NONCE | CLOSED->RETIRED | NO |
| A-RECORD-CLOSE | Audit | Audit | EDGE_NONCE | exact close/drain | NO |
| A-DECISION-INPUT-PUBLISH | OperationalInput | OperationalInput | SERVICE | canonical event/info-time/completeness | indirect |
| A-DECISION-STATE-INIT | OperationalState | OperationalState | ONE_SHOT | initialization frontier | indirect |
| A-DECISION-STATE-UPDATE | OperationalState | OperationalState | SERVICE | ACTIVE canonical batch | indirect |
| A-ACTIVE-DECIDE | OperationalDecision | OperationalDecision | SERVICE | canonical opportunity within final proof authority | indirect |
| A-CAPITAL-ACTION-AUTHORIZE | Safety | Safety | ONE_SHOT | proof+selection/final envelope/current SafetyContract/all expected change roots resolved/pre-risk/observation/all-scope risk | NO |
| A-CAPITAL-ACTION-CANCEL | Safety | Safety | ONE_SHOT | deterministic cancel | NO |
| A-CAPITAL-ORDER | Safety | Execution | EPISODE | dispatch/claim/pending/freshness/final action envelope | YES |
| A-CAPITAL-ACTION-RECOVER | Safety | Execution | EPISODE | deterministic cancel/reduction; Genesis containment only pre-existing risk | reduce |
| A-SAFETY-PREFLIGHT | Safety | Safety | ONE_SHOT | deployment/final proof/selection/runtime/current SafetyContract | NO |
| A-CAPITAL-AUTHORIZE | Safety | Safety | ONE_SHOT | selection/current Safety/all expected roots resolved/pre-risk/observation/all-scope | NO |
| A-CAPITAL-ACTIVATE | Safety | Execution | EPISODE | selected+reliance/final envelope/activation/freshness | YES |
| A-DEPLOYMENT-CANCEL | Safety | Safety | ONE_SHOT | deterministic/intervention | NO |
| A-CAPITAL-DEACTIVATE | Safety | Execution | EPISODE | normal/mandatory stale/Safety response | reduce |
| A-EMERGENCY-FLAT | Safety | Execution | EPISODE | emergency/Safety response/Genesis containment reduction | reduce |
| A-RUNTIME-RECONCILE | Safety + independent Audit | Safety | ONE_SHOT | broker observation/orphan/Safety unknown/Genesis bootstrap | NO |

## 12. Complete guarded transition/event registry — exhaustive

All mutable edges obey §1 CAS; no older file supplies omitted edges. Finite slash-state notation enumerates each named predecessor separately under same exact authority/guard, not wildcard authority.

### 12.1 Shared / role / evidence / Safety

```text
root/kernel #0=A-SYSTEM-GENESIS
root/kernel g->g+1=A-TRUST-ROLE-ROTATE[ROOT]
non-root role/binding replacement=A-TRUST-ROLE-ROTATE[ROLE]
VAR absent->ISSUED=A-AUTHORITY-ISSUE
VAR ISSUED->CONSUMED=successful bound use
VAR ISSUED->REVOKED=A-AUTHORITY-REVOKE
LegacyHead g->g+1=A-LEGACY-RECONCILE
FamilyRelationPolicyRegistry g->g+1=A-RELATION-POLICY-FREEZE
RelationRegistry absent key->ADJUDICATED=A-RELATION-ADJUDICATE
EvidenceSnapshot absent EVIDENCE_KEY->REGISTERED=A-EVIDENCE-REGISTER
same Evidence key/same payload->existing; conflict->IntegrityDefectRecord
Attestation absent exact key->PASS|FAIL|BLOCKED|UNKNOWN=A-INTEGRITY-AUDIT
same attestation key/same payload->existing; conflict->IntegrityDefectRecord
EvidenceHead g->g+1=only exact §4 writers
Expected SafetyChange root=derived immediately from canonical trigger; no mutable root-creation edge
Attempt[g0] absent expected slot->NO_CHANGE=A-SAFETY-CONTRACT-PREPARE[trigger-frontier key+eligible]
Attempt[g0] absent expected slot->PREPARED=A-SAFETY-CONTRACT-PREPARE[trigger-frontier key+policy|constitutional|INITIAL]
Attempt[g] PREPARED->CONSUMED=A-SAFETY-CONTRACT-FREEZE[first eligibility+current policy compatibility]
Attempt[g] PREPARED->INVALIDATED_STALE=A-INTEGRITY-AUDIT[objective staleness]
Attempt[g] PREPARED->INVALIDATED=A-INTEGRITY-AUDIT[proposal/integrity defect]
Attempt[g] INVALIDATED_STALE/INVALIDATED + material remediation state -> SUPERSEDED_BY_SUCCESSOR atomically with Attempt[g+1] PREPARED=A-SAFETY-CONTRACT-PREPARE[remediation successor]
Expected root with absent/nonterminal attempt -> SATISFIED_BY_SUPERSEDING_CHANGE=A-SAFETY-CONTRACT-PREPARE[positive current-generation resolution proof]
Attempt[g] INVALIDATED_STALE/INVALIDATED -> SATISFIED_BY_SUPERSEDING_CHANGE=A-SAFETY-CONTRACT-PREPARE[positive current-generation resolution proof]
NO_CHANGE/CONSUMED/SATISFIED_BY_SUPERSEDING_CHANGE are root-terminal accounting dispositions
terminal attempt/disposition->PREPARED=DENIED
SafetyRegistry EMPTY->CURRENT(g1)=A-SAFETY-CONTRACT-FREEZE[INITIAL+containment handoff if live]
SafetyRegistry CURRENT(g)->CURRENT(g+1)=A-SAFETY-CONTRACT-FREEZE[MIGRATION+current predecessor+handoff]
SafetyObservationRegistry absent opportunity->record=A-SAFETY-OBSERVE[CURRENT|ACTIVE_PREPARED_HANDOFF|GENESIS_CONTAINMENT]
same opportunity/same payload->existing; conflict->IntegrityDefectRecord
FidelityLedger append=A-INTEGRITY-AUDIT[OPERATIONAL_COMPLETENESS]
```

### 12.2 Family / Program

```text
Family absent->LOCKED+BootstrapSlot EMPTY=A-RESEARCH-FAMILY-ASSIGN
Family LOCKED->CANCELLED=A-FAMILY-CANCEL
Family LOCKED->ACTIVE=A-PROGRAM-CREATE
Family ACTIVE->QUIESCING=A-FAMILY-QUIESCE
Family QUIESCING->CLOSED=A-FAMILY-CLOSE[FAMILY_QUIESCENCE_DRAIN_COMPLETE]
Family CLOSED->RETIRED=A-RETIRE[FAMILY]
Family LOCKED/ACTIVE/QUIESCING->INVALIDATING=A-FAMILY-INVALIDATE
Family INVALIDATING->INVALIDATED=A-FAMILY-INVALIDATE[FAMILY_INVALIDATION_DRAIN_COMPLETE]
BootstrapSlot EMPTY->RESERVED=A-PROGRAM-BUDGET[INITIAL]
BootstrapSlot RESERVED->CONSUMED=A-PROGRAM-CREATE
BootstrapSlot RESERVED->RELEASED=A-FAMILY-CANCEL
BootstrapSlot RESERVED->INVALIDATED=A-INTEGRITY-AUDIT[BOOTSTRAP_DEFECT]
Program+Reservation absent target slot->DRAFT+RESERVED=A-PROGRAM-BUDGET[INITIAL|LATER]
same slot/same payload->existing; conflict->IntegrityDefectRecord
Reservation INITIAL->CONSUMED=A-PROGRAM-CREATE
Reservation LATER->CONSUMED=A-PROGRAM-RENEW
Reservation INITIAL->RELEASED=A-FAMILY-CANCEL
Reservation LATER->RELEASED=A-FAMILY-QUIESCE[unused]
Reservation RESERVED->INVALIDATED=A-INTEGRITY-AUDIT[RESERVATION_DEFECT|ANCESTRY_INVALIDATION]
Program DRAFT[gen1]->AUTHORIZED=A-PROGRAM-CREATE
Program DRAFT[gen>1]->AUTHORIZED=A-PROGRAM-RENEW
Program DRAFT[gen1]->CANCELLED=A-FAMILY-CANCEL
Program DRAFT[gen>1]/AUTHORIZED->CANCELLED=A-FAMILY-QUIESCE
Program AUTHORIZED->ACTIVE=A-DISCOVERY-START
Program ACTIVE->STOPPED=A-PROGRAM-CLOSE
Program STOPPED->CLOSED=A-RECORD-CLOSE[PROGRAM_DESCENDANT_DRAIN_CURRENT]
Program DRAFT/AUTHORIZED/ACTIVE/STOPPED->INVALIDATED=A-INTEGRITY-AUDIT[PROGRAM_DEFECT|ANCESTRY_INVALIDATION]
Ledger absent->OPEN=A-PROGRAM-CREATE
Ledger OPEN->OPEN append=only exact §4 writers
Ledger OPEN->SEALED[NORMAL]=A-FAMILY-CLOSE
Ledger OPEN->SEALED[INVALIDATION]=A-FAMILY-INVALIDATE
Ledger SEALED->OPEN=DENIED
DebtGroupReconciliationRecord absent->RECORDED=A-FAMILY-DEBT-LINK[LEDGER_OPEN|LEDGER_SEALED_OR_ABSENT]
```

ANCESTRY_INVALIDATION only governed ancestor/retrospective defect and only listed child edges. Drain requires no nonterminal descendants/reservations/new authority and reconciled debt/exposure; invalidation permits NO_FAMILY_LEDGER_GENESIS without fabricated Ledger.

### 12.3 Problem / Episode / Hypothesis / Contract / Candidate

```text
Problem absent->ACTIVE_RECORD=A-CREATE
Problem ACTIVE_RECORD->RETIRED=A-RETIRE[PROBLEM_OR_CANDIDATE+drain]
Problem ACTIVE_RECORD->INVALIDATED=A-INTEGRITY-AUDIT[PROBLEM_DEFECT|ANCESTRY_INVALIDATION]
Episode absent->PLANNED=A-CREATE
Episode PLANNED->CONTRACTED=A-LOCK
Episode PLANNED->CANCELLED=A-FAMILY-QUIESCE
Episode CONTRACTED->CANCELLED=A-FAMILY-QUIESCE
Episode CONTRACTED->RESEARCHING=A-DISCOVERY-START
Episode RESEARCHING->ADJUDICATED=A-ADJUDICATE[EPISODE_SCIENTIFIC_CLOSURE_VALID]
Episode PLANNED/CONTRACTED/RESEARCHING->INVALIDATED=A-INTEGRITY-AUDIT[EPISODE_DEFECT|ANCESTRY_INVALIDATION]
Hypothesis absent->PROPOSED=A-CREATE
Hypothesis PROPOSED->CONTRACTED=A-LOCK
Hypothesis PROPOSED->CANCELLED=A-FAMILY-QUIESCE
Hypothesis CONTRACTED->CANCELLED=A-FAMILY-QUIESCE
Hypothesis CONTRACTED->DISCOVERY_ACTIVE=A-DISCOVERY
Hypothesis DISCOVERY_ACTIVE->DISCOVERY_CLOSED=A-DISCOVERY
Hypothesis DISCOVERY_CLOSED->ADJUDICATED=A-ADJUDICATE[HYPOTHESIS_SCIENTIFIC_CLOSURE_VALID]
Hypothesis PROPOSED/CONTRACTED/DISCOVERY_ACTIVE/DISCOVERY_CLOSED->INVALIDATED=A-INTEGRITY-AUDIT[HYPOTHESIS_DEFECT|ANCESTRY_INVALIDATION]
Contract absent->DRAFT=A-CONTRACT-DRAFT
Contract DRAFT->PRECOMMIT_REVIEW=A-CONTRACT-DRAFT
Contract PRECOMMIT_REVIEW->DRAFT=A-CONTRACT-DRAFT[review-return]
Contract PRECOMMIT_REVIEW->LOCKED=A-LOCK[derived claim/risk/admissibility/identification; child checks access boundary+heads]
Contract DRAFT->CANCELLED=A-FAMILY-QUIESCE
Contract PRECOMMIT_REVIEW->CANCELLED=A-FAMILY-QUIESCE
Contract LOCKED->CANCELLED=A-FAMILY-QUIESCE[no started child]
Contract LOCKED->ACTIVE=A-DISCOVERY-START
Contract ACTIVE->CLOSED=A-RECORD-CLOSE[CONTRACT_DESCENDANT_DRAIN_CURRENT]
Contract DRAFT/PRECOMMIT_REVIEW/LOCKED/ACTIVE->INVALIDATED=A-INTEGRITY-AUDIT[CONTRACT_DEFECT|ANCESTRY_INVALIDATION]
Candidate absent->DRAFT=A-CREATE
Candidate DRAFT->FROZEN=A-LOCK[research identity/genealogy]
Candidate DRAFT->CANCELLED=A-FAMILY-QUIESCE
Candidate DRAFT/FROZEN->INVALIDATED=A-INTEGRITY-AUDIT[CANDIDATE_DEFECT|ANCESTRY_INVALIDATION]
Candidate FROZEN->RETIRED=A-RETIRE[PROBLEM_OR_CANDIDATE+drain]
```

### 12.4 Relation

```text
RelationCoverageManifest absent->FROZEN=A-RELATION-COVERAGE-FREEZE
RelationGateSpec absent+RelationDecision absent->SPEC_LOCKED=A-RELATION-SPEC-FREEZE
RelationDecision SPEC_LOCKED->ADJUDICATED+RelationRegistry CAS=A-RELATION-ADJUDICATE
invalidated prior FULL privilege->FAMILY_DEBT_GROUP_CURRENT=false + A-FAMILY-DEBT-LINK before future privilege
```

### 12.5 Evidence / CandidateProof

```text
EvidenceReservation[VALIDATION,promotion] absent->RESERVED + CandidateProof absent->VALIDATION_RESERVED=A-EVIDENCE-RESERVE[eligible Candidate+Contract+error/order/planned/narrowing]
EvidenceReservation[VALIDATION,nonpromotion] absent->RESERVED + CandidateProof absent->VALIDATION_RESERVED=A-EVIDENCE-RESERVE[nonproduction]
Reservation RESERVED->IN_USE=A-VALIDATE
Reservation RESERVED->RELEASED=A-EVIDENCE-RELEASE[unused]
Reservation IN_USE->CONSUMED=A-EVIDENCE-RELEASE
Reservation RESERVED/IN_USE->INVALIDATED=A-INTEGRITY-AUDIT[EVIDENCE|IDENTIFICATION|ADMISSIBILITY|ANCESTRY defect]
CandidateProof VALIDATION_RESERVED->CANCELLED=A-FAMILY-QUIESCE
CandidateProof VALIDATION_RESERVED->VALIDATING=A-VALIDATE[promotion=>exact REGISTERED Attempt]
CandidateProof VALIDATING->VALIDATION_CLOSED=A-VALIDATE[ProofBundle+execution integrity+identification]
CandidateProof VALIDATION_CLOSED->CRITIC_REVIEWED=A-CRITIC
CandidateProof CRITIC_REVIEWED->SCIENTIFIC_ADJUDICATED=A-ADJUDICATE[exact narrowing+final comparative]
CandidateProof SCIENTIFIC_ADJUDICATED->GOVERNOR_ADJUDICATED=A-GOVERN
CandidateProof GOVERNOR_ADJUDICATED->CLOSED=A-RECORD-CLOSE
CandidateProof each pre-CLOSED->INVALIDATED=A-INTEGRITY-AUDIT[exact dependency/integrity/identification/admissibility/ancestry cause]
```

### 12.6 Experiment / Shadow

```text
Experiment absent->LOCKED[DISCOVERY]=A-LOCK[EXPERIMENT_GENESIS]
Experiment absent->LOCKED[VALIDATION]=A-LOCK[EXPERIMENT_GENESIS+VALIDATION_DERIVATION_FROZEN]
Experiment absent->LOCKED[SHADOW]=A-LOCK[EXPERIMENT_GENESIS+SHADOW_DERIVATION_FROZEN]
LOCKED[DISCOVERY]->RUNNING[DISCOVERY]=A-RESEARCH-EVAL
RUNNING[DISCOVERY]->EXECUTION_CLOSED[DISCOVERY]=A-RESEARCH-EVAL
LOCKED[VALIDATION]->RUNNING[VALIDATION]=A-VALIDATE
RUNNING[VALIDATION]->EXECUTION_CLOSED[VALIDATION]=A-VALIDATE
LOCKED[SHADOW]->RUNNING[SHADOW]=A-SHADOW
RUNNING[SHADOW]->EXECUTION_CLOSED[SHADOW]=A-SHADOW
LOCKED[DISCOVERY]->CANCELLED=A-FAMILY-QUIESCE
LOCKED[VALIDATION]->CANCELLED=A-FAMILY-QUIESCE
LOCKED[SHADOW]->CANCELLED=A-FAMILY-QUIESCE
EXECUTION_CLOSED[DISCOVERY]->INTEGRITY_ADJUDICATED=A-INTEGRITY-AUDIT[DISCOVERY_EXECUTION]
EXECUTION_CLOSED[VALIDATION]->INTEGRITY_ADJUDICATED=A-INTEGRITY-AUDIT[VALIDATION_EXECUTION]
EXECUTION_CLOSED[SHADOW]->INTEGRITY_ADJUDICATED=A-INTEGRITY-AUDIT[SHADOW_EXECUTION]
INTEGRITY_ADJUDICATED->CLOSED=A-RECORD-CLOSE
Experiment LOCKED/RUNNING/EXECUTION_CLOSED exact mode->INVALIDATED=A-INTEGRITY-AUDIT[matching defect|ANCESTRY]
EvidenceReservation[SHADOW] absent->RESERVED=A-EVIDENCE-RESERVE[SHADOW]
RESERVED->IN_USE=A-SHADOW
RESERVED->RELEASED=A-EVIDENCE-RELEASE[unused]
IN_USE->CONSUMED=A-EVIDENCE-RELEASE
RESERVED/IN_USE->INVALIDATED=A-INTEGRITY-AUDIT[EVIDENCE|IDENTIFICATION|ANCESTRY]
Shadow absent->FROZEN=A-SHADOW[SHADOW_GENESIS]
FROZEN->CANCELLED=A-FAMILY-QUIESCE
FROZEN->RUNNING=A-SHADOW
RUNNING->WINDOW_CLOSED=A-SHADOW
WINDOW_CLOSED->EVIDENCE_SEALED=A-EVIDENCE-RELEASE
EVIDENCE_SEALED->CRITIC_REVIEWED=A-CRITIC
CRITIC_REVIEWED->SCIENTIFIC_ADJUDICATED=A-ADJUDICATE
SCIENTIFIC_ADJUDICATED->GOVERNOR_ADJUDICATED=A-GOVERN
GOVERNOR_ADJUDICATED->CLOSED=A-RECORD-CLOSE
Shadow each pre-CLOSED->INVALIDATED=A-INTEGRITY-AUDIT[SHADOW|IDENTIFICATION|ANCESTRY]
```

### 12.7 Search / Evidence / Fidelity

```text
SearchGenerationBatch transitions=exact §5
SearchNode transitions=exact §5
EvidenceSnapshot one-slot=§6.1
Attestation one-slot=§6.2
EvidenceExposureEvent+ExposureLedger+EvidenceHead=A-EVIDENCE-EXPOSURE-RECORD before/atomic access
ProofDependencyInvalidationRecord+EvidenceHead=A-INTEGRITY-AUDIT[PROOF_DEPENDENCY|IDENTIFICATION|ADMISSIBILITY]
SearchCompletenessProof absent closure key->canonical proof=A-SEARCH-CLOSURE
same key/same payload->existing; conflict->IntegrityDefectRecord
OperationalCompletenessRecord+FidelityLedger=A-INTEGRITY-AUDIT[OPERATIONAL_COMPLETENESS]
```

### 12.8 Challenge / Promotion / Rollback

```text
First-eligible opportunity->append-only CHALLENGE_ALLOCATION_OBLIGATION under frozen order rule
ChallengeAttempt absent NEXT_CANONICAL slot->REGISTERED + selection debt + ChallengeLedger allocation + error instance=A-CHALLENGE-REGISTER[current eligibility]
ChallengeAttempt absent NEXT_CANONICAL slot->PREVALIDATION_BLOCKED + selection debt + frozen no-outcome error-spend disposition=A-CHALLENGE-REGISTER[historical obligation no longer validation-eligible before validation/result]
same slot/same payload->existing; conflict->IntegrityDefectRecord
later order slot while earlier unsettled=DENIED
REGISTERED->CANCELLED=A-FAMILY-QUIESCE[proof not started; debt retained]
REGISTERED->INVALIDATED=A-INTEGRITY-AUDIT[dependency|ANCESTRY; debt retained]
REGISTERED->NO_PROMOTE=A-PROMOTE[deterministic+ledger]
REGISTERED->BLOCKED_INVALID=A-PROMOTE[deterministic+ledger]
REGISTERED->PROMOTED=A-PROMOTE[deterministic+order+error+final comparative+PromotionTransaction+ChampionRegistry CAS]
PREVALIDATION_BLOCKED->REGISTERED/PROMOTED=DENIED
RollbackPlan current-owner unused->CONSUMED=A-ROLLBACK[first eligible trigger+target]
ChampionRegistry incumbent->promoted=A-PROMOTE[PROMOTED]
ChampionRegistry current->fallback=A-ROLLBACK
```

### 12.9 Capability

```text
CapabilityArtifact absent FROZEN+CapabilityEpisode absent DESIGN_PROOF=A-CAPABILITY-DESIGN
DESIGN_PROOF->CANCELLED=A-FAMILY-QUIESCE
DESIGN_PROOF->CODE_CANDIDATE_PROOF=A-CAPABILITY-PROOF
CODE_CANDIDATE_PROOF->SHADOW_ELIGIBLE=A-CAPABILITY-PROOF
SHADOW_ELIGIBLE->CRITIC_REVIEWED=A-CRITIC
CRITIC_REVIEWED->SCIENTIFIC_ADJUDICATED=A-ADJUDICATE
SCIENTIFIC_ADJUDICATED->GOVERNOR_ADJUDICATED=A-GOVERN
GOVERNOR_ADJUDICATED->PRODUCTION_AVAILABLE=A-CAPABILITY-PRODUCTION-ACTIVATE[accepted]
GOVERNOR_ADJUDICATED->CLOSED=A-RECORD-CLOSE[rejected]
PRODUCTION_AVAILABLE->RETIRED=A-CAPABILITY-RETIRE
CapabilityEpisode each preterminal->INVALIDATED=A-INTEGRITY-AUDIT[CAPABILITY|IDENTIFICATION|ADMISSIBILITY|ANCESTRY]
```

Capability proof governed; PRODUCTION_AVAILABLE catalog-only.

### 12.10 Input / State / Decision

```text
DecisionInputRegistry absent key->record=A-DECISION-INPUT-PUBLISH
same key/same payload->existing; conflict->IntegrityDefectRecord; missing expected->Fidelity
DecisionStateRegistry absent deployment state->StateRevision#0=A-DECISION-STATE-INIT
StateHead N->N+1=A-DECISION-STATE-UPDATE[canonical batch]
same key/same payload->existing; fork/conflict->IntegrityDefectRecord
DecisionRegistry absent opportunity->DecisionRecord=A-ACTIVE-DECIDE[final proof authority]
ACTION->one CapitalAction PROPOSED; NO_ACTION/BLOCKED->zero
same opportunity/same payload->existing; conflict->IntegrityDefectRecord; missing expected->Fidelity
```

### 12.11 Capital / Broker / Recovery

```text
CapitalAction absent PROPOSED=A-ACTIVE-DECIDE[ACTION]
PROPOSED->AUTHORIZED=A-CAPITAL-ACTION-AUTHORIZE[final envelope+all-scope+Safety]
PROPOSED->DENIED=A-CAPITAL-ACTION-AUTHORIZE
PROPOSED->CANCELLED=A-CAPITAL-ACTION-CANCEL
AUTHORIZED->CANCELLED=A-CAPITAL-ACTION-CANCEL[stale]
AUTHORIZED->EXECUTING=A-CAPITAL-ORDER
EXECUTING->SETTLED=A-CAPITAL-ORDER[terminal]
EXECUTING->PENDING_LIVE=A-CAPITAL-ORDER[accepted pending]
EXECUTING->EXECUTION_FAILED=A-CAPITAL-ORDER[proved no mutation]
EXECUTING->EXECUTION_UNCERTAIN=A-CAPITAL-ORDER[ambiguity]
EXECUTING->EXECUTION_UNCERTAIN=A-RUNTIME-RECONCILE[ORPHAN]
PENDING_LIVE->PENDING_LIVE=A-CAPITAL-ORDER[LIVE_OWNER_PARTIAL_FILL_UPDATE]
PENDING_LIVE->PENDING_LIVE=A-RUNTIME-RECONCILE[ORPHAN_PARTIAL_FILL_UPDATE]
PENDING_LIVE->SETTLED=A-CAPITAL-ORDER[filled/terminal]
PENDING_LIVE->SETTLED=A-CAPITAL-ACTION-RECOVER[confirmed no remaining fill]
PENDING_LIVE->EXECUTION_UNCERTAIN=A-CAPITAL-ACTION-RECOVER[cancel/fill race]
PENDING_LIVE->EXECUTION_UNCERTAIN=A-RUNTIME-RECONCILE[orphan]

CapitalRiskReservation absent->RESERVED=A-CAPITAL-ACTION-AUTHORIZE or A-CAPITAL-AUTHORIZE[ACTIVATION]
RESERVED->COMMITTED_TO_BROKER=A-CAPITAL-ORDER/A-CAPITAL-ACTIVATE
RESERVED->RELEASED=A-CAPITAL-ACTION-CANCEL/A-DEPLOYMENT-CANCEL
COMMITTED_TO_BROKER->SETTLED=A-CAPITAL-ORDER/A-CAPITAL-ACTIVATE[no conditional]
COMMITTED_TO_BROKER->RELEASED=A-CAPITAL-ORDER/A-CAPITAL-ACTIVATE[proved no mutation]
COMMITTED_TO_BROKER->UNCERTAIN=A-CAPITAL-ORDER/A-CAPITAL-ACTIVATE[ambiguity]
COMMITTED_TO_BROKER->UNCERTAIN=A-RUNTIME-RECONCILE[ORPHAN]
COMMITTED_TO_BROKER->CONDITIONAL_LIVE=A-CAPITAL-ORDER[accepted pending]
CONDITIONAL_LIVE->CONDITIONAL_LIVE=A-CAPITAL-ORDER[LIVE_OWNER_PARTIAL_FILL_UPDATE]
CONDITIONAL_LIVE->CONDITIONAL_LIVE=A-RUNTIME-RECONCILE[ORPHAN_PARTIAL_FILL_UPDATE]
CONDITIONAL_LIVE->SETTLED=A-CAPITAL-ORDER[terminal]
CONDITIONAL_LIVE->RELEASED=A-CAPITAL-ACTION-RECOVER[confirmed none]
CONDITIONAL_LIVE->UNCERTAIN=A-CAPITAL-ACTION-RECOVER[cancel/fill race]
CONDITIONAL_LIVE->UNCERTAIN=A-RUNTIME-RECONCILE[orphan]
UNCERTAIN->RECONCILED=A-RUNTIME-RECONCILE

BrokerMutation absent key->DISPATCH_CLAIMED=owning authority before send
DISPATCH_CLAIMED->SETTLED=owning authority[proof]
DISPATCH_CLAIMED->FAILED_NO_MUTATION=owning authority[proof]
DISPATCH_CLAIMED->UNCERTAIN=owning authority[ambiguity]
DISPATCH_CLAIMED->UNCERTAIN=A-RUNTIME-RECONCILE[ORPHAN]
UNCERTAIN->RECONCILED=A-RUNTIME-RECONCILE

RecoveryIntent absent key->ACTIVE=A-CAPITAL-ACTION-RECOVER
same key/same semantics->existing; conflict->IntegrityDefectRecord
RecoveryRecord absent->SETTLED/FAILED_NO_MUTATION/UNCERTAIN=A-CAPITAL-ACTION-RECOVER[matching proof]
RecoveryRecord UNCERTAIN->RECONCILED=A-RUNTIME-RECONCILE
```

Safety/Genesis reduction binds canonical response; retry/session/time cannot resend.

### 12.12 Deployment / registry

```text
Deployment absent key->NO_ACTIVATE=A-SAFETY-PREFLIGHT[deny]
Deployment absent key->BLOCKED=A-SAFETY-PREFLIGHT
Deployment absent key->PLANNED=A-SAFETY-PREFLIGHT[proof+selection+current Safety]
PLANNED->PREFLIGHT_PASSED/PREFLIGHT_DENIED=A-SAFETY-PREFLIGHT
PREFLIGHT_PASSED->STATE_INITIALIZED=A-DECISION-STATE-INIT
STATE_INITIALIZED->AUTHORIZED=A-CAPITAL-AUTHORIZE
PLANNED/PREFLIGHT_PASSED/STATE_INITIALIZED/AUTHORIZED->CANCELLED=A-DEPLOYMENT-CANCEL[exact predecessor]
PLANNED/PREFLIGHT_PASSED/STATE_INITIALIZED/AUTHORIZED->INVALIDATED=A-INTEGRITY-AUDIT[DEPLOYMENT_DEFECT|ANCESTRY]
AUTHORIZED->ACTIVATING=A-CAPITAL-ACTIVATE
ACTIVATING->ACTIVE=A-CAPITAL-ACTIVATE[proof]
ACTIVATING->ACTIVATION_FAILED=A-CAPITAL-ACTIVATE[no footprint]
ACTIVATING->ACTIVATION_UNCERTAIN=A-CAPITAL-ACTIVATE/A-RUNTIME-RECONCILE[exact guard]
ACTIVATION_UNCERTAIN->DEACTIVATED=A-RUNTIME-RECONCILE[FOOTPRINT_CLOSED]
ACTIVE->DEACTIVATING=A-CAPITAL-DEACTIVATE[NORMAL|MANDATORY_STALE|SAFETY_RESPONSE]
DEACTIVATING->DEACTIVATED=A-CAPITAL-DEACTIVATE/A-RUNTIME-RECONCILE[exact guard+FOOTPRINT_CLOSED]
ACTIVE->DEACTIVATED=A-EMERGENCY-FLAT/A-RUNTIME-RECONCILE[exact guard+FOOTPRINT_CLOSED]
DeploymentRegistry EMPTY->ACTIVATING=A-CAPITAL-ACTIVATE
DeploymentRegistry ACTIVATING->ACTIVE/EMPTY/UNCERTAIN=A-CAPITAL-ACTIVATE[exact guard]
DeploymentRegistry ACTIVATING->UNCERTAIN=A-RUNTIME-RECONCILE[ORPHAN]
DeploymentRegistry ACTIVE->EMPTY=A-CAPITAL-DEACTIVATE/A-EMERGENCY-FLAT/A-RUNTIME-RECONCILE[exact guard]
DeploymentRegistry UNCERTAIN->EMPTY=A-RUNTIME-RECONCILE[FOOTPRINT_CLOSED]
DeploymentRegistry UNCERTAIN->ACTIVE=DENIED
```

### 12.13 Safety observation

```text
SafetyObservationRegistry absent opportunity->WITHIN_ENVELOPE/REDUCE/DEACTIVATE/EMERGENCY_FLAT/BLOCKED_UNKNOWN=A-SAFETY-OBSERVE[exact deterministic guard]
same opportunity/same payload->existing; conflict->IntegrityDefectRecord
```

Non-WITHIN first-eligible response mandatory. Genesis WITHIN containment-only.

## 13. Global predicates / gates

Scientific/new-proof privilege requires all applicable:

```text
LEGACY_STATE_HEAD_CURRENT or valid historical projection
LEGACY_DEBT_ELIGIBLE
FAMILY_DEBT_GROUP_CURRENT
SEARCH_OBSERVATION_BOUNDARY_PROVEN
SEARCH_COMPLETENESS_CURRENT
SEARCH_TREE_BUDGET_CURRENT
SEARCH_GENEALOGY_COMPLETE
SEARCH_GENERATION_PREAUTHORIZED where generation occurred
SEARCH_GENERATION_CAPTURE_COMPLETE where generation occurred
SEARCH_GENERATION_EMITTED_SET_CLOSED where generation occurred
STOPPING_RULE_CURRENT
SCIENTIFIC_STOPPING_DISPOSITION_VALID where clean terminal claimed
SCIENTIFIC_CHOICE_CAUSALITY_CLASSIFIED
OUTCOME_MOTIVATED_GOVERNANCE_CHOICE_ACCOUNTED where applicable
SEARCH_CLOSURE_OPPORTUNITY_CANONICAL
EVIDENCE_PROVENANCE_ELIGIBLE
POLICY_GENERATION_CLASSIFICATION_VALID
POLICY_GENERATED_EVIDENCE_PROVENANCE_VALID where applicable
INTERVENTION_CONTEXT_COMPLETE where material
PROSPECTIVE_ISOLATION_ELIGIBLE_IF_CLAIMED
EVIDENCE_ATTESTATION_HISTORY_VALID
EVIDENCE_DEPENDENCY_SET_COMPLETE
EVIDENCE_DEPENDENCY_PROJECTION_CURRENT
VALIDATION_CONSUMPTION_ELIGIBLE
CLAIM_SEMANTICS_CLASSIFICATION_VALID
CLAIM_RISK_CLASS_VALID
ADMISSIBILITY_DIMENSION_APPLICABILITY_CURRENT
SCIENTIFIC_METHOD_ADMISSIBILITY_VALID
PROMOTION_ERROR_CONTROL_ADMISSIBILITY_VALID where promotion-intent
CHALLENGE_ALLOCATION_ORDER_CURRENT where promotion-intent
CHALLENGE_ALLOCATION_OBLIGATION_COVERAGE_CURRENT where promotion-intent
COUNTERFACTUAL_IDENTIFIABILITY_VALID where required
COUNTERFACTUAL_QUALITY_ADMISSIBLE where required
PROOF_RESERVATION_ROOT_VALID
PROOF_AUTHORITY_NARROWING_RULE_CURRENT where promotion-intent
CAPABILITY_GENEALOGY_DEBT_CURRENT where used
CAPABILITY_PROOF_EVIDENCE_GOVERNANCE_VALID where used
PRINCIPAL_SOD_VALID
HISTORICAL_PRINCIPAL_SOD_VALID at relied dependency/time
```

Knowledge-only/nonpromotion does not require Candidate↔Contract production eligibility. Promotion additionally requires REGISTERED canonical ordered Attempt; eligible Candidate+Contract; comparator/accounting/population/error/order; exact Challenge debt+error instance; planned+narrowing/final roots; final utility; bootstrap comparator; deployment/action match; ChallengePolicy/universe/debt/current incumbent/proof reliance; Promotion admissibility/identification/novelty.

### 13.1 Preserved R7 proof/operational gates

R8 may narrow but never delete:

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

Normal new risk requires all:

```text
CURRENT_SAFETY_CONTRACT_EXISTS
CURRENT_DEPLOYMENT_PROOF_ELIGIBLE
CURRENT_CHAMPION_SELECTION_ELIGIBLE
PROOF_RELIANCE_ROOT_CURRENT
CHAMPION_SELECTION_RELIANCE_ROOT_CURRENT
PROOF_RELIANCE_ACCESS_HISTORY_VALID
PROOF_RELIANCE_PRINCIPAL_SOD_VALID
NO_APPLICABLE_PROOF_DEPENDENCY_INVALIDATION
LEGACY_STATE_RETROSPECTIVE_VALID_FOR_PROOF
DEPLOYMENT_BEHAVIORAL_CLOSURE_MATCH
DEPLOYMENT_OPPORTUNITY_WITHIN_PROOF_POPULATION
DEPLOYMENT_ACTION_ENVELOPE_MATCH
SELECTED_DEPLOYED_CHAMPION_MATCH_CURRENT
PRINCIPAL_SOD_VALID[current operational]
AUTHORITY_ADMIN_EVENT_PERFORMANCE_BLIND
RUNTIME_IDENTITY_CURRENT
RUNTIME_ATTESTATION_PERFORMANCE_BLIND
RUNTIME_ATTESTATION_COMPLETENESS_CURRENT
DEPLOYED_RUNTIME_SEMANTICS_ROOT_CURRENT
DEPLOYMENT_RUNTIME_RECONCILED
DEPLOYMENT_REGISTRY_MATCH
DEPLOYMENT_BOUND_SAFETY_GENERATION_CURRENT
DEPLOYMENT_CONTROL_POLICY_CURRENT
DEPLOYMENT_CONTROL_COMPLETENESS_CURRENT
OPERATIONAL_CAPTURE_WINDOW_CURRENT
OPERATIONAL_INPUT_OBSERVATION_BOUNDARY_PROVEN
OPERATIONAL_INPUT_STREAM_COMPLETENESS_CURRENT
DECISION_SOURCE_EVENT_CANONICAL
DECISION_INPUT_PROVENANCE_VALID
DECISION_INPUT_INFORMATION_TIME_VALID
DECISION_INPUT_IDEMPOTENCY_VALID
DECISION_STATE_LINEAGE_VALID
DECISION_STATE_INPUT_CONSUMPTION_VALID
DECISION_STATE_FRONTIER_MATCH
CANONICAL_STATE_ADVANCE_SCHEDULE_CURRENT
DECISION_OPPORTUNITY_CANONICAL
NO_UNRESOLVED_OPERATIONAL_COMPLETENESS_GAP
UNEXPLAINED_BROKER_MUTATION_PRESENT=FALSE
DEPLOYMENT_OPERATIONAL_FIDELITY_BROKEN=FALSE
SAFETY_CONTRACT_CHANGE_CAUSALITY_VALID
SAFETY_CHANGE_EXPECTED_ROOT_COVERAGE_CURRENT
SAFETY_CHANGE_POLICY_ADMISSIBILITY_VALID
CONSTITUTIONAL_SAFETY_INTEGRITY_TRIGGERS_CURRENT
SAFETY_CONTRACT_CHANGE_COMPLETENESS_CURRENT
UNRESOLVED_SAFETY_CHANGE_OPPORTUNITY_PRESENT=FALSE
SAFETY_CONTRACT_CHANGE_EXECUTION_TIMELINESS_VALID
SAFETY_CHANGE_REMEDIATION_CURRENT
SUCCESSOR_POLICY_COMPATIBILITY_VALID where successor/remediation used
PREPARED_CHANGE_HANDOFF_COMPLETENESS_CURRENT where PREPARED
SAFETY_CONTRACT_PROPOSAL_DERIVATION_DETERMINISTIC
SAFETY_RISK_MODEL_ADMISSIBILITY_VALID
SAFETY_TRIGGER_COVERAGE_COMPLETE
SAFETY_DISPOSITION_DETERMINISTIC
SAFETY_DISPOSITION_COMPLETENESS_CURRENT
SAFETY_MONITORING_SPEC_CURRENT
SAFETY_MONITORING_LATENCY_ADMISSIBLE
SAFETY_MONITORING_HANDOFF_COMPLETE
SAFETY_EMERGENCY_RESPONSE_FEASIBILITY_VALID
SAFETY_EMERGENCY_RESPONSE_FEASIBILITY_CURRENT
PRE_RISK_AUTHORIZATION_INPUT_FRONTIER_CURRENT
SAFETY_INPUT_CLOSURE_COMPLETE for latest required observation where ongoing
SAFETY_INPUT_FRESHNESS_VALID where ongoing
SAFETY_INPUT_FRONTIER_CURRENT where ongoing
SAFETY_OBSERVATION_TIMELINESS_VALID where ongoing
SAFETY_OBSERVATION_COMPLETENESS_CURRENT where ongoing
SAFETY_RESPONSE_OBLIGATION_CURRENT
SAFETY_RESPONSE_TIMELINESS_VALID where response required
LATEST_REQUIRED_SAFETY_DISPOSITION_PERMITS_RISK
CAPITAL_SAFETY_CURRENT
SAFETY_CONTRACT_BOOTSTRAP_OR_MIGRATION_RECONCILED
SAFETY_MIGRATION_RISK_MAPPING_CURRENT where applicable
CAPITAL_RISK_SCOPE_SET_COMPLETE
CAPITAL_RISK_MUTATION_BOUNDARY_VALID
CAPITAL_RISK_RESERVATION_CURRENT
PROTECTIVE_PLAN_DERIVATION_DETERMINISTIC
PROTECTIVE_DEPENDENCY_PLAN_CURRENT
PROTECTIVE_MONOTONIC_RISK_REDUCING where applicable
NO_UNRESOLVED_CAPITAL_ACTION_UNCERTAINTY
NO_STALE_RISK_INCREASING_CONDITIONAL_ORDER
STALE_CONDITIONAL_CANCEL_TRIGGER_COMPLETE where applicable
DEPLOYMENT_STALE_TRIGGER_COMPLETE
EXECUTION_INTENT_DERIVATION_DETERMINISTIC
EXECUTION_DISPATCH_COMPLETENESS
BROKER_MUTATION_IDEMPOTENCY_CURRENT
ACTIVATION_INTENT_DERIVATION_DETERMINISTIC where applicable
CANONICAL_EXECUTION_INTENT_IDENTITY_CURRENT where applicable
CANONICAL_ACTIVATION_INTENT_IDENTITY_CURRENT where applicable
CANONICAL_RISK_REDUCTION_INTENT_IDENTITY_CURRENT where applicable
DEPLOYMENT_CANCEL_DISPOSITION_DETERMINISTIC where ordinary cancel
SAFETY_RECOVERY_TRIGGER_COMPLETE where applicable
RECONCILIATION_OBSERVATION_BOUNDARY_PROVEN where used
```

Champion performance claim additionally requires CHAMPION_OPERATIONAL_HISTORY_COVERAGE_COMPLETE. Material UNKNOWN=>fail closed.

## 14. Forbidden hidden control planes

```text
prior-version authority/edge dependency / omitted transition
generic writer / fresh UUID/VAR/retry/session novelty
Family/debt/search/holdout/selection reset / private hidden search / lucky closure prefix
Evidence copy reset / attestation retry-until-PASS
policy-generated evidence mislabeled exogenous / mixed-policy segment hidden / intervention omitted
frozen-but-inadmissible gate / weak Promotion error criterion / negative incumbent value promoted
Candidate-specific error rule frozen before Candidate / mutable allocation as Attempt key / scheduler order selects error wealth
eligible Challenge opportunity disappearing before registration or permanently blocking sequence without terminal accounting
comparator/accounting/population mismatch / weak bootstrap comparator
claim/risk downgrade / post-outcome N/A waiver / predictive-to-policy upcast
planned proof expansion / post-outcome subgroup cherry-pick / broad utility reused on final subgroup/scale
high-risk Candidate forbidden solely for production ineligibility / Candidate mutated for eligibility / post-result child Contract rescue
child Contract eligibility from absence of logs without proven access boundary
ChallengeAttempt bound to post-validation final authority / winner-only challenge / market-timed Promotion / performance Rollback / behavior-history reset
ACT->THINK bypass
Safety trigger exists but expected root visible only at PREPARE / pre-decision new-risk window
broken SafetyChangePolicy required to authorize own repair / inadmissible policy NO_CHANGE
Safety proposal conflict / PREPARED new risk / silent-indefinite prep / favorable freeze timing
INVALIDATED proposal permanently deadlocking all future repair
concurrent Safety root resolved by another valid migration but cannot terminally settle
old unresolved root later using obsolete/weaker policy to overwrite stronger current Safety
same unresolved cause duplicated solely because Safety generation changed
stale PREPARED retry without material remediation
Genesis containment never producing INITIAL after readiness / migration or INITIAL monitoring gap
SafetyRegistry EMPTY + pre-existing risk under permissive/no containment
nonconservative risk model / slow cadence / omitted trigger / stale feasibility
late observation-response credited / BLOCKED_UNKNOWN without failsafe / discretionary REDUCE
missing Safety-change control affects only future risk while existing risk escapes
source/Decision/Safety/Execution/Deployment omission / manual reduction credited / caller-selected risk scope
pending order settled while fillable / partial remainder loss / broker polling nonce / blind retry / unresolved uncertainty
ancestor invalidation leaves child privilege / Capability direct live injection / ambient broker privilege
```

## 15. Self-Audit gate / hard boundary

```text
minimum logical auditors=12
R8-01..R8-03=INTEGRATED
IA8-01..IA8-64=INTEGRATED
material normative correction=>consecutive clean-pass count=0
FULL COUNCIL CLEAN PASS #1=PASS
FULL COUNCIL CLEAN PASS #2=PASS
END-TO-END REGRESSION=PASS INCLUDING XC-01/XC-02/XC-03 + IA8 attacks + permanent R7 regression families
CONSECUTIVE CLEAN PASS COUNT=2
NEW FROZEN EXTERNAL SUBJECT=NONE UNTIL CANDIDATE FREEZE
DO NOT SEND CURRENT BRANCH TO AUDITOR
ARE-0 CLOSED=NO
ARE implementation=NOT AUTHORIZED
P001 substantive research=NOT AUTHORIZED / UNKNOWN
G1 rerun/retune=PROHIBITED
G2=NOT AUTHORIZED
W2/W3=CLOSED
production=CLOSED
AHFMES-NEW=CLOSED
PR #20 merge=NOT AUTHORIZED
```
