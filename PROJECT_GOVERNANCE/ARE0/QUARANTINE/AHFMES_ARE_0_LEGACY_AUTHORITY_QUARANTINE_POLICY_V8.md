# AHFMES ARE-0 — Legacy Authority Quarantine Policy V8

Status: **NORMATIVE CLOSURE / WHOLE-BLOB QUARANTINE / EXACT POST-S0 OUTPUT SET / STRUCTURAL_GENERATION_S1 / NO IMPLEMENTATION AUTHORITY**

## Composition

```text
BASE_POLICY = PROJECT_GOVERNANCE/ARE0/QUARANTINE/AHFMES_ARE_0_LEGACY_AUTHORITY_QUARANTINE_POLICY_V7.md
```

All V7 whole-blob quarantine and fail-closed rules carry forward. For this
V36 wave under STRUCTURAL_GENERATION_S1, V8 replaces the literal post-S0
output set AND adds the Scope-and-discipline section below; both changes are
integral parts of V8, not exceptions to it.

## Exact post-S0 output set

Only these exact paths may change after S0 before candidate construction:

```text
PROJECT_GOVERNANCE/ARE0/QUALIFICATION/AHFMES_ARE_0_SA11_WHOLE_BLOB_QUARANTINE_LEDGER_V1.md
PROJECT_GOVERNANCE/ARE0/QUARANTINE/AHFMES_ARE_0_LEGACY_AUTHORITY_QUARANTINE_RECORD_V3.md
PROJECT_GOVERNANCE/ARE0/QUALIFICATION/AHFMES_ARE_0_INTERNAL_IMPACT_AUDIT_RECORD_V2.md
PROJECT_GOVERNANCE/ARE0/QUALIFICATION/AHFMES_ARE_0_CLEAN_PASS_1_RECORD_V2.md
PROJECT_GOVERNANCE/ARE0/QUALIFICATION/AHFMES_ARE_0_CLEAN_PASS_2_RECORD_V2.md
PROJECT_GOVERNANCE/ARE0/QUALIFICATION/AHFMES_ARE_0_REGRESSION_R7_R8_R9_V2.md
PROJECT_GOVERNANCE/ARE0/QUALIFICATION/AHFMES_ARE_0_FINAL_CONSISTENCY_RECORD_V2.md
PROJECT_GOVERNANCE/ARE0/QUALIFICATION/AHFMES_ARE_0_QUALIFICATION_ROOT_RECORD_V2.md
PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md
PROJECT_GOVERNANCE/ARE0/DIARY/2026-08-26-ARE0-V36-WAVE-LEDGER.md
```

```text
QAO8 = first eight literal PROJECT_GOVERNANCE paths above
JQO_GLOBAL = ninth literal path above (global progress diary)
JQO_LOCAL = tenth literal path above (ARE0 V36 wave ledger)
POST_S0_OUTPUT_SET = QAO8 union {JQO_GLOBAL, JQO_LOCAL}
```

There is no wildcard, directory, suffix, date-family, branch, worktree, or
similarly named path exemption. A post-S0 change outside this exact set fails
the qualification lineage. QAO8, JQO_GLOBAL and JQO_LOCAL are not normative manifest members
and have zero current machine/closure/audit-rule authority.

## Scope and discipline of the output set

```text
SCOPE                = repository-wide: any changed path outside the exact set
                       after S0 fails the lineage, no exceptions.
QAO UPDATES          = in-place only, at these exact paths/versions; a rerun
                       never mints a new versioned filename during the wave.
AUTHORITY INDEX      = PROJECT_GOVERNANCE/CURRENT_AUTHORITY_INDEX.md is
                       finalized AT S0 and is NOT writable post-S0.
DATED DIARIES        = new dated sibling diary files are PROHIBITED during the wave (other than JQO_LOCAL itself);
                       both JQO surfaces absorb all chronology.
JQO CONTINUITY       = material-change checkpoints are MANDATORY in JQO_LOCAL;
                       JQO_GLOBAL mirrors progress references only; hiding a
                       checkpoint from JQO_LOCAL fails lineage proof.
JQO VOCABULARY       = PASS/CLOSED/READY/current-generation claims in any JQO
                       entry have zero resolution power (binding ignores them)
                       and obligate a corrective entry (see R9-X303).
```

## Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
LIVE/PAPER TRADING = NOT AUTHORIZED
```
