# AHFMES ARE-0 — Canonical Authority & Transition Matrix V26

Status: **SOLE CURRENT MACHINE SOURCE / R9-05 ROLLBACK CAUSE-AVAILABILITY NONINTERFERENCE / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Composition / precedence

```text
BASE_MATRIX_V25_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V25.md
BASE_MATRIX_V25_GIT_BLOB_SHA = 0fbd3f24264ce51fa110f7562e01ae99c59b2206
V26 R9-05 > EXACT V25 > EXACT V24 > ... > EXACT V1
```

All V25 and inherited semantics remain in force except R9-05 rollback cause-observation / strategy-selection availability is narrowed below. No new authority class, writable registry, lifecycle state machine, Safety right, capital right, broker right, or implementation right is created.

## 1. External blocker closed by this successor

```text
EXT2-081-01
= OUTCOME_CONDITIONED_ROLLBACK_CAUSE_DISCOVERY_CAN_SELECT_STRATEGY
ROOT = R9-05
NEW ROOT = NO
```

The inherited R9-05 theorem correctly binds rollback cause class, exact displaced incumbent fallback, current proof/selection reliance, first canonical cause-information frontier, upstream cause lineage, cause producer/attester identity and SoD, and it prohibits timing a discretionary upstream mutation from beneficiary outcome in order to manufacture a rollback cause.

That is insufficient when a genuine clean cause already exists independently but beneficiary outcome controls whether it is queried, discovered, admitted, finalized, attested, or otherwise made legally available for `A-ROLLBACK`.

For rollback strategy selection, **control dependence is information flow even when cause bytes are clean and immutable**.

## 2. Existing `ROLLBACK_POLICY_ROOT` now binds authority-conferring cause observation

For every rollback target transition `T` and allowed cause class `C`, the existing frozen pre-outcome `ROLLBACK_POLICY_ROOT[T]` MUST semantically bind a derived projection:

```text
ROLLBACK_CAUSE_OBSERVATION_POLICY_ROOT[T,C]
```

This projection is not a new registry or independently writable policy. It is a deterministic semantic projection of the already-required frozen `ROLLBACK_POLICY_ROOT[T]` and MUST bind at least:

```text
exact allowed cause class C
CAUSE_OBSERVATION_SOURCE_UNIVERSE[T,C]
source/producer identity or governed source-class rules
observation mode: frozen event-driven push, probe, query, subscription or cadence rule
query/discovery opportunity identity and canonical ordering rule
monitor-scope rule and any allowed scope changes
admission / suppression / exclusion rule
currentness / finality / completeness rule
attestation trigger and attestation-availability rule
missing / late / unavailable / access-denied / error / retry / UNKNOWN semantics
authority-relevant timeout, freshness and expiry semantics
exact rule for when an observed cause is eligible to enter the R9-05 rollback path
```

`CAUSE_OBSERVATION_SOURCE_UNIVERSE[T,C]` means the governed source/opportunity universe whose observations are permitted to confer **rollback strategy-selection privilege**. It is not a claim that the architecture knows every possible fact in the world.

A genuine defect discovered outside that governed universe may still be recorded and may drive separately authorized Safety/integrity containment. It cannot confer `A-ROLLBACK` strategy-selection privilege merely because it is genuine.

A policy may use immediate frozen event-driven push/notification semantics; periodic polling is not required. The closure requirement therefore does not authorize or require delaying genuine Safety response.

## 3. Rollback outcome / consequence channel closure

For each `T`, define derived/non-writable:

```text
ROLLBACK_BENEFICIARY_OUTCOME_SOURCE_SET[T]
ROLLBACK_BENEFICIARY_OUTCOME_DESCENDANT_SET[T]
```

The source set includes any Champion/fallback-selection consequence information capable of acting as a selector, including:

```text
Champion/fallback PnL or return
profitability / loss / drawdown / attractiveness
trade or episode result
market-path result when used as Champion-selection consequence
regime information when used to choose between current Champion and fallback
presence / absence of an outcome
publication / result availability
observation / access status
outcome-dependent metadata
outcome-dependent error / exception state
outcome-dependent latency or authority-relevant timing
human / operator / LLM knowledge of any such consequence
any deterministic or stochastic proxy carrying equivalent consequence information
```

