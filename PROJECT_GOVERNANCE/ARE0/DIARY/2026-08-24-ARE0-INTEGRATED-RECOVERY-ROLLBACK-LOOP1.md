# 2026-08-24 — ARE-0 Integrated Recovery/Rollback Design — Adversarial Loop 1

## Authority / scope

- Repository: `Mziana/AHFMES-CHATGPT`
- Design branch: `codex/current-authority-docs`
- Immutable external-audit candidate remains: `081e0472a4322a83af148ee0b60e01a655b0fcbd`
- ARE-0 remains `CLOSED = NO`.
- No implementation, P001 research, production, W2/W3, AHFMES-NEW modification, or PR merge authority.

## Source architecture used

The integrated design was built from the current ARE-0A..0F formal contracts, the integrated Master V2, V25/V31 authority/noninterference generation, and the two accepted auditor seeds. Existing contracts already establish immutable Research Episodes, principal-level SoD, Governance Root/Trusted Gate Registry, content-addressed authority, Evidence Ledger exposure, Program Budget/search genealogy, Champion CAS, Capital Safety separation, and consequence-blind refinement release control.

## Design produced

### V1
`PROJECT_GOVERNANCE/AHFMES_ARE_0_INTEGRATED_RECOVERY_ROLLBACK_ARCHITECTURE_V1.md`

Commit: `fbb1cc91ba83fe35ba76732e5f032395adaf2246`

V1 introduced one integrated architecture rather than two patches:

```text
FACT -> AUTHORITY -> RELIANCE -> ACTION

OBSERVE -> ATTEST -> CONTAIN -> SELECT/RESUME
```

Core recovery mechanism:

```text
semantic idempotency key
!=
reliance idempotency key
```

Core rollback mechanism:

```text
frozen cause-observation contract
+
consequence-blind observation
+
precommitted fallback compatibility
```

## Loop 1 adversarial attack

Attacks included:

```text
authority invalidation after commit
same-subject replacement authority
old-authority replay
duplicate reliance
search/evidence-debt reset
hidden validation via recovery
stale downstream authority
concurrent recovery
root rotation during recovery
outcome-conditioned recovery
outcome-conditioned rollback query/source/retry
human/LLM diagnostic selection
latency/error side channel
post-outcome cause classification
fallback selection by historical performance
fallback-matrix mutation
emergency-flat -> champion escalation
stale champion rollback
recovery + rollback composition
cause exposure -> new research
rollback during capital activation
Safety-root rotation
UNKNOWN cause + attractive historical fallback
unrelated registry churn
```

## Loop 1 findings

Three real design clarifications were found and incorporated into V2:

### L1-01 — Historical invalidation temporal scope

A later authority invalidation must not silently rewrite the historical fact or all historical actions. Default semantics are:

```text
old authority = invalid for future reliance
historical fact/action record = immutable
```

Any stronger retrospective consequence requires a separate explicit governance rule.

### L1-02 — Recovery control-flow noninterference

It is not enough that the replacement evidence itself is historically clean. The path that discovers/admit/attests that evidence must also be consequence-blind.

Therefore recovery acquisition/admission/attestation is now explicitly subject to the same beneficiary-outcome noninterference discipline as V25 release control.

### L1-03 — Cause classification could itself become the optimizer

A frozen observation contract alone is insufficient if the observer can choose the cause taxonomy/classification after seeing the outcome.

V2 therefore freezes:

```text
cause taxonomy
cause classifier/rule
cause precedence/tie rule
```

before outcome exposure. Ambiguity becomes `UNKNOWN_CAUSE`, not a favorable interpretation.

## Results of Loop 1

Passed without additional correction:

```text
semantic/reliance idempotency separation
recovery search-debt inheritance
recovery evidence-exposure inheritance
stale downstream authority denial
concurrent recovery CAS
fallback performance selector exclusion
emergency-flat asymmetry
recovery/rollback authority separation
```

## Current design status

```text
V1 = superseded historical design
V2 = current successor design after Loop 1
Loop 1 = COMPLETE
External audit = REQUIRED
Implementation = NOT AUTHORIZED
```

## Next loop

Attack V2 specifically for second-order composition:

```text
reliance becomes a de facto authority
recovery invalidation laundering
cause classifier poisoning
fallback-matrix governance drift
Safety/Champion race
cross-episode evidence contamination
search-budget bypass through recovery
UNKNOWN starvation under repeated harmless churn
```

Do not declare the design stable until these attacks are attempted.
