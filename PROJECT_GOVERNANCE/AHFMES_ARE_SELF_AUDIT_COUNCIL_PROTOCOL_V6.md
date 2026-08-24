# AHFMES ARE — Self-Audit Council Protocol V6

Status: **MANDATORY PRE-EXTERNAL-AUDIT GOVERNANCE / BIG-WAVE WHOLE-TREE DISCIPLINE / WAVE-7 EXTENSIONS / STATELESS NORMATIVE PROTOCOL / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable protocol base:

```text
BASE_PROTOCOL_V5_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V5.md
BASE_PROTOCOL_V5_GIT_BLOB_SHA = a9fe27e8dabb8790307aa65fc616985f18d07191
```

All V5 protocol rules remain except current-manifest reference and regression ceiling are superseded below.

## 1. Current manifest

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V5.md
```

is the only current normative authority path manifest.

## 2. Wave-7 attack overlays

Attack:

```text
late-discovered invalidation with older underlying event-time attempts to backdate invalidation information-time
first invalidation anchor changes after successor slot already born
ancestor g0 invalidation discovered after g1 RESOLVED but g1 remains effective
ancestor invalidation arrives before descendant commit but stale descendant transaction still wins
successor payload covers direct invalidations but omits uncovered ancestor invalidations
same information-time direct/inherited invalidations lack deterministic tie-break
```

## 3. Permanent regression extension

All earlier R7/R8 and R9-X01..R9-X67 remain mandatory.

Wave-7 adds:

```text
R9-X68 g1 RESOLVED, then new g0 invalidation becomes knowable -> g1 becomes sticky-invalid; g2 required
R9-X69 ancestor invalidation becomes knowable before g1 commit -> ancestor-closure CAS advances; stale g1 transaction loses
R9-X70 late discovery at T2 concerning event T0 -> invalidation information-time T2; existing first invalidation anchor/slot identity unchanged
R9-X71 direct and inherited invalidation at same information-time -> frozen class/identity tie-break deterministic
R9-X72 successor resolution must bind complete effective invalidation set including uncovered ancestor invalidations
```

## 4. Exact-root / big-wave discipline

Inherited byte-root serialization and no-write-after-Pass-#1 rules remain unchanged. Root membership comes from Normative Authority Manifest V5.

Clean Pass #1 remains unauthorized until exact integrated impact attack reports no reproducible blocker.

## 5. Static boundary

This protocol grants no ARE-0 closure, implementation, P001 substantive research, production or PR-merge authority.