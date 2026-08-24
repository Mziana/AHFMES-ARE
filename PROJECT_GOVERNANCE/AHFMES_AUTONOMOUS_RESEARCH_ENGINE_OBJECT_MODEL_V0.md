# AHFMES Autonomous Research Engine V0 — Object Model, Registries, and State Machines

Status: **DESIGN DIRECTION / NOT IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

This document defines the proposed human-readable data model and lifecycle for a future Autonomous Research Engine (ARE). It is intentionally implementation-neutral.

## 1. Design goal

ARE must be able to answer, at any time:

1. What problem are we researching?
2. Why is it economically important?
3. What evidence has already been consumed?
4. What claims have already been rejected?
5. What exactly is allowed to be searched in this cycle?
6. How many research degrees of freedom have been consumed?
7. What does the Critic have authority to do?
8. Is the candidate still immutable?
9. Has validation or shadow evidence been contaminated by adaptation?
10. What exact evidence supports promotion/rejection/invalidity?
11. What is the ancestry of the current candidate?
12. Is the problem unresolved because of no edge, insufficient sample, or insufficient observability?

## 2. Core registries

### 2.1 Problem Registry

Purpose: maintain unresolved scientific/economic problems rather than searching random strategies.

Suggested fields:

```yaml
problem_id: P001
name: PROFIT_GIVEBACK
status: UNRESOLVED
created_from:
  source_type: PPR_EXPERIMENT
  source_id: PPR_W1_G1
observation_summary: "..."
economic_impact:
  frequency: null
  expected_cost: null
  severity: null
evidence_quality: CANONICAL_REPLAY
known_failed_hypotheses:
  - PPR-G1-001
open_questions:
  - "Does richer pre-decision state contain stable incremental EXIT-vs-CONTINUE value?"
research_history: []
current_observability_status: UNKNOWN
priority: TBD
```

Allowed problem statuses:

```text
OBSERVED
OPEN
RESEARCHING
UNRESOLVED
CURRENTLY_NON_PREDICTABLE
INSUFFICIENT_OBSERVABILITY
INSUFFICIENT_SAMPLE
NO_STABLE_EDGE
RESOLVED_BOUNDED
ARCHIVED
```

`RESOLVED_BOUNDED` means only the bounded research question was answered. It does not imply the entire market phenomenon is solved forever.

### 2.2 Hypothesis Registry

Purpose: distinguish a falsifiable hypothesis from a loose idea.

Suggested fields:

```yaml
hypothesis_id: H-P001-001
problem_id: P001
claim: "..."
parent_hypothesis: null
research_contract_id: RC-P001-001
epistemic_status: PROPOSED
origin:
  generated_by: HUMAN | RESEARCH_BRAIN | CRITIC_LEAD
  discovery_evidence: []
material_difference_from_rejected: "..."
status: PROPOSED
verdict: null
```

Allowed status progression:

```text
PROPOSED
-> CONTRACTED
-> DISCOVERY_ACTIVE
-> DISCOVERY_CLOSED
-> VALIDATION_ELIGIBLE
-> VALIDATING
-> REJECTED | INVALID | SHADOW_ELIGIBLE
-> SHADOW_ACTIVE
-> REJECTED | INVALID | PROMOTION_ELIGIBLE
-> PROMOTED | REJECTED
```

A rejected hypothesis is immutable. A materially changed attempt gets a new ID.

### 2.3 Evidence Ledger

Purpose: record chain-of-custody of every evidence object and claim exposure.

Suggested evidence record:

```yaml
evidence_id: EV-W1-001
source_kind: MARKET_DATA | REPLAY | SHADOW | FORWARD | EXTERNAL_EVENT
source_identity:
  path_or_uri: "..."
  sha256: "..."
information_time_contract:
  event_time: "..."
  source_time: "..."
  received_time: "..."
  processed_time: "..."
  decision_available_time: "..."
usage:
  discovery_exposures: []
  validation_exposures: []
  shadow_exposures: []
exposure_count_total: 0
holdout_status: UNEXPOSED | PARTIALLY_CONSUMED | CONSUMED | RETIRED
claims_supported: []
claims_refuted: []
```

The ledger must support **claim-specific and lineage-specific exposure**, not only a global boolean.

### 2.4 Research Contract Registry

Purpose: freeze a bounded research question before search begins.

Suggested record:

```yaml
research_contract_id: RC-P001-001
problem_id: P001
question: "..."
status: DRAFT | LOCKED | RUNNING | CLOSED
parent_contract_id: null
information_available_at_decision: "..."
hypothesis_universe: "..."
primary_population: "..."
discovery_population: "..."
validation_population: "..."
primary_estimand: "..."
secondary_diagnostics: []
allowed_capability_families: []
prohibited_data: []
search_budget:
  hypothesis_families: N
  feature_inventions: N
  thresholds: N
  interactions: N
  model_families: N
  subgroup_cuts: N
  horizon_variants: N
  metric_variants: 0
multiplicity_method: "..."
stopping_rule: "..."
evidence_exposure_policy: "..."
critic_authority: "ATTACK_ONLY"
promotion_authority: "DETERMINISTIC_GOVERNOR"
```

