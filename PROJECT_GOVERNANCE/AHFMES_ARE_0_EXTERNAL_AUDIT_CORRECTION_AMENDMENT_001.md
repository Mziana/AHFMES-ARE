# AHFMES ARE-0 — External Audit Correction Amendment 001

Status: **NORMATIVE BOUNDED CORRECTION / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

This amendment records defects found by the internal re-attack of the external-audit correction package. It is intentionally narrow.

It controls over conflicting text in:

- `AHFMES_ARE_0_EXTERNAL_AUDIT_CORRECTION_PACKAGE_V1.md`
- `AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V1.md`
- `AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V1.md`

## 1. Add `A-CAPITAL-DEACTIVATE`

```text
authority_class = A-CAPITAL-DEACTIVATE
issuer           = TD-CAPITAL-SAFETY
holder/executor  = TD-EXECUTION
scope            = stop/deactivate exact active deployment without changing scientific/Champion history
trigger           = exact deployment stop contract, manual external safety/governance command, or mechanical safety condition
forbidden         = Research/Critic/Governor opinion as sole trigger
capital_mutating  = YES, risk-reducing/neutral only
```

Normal deployment deactivation must not rely on an anonymous `explicit deactivation authority`.

`DeploymentActivationEpisode` correction:

```text
ACTIVE -> DEACTIVATED
= one of:
  A-CAPITAL-DEACTIVATE
  A-ROLLBACK
  A-EMERGENCY-FLAT
```

Each path preserves its own trigger semantics and evidence.

## 2. Add `A-AUTHORITY-REVOKE`

```text
authority_class = A-AUTHORITY-REVOKE
issuer           = TD-GOVERNANCE-ROOT
holder/executor  = trusted authority/gate registry service outside TD-RESEARCH
scope            = revoke exact unused authority/gate/role capability by identity and generation
trigger           = Governance Root / trusted registry revocation operation
capital_mutating  = NO directly
```

Research, Critic, Governor and Promotion may not revoke authorities to manipulate proof history.

## 3. VerifiedAuthorityRecord semantics correction

Canonical mutable event transition requiring new authority:

```text
ISSUED -> REVOKED = A-AUTHORITY-REVOKE
```

Single-use consumption:

```text
ISSUED -> CONSUMED
```

is part of the atomic use transaction of the authority itself.

`EXPIRED` and `STALE` are **derived usability predicates**, not discretionary state transitions:

```text
expired(now, not_after)
stale(current_bound_context, issued_context)
```

A verifier may materialize an audit record saying an authority was observed expired/stale, but no new authority is required to make time pass or a bound context change.

Once expired/stale, use is denied fail-closed. It cannot become usable again; a fresh authority must be issued.

## 4. ResearchFamily exhaustion correction

The earlier line:

```text
ACTIVE -> EXHAUSTED = A-PROGRAM-BUDGET
```

is superseded.

Correct semantics:

```text
family_exhausted
= derived mechanically from FamilyLifetimeLedger + frozen Family Charter stopping/error-control rule

ACTIVE -> EXHAUSTED
= A-ADJUDICATE recording that derived terminal fact
```

`A-PROGRAM-BUDGET` allocates/reserves budget; it does not adjudicate scientific-family lifecycle.

## 5. ResearchProgram authorization correction

The earlier shorthand:

```text
DRAFT -> AUTHORIZED = A-PROGRAM-CREATE + A-PROGRAM-BUDGET
```

means exactly:

```text
transition authority = A-PROGRAM-CREATE
mandatory prerequisite = successful A-PROGRAM-BUDGET reservation bound to the same Program/Family roots
```

There is one transition authority and one independently verified budget prerequisite; no anonymous composite token is created.

## 6. No new rights

This amendment does not add any implementation, research, W2/W3, production, merge, or broker authority.

```text
ARE-0 CLOSED = NO
ARE implementation = NOT AUTHORIZED
P001 = UNKNOWN
W2/W3 = CLOSED
production = CLOSED
merge = NOT AUTHORIZED
```
