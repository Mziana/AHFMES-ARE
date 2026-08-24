# AHFMES ARE-0 — Canonical Authority & Transition Matrix V17

Status: **SOLE CURRENT MACHINE SOURCE / R9-01 EQUIVALENT FINALITY SUPPORT + IMMUTABLE DOMAIN-RESOLVED POST-CUT HANDOFF / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Composition / narrowing

Immutable machine base:

```text
BASE_MATRIX_V16_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V16.md
BASE_MATRIX_V16_GIT_BLOB_SHA = 491766a2e9ec97652d5169f44af8d8112a07a3cb
```

All V16->V1 semantics remain except external finality commit-evidence renewal identity, post-cut observation durability, queue mutability/resolution ownership, and exact bootstrap evidence authority scope are narrowed below.

```text
V17 R9-01 > EXACT V16 > EXACT V15 > ... > EXACT V1
```

R9-02/R9-04/R9-05/R9-06/R9-07 remain unchanged, with post-cut dependency-clear roots additionally consumed wherever inherited reliance/completeness/Safety/capital predicates depend on affected history.

## 1. Internal impact findings closed

Historical exact subject:

```text
60d3d541cd309ab82dc3b70144bf064acb266337
```

Current pre-clean findings normalized to R9-01:

```text
IA20-C01 = FINALITY_RENEWAL_STILL_ONE_WINNER_PAYLOAD
IA20-D01 = GENERIC_LEGACY_QUEUE_CLEAR_IS_CROSS_DOMAIN_UNSOUND
```

Durable pre-Genesis post-cut observation is included in IA20-D01 closure to eliminate crash/restart omission.

`NEW_R9_ROOT = NO`.

## 2. Semantic finality claim is stable; proof artifacts are equivalent support evidence

V14/V16 `FINALITY_EVIDENCE_GENERATION` / one-successor raw proof payload is REVOKED as current authority semantics.

For each `EXTERNAL_FINALIZABLE` source derive non-writable:

```text
FINALITY_SEMANTIC_CLAIM_ROOT[i] = hash(
  BOOTSTRAP_INSTANCE_KEY,
  exact PREGENESIS_SEMANTIC_SOURCE_CUT_ID[i],
  exact <=cut immutability/finality proposition,
  exact <=cut causal/predecessor-closure proposition,
  exact frozen finality-verifier policy root,
  exact forgeability/control-equivalence boundary
)
```

The claim is one semantic proposition. Raw certificates, signatures, proof packages, expiry timestamps, credential rotations, retries and process identities are not scientific coverage identity.

## 3. FinalityVerificationSupportRecord

New immutable pre-system evidence object:

```text
FinalityVerificationSupportRecord
```

Canonical key:

```text
FINALITY_SUPPORT_KEY = hash(
  BOOTSTRAP_INSTANCE_KEY,
  FINALITY_SEMANTIC_CLAIM_ROOT[i],
  exact canonical proof-artifact digest
)
```

Exact authority:

```text
A-PREGENESIS-COMMIT-EVIDENCE-VERIFY
issuer approval = exact bound bootstrap authorization slot
executor = exact bound Bootstrap-Coverage-Audit control
usage = SERVICE / idempotent by FINALITY_SUPPORT_KEY
capital = NO
```

Terminal disposition for one exact support key:

```text
VERIFIED_SUPPORT
REJECTED_SUPPORT
```

`VERIFIED_SUPPORT` requires positive verification under the frozen verifier that the artifact proves the exact current `FINALITY_SEMANTIC_CLAIM_ROOT[i]`. Different source/cut/prefix/verifier/claim cannot satisfy current Genesis.

Multiple `VERIFIED_SUPPORT` records for the same semantic claim are legal and semantically equivalent. They do not compete for an authority slot and cannot select scientific state.

## 4. No raw-proof lottery

No support-specific field may influence:

