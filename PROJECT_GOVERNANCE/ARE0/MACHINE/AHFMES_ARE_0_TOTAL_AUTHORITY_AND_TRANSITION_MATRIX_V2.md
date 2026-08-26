# AHFMES ARE-0 — Canonical Authority & Transition Matrix V2

Status: **SOLE CANONICAL MACHINE SOURCE / R9 CORRECTED FORMAL DESIGN / STATELESS CLOSURE SUBJECT / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Canonical composition / precedence

This file is the sole current machine source for the R9-corrected ARE-0 formal design.

Immutable incorporated base:

```text
BASE_MATRIX_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V1.md
BASE_MATRIX_GIT_BLOB_SHA = c9ae503c74d5b94b2dac992b0c4d2fc6a9d00474
```

The exact base blob is incorporated as machine semantics except:

```text
BASE header/status assertions = HISTORICAL / NOT CURRENT AUTHORITY
BASE §15 self-audit/gate/status assertions = HISTORICAL / NOT CURRENT AUTHORITY
any base clause explicitly replaced or narrowed by this V2 = REPLACED
```

```text
V2 EXPLICIT REPLACEMENT/NARROWING > INCORPORATED BASE BLOB
UNLISTED OLDER/SUBORDINATE FILE = NO AUTHORITY
BASE PATH WITH DIFFERENT BLOB = NOT INCORPORATED
EDGE ABSENT FROM (INCORPORATED BASE + V2) = DENIED
AUTHORITY ABSENT FROM (INCORPORATED BASE + V2) = INVALID
GENESIS MODE ABSENT FROM (INCORPORATED BASE + V2) = INVALID OBJECT AUTHORITY
WRITER ABSENT FROM (INCORPORATED BASE + V2) = WRITE DENIED
UNKNOWN MATERIAL AUTHORITY / CONTROL / LINEAGE / FRESHNESS / COMPLETENESS /
REVALIDATION / ROLLBACK CAUSALITY / MUTATION BOUNDARY / BROKER STATE
= FAIL CLOSED
NO AMBIENT PRIVILEGE
```

R9 machine replacement surfaces are exactly:

```text
R9-01 bootstrap trust / SystemGenesis authority and crash-idempotency
R9-02 Challenge post-access terminal accounting
R9-04 current scientific-reliance revalidation
R9-05 rollback policy / cause provenance / fallback eligibility
R9-06 material risk-state mutation boundary
R9-07 layered operational completeness / completeness SoD
```

R9-03 is closure protocol only; it grants no live/scientific/capital edge.

This Matrix contains no mutable clean-pass/external-audit progress state. Such progress is recorded outside the normative authority root.

## 1. R9-01 — exogenous bootstrap trust / atomic genesis

### 1.1 Exogenous root-of-trust premise

`BOOTSTRAP_TRUST_ANCHOR_ROOT` is an exogenous pre-system root-of-trust premise, not an ARE object, RoleManifest, VAR, TrustedAuthorityRegistry entry, GovernanceRoot generation or post-genesis authority.

It binds:

```text
exact constitutional/bootstrap root
exact Genesis control identity
exact Bootstrap-Audit control identity
positive common-control separation: Genesis != Bootstrap-Audit
bootstrap capability scope = A-PREGENESIS-IMPORT + A-SYSTEM-GENESIS only
no Research / Validation / Promotion / Safety / Execution / broker privilege
```

Absent/UNKNOWN premise, identity, separation or scope => pre-system authority unavailable.

### 1.2 Canonical bootstrap epoch

```text
BOOTSTRAP_EPOCH_KEY = hash(
  BOOTSTRAP_TRUST_ANCHOR_ROOT,
  exact Genesis control identity,
  exact Bootstrap-Audit control identity,
  pre-genesis scientific-state payload root,
  exact SystemGenesis generation-#0 object-set root,
  Genesis containment/change-policy roots,
  bootstrap Champion/comparator/error/order roots
)
```

