# AHFMES ARE-0 — Canonical Authority & Transition Matrix V5

Status: **SOLE CANONICAL MACHINE SOURCE / R9 WAVE-6 STICKY RESOLUTION-INVALIDATION TOTALITY / STATELESS CLOSURE SUBJECT / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable Wave-5 base:

```text
BASE_MATRIX_V4_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V4.md
BASE_MATRIX_V4_GIT_BLOB_SHA = 7e642490446df3b5733aeca1b80da533a29b1f54
```

The exact V4 composition remains fully in force, including explicit preservation of V2 §6.5 normal-new-risk narrowing, except V4 §1 resolution-successor identity/effectiveness rules are narrowed by this V5.

```text
V5 EXPLICIT NARROWING > EXACT V4 > EXACT V3 > EXACT V2 > EXACT V1
UNKNOWN MATERIAL RESOLUTION / INVALIDATION / COMPLETENESS = FAIL CLOSED
```

## 1. R9-07 — sticky resolution invalidation and one successor slot

### 1.1 Root and generation remain

```text
COMPLETENESS_RESOLUTION_ROOT_KEY
NEXT_COMPLETENESS_RESOLUTION_GENERATION
```

remain as defined by V4.

Generation 0 has no predecessor invalidation trigger.

### 1.2 Deterministic invalidation order per resolution generation

Every canonical material invalidation of a resolution generation has an immutable event order key:

```text
COMPLETENESS_RESOLUTION_INVALIDATION_ORDER_KEY = tuple(
  FIRST_INVALIDATION_INFORMATION_TIME,
  stable invalidated-premise/dependency identity tie-break
)
```

For exact `COMPLETENESS_RESOLUTION_ROOT_KEY` and resolution generation `g`:

```text
FIRST_COMPLETENESS_RESOLUTION_INVALIDATION_KEY(g)
= minimum canonical invalidation event under the frozen order key
```

Once the first invalidation exists:

```text
RESOLUTION_GENERATION_INVALIDATED(g) = TRUE FOREVER
```

No remediation, later Audit or disappearance of the original defect can make generation `g` effective again. Historical generation `g` remains immutable evidence only. Recovery requires a successor generation.

### 1.3 Invalidation set

All distinct canonical invalidations of generation `g` are retained:

```text
RESOLUTION_GENERATION_INVALIDATION_SET_ROOT(g)
= append-only ordered fold of every canonical resolution-invalidation identity for generation g
```

Multiple invalidations do not mint multiple successor identities.

### 1.4 Exactly one successor slot per generation

Resolution slot identity is replaced by:

```text
COMPLETENESS_RESOLUTION_SLOT_KEY[g0] = hash(
  COMPLETENESS_RESOLUTION_ROOT_KEY,
  0,
  EMPTY_PREDECESSOR
)

COMPLETENESS_RESOLUTION_SLOT_KEY[g>0] = hash(
  COMPLETENESS_RESOLUTION_ROOT_KEY,
  g,
  exact prior generation resolution-record identity,
  FIRST_COMPLETENESS_RESOLUTION_INVALIDATION_KEY(g-1)
)
```

Only the first canonical invalidation key participates in successor slot identity. Later invalidation events are payload/current-admissibility inputs, not new slot-key material.

Thus two invalidations `I1` and `I2` of g0 cannot create two g1 slots.

### 1.5 Successor settlement frontier / CAS

A successor resolution transaction for generation `g>0` binds as payload and CAS-compares:

```text
PRIOR_RESOLUTION_INVALIDATION_SET_ROOT_AT_SETTLEMENT
= exact RESOLUTION_GENERATION_INVALIDATION_SET_ROOT(g-1)

exact affected completeness adverse-lineage head
exact relied dependency/re-adjudication/reconciliation heads
exact reconstruction/backfill/dependency-removal evidence heads
exact resolution SoD/control heads
```

Successor `RESOLVED` is admissible only if its authoritative recovery/remediation positively addresses **every material invalidation in the bound prior-generation invalidation set** that remains relevant to the relied lineage.

If another canonical invalidation of the prior generation appears before local successor commit, the invalidation-set root changes and the stale successor transaction loses CAS. It may retry only on the **same successor SLOT_KEY** with updated complete payload; retry/time/session cannot mint another slot.

### 1.6 Sticky effectiveness rule

V4 `EFFECTIVE_COMPLETENESS_RESOLUTION` is replaced by:

```text
EFFECTIVE_COMPLETENESS_RESOLUTION(root_key)
= highest canonical RESOLVED generation g such that:
    RESOLUTION_GENERATION_INVALIDATED(g) = FALSE
    AND all resolution evidence/SoD/reliance-handling premises for g are current
```

A generation with any canonical resolution invalidation is permanently excluded from effectiveness, even if the originally invalidated premise later appears repaired. Repair must be represented by the next canonical generation.

If the newest generation becomes invalidated and no valid successor exists, the adverse gap is unresolved.

### 1.7 Invalidation key remains evidence identity

The V4 `COMPLETENESS_RESOLUTION_INVALIDATION_KEY` remains an immutable `IntegrityDefectRecord` identity. Its order key is additionally bound so `FIRST_COMPLETENESS_RESOLUTION_INVALIDATION_KEY` is mechanically decidable.

Same invalidation event/same payload -> existing; conflicting payload -> IntegrityDefect. Distinct material invalidation events remain distinct evidence but share one successor generation slot.

## 2. Mutation-boundary coupling preserved

V4 §2 remains fully in force. Protected-scope mutation-boundary currentness binds the current completeness adverse/resolution/invalidation/unresolved roots. Any new invalidation or successor resolution affecting the protected scope stales unused old boundary authority until governed reconciliation/current boundary.

## 3. Additional forbidden control planes

```text
two invalidation records for one resolution generation -> two successor slot keys
later invalidation event silently ignored by successor evidence payload
new invalidation arrives before successor commit but stale transaction still wins
previously invalidated resolution generation becomes effective again without successor generation
retry after invalidation-set advance mints a new successor slot
```

## 4. Static boundary

This design grants no ARE-0 closure, implementation, P001 substantive research, production or PR-merge authority.