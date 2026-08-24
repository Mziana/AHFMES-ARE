# 2026-08-24 — ARE-0 Integrated Recovery/Rollback V3 Published

## Current design

`PROJECT_GOVERNANCE/AHFMES_ARE_0_INTEGRATED_RECOVERY_ROLLBACK_ARCHITECTURE_V3.md`

Commit: `f0e2b8287162a3958f05de2f52467296a84ef831`

V3 is the first integrated successor design that explicitly composes:

```text
historical authority invalidation
+ prospective reliance recovery
+ recovery non-authority
+ consequence-blind invalidation discovery
+ rollback cause observation
+ frozen cause classifier
+ observer/attester separation
+ fallback matrix currentness
+ Safety/Champion freshness
```

## Why V3 exists

Loop 2 found five second-order gaps in V2:

```text
L2-01 Reliance could be described as non-authoritative but needed an explicit
      mechanical theorem that it cannot be an issuer or substitute for any gate.

L2-02 Historical invalidation discovery itself could be outcome-conditioned.

L2-03 A frozen cause taxonomy was insufficient if the classifier/model could be
      updated or selected after outcome exposure.

L2-04 Fallback compatibility could become stale after Safety/Champion/Deployment
      context changed.

L2-05 Observer/attester separation needed to be strict for any non-flat fallback,
      rather than conditional wording.
```

All five were incorporated into the integrated V3 architecture.

## V3 attack posture

The design is deliberately NOT declared final. Loop 3 must attack composition and positive liveness:

```text
Reliance -> hidden authority
Outcome -> invalidation discovery -> recovery
Outcome -> cause classification -> fallback
Observer/attester collusion
Fallback matrix drift
Safety/Champion race
Recovery -> debt/holdout reset
UNKNOWN starvation
Concurrent recovery + rollback
Cause discovery after outcome but via independent schedule
```

## Acceptance gate

Do not send an acceptance claim until V3 survives the next attack loop. The external candidate remains immutable and is not being silently modified by these successor designs.

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
```
