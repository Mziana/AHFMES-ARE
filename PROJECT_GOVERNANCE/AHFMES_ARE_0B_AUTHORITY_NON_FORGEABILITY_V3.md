# AHFMES ARE-0B — Authority, Separation of Duty, Root of Trust, and Non-Forgeability V3

Status: **SECOND-PASS CORRECTED FORMAL DESIGN / INTERNAL RED-TEAM PASS / EXTERNAL AUDIT REQUIRED / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

This is the normative ARE-0B draft for external review.

## 1. Purpose

Prevent Research Brain, candidate/model/code, Critic, Governor, serialized state, or any one principal from fabricating the right to validate, promote, activate capital, or rewrite canonical scientific state.

Core theorem:

```text
LOCAL DATA != AUTHORITY
WELL-FORMED RECORD != TRUST
AUTHORITY CLASS SEPARATION != SEPARATION OF DUTY
```

All three distinctions are mandatory.

## 2. Trust worlds

```text
WORLD 1 THINK   = research creation/adaptation
WORLD 2 PROVE   = contract/evidence/validation/Critic/Governor
WORLD 3 ACT     = promotion registry/capital safety/execution
```

No WORLD 1 principal may unilaterally create a WORLD 3 state transition.

## 3. Authority classes

```text
A-CREATE
A-CONTRACT-DRAFT
A-LOCK
A-DISCOVERY
A-EVIDENCE-RESERVE
A-EVIDENCE-RELEASE
A-VALIDATE
A-SHADOW
A-CRITIC
A-GOVERN
A-PROMOTE
A-ROLLBACK
A-CAPABILITY
A-CAPITAL-ACTIVATE
A-EMERGENCY-FLAT
```

Each class has a versioned schema specifying mandatory bindings. Caller cannot omit required bindings.

## 4. Trust domains

```text
TD-RESEARCH
TD-CONTRACT
TD-EVIDENCE
TD-VALIDATION
TD-CRITIC
TD-GOVERNOR
TD-PROMOTION
TD-CAPITAL-SAFETY
TD-CHAMPION-REGISTRY
TD-EXECUTION
TD-AUDIT
TD-GOVERNANCE-ROOT
```

## 5. Separation-of-duty rules

For one candidate/contract/promotion episode, the same principal identity MUST NOT combine:

```text
A-DISCOVERY + A-VALIDATE
A-DISCOVERY + A-CRITIC
A-DISCOVERY + A-GOVERN
A-DISCOVERY + A-PROMOTE
A-DISCOVERY + A-CAPITAL-ACTIVATE
A-VALIDATE  + A-CRITIC
A-VALIDATE  + A-GOVERN
A-VALIDATE  + A-PROMOTE
A-CRITIC    + A-GOVERN
A-CRITIC    + A-PROMOTE
A-GOVERN    + A-PROMOTE
A-PROMOTE   + A-CAPITAL-ACTIVATE
A-PROMOTE   + broker execution mutation power
```

Different episodes may reuse service software, but principal identity/authority context must preserve the separation for the decision under review.

A physical process hosting multiple services must still expose distinct principals/capabilities; process co-location is not permission collapse.

## 6. Principal Role Manifest

```yaml
principal_id: ...
trust_domain_id: ...
allowed_authority_classes: [...]
forbidden_combinations: [...]
issuer_scope: [...]
manifest_revision: ...
manifest_root_hash: ...
valid_from_utc: ...
valid_until_utc: ...
```

Role Manifest is content-addressed and verified by a trusted registry.

Research Brain cannot edit its own Role Manifest.

## 7. Governance Root Manifest

ARE needs a bootstrap root above the Trusted Gate Registry.

Conceptual immutable root:

```yaml
governance_root_id: AGR-...
scientific_constitution_root_hash: ...
capital_safety_charter_root_hash: ...
trusted_gate_registry_root_hash: ...
role_registry_root_hash: ...
governance_revision: ...
change_authority_class: HUMAN/GOVERNANCE EXTERNAL TO ARE RESEARCH
```

Rules:

```text
ARE Research cannot mint/change Governance Root
Critic cannot mint/change Governance Root
Governor cannot mint/change Governance Root
Promotion Gate cannot mint/change Governance Root
```

Changing constitutional trust roots is a separate explicit governance operation outside ordinary autonomous research.

Exact human signing/credential technology is implementation work; the topology is not.

## 8. Trusted Gate Registry

Each issuing gate is content-addressed:

