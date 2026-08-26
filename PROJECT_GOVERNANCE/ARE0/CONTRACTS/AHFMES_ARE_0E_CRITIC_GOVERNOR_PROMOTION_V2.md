# AHFMES ARE-0E — Critic, Governor, Comparative Promotion, Shadow, Champion Drift, and Rollback V2

Status: **SECOND-PASS CORRECTED FORMAL DESIGN / INTERNAL RED-TEAM PASS / EXTERNAL AUDIT REQUIRED / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

This is the normative ARE-0E draft for external review.

## 1. Core question

Promotion answers:

> Does this exact challenger have sufficient bounded evidence to replace the exact current champion in this exact deployment context under frozen economics, proof gates, and Capital Safety constraints?

It does not answer merely whether challenger P&L is positive.

## 2. Role chain

```text
Research -> Validation -> Critic -> Governor -> Promotion Gate -> Champion Registry -> Capital Safety Activation
```

Each arrow is a separate authority boundary under ARE-0B.

## 3. Critic contract

Inputs are frozen/content-addressed.

Allowed outputs:

```text
ACCEPT_BOUNDED_CLAIM
LIMIT_CLAIM
REJECT_SUPPORT
INVALIDATE_INTEGRITY
INSUFFICIENT_SUPPORT
UNRESOLVED_RISK
```

Critic cannot:

```text
retune
change candidate
change population
change metric
change horizon
open rescue subgroup
reclassify evidence relation
mint Governor/Promotion authority
```

Critic observation itself is logged as evidence exposure if it can motivate later research.

## 4. Governor contract

Governor evaluates one frozen Proof Bundle against one frozen PromotionGateSpec.

Governor cannot edit either.

Disposition:

```text
INVALID
REJECT
NO_PROMOTION
PROMOTION_ELIGIBLE
ROLLBACK_REQUIRED
```

Semantics:

```text
INVALID       = integrity/authority/provenance failed; no scientific verdict
REJECT        = valid proof contradicts required scientific/economic gate
NO_PROMOTION  = bounded knowledge may remain valid but capital replacement not justified
PROMOTION_ELIGIBLE = all required gates satisfied; still not active capital
```

## 5. Historical disposition is episode-specific

A candidate may participate in multiple Research Episodes over time if exact content is unchanged.

Example:

```text
Episode E1: insufficient support -> NO_PROMOTION
later genuinely new prospective evidence exists
Episode E2: same exact candidate root may be evaluated under new locked contract
```

E2 does not erase E1.

If candidate content changes, descendant identity is mandatory.

A `REJECT` may also be revisited only through a new Research Episode with materially new legitimate evidence/authority; the original rejection remains immutable and cannot be described as “reversed” without the new bounded context.

## 6. PromotionGateSpec timing

Exact PromotionGateSpec must be locked:

```text
before verdict-bearing validation/shadow evidence is disclosed for the candidate episode
```

Gate design may use discovery evidence, but those choices are part of Search Genealogy/Budget.

Post-validation threshold/gate changes create descendant research and cannot rescue the current episode.

## 7. Proof Bundle V2

Binds:

```text
challenger exact root
comparison champion exact root
deployment context root
Research Episode/Contract root
search/program budget proof
Evidence Ledger proof
validation proof
prospective/shadow class proof
Critic disposition
incremental economics
uncertainty
stability/support/concentration
tail risk
OOD behavior
execution feasibility/cost
Capital Safety
PromotionGateSpec
constitution/governance roots
```

## 8. Comparison champion is frozen scientific context

At comparison start:

```text
comparison_champion_root = Champion A
```

If Champion Registry later changes A -> B while challenger C is still under proof:

```text
C vs A proof may remain valid scientific evidence
BUT
C cannot use that proof alone to replace B
```

Promotion requires exact current champion binding.

Options:

```text
new comparative episode C vs B
or
precommitted compatibility/bridge proof if formal architecture later supports it
```

Default: new comparison required.

## 9. Multiple challengers concurrently

C1/C2/C3 may be evaluated against Champion A under one precommitted validation family.

If C1 is promoted first:

```text
C2/C3 A-PROMOTE authorities against A become stale
```

Their scientific results vs A remain evidence; promotion against new Champion C1 requires fresh comparative authority/evidence as specified by contract.

This prevents tournament races from using obsolete baselines.