Pre-system persistence provides one semantic CAS slot per epoch.

```text
same epoch + same payload retry = same canonical continuation/result
same epoch + conflicting payload = INVALID
concurrent nodes same epoch/same payload = exactly one canonical result
```

The pre-genesis payload root is computed before write; `A-PREGENESIS-IMPORT` records that exact root. Crash after import permits only identical continuation.

### 1.3 SystemGenesis semantic atomicity

Base bootstrap authority is replaced by:

```text
A-SYSTEM-GENESIS prerequisite =
  valid BOOTSTRAP_TRUST_ANCHOR_ROOT
  + exact Genesis identity
  + exact independent Bootstrap-Audit identity
  + positive control separation
  + exact BOOTSTRAP_EPOCH_KEY
```

```text
SYSTEM_GENESIS_COMMIT =
  create exact generation-#0 object set
  + bind bootstrap epoch/trust/control roots into SystemGenesisManifest
  + consume bootstrap epoch capability
  + seal pre-system CAS slot terminal
```

Mandatory theorem:

```text
SystemGenesis #0 exists
=> BOOTSTRAP_EPOCH_KEY irrevocably consumed
=> bootstrap capability permanently unusable
```

No legal crash state allows generation #0 and reusable bootstrap authority simultaneously. Initial roles/registries/root machinery become authoritative only after the semantic commit and never retroactively authorize genesis.

### 1.4 Exact authority rows

| Authority | Issuer approval | Executor / holder | Usage | Exact scope / prerequisites | Capital |
|---|---|---|---|---|---|
| A-PREGENESIS-IMPORT | exogenous BootstrapTrust: exact Genesis + independent Bootstrap-Audit | Bootstrap-Audit | ONE_SHOT per BOOTSTRAP_EPOCH_KEY | exact pre-genesis payload root; identical retry only | NO |
| A-SYSTEM-GENESIS | exogenous BootstrapTrust: exact Genesis + independent Bootstrap-Audit | Genesis | ONE_SHOT per BOOTSTRAP_EPOCH_KEY | exact epoch + base §3 generation-#0 set + atomic bootstrap consumption | NO |

Post-genesis, incorporated root/VAR/role rules apply. Bootstrap authority is dead.

## 2. R9-02 — total Challenge allocation settlement

### 2.1 Stable semantic opportunity

At first eligibility, before relevant outcome access:

```text
CHALLENGE_SEMANTIC_OPPORTUNITY_ROOT = hash(
  Champion slot,
  exact incumbent,
  Candidate root,
  exact eligible Contract root,
  PROOF_RESERVATION_ROOT,
  CHALLENGE_ALLOCATION_ORDER_KEY,
  ChampionChallengePolicy generation,
  CHAMPION_LIFECYCLE_POLICY_BUNDLE_ROOT
)
```

Later exposure, retry, wrapper ID, policy reserialization, session/time cannot change this root. The append-only Challenge allocation obligation binds it.

### 2.2 Pre-outcome accounting policy

Base Challenge order rule is replaced/narrowed to freeze before outcome:

```text
CHALLENGE_ALLOCATION_ORDER_RULE_ROOT = hash(
  canonical first-eligibility information-time definition,
  stable opportunity tie-break,
  batching rule,
  frozen error-spending/renewal semantics,
  PREVALIDATION_BLOCKED_ACCOUNTING_RULE_ROOT,
  POSTACCESS_BLOCKED_ACCOUNTING_RULE_ROOT
)
```

Both blocked-accounting roots deterministically map precommitted policy + whole-search/Challenge debt state to conservative selection/error-spend consequence. No post-result principal chooses a cheaper disposition.

### 2.3 Total access / eligibility classes

At registration frontier derive, under governed access boundary:

```text
ACCESS_CLASS = NO_ACCESS_PROVEN | ACCESS_PROVEN | ACCESS_UNKNOWN
ELIGIBILITY_CLASS = ELIGIBLE_TRUE | ELIGIBLE_FALSE | ELIGIBILITY_UNKNOWN
```

