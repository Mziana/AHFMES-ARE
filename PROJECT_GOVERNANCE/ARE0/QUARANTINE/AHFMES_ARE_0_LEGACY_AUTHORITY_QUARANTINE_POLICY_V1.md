# AHFMES ARE-0 — Legacy Authority Quarantine Policy V1

Status: **NORMATIVE CLOSURE / AUTHORITY-HYGIENE COMPANION / NO MACHINE-RIGHT GRANT / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 1. Purpose

This policy removes ambiguity created by historical ARE design files whose own old headers/body may use words such as `normative`, `current`, `canonical`, `approved`, `authority`, `ready`, or equivalent.

It does **not** edit or erase those historical files. It defines their current authority classification.

## 2. Closed-set supersession theorem

Current ARE-0 machine and closure authority may originate only from exact paths listed in the current `AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V6.md`.

For every repository path `P` not listed in that manifest's current normative authority set:

```text
P NOT IN CURRENT_NORMATIVE_MANIFEST
=> P_CURRENT_MACHINE_AUTHORITY = NONE
=> P_CURRENT_CLOSURE_AUTHORITY = NONE
=> any internal self-claim of "normative/current/canonical/approved/implementation authority"
   is HISTORICAL_TEXT_ONLY and explicitly superseded
```

An unlisted file cannot self-promote by changing its own prose, status header, version number, filename, timestamp, or internal precedence claim.

The only legal way to grant a path current normative authority is a pre-Clean-Pass integrated normative change that adds the exact path to the current manifest and survives whole-tree impact attack.

## 3. Historical preservation

Historical files remain immutable evidence/rationale where already committed. Their old self-description is preserved as evidence of the state that existed at that historical time.

```text
HISTORICAL SELF-CLAIM != CURRENT AUTHORITY
PRESERVED HISTORY != AMBIENT PRIVILEGE
```

No historical file may widen or contradict the current Matrix/Inventory/Protocol/Manifest package.

## 4. Authority-quarantine audit requirement

Before Clean Pass #1, SA-11 must produce a non-normative immutable `LEGACY_AUTHORITY_QUARANTINE_RECORD` for the exact candidate tree.

The record must include at minimum:

```text
exact subject commit/tree
exact current Normative Authority Manifest blob
all unlisted PROJECT_GOVERNANCE paths inspected for current-looking authority self-claims
for each detected self-claim:
  exact path
  exact Git blob ID
  exact quoted/located claim class
  classification = HISTORICAL_TEXT_ONLY / QUARANTINED
confirmation that no unlisted path is relied on for machine/closure authority
```

A detected old self-claim is not a blocker **if and only if** it is positively classified by this policy and the implementation/closure package does not rely on it.

An unlisted file that is actually relied upon for current semantics is a blocker and must either be added to the manifest before Clean Pass #1 or the dependency removed.

## 5. Post-Pass discipline

After Clean Pass #1, an unlisted historical design/spec file cannot gain authority by self-edit because manifest membership controls authority. However, any change that creates or materially changes an authority-like self-claim in `PROJECT_GOVERNANCE` after the quarantine record was bound makes cross-document consistency stale and requires SA-11 quarantine recheck before freeze/external dispatch.

It does not silently alter `NORMATIVE_CANDIDATE_TREE_ROOT`; it blocks final consistency/dispatch until the non-normative quarantine evidence is refreshed and confirms the self-claim remains non-authoritative.

No such refresh may add rights.

## 6. Examples already observed

Historical files such as ARE-0A/0B/0C/0D drafts may contain text equivalent to:

```text
"This is the normative ARE-0X draft for external review."
```

Under this policy, when their exact path is absent from the current normative manifest:

```text
that sentence = historical self-description only
current authority = NONE
```

## 7. Static boundary

This policy grants no machine transition, writer, scientific privilege, capital privilege, ARE-0 closure, implementation, P001 substantive research, production, or PR-merge authority.