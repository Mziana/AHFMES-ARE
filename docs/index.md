# AHFMES-ARE Documentation Index

> **Single source of truth** for all 1,250 markdown files in this repository.
> Start here. Everything else is a detail.

---

## Quick Start

- **New AI agent?** Read [`../CLAUDE.md`](../CLAUDE.md) (Claude Code) or [`../AGENTS.md`](../AGENTS.md) (universal)
- **New developer?** Read [`../README.md`](../README.md) then come back here
- **Want to run tests?** `python -m pytest tests/ -q` (535 tests, ~95s)

---

## Repository Structure

```
AHFMES-ARE/
├── are/                          # Core Python package (78 files, 22K LOC)
│   ├── backtest.py               # IsolatedBacktestEngine
│   ├── engine.py                 # Runtime engine
│   ├── safety.py                 # Drawdown breaker
│   ├── mt5_gateway.py            # MT5 execution bridge
│   ├── validation.py             # Integrity checks
│   ├── data_pipeline.py          # Data ingestion
│   └── research/                 # WFO/DSR pipeline
├── tests/                        # 76 test files, 535 tests
├── UI/                           # Next.js dashboard (Supabase)
├── TOOLS/                        # Standalone utilities
├── data/                         # Backtest results, market data
├── docs/                         # You are here
└── PROJECT_GOVERNANCE/           # 393 governance docs
```

---

## Navigation by Topic

### 🏗 Architecture
| File | Purpose |
|------|---------|
| [`GRAND DESIGN/AHFMES_ARE_GRAND_DESIGN_V1.md`](../GRAND%20DESIGN/AHFMES_ARE_GRAND_DESIGN_V1.md) | Master architecture document |
| [`ENGINEERING/RULES.md`](../ENGINEERING/RULES.md) | Engineering rules and constraints |
| [`ENGINEERING/ARCH_DEBT_REGISTER.md`](../ENGINEERING/ARCH_DEBT_REGISTER.md) | Architecture debt tracker |

### 🔬 Research & Backtest
| File | Purpose |
|------|---------|
| [`are/backtest.py`](../are/backtest.py) | Core backtest engine |
| [`are/research/orchestrator.py`](../are/research/orchestrator.py) | WFO/DSR pipeline |
| [`are/validation.py`](../are/validation.py) | Integrity checks |
| [`are/qualify_proposal.py`](../are/qualify_proposal.py) | Proposal screening |

### 🚀 Execution & MT5
| File | Purpose |
|------|---------|
| [`are/mt5_gateway.py`](../are/mt5_gateway.py) | MT5 bridge |
| [`are/execution_state.py`](../are/execution_state.py) | Order state machine |
| [`PROJECT_GOVERNANCE/MT5_BRIDGE/`](../PROJECT_GOVERNANCE/MT5_BRIDGE/) | MT5 governance (10 docs) |

### 🛡 Safety & Risk
| File | Purpose |
|------|---------|
| [`are/safety.py`](../are/safety.py) | Drawdown breaker, circuit breaker |
| [`are/breaker.py`](../are/breaker.py) | Emergency stop logic |
| [`are/input_guard.py`](../are/input_guard.py) | Input validation |

### 📋 Governance (393 docs)
| Directory | Files | Purpose |
|-----------|-------|---------|
| `PROJECT_GOVERNANCE/ARE0/` | 261 | Core authority, contracts, council protocols |
| `PROJECT_GOVERNANCE/ARE1/` | 14 | ARE1 phase governance |
| `PROJECT_GOVERNANCE/ARE2/` | 15 | ARE2 phase governance |
| `PROJECT_GOVERNANCE/ARE3/` | 19 | ARE3 phase governance |
| `PROJECT_GOVERNANCE/ARE4/` | 19 | ARE4 phase governance |
| `PROJECT_GOVERNANCE/RED_TEAM_HARDENING/` | 14 | Red team hardening |
| `PROJECT_GOVERNANCE/COGNITIVE_ROADMAP/` | 16 | Cognitive roadmap |
| `PROJECT_GOVERNANCE/P001/` | 13 | P001 program governance |
| `PROJECT_GOVERNANCE/WEB_UI/` | 10 | Web UI governance |

### 📊 Data & Inventory
| File | Purpose |
|------|---------|
| [`DATA_INVENTORY.md`](../DATA_INVENTORY.md) | Data catalog |
| [`are/data_pipeline.py`](../are/data_pipeline.py) | Data ingestion pipeline |
| [`are/data_loader.py`](../are/data_loader.py) | Data loading utilities |

### 🔧 Engineering
| File | Purpose |
|------|---------|
| [`ENGINEERING/IAQ_LEDGER.md`](../ENGINEERING/IAQ_LEDGER.md) | Implementation authority ledger |
| [`ENGINEERING/SLICE_1_CONTRACT.md`](../ENGINEERING/SLICE_1_CONTRACT.md) | Slice 1 contracts |
| [`ENGINEERING/IMPLEMENTATION_AUTHORITY_CHARTER.md`](../ENGINEERING/IMPLEMENTATION_AUTHORITY_CHARTER.md) | Authority charter |

### 📝 Journal & Progress
| File | Purpose |
|------|---------|
| [`JOURNAL.md`](../JOURNAL.md) | Development journal |
| [`PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md`](../PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md) | Global progress diary |
| [`MIGRATION_SCOPE.md`](../MIGRATION_SCOPE.md) | Migration scope |
| [`RECOMMENDATIONS.md`](../RECOMMENDATIONS.md) | Recommendations |

---

## Agent Entry Points

| Agent | File |
|-------|------|
| Claude Code | [`CLAUDE.md`](../CLAUDE.md) |
| Universal | [`AGENTS.md`](../AGENTS.md) |
| Consolidation | [`CONSOLIDATION_PLAN.md`](../CONSOLIDATION_PLAN.md) |
