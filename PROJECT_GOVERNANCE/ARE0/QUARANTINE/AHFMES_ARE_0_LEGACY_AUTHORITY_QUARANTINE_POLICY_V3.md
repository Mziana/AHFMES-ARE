# AHFMES ARE-0 — Legacy Authority Quarantine Policy V3

Status: **NORMATIVE CLOSURE / SELF-REFERENCE-FREE SA-11 INPUT PROJECTION / NO MACHINE-RIGHT GRANT / STATELESS / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable base:

```text
BASE_QUARANTINE_POLICY_V2_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_LEGACY_AUTHORITY_QUARANTINE_POLICY_V2.md
BASE_QUARANTINE_POLICY_V2_GIT_BLOB_SHA = 37fe8d582b3ebb699705e485829624d9765ad3b4
```

All V2->V1 rules remain except V2 §§2,3,5 exact-subject/evidence-frontier construction is replaced/narrowed here. Manifest routing remains through the stable binding.

## 1. IA-E02 correction theorem

An audit output cannot be required to content-address itself. SA-11 therefore separates:

```text
QUALIFICATION_INPUT_FRONTIER (QIF) = governance inputs to be inspected
QUALIFICATION_AUDIT_OUTPUT_SET (QAO) = exact finite evidence-output paths
QUALIFICATION_EVIDENCE_SET = exact path/blob instances produced at QAO paths
```

QAO paths have no machine/closure/audit-rule authority and may never satisfy a current semantic dependency. Their exclusion is solely to avoid evidence self-reference.

## 2. Exact finite QAO path set

Only these exact paths are excluded from QIF:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_SA11_AUTHORITY_CLAIM_TRIGGER_LEDGER_V1.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_LEGACY_AUTHORITY_QUARANTINE_RECORD_V2.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_INTERNAL_IMPACT_AUDIT_RECORD_V1.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_CLEAN_PASS_1_RECORD_V1.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_CLEAN_PASS_2_RECORD_V1.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_REGRESSION_R7_R8_R9_V1.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_FINAL_CONSISTENCY_RECORD_V1.md
PROJECT_GOVERNANCE/AHFMES_ARE_0_QUALIFICATION_ROOT_RECORD_V1.md
```

No prefix, suffix, glob, directory, version-family or “audit-like” inference is allowed. A similarly named path not exactly listed remains ordinary governance input and is scanned.

Changing this path set is a normative change and, after Clean Pass #1, resets clean-pass credit to zero.

## 3. QIF construction

For an exact repository tree `T`:

```text
G(T) = every recursive blob under PROJECT_GOVERNANCE/
QAO(T) = members of the exact §2 path set that exist in T
QIF(T) = G(T) - QAO(T)
N(T) = exact current normative manifest membership
UQIF(T) = QIF(T) - N(T)
```

Every path in `UQIF(T)` is in the authority-hygiene inspection frontier, including nested subtrees. Every inspectable text blob is scanned completely with the V2 trigger vocabulary. Opaque/incomplete inputs conservatively produce UNKNOWN.

## 4. Deterministic QIF root

Define `PAIR_SERIALIZATION_V1(path, blob)` as:

```text
u32be(len(UTF8(path))) || UTF8(path) ||
u32be(len(ASCII(lowercase_git_blob_sha))) || ASCII(lowercase_git_blob_sha)
```

Sort pairs by raw UTF-8 path bytes ascending. Then:

```text
SA11_INPUT_FRONTIER_ROOT =
SHA256(
  UTF8("AHFMES-SA11-QIF-V1\0") ||
  concat(PAIR_SERIALIZATION_V1(path, blob) for every sorted pair in QIF(T))
)
```

The root binds exact path/blob identity without embedding a commit SHA and is therefore self-reference-free with respect to QAO outputs.

## 5. Trigger ledger and quarantine inventory

For every trigger hit in `UQIF(T)`, the trigger ledger carries:

```text
SA11_INPUT_FRONTIER_ROOT
exact path
exact Git blob ID
exact line/range where available
bounded quote or exact locator
trigger term/class
context disposition = AUTHORITY_LIKE_SELF_CLAIM / NON_CLAIM_CONTEXT / UNKNOWN
```

Every `AUTHORITY_LIKE_SELF_CLAIM` or `UNKNOWN` hit maps to the quarantine record with exact path/blob/locator, bounded quote/locator, claim class and `HISTORICAL_TEXT_ONLY / QUARANTINED` classification.

The ledger/record do not list their own blobs. Their integrity is handled by the evidence-set root in §6.

## 6. Evidence-set root

For a final candidate tree `C`, define:

```text
E(C) = every existing exact QAO §2 path/blob pair in C
QUALIFICATION_EVIDENCE_SET_ROOT =
SHA256(
  UTF8("AHFMES-SA11-EVIDENCE-V1\0") ||
  concat(PAIR_SERIALIZATION_V1(path, blob) for every sorted pair in E(C))
)
```

A qualification-root record may bind `SA11_INPUT_FRONTIER_ROOT`, current normative root and the exact evidence-output roles/hashes it observed, but it never has to embed its own Git blob. The final candidate/binder construction content-addresses the candidate externally.

## 7. Freshness and final-candidate equality

SA-11 evidence generated against input tree `T0` remains applicable to a later candidate `C` only if:

```text
SA11_INPUT_FRONTIER_ROOT(C) == SA11_INPUT_FRONTIER_ROOT(T0)
current normative manifest/root unchanged
current binding unchanged
all detector rules unchanged
all required QAO outputs are present and mutually consistent
```

Thus adding/changing only exact QAO output blobs does not alter the inspected QIF. Any change to any non-QAO governance path/blob changes QIF and requires a complete SA-11 rescan before dispatch.

Changing a QAO output after its dependent final-consistency/evidence-root check invalidates that check and blocks dispatch until the evidence-set root and dependent evidence are refreshed. This does not grant clean-pass credit by itself.

## 8. Anti-laundering rules

```text
QAO path used as machine/closure/audit-rule semantic dependency -> qualification FAIL
unlisted non-QAO path renamed to resemble QAO -> still scanned
new audit output path not exactly in §2 -> still scanned
QAO set expanded after observing results -> normative change; impact rerun; clean count 0
QIF root mismatch at final candidate -> SA-11 FAIL
missing required trigger hit -> SA-11 FAIL
```

## 9. Static firewall

This policy grants no machine transition, writer, scientific privilege, capital privilege, ARE-0 closure, implementation, P001 substantive research, production, live/paper trading or PR-merge authority.
