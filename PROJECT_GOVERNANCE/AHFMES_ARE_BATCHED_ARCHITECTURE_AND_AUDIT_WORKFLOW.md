# AHFMES ARE — Batched Architecture & Audit Workflow

Status: **ACTIVE GOVERNANCE WORKFLOW / SELF-AUDIT COUNCIL REQUIRED / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

## 1. Purpose

This document defines the default AHFMES ARE architecture/audit cadence.

The old micro-cycle is prohibited by default:

```text
small design
-> external audit
-> small correction
-> external audit
-> repeat
```

Canonical major-layer cycle:

```text
COMPLETE ONE MAJOR ARCHITECTURAL LAYER
        ↓
INTERNAL ARCHITECT REVIEW
        ↓
SELF-AUDIT COUNCIL WAVE A — SPECIALISTS
        ↓
SELF-AUDIT COUNCIL WAVE B — CROSS-DOMAIN
        ↓
META-ADVERSARIAL CLOSURE SKEPTIC
        ↓
CONSOLIDATED CORRECTION
        ↓
RE-RUN IMPACTED AUDITORS
        ↓
FULL COUNCIL PASS #1 — NO NEW REPRODUCIBLE BLOCKER
        ↓
FULL COUNCIL PASS #2 — NO NEW REPRODUCIBLE BLOCKER
        ↓
END-TO-END SCENARIO SIMULATION
        ↓
FREEZE EXACT CLOSURE-CANDIDATE SHA
        ↓
EXTERNAL ADVERSARIAL CLOSURE AUDIT
        ↓
PASS or BOUNDED CORRECTION
```

Canonical council protocol:

`PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V1.md`

This workflow does not weaken scientific, authority, evidence, Capital Safety, exact-SHA, or implementation gates.

---

## 2. Governing principle

Audit cadence is organized by **major architectural layer**, not by individual patch.

```text
ONE MAJOR LAYER
-> DESIGN COMPLETELY
-> ATTACK INTERNALLY WITH ROLE-SEPARATED AUDITORS
-> CORRECT AS A SYSTEM
-> REQUIRE TWO CONSECUTIVE CLEAN FULL-COUNCIL PASSES
-> FREEZE
-> EXTERNAL AUDIT
```

External audit is not a substitute for obvious internal completeness work.

Do not defer a known blocker merely to make a batch look complete.

---

## 3. Major layers

```text
ARE-0 — Formal Constitution / Scientific Architecture
ARE-1 — Scientific Kernel / Registries / Authority Infrastructure
ARE-2 — Experience Intelligence
ARE-3 — Autonomous Science / Research Brain
ARE-4 — Governed Evolution
```

Each layer may contain many internal work packages. External design audit should normally occur only after the layer is integrated enough to evaluate global invariants.

---

## 4. Mandatory Self-Audit Council

Before any closure-candidate SHA can be frozen:

```text
SELF_AUDIT_COUNCIL_REQUIRED = TRUE
```

Baseline council has 12 logical auditors, expandable as new recurring failure classes appear.

The council is role-separated but is not claimed to be cryptographically or cognitively independent when one underlying model/service is reused.

Council structure:

### Wave A — specialists

```text
SA-01 State-Machine Totality
SA-02 Authority / Principal SoD
SA-03 Evidence / Holdout / Legacy Provenance
SA-04 Search-Debt / Multiplicity
SA-05 Champion Selection / Promotion / Rollback
SA-06 Temporal / Information-Time / Replay
SA-07 Capital Safety / Concurrency
SA-08 Protective / Recovery / Broker Semantics
SA-09 Genesis / Bootstrap / Migration
```

### Wave B — cross-domain

```text
SA-10 Scientific-Capital Boundary
SA-11 Cross-Document Consistency
```

### Final internal skeptic

```text
SA-12 Adversarial Integrator / Closure Skeptic
```

One auditor's PASS cannot override another reproducible blocker.

---

## 5. Two-consecutive-clean-pass rule

One clean council pass is insufficient.

Freeze eligibility requires:

```text
FULL COUNCIL PASS N
= NO NEW REPRODUCIBLE BLOCKER

FULL COUNCIL PASS N+1
= NO NEW REPRODUCIBLE BLOCKER
```

