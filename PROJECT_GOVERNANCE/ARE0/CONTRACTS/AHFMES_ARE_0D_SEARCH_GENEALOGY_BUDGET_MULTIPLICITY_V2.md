# AHFMES ARE-0D — Search Genealogy, Program Budget Envelope, Research Debt, and Multiplicity V2

Status: **SECOND-PASS CORRECTED FORMAL DESIGN / INTERNAL RED-TEAM PASS / EXTERNAL AUDIT REQUIRED / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

This is the normative ARE-0D draft for external review.

## 1. Why V2 exists

The first internal draft correctly tracked full search genealogy per contract, but a second-pass attack found a loophole:

```text
failed contract
-> create descendant contract
-> request fresh large budget
-> continue searching until PASS
```

Inherited debt alone does not prevent unlimited expansion.

V2 therefore adds a **Research Program Budget Envelope** at the research-family level.

## 2. Core theorem

```text
CONTRACT BUDGET
<=
PROGRAM BUDGET ENVELOPE
```

and:

```text
DESCENDANT CONTRACT
!= FRESH PROGRAM BUDGET
```

The family-level envelope constrains cumulative autonomous search across related contracts.

## 3. Research Family Root

All causally related search belongs to one `research_family_root`.

Relatedness follows:

```text
Problem ancestry
Research Episode ancestry
failed hypothesis motivation
validation/shadow feedback
feature/model reformulation
metric/horizon reformulation
capability-gap work
candidate descendants
```

New ID/repo/file/branch does not reset family identity.

## 4. Research Program object

Before a bounded autonomous research program begins, create:

```yaml
research_program_id: RP-...
research_family_root: ...
problem_root: ...
program_question_class: ...
program_budget_envelope_root_hash: ...
evidence_policy_root_hash: ...
allowed_contract_classes: [...]
program_stopping_rule: ...
created_before_outcome_exposure: true
```

This object is locked by non-Research authority.

## 5. Program Budget Envelope

Vector limits across the ENTIRE related program:

```yaml
program_budget_envelope:
  max_contract_descendants: ...
  max_problem_reformulations: ...
  max_hypothesis_families: ...
  max_feature_inventions: ...
  max_feature_interactions: ...
  max_threshold_evaluations: ...
  max_hyperparameter_evaluations: ...
  max_model_families: ...
  max_model_architectures: ...
  max_population_cuts: ...
  max_subgroup_cuts: ...
  max_horizon_evaluations: ...
  max_metric_alternatives: ...
  max_candidate_births: ...
  max_candidate_descendants: ...
  max_capability_gap_hypotheses: ...
  max_capability_additions: ...
  max_validation_batches: ...
  max_validation_extra_queries: ...
  max_shadow_descendants: ...
```

No universal numeric values are invented here. Values must be frozen before the relevant program sees outcomes.

## 6. Contract-level sub-budget

Each Research Contract receives a sub-budget that cannot exceed remaining Program Budget.

```text
remaining_program_budget
-> allocate contract sub-budget
-> actual search consumes both contract and program counters
```

Unused sub-budget may return to the program envelope only if this behavior was precommitted and does not depend on favorable/unfavorable results.

## 7. Program budget expansion

Outcome-driven expansion of an existing Program Budget Envelope is prohibited.

Allowed new budget requires a new separately-governed Research Program only when materially new scientific conditions exist, such as:

```text
new prospective evidence epoch
externally-originated new capability not motivated by program outcome
materially new problem charter
scientific constitution change
```

Even then:

```text
old research/search/evidence history remains linked
old holdout does not become clean
new Program cannot claim old failed search never occurred
```

The new program requires explicit governance authority; Research Brain cannot self-expand budget.

## 8. Search Tree

Every outcome-aware choice creates immutable Search Node:

```yaml
search_node_id: ...
research_program_id: ...
research_family_root: ...
parent_search_node_id: ...
contract_root: ...
action_class: ...
option_set_root: ...
selected_option_root: ...
selection_basis: PRECOMMITTED | OUTCOME_INFORMED | EXTERNAL_PRIOR
source_evidence_refs: [...]
outcome_information_seen: ...
created_at_utc: ...
node_root_hash: ...
```

Tree is append-only/content-addressed.

## 9. Mandatory action classes

