# AHFMES ARE-0 — Authority-Sensitive Object Inventory V30

Status: **CURRENT CLOSED-WORLD COMPANION / INHERITS V29 AS BASE + INTEGRATES IMPACT-ATTACK CORRECTIONS (T3, T6) / NO IMPLEMENTATION AUTHORITY**

## Composition

```text
CURRENT_MACHINE = PROJECT_GOVERNANCE/ARE0/MACHINE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V30.md
BASE_INVENTORY = PROJECT_GOVERNANCE/ARE0/MACHINE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V29.md
```

All inherited objects remain. Additions below integrate impact-attack
corrections T3 and T6 under S1 path adoption.

| Object | Exact key | Sole writer | States / terminal state | CAS and idempotency | UNKNOWN rule |
|---|---|---|---|---|---|
| `REFINEMENT_RELIANCE_INVALIDITY_EVENT_ROOT` | exact failed carrier `P` | derived, non-writable | `PROVEN`, `NOT_PROVEN`; `PROVEN` immutable | no write or replacement | absent/non-final proof is `NOT_PROVEN` for authority use |
| `REFINEMENT_PROSPECTIVE_RELIANCE_SUBJECT` | `D,S,P,invalidity-root,static-semantics-root` | derived, non-writable | one deterministic value | actor, VAR, retry, wall-clock and outcome identity excluded | malformed/ambiguous inputs produce no subject |
| `REFINEMENT_PROSPECTIVE_RELIANCE_RECEIPT` | exact recovery subject | exact V29 Edge 1 authority | `ABSENT`, `CANONICAL`, `INTEGRITY_DEFECT`; canonical immutable | atomic receipt plus VAR consumption; identical replay recognizes ONLY after full precondition re-evaluation (IC-2); conflict defects | no receipt means authority-sensitive `UNKNOWN` |
| `REFINEMENT_PROSPECTIVE_RELIANCE_VAR_CURRENT` | `D,S,P` and exact authority proposal | inherited authority issuer/gate; issuance atomically creates paired ledger entry (IC-3) | `CURRENT`, `EXPIRED`, `REVOKED`, `CONSUMED`, `INVALID`; absent ledger pair => `INVALID` | one `EDGE_NONCE`; replacement binds predecessor | unknown currentness is `INVALID` for use |
| `EDGE_NONCE_CONSUMPTION_LEDGER` | `recovery subject, nonce` | exact Matrix V29/V30 Edge 1 authority | `UNUSED`, `CONSUMED`; `CONSUMED` immutable; crash finalization per IC-4 derives ONLY from this object + VAR state | atomic with receipt append; finalize idempotent; conflicting duplicate defects | absent/ambiguous state is treated as `CONSUMED` (fail-closed) |
| `REFINEMENT_PROSPECTIVE_RELIANCE_SOD_ROOT` | exact recovery subject | derived, non-writable | `VALID`, `INVALID`; terminal for issued proposal | no actor may self-repair root | unknown common control is `INVALID` |
| `ROLLBACK_CAUSE_OBSERVATION` | `rollback_id, source_event_id` | R9-05 observation writer bound to `(holder-control-id, RoleManifest-generation)` validated at use (IC-5) | `ABSENT`, `RECORDED`, `INTEGRITY_DEFECT`; RECORDED immutable; **INTEGRITY_DEFECT is TERMINAL for its key** — later attempts require a NEW `rollback_id` episode (T6) | exact identical write recognizes after full precondition check; different payload for same key => defect record, terminal | unavailable/ambiguous cause remains `UNKNOWN`, never favorable |
| `ROLLBACK_CAUSE_OBSERVATION_SOURCE_UNIVERSE` | exact rollback episode | derived, non-writable | `COMPLETE`, `INCOMPLETE`, `INVALID` | canonical ordering and source identity only | not complete means no cause-based privilege |
| `ROLLBACK_POLICY_ROOT` | exact rollback policy generation | inherited policy authority only; generation writes bind writer identity per IC-5 pattern | `CURRENT`, `SUPERSEDED`, `INVALID` | no observation may write/mutate it | missing/ambiguous root blocks policy reliance |
| `EDGE_INTERFERENCE_EVIDENCE` | `rollback_id, attempt-sequence` | R9-05 observation writer (same bound identity as IC-5) | append-only `DENIED_ATTEMPT` records; immutable | append-only; no read grants privilege | presence never creates privilege; absence proves nothing favorable |

## Cross-object rules

```text
1. A receipt contains references to semantic facts; it never duplicates or
   mutates semantic payload.
2. A cause observation or interference-evidence record cannot be consumed as
   an authority issuer, candidate selector, release-control input, capital
   permission, or policy-generation input for any future generation.
3. A historical-invalidity proof and a prospective receipt are different
   objects; neither can rewrite the other.
4. Any `INTEGRITY_DEFECT`, missing source identity, or ambiguous ordering
   fails closed; defects are keyed to their subject/episode, terminal for that
   key, non-contagious, and grant no privilege.
5. No object key includes actor, holder, issuer, VAR, retry count, outcome,
   PnL, candidate attractiveness, process, host, or scheduling preference;
   writer BINDING fields are validation inputs, not key material.
6. Recognition/replay of any existing object re-runs full currentness
   preconditions (stale-authority replay can never surface canonical state).
```

## Firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
```
