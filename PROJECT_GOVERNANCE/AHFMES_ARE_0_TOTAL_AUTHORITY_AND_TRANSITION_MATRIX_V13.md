# AHFMES ARE-0 — Canonical Authority & Transition Matrix V13

Status: **SOLE CURRENT MACHINE SOURCE / R9-01 EXTERNAL SOURCE FINALITY + CANONICAL CUT-VECTOR COMMIT CLOSURE / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Composition / narrowing

Immutable machine base:

```text
BASE_MATRIX_V12_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V12.md
BASE_MATRIX_V12_GIT_BLOB_SHA = 6958fb579c6e67190e13362306e63cb1b67dd3dc
```

All V12->V1 semantics remain except external/non-CAS source currentness through SystemGenesis, canonical genesis cutoff and multi-source commit-frontier semantics are narrowed below.

```text
V13 R9-01 > EXACT V12 > EXACT V11 > ... > EXACT V1
```

R9-02/R9-04/R9-05/R9-06/R9-07 remain unchanged.

## 1. Finding closed — external source head TOCTOU

Historical impact finding:

```text
IA17-C01 = EXTERNAL_SOURCE_HEAD_TOCTOU_AT_SYSTEMGENESIS
ROOT = R9-01
NEW R9 ROOT = NO
```

A read/check of external non-CAS source head `H` followed by local SystemGenesis commit is not proof that the source remained unchanged between the check and commit. Retry/double-read is not an atomicity theorem.

Current V13 therefore never treats mere last-observed head equality, wall-clock freshness or repeated reads as external commit fencing.

## 2. Frozen source finality semantics

`PREGENESIS_COVERAGE_SOURCE_CONTRACT_ROOT` must additionally define for every relied source exact:

```text
source ordering/version semantics
whether source is LOCAL_CAS or EXTERNAL_FINALIZABLE or EXTERNAL_NONFINALIZABLE
finality/watermark rule
retroactive correction/reorg semantics
predecessor/causal closure rule
eligible-event relation to GENESIS_CUTOFF_RULE_ROOT
proof-verification rule for source-issued finality
control-equivalence / forgeability boundary of finality proof
```

These rules are static authority semantics and cannot change through reconciliation.

A source cannot be classified `EXTERNAL_FINALIZABLE` unless an independently verifiable proof can positively establish that all events/facts eligible at or before a claimed cut are immutable/final under the frozen source contract. Mere timestamp, HTTP freshness, latest-head observation or auditor assertion is insufficient.

## 3. Per-source canonical cut token

For each relied source `i`, derive exact:

```text
PREGENESIS_SOURCE_CUT_TOKEN[i] = hash(
  source identity,
  source-contract identity,
  exact cut ordinal/version/watermark,
  exact included-prefix/event-set root through cut,
  exact finality-proof root or LOCAL_CAS,
  exact retroactive-correction disposition,
  exact predecessor/causal-closure proof,
  canonical information frontier
)
```

Admissibility:

### 3.1 LOCAL_CAS

The cut token names the exact locally authoritative head and SystemGenesis must CAS-compare that exact head in the same atomic local transaction that commits genesis.

### 3.2 EXTERNAL_FINALIZABLE

The cut token must carry a positive independently verifiable finality proof under the frozen contract proving:

```text
no event/fact eligible at or before the cut can be added, removed, reordered or rewritten after proof finalization
all required predecessor/causal facts for the cut are closed
any correction/reorg channel that could alter <= cut is itself closed/final or positively absent
```

A later source head containing only events strictly after the finalized cut does not by itself stale the cut.

### 3.3 EXTERNAL_NONFINALIZABLE

If no positive immutable cut/finality theorem exists, clean COMPLETE coverage cannot rely on a snapshot as if atomic. The source remains `SOURCE_UNKNOWN_CONSERVATIVE` for affected obligations, or SystemGenesis is denied where conservative UNKNOWN cannot satisfy inherited Safety/authority requirements.

## 4. Canonical multi-source cut vector

Define:

```text
PREGENESIS_SOURCE_CUT_VECTOR_ROOT = hash(
  PREGENESIS_COVERAGE_SOURCE_CONTRACT_ROOT,
  GENESIS_CUTOFF_RULE_ROOT,
  exact ordered set of PREGENESIS_SOURCE_CUT_TOKEN[i],
  exact cross-source predecessor/causal-closure proof,
  exact unresolved nonfinalizable-source root,
  canonical information frontier
)
```

