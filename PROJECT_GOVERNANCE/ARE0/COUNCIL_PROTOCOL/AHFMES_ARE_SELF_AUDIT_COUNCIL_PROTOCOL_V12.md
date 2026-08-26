# AHFMES ARE — Self-Audit Council Protocol V12

Status: **CURRENT CLOSURE/AUDIT PROTOCOL / WHOLE-BLOB SA-11 / TWO-CLEAN-PASS FREEZE / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable base:

```text
BASE_PROTOCOL_V11_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_SELF_AUDIT_COUNCIL_PROTOCOL_V11.md
BASE_PROTOCOL_V11_GIT_BLOB_SHA = d49b4839962e9847975e08331d82747ba059ccbc
```

All V11→V2 rules remain except SA-11 trigger-ledger qualification is replaced by Policy V4 whole-blob quarantine and final lineage proof. Machine semantics remain solely in Matrix V8.

## 1. Current manifest resolution

The Council resolves current normative authority only through:

```text
PROJECT_GOVERNANCE/AHFMES_ARE_0_CURRENT_NORMATIVE_MANIFEST_BINDING.md
```

The binding must resolve Manifest V11 inside the same exact pre-pass subject. No historical manifest, PR metadata, authority index, handoff or audit record may substitute.

## 2. Pre-pass exact subject S0

Before Clean Pass #1, the integrated correction generation is frozen as exact commit `S0`.

The Council must positively record:

```text
S0 exact commit SHA
S0 root tree SHA
S0 PROJECT_GOVERNANCE subtree SHA
current Manifest V11 path/blob
current stable-binding blob
all 38 normative members exist
all 37 non-self required blobs match Manifest V11
Matrix V8 exact blob unchanged
Inventory V8 exact blob unchanged
no new reproducible impact blocker
SA-11 whole-blob quarantine PASS under Policy V4
clean-pass count = 0
```

No clean-pass credit can be earned before this pre-pass qualification is complete.

## 3. SA-11 whole-blob semantics

For `S0`, every recursive governance blob not listed by current Manifest V11 is universally `WHOLE_BLOB_HISTORICAL_QUARANTINE` with zero current machine/closure/audit-rule authority.

The Council does not rely on phrase detection, filename inference, or per-claim review to establish quarantine. A current semantic dependency on an unlisted path is itself a blocker.

The exact eight post-S0 qualification-output paths are those in Policy V4 §3 and have zero authority.

## 4. Integrated impact attack

Before Clean Pass #1, run Lane A-F against the whole current composition, including at minimum:

```text
A — state/object totality, genesis, writers, terminality, unknown handling
B — authority non-forgeability, SoD/common control, bootstrap/root-of-trust
C — evidence/search/multiplicity, post-access settlement, revalidation
D — Champion/promotion/rollback/meta-policy/current-reliance coupling
E — closure routing, whole-blob quarantine, stale pointers, self-reference, candidate lineage
F — capital/material-risk mutation boundary, reconciliation, operational completeness, broker/Safety coupling
```

A concern is a blocker only when a reproducible legal path or closure inconsistency is demonstrated. Any new reproducible blocker resets clean-pass count to zero and requires integrated correction before retry.

## 5. Clean Pass #1

Clean Pass #1 is a whole-composition adversarial review of the exact frozen normative bytes from `S0`.

PASS means:

```text
no new reproducible blocker
same exact normative root as pre-pass qualification
Matrix bytes unchanged
Manifest/binding/policy/protocol bytes unchanged
all Lane A-F obligations rechecked
```

The result is written only to the exact non-normative QAO Clean-Pass-1 path. No normative byte may be edited to record PASS.

## 6. Clean Pass #2

Clean Pass #2 is a fresh whole-composition adversarial review after Pass #1, against exactly the same normative root.

PASS requires independently rechecking the full attack surface rather than merely confirming Pass #1 notes.

```text
PASS_1_NORMATIVE_ROOT == PASS_2_NORMATIVE_ROOT
```

Any normative-member byte/path/blob change after Pass #1 resets the sequence to zero. There is no editorial/status/semantic-equivalence exception.

## 7. Regression

After two clean passes, execute the permanent regression catalog:

```text
R7 permanent scenarios
R8 permanent scenarios
R9-X01 through current highest frozen R9 scenario
```

At minimum R9-X01..R9-X107 remain mandatory from the inherited protocol/correction chain. The regression record must bind the same normative root as both clean passes.

A regression failure is a blocker and invalidates clean-pass qualification until corrected and rerun from count zero.

## 8. Final consistency and post-S0 lineage

After regression, final consistency proves:

```text
S0 is ancestor of final internal candidate C
all changed paths S0..C are a subset of Policy V4 exact eight QAO paths
no non-QAO path changed
no normative member changed
current Manifest V11 and stable binding remain byte-identical to S0
same normative root across pre-pass, CP1, CP2, regression and final consistency
all required QAO outputs present and mutually consistent
QAO outputs have zero machine/closure/audit-rule authority
PR metadata is not authority
```

If any non-QAO path changes after S0, qualification lineage fails. If any normative member changes, clean-pass count also resets to zero.

## 9. Candidate and binder construction

Only after §8 PASS may one exact immutable external-audit candidate commit `C` be designated.

The handoff/binder must be an exact one-commit child `B` of `C` and that child may change exactly one binder path only. The binder is non-normative and cannot modify candidate semantics.

External auditors must audit `C`, not `B` and not the moving branch head.

## 10. Static firewall

Internal qualification or external-audit readiness grants none of:

```text
ARE-0 CLOSED
implementation authority
P001 substantive research authority
production authority
live/paper trading authority
PR merge authority
```

Those remain separately denied unless explicitly granted by later authority outside this qualification protocol.
