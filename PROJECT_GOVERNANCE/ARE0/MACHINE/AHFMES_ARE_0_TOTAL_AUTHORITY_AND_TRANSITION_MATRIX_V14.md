# AHFMES ARE-0 — Canonical Authority & Transition Matrix V14

Status: **SOLE CURRENT MACHINE SOURCE / R9-01 SEMANTIC-CUT VS COMMIT-EVIDENCE SEPARATION + POST-CUT PRECOMMIT HANDOFF / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 0. Composition / narrowing

Immutable machine base:

```text
BASE_MATRIX_V13_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_TOTAL_AUTHORITY_AND_TRANSITION_MATRIX_V13.md
BASE_MATRIX_V13_GIT_BLOB_SHA = 70bf65286fb95d00dbdf6bffe4f7ab4f2cabb695
```

All V13->V1 semantics remain except source-currentness, commit fencing/finality evidence, post-cut precommit knowledge handling, and SystemGenesis handoff are narrowed below.

```text
V14 R9-01 > EXACT V13 > ... > EXACT V1
```

R9-02/R9-04/R9-05/R9-06/R9-07 remain unchanged.

## 1. Historical external blockers closed together

Exact historical externally audited candidate:

```text
63ca962729facb6aaed322a97689fb890b6dac66
```

Reproducible blockers, all normalized to R9-01:

```text
POST_CUT_PRECOMMIT_FACT_HAS_NO_DURABLE_HANDOFF
LOCAL_CAS_POSTCUT_HEAD_ADVANCE_HAS_NO_TOTAL_RECOVERY
EXTERNAL_FINALITY_PROOF_RENEWAL_ONE_SLOT_DEADLOCK
```

No new R9 root is introduced.

## 2. Three-layer source identity theorem

Current source state is separated into exact non-interchangeable layers:

```text
A. SEMANTIC_SOURCE_CUT_STATE
B. COMMIT_EVIDENCE_STATE
C. POST_CUT_PRECOMMIT_HANDOFF_STATE
```

### 2.1 Semantic source cut state

For source `i`:

```text
PREGENESIS_SEMANTIC_SOURCE_CUT_ID[i] = hash(
  source identity,
  source-contract identity,
  exact semantic cut ordinal/version/watermark,
  exact included-prefix/event-set root through cut,
  exact retroactive-correction disposition,
  exact predecessor/causal-closure root through cut,
  canonical information frontier through cut
)
```

Raw mutable latest-head identity, renewable certificate/proof bytes, proof expiry timestamp, retry counter and scheduler time are excluded.

`PREGENESIS_SEMANTIC_SOURCE_CUT_VECTOR_ROOT` is the ordered multi-source fold of these semantic IDs plus frozen source contract, cutoff rule, cross-source causal closure and unresolved nonfinalizable-source root.

The inherited `FIRST_CANONICAL_PREGENESIS_SOURCE_CUT_VECTOR_ROOT` is interpreted as the first canonical **semantic** vector. It cannot be changed by harmless post-cut tail growth or renewal mechanics.

### 2.2 Mechanical commit evidence state

Mechanical evidence proves that the already-selected semantic cut remains admissible at commit. It cannot select or mutate scientific history.

For every source define exactly one current evidence chain:

```text
SOURCE_COMMIT_EVIDENCE_SLOT_KEY[i] = hash(
  BOOTSTRAP_INSTANCE_KEY,
  PREGENESIS_SEMANTIC_SOURCE_CUT_ID[i]
)
```

and monotone canonical generations:

```text
SOURCE_COMMIT_EVIDENCE_GENERATION[i,g]
```

Generation payload binds exact semantic cut ID and source-class-specific evidence. It cannot alter source contract, semantic cut, included-prefix root, revision `r`, knowledge-obligation root `O`, materiality rule, authorization, RoleManifest, Safety, comparator, governance or capital semantics.

Only one current generation may exist for one slot. Same generation/same payload is idempotent; conflicting payload is IntegrityDefect. `g+1` exists only under exact deterministic successor conditions below.

### 2.3 Post-cut precommit handoff state

For every material/applicable fact with semantic order strictly `> cut` that becomes governed-knowable after the canonical semantic cut is fixed but before atomic SystemGenesis commit, derive append-only:

```text
POST_CUT_PRECOMMIT_OBLIGATION_KEY = hash(
  BOOTSTRAP_INSTANCE_KEY,
  PREGENESIS_SEMANTIC_SOURCE_CUT_VECTOR_ROOT,
  FIRST_POST_CUT_GOVERNED_INFORMATION_TIME,
  stable source/fact identity under frozen tie-break
)
```

Unknown completeness of a material post-cut tail creates exact conservative obligation:

```text
UNKNOWN_POST_CUT_TAIL_OBLIGATION
```

No actor may omit an obligation by delaying capture, delaying commit, or claiming that `>cut` means unknowable-to-genesis.

## 3. Coverage identity does not bind renewable mechanical evidence bytes

V11 one semantic opportunity remains:

```text
PREGENESIS_COVERAGE_OPPORTUNITY_KEY = hash(
  BOOTSTRAP_INSTANCE_KEY,
  current PREGENESIS_IMPORT_REVISION_ROOT[r],
  CURRENT_PREGENESIS_KNOWLEDGE_OBLIGATION_SET_ROOT,
  GENESIS_CUTOFF_RULE_ROOT,
  PREGENESIS_MATERIALITY_APPLICABILITY_ROOT
)
```

V12/V13 coverage is narrowed as follows:

```text
PreGenesisKnowledgeCoverageAttestation
  binds exact semantic source cut vector,
  source completeness through semantic cut,
  causal closure through semantic cut,
  source contract / SoD / unknown disposition,
  but NOT raw renewable SOURCE_COMMIT_EVIDENCE_GENERATION payload identity.
```

A mechanical evidence refresh for the same exact semantic cut therefore:

```text
does not change Q
does not create a second coverage attestation
does not change r or O
does not remint canonical cut
does not change scientific coverage disposition
```

A factual `<=cut` correction/reorg changes or invalidates semantic cut truth and cannot use the mechanical refresh path.

## 4. LOCAL_CAS cut-scoped fence semantics

For `LOCAL_CAS`, commit evidence must prove the semantic prefix through the selected cut is still exact while allowing unrelated strictly-post-cut tail growth.

Preferred admissible form:

```text
LOCAL_CAS_CUT_FENCE = immutable/versioned cut-scoped prefix identity
```

If the local store only exposes a mutable global head, deterministic refresh is legal only when an exact independently checkable delta proof establishes:

```text
old head H_g -> new head H_g+1
all changed events are strictly > semantic cut
no <=cut add/remove/reorder/rewrite
no predecessor/causal reinterpretation of <=cut prefix
no source-contract/currentness change
```

Then:

```text
SOURCE_COMMIT_EVIDENCE_GENERATION[g] -> [g+1]
```

under exact authority `A-PREGENESIS-COMMIT-EVIDENCE-REFRESH[LOCAL_CAS]`.

This refresh is SERVICE/idempotent under the single successor slot and grants zero scientific/coverage authority.

Repeated harmless `>cut` appends may advance evidence generation but cannot create Q1/Q2 coverage opportunities and cannot starve SystemGenesis merely because the mutable tail grows. Genesis CAS-compares the current admissible cut-scoped fence/evidence generation in its local transaction.

Any inability to prove tail-only change yields conservative deny/UNKNOWN; no fabricated refresh.

## 5. EXTERNAL_FINALIZABLE renewable finality evidence

For `EXTERNAL_FINALIZABLE`, semantic cut identity is independent of renewable proof artifact identity.

Define:

```text
FINALITY_EVIDENCE_SLOT_KEY[i] = SOURCE_COMMIT_EVIDENCE_SLOT_KEY[i]
FINALITY_EVIDENCE_GENERATION[i,g]
```

A current generation is valid only when its proof verifies under the frozen verifier for the exact same semantic cut/prefix.

Deterministic successor `g+1` is legal only if current `g` becomes mechanically non-current because of expiry/revocation/credential rotation/evidence-format renewal **without any factual change to <=cut semantics**, and fresh proof positively verifies the exact same semantic cut/prefix.

Exact authority:

```text
A-PREGENESIS-COMMIT-EVIDENCE-REFRESH[EXTERNAL_FINALIZABLE]
```

Rules:

```text
one successor slot per predecessor generation
concurrent competing renewals collide on that successor slot
renewal cannot choose another/older/favorable cut
renewal cannot change revision or knowledge root
renewal cannot hide <=cut correction/reorg
renewal cannot create scientific coverage opportunity
```

If proof failure arises because <=cut factual truth changed or cannot be positively preserved, renewal-only path is denied and semantic reconciliation/fresh coverage is required.

## 6. EXTERNAL_NONFINALIZABLE

No mechanical refresh can promote `EXTERNAL_NONFINALIZABLE` to COMPLETE.

Affected semantic obligations remain `SOURCE_UNKNOWN_CONSERVATIVE` and post-cut tail completeness remains `UNKNOWN_POST_CUT_TAIL_OBLIGATION` where applicable. Inherited Safety/authority predicates that require positive completeness remain denied.

## 7. Post-cut governed-knowledge frontier

Define derived exact:

```text
POST_CUT_PRECOMMIT_GOVERNED_FRONTIER_ROOT
POST_CUT_PRECOMMIT_OBLIGATION_SET_ROOT
POST_CUT_PRECOMMIT_COMPLETENESS_ROOT
```

These are derived from the frozen source contract + materiality rule over observations strictly after the semantic cut and before the atomic Genesis commit frontier.

Possible completeness dispositions:

```text
POST_CUT_TAIL_COMPLETE
POST_CUT_TAIL_UNKNOWN_CONSERVATIVE
```

Known material post-cut facts cannot be placed into UNKNOWN merely for convenience. If the external tail cannot be proven complete, UNKNOWN is mandatory.

## 8. Atomic SystemGenesis handoff

SystemGenesis terminal transaction requires all inherited predicates plus exact current:

