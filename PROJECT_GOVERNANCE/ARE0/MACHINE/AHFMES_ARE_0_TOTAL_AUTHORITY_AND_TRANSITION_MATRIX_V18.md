# AHFMES ARE-0 — Canonical Authority & Transition Matrix V18

Status: **SOLE CURRENT MACHINE SOURCE / R9-01 SET-VALUED POST-CUT OBLIGATION CLASSIFICATION / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Composition / narrowing

Immutable machine base:

```text
BASE_MATRIX_V17_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V17.md
BASE_MATRIX_V17_GIT_BLOB_SHA = 7234b6572c71230e03d27d29fba3e007b331c547
```

All V17->V1 semantics remain except post-cut observation-to-obligation classification and obligation-set closure are narrowed below.

```text
V18 R9-01 > EXACT V17 > ... > EXACT V1
```

## 1. Finding closed

Exact pre-clean subject:

```text
97a2a8f0a2086e9ee71b2981e37ec1f7e8cdd25b
```

Finding:

```text
IA22-D01 = POST_CUT_OBLIGATION_CLASSIFICATION_IS_NOT_CANONICAL_SET_VALUED
ROOT = R9-01
NEW_R9_ROOT = NO
```

V17 correctly makes the resolver map total over obligation classes, but does not itself make the preceding fact->class/scope decomposition canonical and complete. One multi-domain fact could therefore be under-classified before the resolver map is consulted.

## 2. Static classification semantics

Static generation-0 authority semantics and the sealed bootstrap target bind exact:

```text
POST_CUT_OBLIGATION_CLASSIFICATION_ROOT
```

It commits the frozen deterministic classifier/decomposer policy, exact class ontology, affected-scope derivation, source/materiality applicability, causal/predecessor projection rules, UNKNOWN treatment and canonical tuple ordering.

It is static authority semantics. No import, observation producer, Genesis executor, post-genesis reconciler, scientific actor, Safety actor, runtime actor, operator, chat surface or scheduler may alter it.

A different classification root after sealed authorization is a static conflict and SystemGenesis is denied.

## 3. Canonical set-valued classification

For every material durable `PreGenesisPostCutObservationRecord D`, derive non-writable:

```text
POST_CUT_OBLIGATION_CLASS_SET[D] = CLASSIFY(
  D,
  POST_CUT_OBLIGATION_CLASSIFICATION_ROOT,
  PREGENESIS_MATERIALITY_APPLICABILITY_ROOT,
  frozen source/capture contract,
  frozen class ontology
)
```

The result is a canonical ordered **set**, not one selected label. Each tuple is exactly:

```text
(
  stable fact identity,
  obligation_class,
  affected_scope_root,
  causal_dependency_root,
  source/materiality projection root
)
```

For a material known fact the set MUST be non-empty and MUST contain every simultaneously applicable class/scope. A single fact may therefore create scientific/evidence, broker/account/exposure and Safety/containment sibling obligations at the same time.

No writer-controlled priority, first-match, dominant-domain, favorable-domain or single-label collapse is legal.

## 4. Classification completeness / conservative UNKNOWN

Classification is admissible only when completeness of applicable classes and affected scopes is mechanically established under the frozen policy.

If exact class/scope completeness cannot be established:

```text
POST_CUT_CLASSIFICATION_COMPLETE[D] = FALSE
```

and the handoff MUST contain a conservative UNKNOWN obligation whose affected-domain gate set is the complete mechanically provable superset of domains that could be affected under the frozen source/fact applicability rules.

If even that possible-domain set cannot be proven complete, the conservative gate set is all authority-sensitive domains reachable by the source contract/materiality ontology. Silence, operator assertion or resolver convenience cannot narrow it.

UNKNOWN classification cannot become clean merely because one candidate domain resolves.

## 5. Exact obligation-set closure

Before SystemGenesis may commit, derive:

```text
EXPECTED_POST_CUT_PRECOMMIT_OBLIGATION_SET =
  canonical_union(
    POST_CUT_OBLIGATION_CLASS_SET[D] for every included material durable observation D,
    required conservative UNKNOWN classification obligations,
    V17/V16 UNKNOWN tail obligations
  )
```