Descendant closure follows both content derivation and every authority-relevant control/availability influence edge defined below. Renaming, hashing, summarizing, thresholding, embedding or otherwise transforming outcome information does not remove ancestry.

## 4. Full rollback cause-selection influence graph

For each `T,C`, define derived/non-writable:

```text
ROLLBACK_CAUSE_SELECTION_INFLUENCE_GRAPH[T,C]
ROLLBACK_CAUSE_SELECTION_INFLUENCE_CLOSURE_COMPLETE[T,C]
```

The graph MUST contain every content and control/availability influence capable of changing whether, when, or under what legal state an otherwise genuine cause can make `A-ROLLBACK` strategy selection available.

For nodes/events `a -> b`, an influence edge exists whenever, holding all other declared genuine non-performance cause facts and exogenous governance/integrity facts fixed, an admissible variation in the value, presence, absence, observation, availability, control decision or authority-relevant timing of `a` can change any of the following for `b`:

```text
observation-source or monitor-scope selection
subscription / push / probe / query activation
discovery opportunity or retry activation
source/method choice
admission / suppression / exclusion
currentness / finality / completeness
missing/late/error interpretation
attestation request / availability / completion
cause-event canonicalization or eligibility
whether a freshness/expiry/order boundary is crossed
whether the cause is legally available to R9-05
whether `A-ROLLBACK` fallback strategy selection is legally available
```

A control edge exists even when no outcome bytes are copied into the cause record. For example:

```text
if Champion looks bad -> query immutable clean integrity archive R
else                  -> do not query R
```

contains an outcome -> query-control edge.

The categories above are not exhaustive. Any undeclared scheduler branch, callback, prompt/context, model latent, operator decision, access-control result, cache behavior, API absence, retry policy, exception path or external lookup that can materially alter rollback-selection availability MUST be represented or closure is FALSE.

Physical timing jitter that cannot alter canonical opportunity order, currentness, finality, freshness, expiry, attestation, cause availability or rollback legality is non-semantic. Timing that can cross one of those boundaries is an influence edge.

## 5. Consequence-blind rollback selection noninterference

Define derived/non-writable:

```text
ROLLBACK_CAUSE_SELECTION_NONINTERFERENCE_VALID[T,C]
ROLLBACK_CAUSE_SELECTION_NONINTERFERENCE_ROOT[T,C]
```

`ROLLBACK_CAUSE_SELECTION_NONINTERFERENCE_VALID[T,C] = TRUE` only if all of the following hold:

```text
A. ROLLBACK_CAUSE_SELECTION_INFLUENCE_CLOSURE_COMPLETE[T,C] = TRUE;
B. exact ROLLBACK_CAUSE_OBSERVATION_POLICY_ROOT[T,C] is current and was frozen
   under the inherited pre-outcome ROLLBACK_POLICY_ROOT rule;
C. no ROLLBACK_BENEFICIARY_OUTCOME_SOURCE_SET or descendant can influence
   source/monitor scope, observation activation, push/probe/query/discovery,
   retry, admission, suppression, finality, currentness or attestation in a way
   that changes rollback-selection availability;
D. holding genuine non-performance cause facts and exogenous governance/integrity
   facts fixed, varying Champion/fallback consequence sources and descendants
   leaves invariant whether each governed cause opportunity is observed, queried,
   admitted, finalized, attested and legally available to R9-05;
E. under the same counterfactual, exact legal availability of A-ROLLBACK as a
   fallback-strategy selector is invariant;
F. outcome presence/absence/access/error/latency/timing and human/LLM knowledge
   cannot act as hidden selectors;
G. any material UNKNOWN or opaque ancestry/control influence that can alter
   rollback-selection availability => FALSE.
```

The counterfactual does not require Safety actions to be invariant. It applies to the authority path that selects the displaced incumbent fallback under `A-ROLLBACK`.

