# AHFMES ARE V0 — Formal Architecture / Contract Design Authority

Status: **ACTIVE FORMALIZATION AUTHORITY / DESIGN-ONLY / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**  
Repository: `Mziana/AHFMES-CHATGPT`

## 1. Explicit lead authorization

The lead/user instruction on 2026-08-20 is interpreted narrowly as authorization to **begin the prepared ARE project at its next legitimate gate**, not as permission to skip governance stages.

Canonical authority token:

```text
AUTHORIZE_AHFMES_ARE_V0_FORMAL_ARCHITECTURE_AND_CONTRACT_DESIGN_PLUS_ADVERSARIAL_AUDIT_ONLY
```

This authority opens the **formalization phase** defined by the accepted ARE V0 governance checkpoint.

It does **not** close `ARE-0`, does **not** authorize autonomous implementation, and does **not** authorize any trading-strategy search.

## 2. Exact allowed scope

The following work is authorized on the existing work branch only:

1. formal ARE architecture and contract design;
2. state-machine formalization and invariant design;
3. object/schema authority design;
4. Evidence Ledger semantics;
5. validation/holdout-consumption semantics;
6. full search-tree genealogy and research-budget accounting;
7. multiplicity accounting design;
8. Critic authority contract;
9. Governor/promotion contract design;
10. authority non-forgeability design;
11. capability-gap proof contract;
12. frozen-shadow lifecycle design;
13. rollback and immutable-descendant rules;
14. adversarial desk audit of the above;
15. governance/journal/status/flowchart updates necessary to preserve continuity;
16. creation of tracking issues/comments for this design phase.

## 3. Explicitly prohibited

```text
ARE runtime/source implementation     = PROHIBITED
ARE autonomous-research code          = PROHIBITED
new trading strategy implementation   = PROHIBITED
P001 manual solution search           = PROHIBITED
G1 rerun / retune                     = PROHIBITED
G2 rescue                             = NOT AUTHORIZED
W2/W3 access                          = PROHIBITED
Training/OOS                          = PROHIBITED
production modification               = PROHIBITED
AHFMES-NEW modification               = PROHIBITED
new work branch                       = PROHIBITED without separate approval
force push                            = PROHIBITED
PR #20 merge                          = NOT AUTHORIZED
live/demo capital experiment          = PROHIBITED by this authority
```

No code implementation authority may be inferred from successful formalization.

## 4. Primary adversarial closure targets

Formalization must explicitly attack and close, or return `CHANGES_REQUIRED` on, the five accepted high-risk surfaces:

### A01 — State-machine completeness

Every Problem, Hypothesis, Evidence, Research Contract, Experiment, Candidate, Capability, epistemic state, shadow state, and promotion state must have explicit legal transitions, terminal states, and fail-closed illegal-transition behavior.

### A02 — Authority non-forgeability

Research-owned data fields must never be sufficient to manufacture validation or promotion authority. Caller-supplied labels, status strings, tokens, sentinels, or reconstructed membership objects cannot substitute for verified gate output.

### A03 — Evidence-consumption semantics

The design must define what constitutes evidence exposure, how exposure is inherited across related lineages/descendants, when validation evidence loses independence, and how prospective evidence renews independent proof capacity.

### A04 — Full search-tree multiplicity / research-budget accounting

The design must account for the full genealogy of feature invention, thresholds, interactions, model families, subgroups, horizons, metrics, reformulations, descendants, capability additions, and validation exposures. Minting a new object ID must not reset scientific debt or budget.

### A05 — Promotion / Critic authority contract

The design must separate candidate creation, adversarial criticism, proof, and promotion. Promotion must be comparative versus champion and mechanical/deterministic wherever possible; Critic cannot rescue, retune, redefine success, or self-promote.

## 5. Required design principles

The following remain binding throughout this phase:

```text
THINK -> PROVE -> ACT
```

Direct `THINK -> ACT` remains prohibited.

Also binding:

- discovery != validation;
- no self-acceptance;
- information-time/as-of provenance;
- precommitted estimand and primary population;
- finite research budget;
- full genealogy multiplicity accounting;
- holdout evidence is consumable;
- rejected evidence is immutable;
- candidate identity is immutable during proof;
- modification after validation/shadow creates a descendant;
- `INVALID != REJECT`;
- `NO_RESULT` / `CURRENTLY_NON_PREDICTABLE` are valid outcomes;
- capability gap must itself be supported;
- uncertainty fails closed.

## 6. ARE-0 formalization deliverables

The design phase is expected to produce a bounded set of formal artifacts, including at minimum:

```text
ARE-0A — State Machines & Invariants
ARE-0B — Authority / Non-Forgeability Contract
ARE-0C — Evidence Ledger & Holdout-Consumption Contract
ARE-0D — Search Genealogy / Research Budget / Multiplicity Contract
ARE-0E — Critic / Governor / Promotion Contract
ARE-0F — Integrated Adversarial Audit & Closure Disposition
```

Flowcharts and human-readable rationale must accompany formal schemas where necessary.

## 7. Closure rule

`ARE-0 FORMAL CONSTITUTION = CLOSED` may be claimed only if **all** required formal contracts receive explicit adversarial closure with no unresolved high-severity governance loophole.

Allowed final dispositions for this phase:

```text
ACCEPT_ARE0_FORMAL_DESIGN_CLOSED
CHANGES_REQUIRED
ARE0_FORMALIZATION_INVALID
```

There is no partial implementation authority.

If accepted, the next possible phase would require a **separate implementation authority**. Acceptance of ARE-0 design alone does not authorize ARE-1/2/3/4 code.

## 8. Repository topology

Use the existing branch only:

```text
codex/current-authority-docs
```

PR #20 remains draft/open/unmerged unless separately authorized.

## 9. Seed problem firewall

`P001 — PROFIT GIVEBACK` remains a testcase specification only:

```text
STATUS = UNRESOLVED
ANSWER = UNKNOWN
```

This formalization phase may design how a future ARE would research P001, but it may not perform that research or propose a substantive trading answer.

## 10. Immediate next work

Begin with **ARE-0A State Machines & Invariants** and **ARE-0B Authority / Non-Forgeability Contract**, because weaknesses there can invalidate every later registry or scientific gate.

Only after those foundations survive adversarial review should exact evidence-consumption and search-budget mechanics be frozen.
