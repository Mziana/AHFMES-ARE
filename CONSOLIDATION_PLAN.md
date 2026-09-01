# AHFMES Repository Consolidation Plan

## Current State: 3 Parallel Repos

| Repo | Root .py | Total .py | MD Files | Tests | Status |
|------|----------|-----------|----------|-------|--------|
| **AHFMES** | 49 flat | 1981 | 1250 | unknown | Legacy runtime |
| **AHFMES-CHATGPT-DEEP** | 49 flat (identical) | 212 | 240 | unknown | ChatGPT fork |
| **AHFMES-ARE** | 78 in `are/` pkg | 183 | 1250 | 535 pass | **ACTIVE** |

## Root Cause

AHFMES and AHFMES-CHATGPT-DEEP share **identical** root-level Python files:
`orchestrator.py`, `circuit_breaker.py`, `habitat_*.py`, `paper_executor.py`, `telemetry.py`, etc.

These are **forks from the same codebase** created by different AI agents (Claude, ChatGPT, Codex)
working independently. AHFMES-ARE is the **consolidated rewrite** with proper packaging.

## Overlap Matrix

```
AHFMES ↔ AHFMES-CHATGPT-DEEP:  ~95% identical root .py files
AHFMES ↔ AHFMES-ARE:           ~40% concept overlap (habitat, execution, telemetry)
AHFMES-ARE is the SUPERSET:     78 files, proper package, 535 tests
```

## Recommendation: AHFMES-ARE is the Canonical Repo

### Why AHFMES-ARE Wins

1. **Proper Python packaging** (`are/` package with `__init__.py`)
2. **535 passing tests** — no other repo has verified test coverage
3. **Active development** — last commit `148a5fa` (today)
4. **Clean module boundaries** — core/data/research/execution separation
5. **AI entry points** — CLAUDE.md + AGENTS.md

### What to Archive

| Repo | Action | Reason |
|------|--------|--------|
| AHFMES | `git tag archive/pre-are-v1 && archive repo` | Superseded by ARE |
| AHFMES-CHATGPT-DEEP | `git tag archive/chatgpt-fork && archive repo` | Fork of AHFMES, not ARE |

### Migration Steps

1. **Do NOT delete** old repos — tag and archive them on GitHub
2. **Extract any unique logic** from AHFMES/AHFMES-CHATGPT-DEEP not in ARE:
   - Check `dashboard/`, `tools/condition_atlas/`, `research/remediation/`
   - Compare habitat modules (may have diverged)
3. **Consolidate agent-memory** — merge `.agent-memory/delegation/` logs into ARE
4. **Single source of truth** — all future work in AHFMES-ARE only
5. **Add GitHub topic** `archived` to old repos

### Expected Outcome

```
BEFORE: 3 repos × 1250+ MD files × 2400+ .py files = chaos
AFTER:  1 repo  × structured docs  × 78 core files  = clarity
```
