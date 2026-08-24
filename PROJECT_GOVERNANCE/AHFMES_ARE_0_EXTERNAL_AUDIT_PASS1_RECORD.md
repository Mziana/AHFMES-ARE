# AHFMES ARE-0 — External Adversarial Audit Pass 1 Record

Status: **EXTERNAL AUDIT COMPLETED / CHANGES_REQUIRED / HISTORICAL AUDIT EVIDENCE**  
Effective date: **2026-08-20**

## 1. Subject audited

Normative package subject:

```text
5eb148bf8a7aa554e3a762df44247e8c739a4064
```

Audit handoff/live head at the time of the reviews:

```text
3002d2c8c9538b4d98788a5cbdb2912e173600c0
```

The later source-reuse workflow record did not alter the normative scientific architecture under audit.

## 2. External disposition

Two independent external adversarial reviews returned the same top-level disposition:

```text
EXTERNAL AUDIT = CHANGES_REQUIRED
ARE0_FORMALIZATION_INVALID = NO
ACCEPT_ARE0_FORMAL_DESIGN_CLOSED = NO
ARE-0 CLOSED = NO
ARE IMPLEMENTATION AUTHORITY = NO
P001 = UNKNOWN / UNTOUCHED
W2/W3 = CLOSED
PRODUCTION = CLOSED
MERGE = NOT AUTHORIZED
```

Both reviews explicitly recognized that first-generation blockers had materially improved; the new findings were deeper global-governance issues rather than a collapse of the overall architecture direction.

## 3. External review A — seven blocking families

```text
EXT-ARE0-01 STATE_TRANSITION_COVERAGE_STILL_INCOMPLETE
EXT-ARE0-02 PROMOTION_STATE_REENTERS_SCIENTIFIC_SEMANTICS
EXT-ARE0-03 PROBLEM_ROOT_IDENTITY_AMBIGUITY
EXT-ARE0-04 PROGRAM_RESET_AND_FAMILY_META_BUDGET_GAP
EXT-ARE0-05 SEARCH_COMPLETENESS_PROOF_HAS_NO_TRUSTED_OBSERVATION_BOUNDARY
EXT-ARE0-06 EVIDENCE_IDENTITY_VS_ATTESTATION_COLLAPSE
EXT-ARE0-07 CAPITAL_SAFETY_VETO_CAN_BE_MISCLASSIFIED_AS_SCIENTIFIC_REJECT
```

Key required corrections included exhaustive transition matrices, scientific/promotion orthogonality, immutable Problem definition root plus append-only history root, family-lifetime error/search budget, trusted search/evaluation choke point, EvidenceSnapshot/attestation separation, and safety-veto deployment disposition.

## 4. External review B — six blocking families

```text
ARE-X01 UNMEDIATED_EVIDENCE_SEARCH_SIDE_CHANNEL
ARE-X02 WORLD3_AUTHORITY_MATRIX_IS_NOT_TOTAL
ARE-X03 PROGRAM_RESTART_META_P_HACKING
ARE-X04 STATE_MACHINE_TOTALITY_NOT_CLOSED
ARE-X05 UNRELATED_SUPPORTED_TOO_POWERFUL_WITHOUT_FORMAL_POSITIVE_STANDARD
ARE-X06 STATE_ADAPTATION_VS_POLICY_ADAPTATION_HAS_NO_MECHANICAL_BOUNDARY
```

This review independently confirmed the hidden-search and cross-Program multiplicity risks, then added total World-3 authority ownership, a positive unrelatedness proof contract, and a mechanical boundary for decision-relevant mutable online state.

## 5. Normalized correction families

Because the reviews overlap, the canonical correction tracker is Issue #22 and uses:

```text
EC-01 state-machine totality / repeatable proof episodes
EC-02 scientific/promotion/deployment orthogonality
EC-03 Problem definition root vs history root
EC-04 total authority ownership + Program/Family authorities
EC-05 family lifetime meta-budget / cross-Program renewal
EC-06 trusted outcome-access closure + search instrumentation
EC-07 EvidenceSnapshot / attestations / prospective isolation
EC-08 positive unrelatedness theorem
EC-09 decision-relevant mutable state boundary
EC-10 correction-package/re-audit integrity
```

## 6. What the external audits accepted as materially improved

The reviews did not reopen already-corrected first-generation findings such as:

```text
archive != scientific disposition
Experiment integrity PASS != scientific success
Problem history via immutable Research Episodes
candidate mutation -> descendant
revision + previous-event hash + CAS
Governance Root / Trusted Gate Registry
canonical and transitive content identity
verify-at-use freshness
single-use promotion
stale Champion CAS
human/auditor evidence contamination
STRICT_BLIND != LIVE_FROZEN
contract descendant != fresh contract budget
```

These remain subject to re-audit but were not the reason for Pass-1 `CHANGES_REQUIRED`.

## 7. Correction lineage

Bounded correction work after Pass 1 includes:

```text
7e368eddf54ecf600c0b480f5d55a91bda085f5e
  external audit correction package

5ca7e4a4dd71a476642c0982ed25f68d30e441ee
  initial total authority/transition matrix

659ac0f6b9658e11388ba3ab181c1979fb3ef899
  internal correction of anonymous authority gaps

b734ec71ebdff416f37492ab787631d222a9b276
  closed-world authority-sensitive object state totality register

e5c76996b22e622d28f1f8c9dd32fa29cd4cead2
  amendment for capital deactivation, authority revocation and residual totality gaps

000581fd1086e3d1e3f47243d42329cf29e474a6
  internal Architect -> Red-Team -> Scientific-Governor correction review
```

No entry in this lineage authorizes implementation.

## 8. Current scientific firewall

```text
P001 substantive research = NOT AUTHORIZED
G1 rerun/retune = PROHIBITED
G2 = NOT AUTHORIZED
W2/W3 = CLOSED
ARE Python implementation = NOT AUTHORIZED
production = CLOSED
AHFMES-NEW = CLOSED
PR #20 merge = NOT AUTHORIZED
```

## 9. Next gate

```text
EXTERNAL RE-AUDIT OF THE CORRECTED ARE-0 PACKAGE
```

The re-audit must not assume internal correction is correct. It should attempt concrete exploit paths again.