SystemGenesis MUST prove in the same atomic handoff transaction:

```text
POST_CUT_PRECOMMIT_OBLIGATION_SET_ROOT
== root(EXPECTED_POST_CUT_PRECOMMIT_OBLIGATION_SET)
```

Any omitted applicable sibling, extra writer-invented class, altered scope, unresolved classification ambiguity, missing causal projection or root mismatch => no clean Genesis commit. The result is reject or conservative UNKNOWN according to the frozen policy; never optimistic omission.

The Genesis executor is only a verifier/committer of this derived closure. It has zero discretion to choose classes or scopes.

## 6. Resolver ordering

V17 `POST_CUT_OBLIGATION_CLASS_RESOLVER_ROOT` remains current, but it applies **only after** V18 classification and obligation-set closure succeed.

```text
OBSERVATION
-> V18 canonical set-valued classification
-> exact immutable obligation-set closure
-> V17 per-domain resolver map
-> derived per-obligation/per-domain resolution
```

A valid resolver mapping cannot cure an under-classified obligation set.

Missing/ambiguous/overlapping resolver mapping remains OPEN/UNKNOWN under V17. Missing/ambiguous classification is independently OPEN/UNKNOWN under V18.

## 7. Sibling-domain independence

For one fact D producing sibling obligations `S`, `B`, `F`:

```text
resolve(S) != resolve(B)
resolve(S) != resolve(F)
resolve(B) != resolve(F)
```

unless exact canonical evidence independently satisfies each sibling's frozen resolver requirements. Resolving, superseding or correcting one sibling cannot delete/reclassify another sibling from immutable queue #0.

Dependency-clear roots are derived at exact class + affected scope + fact identity. Aggregate domain clear is FALSE while any applicable sibling for that domain/scope remains OPEN/UNKNOWN.

## 8. Known facts, UNKNOWN tails and causal closure

V17 durable observation and V16 handoff frontier remain mandatory.

A known D cannot be replaced by a generic UNKNOWN in order to hide its known class/scope consequences. Its exact known classification obligations remain, while any additional unprovable tail or classification extent remains separately UNKNOWN.

An unresolved cross-source or causal predecessor keeps every dependent sibling obligation OPEN even if its local resolver evidence otherwise appears complete.

## 9. <=cut firewall

The V18 classifier is exclusively for semantically `>cut` precommit handoff evolution.

Any actual `<=cut` correction, reorg, missing predecessor or reinterpretation that invalidates relied prefix semantics MUST follow inherited semantic coverage invalidation/reconciliation/new-cut discipline. It cannot be re-labelled as post-cut classification debt.

## 10. Authority scope

No new active writer capability is created by V18. Classification roots and class sets are derived/non-writable. Existing `A-PREGENESIS-POSTCUT-OBSERVE` still writes only observation records; existing `A-SYSTEM-GENESIS` only verifies and atomically commits the derived closure.

Chat/Human-ARE conversation may explain, research, simulate or express governed intent but cannot classify facts authoritatively, clear obligations or exercise ambient broker/capital authority.

## 11. Crash / retry / concurrency theorem

```text
D durable before frontier
-> retry re-derives identical class set under sealed root

D applies to S+B+F
-> all three sibling tuples required independent of executor/operator ordering

scientific sibling resolves first
-> broker/Safety siblings remain OPEN

classifier/root changes after bootstrap seal
-> static conflict; no Genesis

classification incomplete
-> conservative UNKNOWN gate; never clean omission

actual <=cut mutation
-> V18 post-cut classifier cannot preserve stale coverage
```

## 12. Forbidden control planes

```text
first-match or single-label classification of a multi-domain fact
operator/Genesis executor choosing the favorable class or scope
resolver-map totality treated as proof of classification completeness
known D emitted in only one applicable sibling domain
UNKNOWN narrowed by silence or discretionary assertion
one sibling resolution deleting another sibling
post-seal classifier/root mutation
<=cut correction routed through post-cut classification
classification output used as capital/scientific authority by itself
```

All inherited forbidden controls remain.

## 13. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