## 10. Incremental estimand

Primary promotion claim is champion-relative:

```text
DeltaDecisionValue = Challenger - ComparisonChampion
```

under exact economic/opportunity semantics.

## 11. Opportunity-set changes

If challenger changes when it trades:

### Common-opportunity layer

Paired comparison on overlap where credible.

### Whole-policy layer

Frozen eligible stream including:

```text
unique challenger trades
unique champion trades
abstentions
missed opportunities
costs/exposure
```

PromotionGateSpec predeclares which is primary and how both constrain promotion.

Cannot choose favorable layer after outcomes.

## 12. Frequency

Opportunity density is secondary preference only after primary evidence/economic/safety gates.

High trade count cannot rescue weak/negative/unproven edge.

## 13. Execution economics

Same convention for champion/challenger.

Where material:

```text
spread
commission
slippage
latency
swap
fills/partial fills
broker constraints
```

Unknown material cost -> NO_PROMOTION/INSUFFICIENT_EXECUTION_EVIDENCE unless frozen conservative sensitivity gate covers it.

## 14. Uncertainty and statistical proof

PromotionGateSpec specifies pre-outcome method:

```text
confidence/credible bound
bootstrap/dependence handling
family/sequential correction
minimum effect definition
```

Research cannot switch method after failure.

## 15. Stability/support/concentration

Required dimensions may include:

```text
time blocks
sessions
regimes
volatility/hostility
prospective epochs
folds
```

Proof also reports concentration such as share of benefit from extreme few blocks.

Insufficient support -> NO_PROMOTION, not optimistic promotion.

## 16. Tail risk

Mean improvement cannot override Capital Safety/tail constraints.

Gate may include precommitted:

```text
worst-block loss
drawdown distribution
loss clustering
exposure concentration
gap sensitivity
catastrophic failure modes
```

## 17. OOD / uncertainty behavior

Candidate must define behavior outside validated support:

```text
ABSTAIN
DEGRADE_TO_CHAMPION
DEGRADE_TO_SAFE_POLICY
bounded risk reduction
```

Undefined OOD behavior for material states -> NO_PROMOTION or explicit domain restriction.

## 18. Capital Safety veto

```text
Capital Safety FAIL -> no promotion/activation
```

Research cannot negotiate safety downward in the same strategy claim.

## 19. Shadow contract

Freeze before active window:

```text
candidate
comparison champion
start/end rule
permitted metrics
cost semantics
minimum support
adaptation prohibition
disclosure plan
prospective evidence class
```

During ACTIVE:

```text
same candidate cannot adapt from own outcome
```

Feedback creates descendant or future Research Episode; Evidence Ledger records exposure.

## 20. Strict prospective vs live-frozen shadow

Proof bundle records ARE-0C evidence class:

```text
PROSPECTIVE_STRICT_BLIND
PROSPECTIVE_LIVE_FROZEN
SHADOW_LIVE
```

PromotionGateSpec decides which class/support is required.

Architecture may not label LIVE_FROZEN evidence as strictly blind merely because it occurred in the future.

## 21. Governor deterministic gate order

```text
G00 Governance/authority roots
G01 exact candidate/Champion identity
G02 Contract/Research Episode integrity
G03 Evidence Ledger eligibility/freshness
G04 Program/Search budget + multiplicity
G05 validation integrity
G06 primary incremental economics
G07 uncertainty/statistical gate
G08 stability/support/concentration
G09 tail risk
G10 OOD/domain behavior
G11 execution costs/feasibility
G12 prospective/shadow requirements
G13 Critic bounded disposition
G14 Capital Safety
G15 current Champion Registry freshness
```

Mapping:

```text
integrity/authority defect -> INVALID
primary scientific/economic fail -> REJECT
support/operational insufficiency -> NO_PROMOTION
all required gates -> PROMOTION_ELIGIBLE
```

## 22. Governor no-rescue rule

If global result fails but one subgroup looks good:

```text
current episode remains failed/no-promotion
subgroup becomes future research lead
```

No gate/threshold/population edits inside Governor.

## 23. Promotion authority

Only after `PROMOTION_ELIGIBLE` may TD-PROMOTION issue A-PROMOTE bound to:

