# 2026-08-24 — ARE-0 Integrated Recovery/Rollback — Adversarial Loop 2

## Scope

Target: `PROJECT_GOVERNANCE/AHFMES_ARE_0_INTEGRATED_RECOVERY_ROLLBACK_ARCHITECTURE_V2.md`

Target design commit: `948f27cd5d4acbc0afc0d0d5a96a693f18d17aec`

The immutable external-audit candidate remains unchanged:

```text
081e0472a4322a83af148ee0b60e01a655b0fcbd
```

## Second-order attack set

This loop intentionally attacks the correction mechanisms themselves rather than repeating Loop 1 verbatim.

```text
1. RELIANCE becomes de-facto authority
2. historical invalidation laundering
3. outcome-conditioned invalidation discovery
4. cause-classifier poisoning
5. fallback-matrix governance drift
6. Safety/Champion race after cause attestation
7. observer/attester common-principal collapse
8. cross-episode evidence contamination
9. search-budget bypass through recovery
10. UNKNOWN starvation under harmless churn
11. recovery-trigger side channel
12. old champion revival through rollback/reliance composition
```

## Findings

### L2-01 — RELIANCE must be explicitly non-authoritative

The V2 design says Reliance cannot directly mint downstream privilege, but this must be stronger mechanically:

```text
PROSPECTIVE_RELIANCE_RECORD
must never be an issuer or authority class.
```

No gate may accept a Reliance record as a substitute for `A-VALIDATE`, `A-SHADOW`, `A-GOVERN`, `A-PROMOTE`, `A-CAPITAL-ACTIVATE`, or equivalent authority.

**Disposition:** ACCEPT as a required clarification.

### L2-02 — Historical invalidation itself can be outcome-conditioned

If the system only discovers an invalid historical authority after a favorable/unfavorable outcome because an operator chooses whether to run the invalidation investigation, the recovery path inherits the same control-flow defect.

Therefore the invalidation/discovery path must be separated into:

```text
fact of invalidity
+
independent invalidation discovery/attestation
+
prospective reliance decision
```

Outcome-conditioned invalidation discovery cannot be used to manufacture favorable reliance.

**Disposition:** ACCEPT.

### L2-03 — Cause classifier poisoning

A frozen cause taxonomy is insufficient if the classifier/model used to assign cause classes can be updated after observing outcomes or trained on outcome-selected examples.

The classifier identity, training/provenance root, decision rule, and version must therefore be frozen for the active rollback episode. Material classifier change creates a new episode and inherits exposure/debt.

**Disposition:** ACCEPT.

### L2-04 — Fallback matrix drift

A fallback compatibility matrix can be frozen initially but become stale before rollback if Safety/Champion/Deployment context changes.

Therefore rollback authority must bind:

```text
fallback_matrix_root
fallback_matrix_generation
current Safety root
current Champion Registry generation
current Deployment Context
```

A matrix change makes existing fallback authority stale. Safety containment remains available; strategic fallback selection is denied until fresh authority exists.

**Disposition:** ACCEPT.

### L2-05 — Observer/attester common-control collapse

The V2 wording “where existing SoD requires it” is too permissive for a fallback-unlocking cause attestation.

For any cause attestation that can unlock a non-flat fallback:

```text
observer principal != attester principal
observer trust domain != attester trust domain
common-control relation must be denied
```

Emergency flat does not require the attestation if Safety independently authorizes containment.

**Disposition:** ACCEPT.

## Attacks that remained closed

```text
cross-episode evidence contamination
search-budget reset through recovery
UNKNOWN starvation caused solely by unrelated registry churn
stale champion after rollback
recovery/rollback composition privilege escalation
```

## Important positive-liveness result

The design retains a safe positive path:

```text
cause unknown
=> Safety can still FLAT
```

Therefore cause-observation failure does not have to block risk containment.

Likewise:

```text
authority invalidated
=> historical fact preserved
=> later independent valid authority
=> prospective reliance can recover
```

This is the desired liveness asymmetry.

## Required V3 integrated changes

The next integrated design revision must make these explicit in the main architecture, not as optional implementation notes:

```text
R1 RELIANCE_NON_AUTHORITY theorem
R2 outcome-independent invalidation discovery
R3 frozen cause-classifier provenance
R4 fallback matrix generation/currentness binding
R5 strict observer/attester separation for non-flat fallback
```

No implementation should begin before those are incorporated and attacked again.