```text
PREGENESIS_COVERAGE_OPPORTUNITY_KEY
PreGenesisKnowledgeCoverageAttestation semantic payload
PREGENESIS_IMPORT_REVISION_ROOT
CURRENT_PREGENESIS_KNOWLEDGE_OBLIGATION_SET_ROOT
semantic source cut/vector
Champion/comparator/selection
Safety or capital decision
STATIC_GEN0_AUTHORITY_SEMANTICS_COMMITMENT_ROOT
any authority-bearing generation-0 semantic field
```

At SystemGenesis derive only normalized:

```text
FINALITY_SEMANTIC_VERIFICATION_RESULT_ROOT = hash(
  ordered exact FINALITY_SEMANTIC_CLAIM_ROOT set,
  literal VERIFIED_FOR_SYSTEM_GENESIS,
  exact frozen verifier-policy roots
)
```

Raw support identities remain audit provenance only.

Thus P1/P2 that both prove the same claim may coexist without first-writer selection, payload conflict, new Q, new cut or new scientific authority.

## 5. Frozen support-currentness modes

For each external-finalizable source the frozen source contract binds exactly one:

```text
HISTORICALLY_SEALED_FINALITY
CURRENT_SUPPORT_REQUIRED
```

### 5.1 HISTORICALLY_SEALED_FINALITY

A support positively verified at its canonical verification frontier seals the semantic finality claim for that relied frontier. Ordinary later certificate/credential/proof expiry does not retroactively erase the already-established semantic fact.

Only governed evidence that the original semantic claim was invalid, forged, revoked at the relied verification frontier, or contradicted by an actual <=cut correction/reorg invalidates it.

### 5.2 CURRENT_SUPPORT_REQUIRED

SystemGenesis requires:

```text
exists VERIFIED_SUPPORT P
such that CURRENT_SUPPORT_VALID(P, exact Genesis commit frontier) = TRUE
```

If P0 expires, P1/P2 for the exact same semantic claim may be appended and independently verified without changing cut/revision/O/Q/coverage attestation.

If current-support validity cannot be mechanically established through the Genesis commit frontier under frozen verifier/currentness rules, clean `EXTERNAL_FINALIZABLE` treatment is denied and affected obligations use conservative nonfinalizable/UNKNOWN semantics.

Actual <=cut factual change cannot be repaired by another proof artifact; semantic coverage is invalidated and inherited reconciliation/new canonical cut rules apply.

## 6. LOCAL_CAS V15/V16 remains cut-scoped

V15/V16 LOCAL_CAS semantics remain fully current:

```text
LOCAL_CAS COMPLETE
requires transactionally comparable <=cut semantic prefix fence
independent of harmless >cut tail growth
```

No global-head evidence generation or proof-support mechanism can substitute for this cut-scoped predicate.

## 7. Durable pre-Genesis post-cut observation

A governed-known material >cut fact must not exist only in volatile process memory before the generation-0 queue is created.

New immutable pre-system evidence object:

```text
PreGenesisPostCutObservationRecord
```

Canonical key:

```text
POST_CUT_PRECOMMIT_OBSERVATION_KEY = hash(
  BOOTSTRAP_INSTANCE_KEY,
  exact source identity,
  stable source/fact identity,
  exact FIRST_POST_CUT_GOVERNED_INFORMATION_TIME under frozen tie-break
)
```

Exact authority:

```text
A-PREGENESIS-POSTCUT-OBSERVE
issuer approval = exact bound bootstrap slot + frozen source contract
executor = exact frozen capture/observation producer for that source
usage = SERVICE / idempotent by exact observation key
capital = NO
```

Payload binds source evidence/provenance, semantic order relative to canonical cut, first governed information frontier, capture-control identity and causal/predecessor links.

Capture producer cannot choose materiality. Applicability is derived only under frozen `PREGENESIS_MATERIALITY_APPLICABILITY_ROOT`.