Exactly one initial disposition is legal:

```text
REGISTERED
= ACCESS_CLASS = NO_ACCESS_PROVEN
  AND ELIGIBILITY_CLASS = ELIGIBLE_TRUE

PREVALIDATION_BLOCKED
= ACCESS_CLASS = NO_ACCESS_PROVEN
  AND ELIGIBILITY_CLASS IN {ELIGIBLE_FALSE, ELIGIBILITY_UNKNOWN}

POSTACCESS_BLOCKED
= ACCESS_CLASS IN {ACCESS_PROVEN, ACCESS_UNKNOWN}
  regardless of ELIGIBILITY_CLASS
```

Thus material UNKNOWN never grants Validation/Promotion and never deadlocks the allocation queue merely because definitive private-access classification is impossible.

`ELIGIBILITY_UNKNOWN` under proven no-access uses the frozen conservative prevalidation accounting rule. `ACCESS_UNKNOWN` uses the frozen conservative postaccess accounting rule and records access uncertainty/integrity state.

### 2.4 Atomic blocked payloads

For exact `NEXT_CANONICAL_CHALLENGE_ALLOCATION_SLOT`:

```text
PREVALIDATION_BLOCKED writes:
  CHALLENGE_SEMANTIC_OPPORTUNITY_ROOT
  deterministic conservative selection-debt charge
  deterministic no-outcome error-spend consequence
  eligibility cause/class
  terminal ChallengeAttempt + ChallengeLedger settlement

POSTACCESS_BLOCKED writes:
  CHALLENGE_SEMANTIC_OPPORTUNITY_ROOT
  deterministic conservative selection-debt charge
  deterministic conservative postaccess error-spend consequence
  POSTACCESS_EXPOSURE_LINEAGE_ROOT
  ACCESS_CLASS = ACCESS_PROVEN | ACCESS_UNKNOWN
  terminal ChallengeAttempt + ChallengeLedger settlement
```

Both grant no Validation/Promotion authority. `POSTACCESS_BLOCKED -> REGISTERED/PROMOTED = DENIED`.

`ACCESS_UNKNOWN` also creates/links the applicable IntegrityDefect/access-uncertainty evidence. Unauthorized validation already started creates independent IntegrityDefect + proof/dependency invalidation in addition to terminal accounting.

Later exposure lineage is payload, never slot identity.

### 2.5 No revival / no global tombstone

Same semantic opportunity or materially same contaminated scientific opportunity wrapped in new ID/Contract/policy generation cannot register again.

A later genuinely new proof opportunity is legal only with mechanically new governed evidence/proof authority, valid independence/identification and full inherited contamination/search/selection debt lineage. Old obligation remains terminal; Candidate is not globally tombstoned solely by one blocked opportunity.

### 2.6 Exact authority / transitions

| Authority | Issuer approval | Executor / holder | Usage | Exact scope / prerequisites | Capital |
|---|---|---|---|---|---|
| A-CHALLENGE-REGISTER | Promotion | ChampionRegistry | ONE_SHOT per CHALLENGE_SEMANTIC_OPPORTUNITY_ROOT | exact NEXT_CANONICAL; total access/eligibility classes; frozen accounting roots | registry |

Base initial §12.8 edges are replaced by the three total guards above.

## 3. R9-04 — Champion current scientific reliance / revalidation

### 3.1 Pre-outcome lifecycle bundle

Before relevant Challenger outcome access:

```text
CHAMPION_LIFECYCLE_POLICY_DERIVATION_ROOT
CHAMPION_LIFECYCLE_POLICY_BUNDLE_ROOT = hash(
  REVALIDATION_POLICY_ROOT,
  ROLLBACK_POLICY_ROOT,
  every other material survival/recovery policy
)
```

The bundle is mechanically derived from constitution/claim/risk/deployment class or chosen only through prospectively governed/search-accounted alternatives before outcome.