The vector is admissible only when every source component is either:

```text
LOCAL_CAS with atomic commit compare
EXTERNAL_FINALIZABLE with positive finality proof
or explicitly UNKNOWN_CONSERVATIVE with inherited no-clean-privilege consequences
```

A vector with a source cut that depends on a predecessor/fact outside another source's included cut is not closed and cannot be COMPLETE.

## 5. Performance-blind canonical cut selection

Caller/auditor/Genesis may not select an older convenient finalized cut.

The frozen `GENESIS_CUTOFF_RULE_ROOT` must deterministically identify the **first canonical all-source cut vector** at which all required source classes are simultaneously eligible for coverage under their frozen finality/CAS rules.

Define:

```text
FIRST_CANONICAL_PREGENESIS_SOURCE_CUT_VECTOR_ROOT
```

Once the semantic opportunity is formed for a given journal revision/knowledge state, later scheduler delay, wall-clock time, retry, source-head advance strictly after finalized cuts, performance/PnL observation or process restart cannot remint an alternate cut for the same opportunity.

If a required <=cut correction/reorg or source-contract-relevant fact invalidates the vector, the opportunity becomes non-current and reconciliation/fresh coverage is required.

## 6. Observation frontier / completeness narrowing

V12 `PREGENESIS_SOURCE_OBSERVATION_FRONTIER_ROOT` and `PREGENESIS_SOURCE_COMPLETENESS_ROOT` additionally bind exact:

```text
PREGENESIS_SOURCE_CUT_VECTOR_ROOT
FIRST_CANONICAL_PREGENESIS_SOURCE_CUT_VECTOR_ROOT
all per-source finality proofs / LOCAL_CAS heads
cross-source causal-closure proof
unresolved nonfinalizable-source root
```

For external finalized sources, knowledge obligations are derived from the exact finalized included prefix through the canonical cut, not from a mutable notion of `latest` at local commit time.

Material events strictly after the canonical finalized cut belong to later governed evolution and do not stale SystemGenesis merely because their source head advanced before the local commit. Events/corrections whose semantic order is <= cut do stale/deny.

## 7. Coverage opportunity / attestation narrowing

V11/V12 stable coverage opportunity is narrowed so its exact payload transitively binds:

```text
FIRST_CANONICAL_PREGENESIS_SOURCE_CUT_VECTOR_ROOT
PREGENESIS_SOURCE_CUT_VECTOR_ROOT
```

`PreGenesisKnowledgeCoverageAttestation` additionally binds both roots and every finality/causal proof identity represented by the vector.

Same journal revision/knowledge state/canonical vector cannot create a second opportunity because a source published later >cut events.

Different vector is admissible only when the prior opportunity became non-current due to a material <=cut invalidation or revision/knowledge-root advance under inherited rules; timing choice alone cannot select it.

## 8. SystemGenesis atomic commit theorem

SystemGenesis terminal transaction requires all inherited V12 predicates plus:

```text
FIRST_CANONICAL_PREGENESIS_SOURCE_CUT_VECTOR_ROOT exact/current
PREGENESIS_SOURCE_CUT_VECTOR_ROOT exact/current
all LOCAL_CAS source heads compared in the same local atomic transaction
all EXTERNAL_FINALIZABLE finality proofs verify independently and remain valid for <=cut semantics
all cross-source predecessor/causal closure proofs PASS
all EXTERNAL_NONFINALIZABLE affected obligations carry conservative UNKNOWN consequences or deny
no known <=cut correction/reorg/gap is outstanding
```

For an external finalized source, local transaction atomicity does not depend on the mutable later source head; it depends on immutable finality of the exact cut prefix.

Forbidden pseudo-fence:

```text
read H
verify H
external source changes
commit local genesis assuming H stayed latest
```

without an admissible finalized cut theorem.

## 9. Crash / retry / race semantics

```text
crash before local atomic genesis commit -> journal remains IMPORT_RECORDED[r]; slot remains BOUND_TO_JOURNAL
local CAS source changes -> atomic compare fails; no partial genesis
external <=cut correction invalidates finality proof -> current coverage denied; reconcile/re-attest
external >cut event after finality -> same finalized cut remains valid; no timing remint
retry with same revision/knowledge/cut -> idempotent same opportunity/payload
retry proposing older/different convenient cut -> denied
```

No partial SystemGenesis state is legal.

## 10. Static firewall

This Matrix grants no ARE-0 closure, implementation, P001 substantive research, production, live/paper trading or PR-merge authority.
