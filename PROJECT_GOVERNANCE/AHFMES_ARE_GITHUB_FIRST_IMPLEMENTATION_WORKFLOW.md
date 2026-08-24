# AHFMES ARE — GitHub-First Implementation Workflow

Status: **FUTURE IMPLEMENTATION WORKFLOW / NO CURRENT IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

## 1. Purpose

This document freezes the intended engineering workflow for future AHFMES Autonomous Research Engine (ARE) implementation.

It does **not** authorize implementation now.

The current ARE phase remains formal design + external adversarial audit.

## 2. Engineering environment constraint

The designated remote engineer is assumed to have GitHub repository access but **no reliable access to the local Windows/MT5 research environment**.

Therefore source implementation must not depend on direct local edits.

Canonical workflow:

```text
FORMAL DESIGN CLOSED
        ↓
SEPARATE IMPLEMENTATION AUTHORITY
        ↓
CREATE / AUTHORIZE EXACT GITHUB IMPLEMENTATION BRANCH
        ↓
ENGINEER IMPLEMENTS IN GITHUB
        ↓
REMOTE SOURCE / CONTRACT AUDIT
        ↓
CORRECTION CYCLE IN GITHUB IF REQUIRED
        ↓
FREEZE EXACT AUDITED COMMIT SHA
        ↓
PULL THAT EXACT SHA TO LOCAL RESEARCH CHECKOUT
        ↓
ANTIGRAVITY LOCAL INTEGRATION / TEST HARNESS
        ↓
UNIT + REGRESSION + CONCURRENCY + FAULT + REPLAY TESTS
        ↓
LOCAL EVIDENCE PUBLICATION BACK TO GITHUB
        ↓
INDEPENDENT ADJUDICATION
        ↓
NEXT AUTHORITY GATE
```

No engineer should silently patch the local checkout and then treat local state as canonical source.

## 3. Source of truth during implementation

During an authorized implementation package:

```text
GitHub exact branch + exact commit SHA
= source authority

local checkout
= test/integration replica of an exact audited SHA
```

Local modifications discovered during testing are diagnostic only until reproduced as explicit GitHub code changes, committed, re-audited, and pulled again.

The local environment must never become an undocumented fork.

## 4. Engineer instruction contract

Every implementation assignment given to the remote engineer must include:

```text
repository
base commit SHA
implementation branch
controlling implementation authority
normative ARE documents and exact versions
allowed paths
prohibited paths
required interfaces
required invariants
required adversarial tests
explicit non-authorities
expected commit / PR structure
stop conditions
```

The engineer must not infer authority from architecture prose alone.

## 5. Branch discipline

Current policy prohibits new branches without explicit approval.

Therefore, when implementation is eventually authorized, the authority must explicitly identify either:

```text
A. exact existing implementation branch to use
or
B. permission to create one named implementation branch from an exact approved base SHA
```

The engineer must not create side branches, force-push, merge, or rebase protected lineage unless the controlling authority explicitly permits it.

## 6. GitHub implementation phase

The engineer works only against repository-visible source.

Expected progression:

```text
normative contract
→ minimal implementation slice
→ commit
→ remote source audit
→ bounded corrections
→ exact candidate implementation SHA
```

Large rewrites are prohibited unless specifically authorized.

Each work package should preserve traceability from source code to ARE contract/invariant identifiers.

Example:

```text
ARE-1A registry implementation
implements:
INV-...
SC-...
AUTH-...
```

## 7. Remote audit before local testing

Before pulling code to the local machine, auditors should inspect the exact GitHub implementation SHA for at least:

```text
contract conformance
state-transition enforcement
authority non-forgeability
content-addressed identity
Evidence Ledger semantics
search-budget accounting
Critic/Governor separation
fail-closed behavior
unintended production/broker paths
scope creep
```

Remote source-audit result should be one of:

```text
SOURCE_AUDIT_PASS_FOR_LOCAL_TEST
CHANGES_REQUIRED
IMPLEMENTATION_INVALID
```

Only `SOURCE_AUDIT_PASS_FOR_LOCAL_TEST` opens the local pull/test gate.

This is **not** production approval.

## 8. Exact-SHA local pull rule

Local testing must identify the exact audited source identity:

```text
repository
branch
commit SHA
parent SHA
expected changed paths
```

Antigravity/local tooling must verify the checkout before running tests.

No testing result may be attributed to the audited implementation if the local source differs materially from that SHA.

## 9. Antigravity local role

Antigravity is the local implementation/test operator, not the source authority.

Its responsibilities may include:

```text
pull exact audited SHA
verify repository identity
create/use local virtual environment
run static/import checks
run unit tests
run regression tests
run concurrency/fault-injection tests
exercise storage transactions/recovery
exercise MT5/data interfaces where authorized
run frozen replay harnesses when separately authorized
capture stdout/logs/artifacts
report environment-specific defects
```

Antigravity may suggest code corrections, but corrections must return to GitHub engineering lineage before they become canonical.

## 10. Defect loop

If local testing finds a source defect:

```text
LOCAL FAILURE
→ diagnostic evidence
→ defect report to GitHub
→ engineer patches GitHub source
→ new commit SHA
→ remote re-audit
→ pull new exact SHA
→ rerun only as authorized
```

Do not hot-fix local source and continue as if the audited SHA were unchanged.

## 11. Scientific run firewall

Implementation testing is separate from substantive strategy research.

Unless a later authority explicitly opens it:

```text
P001 research = CLOSED
W2/W3         = CLOSED
production    = CLOSED
broker capital execution = CLOSED
```

Implementation tests should initially use synthetic fixtures, deterministic mock data, frozen non-verdict fixtures, and governance-focused adversarial cases.

Any real scientific replay/data consumption requires a separate research authority.

## 12. Evidence return to GitHub

Local test results must be published back to GitHub as evidence tied to exact implementation SHA and environment identity.

Minimum provenance:

```text
implementation SHA
local checkout identity
Python/environment identity
OS/runtime identity
input fixture hashes
command/test identity
run count
raw stdout/logs
result summary
known limitations
```

Raw evidence should precede narrative summaries.

## 13. Promotion of implementation status

The intended implementation lifecycle is:

```text
DESIGN_CLOSED
→ IMPLEMENTATION_AUTHORIZED
→ GITHUB_IMPLEMENTED
→ REMOTE_SOURCE_AUDITED
→ LOCAL_TEST_ELIGIBLE
→ LOCAL_TESTED
→ IMPLEMENTATION_ADJUDICATED
```

None of these states imply strategy promotion or production authority.

## 14. Current boundary

As of this document:

```text
ARE-0 external adversarial audit = NEXT
ARE-0 formal design              = NOT CLOSED
ARE implementation               = NOT AUTHORIZED
GitHub engineering               = NOT STARTED
local Antigravity implementation tests = NOT OPEN
```

This document only freezes the future workflow so later agents do not accidentally require the remote engineer to access the local machine or make local source the canonical engineering surface.
