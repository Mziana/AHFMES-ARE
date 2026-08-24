# AHFMES ARE-0 — Canonical Authority & Transition Matrix V4

Status: **SOLE CANONICAL MACHINE SOURCE / R9 WAVE-5 RESOLUTION SUCCESSOR + GATE-PRESERVATION HARDENING / STATELESS CLOSURE SUBJECT / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Canonical composition / precedence

This file is the sole current machine source for ARE-0.

Immutable Wave-4 base:

```text
BASE_MATRIX_V3_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V3.md
BASE_MATRIX_V3_GIT_BLOB_SHA = 5c8b2e53000253a069de1c0765beec79fc33e631
```

The exact V3 blob, its exact V2 base and its exact V1 base remain incorporated except the surfaces explicitly replaced/narrowed here.

### 0.1 Explicit preservation of V2 §6.5 normal-new-risk narrowing

The Wave-4 phrase replacing the V2 R9-07 §6 surface is clarified and narrowed:

```text
V2 §6.1..§6.4 completeness/adverse-history semantics
  -> replaced by V3/V4 R9-07 semantics

V2 §6.5 NORMAL-NEW-RISK NARROWING
  -> REMAINS FULLY IN FORCE
  -> no R9 predicate is deleted
  -> its completeness predicates are interpreted using the current V4 effective completeness semantics
```

In particular the composed normal-new-risk gate still requires all applicable V2 §6.5 R9 predicates, including:

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

and all incorporated base R7/R8 gates. No replacement in V3/V4 may be read as widening normal new-risk authority.

### 0.2 Wave-5 replacement surface

V3 R9-04 revalidation semantics remain unchanged.

V3 R9-07 §§2.2..2.5 resolution identity/lifecycle are replaced by this V4 §1. V3 non-substitution, completeness surface definitions and historical-adverse immutability remain.

V3/V2 R9-06 mutation-boundary input frontier is narrowed by V4 §2 to bind effective completeness-resolution state.

```text
V4 EXPLICIT NARROWING > EXACT V3 BASE > EXACT V2 BASE > EXACT V1 BASE
UNKNOWN MATERIAL AUTHORITY / RESOLUTION / COMPLETENESS / MUTATION BOUNDARY = FAIL CLOSED
```

## 1. R9-07 — generational completeness-defect resolution

### 1.1 Stable root key and deterministic generation

An exact historical completeness adverse gap affecting an exact relied lineage has one stable root identity:

```text
COMPLETENESS_RESOLUTION_ROOT_KEY = hash(
  completeness surface class,
  exact adverse-gap / adverse-record identity,
  exact affected relied dependency lineage root
)
```

Resolution generations are monotone and never reused:

```text
NEXT_COMPLETENESS_RESOLUTION_GENERATION
= 1 + max(all generations ever allocated for COMPLETENESS_RESOLUTION_ROOT_KEY,
          including later-invalidated historical resolutions)
```

Generation 0 is first resolution opportunity. A later generation may exist only after the previous effective resolution has a canonical material invalidation/defect record and a new remediation opportunity is positively available.

Stable one-slot identity per generation:

```text
COMPLETENESS_RESOLUTION_SLOT_KEY = hash(
  COMPLETENESS_RESOLUTION_ROOT_KEY,
  exact resolution generation,
  exact prior resolution record identity or EMPTY,
  exact prior resolution invalidation identity or NONE
)
```

Backfill/reconstruction/remediation evidence is payload, **not slot-key material**. Competing evidence packages for the same generation therefore collide on one slot rather than minting parallel resolution identities.

### 1.2 Resolution record

Existing Wave-4 object remains:

```text
OperationalCompletenessDefectResolutionRecord
```

Each record binds:

```text
COMPLETENESS_RESOLUTION_ROOT_KEY
COMPLETENESS_RESOLUTION_SLOT_KEY
resolution generation
exact adverse gap/record
exact affected relied dependency lineage
authoritative reconstruction/backfill/reconciliation OR dependency-removal proof
resolution evidence root
independent Audit/control root
affected reliance invalidation/re-adjudication/reconciliation root
RESOLVED
```

Historical `OperationalCompletenessRecord FAIL/UNKNOWN` remains immutable.

### 1.3 Resolution SoD / anti-self-reconstruction

A resolution is admissible only if:

```text
resolution Audit is independent by common control from the original audited capture/control surface
AND
resolution Audit is independent by common control from any discretionary reconstruction/backfill producer/operator
UNLESS the reconstruction source is positively external/self-verifying and the audited/reconstruction principal cannot forge, suppress or rewrite the relied evidence
```

The Audit cannot manufacture its own reconstruction and attest it as authoritative.

### 1.4 Exact resolution authority

| Authority | Issuer approval | Executor / holder | Usage | Exact scope / prerequisites | Capital |
|---|---|---|---|---|---|
| A-INTEGRITY-AUDIT[COMPLETENESS_RESOLUTION] | independent Audit | independent Audit | ONE_SHOT per COMPLETENESS_RESOLUTION_SLOT_KEY | exact adverse gap/lineage + authoritative recovery/dependency removal + resolution SoD + affected reliance handling | NO |

Exact edge:

```text
OperationalCompletenessDefectResolutionRecord absent exact SLOT_KEY
-> RESOLVED
= A-INTEGRITY-AUDIT[COMPLETENESS_RESOLUTION]
```

Same SLOT_KEY/same payload -> existing. Same SLOT_KEY/conflicting payload -> IntegrityDefect; no second resolution at that generation.

