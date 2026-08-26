# AHFMES ARE-0 — Legacy Authority Quarantine Policy V2

Status: **NORMATIVE CLOSURE / SUBJECT-BOUND AUTHORITY HYGIENE / NO MACHINE-RIGHT GRANT / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable policy base:

```text
BASE_QUARANTINE_POLICY_V1_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_LEGACY_AUTHORITY_QUARANTINE_POLICY_V1.md
BASE_QUARANTINE_POLICY_V1_GIT_BLOB_SHA = 39ad0491105a30aaef9a7bb5ffe911a7ca1bbea4
```

All V1 rules remain except V1 §2 literal `Manifest V6` routing and V1 §4 inspection sufficiency are replaced/narrowed here.

This policy cannot add machine rights.

## 1. Current-manifest resolver

Current machine/closure authority is determined only through the normative stable binding:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_CURRENT_NORMATIVE_MANIFEST_BINDING.md
```

For exact subject/tree `S`, let:

```text
M = SUBJECT_BOUND_CURRENT_NORMATIVE_MANIFEST(S)
```

as validated by that binding and the current Protocol.

No literal historical manifest version embedded in an older policy/protocol, no PR metadata, no Current Authority Index, no audit handoff and no unlisted file may substitute for `M`.

For every repository path `P` not listed in `M`:

```text
P NOT IN M
=> P_CURRENT_MACHINE_AUTHORITY = NONE
=> P_CURRENT_CLOSURE_AUTHORITY = NONE
=> P_CURRENT_AUDIT_RULE_AUTHORITY = NONE
=> any self-claim of normative/current/canonical/approved/authority/ready/closed/audited status
   = HISTORICAL_TEXT_ONLY unless the current manifest positively grants the exact path a role
```

A stale or ambiguous binding/manifest resolution is a closure blocker; it never falls back to an older manifest.

## 2. Recursive inspection frontier

Before Clean Pass #1, SA-11 must inspect the exact recursive `PROJECT_GOVERNANCE` blob frontier of the exact candidate subject, including nested subdirectories such as `DIARY`.

The evidence must bind:

```text
exact subject commit/tree
exact stable manifest-binding blob
exact resolved current Manifest path/blob
complete recursive governance path/blob frontier
exact current normative-member set N
exact unlisted governance set U = G - N
```

`G-N` proves coverage/classification scope only. It is **not** sufficient evidence that authority-like claims were individually detected and reviewed.

## 3. Mechanical trigger ledger

For every inspectable text blob in `U`, SA-11 must run the same declared trigger vocabulary across the complete file. The minimum case-insensitive trigger vocabulary is:

```text
normative
current
canonical
approved
authority
authorized
ready
closed
audited
audit pass
external audit
implementation authority
production authority
merge authority
```

Equivalent explicit status/authority phrases discovered during inspection are added conservatively; reducing the detector after observing results is forbidden.

Every trigger hit must appear in a non-normative `AUTHORITY_CLAIM_TRIGGER_LEDGER` with:

```text
exact path
exact Git blob ID
exact line/range where available
bounded quote or exact locator
trigger term/class
context disposition = AUTHORITY_LIKE_SELF_CLAIM / NON_CLAIM_CONTEXT / UNKNOWN
```

A text blob that cannot be completely inspected, a binary/opaque governance blob with plausible authority semantics, a missing locator, or an omitted trigger hit yields `UNKNOWN`; SA-11 cannot PASS until conservatively resolved.

## 4. Per-claim quarantine inventory

Every ledger entry disposed as `AUTHORITY_LIKE_SELF_CLAIM` or `UNKNOWN` must appear in `LEGACY_AUTHORITY_QUARANTINE_RECORD` with at minimum:

```text
exact path
exact Git blob ID
exact location/range where available
bounded verbatim quote or exact claim locator
claim class
classification = HISTORICAL_TEXT_ONLY / QUARANTINED
```

A claim is authority-like when the document asserts or presents its own status, role, precedence, acceptance, readiness, closure, audit qualification, implementation permission, production permission or equivalent current-looking authority. Generic discussion of the words in a policy/example may be disposed `NON_CLAIM_CONTEXT` only with exact locator evidence.

Ambiguous context is classified conservatively as an authority-like claim; ambiguity cannot be used to avoid an entry.

A detected unlisted self-claim is not a blocker only if it is positively quarantined and no current machine/closure/audit semantic dependency relies on that unlisted path.

An unlisted path actually relied upon for current semantics is a blocker: add it through a pre-clean integrated normative change or remove the dependency.

## 5. Evidence freshness

The frontier, trigger ledger and quarantine record are exact-subject evidence.

Any change before dispatch to:

```text
subject tree
stable manifest binding
resolved manifest/member set
any inspected governance blob
any authority-like claim or its locator
```

makes SA-11 evidence stale and requires a full subject-consistent refresh before dispatch.

After Clean Pass #1, a normative-member byte/path/blob change resets clean-pass credit under Protocol. A non-normative governance change that affects the inspection frontier does not silently change the normative root but blocks final consistency/dispatch until SA-11 evidence is refreshed.

## 6. No outcome-shaped detector

Detector vocabulary, claim-class rules, and inspection frontier must be fixed before observing the resulting claim dispositions for the exact qualification run. They may be expanded conservatively after discovery; they may not be narrowed to remove inconvenient claims.

## 7. Static boundary

This policy grants no machine transition, writer, scientific privilege, capital privilege, ARE-0 closure, implementation, P001 substantive research, production, live/paper trading or PR-merge authority.