Both passes must operate on the same normative candidate tree except audit records that do not change semantics.

Any normative change resets:

```text
CLEAN_PASS_COUNT = 0
```

Any new blocker discovered by any auditor also resets the count.

---

## 6. Correction impact rule

Every correction declares which auditors are affected.

Affected auditors must be re-run before the next full council pass.

Examples:

```text
Decision identity change
-> SA-01
-> SA-06
-> SA-07 if CapitalAction genesis/risk changes
-> SA-10
-> SA-11
-> always SA-12

Safety-contract change
-> SA-02
-> SA-07
-> SA-08
-> SA-09
-> SA-10
-> SA-11
-> SA-12

Family relation / multiplicity change
-> SA-02
-> SA-03
-> SA-04
-> SA-05
-> SA-10
-> SA-11
-> SA-12
```

No correction is considered closed merely because its author says the exploit is fixed.

---

## 7. Permanent regression of external findings

Every externally discovered blocker class becomes a permanent internal regression scenario.

A finding is not deleted from the attack suite because one patch passes.

Current regression classes include at least:

```text
bootstrap double reservation
manifest/genesis ambiguity
Decision exact-key replay
semantic decision replay via wall-clock/cutoff variation
aggregate risk overbooking
protective polarity reversal
OperationalDecision / CapitalSafety self-approval
pre-genesis history omission
legacy cutoff gap
late legacy discovery after genesis
cross-Family first-winner promotion
post-outcome challenger-universe definition
Research self-granting Family independence
rollback used as adaptive strategy selection
ProtectiveDependencyPlan created after Safety approval
initial CapitalSafetyContract bootstrap ambiguity
SafetyContract self-witnessing
hidden SearchAction winner-only generation
```

New external classes append to this list.

---

## 8. Minimum integrated scenarios

Before freeze, the council must walk the complete design through at least:

### Scenario A — normal failed research

```text
Problem
-> Family
-> Program
-> Contract
-> Search
-> Candidate
-> Validation
-> Critic
-> Scientific Adjudication
-> Governor
-> REJECT / NO PROMOTION
```

Expected: no deadlock, no erased debt, no uncharged search path.

### Scenario B — successful challenger

```text
Problem
-> Candidate
-> Validation
-> Critic
-> Scientific PASS
-> Governor
-> prospective/shadow proof where required
-> promotion selection accounting
-> Champion Registry CAS
-> Capital Safety preflight
-> activation
```

Expected: no direct or indirect THINK -> ACT path.

### Scenario C — evidence/provenance invalidation

```text
proof prepared
-> provenance/isolation/legacy defect discovered
-> governance generation advances
-> dependent authority stale
-> promotion/deployment/new risk denied where required
```

### Scenario D — online adaptive state

```text
ACTIVE Champion
-> canonical input event
-> frozen updater
-> DecisionState
-> canonical Decision opportunity
-> DecisionRecord
```

Expected: no caller-selected replay nonce or Research state injection.

### Scenario E — legitimate rollback

```text
Champion B
-> frozen rollback trigger class fires for safety/integrity/execution reason
-> deactivation/reconciliation
-> registry rollback
-> fresh preflight
-> fresh activation
```

Expected: rollback never becomes performance-driven adaptive A↔B strategy selection.

### Scenario F — autonomous p-hacking attempt

```text
failed Program
-> new Program
-> new Family
-> new claim wording
-> new prospective epoch
-> new challenger-universe rule
```

Expected: scientific/search/selection debt cannot reset by relabeling.

### Scenario G — concurrency

```text
multiple simultaneous risk-increasing actions
+ pending orders
+ activation exposure
+ uncertain fills
```

Expected: aggregate worst-case risk remains inside Capital Safety envelope.

### Scenario H — first-generation bootstrap

Walk every generation-zero / first-generation object without assuming a nonexistent previous root.

### Scenario I — late historical discovery

```text
genesis believed complete
-> old pre-ARE experiment discovered later
-> legacy governance head/reconciliation advances
-> affected debt/proofs/selection/deployment become stale or reconciled
```

### Scenario J — invalid/unknown path

