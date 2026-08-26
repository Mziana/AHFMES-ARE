# AHFMES ARE-0 — Canonical Authority & Transition Matrix V11

Status: **SOLE CURRENT MACHINE SOURCE / R9-01 FROZEN MATERIALITY + ONE COVERAGE OPPORTUNITY / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable machine base:

```text
BASE_MATRIX_V10_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V10.md
BASE_MATRIX_V10_GIT_BLOB_SHA = 10ac2603f3a996c790cb9d595624c4701949665a
```

All V10->V1 semantics remain except pregenesis materiality/applicability and coverage-attestation opportunity identity/currentness are narrowed here.

```text
V11 R9-01 > EXACT V10 > EXACT V9 > EXACT V8 > EXACT V7 > EXACT V6 > EXACT V5 > EXACT V4 > EXACT V3 > EXACT V2 > EXACT V1
```

R9-02/R9-04/R9-05/R9-06/R9-07 remain unchanged.

## 1. Frozen pregenesis materiality / applicability rule

The static generation-#0 authority-semantics commitment must additionally bind exact:

```text
PREGENESIS_MATERIALITY_APPLICABILITY_ROOT
```

This root is frozen before authorization/import and defines, performance-blindly, which governed-known facts create pregenesis knowledge obligations.

At minimum the rule covers any fact that can materially affect:

```text
legacy scientific/search/validation/selection history
Evidence provenance/exposure/holdout/search debt
Champion/incumbent/comparator factual identity or lineage
proof/selection/reliance ancestry
broker/account/exposure/standing conditional state
Safety containment/observation/reconciliation prerequisites
operational completeness/integrity/debt
any generation-#0 FINAL_REVISION_DERIVED factual field
any later scientific/Safety/capital authority predicate relying on pregenesis history
```

Mandatory semantics:

```text
material/applicable = TRUE -> obligation required
material/applicable = FALSE -> only if deterministically proven under frozen rule
materiality/applicability UNKNOWN -> treat as MATERIAL/APPLICABLE and include conservatively
```

No actor may classify a known fact as immaterial based on result, PnL, desired comparator, desired Champion, desired Safety state, desired debt, desired closure timing or convenience.

Changed materiality/applicability rule after authorization/import is a static-semantic conflict and cannot be introduced by reconciliation.

## 2. Knowledge obligation identity narrowed

V10 `PREGENESIS_KNOWLEDGE_OBLIGATION_KEY` remains, with the exact frozen materiality/applicability root transitively bound by its applicability decision and the current knowledge fold.

A fact governed-known through the frozen universe must either:

```text
create an obligation
OR
have a positive deterministic NON_APPLICABLE proof under PREGENESIS_MATERIALITY_APPLICABILITY_ROOT
```

UNKNOWN never erases the obligation.

`CURRENT_PREGENESIS_KNOWLEDGE_OBLIGATION_SET_ROOT` therefore includes every required semantic obligation through its governed frontier regardless of service scheduling.

## 3. One semantic coverage opportunity per current state

Replace V10 coverage-attestation keying by a stable opportunity identity that excludes later clock/frontier remint:

```text
PREGENESIS_COVERAGE_OPPORTUNITY_KEY = hash(
  BOOTSTRAP_INSTANCE_KEY,
  exact current PREGENESIS_IMPORT_REVISION_ROOT[r],
  exact CURRENT_PREGENESIS_KNOWLEDGE_OBLIGATION_SET_ROOT,
  GENESIS_CUTOFF_RULE_ROOT,
  PREGENESIS_MATERIALITY_APPLICABILITY_ROOT
)
```

At the first canonical frontier where all exact prerequisites for auditing this opportunity are simultaneously available derive immutable payload:

```text
FIRST_PREGENESIS_COVERAGE_ELIGIBLE_INFORMATION_TIME
```

under the frozen `GENESIS_CUTOFF_RULE_ROOT`.

