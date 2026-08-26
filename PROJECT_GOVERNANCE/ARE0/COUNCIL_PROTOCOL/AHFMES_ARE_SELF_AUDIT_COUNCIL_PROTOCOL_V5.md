# AHFMES ARE — Self-Audit Council Protocol V5

Status: **MANDATORY PRE-EXTERNAL-AUDIT GOVERNANCE / BIG-WAVE WHOLE-TREE DISCIPLINE / WAVE-6 EXTENSIONS / STATELESS NORMATIVE PROTOCOL / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable protocol base:

```text
BASE_PROTOCOL_V4_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V4.md
BASE_PROTOCOL_V4_GIT_BLOB_SHA = 81a71c71556cea69d8d348b26017c1968b8ee7d3
```

All V4 protocol rules remain, except current-manifest reference and regression ceiling are superseded below.

## 1. Current manifest

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V4.md
```

is the only current normative authority path manifest.

## 2. Big-wave sequencing unchanged

Normalize all reproducible findings, write one integrated correction tree, attack exact bytes, and authorize Clean Pass #1 only if no reproducible blocker remains. Micro-patch convergence is not closure evidence.

## 3. Wave-6 attack overlays

Attack:

```text
multiple invalidation events on one completeness-resolution generation
same next generation receiving multiple successor SLOT_KEYs
first invalidation tie/order ambiguity
late invalidation arriving between successor proof read and commit
stale successor commit ignoring changed invalidation-set root
previously invalidated resolution becoming effective again after premise repair without successor generation
retry after invalidation-set advance minting a fresh slot instead of reusing same successor slot
```

## 4. Permanent regression extension

All earlier R7/R8 and R9-X01..R9-X62 remain mandatory.

Wave-6 adds:

```text
R9-X63 resolution g0 receives two material invalidations I1/I2 -> exactly one g1 SLOT_KEY anchored to canonical first invalidation; both retained in invalidation set
R9-X64 g1 successor reads invalidation set {I1}; I2 arrives before commit -> stale g1 transaction loses; retry uses same g1 SLOT_KEY with {I1,I2}
R9-X65 g0 invalidated then original premise repaired without g1 -> g0 remains permanently ineffective
R9-X66 two invalidations with equal information time -> stable premise/dependency tie-break selects one FIRST invalidation key deterministically
R9-X67 retry/session/process wrapper after invalidation-set change -> no new successor slot
```

## 5. Exact-root discipline

The inherited exact byte-root serialization and post-Pass-#1 no-write rule remain unchanged. Root membership comes from Normative Authority Manifest V4.

## 6. Static boundary

This protocol grants no ARE-0 closure, implementation, P001 substantive research, production or PR-merge authority.