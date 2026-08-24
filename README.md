# AHFMES-ARE

Isolated repository for the **AHFMES Autonomous Research Engine (ARE)** architecture and governance.

## Migration boundary

This repository is a byte-preserving extraction of the ARE-only documents from
`Mziana/AHFMES-CHATGPT` at source commit
`dcecafd1f9caae130da3880170f018026b1d5183`.

It deliberately excludes Condition Atlas, Position Path Replay, research data,
production/runtime code, tests, generated artifacts, and mixed project-status
documents. Historical references to those systems inside preserved ARE design
documents remain historical citations only; their source artifacts are not
present in this repository.

## Current safety status

This migration does **not** transfer any execution authority.

- ARE-0 design closure: **NO**
- External-audit readiness: **NO**
- Implementation: **NOT AUTHORIZED**
- Substantive research / P001: **NOT AUTHORIZED**
- Production, paper, or live trading: **CLOSED**

Start with
[`PROJECT_GOVERNANCE/CURRENT_AUTHORITY_INDEX.md`](PROJECT_GOVERNANCE/CURRENT_AUTHORITY_INDEX.md).
The former source-repository commit identities remain provenance evidence, not
the identity of a new ARE audit candidate.