Any unknown authority, missing provenance, ambiguous transition, unknown risk, stale relation, uncertain execution or unclosed search debt fails closed without inventing an implicit route.

---

## 9. External audit role

External auditor receives a complete exact closure candidate for one major layer.

Expected attack style:

```text
global invariants
cross-object privilege
state-machine totality
principal SoD
evidence/legacy continuity
search/multiplicity/selection
information-time/replay
capital concurrency
protective/recovery semantics
genesis/bootstrap/migration
ACT boundary
```

External findings are attack inputs, not automatic truth.

Each requires reproduction, scope classification, overlap/root-cause check, consequence analysis and correction attack.

---

## 10. Correction policy after external CHANGES_REQUIRED

1. filter findings;
2. merge root-cause duplicates;
3. reject false positives;
4. distinguish formal architecture defects from implementation details;
5. add every accepted class to permanent regression scenarios;
6. add/retune a dedicated council auditor if current roles missed a recurring class;
7. correct accepted blockers as one bounded batch;
8. run impacted auditors;
9. run two clean full-council passes;
10. freeze one new exact candidate;
11. external-audit the integrated candidate.

Do not create one external audit cycle per finding unless a fundamental defect invalidates the whole batch.

---

## 11. Stop-the-batch exception

Immediately stop downstream work if an accepted finding implies:

```text
constitutional contradiction
THINK -> ACT path
unbounded Research authority
Capital Safety bypass
non-recoverable evidence contamination model
fundamental multiplicity invalidity
trust-root collapse
architecture direction invalidity
```

Batching is not permission to build on a broken foundation.

---

## 12. Roadmap cadence

```text
ARE-0 COMPLETE FORMAL ARCHITECTURE
-> SELF-AUDIT COUNCIL x2 CLEAN
-> EXTERNAL CLOSURE AUDIT

ARE-1 COMPLETE SCIENTIFIC-KERNEL DESIGN
-> SELF-AUDIT COUNCIL x2 CLEAN
-> DESIGN AUDIT
-> EXPLICIT IMPLEMENTATION AUTHORITY
-> GITHUB IMPLEMENTATION
-> REMOTE SOURCE AUDIT
-> EXACT SHA
-> ANTIGRAVITY LOCAL INTEGRATION/RUNTIME TEST

ARE-2 COMPLETE EXPERIENCE-INTELLIGENCE DESIGN
-> COUNCIL
-> EXTERNAL DESIGN AUDIT
-> IMPLEMENT ONLY IF AUTHORIZED

ARE-3 COMPLETE AUTONOMOUS-SCIENCE DESIGN
-> COUNCIL
-> EXTERNAL DESIGN AUDIT
-> IMPLEMENT ONLY IF AUTHORIZED

ARE-4 COMPLETE EVOLUTION DESIGN
-> COUNCIL
-> EXTERNAL DESIGN AUDIT
-> IMPLEMENT ONLY IF AUTHORIZED
```

Design closure never implies implementation authority.

---

## 13. GitHub-first engineering remains unchanged

When implementation is eventually authorized:

```text
complete audited design
-> explicit implementation authority
-> engineer codes in GitHub
-> remote exact-SHA source audit
-> pull exact audited SHA locally
-> Antigravity integration/runtime/MT5 testing
-> evidence published back to GitHub
-> independent adjudication
```

Local source edits must not silently become canonical implementation.

---

## 14. Source reuse / worktree hygiene

```text
same responsibility -> patch/extend existing .py
existing primitive -> reuse before cloning
new responsibility -> new module only with written justification
ARE-specific new modules -> bounded are/ package
version history -> Git, not *_v2/new/final/backup.py
legacy cleanup -> separate hygiene patch after proven obsolete
```

---

## 15. Current firewall

```text
ARE-0 CLOSED = NO
ARE implementation = NOT AUTHORIZED
P001 substantive research = NOT AUTHORIZED / ANSWER UNKNOWN
G1 rerun/retune = PROHIBITED
G2 = NOT AUTHORIZED
W2/W3 = CLOSED
production = CLOSED
AHFMES-NEW = CLOSED
PR #20 merge = NOT AUTHORIZED
```

The Self-Audit Council strengthens pre-external falsification. It does not replace external closure authority.