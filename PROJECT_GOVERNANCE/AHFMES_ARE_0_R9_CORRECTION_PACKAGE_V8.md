# AHFMES ARE-0 — R9 Correction Package V8

Status: **NORMATIVE INTERNAL-IMPACT CORRECTION COMPANION / R9-01 IDENTITY-HIERARCHY HARDENING / SA-11 CLAIM-EVIDENCE RETAINED / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 0. Composition

Immutable correction base:

```text
BASE_R9_CORRECTION_PACKAGE_V7_PATH = PROJECT_GOVERNANCE/AHFMES_ARE_0_R9_CORRECTION_PACKAGE_V7.md
BASE_R9_CORRECTION_PACKAGE_V7_GIT_BLOB_SHA = aec65399e7cb407717ef75217ef87746a4f451ca
```

V7 and its exact V6 base remain historical/current correction context except R9-01 is narrowed by this V8.

This companion cannot add machine rights absent from Matrix V8.

## 1. Internal independent-lane findings on V7 subject

Exact impact subject attacked:

```text
7b4e734bffdd1e911e1f4ea761ce73717dea21d6
```

Normalized findings:

```text
IA-A01 = BOOTSTRAP_INSTANCE_KEY_STILL_CONTROL_IDENTITY_DERIVED
root = R9-01

IA-F01 = GENERATION0_COMMITMENT_NOT_EXPLICITLY_FULL_CONTENT
root = R9-01
```

No new R9 family.

V7 had removed scientific/policy payload from instance identity but still included trust/control authorization inputs. A changed authorization binding for the same semantic system could therefore compute a different key unless identity is moved above authorization.

V7 also froze generation-#0 schema/template plus policy abstractions. To eliminate same-schema/different-authority-payload lottery, the commitment must bind full exact generation-#0 content.

## 2. Current R9-01 hierarchy

Matrix V8 establishes:

```text
ARE_SYSTEM_IDENTITY_ROOT + BOOTSTRAP_DOMAIN_IDENTITY_ROOT + GENESIS_ORDINAL_0
        ↓
BOOTSTRAP_INSTANCE_KEY
        ↓
immutable BOOTSTRAP_AUTHORIZATION_BINDING_ROOT
        ↓
immutable SYSTEM_GENESIS_PAYLOAD_COMMITMENT_ROOT
        ↓
monotone PREGENESIS_IMPORT_REVISION_ROOT[r]
        ↓
SYSTEM_GENESIS_COMMITTED terminal
```

The instance key excludes trust anchor, operators, credentials, payload, policy, process and config.

## 3. Authorization conflict theorem

After first journal creation:

```text
changed trust anchor / Genesis control / Bootstrap-Audit control / separation / capability scope
=> same instance key
=> conflicting authorization
=> DENIED
```

No current recovery edge exists. Loss of the bound controls leaves bootstrap fail-closed rather than allowing a new journal.

## 4. Full exact generation-#0 content commitment

`SYSTEM_GENESIS_PAYLOAD_COMMITMENT_ROOT` binds every authority-bearing generation-#0 payload, including initial roles/bindings/registries/governance/Safety/comparator/accounting/error-order contents and embedded specs.

Same schema with changed content is a commitment conflict on the same instance.

## 5. Knowledge closure

At SystemGenesis, inherited LegacyCutoff closure must be complete through governed genesis cutoff or conservatively UNKNOWN. Known material history cannot be omitted under a COMPLETE claim. Unbound import evidence cannot satisfy genesis.

## 6. SA-11 evidence correction retained

The local quarantine finding remains mandatory. Before Clean Pass #1:

```text
EXHAUSTIVE_UNLISTED_FRONTIER_PROVEN
AUTHORITY_LIKE_CLAIM_INVENTORY_COMPLETE
```

and every detected claim must have exact path/blob/location-or-bounded-quote/claim-class/classification evidence.

## 7. Permanent regressions

Protocol V9 adds R9-X89..X93 on top of inherited X01..X88.

## 8. Qualification consequence

This V8 changes normative bytes; all prior roots/passes remain historical only. Full impact, two clean passes, permanent regression and final consistency are mandatory before new external dispatch.

## 9. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
PR #20 MERGE = NOT AUTHORIZED
```