After `LOCKED`, mutating a scientific degree of freedom invalidates the contract. A new idea becomes a descendant contract.

### 2.5 Experiment Registry

Purpose: bind one execution to one locked contract and immutable candidate.

Suggested fields:

```yaml
experiment_id: EXP-P001-001
research_contract_id: RC-P001-001
candidate_id: C-P001-001
execution_identity: "..."
input_evidence_ids: []
started_at: "..."
ended_at: "..."
run_count: 1
integrity_status: PASS | FAIL
scientific_verdict: REJECT | CLUE | VALIDATED | INVALID
artifacts: []
```

One experiment cannot silently become a new experiment by changing its candidate.

### 2.6 Candidate / Challenger Registry

Purpose: represent proposed policy/model/capability/code descendants as immutable research objects.

Common fields:

```yaml
candidate_id: C-P001-001
candidate_type: POLICY | MODEL | CAPABILITY | CODE
parent_candidate_id: null
parent_champion_identity: "..."
problem_id: P001
research_contract_id: RC-P001-001
reason_for_mutation: "..."
changed_components: []
feature_set_identity: "..."
parameter_identity: "..."
model_identity: null
code_sha: null
status: FROZEN_CANDIDATE
```

Candidate statuses:

```text
DRAFT
FROZEN_CANDIDATE
DISCOVERY_TESTED
VALIDATION_ELIGIBLE
VALIDATING
SHADOW_ELIGIBLE
SHADOW_ACTIVE
PROMOTION_ELIGIBLE
PROMOTED
REJECTED
INVALID
ARCHIVED
```

Any adaptation motivated by candidate outcomes creates a descendant candidate.

### 2.7 Capability Registry

Purpose: let AHFMES expand what it can observe/represent without freezing today's feature vocabulary.

Suggested fields:

```yaml
capability_id: CAP-TF-H1-001
name: H1_CONTEXT
family: TIMEFRAME_CONTEXT
status: DISCOVERY | VALIDATED | SHADOW | ACTIVE | REJECTED
input_sources: []
information_time_contract: "..."
implementation_identity: "..."
known_value_claims: []
known_limitations: []
introduced_for_problem: null
```

Capability existence does not imply capability usefulness.

### 2.8 Graveyard / Rejected Hypothesis Registry

Purpose: prevent rediscovery and post-hoc resurrection of failed ideas.

Minimum record:

```yaml
hypothesis_id: PPR-G1-001
claim: "After +1, protect around break-even improves SHORT W1 economics"
status: REJECTED
canonical_evidence: "artifacts/PPR_W1_G1_REPLAY_2026-08-19/stdout_raw.json"
why_rejected:
  - "operational executable-tick delta negative"
  - "bootstrap lower bounds non-positive"
  - "fold/LODO stability gates failed"
  - "absolute known-cost G1 EV negative"
retry_policy: "PROHIBITED unless materially different hypothesis and new authority"
```

## 3. Scientific state machine

### Problem state

```text
OBSERVED
  ↓
OPEN
  ↓
RESEARCHING
  ├──> RESOLVED_BOUNDED
  ├──> CURRENTLY_NON_PREDICTABLE
  ├──> INSUFFICIENT_OBSERVABILITY
  ├──> INSUFFICIENT_SAMPLE
  ├──> NO_STABLE_EDGE
  └──> UNRESOLVED
```

No state forces generation of a strategy.

### Claim epistemic state

```text
OBSERVED
  ↓
SUSPECTED
  ↓
DISCOVERY_CLUE
  ↓
VALIDATED
  ↓
PRODUCTION_ELIGIBLE
```

Failure can branch at any stage to:

```text
REJECTED
INVALID
```

`INVALID` means the experiment/evidence contract failed; it is different from a valid experiment that scientifically rejected the hypothesis.

## 4. Validation-budget / holdout-consumption model

A long-lived autonomous researcher cannot reuse one holdout forever.

The architecture must treat validation evidence as a finite resource.

Example conceptual ledger:

```text
EV-W2-001
initial status         = UNEXPOSED
RC-001 exposure        = VALIDATION #1
RC-002 exposure        = VALIDATION #2, genealogically related
...
status                 = PARTIALLY_CONSUMED / CONSUMED
```

The exact statistical accounting method is **not yet frozen** in V0, but the architectural requirement is frozen-direction: exposure must be observable, countable, lineage-aware, and capable of making a holdout ineligible for future independent claims.

