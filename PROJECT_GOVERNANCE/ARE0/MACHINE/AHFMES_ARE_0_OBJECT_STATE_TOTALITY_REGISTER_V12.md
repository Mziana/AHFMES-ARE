# AHFMES ARE-0 — Authority-Sensitive Object Inventory V12

Status: **CURRENT CLOSED-WORLD COMPANION / R9-01 PREGENESIS COVERAGE INDEPENDENCE / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Composition

Current machine source:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V12.md
```

Immutable base:

```text
BASE_INVENTORY_V11_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V11.md
BASE_INVENTORY_V11_GIT_BLOB_SHA = c6123beee7bcb323f26ff8c5e1eb55ccba6b7d6a
```

All V11->V2 identities remain except import/coverage control separation and source-contract/currentness identities are narrowed below.

## 1. Pre-system control identities

Current authorization/journal lineage binds exact:

```text
Bootstrap-Import control identity
Bootstrap-Coverage-Audit control identity
Genesis control identity
```

For discretionary relied source/capture surfaces:

```text
Genesis != Bootstrap-Import
Genesis != Bootstrap-Coverage-Audit
Bootstrap-Import != Bootstrap-Coverage-Audit
```

by common-control equivalence.

Same-control import/coverage is legal only when exact relied source is positively external/self-verifying and importer cannot forge/suppress/rewrite it.

## 2. Static source-contract identities

Immutable after authorization/import:

```text
PREGENESIS_COVERAGE_SOURCE_CONTRACT_ROOT
PREGENESIS_MATERIALITY_APPLICABILITY_ROOT
GENESIS_CUTOFF_RULE_ROOT
STATIC_GEN0_AUTHORITY_SEMANTICS_COMMITMENT_ROOT
```

`PREGENESIS_COVERAGE_SOURCE_CONTRACT_ROOT` maps every materiality class to exact source/event universe, capture boundary, canonicalization, gap/freshness rule, source/capture control root, external/self-verifying property and source->knowledge-obligation mapping.

Derived predicate:

```text
PREGENESIS_COVERAGE_SOURCE_CONTRACT_TOTALITY_VALID
```

Unknown/missing material source class denies clean COMPLETE coverage.

## 3. Source observation/completeness roots

Derived, non-writable identities:

```text
PREGENESIS_SOURCE_OBSERVATION_FRONTIER_ROOT
PREGENESIS_SOURCE_COMPLETENESS_ROOT
PREGENESIS_COVERAGE_SOD_VALID
```

The source observation frontier binds current source heads/revisions, canonicalized observed fact roots, gaps/freshness and external/self-verifying proofs.

The source completeness root binds source contract + observation frontier + required universe coverage + control/SoD + unresolved source uncertainty.

Possible source completeness dispositions:

```text
SOURCE_COMPLETE
SOURCE_UNKNOWN_CONSERVATIVE
```

Known gap/suppression cannot be `SOURCE_COMPLETE`.

## 4. Knowledge obligation fold

`CURRENT_PREGENESIS_KNOWLEDGE_OBLIGATION_SET_ROOT` is derived from:

```text
PREGENESIS_MATERIALITY_APPLICABILITY_ROOT
+
PREGENESIS_SOURCE_OBSERVATION_FRONTIER_ROOT
```

not solely from imported journal contents.

Therefore an omitted source fact can still create a semantic obligation.

## 5. PreGenesisKnowledgeCoverageAttestation V12 payload

Current object remains one immutable record per V11 coverage opportunity key.

Payload additionally binds:

```text
PREGENESIS_COVERAGE_SOURCE_CONTRACT_ROOT
PREGENESIS_SOURCE_OBSERVATION_FRONTIER_ROOT
PREGENESIS_SOURCE_COMPLETENESS_ROOT
Bootstrap-Import control identity
Bootstrap-Coverage-Audit control identity
PREGENESIS_COVERAGE_SOD_VALID
```

Writer:

```text
A-PREGENESIS-COVERAGE-AUDIT
-> Bootstrap-Coverage-Audit only
```

The Bootstrap-Import control is not a coverage writer for discretionary source universes.

## 6. Currentness

Coverage is current only if all V11 predicates and:

```text
source contract unchanged
source observation frontier unchanged
source completeness root unchanged
coverage SoD current
source/capture control roots current
external/self-verifying proofs current where relied
all material classes covered or conservative UNKNOWN
```

Any relevant source-head/gap/control/self-verification advance makes old coverage non-current.

## 7. Authorization-slot extension

`BootstrapAuthorizationSlot` immutable payload additionally binds:

```text
Bootstrap-Import control identity
Bootstrap-Coverage-Audit control identity
pairwise SoD/separation evidence
PREGENESIS_COVERAGE_SOURCE_CONTRACT_ROOT
```

Authorization issuance closure uniqueness includes these fields.

Changed importer/coverage auditor/source contract after sealing => conflict; no replacement/current slot remint.

## 8. Exact writers / lifecycle

```text
BootstrapAuthorizationSlot
  -> A-BOOTSTRAP-AUTHORIZE
  -> atomic bind side effect of A-PREGENESIS-IMPORT[INITIAL]
  -> atomic consume side effect of A-SYSTEM-GENESIS

BootstrapInstanceJournal
  -> A-PREGENESIS-IMPORT[INITIAL] by Bootstrap-Import
  -> A-PREGENESIS-IMPORT[RECONCILE] by Bootstrap-Import
  -> A-SYSTEM-GENESIS by Genesis

PreGenesisKnowledgeCoverageAttestation
  -> A-PREGENESIS-COVERAGE-AUDIT by Bootstrap-Coverage-Audit
```

No generic pre-system writer exists.

## 9. Closed-world invariants

```text
IMPORTER IS NOT OWN COVERAGE WITNESS FOR DISCRETIONARY SOURCES
SAME-CONTROL EXCEPTION REQUIRES EXTERNAL/SELF-VERIFYING UNSUPPRESSIBLE SOURCE
SOURCE CONTRACT FROZEN BEFORE IMPORT
MATERIAL SOURCE CLASS OMITTED -> COMPLETE DENIED
IMPORT OMISSION DOES NOT ERASE SOURCE-DERIVED KNOWLEDGE OBLIGATION
SOURCE HEAD ADVANCE STALES COVERAGE
UNKNOWN SOURCE COMPLETENESS CANNOT CREATE CLEAN SCIENTIFIC HISTORY
SYSTEM_GENESIS_COMMITTED REMAINS TERMINAL
```

## 10. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
