# AGENTS.md — Universal AI Agent Instructions

## Navigation

Start at `are/__init__.py`. Trace entry points via `IsolatedBacktestEngine` in `are/backtest.py`.

## Module Map

| Module | Files | Purpose |
|--------|-------|---------|
| Core | `backtest.py`, `engine.py`, `runner.py` | Vectorized backtest engine |
| Data | `data_pipeline.py`, `data_loader.py` | Data ingestion, purification, LOCF |
| Research | `orchestrator.py`, `validation.py`, `evidence.py` | WFO, DSR, evidence chain |
| Execution | `mt5_gateway.py`, `execution_state.py` | MT5 bridge, order management |
| Risk | `safety.py`, `breaker.py` | Drawdown breaker, circuit breaker |
| Strategy | `strategy_engine.py`, `alpha_generator.py` | Strategy dispatch, alpha seeds |
| CLI | `cli.py` | Command-line interface |
| Web | `web_ui.py` | Dashboard server |

## Testing

```bash
python -m pytest tests/ -q --tb=line
```

All 535 tests must pass. Tests are in `tests/are/`.

## Research Pipeline

```
Proposal → Screening → WFO → DSR → Holdout → Gate
```

Each stage is orchestrated by `are/research/orchestrator.py`. Never bypass the orchestrator for qualification.

## Critical Rules

1. **DO NOT** bypass orchestrator for proposal qualification
2. **DO NOT** allow strategy code to mutate input DataFrames
3. **DO NOT** use synthetic data in WFO — real historical data required
4. **Signal format:** DataFrame with `'signal'` column, values in `{-1, 0, 1}`
5. **Execution model:** `signal_timing = next_bar_close` (close-to-close)

## Documentation State

⚠️ 1,248 markdown files in `PROJECT_GOVERNANCE/` with no central index.
This file and `CLAUDE.md` are the primary entry points for AI agents.