### 1.5 Resolution invalidation without history rewrite

A resolution record is immutable evidence. If any relied resolution premise later becomes materially invalid, independent Audit writes an existing `IntegrityDefectRecord` in exact mode:

```text
A-INTEGRITY-AUDIT[COMPLETENESS_RESOLUTION_INVALIDATION]
```

Canonical key:

```text
COMPLETENESS_RESOLUTION_INVALIDATION_KEY = hash(
  COMPLETENESS_RESOLUTION_ROOT_KEY,
  exact resolution generation,
  exact resolution record identity,
  exact invalidated premise/dependency identity,
  first canonical invalidation-information frontier
)
```

This record does not rewrite `RESOLVED`; it makes that generation ineffective for the current unresolved projection.

Same invalidation key/same payload -> existing; conflict -> IntegrityDefect.

### 1.6 Successor re-resolution

After a resolution is invalidated, the same gap/relied lineage is unresolved again. A successor resolution generation may be created only if:

```text
prior resolution invalidation is canonical/current
material remediation state is positively new relative to the invalidated resolution
new authoritative recovery/dependency-removal evidence is available
resolution SoD is valid
all affected reliance invalidation/re-adjudication/reconciliation requirements are current
```

The successor uses `NEXT_COMPLETENESS_RESOLUTION_GENERATION` and the single `COMPLETENESS_RESOLUTION_SLOT_KEY` for that generation.

Thus:

```text
resolution g0 valid
-> later g0 premise invalidated
-> gap becomes unresolved
-> material remediation
-> resolution g1 may become RESOLVED
```

without rewriting g0 and without allowing two g1 records.

### 1.7 Adverse / resolution / unresolved projections

```text
COMPLETENESS_ADVERSE_LINEAGE_ROOT
= append-only all historical adverse completeness evidence

COMPLETENESS_RESOLUTION_SET_ROOT
= append-only all resolution-record identities across generations

COMPLETENESS_RESOLUTION_INVALIDATION_SET_ROOT
= append-only all canonical resolution-invalidation identities

EFFECTIVE_COMPLETENESS_RESOLUTION(root_key)
= highest canonical resolution generation whose exact resolution premises are current
  and which has no applicable current resolution-invalidation record

UNRESOLVED_COMPLETENESS_ADVERSE_LINEAGE_ROOT(surface, relied_frontier)
= deterministic projection of adverse lineage minus only exact gap/lineage pairs
  with an EFFECTIVE_COMPLETENESS_RESOLUTION whose affected reliance handling is current
```

A later-invalid g0 does not block a valid g1. A historical g0 remains evidence and cannot be deleted.

### 1.8 Exact invalidation authority

| Authority | Issuer approval | Executor / holder | Usage | Exact scope / prerequisites | Capital |
|---|---|---|---|---|---|
| A-INTEGRITY-AUDIT[COMPLETENESS_RESOLUTION_INVALIDATION] | independent Audit | independent Audit | ONE_SHOT per invalidation key | exact previously relied resolution premise/dependency materially invalid | NO |

The writer creates `IntegrityDefectRecord` only; it does not mutate the old resolution record.

## 2. R9-06 × R9-07 — mutation-boundary completeness coupling

The incorporated `MUTATION_BOUNDARY_INPUT_FRONTIER_ROOT` is narrowed to additionally bind, for every relied completeness surface relevant to protected broker/account scope:

```text
exact OperationalCompletenessRecord head/frontier
COMPLETENESS_ADVERSE_LINEAGE_ROOT
COMPLETENESS_RESOLUTION_SET_ROOT
COMPLETENESS_RESOLUTION_INVALIDATION_SET_ROOT
UNRESOLVED_COMPLETENESS_ADVERSE_LINEAGE_ROOT
```

A resolution, resolution invalidation, or adverse-lineage change that affects protected-scope completeness therefore makes an unused stale mutation-boundary generation lose currentness/requires governed reconciliation before new risk.

Known local head advance before boundary CAS still makes the transaction lose under V2/V3 rules. External facts remain bounded by canonical observation/freshness and fail closed when unknown.

## 3. Exact V4 writer extensions

V3 writers remain, with these exact additions:

```text
IntegrityDefectRecord
  -> incorporated existing defect writers
  -> A-INTEGRITY-AUDIT[COMPLETENESS_RESOLUTION_INVALIDATION]

OperationalFidelityLedger
  -> incorporated writers
  -> A-INTEGRITY-AUDIT[COMPLETENESS_RESOLUTION]
  -> A-INTEGRITY-AUDIT[COMPLETENESS_RESOLUTION_INVALIDATION]
```

`OperationalCompletenessDefectResolutionRecord` remains writable only by `A-INTEGRITY-AUDIT[COMPLETENESS_RESOLUTION]` under one exact generational slot.

## 4. Additional forbidden control planes

```text
interpreting V3 replacement as deleting V2 §6.5 normal-new-risk narrowing
resolution g0 invalidated -> permanent inability to re-resolve the same gap
alternate reconstruction payload minting a parallel resolution slot at same generation
resolution Audit common-controlled with discretionary reconstruction producer
resolution invalidation rewriting historical RESOLVED record
successor resolution generation without canonical prior invalidation + material remediation
mutation boundary remaining current after relied effective completeness-resolution state changes
```

## 5. Static boundary

This design grants no ARE-0 closure, implementation, P001 substantive research, production or PR-merge authority. Audit-progress state remains outside the Matrix.