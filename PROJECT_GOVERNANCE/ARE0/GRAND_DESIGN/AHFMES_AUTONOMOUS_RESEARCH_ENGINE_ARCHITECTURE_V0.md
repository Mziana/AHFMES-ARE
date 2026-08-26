# AHFMES Autonomous Research Engine — Architecture V0 Direction

Status: **ARCHITECTURAL DIRECTION / NOT IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**  
Repository: `Mziana/AHFMES-CHATGPT`

## 1. Purpose

This document records the accepted direction for the next research/development phase after the closed `POSITION_PATH_REPLAY_V1` W1 G1 experiment.

It does **not** authorize implementation, W2/W3 access, Training/OOS, production changes, merge, live capital use, or any retry/retune of the rejected G1 hypothesis.

The project direction is no longer to keep manually tuning individual entry/exit rules. The target is to make AHFMES progressively capable of discovering problems, forming bounded hypotheses, testing them, rejecting false ideas, remembering evidence, and proposing evolutionary descendants under a hard scientific and capital-safety boundary.

Core principle:

> **Do not limit what AHFMES may think about. Limit what may be treated as proven and what may touch capital.**

## 2. What is frozen vs evolvable

### Frozen / constitutional

- evidence-first scientific discipline;
- micro-execution economic horizon;
- uncertainty awareness;
- path/state awareness;
- provenance and auditability;
- no leakage;
- discovery != validation;
- no self-acceptance;
- bounded research search;
- rejected evidence remains immutable;
- capital survival constraints.

### Evolvable research space

- timeframe / information horizon;
- indicators and feature families;
- market representations;
- models;
- policy composition;
- external data sources;
- news/event context;
- intermarket context;
- capabilities;
- eventually code, but only as isolated candidates.

`HIGH OPPORTUNITY DENSITY` is a preference conditional on evidence, not a quota. Frequency must never override evidence quality.

## 3. Three-world authority model

```text
WORLD 1 — THINK
Research / discovery / hypothesis / capability search

          ↓

WORLD 2 — PROVE
Scientific Constitution / Critic / validation / frozen shadow / Governor

          ↓

WORLD 3 — ACT
Operational Brain / Capital Safety Kernel / Executor
```

Allowed flow:

```text
THINK -> PROVE -> ACT
```

Prohibited flow:

```text
THINK --------> ACT
```

Research/candidate creation and promotion/capital authority are separate powers.

## 4. Scientific Constitution

The Scientific Constitution protects the system from false knowledge.

Mandatory principles:

- no data leakage;
- as-of / information-time provenance;
- discovery and validation must be separated;
- no self-validation / no self-acceptance;
- primary population and primary estimand frozen before validation;
- full multiplicity accounting;
- research budget and stopping rule frozen before search;
- validation exposure is consumable, not infinitely reusable;
- rejected evidence is immutable;
- candidate genealogy is mandatory;
- `NO RESULT` is a valid scientific outcome;
- `CURRENTLY_NON_PREDICTABLE` is a valid problem state.

## 5. Capital Safety Kernel

The Capital Safety Kernel protects the system from economic/technical ruin and is not a performance feature family.

Examples:

- maximum catastrophic loss;
- maximum exposure;
- emergency flat / kill switch;
- broker sanity;
- data sanity;
- execution bounds;
- production authority boundary;
- rollback capability.

A candidate may not argue that disabling a survival guard is an acceptable way to improve EV.

## 6. Evidence Ledger

Scientific Memory alone is insufficient. AHFMES must know not only *what* it believes, but *why* it is entitled to believe it.

Each claim/evidence relationship should eventually record at least:

```text
claim_id
source_data
information_available_as_of
discovery_use
validation_use
exposure_count
research_lineage
search_family
multiplicity_account
epistemic_status
production_authority
```

Example states:

```text
OBSERVED
SUSPECTED
DISCOVERY_CLUE
VALIDATED
PRODUCTION_ELIGIBLE
REJECTED
```

