# AHFMES ARE — Self-Audit Council Protocol V32

Status: **NORMATIVE / V31 INHERITED + R9-05 ROLLBACK CAUSE-AVAILABILITY NONINTERFERENCE AUDIT / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 1. Inheritance / current successor

Protocol V31 remains in force. This V32 adds mandatory audit gates for `EXT2-081-01` and R9-05 rollback cause-observation / fallback-selection control-flow noninterference.

Current successor components are Matrix V26 / Inventory V26 / Correction V31 under the successor manifest. Policy V5 remains unchanged.

```text
FAILED_EXTERNAL_SUBJECT = 081e0472a4322a83af148ee0b60e01a655b0fcbd
EXTERNAL_FINDING = EXT2-081-01
ROOT = R9-05
NEW ROOT = NO
```

No predecessor internal clean-pass, regression or external-audit credit transfers to the normative successor.

## 2. Mandatory rollback influence reconstruction

For every authority-conferring `A-ROLLBACK` attempt and allowed cause class, auditors MUST reconstruct exact current:

```text
ROLLBACK_POLICY_ROOT
ROLLBACK_CAUSE_OBSERVATION_POLICY_ROOT
CAUSE_OBSERVATION_SOURCE_UNIVERSE
ROLLBACK_BENEFICIARY_OUTCOME_SOURCE_SET
ROLLBACK_BENEFICIARY_OUTCOME_DESCENDANT_SET
ROLLBACK_CAUSE_SELECTION_INFLUENCE_GRAPH
ROLLBACK_CAUSE_SELECTION_INFLUENCE_CLOSURE_COMPLETE
ROLLBACK_CAUSE_SELECTION_NONINTERFERENCE_VALID
ROLLBACK_CAUSE_SELECTION_NONINTERFERENCE_ROOT
ROLLBACK_CAUSE_EVENT_KEY
ROLLBACK_CAUSE_LINEAGE_VALID
```

The reconstruction MUST include both cause/evidence content and every control/availability influence that can alter fallback-selection availability.

At minimum enumerate and attack:

```text
source/monitor/scope selection
subscription/event-push activation
probe/query/discovery activation
retry/error/absence handling
source/method selection
admission/suppression/exclusion
finality/currentness/completeness
attestation request/availability/completion
cause canonicalization/eligibility
freshness/expiry/order boundary timing
outcome presence/absence/access/error/latency side channels
human/LLM/operator control decisions
legal cause availability to R9-05
legal availability of A-ROLLBACK
```

A graph that contains clean immutable cause provenance but omits the branch that decides whether to look at that cause is incomplete.

## 3. Required consequence attacks

Auditors MUST attempt at least:

```text
A. Champion favorable -> do not query clean immutable genuine cause R;
   Champion unfavorable -> query R and attempt A-ROLLBACK.

B. same visible R exists in both worlds;
   favorable -> suppress/defer admission or finality;
   unfavorable -> admit/finalize and attempt A-ROLLBACK.

C. same visible/admitted R exists in both worlds;
   favorable -> attestation suppressed/deferred;
   unfavorable -> attestation completed and rollback requested.

D. outcome value is hidden but outcome presence/absence, publication timing,
   access result, exception state or latency selects query/retry/attestation.

E. human/operator/LLM sees Champion PnL or attractiveness, then chooses whether
   to expand monitor scope, query a clean source, retry a failed lookup, request
   finality, or complete attestation.

F. transformed/hashed/thresholded/embedded outcome proxy selects cause availability.

G. outcome triggers discovery of a genuine integrity defect; attempt to use the
   same defect both for valid Safety containment and for fallback strategy selection.
```

Expected behavior:

```text
material consequence -> cause-availability control path
=> rollback-selection noninterference FALSE
=> A-ROLLBACK fallback selection denied
```

while separately valid factual/Safety containment remains available.

## 4. Counterfactual audit

Holding exact genuine non-performance cause facts and exogenous governance/integrity facts fixed, auditors MUST vary Champion/fallback consequence sources and descendants.

The authority-conferring rollback path passes only if the following remain invariant:

```text
governed observation opportunities
query/discovery/retry activation
admission/suppression
finality/currentness/completeness
attestation availability/completion
legal availability of the cause to R9-05
legal availability of A-ROLLBACK fallback selection
```

Any material hidden/opaque/UNKNOWN influence capable of changing these => FAIL.

## 5. Positive rollback liveness control

Auditors MUST prove at least one positive path, not merely denial paths:

```text
frozen pre-outcome rollback policy
+ consequence-blind frozen event-driven push/subscription OR governed probe/cadence
+ same genuine allowed cause R
+ complete influence closure
+ noninterference PASS
+ inherited first-information/provenance/SoD PASS
+ exact displaced incumbent remains current/eligible
+ current proof/selection/Safety/runtime/deployment predicates PASS
+ exact inherited rollback authority PASS
=> A-ROLLBACK is drainable
```