## 6. Existing `ROLLBACK_CAUSE_LINEAGE_VALID` narrowed for `A-ROLLBACK`

All inherited R9-05 cause-lineage conditions remain mandatory.

In addition, for `A-ROLLBACK` fallback strategy selection:

```text
ROLLBACK_CAUSE_LINEAGE_VALID[T,C]
=> ROLLBACK_CAUSE_SELECTION_NONINTERFERENCE_VALID[T,C] = TRUE
```

and `A-ROLLBACK` MUST fail closed unless the exact current cause class / cause-event path satisfies the consequence-blind observation theorem above.

Therefore:

```text
clean genuine cause
+ valid producer/attester/executor SoD
+ valid exact displaced-incumbent fallback
+ current proof/selection reliance
```

is **not sufficient** if beneficiary outcome influenced whether the cause became available for rollback selection.

No attester, operator, LLM, scheduler or other independent principal obtains discretion to use outcome as a search/admission/attestation switch merely by being distinct from the rollback executor.

## 7. Safety / factual-cause separation

Failure of rollback-selection noninterference does not erase a genuine integrity or Safety fact.

An outcome-triggered or otherwise rollback-selection-tainted discovery MAY, under the exact separately inherited authorities and state transitions, support actions such as:

```text
record factual IntegrityDefect / incident state
increase observation / diagnosis
cancel pending risk increase
deactivate or block new risk
reduce exposure
close exposure
invoke other fail-closed Safety containment
```

where each such action independently satisfies its own current authority, SoD, currentness, settlement and Safety semantics.

It MUST NOT by itself authorize:

```text
ChampionRegistry B -> displaced incumbent A
A-ROLLBACK fallback strategy selection
```

This separation prevents rollback from becoming a performance router while preserving immediate fail-closed Safety containment.

## 8. Positive rollback liveness

Rollback remains drainable when the cause-availability path is consequence-blind.

Legal positive example:

```text
frozen ROLLBACK_POLICY_ROOT
+ frozen event-driven push source or outcome-independent governed cadence/probe
+ genuine allowed cause R observed under that policy
+ ROLLBACK_CAUSE_SELECTION_NONINTERFERENCE_VALID = TRUE
+ inherited cause provenance / first-information / SoD = PASS
+ exact displaced incumbent A remains current and eligible
+ current proof/selection/Safety/runtime/deployment predicates = PASS
+ exact inherited rollback authority = PASS
=> A-ROLLBACK may proceed
```

The existence of beneficiary outcome elsewhere in the system does not itself taint a cause path. The prohibited condition is **causal/control dependence of rollback-selection availability on that outcome**.

## 9. Rotation / currentness / replay

Any authority-semantic rollback object or VAR that binds `ROLLBACK_POLICY_ROOT` or R9-05 prerequisite roots MUST resolve the exact current V26 semantics, including the exact current `ROLLBACK_CAUSE_OBSERVATION_POLICY_ROOT` and `ROLLBACK_CAUSE_SELECTION_NONINTERFERENCE_ROOT` where applicable.

Changing the governed observation source universe, trigger/cadence/query opportunity rule, admission/suppression rule, attestation-availability rule, or another field that changes the semantic cause-observation policy is a semantic policy change. Stale acceptance/authority/currentness may not be reused across that change under inherited rules.

Unrelated monitor activity or unrelated registry/CAS churn does not by itself change the semantic observation policy and MUST NOT force semantic remint.

## 10. Fail-closed rule

For any `A-ROLLBACK` attempt, material uncertainty about whether Champion/fallback consequence information influenced cause availability is authority-relevant uncertainty:

```text
UNKNOWN / INCOMPLETE MATERIAL INFLUENCE CLOSURE
=> ROLLBACK_CAUSE_SELECTION_NONINTERFERENCE_VALID = FALSE
=> A-ROLLBACK STRATEGY SELECTION = DENIED
```

Independent Safety containment remains governed by its own inherited fail-closed semantics.

## 11. Firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR MERGE = NOT AUTHORIZED
AHFMES-NEW = CLOSED
W2/W3 = CLOSED
```
