# AHFMES ARE-0 — External Adversarial Audit Handoff

Status: **READY FOR INDEPENDENT EXTERNAL AUDIT / NOT CLOSED / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

## 1. Purpose

This file is the morning handoff for an independent auditor. The design team has completed a long internal Architect -> Red-Team -> Scientific-Governor pass. The auditor should now try to break the complete normative package as one system.

Do not treat internal `PASS` labels as closure.

## 2. Repository state to verify first

Repository:

`Mziana/AHFMES-CHATGPT`

Branch:

`codex/current-authority-docs`

Package publication commit:

`5eb148bf8a7aa554e3a762df44247e8c739a4064`

Authority-index update immediately after package:

`5221de482a1027ac99437c611ab506db1c8f13f1`

Verify live head before review. Do not assume this handoff's SHA is still latest if the branch moved later.

PR #20 must remain:

```text
OPEN
DRAFT
UNMERGED
```

Issue #21 is the ARE-0 tracker.

## 3. Normative reading order

1. `PROJECT_GOVERNANCE/CURRENT_AUTHORITY_INDEX.md`
2. `PROJECT_GOVERNANCE/AHFMES_ARE_FORMAL_ARCHITECTURE_MASTER_V2.md`
3. `PROJECT_GOVERNANCE/AHFMES_ARE_0A_STATE_MACHINES_AND_INVARIANTS_V3.md`
4. `PROJECT_GOVERNANCE/AHFMES_ARE_0B_AUTHORITY_NON_FORGEABILITY_V3.md`
5. `PROJECT_GOVERNANCE/AHFMES_ARE_0C_EVIDENCE_LEDGER_AND_HOLDOUT_CONSUMPTION_V2.md`
6. `PROJECT_GOVERNANCE/AHFMES_ARE_0D_SEARCH_GENEALOGY_BUDGET_MULTIPLICITY_V2.md`
7. `PROJECT_GOVERNANCE/AHFMES_ARE_0E_CRITIC_GOVERNOR_PROMOTION_V2.md`
8. `PROJECT_GOVERNANCE/AHFMES_ARE_0F_INTERNAL_THREE_ROLE_ADVERSARIAL_REVIEW_V1.md`
9. this handoff.

Older ARE-0A V1 / ARE-0B V1 are historical initial drafts, not normative when conflicting with the versions above.

## 4. What the internal design pass already corrected

External first-round blockers:

```text
archive/disposition collapse
evidence-state dimensional collapse
incomplete transition graph
missing knowledge-only terminal path
Experiment integrity vs scientific-result conflation
concurrent scientific state fork
principal separation missing
root of trust undefined
content/hash binding incomplete
stale authority / TOCTOU
Champion promotion race/replay
```

Additional internal blockers found before handoff:

```text
Problem disposition overwrite across research episodes
insufficient Validation/Critic/Governor/Promotion separation
contract descendant budget reset
prospective evidence falsely called blind
Champion drift during challenger proof
```

Auditor should verify corrections actually close the attack, not trust the design team's statement.

## 5. Priority attack area A01 — State semantics

Try to:

```text
archive a REJECTED/INVALID result and erase its meaning
reopen a Problem and overwrite prior Research Episode result
skip required lifecycle state
force knowledge-only result into promotion path
interpret Experiment integrity PASS as hypothesis PASS
mutate a FROZEN candidate without descendant
create two concurrent transitions from one revision
recover from partial persistence into an advanced state
reset debt through new Problem/Candidate identity
```

Required outcome: fail closed or preserved immutable history.

## 6. Priority attack area A02 — Authority non-forgeability

Try to:

```text
construct valid-looking VAR manually
use friendly gate name without exact root
let Research alter its Role Manifest
let one principal own Validation + Critic + Governor + Promotion
reuse parent authority on descendant
reuse validation authority after Evidence Ledger changes
reuse proof after hidden Search Node appears
replay single-use authority
change candidate dependency behind mutable path
create canonical-hash ambiguity
promote against stale Champion generation
replay promotion in another deployment context
change Capital Safety after proof then reuse authority
```

Any successful canonical transition is blocking.

## 7. Priority attack area A03 — Evidence / holdout consumption

Try to:

```text
rename/copy/subset data into a fresh holdout
mint new Evidence ID for same snapshot
create new Problem after validation failure and reuse holdout
claim pass/fail disclosure is zero exposure
query blinded validator repeatedly
insert new candidate after first batch result
call related claim unrelated
use human/auditor knowledge without contamination edge
reserve same holdout concurrently
call revised historical news live-available
call LIVE_FROZEN prospective evidence STRICT_BLIND
```

Focus especially on claim-family relatedness semantics.

## 8. Priority attack area A04 — Search budget / multiplicity

Try to:

```text
split search across many contracts
split search across many Problems
start a fresh Research Program after failure
hide 10,000 trials in one optimizer call
hide many candidates in one LLM generation
switch statistical framework after failure
rescue subgroup/horizon/metric
add capability after failure without gap proof
query validation one extra time
stop at first PASS
omit failed Search Nodes from Search Tree
split Validation Family into many apparent single tests
```

Program Budget Envelope must prevent endless descendant-budget expansion.

## 9. Priority attack area A05 — Critic / Governor / Promotion

Try to:

```text
promote standalone positive P&L without Champion comparison
cherry-pick only common opportunities
hide common-opportunity harm inside whole-policy result
ignore material unknown costs
promote concentrated/tail-risk edge
promote with undefined OOD behavior
Critic rescues candidate
Governor changes primary gate
mutate candidate during shadow
promote C vs A after Champion became B
race multiple challengers against stale Champion
use frequency to rescue weak evidence
weaken Capital Safety for EV
force knowledge-only claim to capital
retest same candidate as if prior episode/evidence never existed
promote code candidate without sandbox/regression/rollback proof
```

## 10. Cross-world attack

Try to find ANY path:

```text
THINK -> ACT
```

that bypasses PROVE.

Examples:

```text
Research Brain writes Champion Registry
candidate invokes broker
Critic invokes promotion
Governor invokes broker activation
A-PROMOTE acts as A-CAPITAL-ACTIVATE
serialized status reload activates strategy
```

Any such path is critical/blocking.

## 11. Residuals intentionally left visible

The design explicitly asks external audit to examine:

```text
R-01 positive proof for genuinely unrelated claim families
R-02 completeness of search instrumentation with flexible LLM/code tools
R-03 concrete root-of-trust realization without power collapse
R-04 future contract-specific numerical statistical/economic gates
R-05 strict prospective isolation on one physical machine
R-06 atomic storage/recovery realization
```

Do not mistake explicit residual disclosure for acceptance. Upgrade to blocker if architecture is insufficient.

## 12. P001 firewall

P001 remains:

```text
UNRESOLVED
ANSWER = UNKNOWN
```

Do not audit by proposing a better exit strategy. Audit whether ARE could someday research P001 lawfully.

## 13. Hard scope firewall

```text
ARE implementation          = NOT AUTHORIZED
P001 substantive research   = NOT AUTHORIZED
G1 retune                   = PROHIBITED
G2                          = NOT AUTHORIZED
W2/W3                       = CLOSED
Training/OOS                = CLOSED
Production                  = CLOSED
AHFMES-NEW modification     = CLOSED
PR #20 merge                = NOT AUTHORIZED
```

## 14. Required finding format

For each defect:

```text
FINDING_ID
SEVERITY
SUBJECT FILE/SECTION
ATTACK PRECONDITIONS
ATTACK PATH
WHY CURRENT CONTRACT FAILS
REQUIRED CORRECTION / INVARIANT
CROSS-DOCUMENT IMPACT
```

Prefer a small number of precise finding families over dozens of cosmetic comments.

## 15. Allowed external disposition

Exactly one:

```text
CHANGES_REQUIRED
ACCEPT_ARE0_FORMAL_DESIGN_CLOSED
ARE0_FORMALIZATION_INVALID
```

Do not use `PASS` ambiguously.

If `ACCEPT_ARE0_FORMAL_DESIGN_CLOSED` is eventually issued, that still does NOT authorize implementation. A separate implementation authority remains mandatory.

## 16. Current handoff disposition

```text
NORMATIVE PACKAGE = READY FOR EXTERNAL ADVERSARIAL AUDIT
INTERNAL REVIEW    = COMPLETE
ARE-0              = NOT CLOSED
IMPLEMENTATION     = NOT AUTHORIZED
NEXT               = INDEPENDENT EXTERNAL AUDIT
```
