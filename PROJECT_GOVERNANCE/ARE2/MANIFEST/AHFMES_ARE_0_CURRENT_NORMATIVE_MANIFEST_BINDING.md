# AHFMES ARE-0 — Current Normative Manifest Binding

Status: **NORMATIVE CLOSURE ROUTING / STABLE PATH / STRUCTURAL_GENERATION_S1 / NO IMPLEMENTATION AUTHORITY**

```text
CURRENT_NORMATIVE_MANIFEST_PATH = PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V41.md
CURRENT_NORMATIVE_MANIFEST_GENERATION = 41
```

This stable path is the sole current manifest resolver. For exact subject `S`,
resolution is valid only if Manifest V39 exists in `S` at this S1 path, lists
this exact binding blob, current Quarantine Policy V9 and Protocol V36 resolve
membership only through this binding, all non-self manifest constraints resolve
in the same `S`, and no PR, index, handoff, QAO, JQO, or historical document
overrides it. Pre-S1 absolute paths have no resolving power; only the S1 path
namespace (`PROJECT_GOVERNANCE/ARE0/...`) is current.

This binding intentionally does **not** contain a Manifest V39 blob hash. The
manifest binds this binding's hash; adding the manifest hash here would create
a circular identity dependency.

Missing, ambiguous, stale, conflicting, malformed, cross-subject, or
non-current resolution fails closed with no historical fallback or prefix
repair. Path matching is byte-exact and case-sensitive ordinal comparison;
any non-canonical spelling, casing variant, or prefix/partial form fails
closed before hashing. This binding grants no machine, scientific, Safety,
capital, implementation, production, trading, merge, or closure authority.
Any byte change after CP1 resets clean-pass credit.
