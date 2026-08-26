# AHFMES ARE-0 — External Re-Audit Pass 3 Filtered Record

Status: **PASS 3 = CHANGES_REQUIRED / FILTERED INTO FINAL ARE-0 CLOSURE BATCH / NO IMPLEMENTATION AUTHORITY**  
Date: **2026-08-20**

## 1. Exact audited subject

```text
b7abdbb71c35b188abdb6d6965a8224a5de82696
```

The external reports were treated as adversarial inputs, not automatic truth. No claim of auditor independence is inferred beyond what each report itself establishes.

Pass-3 disposition remains:

```text
CHANGES_REQUIRED
ARE0_FORMALIZATION_INVALID = NO
ARE-0 CLOSED = NO
IMPLEMENTATION AUTHORITY = NO
P001 = UNKNOWN / UNTOUCHED
W2/W3 = CLOSED
PRODUCTION = CLOSED
MERGE = NO
```

## 2. Filtering method

Each reported exploit was classified only after independent contract analysis:

```text
REPRODUCE AGAINST CURRENT MATRIX
-> CHECK WHETHER PATH IS LITERALLY LEGAL OR AMBIGUOUS
-> CHECK GLOBAL SCIENTIFIC/AUTHORITY CONSEQUENCE
-> MERGE DUPLICATE FINDINGS
-> ATTACK THE PROPOSED FIX
-> DISPOSITION
```

Allowed finding dispositions:

```text
ACCEPT_AS_BLOCKER
ACCEPT_WITH_MODIFICATION
MERGE_WITH_EXISTING_FINDING
DEFER_TO_IMPLEMENTATION
REJECT_FALSE_POSITIVE
```

## 3. Filtered Pass-3 blocker families

### P3F-01 — RESEARCH FAMILY IDENTITY / PROBLEM-RELABEL / SHARED CAS

Disposition: **ACCEPT_WITH_MODIFICATION**

The reports correctly expose two coupled defects:

1. `first registered family for exact Problem definition` can be abused by outcome-motivated Problem reformulation to obtain a fresh family lifetime ledger;
2. the Matrix refers to a family-registry generation but does not define a canonical authority-sensitive shared CAS registry, allowing concurrent first-family claims.

Required closure invariant:

```text
new Problem ID / wording / problem_definition_root
!= new statistical life
```

Outcome-motivated or descendant Problems default to the existing related Research Family unless a valid pre-outcome independent relation decision grants distinct-family privilege.

A canonical `ResearchFamilyRegistry` must own the single-valued assignment/CAS surface.

### P3F-02 — RELATION DECISION UNIQUENESS

Disposition: **ACCEPT_AS_BLOCKER**

Pre-outcome timing alone is insufficient if multiple RelationDecision objects can exist for the same canonical relation key and a favorable one is selected later.

Required closure invariant:

```text
RELATION_KEY
-> exactly one canonical adjudicated relation slot
```

Conflicting precommitted alternatives for one key fail closed as `RELATED`/`RELATION_CONFLICT`; they cannot be shopped after outcomes are known.

A canonical `RelationRegistry` CAS surface is required.

### P3F-03 — FAMILY QUIESCENCE / TERMINATION

Disposition: **ACCEPT_AS_BLOCKER**

Current `ACTIVE -> RETIRED` Family semantics can strand an OPEN FamilyLifetimeLedger and nonterminal descendant Programs/proof episodes.

Required closure model:

```text
ACTIVE
-> QUIESCING
-> CLOSED
```

`QUIESCING` denies creation/renewal/new discovery rights while already-authorized descendants are deterministically closed or invalidated. `CLOSED` atomically seals the FamilyLifetimeLedger and requires no nonterminal authority-bearing descendants.

Archival retirement is not a shortcut around quiescence/ledger sealing.

### P3F-04 — SELECTED CHAMPION VS DEPLOYED CHAMPION

Disposition: **ACCEPT_AS_BLOCKER**

Promotion and capital activation are intentionally separate, therefore:

```text
ChampionRegistry.current
!= necessarily the Champion currently controlling capital
```

Required canonical terms:

```text
selected_champion_root
= current ChampionRegistry selection

deployed_champion_root
= Champion bound to the exact ACTIVE DeploymentActivationEpisode
```

Capital decisions must use `deployed_champion_root`; a registry selection has zero runtime effect until fresh activation succeeds.

A single-valued `DeploymentRegistry`/active-deployment slot is required to prevent concurrent ACTIVE deployment ambiguity.

### P3F-05 — SCIENTIFIC PROOF FRESHNESS MUST REACH ACT

Disposition: **ACCEPT_AS_BLOCKER**