### Holdout exhaustion

A validation dataset cannot be treated as permanently untouched after repeated autonomous exposure.

The future architecture must distinguish:

```text
DISCOVERY POOL
VALIDATION POOL / VALIDATION BUDGET
PROSPECTIVE / FUTURE EVIDENCE
```

Exposure to validation evidence is a consumed scientific resource and must be recorded in the Evidence Ledger.

## 7. Research Contract

Every autonomous research cycle must start from an immutable `RESEARCH_CONTRACT`.

Minimum fields:

```text
contract_id
problem_id
question
information_available_at_decision
hypothesis_family
discovery_population
validation_population
primary_population
primary_metric / estimand
secondary_diagnostics
allowed_capability_families
prohibited_data
search_tree_budget
multiplicity_method
stopping_rule
critic_authority
promotion_authority
evidence_exposure_policy
```

After `LOCKED`, the Research Brain may not rescue the experiment by changing threshold, subgroup, metric, horizon, population, or success criterion. A materially changed question requires a descendant Research Contract with explicit genealogy.

## 8. Full search genealogy and research budget

Multiplicity applies to the entire search tree, not only the final candidate count.

The lineage must account for:

- hypothesis families;
- feature inventions;
- thresholds;
- interactions;
- model families;
- horizons;
- subgroup/population cuts;
- alternative metrics;
- problem reformulations;
- candidate variants;
- validation exposures.

Research objective:

```text
ANSWER THIS QUESTION
WITHIN THIS SEARCH BUDGET
```

Not:

```text
FIND SOMETHING PROFITABLE
```

When the budget is exhausted, `NO_EDGE_FOUND` is a legitimate closure.

## 9. Critic authority

The Critic is adversarial and bounded.

The Critic may:

- attack assumptions;
- detect leakage;
- detect multiplicity or provenance violations;
- question sample support and concentration;
- invalidate a candidate;
- reduce/limit a claim to what evidence supports.

The Critic may **not**:

- change a failed candidate's threshold;
- select a rescue subgroup;
- replace the primary metric;
- redefine success after seeing results;
- create a path for the same candidate to self-rescue.

A Critic-discovered alternative becomes a new research question/descendant, not a repair of the failed candidate.

## 10. Governor authority

The Governor should be deterministic/mechanical wherever possible.

Examples:

```text
if leakage_detected: INVALID
if research_contract_violated: INVALID
if search_budget_violated: INVALID
if validation_exposure_invalid: INVALID
if primary_gate_failed: REJECT
if safety_regression: REJECT
if frozen_shadow_violated: INVALID
```

An LLM may explain the decision. It should not be the sole authority that decides a candidate is "good enough" for promotion.

Promotion evaluates **incremental decision value versus the current champion**, cost-adjusted and paired where credible, plus stability/tail/support/OOD/execution feasibility. A challenger must prove that replacing A with B is better; it is not enough that B made money in isolation.

## 11. Frozen shadow lifecycle

Shadow is valuable but is not automatically independent validation.

Candidate lifecycle:

```text
candidate frozen
-> SHADOW START
-> no adaptation of that candidate from its own shadow outcomes
-> SHADOW CLOSE
-> adjudication
```

If shadow evidence motivates a change, the change creates a new descendant candidate and new evidence exposure.

## 12. Information-time as a first-class primitive

Every observable should ultimately carry as-of provenance such as:

```text
event_time
source_time
received_time
processed_time
decision_available_time
```

This applies not only to news but also ticks, candle closes, higher-timeframe state, external feeds, revisions, derived features, and model outputs.

Research must be able to prove what information was actually available at the decision timestamp.

## 13. Evolution hierarchy

### Level 0 — Knowledge evolution

A discovery may become scientific knowledge without changing active policy.

### Level 1 — Policy evolution

New decision composition from existing observables/operators; no core source change required.

### Level 2 — Model evolution

New model artifacts/weights/calibration/feature subsets; core executor may remain unchanged.

### Level 3 — Capability evolution