```yaml
gate_id: ...
gate_root_hash: ...
issuer_principal_id: ...
issuer_role_manifest_hash: ...
allowed_authority_classes: [...]
mandatory_binding_schema_hash: ...
constitution_root_hash: ...
gate_registry_generation: N
valid_from_utc: ...
revoked_at_utc: null
```

A friendly name `GATE-V1` is never authority without exact root verification.

## 9. Verification chain

A usable authority capability must pass:

```text
Governance Root current
-> Trusted Gate Registry current
-> gate root current/not revoked
-> issuer Role Manifest current
-> issuer allowed requested authority class
-> mandatory bindings exact
-> subject/context hashes exact
-> freshness snapshots current
-> nonce/lifetime valid
```

A YAML/JSON row copied from storage is inert until this chain verifies.

## 10. Canonical content identity

Normative canonicalization family:

```text
AHFMES_CANONICAL_OBJECT_V1
```

Rules:

```text
UTF-8
Unicode NFC
map keys canonical lexicographic order
integer canonical decimal form
scientific decimals canonical decimal STRING representation
no binary float serialization in authority identity
UTC RFC3339 Z timestamps with schema-defined precision
NaN/Infinity prohibited
binary artifacts referenced by SHA-256 + byte length
ordered arrays preserve order
scientific sets sort canonically
mutable aliases prohibited in proof closure
```

## 11. Domain-separated hashes

```text
SHA256("AHFMES:" || domain_tag || ":V1\n" || canonical_bytes)
```

Required distinct tags include:

```text
CANDIDATE_ROOT
RESEARCH_CONTRACT
EVIDENCE_SNAPSHOT
EVIDENCE_MANIFEST
SEARCH_TREE
SEARCH_DEBT
VALIDATION_FAMILY
PROOF_BUNDLE
PROMOTION_GATE_SPEC
GATE_MANIFEST
ROLE_MANIFEST
CONSTITUTION
CAPITAL_SAFETY
DEPLOYMENT_CONTEXT
CHAMPION_REGISTRY_EVENT
```

Cross-type hash substitution is invalid.

## 12. Transitive content closure

At proof boundary, candidate/model/capability identity recursively includes all material dependencies by content hash.

Forbidden material reference:

```text
models/current.pkl
config/latest.json
branch HEAD
latest feature registry
```

Required:

```text
exact model bytes hash
exact policy spec hash
exact feature schema hash
exact parameters hash
exact execution semantics hash
exact capability dependency closure
exact contract root
exact genealogy root
```

No mutable pointer can change bytes while keeping an old authority valid.

## 13. Verified Authority Record V3

Conceptual:

```yaml
authority_id: ...
authority_class: ...
subject_root_hash: ...
subject_type: ...
transition_binding:
  expected_lifecycle: ...
  expected_disposition: ...
  expected_state_revision: ...
  expected_previous_event_hash: ...
context_bindings:
  research_contract_root_hash: ...
  research_family_root: ...
  claim_family_root: ...
  evidence_manifest_root_hash: ...
  evidence_ledger_revision: ...
  evidence_ledger_snapshot_hash: ...
  search_tree_root_hash: ...
  search_debt_revision: ...
  validation_family_root_hash: ...
  constitution_root_hash: ...
  governance_root_revision: ...
issuer:
  gate_root_hash: ...
  principal_id: ...
  role_manifest_root_hash: ...
usage:
  single_use: true|false per authority schema
  nonce: ...
  issued_at_utc: ...
  not_after_utc: ...
proof: ...
```

Mandatory fields are authority-class specific but fixed by the gate schema, not caller preference.

## 14. Freshness theorem

Authority is checked at issuance AND at use.

Any bound dynamic context change makes unused authority stale unless an atomic reservation explicitly protects that context.

Examples:

```text
Evidence Ledger exposure changed -> old A-VALIDATE stale
search debt changed -> old validation/promotion proof stale
candidate root changed -> authority inapplicable
constitution changed -> authority stale unless explicit compatibility migration
champion changed -> old A-PROMOTE stale
safety kernel changed -> old promotion/activation stale
```

## 15. Authority use transaction

For single-use authority:

```text
verify trust chain
verify content roots
verify state revision
verify ledger/search/registry snapshots
verify nonce UNUSED
then one atomic transaction:
  nonce -> CONSUMED
  transition event -> APPENDED
  affected canonical revisions -> ADVANCED
```

Partial success is not allowed.

Crash recovery treats transition as not committed unless an exact transaction commit record proves all required effects committed.

## 16. Evidence reservation exception to freshness

An Evidence Reservation may atomically lock a validation episode against conflicting use under ARE-0C.

In that case A-VALIDATE binds the Reservation root and ledger reservation revision.

Any exposure inconsistent with the reservation invalidates or blocks authority.