It is transitively bound by:

```text
PROOF_RESERVATION_ROOT
CHALLENGE_SEMANTIC_OPPORTUNITY_ROOT
Challenge error-control instance where applicable
FINAL_COMPARATIVE_EVALUATION_ROOT
PROOF_RELIANCE_ROOT
PromotionTransaction
CHAMPION_SELECTION_RELIANCE_ROOT
```

Post-outcome lifecycle change is a new meta-policy requiring new scientific/selection accounting.

### 3.2 Persistent current-reliance state

R9 adds:

```text
ChampionRelianceRegistry
ChampionRevalidationRecord
```

Per Champion selection generation:

```text
RELIANCE_STATE = CURRENT | SUSPENDED | REVOKED
```

Historical ProofBundle/PROOF_RELIANCE_ROOT never change.

Successful Promotion atomically creates:

```text
ChampionRelianceRegistry[Champion selection generation] = CURRENT
binds historical proof reliance + selection reliance + lifecycle bundle + initial reliance frontier
```

`CHAMPION_GENERATION_RELIANCE_ELIGIBLE(g)` is per generation, not synonymous with “currently selected”. Monitoring remains applicable to a displaced generation while it is retained as a live rollback target under an unconsumed RollbackPlan; otherwise expiry can make it ineligible without affecting current selection.

### 3.3 Revalidation policy / order rule

`REVALIDATION_POLICY_ROOT` prospectively freezes:

```text
trigger/cadence/support-expiry rules
required Evidence class
DGP/intervention/identification requirements
claim/risk evidence horizon
material DGP/regime relevance-change response
material operational-drift response
missing/late/UNKNOWN semantics
sequential/multiplicity error treatment
REVALIDATION_ORDER_RULE_ROOT
REVALIDATION_RECOVERY_RULE_ROOT
```

`REVALIDATION_ORDER_RULE_ROOT` freezes:

```text
FIRST_REVALIDATION_INFORMATION_TIME definition
stable trigger tie-break
batching/coalescing rule
canonical order
revalidation completion/deadline semantics
```

`REVALIDATION_POLICY_ADMISSIBILITY_VALID` requires materially adequate coverage and realistically satisfiable governed evidence. Empty trigger coverage, unjustified extreme cadence, unreachable evidence class or indefinite retain-on-UNKNOWN are invalid.

### 3.4 Expected obligations / canonical order

Every required trigger creates an append-only semantic obligation at first canonical information frontier:

```text
REVALIDATION_ORDER_KEY = tuple(
  FIRST_REVALIDATION_INFORMATION_TIME,
  stable trigger identity under frozen tie-break
)

REVALIDATION_OPPORTUNITY_KEY = hash(
  Champion selection generation,
  CHAMPION_LIFECYCLE_POLICY_BUNDLE_ROOT,
  REVALIDATION_ORDER_KEY,
  required method/evidence class,
  prior canonical revalidation lineage
)

NEXT_CANONICAL_REVALIDATION_SLOT = minimum unsettled obligation under REVALIDATION_ORDER_KEY
```

Later obligations cannot leapfrog an earlier unsettled one. Batching/coalescing is allowed only exactly as precommitted by the order rule.

```text
REVALIDATION_OPPORTUNITY_COVERAGE_CURRENT
= every required obligation through relied frontier is terminal or exact allowed in-progress slot under frozen deadline rule
```

If an obligation passes its deterministic deadline without terminal disposition, reliance becomes `SUSPENDED`; no synthetic PASS exists.

### 3.5 Explicit proof / nonproof terminal authority

For exact `NEXT_CANONICAL_REVALIDATION_SLOT`:

```text
EvidenceReservation[REVALIDATION] absent
+ CandidateProofEpisode[REVALIDATION] absent
-> VALIDATION_RESERVED
= A-EVIDENCE-RESERVE[REVALIDATION]

VALIDATION_RESERVED -> VALIDATING = A-VALIDATE[REVALIDATION]
VALIDATING -> VALIDATION_CLOSED = A-VALIDATE[REVALIDATION]
VALIDATION_CLOSED -> CRITIC_REVIEWED = A-CRITIC
CRITIC_REVIEWED -> SCIENTIFIC_ADJUDICATED = A-ADJUDICATE
```

ScientificAdjudicationRecord seals:

```text
REVALIDATION_SCIENTIFIC_DISPOSITION_ROOT = deterministic mapping under frozen policy
result class = PASS | FAIL | NEGATIVE | UNKNOWN
```

Governor cannot choose the scientific result. Exact authority:

| Authority | Issuer approval | Executor / holder | Usage | Exact scope / prerequisites | Capital |
|---|---|---|---|---|---|
| A-GOVERN[REVALIDATION_PROOF] | exact ScientificAdjudicationRecord + frozen deterministic disposition + Critic/Governor SoD | Governor | ONE_SHOT per REVALIDATION_OPPORTUNITY_KEY | exact NEXT slot; write exact mapped disposition + reliance update; no selection/fallback | indirect eligibility |
| A-GOVERN[REVALIDATION_NONPROOF] | canonical deadline/expiry state + independent Audit evidence of unavailable/missed proof | Governor | ONE_SHOT per REVALIDATION_OPPORTUNITY_KEY | exact NEXT slot; only EXPIRED/UNKNOWN_NO_PROOF adverse terminal; never PASS | indirect eligibility |

`A-GOVERN[REVALIDATION_PROOF]` atomically writes `ChampionRevalidationRecord` + reliance CAS. `A-GOVERN[REVALIDATION_NONPROOF]` terminally settles an otherwise deadlocking missed/unavailable obligation and suspends reliance.

Same opportunity/same payload returns existing; conflict => IntegrityDefect.

### 3.6 Reliance state transitions

Deterministic mapping:

```text
CURRENT + PASS -> CURRENT refreshed within already-proven scope
CURRENT + UNKNOWN/EXPIRED/UNKNOWN_NO_PROOF -> SUSPENDED
CURRENT + FAIL/NEGATIVE -> REVOKED

SUSPENDED + approved RECOVERY opportunity PASS -> CURRENT
SUSPENDED + adverse/unknown -> SUSPENDED or REVOKED according to frozen mapping

REVOKED -> CURRENT by revalidation = DENIED
REVOKED -> SUSPENDED = DENIED
```

A `RECOVERY` opportunity is legal only if prospectively permitted by `REVALIDATION_RECOVERY_RULE_ROOT`, mechanically distinct, ordered, sequential-error accounted, and all prior adverse lineage remains visible. It can recover insufficiency/expiry suspension; it cannot erase a material FAIL/NEGATIVE.

A REVOKED Champion behavior can regain new-risk authority only through new governed scientific/selection proof and Challenge/Promotion, with inherited history/debt. This prevents revalidation from becoming regime-based on/off selection.

### 3.7 Live exposure split

When state ceases CURRENT:

```text
new alpha/risk-increasing authority = stale immediately
normal new risk = DENIED
stale risk-increasing pending/conditional authority = cancel/reconcile
```

Existing-risk escape remains under Safety/recovery:

```text
protective / cancel / monotonic reduce / close / deactivation authority survives
```

If broker/mutation boundary is UNKNOWN, reduction follows current reconciliation/worst-case Safety rules first; stale alpha never authorizes blind broker mutation.

## 4. R9-05 — rollback recovery, not hidden selection

### 4.1 Policy / fallback

`ROLLBACK_POLICY_ROOT` is inside the pre-outcome lifecycle bundle. Exact RollbackPlan is deterministic from it.

```text
FALLBACK_ROLLBACK_ELIGIBILITY_VALID =
  target = exact previously displaced incumbent
  + historical CHAMPION_SELECTION_RELIANCE_ROOT_AT_DISPLACEMENT exists and is uninvalidated
  + target CHAMPION_GENERATION_RELIANCE_ELIGIBLE = TRUE
  + target proof reliance current for intended scope
  + target runtime/Safety/deployment-preflight eligibility positively satisfiable
  + no integrity/ancestry invalidation
```