When current observability is demonstrably insufficient, AHFMES may propose new sensors, representations, timeframes, data sources, or code capabilities.

Capability-gap status is itself a claim that must be supported. Failure to solve a problem does not automatically justify more features/data.

Possible problem states include:

```text
UNRESOLVED
CURRENTLY_NON_PREDICTABLE
INSUFFICIENT_OBSERVABILITY
INSUFFICIENT_SAMPLE
NO_STABLE_EDGE
```

## 14. Code evolution model

Direct in-place self-modification of the active champion is prohibited.

Preferred model:

```text
ACTIVE CHAMPION = immutable

Research
-> capability proposal
-> CODE CANDIDATE
-> isolated workspace / sandbox
-> compile/static checks
-> unit tests
-> regression
-> historical scientific replay
-> Critic
-> frozen shadow
-> Governor
-> PROMOTE or REJECT
```

Old champion remains available for rollback.

Every policy/model/code candidate should have genealogy including parent, reason for mutation, problem addressed, research contract, evidence, tests, validation/shadow status, and promotion disposition.

## 15. Experience and memory direction

Future memory should separate at least:

- Market Memory;
- Trade Memory;
- Decision Memory;
- Scientific Memory;
- Problem Memory;
- Regret / Decision-Value Memory;
- Rejected Hypothesis / Graveyard Memory;
- Evidence Ledger.

Counterfactual/regret observations should carry a quality class; not all "what if" outcomes are ground truth.

## 16. Seed problem P001

The first canonical seed problem for the future Autonomous Research Engine is:

```text
PROBLEM_ID = P001
NAME       = PROFIT GIVEBACK
```

Known evidence:

```text
Hypothesis:
After an executable +$1 favorable excursion, protect around gross break-even.

Result:
PPR_W1_G1_REJECT
```

Known lesson:

The simple binary state "ever reached +1" plus "now returned around 0" did not improve executable economics robustly enough under the frozen W1 experiment.

Open question:

```text
Does richer information available BEFORE the exit decision
contain stable incremental decision value for:
EXIT versus CONTINUE?
```

Answer:

```text
UNKNOWN
```

Do not manually fill the answer with a G1.1/G2/threshold/indicator rescue. P001 is intentionally preserved as the first real test case for the future Research Engine.

## 17. Phased direction

```text
ARE-0 — Constitution
DNA, Scientific Constitution, Capital Safety Kernel,
epistemic states, evidence-consumption rules.

ARE-1 — Scientific Registries
Problem Registry, Evidence Ledger, Hypothesis Registry,
Research Contract Registry, Experiment Registry, Graveyard,
Capability Registry, candidate genealogy.

ARE-2 — Experience Intelligence
Richer Experience Store, Decision Memory, Regret Memory,
counterfactual quality, anomaly/problem detection.

ARE-3 — Autonomous Science
Research prioritization, bounded search, Critic,
hypothesis generation, capability-gap assessment.

ARE-4 — Evolution
Policy/model challengers, capability/code candidates,
frozen shadow lifecycle, deterministic promotion/rollback.
```

Do not reverse this order. Autonomous strategy/code generation before Constitution and registries is out of sequence.

## 18. Current authority boundary

This document records architecture direction only.

```text
ARE V0 IMPLEMENTATION     = NOT YET AUTHORIZED
NEW STRATEGY RESEARCH     = NOT AUTHORIZED BY THIS DOCUMENT
G1 RERUN / RETUNE         = PROHIBITED
G2 RESCUE                 = NOT AUTHORIZED
W2/W3                     = CLOSED
TRAINING/OOS              = CLOSED
PRODUCTION                = CLOSED
MERGE PR #20              = PROHIBITED WITHOUT SEPARATE AUTHORITY
AHFMES-NEW MODIFICATION   = PROHIBITED WITHOUT SEPARATE AUTHORITY
```

The next sensible gate is **formal ARE V0 architecture/contract design and audit**, not autonomous implementation.