```text
challenger root
expected current champion root
registry generation/previous hash
deployment context
Capital Safety root
execution contract
Proof Bundle
PromotionGateSpec
rollback target
single-use nonce
```

## 24. Champion Registry transaction

Atomic compare-and-swap.

```text
if current Champion differs from comparison/promotion binding -> DENY STALE
```

Promotion does not erase prior champions/results.

## 25. Capital activation

Scientific/deployment promotion still != broker activation.

Capital Safety/Execution checks issue separate activation authority.

Emergency flat can reduce risk without scientific promotion.

## 26. Rollback contract

Before activation register:

```text
rollback target exact root
compatibility proof
state/memory migration rule
telemetry continuity
trigger classes
registry generation binding
```

Rollback is a new registry event, not history rewrite.

## 27. State/schema compatibility on rollback

If promoted candidate changes internal state/model schema, rollback proof must show old champion can resume safely.

Possible approaches later:

```text
champion-specific isolated state
versioned migration adapter
cold restart from safe canonical state
```

Exact implementation deferred; promotion cannot assume compatibility without proof.

## 28. Post-promotion monitoring

Monitor drift/runtime anomalies, but:

```text
monitoring cannot mutate champion in place
```

Material change -> new Research Episode/descendant.

Emergency safety stop is allowed without research cycle because it only reduces risk.

## 29. Knowledge-only result

```text
VALIDATED_BOUNDED
-> Scientific Memory
-> NO_PROMOTION
```

Not every scientific success needs shadow/capital.

## 30. Capability/code candidate extra gates

Additional proof:

```text
source content closure
static/security checks
unit tests
regression
replay/determinism compatibility where required
latency/resource limits
sandbox isolation
rollback compatibility
```

Active champion is never edited in place.

## 31. Deployment context binding

Context can include:

```text
symbol/market
broker/account class
risk/lot envelope
runtime version
data feed contract
execution venue
Capital Safety version
execution contract
```

Proof cannot be replayed across context without compatibility/revalidation.

## 32. Reporting vocabulary

Never collapse:

```text
PROFITABLE
BETTER_THAN_CHAMPION
VALIDATED_BOUNDED
NO_PROMOTION
PROMOTION_ELIGIBLE
PROMOTED
CAPITAL_ACTIVE
```

## 33. Reason codes

```text
INVALID_AUTHORITY
INVALID_IDENTITY
INVALID_CONTRACT
INVALID_EVIDENCE
INVALID_SEARCH_ACCOUNTING
REJECT_INCREMENTAL_VALUE
REJECT_UNCERTAINTY
NO_PROMOTION_SUPPORT
NO_PROMOTION_CONCENTRATION
REJECT_TAIL
NO_PROMOTION_OOD
NO_PROMOTION_EXECUTION
REJECT_SHADOW
REJECT_CRITIC
REJECT_CAPITAL_SAFETY
STALE_COMPARISON_CHAMPION
STALE_PROMOTION
PROMOTION_ELIGIBLE
```

## 34. Second-pass attacks

Internal Red-Team attacked:

```text
1 standalone P&L beats no champion
2 overlap-only cherry-picking
3 portfolio-only hides harmful overlap
4 mean EV hides tail damage
5 tiny-period concentration
6 unknown cost = zero
7 shadow mutation same ID
8 Critic rescue
9 Governor metric rescue
10 Champion changes during candidate proof
11 multiple challengers race vs old Champion
12 promotion replay other deployment
13 frequency rescues weak edge
14 knowledge-only forced to capital
15 safety weakened for EV
16 NO_PROMOTION treated as erasing prior episode
17 same candidate retested on consumed evidence as if fresh
18 rollback state incompatibility
```

V2 explicitly addresses all eighteen.

## 35. External audit obligations

Auditor should attempt to obtain PROMOTION_ELIGIBLE/PROMOTE with:

```text
stale champion
standalone profit only
post-hoc comparison population
insufficient support
unknown costs
undefined OOD
Critic rescue
shadow mutation
safety regression
context replay
consumed evidence retest
```

Any successful path is blocking.

## 36. Current disposition

```text
ARE-0E V2
= SECOND-PASS CORRECTED FORMAL DESIGN
= INTERNAL RED-TEAM PASS
= READY FOR EXTERNAL ADVERSARIAL AUDIT
= NOT CLOSED
= NO IMPLEMENTATION AUTHORITY
```