Evidence freshness currently propagates through promotion but can stop before safety preflight/capital activation. A promoted-but-not-yet-deployed Champion whose proof later becomes invalid must not receive fresh capital authority.

Required derived predicate:

```text
CURRENT_DEPLOYMENT_PROOF_ELIGIBLE = TRUE
```

It binds at minimum:

```text
Champion root
PromotionTransaction
GovernorRecord
ScientificAdjudicationRecord
ProofBundle
all current EvidenceGovernanceHead dependencies
current proof-dependency validity
deployment context
```

Both `A-SAFETY-PREFLIGHT` and `A-CAPITAL-ACTIVATE` require it. Active deployments whose proof dependency becomes invalid are routed to the existing Capital Safety deactivation path.

### P3F-06 — DECISION INPUT PRODUCER PROVENANCE

Disposition: **ACCEPT_AS_BLOCKER**

Protecting the writer of DecisionStateRevision is insufficient if external Research can produce a semantically controlling input that the valid operational updater consumes.

Every decision-relevant input must prove:

```text
input_root
producer_principal
producer_trust_domain
source_class
generation/revision
information_time
active Champion closure membership where semantic/derived
```

External `TD-RESEARCH`, `TD-CRITIC`, `TD-GOVERNOR`, and `TD-PROMOTION` cannot publish semantic control inputs into active capital mapping.

A Research-origin component may affect live decisions only if it is itself part of the frozen/proven active Champion transitive closure and executes under operational—not Research—authority.

### P3F-07 — SAFETY AUTHORITY CONTINUITY DURING REVOCATION

Disposition: **ACCEPT_AS_BLOCKER**

A legal Governance Root rotation/revocation must not remove the final capital-deactivation/emergency path while exposure is ACTIVE.

Required invariant:

```text
NEVER revoke the last valid risk-reducing safety authority
while capital exposure is ACTIVE
```

Safety-critical authority/gate/Role rotation requires either:

```text
verified replacement installed atomically first
```

or:

```text
capital reaches verified flat/inactive state before revocation
```

### P3F-08 — GOVERNED STREAM GENESIS

Disposition: **ACCEPT_AS_BLOCKER**

Append-only lineage is not complete without exact revision/generation zero semantics.

General theorem:

```text
EVERY GOVERNED APPEND-ONLY STREAM
MUST HAVE EXACT GENESIS SEMANTICS
```

This includes at minimum:

```text
ResearchFamilyRegistry
RelationRegistry
ChampionRegistry
CapabilityRegistry
DeploymentRegistry
EvidenceGovernanceHead
FamilyLifetimeLedger
DecisionStateRevision
trusted authority/revocation registry heads
```

DecisionState requires a validated initializer bound to the exact deployed Champion/deployment; an arbitrary checkpoint cannot become revision 0.

## 4. Pass-3 findings that remain closed

The reports did not successfully reopen the following earlier corrections:

```text
single canonical machine source
Critic before final ScientificAdjudication
later Program cannot use A-PROGRAM-CREATE
attestation supersession stales evidence-dependent proof authority through promotion
Research cannot directly write an existing DecisionState chain
A-ROLLBACK is registry-only
PRODUCTION_AVAILABLE capability cannot silently alter active Champion closure
Capital Safety veto != scientific REJECT
Research cannot directly trigger emergency-flat authority
Experiment integrity PASS != scientific success
```

These remain subject to integrated closure-candidate re-attack; `remain closed` here is not final ARE-0 closure.

## 5. Auditor recommendations not adopted mechanically

Some audit text recommends:

```text
bounded correction
-> freeze new SHA
-> Pass 4 re-audit
```

That cadence is **not adopted** because the project has since frozen the batched architecture/audit workflow:

`PROJECT_GOVERNANCE/AHFMES_ARE_BATCHED_ARCHITECTURE_AND_AUDIT_WORKFLOW.md`

Current default is:

```text
filter Pass-3 findings
-> complete ALL remaining ARE-0 architecture
-> consolidate accepted corrections
-> internal Architect review
-> internal Red-Team attack
-> internal Scientific-Governor review
-> end-to-end scenario simulation
-> freeze ONE ARE-0 closure-candidate SHA
-> FINAL external ARE-0 closure audit
```

A foundational defect would stop the batch. Pass 3 found blocking machinery gaps, but did not invalidate the architecture direction.

## 6. Hard firewall

```text
ARE-0 CLOSED = NO
ARE implementation = NOT AUTHORIZED
P001 substantive research = NOT AUTHORIZED / ANSWER UNKNOWN
G1 rerun/retune = PROHIBITED
G2 = NOT AUTHORIZED
W2/W3 = CLOSED
Training/OOS = CLOSED
production = CLOSED
AHFMES-NEW = CLOSED
PR #20 merge = NOT AUTHORIZED
```
