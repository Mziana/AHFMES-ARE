# AHFMES ARE-0 — Canonical Authority & Transition Matrix V30

Status: **SOLE CURRENT MACHINE SOURCE / STRUCTURAL_GENERATION_S1 / INHERITS V29 AS BASE + INTEGRATES IMPACT-ATTACK CORRECTIONS (T1-T5, IA3-01) / NO IMPLEMENTATION AUTHORITY**

## Composition

```text
BASE_MATRIX_V29 = PROJECT_GOVERNANCE/ARE0/MACHINE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V29.md
V30 > V29 > all inherited matrix versions
```

V30 inherits every V29 clause as its base, integrates the internal impact-attack
corrections below (Council-grade triage of subject c2ef649), and adds no
capital, execution, broker, Safety, evidence-admission, semantic classification,
or promotion authority.

## Integrated corrections (binding on all implementations)

### IC-1 (T1) — External normative-root anchor

Manifest validity at any subject `S` additionally requires: the published
`NORMATIVE_ROOT` for the current generation (recorded in this wave's SA-11 QAO
ledger and re-published at every candidate freeze) equals the locally recomputed
root under the canonical algorithm. Mismatch => all resolution fails closed
before any member is consulted. The QAO record supplies the published value;
authority derives from the reconciliation obligation, never from the record.

### IC-2 (T2) — Recognition is a gated read

Recognition of an existing byte-identical receipt is a transition-read that
MUST re-evaluate ALL Edge 1 preconditions at use time, including VAR
CURRENT/not-revoked/not-expired and holder/RoleManifest currency. Failure =>
conservative `UNKNOWN`; a stale-authority replay can never surface a canonical
receipt downstream.

### IC-3 (T4) — Atomic UNUSED issuance

The `EDGE_NONCE_CONSUMPTION_LEDGER` entry (`UNUSED`) is created atomically by
the issuer in the SAME transaction that issues the VAR. A VAR whose ledger
entry is absent => the VAR itself is `INVALID` (no orphan VAR).

### IC-4 (IA3-01) — Deterministic crash finalization

Effect order for Edge 1 commits is receipt-append FIRST, nonce-consumption
SECOND, both inside one transaction; a recovery procedure exposes one
idempotent finalize step that forces any `UNUSED` entry paired with an appended
receipt to `CONSUMED`, deriving decisions ONLY from ledger+VAR state. Behavior
never depends on unobserved external facts.

### IC-5 (T5) — Writer binding for Edge 2

Every `ROLLBACK_CAUSE_OBSERVATION` write binds `(holder-control-id,
RoleManifest-generation)` of the observation writer, validated at use against
the inherited R9-05 authority registry; unbound or stale writer identity =>
write denied (fail-closed).

### IC-6 (T7 clarification) — Lineage by manifest table

Composition/base pointers written before S1 (absolute legacy paths) carry no
resolution power; inheritance resolves through the Manifest member table only.

Edge 1 and Edge 2 bodies from V29 remain in force with these integrations;
where wording conflicts, V30 prevails.

## Firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
```
