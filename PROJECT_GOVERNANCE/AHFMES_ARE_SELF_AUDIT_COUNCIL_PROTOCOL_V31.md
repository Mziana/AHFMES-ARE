# AHFMES ARE — Self-Audit Council Protocol V31

Status: **NORMATIVE / V30 INHERITED + R9-01 CONTROL-FLOW NONINTERFERENCE / EXACT VAR-PROPOSAL AUDIT / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 1. Inheritance / current successor

Protocol V30 remains in force. This V31 adds mandatory audit gates for authority-relaxing control-flow/availability influence and exact refinement VAR proposal/target-acceptance semantics.

Current successor components are Matrix V25 / Inventory V25 / Correction V30 under the current manifest. Policy V5 remains unchanged.

## 2. Pre-S0 findings retained as attack obligations

```text
IA31-A01
= RELEASE_CONTROL_FLOW_NONINTERFERENCE_NOT_CLOSED
ROOT = R9-01
NEW ROOT = NO

IA31-A02
= REFINEMENT_TARGET_ACCEPTANCE_PROPOSAL_NOT_EXACT_TO_FULL_VAR
ROOT = R9-01 x CLOSED-WORLD AUTHORITY NON-FORGEABILITY
NEW ROOT = NO
```

Passing V30 content-taint attacks does not imply these findings are closed. Auditors must independently attack content and control influence.

## 3. Mandatory full release-influence reconstruction

For every authority-sensitive refinement release, auditors MUST reconstruct the existing:

```text
BENEFITED_AUTHORITY_LINEAGE_CLOSURE
BENEFICIARY_OUTCOME_SOURCE_SET
BENEFICIARY_OUTCOME_DESCENDANT_SET
REFINEMENT_PRIVILEGE_RELEASE_DEPENDENCY_GRAPH
RELEASE_DRIVING_DEPENDENCY_CLOSURE_COMPLETE
REFINEMENT_PRIVILEGE_RELEASE_NONINTERFERENCE_VALID
```

The reconstruction MUST include both content derivation and any control/availability influence that can change whether/when relief occurs.

At minimum enumerate and attack:

```text
query/discovery activation
source/support selection
admission/suppression
finality/currentness/completeness
attestation availability
holder nomination
target acceptance
root-kernel approval
root-gate issuance
VAR revocation/replacement/currentness
commit scheduling/order/availability
timing that can cross freshness/expiry/CAS/order boundaries
outcome presence/absence/access/error/latency side channels
human/LLM/operator control decisions
```

A graph that contains every data-transform edge but omits a release-gating control branch is incomplete.

## 4. Required control-flow consequence attacks

Auditors MUST attempt at least:

```text
A. favorable outcome -> query clean immutable historical archive;
   unfavorable outcome -> do not query it.

B. same clean support exists in both worlds, but favorable outcome -> admit/finalize it;
   unfavorable outcome -> suppress/defer it.

C. all evidence is clean and fixed, but favorable outcome -> holder signs target acceptance
   or root approval/issuance is triggered; unfavorable outcome -> no authority path.

D. outcome value is hidden, but its presence/absence, publication timing, access result,
   exception state or latency selects the release path.

E. human/LLM sees beneficiary outcome, then chooses whether to request a clean archive,
   finality attestation, holder acceptance or issuance.
```

All authority-relaxing paths must fail unless the exact release-control decision remains unchanged under the V25 counterfactual noninterference theorem.

Outcome-triggered paths may still produce factual-only records when inherited factual-governance predicates hold; they cannot restore privilege for the benefited lineage.

## 5. Positive control / liveness

Auditors MUST prove a positive path where:

```text
later historical support is discovered by an outcome-independent governed procedure;
source/method/content are positively historical-identifying and outcome-isolated;
release-support acquisition/admission/finality path is also outcome-independent;
exact holder/issuer/SoD/currentness predicates are valid;
exact current refinement VAR exists when a mutable batch write is required.
```

The mechanism must not deadlock merely because the record is discovered after SystemGenesis or after a beneficiary outcome exists elsewhere in the system.

