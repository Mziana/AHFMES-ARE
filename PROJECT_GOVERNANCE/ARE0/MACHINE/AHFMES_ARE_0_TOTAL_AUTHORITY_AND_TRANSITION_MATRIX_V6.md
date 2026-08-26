# AHFMES ARE-0 — Canonical Authority & Transition Matrix V6

Status: **SOLE CANONICAL MACHINE SOURCE / R9 WAVE-7 INVALIDATION ANCESTRY + INFORMATION-TIME CLOSURE / STATELESS CLOSURE SUBJECT / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable Wave-6 base:

```text
BASE_MATRIX_V5_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V5.md
BASE_MATRIX_V5_GIT_BLOB_SHA = 257539aa3d6a4cc113a39ff1358bb7ed58b3bbe7
```

The exact V5 composition remains fully in force except the resolution-generation invalidation trigger/ancestry rules are narrowed here.

```text
V6 EXPLICIT NARROWING > EXACT V5 > EXACT V4 > EXACT V3 > EXACT V2 > EXACT V1
UNKNOWN MATERIAL INVALIDATION ANCESTRY / INFORMATION TIME / COMPLETENESS = FAIL CLOSED
```

## 1. R9-07 — invalidation information-time and descendant propagation

### 1.1 Invalidation information-time cannot backdate

For every direct or inherited resolution-generation invalidation effect define:

```text
RESOLUTION_INVALIDATION_INFORMATION_TIME
= first canonical governed information frontier at which
  the material invalidation effect on the exact resolution generation
  is knowable to the governed Audit/completeness universe
```

Underlying source event-time, old document timestamp, later-discovered historical fact or reconstructed earlier chronology cannot backdate this information time.

```text
later discovery at T2 of fact concerning T0
=> invalidation information time = T2 governed knowability frontier
not T0
```

Stable order:

```text
RESOLUTION_INVALIDATION_TRIGGER_ORDER_KEY = tuple(
  RESOLUTION_INVALIDATION_INFORMATION_TIME,
  direct-vs-inherited canonical class,
  exact invalidation identity / ancestor-generation identity tie-break
)
```

### 1.2 Ancestor invalidation closure bound by each resolution generation

Every `OperationalCompletenessDefectResolutionRecord` generation `g` binds at settlement:

```text
ANCESTOR_RESOLUTION_INVALIDATION_CLOSURE_ROOT_AT_SETTLEMENT(g)
= append-only canonical fold of every resolution-invalidation identity
  for the same COMPLETENESS_RESOLUTION_ROOT_KEY
  on generations < g
  knowable through g's exact settlement frontier
```

The g settlement transaction CAS-compares this exact ancestor closure root together with the V5 current prior-generation invalidation set and other completeness/reliance heads.

If an ancestor invalidation becomes canonically knowable before g commit, the ancestor-closure root advances and the stale g transaction loses. Retry uses the same g SLOT_KEY with updated complete payload.

### 1.3 Late ancestor invalidation invalidates existing descendants

For a RESOLVED generation `g`, define:

```text
UNCOVERED_ANCESTOR_INVALIDATION_SET_ROOT(g)
= every canonical invalidation identity for the same resolution root key
  on ancestor generations < g
  whose invalidation information time is later than g's bound ancestor-closure frontier
  and therefore is absent from ANCESTOR_RESOLUTION_INVALIDATION_CLOSURE_ROOT_AT_SETTLEMENT(g)
```

Because the root key already fixes exact adverse gap + exact affected relied lineage, any such uncovered ancestor invalidation is conservatively material to an already-existing descendant resolution unless a later successor generation is adjudicated against the enlarged closure.

Thus:

```text
RESOLUTION_GENERATION_INVALIDATED(g) = TRUE FOREVER
if either:
  a direct canonical invalidation of g exists; OR
  UNCOVERED_ANCESTOR_INVALIDATION_SET_ROOT(g) is non-empty
```

No descendant generation may remain effective merely because the late defect was originally recorded against an ancestor.

### 1.4 One immutable first invalidation trigger per generation

For generation `g`, the first invalidation anchor is the trigger with minimum **information-time order** at the first frontier where `RESOLUTION_GENERATION_INVALIDATED(g)` becomes true:

```text
FIRST_COMPLETENESS_RESOLUTION_INVALIDATION_KEY(g)
= minimum RESOLUTION_INVALIDATION_TRIGGER_ORDER_KEY
  among direct or uncovered-ancestor triggers
  at the first invalidated frontier
```

Once established, this key is immutable forever.

Later-discovered invalidations cannot replace it because their governed information time is later, even when they concern an earlier historical event.

Tie at identical information-time frontier is resolved by the frozen class/identity tie-break.

### 1.5 Effective invalidation set per generation

Replace the V5 payload set with:

```text
RESOLUTION_GENERATION_EFFECTIVE_INVALIDATION_SET_ROOT(g)
= append-only ordered fold of:
    all direct canonical invalidations of g
    + all uncovered ancestor invalidations that invalidate g
```

A successor `g+1` binds/CAS-compares the exact current effective invalidation-set root of `g` at settlement and must address every material element relevant to the fixed adverse gap/relied lineage.

If a new direct or ancestor invalidation becomes knowable before successor commit, stale CAS loses; retry uses the same successor SLOT_KEY anchored by immutable FIRST invalidation key.

### 1.6 Successor slot identity remains one per generation

V5 successor slot rule remains, interpreted with the V6 immutable first invalidation trigger:

```text
COMPLETENESS_RESOLUTION_SLOT_KEY[g>0] = hash(
  COMPLETENESS_RESOLUTION_ROOT_KEY,
  g,
  exact prior generation resolution-record identity,
  FIRST_COMPLETENESS_RESOLUTION_INVALIDATION_KEY(g-1)
)
```

Direct versus inherited late invalidation cannot mint a second slot.

### 1.7 Effectiveness

```text
EFFECTIVE_COMPLETENESS_RESOLUTION(root_key)
= highest canonical RESOLVED generation g such that:
    RESOLUTION_GENERATION_INVALIDATED(g) = FALSE
    AND all own resolution/SoD/reliance premises are current
```

Any direct or uncovered-ancestor invalidation permanently excludes generation g. Recovery occurs only through a later generation bound to the enlarged invalidation ancestry.

## 2. Mutation-boundary and normal-new-risk coupling preserved

All V4/V5 mutation-boundary completeness coupling and explicit preservation of V2 §6.5 normal-new-risk narrowing remain fully in force.

A late ancestor invalidation that makes the effective completeness resolution disappear therefore also changes protected-scope unresolved completeness state and stales affected unused mutation-boundary authority/new-risk eligibility until governed reconciliation/current successor resolution.

## 3. Additional forbidden control planes

```text
late-discovered historical invalidation backdated to change an already-born successor slot key
ancestor invalidation recorded only on g0 while g1 remains effective despite not binding it
resolution generation settles while ancestor invalidation closure changed before commit
first invalidation anchor recomputed after later discovery
successor addresses direct invalidations but silently ignores uncovered ancestor invalidations
```

## 4. Static boundary

This design grants no ARE-0 closure, implementation, P001 substantive research, production or PR-merge authority.