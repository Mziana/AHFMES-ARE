# AHFMES ARE-0 — R9 Correction Package V11

Status: **CURRENT CLOSURE CORRECTION COMPANION / IA-E03 / NO MACHINE-RIGHT GRANT / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 1. Purpose

This package closes the final pre-clean authority-hygiene weakness discovered after V10:

```text
IA-E03 = CLAIM-DETECTOR UNSOUNDNESS AS QUALIFICATION PRIMITIVE
family  = R9-03 closure-protocol / authority-hygiene
new architectural root = NONE
```

A finite phrase detector can miss equivalent authority language even when applied exhaustively. Therefore SA-11 no longer conditions safety on successful phrase detection.

## 2. Correction

Policy V4 applies blanket whole-blob quarantine to every exact governance blob outside current Manifest V11 membership at the exact pre-pass subject `S0`.

Consequences:

```text
unlisted claim detected     -> quarantined
unlisted claim missed       -> quarantined
unlisted claim ambiguous    -> quarantined
unlisted blob opaque        -> quarantined
unlisted higher version     -> quarantined
legacy implementation grant -> quarantined for current ARE-0 authority
```

No unlisted blob may supply current machine/closure/audit-rule semantics.

If a current normative member relies on an unlisted path as semantic authority, qualification fails rather than importing that dependency.

## 3. Self-reference-free evidence

The exact pre-pass commit `S0` is the immutable inspection subject. After `S0`, only Policy V4's exact eight QAO paths may change before final candidate designation.

Final consistency proves by Git ancestry/diff that every post-S0 write is QAO-only. This removes any need for an audit output to hash or inspect itself.

## 4. Mandatory added regression scenarios

```text
R9-X108 unlisted file uses novel synonym not in old trigger vocabulary -> whole blob remains quarantined
R9-X109 unlisted binary/opaque governance blob carries authority-like payload -> whole blob remains zero-authority
R9-X110 unlisted historical manifest has higher filename generation than current -> cannot override stable binding/Manifest V11
R9-X111 QAO-named lookalike path added after S0 -> non-QAO change; qualification lineage FAIL
R9-X112 exact QAO output attempts to define machine writer/edge -> attempted right invalid; qualification FAIL if relied upon
R9-X113 current normative file cites unlisted file as required semantic authority -> SA-11 FAIL despite blanket quarantine
R9-X114 post-S0 non-governance source edit occurs -> final candidate integrity FAIL under Protocol V12 default deny
R9-X115 final candidate descendant contains only exact QAO writes -> qualification lineage may remain valid if all roots/records agree
```

The permanent current regression range therefore becomes:

```text
R9-X01..R9-X115
```

## 5. Machine-semantics boundary

This correction changes no ARE machine transition, state object, writer, genesis edge, scientific privilege, capital privilege, broker mutation authority or Safety action.

Matrix V8 remains the sole current machine-semantic source. Inventory V8 remains the current closed-world companion.

## 6. Clean-pass consequence

This is a pre-clean normative correction. Existing clean-pass credit remains zero. After Manifest V11 generation freezes, the required order is:

```text
integrated Lane A-F impact attack
-> SA-11 whole-blob qualification
-> Clean Pass #1
-> no normative writes
-> Clean Pass #2
-> no normative writes
-> R7/R8/R9-X01..X115 regression
-> final consistency / QAO-only lineage proof
-> exact candidate freeze
-> binder-only child
```

## 7. Static firewall

No ARE-0 closure, implementation, P001, production, live/paper trading or PR-merge authority is granted.
