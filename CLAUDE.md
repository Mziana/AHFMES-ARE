# CLAUDE.md — Claude Code Entry Point

## Project

AHFMES-ARE: Autonomous Research Engine for algorithmic trading.
Vectorized backtesting (Polars), WFO/DSR research pipeline, MT5 execution gateway.

## Structure

```
are/           78 Python files, 22K LOC — core engine + strategy + research
tests/         76 test files, 535 tests — all must pass
UI/            Next.js dashboard (separate process)
data/          backtest results (JSON), market data (Parquet), strategy configs
TOOLS/         standalone utilities (blob_verifier, manifest_hash, path_router)
```

## Quick Commands

```bash
python -m pytest tests/ -q          # run all 535 tests
python -m pytest tests/ -q --tb=short  # failures with tracebacks
python -m are.cli                   # CLI entry point
```

## Critical Files

- `are/backtest.py` — IsolatedBacktestEngine, vectorized backtest core
- `are/research/orchestrator.py` — WFO/DSR pipeline (PRECHECK→DATA→STRATEGY→BASELINE→WFO→OOS→STATISTICS→CRISIS→GATE→ARTIFACT)
- `are/validation.py` — integrity checks, equity invariant, provenance hash
- `are/qualify_proposal.py` — proposal screening gate
- `are/safety.py` — drawdown circuit breaker, risk management
- `are/mt5_gateway.py` — MT5 execution bridge

## Execution Contract

- `signal_timing = next_bar_close` — close-to-close model
- Strategies MUST return DataFrame with `'signal'` column in `{-1, 0, 1}`
- WFO requires real historical data — no synthetic fallback

## Rules

- **Branching:** main only. No feature branches.
- **Before commit:** `python -m pytest tests/ -q` must pass (535/535)
- **Strategy mutation:** Strategies MUST NOT mutate input DataFrames
- **Qualification:** Never bypass orchestrator for proposal screening

## Recent Fixes (P0/P1)

- Strategy mutation firewall (prevents input DataFrame corruption)
- Equity invariant checks (P1 validation hardening)
- Provenance hashing (traceability for backtest artifacts)
- WFO fail-closed semantics (rejects invalid fold configurations)