```text
PREGENESIS_SEMANTIC_SOURCE_CUT_VECTOR_ROOT
all required SOURCE_COMMIT_EVIDENCE_GENERATION current/valid
POST_CUT_PRECOMMIT_GOVERNED_FRONTIER_ROOT
POST_CUT_PRECOMMIT_OBLIGATION_SET_ROOT
POST_CUT_PRECOMMIT_COMPLETENESS_ROOT
```

In the same local atomic transaction that consumes bootstrap authority and creates generation-0, Genesis must seed exact:

```text
Generation0PostCutCorrectionQueue #0
```

with every current `POST_CUT_PRECOMMIT_OBLIGATION_KEY` plus any `UNKNOWN_POST_CUT_TAIL_OBLIGATION`.

Exact creation/seed edge:

```text
A-SYSTEM-GENESIS
```

No separate caller-controlled omission step exists.

`Generation0PostCutCorrectionQueue #0` is not clean-history evidence and grants no scientific/Safety/capital privilege.

## 9. Post-genesis reconciliation / terminality

Exact writer for queue resolution:

```text
A-LEGACY-RECONCILE
executor = inherited Legacy-reconciliation AUDIT control
```

Each pending obligation resolves only by monotone correction into the canonical Legacy/Evidence/Exposure/search-debt/scientific state as applicable, or by a positive frozen-rule NON_APPLICABLE proof where legally possible.

States:

```text
PENDING
UNKNOWN_CONSERVATIVE
RECONCILED
NON_APPLICABLE_PROVEN
```

`RECONCILED` and `NON_APPLICABLE_PROVEN` are terminal for that obligation identity. UNKNOWN cannot silently become absent.

Until all privilege-relevant obligations are terminally reconciled, derived gate:

```text
POST_CUT_PRECOMMIT_CLEAN_PRIVILEGE_VALID = FALSE
```

Consequences include denial of any claim that depends on clean/no-debt initial lineage and denial of normal new-risk privilege where inherited Safety/capital predicates require resolved history. Conservative risk-reduction/reconciliation/emergency actions remain governed by inherited rules.

## 10. Race / crash / retry theorem

```text
harmless LOCAL_CAS >cut append before Genesis
-> stale mechanical evidence only
-> deterministic cut-fence refresh
-> same semantic cut/Q/A
-> Genesis remains drainable

finality proof expires; facts unchanged
-> old evidence generation non-current
-> exactly one successor generation may renew same semantic cut
-> same Q/A
-> Genesis remains drainable

material >cut fact becomes governed-known before Genesis
-> post-cut obligation appears
-> must be atomically seeded at Genesis
-> cannot be omitted by commit delay

unknown external post-cut tail completeness
-> UNKNOWN_POST_CUT_TAIL_OBLIGATION seeded
-> no clean privilege

<=cut factual change/reorg
-> mechanical refresh DENIED
-> semantic coverage/currentness invalid
-> reconciliation/fresh coverage required
```

Crash before terminal transaction leaves bootstrap unconsumed and queue uncreated. Retry recomputes current mechanical evidence and post-cut handoff roots. Crash after atomic commit leaves exactly one generation-0 queue and consumed bootstrap slot. No partial queue/genesis state is legal.

## 11. Exact new authority rows

| Authority | Issuer approval | Executor | Usage | Exact prerequisites | Capital |
|---|---|---|---|---|---|
| `A-PREGENESIS-COMMIT-EVIDENCE-REFRESH[LOCAL_CAS]` | bound bootstrap slot | Bootstrap-Coverage-Audit | SERVICE / one deterministic successor per evidence generation | same semantic cut; positive tail-only delta/prefix proof; no <=cut change | NO |
| `A-PREGENESIS-COMMIT-EVIDENCE-REFRESH[EXTERNAL_FINALIZABLE]` | bound bootstrap slot | Bootstrap-Coverage-Audit | SERVICE / one deterministic successor per evidence generation | predecessor mechanically non-current; fresh proof same semantic cut/prefix; no factual <=cut change | NO |
| `A-SYSTEM-GENESIS` | inherited bound slot | Genesis | ONE_SHOT terminal | inherited predicates + current mechanical evidence + atomic post-cut obligation queue seed | NO |
| `A-LEGACY-RECONCILE[POST_CUT_PRECOMMIT]` | inherited GovernanceRoot/Audit discipline | Legacy-reconciliation AUDIT | serial CAS | exact pending queue obligation; monotone canonical correction; no static semantic mutation | NO |

Commit-evidence refresh authority cannot issue/import/reconcile scientific history, attest coverage, change authorization, or create capital authority.

## 12. Forbidden control planes

```text
raw latest head/proof bytes used to remint scientific opportunity
proof renewal selects different cut
LOCAL_CAS >cut append creates new Q
mechanical evidence refresh hides <=cut correction
operator delays Genesis after seeing D>cut then omits D
known D>cut treated absent because semantic cut already frozen
UNKNOWN post-cut tail represented complete/clean
Genesis creates generation-0 without atomic post-cut queue seed
queue obligation deleted rather than terminally reconciled
pending/UNKNOWN queue used as clean-history privilege
refresh principal gains importer/Genesis/scientific/capital authority by implication
```

All inherited forbidden controls remain.

## 13. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
