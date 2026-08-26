# AHFMES ARE-0F — Internal Three-Role Adversarial Design Review V1

Status: **INTERNAL ADVERSARIAL REVIEW COMPLETE / EXTERNAL AUDIT REQUIRED / ARE-0 NOT CLOSED / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

## 1. Purpose

This file records the self-attack performed before independent external audit.

The three review roles are functional review passes, not a claim of three separate external auditors:

```text
ROLE 1 — ARCHITECT
build coherent contracts

ROLE 2 — RED-TEAM
attempt privilege escalation, leakage, budget reset, stale authority, and scientific p-hacking

ROLE 3 — SCIENTIFIC GOVERNOR
check scope, constitution, authority boundaries, unresolved residuals, and whether Red-Team fixes create new loopholes
```

No role has implementation authority.

## 2. Audit subjects

Normative drafts prepared for external audit:

```text
ARE-0A V3 — State Machines / Research Episodes / Invariants
ARE-0B V3 — Authority / Separation of Duty / Root of Trust
ARE-0C V2 — Evidence Ledger / Holdout / Prospective Evidence
ARE-0D V2 — Program Budget / Search Genealogy / Multiplicity
ARE-0E V2 — Critic / Governor / Promotion / Rollback
ARE Formal Architecture Master V2 — integrated map
```

## 3. Imported external findings

The first independent review of initial 0A/0B drafts found the following canonical blocker families.

### 0A

```text
A0A-01 archive/disposition collapse
A0A-02 evidence state dimensional collapse
A0A-03 incomplete/contradictory transition graph
A0A-04 missing knowledge-only terminal path / experiment semantic conflation
A0A-05 concurrent transition fork
```

### 0B

```text
A0B-01 authority class separation without principal separation
A0B-02 undefined authority root of trust
A0B-03 non-canonical / non-transitive content hashing
A0B-04 stale authority / Evidence Ledger TOCTOU
A0B-05 champion registry promotion race/replay/context mismatch
```

These were treated as blocking, not cosmetic.

## 4. External findings correction disposition

### A0A-01

Corrected by separating:

```text
scientific disposition
retention/archive status
process lifecycle
```

No semantic `REJECTED -> ARCHIVED` transition exists in normative 0A V3.

### A0A-02

Corrected by replacing Evidence master enum with orthogonal:

```text
provenance
origin
append-only exposure events
relational eligibility
retention
```

Exact holdout semantics live in 0C.

### A0A-03

Corrected by explicit legal lifecycle graphs and Research Episode model. Unspecified transitions fail closed.

### A0A-04

Corrected by:

```text
VALIDATED_BOUNDED knowledge-only closure
Experiment lifecycle/integrity/scientific result separation
```

### A0A-05

Corrected by exact revision + previous-event hash + atomic compare-and-append.

### A0B-01

Corrected by trust domains + principal Role Manifests + explicit forbidden separation-of-duty combinations.

### A0B-02

Corrected by Governance Root Manifest -> Trusted Gate Registry -> Role Manifest -> gate proof chain.

### A0B-03

Corrected by canonical object encoding, domain-separated SHA-256 identities, and transitive content-addressed dependency closure.

### A0B-04

Corrected by authority binding to exact Evidence Ledger/search debt/state revisions plus verify-at-use and atomic consumption.

### A0B-05

Corrected by A-PROMOTE binding to exact current champion, registry generation, deployment context, safety/execution roots, proof bundle, and CAS transition.

## 5. Internal Red-Team Round 2 — new findings

After correcting external findings, internal review deliberately attacked the fixes and found three additional design risks.

### IR-01 — Problem disposition overwrite across new research

Risk:

```text
P001 closed UNRESOLVED
-> reopened
-> later RESOLVED_BOUNDED
```

could make a single mutable Problem disposition hide historical scientific outcomes.

Correction:

```text
persistent Problem
+ immutable Research Episodes
```

Each Episode retains its own adjudicated disposition forever.

### IR-02 — separation-of-duty matrix still too weak

Risk: separate authority class names could still be held by one principal.

Correction in 0B V3:

```text
Validation != Critic != Governor != Promotion != Capital Activation
for the same decision episode
```

plus Governance Root outside Research authority.

### IR-03 — descendant contract could expand research forever

Risk:

```text
contract budget exhausted
-> descendant contract
-> new budget
-> repeat until PASS
```

Correction in 0D V2:

```text
family-level Research Program Budget Envelope
```