```text
PROBLEM_REFORMULATION
HYPOTHESIS_FAMILY_BIRTH
FEATURE_INVENTION
FEATURE_SELECTION
FEATURE_INTERACTION
THRESHOLD_EVALUATION
HYPERPARAMETER_EVALUATION
MODEL_FAMILY_EVALUATION
MODEL_ARCHITECTURE_EVALUATION
POPULATION_CUT
SUBGROUP_CUT
HORIZON_EVALUATION
METRIC_ALTERNATIVE
LOSS_OBJECTIVE_ALTERNATIVE
CANDIDATE_BIRTH
CANDIDATE_DESCENDANT
CAPABILITY_GAP_HYPOTHESIS
CAPABILITY_ADDITION
VALIDATION_BATCH
VALIDATION_EXTRA_QUERY
SHADOW_DESCENDANT
STOPPING_RULE_EVENT
```

Unknown adaptive action class is not silently free; it must be classified before independent claims proceed.

## 10. Research Debt Vector

Actual cumulative counters are derived from Search Tree, not caller-maintained mutable counters.

```text
program_debt = fold(all valid Search Nodes in research_family_root)
```

Cached debt vectors are non-authoritative.

## 11. Search algorithm identity

Any automated search tool is itself content-addressed and budgeted.

Contract binds:

```text
algorithm root
search-space grammar
maximum evaluations
randomness/seed authority if relevant
objective data role
stopping rule
candidate output count
```

One optimizer call containing 10,000 evaluations counts according to evaluations, not API-call count.

## 12. LLM candidate generation

LLM generation episode records:

```text
model/version identity if available
prompt/context root
visible outcome context
generation grammar
number candidates emitted
selection method
```

If 100 candidates are emitted and inspected, genealogy reflects that search space.

If the LLM saw validation/shadow outcomes, new ideas inherit outcome-informed ancestry and evidence contamination.

## 13. Continuous optimization

Every objective evaluation against outcome-bearing discovery data counts unless an auditable bounded batch search algorithm records the complete evaluation set under one fixed algorithm contract.

A selected optimum does not erase evaluated alternatives.

## 14. Problem reformulation

Changing wording does not create a new program when motivated by results.

```text
failed P001 episode
-> "new" P999 question derived from why P001 failed
```

remains linked through a motivation edge.

New program/family requires independent origin proof; default under ambiguity is related.

## 15. Capability expansion

```text
failure
!= insufficient observability
```

Capability addition requires:

```text
capability-gap Research Episode
bounded evidence
Program Budget availability
action nodes for gap hypothesis + capability search
```

H1/news/DXY/new encoder are not free “more data” responses.

## 16. Contract mutation

Changing after outcome:

```text
primary metric
population
horizon
feature family
model family
statistical method
validation family
```

requires descendant contract and consumes Program Budget.

It cannot rescue the parent result.

## 17. Statistical-method switch attack

Attack:

```text
frequentist gate fails
-> descendant uses Bayesian gate on same validation outcome
```

Defense:

- method change is an outcome-informed Search Node;
- same exposed validation evidence is not independent for the descendant under ARE-0C;
- new independent confirmation requires eligible/prospective evidence;
- Program Budget debt persists.

## 18. Discovery versus validation multiplicity

Discovery search can be broad within budget.

A truly untouched independent validation set may test a precommitted selected claim without mechanically correcting for every discovery exploration, because selection occurred on independent evidence.

However:

```text
full discovery genealogy remains mandatory
```

for reproducibility, overfitting diagnosis, future relatedness, and program governance.

Validation multiplicity is separately controlled for claims/candidates/metrics/populations exposed on the validation evidence.

## 19. Validation Family

Before outcome access:

```yaml
validation_family_id: ...
research_program_id: ...
research_family_root: ...
claim_family_root: ...
candidate_batch_root: ...
primary_claim_manifest: ...
primary_estimand_manifest: ...
population_manifest: ...
secondary_diagnostics_manifest: ...
error_control_plan_root: ...
sequential_plan_root: ...
stopping_rule_root: ...
```

Result-driven insertion into the family is prohibited.

## 20. Multiplicity plan classes

The architecture supports a precommitted method appropriate to claim structure:

```text
single fixed claim
family-wise error control
false-discovery control for bounded claim family
sequential alpha/error spending
always-valid/e-value style sequential evidence
bootstrap/interval family gate with declared correction
Bayesian decision rule with frozen prior/loss/calibration
```