Later wall-clock time, scheduler delay, process restart or repeated audit call cannot change the opportunity key while instance/revision/knowledge-root/rules are unchanged.

Exactly one canonical `PreGenesisKnowledgeCoverageAttestation` may settle one opportunity.

## 4. Attestation key / payload

Current one-slot record identity is:

```text
PREGENESIS_COVERAGE_ATTESTATION_KEY = hash(
  PREGENESIS_COVERAGE_OPPORTUNITY_KEY
)
```

The immutable attestation payload binds:

```text
PREGENESIS_COVERAGE_OPPORTUNITY_KEY
FIRST_PREGENESIS_COVERAGE_ELIGIBLE_INFORMATION_TIME
exact current revision
exact current knowledge-obligation-set root
PREGENESIS_MATERIALITY_APPLICABILITY_ROOT
exact known-material covered-set root
exact NON_APPLICABLE proof set where any
unresolved genuinely unknowable universe root
conservative unknown-debt/lineage consequences
Bootstrap-Audit identity / Genesis SoD
```

Same key/same payload -> existing/idempotent. Same key/conflicting payload -> IntegrityDefect/invalid. No second attestation slot exists merely because a later frontier/time is available.

## 5. Canonical genesis cutoff

Current cutoff is no longer an arbitrary attestation frontier.

For the current opportunity:

```text
GENESIS_CUTOFF_INFORMATION_FRONTIER_ROOT
= FIRST_PREGENESIS_COVERAGE_ELIGIBLE_INFORMATION_TIME
  + exact current knowledge-obligation-set identity bound by the attestation
```

as deterministically represented under `GENESIS_CUTOFF_RULE_ROOT`.

`PREGENESIS_COVERAGE_ATTESTATION_CURRENT` requires:

```text
attestation key == exact current PREGENESIS_COVERAGE_OPPORTUNITY_KEY
current journal revision unchanged
current knowledge-obligation-set root unchanged
materiality/cutoff/static/auth roots unchanged
known required obligations all covered
all NON_APPLICABLE exclusions positively proven under frozen rule
Bootstrap-Audit/Genesis SoD current
```

If revision or knowledge-root changes, the old opportunity becomes historical/non-current and exactly one new opportunity may arise from the new state.

If neither changes, later time cannot create another current opportunity.

## 6. Late fact / reconcile / fresh opportunity theorem

```text
r0 / O0 -> opportunity Q0 -> attestation A0
D becomes governed-known and applicable
=> O1 != O0
=> Q0/A0 non-current
=> if r0 does not include D, reconciliation r0->r1 required
=> derive Q1 from r1/O1
=> exactly one A1 may settle Q1
=> SystemGenesis may use A1
```

A fact with materiality UNKNOWN is included in O1 conservatively; it cannot be excluded to preserve Q0.

## 7. SystemGenesis currentness narrowing

V10 terminal transaction remains and requires exact:

```text
PREGENESIS_COVERAGE_OPPORTUNITY_KEY current
PREGENESIS_COVERAGE_ATTESTATION_KEY current
FIRST_PREGENESIS_COVERAGE_ELIGIBLE_INFORMATION_TIME fixed
PREGENESIS_MATERIALITY_APPLICABILITY_ROOT fixed
all current required obligations covered or conservative UNKNOWN where genuinely unknowable
```

No timing choice among multiple same-state attestations exists.

## 8. Forbidden control planes

```text
known fact labeled immaterial without frozen positive NON_APPLICABLE proof
UNKNOWN materiality used to omit obligation
post-result materiality/applicability change
same instance/revision/knowledge-root creates A0 at F0 and A1 at F1
later clock/frontier used as coverage key material
coverage service retry creates another opportunity without state change
current attestation selected by timing rather than one semantic opportunity
```

All V10 forbidden controls remain.

## 9. Static boundary

This Matrix grants no ARE-0 closure, implementation, P001 substantive research, production, live/paper trading or PR-merge authority.