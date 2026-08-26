# AHFMES ARE — Source Reuse & Worktree Hygiene Contract

Status: **FUTURE IMPLEMENTATION DESIGN RULE / NO CURRENT IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

## 1. Purpose

This document freezes a source-architecture rule for future AHFMES Autonomous Research Engine (ARE) implementation:

> **Reuse / patch / extend an existing Python module when its current semantic responsibility matches the new requirement. Create a new module only when the responsibility is genuinely new and cannot be added without corrupting the existing module boundary.**

The objective is to keep the repository and local worktree clean, auditable, and understandable. It does **not** authorize implementation now.

## 2. Core rule

Every future ARE implementation change must be classified before coding as exactly one of:

```text
EXTEND_EXISTING
ADAPT_EXISTING
NEW_MODULE_JUSTIFIED
RETIRE_AFTER_PROVEN_UNUSED
```

`NEW_MODULE_JUSTIFIED` is not the default.

A new source file requires a written justification answering:

```text
What responsibility is new?
Why does no current module own it?
Why would modifying an existing module violate cohesion or authority separation?
Where will the new module live?
Which old modules will consume it?
Does it duplicate any existing event/store/hash/memory/execution function?
```

If those questions cannot be answered, reuse an existing module instead.

## 3. Prohibited source-clutter patterns

Do not create repository clutter such as:

```text
orchestrator_v2.py
orchestrator_new.py
orchestrator_final.py
habitat_memory_old.py
learning_gate_copy.py
evidence_ledger_test2.py
foo_backup.py
foo_fixed.py
foo_latest.py
```

Do not keep temporary implementation copies, `.bak` source, scratch Python files, or abandoned parallel implementations in the tracked worktree.

Version history belongs in Git, not duplicated filenames.

## 4. Root-directory rule

The current AHFMES source tree is historically root-heavy. Future ARE implementation must **not continue scattering every new ARE concern into repository root**.

Rule:

```text
existing responsibility -> modify existing existing module in place

genuinely new ARE responsibility -> place under one bounded `are/` package
```

Conceptual future layout only:

```text
are/
    __init__.py
    authority.py
    evidence.py
    research_program.py
    critic.py
    governor.py
    ... only if justified by closed formal contracts
```

This is a layout policy, not implementation authority and not a frozen exact module list.

Tests for new ARE-only code should similarly be grouped under a bounded test namespace such as:

```text
tests/are/
```

rather than adding unrelated `test_are_*.py` files throughout the repository.

## 5. Existing source should remain the operational body

ARE is an extension/evolution of AHFMES, not a parallel bot.

Do not create a second copy of the operational system.

In particular, absent a later explicit architectural reason:

```text
NO second orchestrator
NO second executor stack
NO second broker adapter stack
NO second telemetry stack
NO second habitat-memory implementation
NO second freeze-policy implementation
NO second runtime-identity implementation
```

ARE components should integrate through existing ownership boundaries.

## 6. Preliminary source-reuse inventory

This inventory is preliminary engineering guidance derived from the current repository. Exact implementation mapping must be re-audited after ARE-0 closure and before implementation authority.

### `orchestrator.py`

Current role: active composition root wiring habitat perception/memory, confidence, execution planning, safety, telemetry, direction discovery, pattern memory/event infrastructure, LearningGate, freeze/runtime identity and executor lifecycle.

Future rule:

```text
REUSE / EXTEND
```

Do not create `are_orchestrator.py` merely to wire ARE. New ARE services should eventually be injected/wired from the existing orchestrator or from a narrowly scoped composition helper if size/cohesion audit requires it.

The operational execution loop remains owned by existing AHFMES.

### `habitat_memory.py`

Current role: habitat-level observation/evaluation memory, maturity, real/shadow outcomes, direction counters, MAE and intent/exit history.

Future rule:

```text
REUSE for habitat/market experience that belongs to habitat semantics.
DO NOT overload it with global scientific-governance registries.
```

Richer experience fields that naturally belong to a habitat/trade evaluation may extend this module, but Problem Registry, Research Contract, Evidence Ledger authority or Governor state should not be stuffed into HabitatMemory simply to avoid creating a file.

### `evaluation_writer.py`

Current role: bridge from position outcome to HabitatMemory evaluation.

Future rule:

```text
REUSE / EXTEND as an integration bridge where richer trade/decision experience is emitted.
```

Do not create a duplicate exit-to-memory writer if the existing bridge can be safely extended or adapted.

### `learning_gate.py`

Current role: LEARN vs FROZEN_EVAL boundary, freeze-integrity checking, mutation rejection and frozen evidence.

Future rule:

```text
REUSE its frozen-learning boundary.
DO NOT reinterpret it as the entire ARE authority system.
```

If ARE-0B ultimately requires a distinct trusted authority service, that is a genuinely new responsibility and may justify a bounded `are/authority.py`; it should interoperate with LearningGate rather than replace or duplicate it.

### `pattern_events.py`

Current role: frozen event dataclasses plus an append-only EventStore with monotonic IDs and transaction buffering/commit/rollback semantics.

Future rule:

```text
REUSE / GENERALIZE where safe before inventing a second event-store implementation.
```

ARE state/event needs stronger revision/CAS and authority semantics than the current Pattern EventStore provides. Future implementation must first decide whether to safely generalize/refactor the existing store or wrap its reusable mechanics. A second unrelated event log is prohibited without explicit justification.

