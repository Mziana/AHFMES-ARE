# AHFMES ARE-0 — Authority-Sensitive Object Inventory V13

Status: **CURRENT CLOSED-WORLD COMPANION / R9-01 EXTERNAL SOURCE FINALITY + CUT-VECTOR TOTALITY / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Composition

Current machine source:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V13.md
```

Immutable base:

```text
BASE_INVENTORY_V12_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V12.md
BASE_INVENTORY_V12_GIT_BLOB_SHA = d6e6564fa113486a35d96aeef8bb48a4d29c2633
```

All V12->V2 identities remain except external source finality/cut-vector/currentness identities are narrowed below.

## 1. Frozen source-finality classification

For every source in `PREGENESIS_COVERAGE_SOURCE_CONTRACT_ROOT`, exact static classification is one of:

```text
LOCAL_CAS
EXTERNAL_FINALIZABLE
EXTERNAL_NONFINALIZABLE
```

Static source contract also fixes:

```text
ordering/version rule
finality/watermark rule
correction/reorg semantics
predecessor/causal closure rule
eligible-event relation to GENESIS_CUTOFF_RULE_ROOT
finality-proof verifier and control-equivalence/forgeability boundary
```

No reconciliation writer may change these semantics.

## 2. Derived per-source identities

For each relied source `i`:

```text
PREGENESIS_SOURCE_CUT_TOKEN[i]
```

is derived/non-writable and binds exact source, contract, cut ordinal/version/watermark, included-prefix root, finality proof or LOCAL_CAS identity, correction disposition, causal closure and information frontier.

For `EXTERNAL_FINALIZABLE`, the token is valid only with positive independently verifiable proof that <=cut eligible facts cannot later be added/removed/reordered/rewritten and all correction/reorg paths affecting <=cut are finalized/closed.

For `EXTERNAL_NONFINALIZABLE`, no read/freshness/head equality can be promoted into an atomic finalized cut.

## 3. Multi-source vector identities

Derived/non-writable:

```text
PREGENESIS_SOURCE_CUT_VECTOR_ROOT
FIRST_CANONICAL_PREGENESIS_SOURCE_CUT_VECTOR_ROOT
PREGENESIS_CROSS_SOURCE_CAUSAL_CLOSURE_ROOT
PREGENESIS_NONFINALIZABLE_SOURCE_UNCERTAINTY_ROOT
```

The vector contains every relied source exactly once under the frozen source contract.

Cross-source closure fails when a cut contains a dependent fact without every required predecessor/fact within the corresponding other-source cut or conservative UNKNOWN accounting.

## 4. Observation/completeness extension

Current derived roots additionally bind cut-vector identities:

```text
PREGENESIS_SOURCE_OBSERVATION_FRONTIER_ROOT
PREGENESIS_SOURCE_COMPLETENESS_ROOT
CURRENT_PREGENESIS_KNOWLEDGE_OBLIGATION_SET_ROOT
```

For external finalized sources, governed coverage through genesis uses the exact immutable finalized prefix selected by `FIRST_CANONICAL_PREGENESIS_SOURCE_CUT_VECTOR_ROOT`.

A later strictly-post-cut source event does not mutate that finalized prefix. A correction/reorg/fact semantically ordered <=cut invalidates currentness.

## 5. PreGenesisKnowledgeCoverageAttestation V13 payload

Inherited one-slot attestation additionally binds exact:

```text
FIRST_CANONICAL_PREGENESIS_SOURCE_CUT_VECTOR_ROOT
PREGENESIS_SOURCE_CUT_VECTOR_ROOT
PREGENESIS_CROSS_SOURCE_CAUSAL_CLOSURE_ROOT
all LOCAL_CAS source-head identities
all EXTERNAL_FINALIZABLE finality proof roots
PREGENESIS_NONFINALIZABLE_SOURCE_UNCERTAINTY_ROOT
```

Writer remains:

```text
A-PREGENESIS-COVERAGE-AUDIT
-> Bootstrap-Coverage-Audit only
```

No finality proof may be authored by a common-control principal that can forge the relied source prefix unless the frozen source contract positively proves independent self-verification sufficient to defeat such forgery/suppression.

## 6. SystemGenesis source commit surface

Exact terminal commit treatment:

```text
LOCAL_CAS
  -> exact head CAS in same local atomic SystemGenesis transaction

EXTERNAL_FINALIZABLE
  -> immutable finalized cut proof; later >cut head movement irrelevant to current cut

EXTERNAL_NONFINALIZABLE
  -> conservative UNKNOWN consequences or denial where UNKNOWN cannot satisfy inherited Safety/authority predicate
```

No object/writer exists for a caller-selected `latest-head accepted` shortcut.

## 7. Currentness / invalidation

Current coverage/genesis source state is invalidated by any:

```text
LOCAL_CAS head mismatch at atomic commit
known <=cut external correction/reorg
invalid/expired/forged finality proof under frozen verifier
cross-source causal predecessor gap
source-contract mismatch
nonfinalizable source represented as COMPLETE
caller-selected noncanonical cut vector
```

Not an invalidator by itself:

```text
strictly >cut event on an EXTERNAL_FINALIZABLE source after the canonical cut is finalized
```

provided it cannot alter/reinterpret any <=cut fact or predecessor closure.

## 8. Closed-world invariants

```text
LAST READ != EXTERNAL ATOMIC FENCE
DOUBLE READ != EXTERNAL ATOMIC FENCE
EXTERNAL COMPLETE REQUIRES POSITIVE FINALIZED CUT OR CONSERVATIVE UNKNOWN
LOCAL CAS COMPARE OCCURS IN SAME GENESIS TRANSACTION
CANONICAL CUT IS PERFORMANCE-BLIND / NOT CALLER-SELECTED
CROSS-SOURCE CUT MUST BE CAUSALLY CLOSED
POST-CUT ADVANCE DOES NOT REMINT SAME OPPORTUNITY
<=CUT CORRECTION INVALIDATES CURRENT COVERAGE
SYSTEM_GENESIS_COMMITTED REMAINS TERMINAL
```

## 9. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