Fallback need not already be selected or deployed. Successful rollback changes selection only; `selected != deployed` remains and fresh DeploymentEpisode/preflight is mandatory before new risk.

If false/UNKNOWN: rollback denied; new risk denied; safe deactivation/drain as applicable.

### 4.2 Cause provenance / timing

```text
ROLLBACK_CAUSE_EVENT_KEY = hash(
  frozen allowed cause class,
  first canonical cause-information frontier,
  exact upstream mutation/event lineage,
  cause producer/control root,
  cause attestation root
)
```

`ROLLBACK_CAUSE_LINEAGE_VALID` requires genuine material cause, canonical first-information time, first-eligible policy handling, and common-control/SoD validity among cause creator, attester and rollback executor.

If a discretionary upstream mutation creates the cause, it must have a prospectively defined non-performance/non-strategy-selection governance key and may not be timed/selected using Champion outcome, PnL, market/regime or equivalent alpha information to obtain rollback privilege.

Volatility/session/regime/time/PnL switching is not rollback unless the switching policy itself went through THINK→PROVE→ACT.

## 5. R9-06 — material risk-state mutation boundary

### 5.1 Persistent objects / deterministic generations

R9 adds:

```text
CapitalMutationBoundaryRegistry
CapitalMutationBoundaryManifest
```

```text
NEXT_MUTATION_BOUNDARY_GENERATION = 1 + max(all generations ever allocated, including invalid/stale)
```

Every material boundary change creates a canonical update opportunity:

```text
MUTATION_BOUNDARY_INPUT_FRONTIER_ROOT = hash(
  exact mutation-source registry/control heads,
  exact broker credential/fencing/exclusivity heads,
  exact broker observation/reconciliation heads,
  standing conditional/protective state heads,
  relevant runtime/authority heads,
  applicable broker/exposure completeness head,
  canonical information frontier
)

MUTATION_BOUNDARY_GENERATION_SLOT_KEY = hash(
  protected scope root,
  NEXT_MUTATION_BOUNDARY_GENERATION,
  exact predecessor generation/root or EMPTY,
  MUTATION_BOUNDARY_INPUT_FRONTIER_ROOT
)
```

One slot/same payload -> existing; conflict -> IntegrityDefect. A stale proposal cannot reuse or skip generation history.

### 5.2 Complete source theorem

Manifest binds:

```text
protected scope
MATERIAL_MUTATION_SOURCE_COVERAGE_ROOT
complete MATERIAL_RISK_STATE_MUTATION_SOURCE set
source classifications/control roots
fencing/exclusivity evidence
shared canonical reservation/reconciliation topology
broker-native mutation classes/semantics
standing conditional/protective interaction model
observation/reconciliation contract
MUTATION_BOUNDARY_INPUT_FRONTIER_ROOT
MUTATION_BOUNDARY_GENERATION
```

Sources include ARE and other processes, manual actors, server-side SL/TP/conditional fills, stop-out/liquidation, cancel/reject/amend/fill and other broker-native material transitions.

```text
CAPITAL_RISK_MUTATION_BOUNDARY_VALID
IFF every material source is:
A serialized through same canonical risk/reservation/reconciliation topology; OR
B positively fenced/excluded; OR
C broker-native governed class with positively bounded/observed effects and interactions;
otherwise UNKNOWN/invalid.
```

Nominal “risk reducing” does not prove safety because standing protection may invert.

### 5.3 Exact authority / CAS frontier

| Authority | Issuer approval | Executor / holder | Usage | Exact scope / prerequisites | Capital |
|---|---|---|---|---|---|
| A-RUNTIME-RECONCILE[MUTATION_BOUNDARY] | CapitalSafety + independent Audit | CapitalSafety | ONE_SHOT per generation slot | exact predecessor + exact MUTATION_BOUNDARY_INPUT_FRONTIER_ROOT + complete source/fencing/broker/reconcile proof; performance-blind | NO |