The positive control must also demonstrate that beneficiary outcome existing elsewhere in the system does not itself cause false taint when no causal/control path from that outcome reaches rollback-selection availability.

If the correction makes genuine consequence-blind rollback impossible, qualification fails for liveness/totality.

## 6. Safety containment positive control

Auditors MUST prove a genuine defect found through an outcome-conditioned path may still, under its own valid authority, support fail-closed Safety/integrity actions such as factual incident recording, cancellation of risk increase, deactivation/no-new-risk, reduction or closure.

Expected:

```text
factual/Safety consequence = may remain legal under exact independent authority
A-ROLLBACK strategy selection = denied from the tainted cause-availability path
```

If Safety containment is unnecessarily blocked, qualification fails. If containment silently implies fallback strategy selection, qualification also fails.

## 7. Currentness / replay / starvation attacks

Auditors MUST attempt:

```text
change observation source universe after authority acceptance -> reuse stale authority
change cadence/push/query rule -> reuse stale rollback acceptance
change admission/attestation rule -> reuse stale currentness
stale displaced incumbent + clean consequence-blind cause -> attempt rollback
unrelated monitor activity -> force semantic remint/starvation
unrelated TrustedAuthorityRegistry CAS churn -> alter observation-policy semantics
same semantic policy + byte-equivalent retry -> duplicate authority mint
```

Expected:

```text
semantic observation-policy change -> inherited stale authority/currentness denied
stale fallback -> rollback denied
unrelated activity/churn -> no semantic remint or starvation
idempotent same semantic attempt -> inherited one-canonical-authority semantics
```

## 8. Permanent regression additions

Protocol V31 scenarios through `R9-X278` remain permanent. Add exactly:

```text
R9-X279 — OUTCOME_CONDITIONED_CLEAN_ROLLBACK_CAUSE_QUERY
SETUP:
- immutable signed genuine cause R exists independently of Champion outcome;
- R is in the governed authority-conferring source universe;
- favorable Champion outcome -> attester/monitor does not query R;
- unfavorable Champion outcome -> same principal queries/adopts R;
- R otherwise satisfies inherited cause provenance/SoD requirements;
- A is the exact valid displaced incumbent.
EXPECT:
- outcome -> query/discovery control edge is represented;
- rollback cause-selection noninterference = FALSE;
- R may support separately authorized factual/Safety consequences;
- R cannot authorize A-ROLLBACK fallback strategy selection;
- rollback selection remains denied until a consequence-blind cause-observation path exists.

R9-X280 — OUTCOME_CONDITIONED_ROLLBACK_ATTESTATION_SUPPRESSION
SETUP:
- same genuine cause R is visible/admitted in both counterfactual worlds;
- favorable Champion outcome -> cause attestation is suppressed/deferred;
- unfavorable Champion outcome -> attestation is completed and rollback requested;
- all other inherited cause/fallback facts are fixed.
EXPECT:
- outcome -> attestation-availability control edge is represented;
- rollback cause-selection noninterference = FALSE;
- A-ROLLBACK fallback strategy selection denied;
- separately valid Safety containment remains legal.
```

Permanent totals become:

```text
R7 = 26
R8 = 40
R9 = 280
TOTAL = 346
```

The positive liveness and Safety-containment controls in Sections 5-6 are mandatory qualification controls in addition to the 346 permanent regression scenarios.

## 9. Outside-family compositions

In addition to all inherited lanes and V31 compositions, attack:

```text
clean cause x outcome-conditioned query
clean cause x outcome-conditioned admission/finality
clean cause x outcome-conditioned attestation
independent attester x performance-aware search discretion
LLM/human outcome knowledge x monitor-scope expansion
error/retry policy x consequence channel
outcome timing x freshness/attestation boundary
Safety containment x hidden fallback selection
observation-policy rotation x stale authority
consequence-blind push source x positive rollback liveness
```

One reproducible bypass, deadlock, replay, starvation, ambiguity or unsafe composition blocks qualification.

## 10. Qualification chronology

After the integrated V26 successor wave and only after a whole-architecture/outside-family impact audit is clean:

```text
freeze exact S0
verify current manifest + every non-self same-subject full Git object identity
compute normative root twice independently
complete subject-bound whole-blob historical-authority quarantine verification
run inherited whole-architecture lanes from zero on exact S0
run V32 rollback-control attacks and positive controls
CP1
NO NORMATIVE WRITE
CP2 on identical root
permanent 346/346 regression
final consistency
self-reference-free candidate
exact QAO-only qualification lineage
exactly one binder-only child
independent external re-audit
```

Any normative byte change after S0 restarts qualification. Any normative byte change after CP1 resets clean-pass credit to zero.

## 11. Progress / firewall

Every completed audit/adjudication/design milestone must be reflected in `PROJECT_JOURNAL` with exact subject and qualification-credit status. Issue/PR metadata may supplement the journal but does not replace it.

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR MERGE = NOT AUTHORIZED
AHFMES-NEW = CLOSED
W2/W3 = CLOSED
```
