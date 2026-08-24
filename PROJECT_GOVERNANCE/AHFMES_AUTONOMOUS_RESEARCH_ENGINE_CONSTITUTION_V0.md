# AHFMES Autonomous Research Engine V0 — Scientific Constitution and Capital Safety Boundary

Status: **CONSTITUTIONAL DESIGN DIRECTION / NOT IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

## 1. Constitutional principle

AHFMES may expand what it observes, models, and researches. It may not redefine truth or capital safety merely because a candidate appears profitable.

Central rule:

> **Freedom of thought is broad. Proof and capital authority are narrow.**

## 2. DNA definition

The current architectural DNA is:

```text
EVIDENCE-FIRST
MICRO-EXECUTION ORIENTED
ADAPTIVE
PATH / STATE AWARE
UNCERTAINTY-AWARE
COUNTERFACTUAL / DECISION-VALUE AWARE
AUDITABLE
FAIL-CLOSED
SURVIVAL-CONSTRAINED
```

`HIGH OPPORTUNITY DENSITY` is a conditional optimization preference, not a mandatory quota.

Information horizon may be broad; execution economics remain micro unless a future separately-authorized project explicitly changes that identity.

Examples that remain compatible with AHFMES:

```text
H1 volatility context -> better M1 hostility estimate -> micro execution
news timing -> no-trade / post-shock state -> micro execution
DXY context -> if proven incremental value -> micro execution
```

Example of DNA drift:

```text
H4 signal -> 36 hour hold -> large swing target
```

That would be a different economic system unless separately re-chartered.

## 3. Scientific Constitution — hard rules

### SC-01 — Discovery is not validation

Evidence used to invent/select a hypothesis cannot simultaneously serve as independent proof of that hypothesis.

### SC-02 — No self-acceptance

The process that creates a candidate cannot unilaterally promote that candidate to capital authority.

### SC-03 — Information-time provenance

A claim may use only information available as-of the decision timestamp under a documented provenance contract.

### SC-04 — Precommit the estimand

Primary population, primary estimand/metric, search family, budget, stopping rule, and validation boundary must be frozen before validation.

### SC-05 — Full multiplicity accounting

Multiplicity is attached to the entire search genealogy, including feature invention, thresholds, model families, subgroup cuts, horizons, metric alternatives, interactions, reformulations, and related validation exposures.

### SC-06 — Research budget is finite

The system may not continue searching until a PASS appears. Budget exhaustion may terminate with `NO_EDGE_FOUND`.

### SC-07 — Holdout evidence is consumable

Repeated exposure to a validation/holdout set reduces or eliminates its independence for related future claims. The Evidence Ledger must track this.

### SC-08 — Rejected evidence is immutable

A valid rejected hypothesis cannot be relabeled promising, retuned in-place, or erased. Materially changed research requires a new descendant identity.

### SC-09 — Candidate immutability during proof

Once a candidate enters validation or a frozen shadow window, its defining policy/model/code identity may not adapt using outcomes from that proof window.

### SC-10 — No rescue within the same experiment

Failure may not be rescued by replacing thresholds, populations, horizons, or primary metrics after outcomes are observed.

### SC-11 — `INVALID` differs from `REJECT`

- `REJECT`: the scientific experiment was valid, but the hypothesis failed.
- `INVALID`: integrity, contract, provenance, or proof rules were violated; no scientific conclusion may be claimed.

### SC-12 — No-result states are legitimate

The system must be allowed to conclude:

```text
NO_STABLE_EDGE
CURRENTLY_NON_PREDICTABLE
INSUFFICIENT_SAMPLE
UNRESOLVED
```

without being forced to add complexity.

### SC-13 — Capability-gap is a hypothesis

Failure of current features/models is not sufficient evidence that a new sensor or data source is required. `INSUFFICIENT_OBSERVABILITY` must itself be supported.

### SC-14 — Comparative promotion

A challenger is evaluated as a replacement for the current champion. Promotion asks whether the incremental decision value of replacing A with B is positive and robust, not whether B made money in isolation.

### SC-15 — Fail closed

When provenance, evidence identity, contract validity, or authority is uncertain, the system does not promote or trade the uncertain candidate.

## 4. Capital Safety Kernel — hard rules

The Capital Safety Kernel is not a candidate policy family.

Minimum protected domains:

```text
catastrophic loss bound
maximum exposure
position/order sanity
broker connectivity sanity
market-data sanity
clock/provenance sanity
execution limits
emergency flat
kill switch
production authority
rollback
```

### CSK-01

Research Brain cannot disable or weaken a survival bound because historical EV appears better without it.

### CSK-02

A promoted trading policy remains subordinate to the Capital Safety Kernel.

### CSK-03

The Safety Kernel may veto a trade or candidate regardless of Research Brain confidence.

### CSK-04

Emergency controls must remain externally/independently callable from the research process.

### CSK-05

A code candidate that changes safety behavior requires a separate safety/governance authority, not ordinary strategy promotion.

## 5. Role separation

### Research Brain

May:

- detect problems;
- discover patterns;
- propose hypotheses;
- generate bounded candidates;
- request capability research;
- produce explanations.

May not:

- promote itself;
- redefine success after seeing results;
- directly write to active capital policy;
- bypass Critic/Governor/Safety.

### Critic

May:

- attack claims/process;
- detect leakage/provenance/multiplicity defects;
- invalidate;
- accept only a bounded claim.

May not:

- retune;
- rescue;
- change primary estimand;
- directly promote.

### Governor

Should be deterministic/mechanical wherever possible.

Consumes frozen evidence and returns bounded dispositions.

### Operational Brain

May adapt state estimates and choose among production-eligible behavior. It does not create unvalidated production policy on the live path.

## 6. State adaptation vs policy adaptation

### State adaptation — fast / live

Allowed examples:

```text
volatility probability changes
regime probability changes
spread hostility changes
confidence changes
similarity changes
trade-health changes
```

### Policy adaptation — slow / proof-gated

Examples:

```text
new exit rule
new threshold family
new model architecture
new feature combination
new timeframe context
new data source
new code capability
```

These require the scientific lifecycle before capital use.

## 7. Information horizon rule

Do not equate information timeframe with holding timeframe.

```text
D1/H4/H1/M15 = possible context sensors
M5/M1/TICK   = possible tactical/execution sensors
```

Higher timeframe or news capability is not automatically useful or authorized. It becomes active only after incremental value is proven.

## 8. News/external-data special rule

News/event/external evidence must include, where applicable:

```text
event_scheduled_time
source_time
first_machine_available_time
received_time
parsed_time
processed_time
decision_available_time
revision_status
source_id
```

Historical revisions may not be treated as if known at original release time.

## 9. Self-code evolution rule

Allowed long-term pattern:

```text
Research -> Code Candidate -> Sandbox -> Tests -> Scientific Proof -> Frozen Shadow -> Governor -> Promote/Reject
```

Prohibited:

```text
active process edits active production source -> restart -> trade
```

The candidate-producing process and the capital-authorizing process remain separate.

## 10. Constitutional amendment principle

These V0 rules are design direction, not yet a formally closed constitution. However, once a future ARE constitution is formally frozen, changing Scientific Constitution or Capital Safety should require a higher-order governance process than ordinary strategy/capability research.

## 11. Current non-authority

This document does not authorize implementation, database/schema migration, autonomous research execution, new market/news data collection, W2/W3, Training/OOS, production modification, code generation, live shadow, or merge.