### `pattern_recovery.py`

Current role: strict snapshot persistence/recovery, canonical JSON, checksum validation, high-watermark restoration and state validation.

Future rule:

```text
REUSE persistence/recovery patterns and primitives where semantics match.
```

Do not duplicate snapshot/recovery code merely because ARE uses a different object schema.

### `policy_contract.py`

Current role: active machine-readable policy contract, structural validation, canonical hashing/domain-hash primitives and policy identity semantics.

Future rule:

```text
REUSE canonicalization / domain-hash conventions where compatible.
```

Do not introduce an independent incompatible hashing convention for ARE objects without a formally audited reason.

### `freeze_snapshot.py`

Current role: content hashing of memory/shadow/pattern/policy state, complete freeze bundles, policy identity and training-run binding validation.

Future rule:

```text
REUSE content-addressing and frozen-bundle concepts.
```

ARE content-addressed candidate/proof identity should not reinvent existing canonical hashing mechanics if the same primitive is valid.

### `runtime_identity.py`

Current role: repository/runtime closure identity, reachable Python module discovery, tracked-source checks and bytecode-vs-source integrity checks.

Future rule:

```text
REUSE and EXTEND runtime/source closure when ARE becomes part of executable runtime.
```

Any new ARE package/module entering runtime must be included in the existing runtime-identity model rather than creating a parallel source-identity subsystem.

### `telemetry.py`

Current role: run-scoped observation/evaluation/trade telemetry with authority latching, canonical outbox identity, projection repair and shutdown evidence.

Future rule:

```text
REUSE / EXTEND for operational ARE telemetry when fields belong to the existing runtime telemetry contract.
```

If scientific governance requires a separate immutable Evidence Ledger, that ledger is not merely telemetry and may justify a separate ARE component. Do not create a duplicate general-purpose telemetry logger.

### `direction_discovery.py`

Current role: existing non-controlling direction discovery / telemetry capability based on accumulated real evaluation data.

Future rule:

```text
PRESERVE as an existing capability; do not replace merely because ARE introduces Research Brain.
```

Future ARE may wrap, evaluate, retire or evolve this capability through scientific governance, but it should not silently clone it into a new direction engine.

### `micro_executor.py`, `executor_factory.py`, broker/transport modules

Current role: micro-position lifecycle and paper/demo execution transport boundary.

Future rule:

```text
PRESERVE / REUSE as ACT-world execution kernel.
```

Research Brain / Critic / Governor must not create a parallel executor. Any future promoted policy reaches capital only through the existing controlled execution boundary unless a separately audited capability-evolution project explicitly replaces it.

## 7. Pre-implementation Source Reuse Audit

Before each implementation work package, engineer instructions must include a `SOURCE_REUSE_MAP`:

```text
Requirement / contract ID
Existing module inspected
Reuse classification
Reason
Exact files allowed to modify
New files requested, if any
New-file justification
Files explicitly prohibited
```

Example:

```text
ARE-1A state-event transition engine

pattern_events.py = ADAPT_EXISTING
learning_gate.py  = EXTEND_EXISTING where freeze integration is needed
policy_contract.py = REUSE HASH PRIMITIVE
runtime_identity.py = EXTEND_EXISTING only when runtime closure changes
are/state.py = NEW_MODULE_JUSTIFIED only if generic ARE state semantics cannot live cleanly in pattern_events.py
```

The exact answer above is illustrative, not pre-authorized implementation.

## 8. New-file budget

Every implementation work package should aim for the **minimum number of new modules consistent with clean separation of responsibility**.

A package with many new `.py` files is an audit smell and must explain why each is necessary.

However, file-count minimization must never override architectural separation. For example:

```text
Evidence Ledger
!= HabitatMemory

Governor authority
!= LearningGate freeze mode

Research Brain
!= Orchestrator execution loop
```

Do not create clutter, but do not collapse distinct trust domains into one giant file merely to reduce file count.

## 9. Legacy-file cleanup policy

Do not delete or move old Python files opportunistically inside a functional ARE implementation patch.

Reason: current runtime identity and source-map machinery depends on exact reachable files and source identity. A mass cleanup mixed with functional change makes audit and regression attribution harder.

Use this sequence:

```text
functional reuse/refactor
→ source audit
→ local regression/integration proof
→ identify truly unreachable/obsolete files
→ dedicated repository-hygiene authority/patch
→ verify runtime closure/source map
→ delete/relocate only proven-unused legacy files
```

Thus old source should be **reused first, proven obsolete second, cleaned third**.

## 10. No undocumented local cleanup

The local Antigravity worktree must mirror an exact audited GitHub SHA during formal tests.

Do not locally rename/delete old Python files to make the tree look cleaner while testing. Any cleanup must first be represented in GitHub source and audited.

## 11. Worktree target

Desired future structure:

```text
existing AHFMES operational modules
        +
small bounded `are/` package for genuinely new scientific responsibilities
        +
organized tests
        +
no duplicate historical source copies
        +
Git history as the version archive
```

The objective is **one evolving AHFMES codebase**, not an old bot plus a second ARE bot living beside it.

## 12. Current boundary

As of this record:

```text
ARE-0 external audit = NEXT
ARE implementation   = NOT AUTHORIZED
Source reuse mapping = DESIGN RULE ONLY
No Python source change is authorized by this document
```

This contract must be included in future engineer implementation instructions after a separate implementation authority is granted.