The reservation cannot be caller-created; it requires TD-EVIDENCE authority.

## 17. Search-debt freshness

Proof authority binds:

```text
research_family_root
search_tree_root_hash
search_debt_root_hash
search_debt_revision
program_budget_envelope_root_hash
validation_family_root_hash
```

Adding hidden candidate/search actions after proof invalidates freshness.

## 18. Critic authority

TD-CRITIC may only produce bounded Critic dispositions.

It cannot:

```text
issue A-GOVERN
issue A-PROMOTE
change candidate
change contract
change evidence role
relabel related claim unrelated
rescue subgroup/metric/threshold
```

Critic-generated new ideas create research leads with contamination/search ancestry.

## 19. Governor authority

TD-GOVERNOR may adjudicate a frozen Proof Bundle against frozen PromotionGateSpec.

It cannot:

```text
change PromotionGateSpec after outcomes
mint final promotion authority
activate capital
edit candidate
```

Governor output is prerequisite evidence for TD-PROMOTION, not the promotion transaction itself.

## 20. Promotion authority

A-PROMOTE must bind exact:

```text
challenger root
expected current champion root
expected champion registry generation
expected registry previous-event hash
deployment slot
deployment-context root
Capital Safety root
execution-contract root
Proof Bundle root
PromotionGateSpec root
rollback target root
single-use nonce
```

No context field may be supplied at use time to widen an already-issued authority.

## 21. Champion compare-and-swap

```text
if current_champion != expected -> DENY_STALE_PROMOTION
if registry_generation != expected -> DENY_STALE_PROMOTION
if previous_event_hash mismatch -> DENY_FORK
if nonce used -> DENY_REPLAY
else atomically consume authority + write registry transition
```

Concurrent A->B and A->C promotions cannot both succeed.

## 22. Capital activation separation

Champion registry promotion is scientific/deployment selection state.

Broker/capital activation requires separate:

```text
A-CAPITAL-ACTIVATE
TD-CAPITAL-SAFETY
execution environment checks
```

A-PROMOTE cannot submit broker orders.

## 23. Emergency authority

A-EMERGENCY-FLAT may stop/flat under Capital Safety.

It may NOT:

```text
promote new strategy
change scientific result
erase loss evidence
reset champion history
```

Emergency safety is asymmetric: it may reduce/stop risk without creating edge.

## 24. Gate/constitution migration

Material root changes require a Governance Root transition.

Migration manifest specifies:

```text
old root
new root
why
which outstanding authorities are revoked
which exact compatibility proofs, if any, preserve authority
migration timestamp/revision
```

Default:

```text
unused outstanding proof authority -> REISSUE REQUIRED
```

## 25. Local compromise assumption

ARE-0B does not assume all future local code is honest.

Threat model includes compromised or buggy Research Brain/candidate code attempting to forge data-plane records.

If the entire Governance Root / authority store / Capital Safety trust boundary is fully compromised by an external attacker with root-machine control, cryptographic/process choices determine residual defense. That operational security problem is implementation scope.

Formal architecture requires that ordinary Research-owned code does NOT possess those roots.

## 26. Three-role second-pass attacks

Internal Red-Team specifically re-attacked:

```text
1 same principal owns Validation + Critic
2 same principal owns Governor + Promotion
3 same principal owns Promotion + Capital Activation
4 fake VAR rooted only in gate friendly name
5 Research modifies its Role Manifest
6 Research modifies Gate Registry
7 mutable model path behind frozen candidate
8 hash ambiguity via floats/order/Unicode
9 stale validation after Evidence Ledger change
10 stale proof after hidden search action
11 concurrent A->B / A->C champion race
12 replay promotion in another deployment slot
13 changed Safety Kernel after proof
14 archive/reload single-use authority replay
15 Critic creates rescue and self-validates it
```

V3 explicitly denies all fifteen by trust-domain, root, content, freshness, or CAS semantics.

## 27. External audit obligations

Auditor should attempt to construct a usable authority when one of these is false:

```text
trusted issuer
role separation
exact subject hash
exact contract
exact ledger snapshot
exact search debt
exact state revision
exact champion generation
exact deployment context
exact safety version
unused nonce
```

If any such forged/stale authority can transition canonical state, ARE-0B remains blocking.

## 28. Current disposition

```text
ARE-0B V3
= SECOND-PASS CORRECTED FORMAL DESIGN
= INTERNAL RED-TEAM PASS
= READY FOR EXTERNAL ADVERSARIAL AUDIT
= NOT CLOSED
= NO IMPLEMENTATION AUTHORITY
```