Contract budgets are sub-budgets and cannot reset the Program envelope.

Outcome-driven Program expansion is prohibited without separate governance/materially new basis.

## 6. Internal Red-Team attack matrix — 0A

Attempted attacks:

```text
archive rejected result and erase rejection
archive invalid result and validate later
reopen Problem and overwrite old disposition
force knowledge-only result into promotion path
confuse Experiment PASS with hypothesis PASS
mutate FROZEN candidate
concurrent state forks
stale transition replay
partial transaction leaves advanced state
new candidate ID resets debt
new Problem ID resets ancestry
retired capability returns as clean identity
```

Internal disposition:

```text
no intended legal path found in normative 0A V3
```

External audit still required.

## 7. Internal Red-Team attack matrix — 0B

Attempted attacks:

```text
Research owns validation + promotion
Validation owns Critic
Governor owns Promotion
Promotion owns capital activation
forge VAR fields
forge friendly gate name
modify Role Manifest
modify Gate Registry
mutable model path behind frozen hash
hash ambiguity via float/order/Unicode
stale validation after ledger exposure
stale proof after hidden search node
reuse parent authority on descendant
replay single-use nonce
concurrent A->B/A->C promotion
replay proof in different deployment slot
change Safety Kernel after proof
```

Internal disposition:

```text
normative 0B V3 contains explicit denial/root/freshness/CAS semantics
```

Residual implementation choices cannot weaken those semantics.

## 8. Internal Red-Team attack matrix — 0C

Attempted attacks:

```text
rename/copy data to reset holdout
new Evidence ID wraps same bytes
new Problem ID after holdout failure
human/auditor sees result then suggests candidate
pass/fail bit treated as no exposure
query blinded validator repeatedly
add candidate after first batch result
call related claim unrelated
same snapshot concurrently reserved
outcome-selected subset called new holdout
historical revised news treated as live value
prospective called blind while Research sees outcome-bearing market path
candidate changes mid prospective epoch
```

Corrections/controls in 0C V2:

```text
content-addressed evidence ancestry
actor-inclusive disclosure ledger
query budget/reservation
precommitted batch
independent relation gate with default RELATED
atomic reservation
as-of provenance
STRICT_BLIND vs LIVE_FROZEN prospective classes
```

## 9. Internal Red-Team attack matrix — 0D

Attempted attacks:

```text
split search across contracts
split search across Problems
new Program after failure
optimizer hides 10k evaluations
LLM hides 100 candidates
subgroup rescue
horizon rescue
metric rescue
statistical-method shopping
capability inflation after failure
extra validation query
stop at first PASS
omit failed search nodes
validation family split into many single tests
```

Correction:

```text
Research Family root
Research Program Budget Envelope
contract sub-budgets
append-only Search Tree
action taxonomy
search completeness proof
Validation Family manifest
method-switch search node + evidence contamination
```

## 10. Internal Red-Team attack matrix — 0E

Attempted attacks:

```text
positive challenger P&L but worse than champion
overlap-only cherry-pick
portfolio-only hides bad overlap
mean EV hides tail loss
edge concentrated in tiny period
unknown costs treated zero
frequency rescues weak edge
undefined OOD still promotes
Critic rescues subgroup
Governor changes metric
candidate mutates during shadow
Champion changes during proof
multiple challengers race against stale Champion
promotion replay different account/context
Capital Safety weakened for EV
knowledge-only result touches capital
same candidate retested as if old failure never happened
rollback schema incompatible
code candidate skips regression/sandbox
```

Controls:

```text
champion-relative estimand
paired + whole-policy layers where needed
precommitted PromotionGateSpec
support/tail/OOD/cost gates
Critic no-rescue
frozen shadow
episode-specific history
stale champion invalidates promotion context
Capital Safety veto
code/capability extra proof
rollback compatibility
```

## 11. Scientific Governor scope audit

The internal Governor checked that the design did NOT accidentally authorize:

```text
ARE implementation
new trading policy
P001 solution search
G1 retune
G2
W2/W3
Training/OOS
production
AHFMES-NEW modification
PR #20 merge
```

Disposition:

```text
NO SCOPE ESCALATION DETECTED
```

## 12. Scientific Governor epistemic audit

The package does NOT claim:

```text
ARE-0 CLOSED
implementation ready
all statistical thresholds solved
all local security mechanics solved
holdout unrelatedness classifier solved
P001 solvable
future candidate profitable
```

It claims only:

```text
formal architecture drafted
known first-round blockers corrected in normative drafts
internal adversarial pass completed
ready for independent external attack
```

## 13. Residuals intentionally exposed to external audit

### R-01 Claim relatedness semantics

Default RELATED is safe, but exact positive proof for genuinely unrelated claims sharing market epochs needs adversarial refinement.

### R-02 Search instrumentation completeness

Architecture requires fail-closed when hidden trials cannot be ruled out. Future implementation must prove instrumentation is complete even when code/LLM/search tools are flexible.

### R-03 Root security realization

Trust topology is formalized, but exact cryptographic/process/hardware mechanism remains implementation design. It may not weaken role separation.

### R-04 Statistical numerical gates

No universal alpha/EV/sample/tail/shadow constants are invented. Future bounded PromotionGateSpecs must freeze them pre-outcome.

### R-05 Strict prospective isolation on one machine

Architecture distinguishes STRICT_BLIND from LIVE_FROZEN. Auditor should attack whether proposed trust-domain separation can be meaningful when Operational Brain and Research Brain share a machine.

### R-06 Partial transaction/recovery implementation

Formal invariant is atomic no-advancement without committed transaction. Concrete storage design remains future implementation work.

These residuals are NOT hidden and do not authorize implementation.

## 14. Cross-document consistency checks

Internal Governor checked:

```text
0A uses Research Episodes rather than mutable Problem scientific history
0B authority binds 0C ledger snapshots
0B authority binds 0D search/program debt
0C reservations bind 0D Validation Family/Program
0D validation eligibility relies on 0C exposure semantics
0E Proof Bundle consumes 0B/0C/0D proofs
0E promotion uses 0B champion CAS
Capital Safety remains outside Research
Master architecture preserves THINK -> PROVE -> ACT
```

No intentional circular authority was found. There are logical dependencies but no component grants itself prerequisite authority.

## 15. P001 firewall audit

P001 remains:

```text
UNRESOLVED
ANSWER = UNKNOWN
```

The package does not propose:

```text
G1.1
G2
ATR
M5/H1
news
retracement speed
new exit threshold
```

Any mentions of timeframe/news/capability are architecture examples, not P001 hypotheses.

## 16. Documentation authority versus implementation

All formal files are specifications only.

No Python source, runtime, test harness, dataset, PPR artifact, W2/W3 file, broker, or production repo is authorized by this audit.

## 17. Internal verdict per package

```text
ARE-0A V3 = INTERNAL RED-TEAM PASS / EXTERNAL AUDIT REQUIRED
ARE-0B V3 = INTERNAL RED-TEAM PASS / EXTERNAL AUDIT REQUIRED
ARE-0C V2 = INTERNAL RED-TEAM PASS / EXTERNAL AUDIT REQUIRED
ARE-0D V2 = INTERNAL RED-TEAM PASS / EXTERNAL AUDIT REQUIRED
ARE-0E V2 = INTERNAL RED-TEAM PASS / EXTERNAL AUDIT REQUIRED
```

“PASS” here means only the internal attack round did not find an unresolved blocker after the recorded corrections. It is not ARE-0 closure.

## 18. Requested external audit style

External auditor should not ask “is this architecture good?”.

It should try to construct concrete counterexamples:

```text
illegal state path
privilege escalation
freshness race
holdout reset
budget reset
hidden multiplicity
validation oracle
post-hoc rescue
stale champion promotion
safety bypass
capital path from Research
```

For each finding, require:

```text
ID
attack preconditions
exact legal/illegal path
why current contract fails
required invariant/correction
severity
```

## 19. Allowed external dispositions

```text
CHANGES_REQUIRED
ACCEPT_ARE0_FORMAL_DESIGN_CLOSED
ARE0_FORMALIZATION_INVALID
```

Internal review does NOT issue `ACCEPT_ARE0_FORMAL_DESIGN_CLOSED`.

That is reserved for the next independent adversarial closure process and project lead authority.

## 20. Current overall disposition

```text
ARE-0F INTERNAL THREE-ROLE REVIEW
= COMPLETE

KNOWN FIRST-ROUND BLOCKERS
= CORRECTED IN NORMATIVE DRAFTS

INTERNAL NEW BLOCKERS
= 3 FOUND AND CORRECTED

BOUNDED RESIDUALS
= EXPLICITLY RECORDED

EXTERNAL AUDIT
= REQUIRED

ARE-0
= NOT CLOSED

IMPLEMENTATION
= NOT AUTHORIZED
```