Research cannot choose whichever framework passes after seeing outcomes.

## 21. Error Budget

When applicable, statistical error budget is its own content-addressed object and ledger.

It binds exact validation family and consumption events.

No universal alpha/threshold is selected by this architecture document; future research/promotion contract must freeze the numerical rule pre-outcome.

## 22. Repeated validation

Without a precommitted sequential method:

```text
first outcome-aware validation disclosure consumes independence
for adaptive related descendants
```

Repeated checks on the same evidence become discovery/diagnostic, not fresh validation.

With a valid sequential plan, looks/spending must follow exact plan and remain in the same Validation Family genealogy.

## 23. Validation oracle attack

Repeated bounded queries can reconstruct holdout behavior.

Therefore Program/Contract budgets include:

```text
validation_batches
validation_extra_queries
permitted disclosed metrics
```

Extra query not precommitted is denied or recorded as new contamination; it never remains invisible.

## 24. Subgroup/population rescue

Precommitted subgroups can be part of one multiplicity family.

Outcome-selected subgroup after primary failure:

```text
parent claim remains failed
new subgroup claim = descendant research
same exposed evidence = discovery, not untouched validation
```

## 25. Hidden-trial completeness

At proof boundary, a `Search Completeness Proof` asserts:

```text
all outcome-aware actions through cutoff are represented
search tree root matches event store
program debt <= envelope
contract debt <= sub-budget
no unknown action classes
```

If completeness cannot be proven:

```text
UNKNOWN_SEARCH_DEBT
-> independent validation/promotion authority denied
```

The system may continue as discovery.

## 26. Search instrumentation boundary

Research-owned code cannot decide which of its own trials are “important enough” to count.

Future implementation must route outcome-bearing research operations through audited search instrumentation/gates or equivalent append-only accounting.

Uninstrumented outcome-aware computation cannot support independent proof claims.

## 27. Stopping rules

Valid stop:

```text
contract budget exhausted
Program Budget exhausted
no candidate survives
all families rejected
insufficient sample
non-predictable conclusion
capability gap not supported
prospective evidence unavailable
integrity failure
```

Invalid implicit stop:

```text
continue until first PASS
```

unless a formally valid precommitted sequential design explicitly permits that stopping behavior.

## 28. Program closure

Program closes with one of:

```text
NO_EDGE_FOUND
VALIDATED_BOUNDED_KNOWLEDGE
PROMOTION_ELIGIBLE_CANDIDATE
CURRENTLY_NON_PREDICTABLE
INSUFFICIENT_SAMPLE
INSUFFICIENT_OBSERVABILITY
NO_STABLE_EDGE
UNRESOLVED
INVALID
```

Closure does not erase tree/debt.

## 29. Restart conditions

A closed Program may not be reopened merely because time passed.

New Program requires explicit governance reason and must state:

```text
what material new evidence/capability/question justifies it
how old search/evidence ancestry is linked
which old validation evidence is now ineligible
what new Program Budget is authorized
```

## 30. Three-role second-pass attacks

Red-Team attacked:

```text
1 descendant contract asks for new giant budget
2 split one search across many contracts
3 split one search across many Problems
4 optimizer hides 10k trials in one call
5 LLM hides 100 candidates in one generation
6 metric/statistical-framework switch after failure
7 subgroup rescue
8 horizon rescue
9 new capability after failure without gap proof
10 extra validator queries
11 stop at first positive result
12 omit failed nodes from final Search Tree
13 start "new program" on same evidence to reset debt
14 claim new Problem unrelated without provenance
```

V2 adds family-level Program Budget, motivation edges, completeness proof, method-switch accounting, and external-governance requirement for genuinely new Program envelopes.

## 31. External audit obligations

Auditor must try to construct a path that gains additional adaptive search chances without increasing Program/Search debt or contaminating evidence.

Priority attacks:

```text
contract splitting
program restart
Problem relabeling
optimizer opacity
LLM opacity
statistical-method shopping
validation-family splitting
subgroup/horizon rescue
capability inflation
hidden trial omission
```

Any successful bypass is blocking.

## 32. Current disposition

```text
ARE-0D V2
= SECOND-PASS CORRECTED FORMAL DESIGN
= INTERNAL RED-TEAM PASS
= READY FOR EXTERNAL ADVERSARIAL AUDIT
= NOT CLOSED
= NO IMPLEMENTATION AUTHORITY
```