A durable observation record serialized before the V16 `POST_CUT_HANDOFF_COMMIT_FRONTIER_ROOT` survives crash/restart and MUST be included in the atomic handoff derivation.

If a discretionary capture surface can suppress material post-cut facts and no independent/self-verifying completeness theorem exists, `UNKNOWN_POST_CUT_TAIL_OBLIGATION` is mandatory.

## 8. Generation0PostCutCorrectionQueue #0 is immutable handoff evidence

V14/V16 queue remains mandatory in every legal SystemGenesis, but any mutable post-genesis per-obligation queue-state semantics are REVOKED.

Current queue state is exactly:

```text
GENESIS_HANDOFF_FROZEN
```

Queue payload atomically binds:

```text
PREGENESIS_SEMANTIC_SOURCE_CUT_VECTOR_ROOT
POST_CUT_HANDOFF_COMMIT_FRONTIER_ROOT
ordered POST_CUT_HANDOFF_SOURCE_FENCE set
exact durable PreGenesisPostCutObservationRecord identities included before frontier
POST_CUT_PRECOMMIT_OBLIGATION_SET_ROOT
POST_CUT_HANDOFF_COMPLETENESS_ROOT
UNKNOWN_POST_CUT_TAIL obligations
POST_CUT_OBLIGATION_CLASS_RESOLVER_ROOT
FINALITY_SEMANTIC_VERIFICATION_RESULT_ROOT
```

No writer may delete, reclassify, reconcile or mutate an obligation inside this queue after Genesis.

## 9. Frozen per-domain resolver map

`STATIC_GEN0_AUTHORITY_SEMANTICS_COMMITMENT_ROOT` and bootstrap target authorization additionally bind exact:

```text
POST_CUT_OBLIGATION_CLASS_RESOLVER_ROOT
```

This is a total mapping from every possible material post-cut obligation class to exact pre-existing canonical post-genesis evidence/authority families.

At minimum:

```text
SCIENTIFIC_LEGACY_SEARCH_EVIDENCE_DEBT
  -> A-LEGACY-RECONCILE plus exact canonical Evidence/Exposure/search-debt records required by the fact class

BROKER_ACCOUNT_EXPOSURE
  -> A-RUNTIME-RECONCILE plus exact canonical CapitalRiskReservation/BrokerMutation/reconciliation evidence required by the fact class

SAFETY_CONTAINMENT_OBSERVATION
  -> A-SAFETY-OBSERVE plus exact canonical Safety/reconciliation evidence required by the fact class
```

Any additional class must map to an exact already-existing canonical authority/evidence family. Missing, ambiguous or overlapping resolver mapping => affected dependency remains OPEN/UNKNOWN and no clean privilege is available.

No generic fallback resolver exists.

V14 generic:

```text
A-LEGACY-RECONCILE[POST_CUT_PRECOMMIT]
```

is REVOKED as an authority to mutate/clear arbitrary queue obligations. `A-LEGACY-RECONCILE` remains usable only for the scientific/legacy domain already authorized by inherited semantics.

## 10. Resolution is derived, not written into queue

Derived/non-writable current roots:

```text
POST_CUT_HANDOFF_OPEN_ROOT[class]
POST_CUT_HANDOFF_DEPENDENCY_CLEAR[class]
```

A dependency clears only when exact canonical domain records required by `POST_CUT_OBLIGATION_CLASS_RESOLVER_ROOT` positively resolve the exact obligation and required causal predecessors.

Examples:

```text
LegacyScientificStateCorrectionRecord alone cannot clear broker exposure
RuntimeReconciliationRecord alone cannot clear scientific/evidence debt
Safety observation cannot clear unrelated scientific/broker obligation
an unrelated clean record cannot clear another class
wall-clock silence/no new event cannot clear UNKNOWN
```

UNKNOWN clears only through positive canonical completeness/resolution evidence under the frozen resolver/source/materiality rules.

