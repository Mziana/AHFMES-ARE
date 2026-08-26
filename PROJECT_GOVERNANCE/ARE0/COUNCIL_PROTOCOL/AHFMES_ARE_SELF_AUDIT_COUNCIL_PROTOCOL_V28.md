# AHFMES ARE — Self-Audit Council Protocol V28

Status: **NORMATIVE / V27 INHERITED + MANIFEST OBJECT-IDENTITY REGRESSION / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-22**

## 1. Inheritance

This protocol inherits Protocol V27 in full except where this successor adds the mandatory manifest-object-identity gate and regression below. Matrix V22, Inventory V22, Policy V5, and all surviving R9 correction semantics remain unchanged unless a later current manifest explicitly supersedes them.

## 2. Pre-clean predecessor finding

```text
SUBJECT = e865c1a1a8ccfbc4e277c8618e8e1f7139989582
FINDING = IA27-H01
CLASS = MANIFEST_MEMBER_BLOB_SHA_MISMATCH
ROOT = R9-01
NEW_R9_ROOT = NO
DISPOSITION = CHANGES_REQUIRED
```

The defect is mechanical but closure-critical: a manifest member carried an abbreviated/non-matching Git object identity. A clean architecture interpretation cannot compensate for a non-closed authority set.

## 3. Mandatory pre-root manifest gate

Before any normative-root computation receives credit, the auditor MUST verify the current stable binding and current manifest on one exact immutable subject and establish:

```text
member_count == declared_member_count
all member paths unique
all non-self declared SHAs match ^[0-9a-f]{40}$
all non-self paths exist at the exact subject
all non-self exact Git blob SHAs equal declared SHAs
all byte lengths equal manifest tuple lengths
self tuple uses literal SELF only
no alternate resolver/fallback/moving-ref substitution
```

Any failure is `CHANGES_REQUIRED` and blocks SA-11, CP1, CP2, regression credit, candidate construction, external-audit readiness, and closure.

Prefix expansion, abbreviated-SHA lookup, UI truncation repair, or best-effort inference is prohibited.

## 4. Permanent regression addition

Add:

```text
R9-X257 — MANIFEST_NONSELF_FULL_GIT_OBJECT_IDENTITY

SETUP:
- current manifest declares a non-self member path P;
- actual subject blob identity is full canonical SHA H;
- manifest declaration is H with one or more hex characters removed, appended, changed, case-mutated, UI-elided, prefix-only, or resolved from another ref.

EXPECT:
- verifier rejects before root hashing;
- verifier does not expand or repair the identity;
- no root/SA-11/CP1/CP2/regression/candidate/closure credit is granted;
- corrected successor requires a new manifest generation and qualification reset.

CONTROL:
- exact canonical 40-hex H at the same immutable subject passes this identity predicate, subject to all other closure gates.
```

The formal permanent regression requirement is therefore:

```text
R7 = 26
R8 = 40
R9 = 257
TOTAL = 323
```

Historical regression results remain historical evidence only after this normative successor wave.

## 5. Independent lane discipline

The inherited A–H whole-architecture lanes remain mandatory. A mechanical manifest PASS does not inherit semantic PASS, and a semantic PASS does not excuse mechanical closure failure. One reproducible bypass, ambiguity, deadlock, remint, stale privilege, manifest defect, quarantine escape, or cross-root composition defect blocks CP1.

## 6. Human–ARE and firewall

Human–ARE chat remains explanatory/research/simulation/governed-intent only, with zero ambient evidence, scientific, Safety, broker, capital, projection, implementation, or execution authority.

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR MERGE = NOT AUTHORIZED
```