The local transaction CAS-compares the exact predecessor registry **and every locally authoritative head included in the input frontier**. Any such head advance before commit makes the transaction lose. External facts not locally CAS-able are bounded by canonical observation identity/freshness; known advance invalidates current generation immediately.

First generation occurs after SystemGenesis and before normal new risk; no permissive implicit generation exists.

Every risk authorization, ExecutionIntent, ActivationIntent, BrokerMutationRecord, RecoveryIntent and settlement/reconcile result binds exact generation.

Validity spans:

```text
AUTHORIZE -> DISPATCH -> BROKER ACCEPT -> PARTIAL/FILL -> SETTLEMENT
```

Loss before send stales unused risk authority. Loss after send makes execution uncertain, retains worst-case reservation, denies new risk and mandates broker reconciliation + Safety observation. External/broker-native mutation is not credited until reconciled exposure and standing protective polarity are re-evaluated.

## 6. R9-07 — layered operational completeness / adverse-history closure

### 6.1 Non-substitutable surfaces

`OperationalCompletenessRecord` is typed by exactly one:

```text
DECISION_INPUT_COMPLETENESS
EXECUTION_DISPATCH_SETTLEMENT_COMPLETENESS
CAPITAL_BROKER_EXPOSURE_COMPLETENESS
SAFETY_OBSERVATION_RESPONSE_COMPLETENESS
```

No PASS substitutes for another surface.

### 6.2 One-slot identity

```text
OPERATIONAL_COMPLETENESS_KEY = hash(
  surface class,
  source contract / authoritative boundary root,
  required event-universe root,
  exact coverage interval/frontier,
  transport/capture boundary root,
  canonicalization rule root,
  gap-detection rule root,
  relied dependency root
)
```

One key has one canonical disposition:

```text
PASS | FAIL | UNKNOWN
```

Same key/same payload -> existing; conflict -> IntegrityDefect. Retry/time/session cannot remint.

### 6.3 Adverse-history theorem

Every surface maintains derived:

```text
COMPLETENESS_ADVERSE_LINEAGE_ROOT
= append-only fold of every FAIL/UNKNOWN/gap/late-defect record affecting the relied lineage

COMPLETENESS_CURRENT(surface, relied_frontier)
= required interval/universe coverage PASS
  AND no unresolved adverse lineage affecting any relied dependency/frontier
```

A later PASS on a successor interval/key does not erase an earlier required gap.

A prior adverse gap may be positively resolved only by:

```text
COMPLETENESS_DEFECT_RESOLUTION_ROOT = hash(
  exact adverse record/gap identity,
  authoritative backfill/reconstruction/reconciliation evidence,
  proof that exact required event universe for affected interval is recovered or dependency no longer relies on it,
  independent Audit attestation,
  affected reliance invalidation/re-adjudication lineage
)
```

If exact reconstruction or dependency removal cannot be proven, the adverse lineage remains unresolved.

### 6.4 Proof payload / SoD

Each record binds source contract, event universe, interval/frontier, transport/capture, canonicalization, gap detection, auditor/control identity, subject/capture identity and reconciliation semantics where applicable.

The theorem proves the exact frozen Candidate/Safety/execution event contract, not impossible world omniscience. If required event/gap semantics are not provable, disposition is UNKNOWN.

```text
AUDIT[COMPLETENESS_SURFACE]
!= common control of exact capture/control surface being attested
```

unless a positively proven external/self-verifying mechanism cannot be forged/suppressed by the subject.

Base `A-INTEGRITY-AUDIT[OPERATIONAL_COMPLETENESS]` is narrowed to exact one-slot key. Late defect creates IntegrityDefect + affected dependency/reliance invalidation; historical records are not rewritten.