`POST_CUT_HANDOFF_DEPENDENCY_CLEAR = TRUE` grants no authority; it only removes one adverse prerequisite.

## 11. SystemGenesis terminal transaction V17

SystemGenesis requires all V16 predicates plus:

```text
external-finalizable semantic claims satisfy exact frozen support-currentness mode
normalized finality semantic verification result exact
every durable post-cut observation serialized/ordered before handoff commit frontier included
unprovable tail completeness represented UNKNOWN
immutable queue #0 created atomically
resolver map exact/static/total for every present/possible obligation class
bootstrap slot consumed + journal terminalized in same transaction
```

For local co-fenced sources, V16 same-transaction serialization totally classifies observation-before vs observation-after Genesis. For external/non-cofenced tails without positive complete-through-commit theorem, ambiguity remains UNKNOWN rather than clean empty.

## 12. Dependency-scoped no-window consequences

```text
POST_CUT_HANDOFF_DEPENDENCY_CLEAR[SCIENTIFIC/EVIDENCE] = FALSE
-> no clean/no-debt lineage assertion for affected dependency
-> dependent proof reliance, Champion eligibility, Promotion and revalidation cannot ignore handoff debt

POST_CUT_HANDOFF_DEPENDENCY_CLEAR[BROKER/EXPOSURE/SAFETY] = FALSE
-> normal new-risk denied for affected account/scope
-> only inherited reconcile/cancel-risk-increase/monotonic-reduce-or-close containment remains legal
```

A favorable post-cut fact cannot directly mutate generation-0 Champion, RoleManifest, static Safety policy, comparator/accounting/error rules, source contract or governance semantics.

## 13. Exact bootstrap capability scope V17

Target-scoped sealed bootstrap authorization scope is exactly:

```text
A-PREGENESIS-IMPORT[INITIAL]
A-PREGENESIS-IMPORT[RECONCILE]
A-PREGENESIS-COVERAGE-AUDIT
A-PREGENESIS-COMMIT-EVIDENCE-VERIFY
A-PREGENESIS-POSTCUT-OBSERVE
A-SYSTEM-GENESIS
```

V14/V15 commit-evidence refresh authorities are no longer current writers.

`A-PREGENESIS-COMMIT-EVIDENCE-VERIFY` can write only FinalityVerificationSupportRecord.
`A-PREGENESIS-POSTCUT-OBSERVE` can write only PreGenesisPostCutObservationRecord.
Neither grants import, scientific, Safety, capital, execution or broker authority.

Changed verifier policy, capture producer, resolver map or source contract after sealed authorization is a static conflict.

## 14. Crash / retry / concurrency theorem

```text
P0 expires; P1/P2 both valid same claim
-> both may exist as equivalent supports
-> no one-winner payload / no IntegrityDefect merely because proof bytes differ
-> normalized semantic result identical

D durable observation commits before crash
-> retry must include D if ordered before handoff frontier

D and local Genesis race
-> V16 serialization order decides: before => included; after => canonical postgenesis evolution; conflict => transaction retry

broker/Safety obligation exists
-> legacy reconciliation alone cannot clear dependency
-> exact domain evidence required

actual <=cut mutation
-> neither support records nor post-cut resolver can preserve stale semantic coverage
```

No partial SystemGenesis/queue/bootstrap state is legal.

## 15. Forbidden control planes

```text
one raw proof successor payload treated as unique authority winner
semantically equivalent proof packages conflict merely because bytes differ
raw support identity affects scientific/Safety/capital/gen0 semantics
ephemeral governed post-cut fact forgotten after crash
queue obligation mutated/deleted post-Genesis
generic legacy reconciler clears broker/Safety obligation
unrelated domain record clears another obligation
UNKNOWN clears by silence/time
capture suppression represented clean without independent completeness theorem
pending handoff ignored by reliance/revalidation/normal-new-risk
support evidence used to hide <=cut correction
```

All inherited forbidden controls remain.

## 16. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
