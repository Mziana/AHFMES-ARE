# AHFMES ARE-0 — Canonical Authority & Transition Matrix V12

Status: **SOLE CURRENT MACHINE SOURCE / R9-01 PREGENESIS COVERAGE INDEPENDENCE + SOURCE-CONTRACT CLOSURE / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Composition / narrowing

Immutable machine base:

```text
BASE_MATRIX_V11_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V11.md
BASE_MATRIX_V11_GIT_BLOB_SHA = dac350ddc0305d1eaad481ebdcc2f8b13ab6d3d8
```

All V11->V1 semantics remain except pregenesis import/coverage control separation, source-contract completeness and coverage-currentness are narrowed below.

```text
V12 R9-01 > EXACT V11 > EXACT V10 > EXACT V9 > ... > EXACT V1
```

R9-02/R9-04/R9-05/R9-06/R9-07 remain unchanged.

## 1. Separate pre-system import and coverage-audit controls

The target-scoped bootstrap authorization assertion and sealed authorization slot must additionally bind exact:

```text
Bootstrap-Import control identity
Bootstrap-Coverage-Audit control identity
```

The existing V9/V10 `Bootstrap-Audit` import/reconcile executor is interpreted as the **Bootstrap-Import** control for current V12 semantics.

`A-PREGENESIS-COVERAGE-AUDIT` is no longer executable by that importer merely because it is the bound Bootstrap-Import control. It is executable only by the exact bound `Bootstrap-Coverage-Audit` control under §2.

Required common-control separation:

```text
Genesis != Bootstrap-Import
Genesis != Bootstrap-Coverage-Audit
Bootstrap-Import != Bootstrap-Coverage-Audit
```

for discretionary relied source/capture surfaces, subject only to the external/self-verifying exception in §2.3.

Unknown material common control => coverage cannot be COMPLETE.

## 2. Frozen pregenesis source/capture contract

The static generation-#0 authority-semantics commitment additionally binds exact:

```text
PREGENESIS_COVERAGE_SOURCE_CONTRACT_ROOT
```

This root is frozen before authorization/import and defines, for every materiality class covered by `PREGENESIS_MATERIALITY_APPLICABILITY_ROOT`:

```text
source identity / authoritative boundary
required event/fact universe semantics
capture/observation boundary
canonicalization and deduplication rule
gap-detection rule
freshness / revision semantics
source/capture control-equivalence root
whether the source is external/self-verifying
proof that importer/subject cannot forge, suppress or rewrite the relied source where that exception is claimed
mapping from source observations to PREGENESIS_KNOWLEDGE_OBLIGATION_KEY
```

No reconciliation revision may change this source contract.

### 2.1 Source-contract totality

Define:

```text
PREGENESIS_COVERAGE_SOURCE_CONTRACT_TOTALITY_VALID
```

iff every fact class material/applicable under the frozen materiality rule is mapped to at least one positively specified authoritative source/capture boundary and the required event/fact universe is mechanically decidable or conservatively UNKNOWN.

Missing material source class, caller-selected source omission or UNKNOWN mapping => not COMPLETE.

### 2.2 Independent source observation frontier

Define:

```text
PREGENESIS_SOURCE_OBSERVATION_FRONTIER_ROOT = hash(
  exact current heads/revisions of every relied source contract,
  exact canonicalized observed fact/event set roots,
  exact gap/freshness state,
  exact external/self-verifying proof roots where applicable,
  canonical information frontier
)
```

`CURRENT_PREGENESIS_KNOWLEDGE_OBLIGATION_SET_ROOT` is derived from the frozen materiality rule **and this source observation frontier**, not solely from what the Bootstrap-Import control chose to place into the journal.

Thus an importer cannot erase a semantic obligation merely by omitting a source fact from `PREGENESIS_IMPORT_REVISION_ROOT[r]`.

### 2.3 Coverage independence / self-verifying exception

Define:

```text
PREGENESIS_COVERAGE_SOD_VALID
```

iff for every relied discretionary source/capture surface:

```text
Bootstrap-Coverage-Audit common-control root
!= Bootstrap-Import / exact capture-producer common-control root
```

unless all are positively proven:

```text
source is external/self-verifying for the exact relied fact universe
Bootstrap-Import/capture principal cannot forge, suppress, reorder or rewrite the relied source evidence
coverage proof verifies against that external/self-verifying root directly
```

Two daemons/processes/machines under one common-control principal are not independent.

If separation/self-verification is UNKNOWN, `COVERAGE_CURRENT_COMPLETE` is denied. Conservative UNKNOWN may be used only with the inherited unknown-debt/unknown-lineage consequences and may not establish clean scientific history.

## 3. Coverage source completeness proof

Add derived exact proof identity:

```text
PREGENESIS_SOURCE_COMPLETENESS_ROOT = hash(
  PREGENESIS_COVERAGE_SOURCE_CONTRACT_ROOT,
  PREGENESIS_SOURCE_OBSERVATION_FRONTIER_ROOT,
  exact required source/event universe coverage,
  exact gap/freshness disposition,
  exact source-control roots,
  PREGENESIS_COVERAGE_SOD_VALID,
  exact external/self-verifying proof roots or NONE,
  exact unresolved source-coverage uncertainty root
)
```

This root is evidence payload, not an independently writable authority object.

A source completeness result can be:

```text
SOURCE_COMPLETE
SOURCE_UNKNOWN_CONSERVATIVE
```

Known source gap or known suppressed/missing required event cannot be represented `SOURCE_COMPLETE`.

## 4. Coverage opportunity / attestation V12 narrowing

V11 stable `PREGENESIS_COVERAGE_OPPORTUNITY_KEY` remains one semantic opportunity per exact revision/knowledge state, and is narrowed to bind the frozen source contract transitively through the static commitment/materiality rule.