Equivalent support renewal and unrelated authority-registry churn must not force semantic batch remint or target re-acceptance solely because unrelated bytes/generations changed.

## 6. Mandatory exact proposed-VAR audit

For every refinement commit proposal, verify the accepted proposal binds at least:

```text
authority class
exact semantic subject
exact intended root-kernel issuer control identity/generation
exact intended root-gate writer identity/generation
exact holder control identity + RoleManifest generation
usage EDGE_NONCE
exact inherited TRANSITION_KEY / edge nonce / episode identity
capital NO
exact semantic/prerequisite/currentness roots
expiry/revocation semantics
latest same-subject terminal VAR predecessor or NONE
```

Then prove:

```text
target acceptance verifies over that exact proposal;
root-kernel approval addresses that exact proposal;
root-gate identity equals the proposal;
actual VAR immutable authority-semantic payload equals the accepted proposal;
no field can be substituted between acceptance, approval and CAS;
changed issuer/root-gate/holder/edge/prerequisite/predecessor invalidates old acceptance;
unrelated global registry churn does not itself alter proposal semantics.
```

## 7. Required replay / replacement / rotation attacks

At minimum attempt:

```text
issuer root K1 accepted -> rotate to K2 -> reuse old target acceptance;
root-gate G1 accepted -> rotate to G2 -> reuse old target acceptance;
accepted EDGE_NONCE N1 -> issue authority for N2;
VAR V1 revoked/expired before use -> replace using proposal that still says predecessor NONE;
holder H1 accepted -> replace holder with H2 while reusing H1 acceptance;
two concurrent issuers race same proposal;
unrelated registry write causes CAS miss -> attempt to reinterpret it as new semantic proposal.
```

Expected behavior:

```text
semantic field change -> old acceptance invalid;
same-subject replacement -> exact terminal predecessor bound;
concurrent same proposal -> one canonical current VAR / idempotent recognition only;
unrelated CAS churn -> retry same proposal after currentness recheck, no remint.
```

## 8. Derived restoration / mutable-write distinction audit

Auditors MUST test the inherited factual-only then later-independent-support path:

```text
1. factual semantic batch B commits under valid exact refinement authority;
2. restoration is initially FALSE/UNKNOWN, so conservative union remains;
3. later semantically equivalent but independently admissible historical support becomes current;
4. restoration proof becomes TRUE without changing B's semantic result.
```

Expected:

```text
no second refinement batch write is required solely for support renewal;
no second semantic subject is minted;
no standalone authority object is created by the derived restoration predicate;
full V25 release-influence noninterference must be TRUE;
every downstream mutable transition still requires its own exact current authority;
any stale downstream VAR remains stale under inherited rules.
```

If the architecture instead silently treats derived restoration as an ungoverned mutable registry grant, qualification fails. If it requires raw support remint and reintroduces V21 starvation, qualification also fails.

## 9. Permanent regression additions

Protocol V30 scenarios through `R9-X270` remain permanent. Add exactly:

```text
R9-X271 — OUTCOME_CONDITIONED_CLEAN_ARCHIVE_QUERY
SETUP:
- immutable historical archive H is independently generated and content-clean;
- favorable beneficiary outcome triggers query of H;
- unfavorable outcome suppresses query;
- queried H would justify privilege relief.
EXPECT:
- outcome -> query control edge exists;
- noninterference FALSE;
- H may support factual recording, but no privilege restoration for benefited lineage.

R9-X272 — OUTCOME_CONDITIONED_ADMISSION_FINALITY
SETUP:
- same independent H is available in both worlds;
- outcome controls admission, finality request or suppression of H.
EXPECT:
- release-control dependence is represented;
- privilege restoration denied;
- clean content alone does not cure outcome-conditioned availability.

R9-X273 — OUTCOME_CONDITIONED_TARGET_ACCEPTANCE_ISSUANCE
SETUP:
- evidence/projection/result are identical and admissible;
- beneficiary outcome controls holder target acceptance or root approval/issuance timing;
- timing determines whether valid authority exists before a semantic expiry boundary.
EXPECT:
- noninterference FALSE;
- no relief through authority-availability conditioning;
- no generic admin/performance-blind assertion substitutes for mechanical proof.

R9-X274 — OUTCOME_PRESENCE_TIMING_SIDECHANNEL
SETUP:
- outcome value is never read;
- outcome existence/publication/access status or outcome-dependent latency controls release path.
EXPECT:
- side channel is an outcome descendant/control influence;
- no privilege restoration.

R9-X275 — EXACT_VAR_PROPOSAL_ROTATION_AND_EDGE_BINDING
SETUP:
- holder accepts proposal under issuer K1/root-gate G1/edge nonce N1;
- before issuance, K1 or G1 rotates, or issuer attempts N2.
EXPECT:
- old acceptance invalid for changed issuer/root-gate/edge;
- fresh exact proposal/acceptance required;
- no field substitution at issuance.

R9-X276 — SAME_SUBJECT_VAR_REPLACEMENT_PREDECESSOR_BINDING
SETUP:
- V1 for subject Q is issued then expires/revokes unused;
- replacement V2 is attempted for same semantic edge;
- attacker reuses proposal/acceptance whose same-subject predecessor is NONE.
EXPECT:
- replacement denied;
- V2 proposal must bind exact terminal V1 predecessor;
- same edge may remain semantically identical without creating a second batch transaction.

R9-X277 — UNRELATED_REGISTRY_CAS_CHURN_NO_SEMANTIC_REMINT
SETUP:
- exact proposal/acceptance are valid;
- unrelated authority registry mutation makes first root-gate CAS attempt miss;
- issuer/holder/semantic/prerequisite fields remain current and unchanged.
EXPECT:
- retry may reuse exact semantic proposal/acceptance after currentness recheck;
- unrelated global predecessor change does not create proposal novelty;
- no starvation/remint solely from unrelated registry churn.

R9-X278 — FACTUAL_BATCH_LATER_INDEPENDENT_RESTORATION
SETUP:
- factual batch B committed validly while restoration FALSE/UNKNOWN;
- later outcome-independent governed support for same semantic result becomes current;
- no semantic class/scope/successor change occurs.
EXPECT:
- no second batch write or new semantic subject solely for support renewal;
- restoration may become TRUE only with full V25 noninterference/provenance/SoD/currentness;
- derived gate grants no standalone mutable authority;
- downstream actions still require fresh/current inherited authority.
```

Permanent totals become:

```text
R7 = 26
R8 = 40
R9 = 278
TOTAL = 344
```

## 10. Outside-family compositions

In addition to all inherited lanes A-H and V30 compositions, attack:

```text
clean evidence x outcome-conditioned lookup
clean evidence x outcome-conditioned admission/suppression
LLM/human outcome knowledge x query/finality request
holder independence x outcome-aware acceptance discretion
root authority x performance/outcome-aware issuance timing
issuer rotation x stale target acceptance
VAR revocation x same-subject predecessor replay
unrelated global registry churn x anti-starvation
factual-only batch x later derived restoration
outcome-presence side channel x expiry/currentness boundary
```

One reproducible bypass/deadlock/replay/ambiguity blocks qualification.

## 11. Clean-pass chronology

After the integrated V25 successor wave and only after its whole-architecture/outside-family impact audit is clean:

```text
freeze exact S0
verify current manifest + every non-self same-subject full Git object identity
compute normative root twice independently
complete subject-bound SA-11
run inherited whole-architecture lanes on exact S0
CP1
NO NORMATIVE WRITE
CP2 on identical root
permanent 344/344 regression
final consistency
self-reference-free candidate
exact QAO-only lineage
exactly one binder-only child
independent external re-audit
```

Any normative byte change after S0 restarts qualification. Any normative byte change after CP1 resets clean-pass credit to zero.

## 12. Progress / firewall

Every completed audit/adjudication/design milestone must be reflected in non-normative GitHub progress metadata with exact subject and qualification-credit status.

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