### 6.5 Normal-new-risk narrowing

Base normal-new-risk gate additionally requires as applicable:

```text
CHAMPION_GENERATION_RELIANCE_ELIGIBLE(selected generation)
REVALIDATION_POLICY_ADMISSIBILITY_VALID
REVALIDATION_OPPORTUNITY_COVERAGE_CURRENT
CHAMPION_LIFECYCLE_POLICY_BUNDLE_CURRENT
CAPITAL_MUTATION_BOUNDARY_GENERATION_CURRENT
CAPITAL_RISK_MUTATION_BOUNDARY_VALID
DECISION_INPUT_COMPLETENESS_CURRENT
EXECUTION_DISPATCH_SETTLEMENT_COMPLETENESS_CURRENT
CAPITAL_BROKER_EXPOSURE_COMPLETENESS_CURRENT
SAFETY_OBSERVATION_RESPONSE_COMPLETENESS_CURRENT
NO_UNRESOLVED_MATERIAL_RISK_STATE_MUTATION
```

Material UNKNOWN => fail closed.

## 7. R9 exact writer additions

```text
ChampionRelianceRegistry
  -> A-PROMOTE[PROMOTED]
  -> A-GOVERN[REVALIDATION_PROOF]
  -> A-GOVERN[REVALIDATION_NONPROOF]
  -> A-INTEGRITY-AUDIT[RELIANCE_DEPENDENCY]

ChampionRevalidationRecord
  -> A-GOVERN[REVALIDATION_PROOF]
  -> A-GOVERN[REVALIDATION_NONPROOF]

CapitalMutationBoundaryRegistry
  -> A-RUNTIME-RECONCILE[MUTATION_BOUNDARY]

CapitalMutationBoundaryManifest
  -> A-RUNTIME-RECONCILE[MUTATION_BOUNDARY]

OperationalCompletenessRecord
  -> A-INTEGRITY-AUDIT[OPERATIONAL_COMPLETENESS] under exact key
```

No older generic writer widens these guards.

## 8. R9 forbidden hidden control planes

The incorporated base forbidden set remains and gains:

```text
self-declared bootstrap trust or bootstrap validated by own generation-#0 objects
same bootstrap epoch alternate payload after crash
SystemGenesis exists with reusable bootstrap authority
Challenge unknown access/eligibility causing permanent allocation deadlock
Challenge initial guard overlap
postaccess penalty chosen after outcome
later exposure used to mint new Challenge semantic slot
POSTACCESS erases debt or wrapper revives same opportunity
winner known before lifecycle bundle fixed
post-result survival policy attached to winner
multiple revalidation triggers settled scheduler-order rather than canonical order
Governor choosing revalidation scientific result instead of deterministic adjudication mapping
missing revalidation proof permanently deadlocking later obligations
revalidation FAIL/NEGATIVE later restored by routine PASS
revalidation optional on/off regime switching
vacuous revalidation policy / delayed opportunity / retry-until-PASS
revalidation failure removes safe reduction authority
rollback to stale/invalid fallback
rollback requires fallback already selected/deployed
outcome-aware maintenance/config timing manufactures rollback cause
mutation-boundary proof commits after relied local source/control head advanced
mutation-boundary generation reused/skipped/conflicted
shared ledger while writer bypasses canonical mutation topology
boundary loss after send treated ordinary settlement
broker-native mutation omitted
completeness successor PASS erases unresolved prior gap
completeness same-key retry until PASS
DecisionInput completeness substituted for broker/exposure/Safety completeness
common-controlled capture self-attestation without unforgeable boundary
unknown source contract represented complete
```

## 9. Static formal boundary

This design itself grants none of the following:

```text
ARE-0 closure
implementation authority
P001 substantive research authority
production authority
PR merge authority
```

Clean-pass count, impact-audit progress, candidate SHA and external-audit disposition are **not machine semantics in this Matrix**. They are recorded in non-normative orientation/audit records under Council Protocol V2.