Future prospective evidence may be required when historical holdouts are exhausted.

## 5. Full-search-tree accounting

A research cycle must record the path by which a winner was found.

Example:

```text
P001
└── RC-P001-001
    ├── Family A
    │   ├── Feature set A1
    │   │   ├── Threshold 1
    │   │   └── Threshold 2
    │   └── Feature set A2
    ├── Family B
    │   └── Model family B1
    └── Family C
        └── subgroup attempt C1
```

The final candidate cannot present itself as "one test" if dozens/hundreds/thousands of branches preceded it.

## 6. Critic contract

The Critic is an authority role, not merely another prompt.

### Allowed

```text
ATTACK
REQUEST_PROVENANCE
ASSERT_LEAKAGE
ASSERT_BUDGET_VIOLATION
ASSERT_MULTIPLICITY_MISMATCH
ASSERT_SAMPLE_WEAKNESS
ASSERT_CLAIM_TOO_BROAD
INVALIDATE
ACCEPT_BOUNDED_CLAIM
```

### Forbidden

```text
RETUNE_THRESHOLD
CHANGE_PRIMARY_METRIC
SELECT_RESCUE_SUBGROUP
CHANGE_HORIZON_AFTER_RESULT
ADD_UNBUDGETED_FEATURE
REWRITE_FAILED_CANDIDATE_IN_PLACE
PROMOTE_TO_CAPITAL
```

Critic suggestions may seed a **new descendant research contract** only after the current verdict is closed.

## 7. Governor contract

Governor must consume frozen evidence and return a mechanical disposition.

Preferred top-level dispositions:

```text
INVALID
REJECT
VALIDATED_BUT_NOT_PRODUCTION_ELIGIBLE
SHADOW_ELIGIBLE
PROMOTION_ELIGIBLE
PROMOTE
```

A promotion gate should compare challenger vs champion using **incremental decision value** and risk/stability constraints, not a raw P&L leaderboard.

Possible gate dimensions:

- paired incremental EV where credible;
- executable cost-adjusted economics;
- uncertainty interval;
- temporal/fold stability;
- tail loss;
- concentration;
- sample support;
- regime/OOD sensitivity;
- execution feasibility;
- capital-safety regression;
- evidence-consumption validity.

Exact numerical gates are future design work and are not authorized by V0.

## 8. Shadow lifecycle

```text
Candidate C1 frozen
        ↓
SHADOW_START
        ↓
receives real-time market/information stream
        ↓
C1 MUST NOT learn from its own outcome
        ↓
SHADOW_CLOSE
        ↓
ADJUDICATE C1
```

If the outcome suggests a change:

```text
C1 remains unchanged
        ↓
create C2
parent = C1
reason = shadow-derived observation
        ↓
new contract / new exposure accounting as required
```

## 9. Capability-gap state machine

Research failure does not imply missing sensors.

```text
NO STABLE ANSWER
      ↓
classify failure
      ├── insufficient sample
      ├── currently non-predictable
      ├── execution economics destroy signal
      ├── problem formulation weak
      └── evidence supports insufficient observability
                                      ↓
                              CAPABILITY_GAP_CLUE
                                      ↓
                              bounded capability research
```

Only the final branch opens a capability question.

## 10. Code-candidate genealogy

For eventual code evolution:

```yaml
code_candidate_id: CODE-031
parent_sha: "..."
problem_id: Pxxx
research_contract_id: RC-xxx
reason_for_mutation: "..."
changed_capabilities:
  - "..."
files_changed: []
static_checks: null
unit_tests: null
regression: null
scientific_validation: null
shadow_evidence: null
governor_disposition: null
rollback_target: "..."
```

The active champion is never modified in place by the same process that generated the candidate.

## 11. Seed record: P001 PROFIT GIVEBACK

```yaml
problem_id: P001
name: PROFIT_GIVEBACK
status: UNRESOLVED
known_failed_hypothesis:
  id: PPR-G1-001
  rule: "after executable +$1, protect around gross break-even"
  verdict: PPR_W1_G1_REJECT
canonical_artifact: artifacts/PPR_W1_G1_REPLAY_2026-08-19/
known_lesson: >
  Binary state 'ever reached +1' plus 'returned around 0' was not sufficient
  to produce robust incremental executable value under the frozen W1 replay.
open_question: >
  Does richer information available before the exit decision contain stable
  incremental decision value for EXIT versus CONTINUE?
answer: UNKNOWN
```

P001 must not be silently converted into "try G1.1", "try G2", "try ATR", or "try higher timeframe". Those are possible future hypotheses only if a locked Research Contract lawfully produces them.

## 12. V0 non-authority

This object model is a design target. It does not authorize schemas/code/database migration, new data access, W2/W3, Training/OOS, live shadow execution, code generation, production modification, or merge.