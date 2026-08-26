# AHFMES ARE-0 — Authority-Sensitive Object Inventory V29

Status: **CURRENT CLOSED-WORLD COMPANION / STRUCTURAL_GENERATION_S1 PATH ADOPTION / INHERITS V28 AS BASE + INTEGRATES COUNCIL RUN S1 CORRECTIONS (RTA-01/02/04) / NO IMPLEMENTATION AUTHORITY**

## Composition

```text
CURRENT_MACHINE = PROJECT_GOVERNANCE/ARE0/MACHINE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V29.md
BASE_INVENTORY = PROJECT_GOVERNANCE/ARE0/MACHINE/AHFMES_ARE_0_OBJECT_STATE_TOTALITY_REGISTER_V28.md
```

All inherited objects remain. The following register is exhaustive for the
V28 recovery and cause-observation additions, inherited as base under S1
path adoption together with the Council Run S1 additions (the
`EDGE_NONCE_CONSUMPTION_LEDGER` row; cross-object rules 2 and 6).

| Object | Exact key | Sole writer | States / terminal state | CAS and idempotency | UNKNOWN rule |
|---|---|---|---|---|---|
| `REFINEMENT_RELIANCE_INVALIDITY_EVENT_ROOT` | exact failed carrier `P` | derived, non-writable | `PROVEN`, `NOT_PROVEN`; `PROVEN` immutable | no write or replacement | absent/non-final proof is `NOT_PROVEN` for authority use |
| `REFINEMENT_PROSPECTIVE_RELIANCE_SUBJECT` | `D,S,P,invalidity-root,static-semantics-root` | derived, non-writable | one deterministic value | actor, VAR, retry, wall-clock and outcome identity excluded | malformed/ambiguous inputs produce no subject |
| `REFINEMENT_PROSPECTIVE_RELIANCE_RECEIPT` | exact recovery subject | exact V28 Edge 1 authority | `ABSENT`, `CANONICAL`, `INTEGRITY_DEFECT`; canonical immutable | atomic receipt plus VAR consumption; identical replay recognizes; conflict defects | no receipt means authority-sensitive `UNKNOWN` |
| `REFINEMENT_PROSPECTIVE_RELIANCE_VAR_CURRENT` | `D,S,P` and exact authority proposal | inherited authority issuer/gate | `CURRENT`, `EXPIRED`, `REVOKED`, `CONSUMED`, `INVALID` | one `EDGE_NONCE`; replacement binds predecessor | unknown currentness is `INVALID` for use |
| `REFINEMENT_PROSPECTIVE_RELIANCE_SOD_ROOT` | exact recovery subject | derived, non-writable | `VALID`, `INVALID`; terminal for issued proposal | no actor may self-repair root | unknown common control is `INVALID` |
| `EDGE_NONCE_CONSUMPTION_LEDGER` | `recovery subject, nonce` | exact Matrix V29 Edge 1 authority | `UNUSED`, `CONSUMED`; `CONSUMED` immutable | atomic with receipt append; identical replay recognizes; conflicting duplicate defects | absent/ambiguous state is treated as `CONSUMED` (fail-closed) |
| `ROLLBACK_CAUSE_OBSERVATION` | `rollback_id, source_event_id` | exact inherited R9-05 observation writer | `ABSENT`, `RECORDED`, `INTEGRITY_DEFECT`; recorded immutable | exact identical write recognizes; conflicting duplicate defects | unavailable/ambiguous cause remains `UNKNOWN`, never favorable |
| `ROLLBACK_CAUSE_OBSERVATION_SOURCE_UNIVERSE` | exact rollback episode | derived, non-writable | `COMPLETE`, `INCOMPLETE`, `INVALID` | canonical ordering and source identity only | not complete means no cause-based privilege |
| `ROLLBACK_POLICY_ROOT` | exact rollback policy generation | inherited policy authority only | `CURRENT`, `SUPERSEDED`, `INVALID` | no observation may write/mutate it | missing/ambiguous root blocks policy reliance |

## Cross-object rules

```text
1. A receipt contains references to semantic facts; it never duplicates or
   mutates semantic payload.
2. A cause observation cannot be consumed as an authority issuer, candidate
   selector, release-control input, capital permission, or policy-generation
   input for any future `ROLLBACK_POLICY_ROOT` generation.
3. A historical-invalidity proof and a prospective receipt are different
   objects; neither can rewrite the other.
4. Any `INTEGRITY_DEFECT`, missing source identity, or ambiguous ordering
   fails closed and leaves authority-sensitive action unavailable.
5. No object key includes actor, holder, issuer, VAR, retry count, outcome,
   PnL, candidate attractiveness, process, host, or scheduling preference.
6. `INTEGRITY_DEFECT` records are keyed to their exact subject/episode; they
   are non-contagious: a defect never mutates an existing canonical receipt,
   observation, or any unrelated object's state, and it grants no privilege.
```

## Firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
```