The `PreGenesisKnowledgeCoverageAttestation` payload must additionally bind exact:

```text
PREGENESIS_COVERAGE_SOURCE_CONTRACT_ROOT
PREGENESIS_SOURCE_OBSERVATION_FRONTIER_ROOT
PREGENESIS_SOURCE_COMPLETENESS_ROOT
Bootstrap-Import control identity
Bootstrap-Coverage-Audit control identity
PREGENESIS_COVERAGE_SOD_VALID
```

Exact writer:

```text
A-PREGENESIS-COVERAGE-AUDIT
executor = Bootstrap-Coverage-Audit
```

The importer cannot write its own coverage attestation for a discretionary source universe.

Same opportunity/same complete payload -> existing. Conflict -> IntegrityDefect/invalid.

## 5. Coverage currentness

`PREGENESIS_COVERAGE_ATTESTATION_CURRENT` now requires all V11 currentness plus:

```text
source contract exact/current
source observation frontier exact/current
source completeness root exact/current
coverage SoD exact/current
all required source heads/freshness states unchanged through commit frontier
all material source classes covered or conservatively UNKNOWN
```

If a source head, gap state, control-equivalence relation, self-verification proof or source completeness state advances before SystemGenesis, the attestation becomes non-current.

## 6. Omission attack theorem

For material legacy/scientific/debt fact `D` available on an authoritative source boundary:

```text
Bootstrap-Import suppresses D from revision r
```

does not erase D.

Expected semantics:

```text
source observation frontier contains/implicates D
-> materiality rule creates obligation OD
-> current knowledge-obligation root includes OD
-> coverage attestation cannot be COMPLETE while r omits D
-> reconcile same instance r->r+1 including D OR retain governed UNKNOWN consequence
-> fresh independent coverage attestation required
```

If the source/capture control itself can suppress D and no independent/self-verifying boundary proves completeness, coverage must remain UNKNOWN_CONSERVATIVE rather than clean COMPLETE.

UNKNOWN_CONSERVATIVE must preserve the inherited unknown scientific/search/debt lineage and cannot be used to establish no-debt/clean-history privilege.

## 7. Authorization / sealed slot binding extension

V9/V10 target authorization remains mandatory and is narrowed so the assertion/issuance closure/sealed slot payload bind exact:

```text
Bootstrap-Import control identity
Bootstrap-Coverage-Audit control identity
required pairwise SoD/separation evidence
PREGENESIS_COVERAGE_SOURCE_CONTRACT_ROOT
```

A changed import/coverage control or source contract after sealing is a static authorization conflict. It cannot be introduced via reconciliation or alternate slot.

`BOOTSTRAP_AUTHORIZATION_TARGET_VALID` additionally verifies those exact fields.

## 8. Reconcile and SystemGenesis interactions

Reconciliation continues to be executed by Bootstrap-Import under the bound slot and cannot mutate source contract, materiality rule, static semantics or coverage-control identity.

SystemGenesis requires:

```text
BootstrapAuthorizationSlot = BOUND_TO_JOURNAL
current journal revision
current stable coverage opportunity/attestation
PREGENESIS_COVERAGE_SOURCE_CONTRACT_TOTALITY_VALID
PREGENESIS_SOURCE_COMPLETENESS_ROOT current
PREGENESIS_COVERAGE_SOD_VALID or positively proven external/self-verifying exception
all known material obligations covered
UNKNOWN source universe -> conservative unknown lineage, never clean privilege
```

The terminal transaction also CAS-compares every locally authoritative source head represented in `PREGENESIS_SOURCE_OBSERVATION_FRONTIER_ROOT`. External non-CAS sources are bounded by exact revision/freshness proof and fail closed on ambiguity.

## 9. Exact authority rows — V12 narrowing

| Authority | Issuer approval | Executor | Usage | Exact prerequisites | Capital |
|---|---|---|---|---|---|
| `A-BOOTSTRAP-AUTHORIZE` | exogenous trust plane | exogenous trust plane | ONE_SHOT slot | target instance + static semantics + Import/Coverage controls + source contract + unique issuance closure | NO |
| `A-PREGENESIS-IMPORT[INITIAL]` | sealed slot | Bootstrap-Import | ONE_SHOT initial | exact target/static/source contract; slot bind+journal r0 atomic | NO |
| `A-PREGENESIS-IMPORT[RECONCILE]` | bound slot | Bootstrap-Import | serial CAS | exact current revision; static/source contract unchanged | NO |
| `A-PREGENESIS-COVERAGE-AUDIT` | bound slot | Bootstrap-Coverage-Audit | ONE_SHOT per current opportunity | independent/source-verifying coverage + current source frontier + current revision/knowledge roots | NO |
| `A-SYSTEM-GENESIS` | bound slot | Genesis | ONE_SHOT terminal | current independent coverage + exact final binding/object set + atomic slot consumption | NO |

No older generic bootstrap writer widens these guards.

## 10. Forbidden control planes

```text
Bootstrap-Import writes its own COMPLETE coverage attestation over discretionary sources
coverage auditor common-controlled with importer/capture producer without unforgeable external source proof
source contract omits a material class covered by materiality rule
import omission removes a semantic knowledge obligation
source head advances but old coverage remains current
UNKNOWN source completeness represented clean COMPLETE
UNKNOWN_CONSERVATIVE used to erase possible legacy/search/selection debt
source/capture contract changed via r->r+1 reconciliation
coverage proof from unbound source/frontier satisfies genesis
same-control daemons represented independent merely by process/machine separation
```

All V11/V10/V9 forbidden controls remain.

## 11. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
