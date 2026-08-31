"""
AHFMES P001 -- Unified CLI Command Center (ACC-503)

Stdlib only (argparse, sys, json, os, time).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import List, Optional

from are.champion import ChampionRegistry
from are.coordinator import AgentAssignment, ResearchCoordinator
from are.dashboard import TerminalDashboard
from are.evidence import EvidenceLedger
from are.governor import CriticEngine, GovernorEngine
from are.habitat import ConditionAtlas, HabitatAdapter
from are.runner import OperationalRunner, RunnerConfig
from are.safety import CapitalSafetyKernel, SafetyLimits
from are.sandbox import CapabilitySandbox
from are.search_tree import ProgramBudget, SearchTreeEngine
from are.storage import EventStore
from are.telemetry import TelemetryAggregator
from are.validation import ValidationService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="are",
        description="AHFMES-ARE Autonomous Recursive Engine -- CLI Command Center",
    )
    parser.add_argument("--db-path", default="ahfmes_are.db", help="Path to SQLite EventStore database")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. status
    status_parser = subparsers.add_parser("status", help="Show system, champion and safety status")
    status_parser.add_argument("--json", action="store_true", help="Output status as JSON")

    # 2. run-cycle
    cycle_parser = subparsers.add_parser("run-cycle", help="Run an autonomous scientific research cycle")
    cycle_parser.add_argument("--symbol", default="XAUUSD", help="Target trading pair symbol")
    cycle_parser.add_argument("--start", default="2025-01-01", help="Start date (YYYY-MM-DD)")
    cycle_parser.add_argument("--end", default="2026-08-01", help="End date (YYYY-MM-DD)")
    cycle_parser.add_argument("--timeframe", default="H1", help="Timeframe")
    cycle_parser.add_argument("--hypothesis-id", default=None, help="Hypothesis ID to investigate")

    # 3. run-daemon
    daemon_parser = subparsers.add_parser("run-daemon", help="Run the operational daemon loop")
    daemon_parser.add_argument("--symbol", default="BTCUSDT", help="Trading symbol")
    daemon_parser.add_argument("--ticks", type=int, default=10, help="Max ticks to run")
    daemon_parser.add_argument("--interval", type=float, default=0.1, help="Tick interval in seconds")

    # 4. champion
    champ_parser = subparsers.add_parser("champion", help="Champion registry commands")
    champ_subs = champ_parser.add_subparsers(dest="champ_command")
    champ_subs.add_parser("history", help="Show full champion succession history")
    champ_subs.add_parser("rollback", help="Roll back active champion to previous champion")

    # 5. safety-kill
    subparsers.add_parser("safety-kill", help="Activate emergency kill-switch immediately")

    # 5b. safety-release
    subparsers.add_parser("safety-release", help="Release persistent kill-switch")

    # 6. dashboard
    subparsers.add_parser("dashboard", help="Render rich terminal dashboard")

    # 7. backtest
    bt_parser = subparsers.add_parser("backtest", help="Run backtest or WFO analysis")
    bt_subs = bt_parser.add_subparsers(dest="bt_command")
    run_parser = bt_subs.add_parser("run", help="Run a single backtest")
    run_parser.add_argument("--strategy", default="dsr-momentum-001", help="Strategy ID from strategies.json")
    run_parser.add_argument("--symbol", default="XAUUSD", help="Trading symbol")
    run_parser.add_argument("--start", default="2025-01-01", help="Start date (YYYY-MM-DD)")
    run_parser.add_argument("--end", default="2026-08-01", help="End date (YYYY-MM-DD)")
    run_parser.add_argument("--capital", type=float, default=100000, help="Initial capital")
    run_parser.add_argument("--timeframe", default="H1", help="Timeframe")
    wfo_parser = bt_subs.add_parser("wfo", help="Run Walk-Forward Optimization")
    wfo_parser.add_argument("--symbol", default="XAUUSD", help="Trading symbol")
    wfo_parser.add_argument("--strategy", default="dsr-momentum-001", help="Strategy ID from strategies.json")
    wfo_parser.add_argument("--folds", type=int, default=5, help="Number of WFO folds")
    wfo_parser.add_argument("--start", default="2025-01-01", help="Start date")
    wfo_parser.add_argument("--end", default="2026-08-01", help="End date")
    wfo_parser.add_argument("--timeframe", default="H1", help="Timeframe")
    wfo_parser.add_argument("--param-grid", default=None, help='Param grid as JSON: "[{lookback:10},{lookback:20}]" or auto')
    wfo_parser.add_argument("--capital", type=float, default=100000, help="Initial capital")
    bt_subs.add_parser("list", help="List all backtest results")

    # 8. data
    data_parser = subparsers.add_parser("data", help="OHLC data management")
    data_subs = data_parser.add_subparsers(dest="data_command")
    data_export = data_subs.add_parser("export", help="Export OHLC data from MT5 to parquet")
    data_export.add_argument("--symbol", default="XAUUSD", help="Symbol to export")
    data_export.add_argument("--timeframe", default="H1", help="Timeframe")
    data_export.add_argument("--start", default="2020-01-01", help="Start date")
    data_export.add_argument("--end", default="2026-12-31", help="End date")
    data_subs.add_parser("list", help="List available OHLC data files")

    # Research / Backtest OS commands
    res_parser = subparsers.add_parser("research", help="Research Plane: full lifecycle backtest")
    res_subs = res_parser.add_subparsers(dest="res_command")
    res_run = res_subs.add_parser("run", help="Run a full research backtest experiment")
    res_run.add_argument("--symbol", default="XAUUSD", help="Symbol")
    res_run.add_argument("--timeframe", default="H1", help="Timeframe (M1, M5, M15, M30, H1, H4, D1)")
    res_run.add_argument("--start", default="2025-01-01", help="Start date")
    res_run.add_argument("--end", default="2026-08-01", help="End date")
    res_run.add_argument("--lookback", type=int, default=20, help="Strategy lookback period")
    res_run.add_argument("--capital", type=float, default=100000, help="Initial capital")
    res_run.add_argument("--folds", type=int, default=5, help="WFO folds")
    res_subs.add_parser("list", help="List all research runs")
    res_inspect = res_subs.add_parser("inspect", help="Inspect a research run")
    res_inspect.add_argument("run_id", help="Run ID to inspect")
    res_subs.add_parser("datasets", help="List frozen datasets")
    res_subs.add_parser("strategies", help="List registered strategies")
    res_replay = res_subs.add_parser("replay", help="Deterministic replay of a run")
    res_replay.add_argument("run_id", help="Run ID to replay")

    return parser


def handle_status(args: argparse.Namespace) -> int:
    store = EventStore(args.db_path)
    champ_reg = ChampionRegistry(store)
    champ = champ_reg.get_active_champion()

    head_op = store.get_head("operational_signals")
    head_champ = store.get_head("champion_registry")
    head_tel = store.get_head("research_telemetry")

    data = {
        "db_path": args.db_path,
        "active_champion": {
            "champion_id": champ.champion_id if champ else "NONE (GENESIS)",
            "candidate_id": champ.candidate_id if champ else "N/A",
            "status": champ.status if champ else "INACTIVE",
            "activated_at": champ.activated_at if champ else 0.0,
        },
        "streams": {
            "operational_signals": head_op[0] if head_op else 0,
            "champion_registry": head_champ[0] if head_champ else 0,
            "research_telemetry": head_tel[0] if head_tel else 0,
        },
        "chain_health": {
            "champion_registry": store.verify_chain("champion_registry") if head_champ else True,
            "operational_signals": store.verify_chain("operational_signals") if head_op else True,
        },
    }
    store.close()

    if getattr(args, "json", False):
        print(json.dumps(data, indent=2))
    else:
        print("=" * 60)
        print("  AHFMES-ARE NODE STATUS SUMMARY")
        print("=" * 60)
        print(f"  Database Path   : {data['db_path']}")
        print(f"  Active Champion : {data['active_champion']['champion_id']} (Candidate: {data['active_champion']['candidate_id']})")
        print(f"  Champion Status : {data['active_champion']['status']}")
        print(f"  Operational Ticks: {data['streams']['operational_signals']}")
        print(f"  Chain Health    : {'VERIFIED OK' if all(data['chain_health'].values()) else 'CORRUPTED'}")
        print("=" * 60)
    return 0


def handle_run_cycle(args: argparse.Namespace) -> int:
    store = EventStore(args.db_path)
    ledger = EvidenceLedger(args.db_path)
    champ_reg = ChampionRegistry(store)

    budget = ProgramBudget(total_budget=100.0)
    search_tree = SearchTreeEngine(budget)
    sandbox = CapabilitySandbox(default_timeout_sec=2.0)
    telemetry = TelemetryAggregator(store)
    atlas = ConditionAtlas()
    habitat = HabitatAdapter(atlas, store)
    validation = ValidationService(ledger, store)
    critic = CriticEngine()
    governor = GovernorEngine()

    coordinator = ResearchCoordinator(
        search_tree_engine=search_tree,
        sandbox=sandbox,
        telemetry=telemetry,
        habitat=habitat,
        validation=validation,
        critic=critic,
        governor=governor,
        champion_registry=champ_reg,
    )

    t_now = time.time()
    hyp_id = args.hypothesis_id or f"HYP_CLI_{int(t_now) % 10000}"
    assignment = AgentAssignment(
        discovery_agent="CLI_Discovery_Agent",
        validation_agent="CLI_Validation_Agent",
        governor_agent="CLI_Governor_Agent",
    )

    # Load REAL market data for evaluation (not hardcoded 0.91)
    try:
        from are.data_loader import load_ohlc_data
        from are.backtest_enhanced import EnhancedBacktestEngine
        from are.strategy_engine import load_strategy_from_config
        timeframe = getattr(args, 'timeframe', 'H1')
        df_real = load_ohlc_data(args.symbol, timeframe, args.start, args.end)
        # Run real backtest to get actual metrics
        engine = EnhancedBacktestEngine()
        with open("data/strategies/strategies.json") as _f:
            _strats = json.load(_f)
        _strat_list = _strats if isinstance(_strats, list) else _strats.get("strategies", [])
        strategy_logic = load_strategy_from_config(_strat_list[0]) if _strat_list else None
        if strategy_logic and len(df_real) > 0:
            bt_result = engine.run_backtest(
                strategy_logic=strategy_logic, historical_data=df_real,
                initial_capital=100000, timeframe_seconds=3600.0,
            )
            m = bt_result.metrics
            eval_score = m.get('sharpe_ratio', 0.0)
            eval_data = {
                "performance": round(eval_score, 4),
                "score": round(eval_score, 4),
                "win_rate": m.get('win_rate', 0),
                "total_trades": m.get('total_trades', 0),
                "max_drawdown": m.get('max_drawdown_pct', 0),
            }
            # Build holdout from last 20% of real OOS returns
            split = int(len(df_real) * 0.8)
            holdout_df = df_real.slice(split)
            holdout_dataset = [
                {"timestamp": int(holdout_df['timestamp'][i]), "score": float(holdout_df['price'][i])}
                for i in range(len(holdout_df))
            ]
            print(f"  Real data: {len(df_real)} bars, Sharpe={eval_score:.4f}, holdout={len(holdout_dataset)} bars")
        else:
            raise ValueError("No strategy or data available")
    except Exception as e:
        print(f"  Real data unavailable ({e}), using minimal fallback")
        eval_data = {"performance": 0.0, "score": 0.0}
        holdout_dataset = [{"timestamp": t_now, "score": 0.0}]

    print(f"[CLI] Running autonomous research cycle for hypothesis {hyp_id}...")
    res = coordinator.run_autonomous_cycle(
        hypothesis_spec={"hypothesis_id": hyp_id, "symbol": args.symbol, "formula": "alpha_momentum_v1"},
        evaluation_func=lambda f: eval_data,
        market_features={"volatility": 1.1, "trend_strength": 1.5},
        holdout_dataset=holdout_dataset,
        assignment=assignment,
        as_of_cutoff=t_now + 100,
    )

    print(f"[CLI] Cycle Result: Status = {res.status}")
    print(f"[CLI] Details: {json.dumps(res.details, indent=2)}")

    store.close()
    ledger.close()
    # Both PROMOTED and REJECTED are valid cycle outcomes
    return 0 if res.status in ("PROMOTED", "REJECTED") else 1


def handle_run_daemon(args: argparse.Namespace) -> int:
    config = RunnerConfig(
        db_path=args.db_path,
        symbol=args.symbol,
        tick_interval_sec=args.interval,
        auto_evolve=True,
    )
    runner = OperationalRunner(config)

    # Synthetic tick generator
    counter = 0
    def tick_gen():
        nonlocal counter
        counter += 1
        vol = 1.0 if counter % 7 != 0 else 3.0 # Shock every 7th tick
        features = {"volatility": vol, "trend_strength": 1.2}
        risk = {"drawdown": 0.01, "volatility": vol, "order_count": counter % 5}
        return features, risk

    print(f"[CLI] Starting Operational Daemon (max_ticks={args.ticks}, interval={args.interval}s)...")
    ticks = runner.run_loop(tick_gen, max_ticks=args.ticks)
    print(f"[CLI] Operational Daemon completed. Processed {ticks} ticks.")

    runner.close()
    return 0


def handle_champion(args: argparse.Namespace) -> int:
    store = EventStore(args.db_path)
    champ_reg = ChampionRegistry(store)

    if args.champ_command == "history":
        records = champ_reg.list_champion_lineage()
        print("=" * 70)
        print(f"  CHAMPION SUCCESSION HISTORY ({len(records)} records)")
        print("=" * 70)
        for r in records:
            act_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(r.activated_at))
            print(f"  [{r.status:10s}] {r.champion_id} (Candidate: {r.candidate_id}) Activated: {act_str}")
        print("=" * 70)
    elif args.champ_command == "rollback":
        active_before = champ_reg.get_active_champion()
        if not active_before:
            print("[CLI] No active champion to roll back.")
        else:
            rolled = champ_reg.rollback_champion("CLI Emergency Rollback")
            if rolled:
                print(f"[CLI] Successfully rolled back champion {active_before.champion_id} to {rolled.champion_id}.")
            else:
                print(f"[CLI] Rolled back champion {active_before.champion_id}. No previous active champion exists.")

    store.close()
    return 0


def handle_safety_kill(args: argparse.Namespace) -> int:
    """Persistent kill switch -- writes to disk so running engine sees it."""
    from are.execution_state import ExecutionStateMachine
    exec_state = ExecutionStateMachine()
    exec_state.set_kill_switch(True)
    # Also verify via CSK
    limits = SafetyLimits(kill_switch_active=True)
    kernel = CapitalSafetyKernel(limits)
    decision = kernel.evaluate_action(
        intended_action={"action": "BUY", "position_size": 0.5},
        current_drawdown=0.01,
        current_volatility=1.0,
        recent_order_count=0,
    )
    print(f"[CLI] PERSISTENT KILL SWITCH ACTIVATED")
    print(f"  State file: {exec_state.state_file}")
    print(f"  CSK Decision: allowed={decision.allowed}, reason={decision.reason}")
    print(f"  All running ARE engines will block orders until kill switch is released.")
    return 0


def handle_safety_release(args: argparse.Namespace) -> int:
    """Release persistent kill switch."""
    from are.execution_state import ExecutionStateMachine
    exec_state = ExecutionStateMachine()
    exec_state.set_kill_switch(False)
    print(f"[CLI] KILL SWITCH RELEASED")
    print(f"  State file: {exec_state.state_file}")
    print(f"  All running ARE engines will resume normal operation.")
    return 0


def handle_dashboard(args: argparse.Namespace) -> int:
    store = EventStore(args.db_path)
    champ_reg = ChampionRegistry(store)
    kernel = CapitalSafetyKernel(SafetyLimits())
    dashboard = TerminalDashboard()

    dashboard.print_dashboard(champ_reg, kernel, store)
    store.close()
    return 0


def handle_backtest(args: argparse.Namespace) -> int:
    """Run backtest or WFO analysis."""
    import json as _json
    from are.backtest_enhanced import EnhancedBacktestEngine
    engine = EnhancedBacktestEngine()

    if args.bt_command == "run":
        # Load strategy from strategies.json
        strat_path = os.path.join("data", "strategies", "strategies.json")
        strategy_logic = None
        initial_capital = args.capital
        if os.path.exists(strat_path):
            with open(strat_path) as f:
                raw = _json.load(f)
            strats = raw if isinstance(raw, list) else raw.get("strategies", [])
            for s in strats:
                if s.get("id") == args.strategy or s.get("name", "").lower().replace(" ", "-") == args.strategy:
                    from are.strategy_engine import load_strategy_from_config
                    strategy_logic = load_strategy_from_config(s)
                    print(f"  Loaded strategy: {s.get('name', s.get('id'))} (family={s.get('family', 'auto')})")
                    break

        # Load real OHLC data from MT5 export or parquet
        import polars as pl
        from are.data_loader import load_ohlc_data, export_mt5_ohlc
        try:
            df = load_ohlc_data(args.symbol, args.timeframe, args.start, args.end)
        except FileNotFoundError:
            print(f"  No parquet data for {args.symbol}. Exporting from MT5...")
            try:
                export_mt5_ohlc(args.symbol, args.timeframe, args.start, args.end)
                df = load_ohlc_data(args.symbol, args.timeframe, args.start, args.end)
            except Exception as e:
                print(f"  FATAL: Cannot load data for {args.symbol}: {e}")
                print(f"  Export MT5 data first: python -m are.cli data export --symbol {args.symbol}")
                return 1

        def default_strategy(df: pl.DataFrame) -> pl.DataFrame:
            # Generate signal from price data (engine purifies non-price cols)
            df = df.with_columns(
                pl.col("price").pct_change(20).alias("_momentum")
            ).with_columns(
                pl.when(pl.col("_momentum") > 0.02).then(1.0)
                .when(pl.col("_momentum") < -0.02).then(-1.0)
                .otherwise(0.0).alias("signal")
            ).drop("_momentum")
            return df

        bt_func = strategy_logic if strategy_logic else default_strategy
        result = engine.run_backtest(
            strategy_logic=bt_func,
            historical_data=df,
            initial_capital=initial_capital,
            timeframe_seconds=3600.0,
        )
        metrics = result.metrics
        print(f"\n{'='*60}")
        print(f"BACKTEST RESULTS -- {args.symbol} {args.timeframe}")
        print(f"{'='*60}")
        print(f"  Period:      {args.start} to {args.end}")
        print(f"  Capital:     ${initial_capital:,.2f}")
        print(f"  Trades:      {metrics.get('total_trades', 0)}")
        print(f"  Win Rate:    {metrics.get('win_rate', 0):.1f}%")
        net_pnl = metrics.get('final_equity', initial_capital) - initial_capital
        print(f"  Net PnL:     ${net_pnl:,.2f} ({metrics.get('total_return_pct', 0):.1f}%)")
        print(f"  Sharpe:      {metrics.get('sharpe_ratio', 0):.3f}")
        print(f"  Max DD:      {metrics.get('max_drawdown_pct', 0):.2f}%")
        print(f"  PF:          {metrics.get('profit_factor', 0):.2f}")
        print(f"{'='*60}\n")

        # Save result to data/backtests/
        import time as _time
        bt_dir = os.path.join("data", "backtests")
        os.makedirs(bt_dir, exist_ok=True)
        bt_id = f"bkt-{int(_time.time()*1000)}"
        bt_file = os.path.join(bt_dir, f"{bt_id}.json")
        with open(bt_file, "w") as f:
            _json.dump({
                "id": bt_id,
                "strategy_id": args.strategy,
                "symbol": args.symbol,
                "timeframe": args.timeframe,
                "start": args.start,
                "end": args.end,
                "initial_capital": initial_capital,
                "metrics": metrics,
                "saved_at": _time.time(),
            }, f, indent=2)
        print(f"  Saved to: {bt_file}")
        return 0

    elif args.bt_command == "wfo":
        import polars as pl
        import math, time as _time
        from are.data_loader import load_ohlc_data, export_mt5_ohlc
        from are.strategy_engine import load_strategy_from_config

        # Load real OHLC data
        try:
            df = load_ohlc_data(args.symbol, args.timeframe, args.start, args.end)
            print(f"  Loaded {len(df)} bars: {args.symbol} {args.timeframe}")
        except FileNotFoundError:
            print(f"  No parquet data for {args.symbol}. Exporting from MT5...")
            try:
                export_mt5_ohlc(args.symbol, args.timeframe, args.start, args.end)
                df = load_ohlc_data(args.symbol, args.timeframe, args.start, args.end)
                print(f"  Exported and loaded {len(df)} bars")
            except Exception as e:
                print(f"  FATAL: Cannot load data for {args.symbol}: {e}")
                return 1

        # Load strategy from registry (not hardcoded)
        strat_path = os.path.join("data", "strategies", "strategies.json")
        strategy_logic = None
        strategy_id = args.strategy
        if os.path.exists(strat_path):
            with open(strat_path) as _f:
                raw = _json.load(_f)
            strats = raw if isinstance(raw, list) else raw.get("strategies", [])
            for s in strats:
                if s.get("id") == args.strategy or s.get("name", "").lower().replace(" ", "-") == args.strategy:
                    strategy_logic = load_strategy_from_config(s)
                    strategy_id = s.get("id", args.strategy)
                    print(f"  Strategy: {s.get('name', strategy_id)} (family={s.get('family', 'auto')})")
                    break
        if not strategy_logic:
            # Fallback: default momentum strategy
            def strategy_logic(df_inner):
                return df_inner.with_columns(
                    pl.col("price").rolling_mean(20).alias("fast_ma"),
                    pl.col("price").rolling_mean(50).alias("slow_ma"),
                ).with_columns(
                    pl.when(pl.col("fast_ma") > pl.col("slow_ma")).then(1.0)
                    .when(pl.col("fast_ma") < pl.col("slow_ma")).then(-1.0)
                    .otherwise(0.0).alias("signal")
                )
            print(f"  Strategy: fallback momentum (ID: {strategy_id})")

        # Build strategy_factory: wraps real strategy with parameter injection
        def strategy_factory(params):
            def logic(df_inner):
                df_with_params = df_inner
                for k, v in params.items():
                    df_with_params = df_with_params.with_columns(
                        pl.lit(v).alias(f"_param_{k}")
                    )
                try:
                    result = strategy_logic(df_with_params)
                    if "signal" in result.columns:
                        return result
                except Exception:
                    pass
                return strategy_logic(df_inner)
            return logic

        # Parse param_grid from CLI or auto-generate from strategy defaults
        if args.param_grid:
            try:
                param_grid = _json.loads(args.param_grid)
                if not isinstance(param_grid, list):
                    raise ValueError("param_grid must be a list of dicts")
            except Exception as e:
                print(f"  ERROR: Invalid param_grid: {e}")
                return 1
        else:
            # Auto-generate: vary lookback if strategy has it, else use sensible defaults
            param_grid = [{"lookback": lb} for lb in range(10, 50, 5)]
            print(f"  Param grid: auto ({len(param_grid)} combos, lookback 10-45)")

        print(f"  Running WFO: {args.folds} folds, {len(param_grid)} param combos...")
        wfo_result = engine.run_walk_forward_optimization(
            strategy_factory=strategy_factory,
            param_grid=param_grid,
            historical_data=df,
            train_window_bars=max(200, df.height // (args.folds * 2)),
            test_window_bars=max(50, df.height // (args.folds * 4)),
            step_bars=max(50, df.height // (args.folds * 4)),
            purge_bars=5,
            label_horizon_bars=1,
            initial_capital=args.capital,
            timeframe_seconds=3600.0,
        )
        print(f"\nWFO COMPLETE -- {strategy_id}, {args.folds} folds, {len(param_grid)} combos")
        print(f"  Pooled OOS Sharpe : {wfo_result.pooled_oos_sharpe:.3f}")
        print(f"  Pooled OOS Return : {wfo_result.pooled_oos_return * 100:.2f}%")
        print(f"  Mean WFE          : {wfo_result.mean_wfe:.3f}")
        print(f"  Fold count        : {wfo_result.fold_count}")
        print(f"  Effective trials  : {wfo_result.effective_trial_count}")

        # Auto-save WFOEvidence
        import os as _os
        wfo_dir = os.path.join("data", "backtests")
        _os.makedirs(wfo_dir, exist_ok=True)
        wfo_file = os.path.join(wfo_dir, f"wfo-{strategy_id}-{int(_time.time()*1000)}.json")
        try:
            with open(wfo_file, "w") as f:
                _json.dump({
                    "strategy_id": strategy_id,
                    "symbol": args.symbol,
                    "timeframe": args.timeframe,
                    "start": args.start,
                    "end": args.end,
                    "fold_count": wfo_result.fold_count,
                    "pooled_oos_sharpe": wfo_result.pooled_oos_sharpe,
                    "pooled_oos_return": wfo_result.pooled_oos_return,
                    "pooled_oos_max_drawdown": wfo_result.pooled_oos_max_drawdown,
                    "mean_wfe": wfo_result.mean_wfe,
                    "effective_trial_count": wfo_result.effective_trial_count,
                    "param_grid": param_grid,
                    "provenance_hash": wfo_result.provenance_hash,
                    "saved_at": _time.time(),
                }, f, indent=2)
            print(f"  Saved to: {wfo_file}")
        except Exception as e:
            print(f"  WARNING: Could not save WFO evidence: {e}")

        # Update strategies.json with WFO results
        try:
            if os.path.exists(strat_path):
                with open(strat_path) as f:
                    strats_raw = _json.load(f)
                strats_list = strats_raw if isinstance(strats_raw, list) else strats_raw.get("strategies", [])
                for s in strats_list:
                    if s.get("id") == strategy_id:
                        s.setdefault("metrics", {})
                        s["metrics"]["wfo_sharpe"] = round(wfo_result.pooled_oos_sharpe, 4)
                        s["metrics"]["wfo_return"] = round(wfo_result.pooled_oos_return * 100, 2)
                        s["metrics"]["wfo_max_dd"] = round(wfo_result.pooled_oos_max_drawdown * 100, 2)
                        s["metrics"]["wfo_folds"] = wfo_result.fold_count
                        s["metrics"]["wfo_effective_trials"] = wfo_result.effective_trial_count
                        s.setdefault("backtestHistory", [])
                        s["backtestHistory"].append({
                            "type": "wfo",
                            "sharpe": round(wfo_result.pooled_oos_sharpe, 4),
                            "return": round(wfo_result.pooled_oos_return * 100, 2),
                            "timestamp": _time.time(),
                        })
                        s["backtestHistory"] = s["backtestHistory"][-50:]
                        break
                save_raw = strats_raw if isinstance(strats_raw, list) else {"strategies": strats_list}
                with open(strat_path, "w") as f:
                    _json.dump(save_raw, f, indent=2)
                print(f"  Updated strategies.json for {strategy_id}")
        except Exception as e:
            print(f"  WARNING: Could not update strategies.json: {e}")

        return 0

    elif args.bt_command == "list":
        bt_dir = os.path.join("data", "backtests")
        if not os.path.exists(bt_dir):
            print("No backtests found."); return 0
        files = sorted([f for f in os.listdir(bt_dir) if f.endswith(".json")])
        print(f"\n{'ID':<25} {'Strategy':<25} {'Trades':<8} {'WR':<8} {'Sharpe':<8}")
        print("-" * 80)
        for fn in files:
            with open(os.path.join(bt_dir, fn)) as f:
                bt = _json.load(f)
            m = bt.get("metrics", {})
            print(f"{bt.get('id','?'):<25} {bt.get('strategy_id','?'):<25} {m.get('total_trades',0):<8} {m.get('win_rate',0):.1f}%  {m.get('sharpe_ratio',0):.3f}")
        print()
        return 0

    print("Usage: are backtest {run|wfo|list}")
    return 0


def handle_data(args: argparse.Namespace) -> int:
    from are.data_loader import export_mt5_ohlc, load_ohlc_data, list_available_data

    if args.data_command == "export":
        try:
            filepath = export_mt5_ohlc(args.symbol, args.timeframe, args.start, args.end)
            print(f"  Exported to: {filepath}")
            return 0
        except Exception as e:
            print(f"  Export failed: {e}")
            return 1

    elif args.data_command == "list":
        list_available_data()
        return 0

    print("Usage: are data {export|list}")
    return 0


def handle_research(args: argparse.Namespace) -> int:
    """Research Plane CLI: full lifecycle backtest via orchestrator."""
    if not args.res_command:
        print("Usage: are research {run|list|inspect|datasets|strategies}")
        return 0

    if args.res_command == "run":
        return _research_run(args)
    elif args.res_command == "list":
        return _research_list()
    elif args.res_command == "inspect":
        return _research_inspect(args)
    elif args.res_command == "datasets":
        return _research_datasets()
    elif args.res_command == "strategies":
        return _research_strategies()
    elif args.res_command == "replay":
        return _research_replay(args)

    return 0


def _research_run(args: argparse.Namespace) -> int:
    """Execute a full research backtest experiment."""
    from are.research import (
        BacktestOrchestrator, DatasetRegistry, StrategyRegistry,
        build_execution_model, build_parameter_grid, build_experiment_config,
    )
    from are.data_loader import load_ohlc_data
    from are.strategy_engine import load_strategy_from_config
    import polars as pl

    print("=" * 60)
    print("  RESEARCH BACKTEST -- Full Lifecycle")
    print("=" * 60)

    # Step 1: Load data
    timeframe = getattr(args, 'timeframe', 'H1')
    print(f"\n[1/6] Loading data: {args.symbol} {timeframe} {args.start} to {args.end}...")
    try:
        df = load_ohlc_data(args.symbol, timeframe, args.start, args.end)
        print(f"  Loaded {len(df)} bars")
    except Exception as e:
        print(f"  Data load failed: {e}")
        print("  Exporting from MT5...")
        from are.data_loader import export_mt5_ohlc
        try:
            filepath = export_mt5_ohlc(args.symbol, timeframe, args.start, args.end)
            df = pl.read_parquet(filepath)
            print(f"  Exported and loaded {len(df)} bars")
        except Exception as e2:
            print(f"  FATAL: Cannot load data: {e2}")
            return 1

    # Step 2: Register dataset
    print("\n[2/6] Registering dataset...")
    ds_reg = DatasetRegistry()
    ds_manifest = ds_reg.register_dataset(
        symbol=args.symbol, df=df, timeframe_seconds=3600.0,
    )
    print(f"  Dataset: {ds_manifest.dataset_id}")
    print(f"  Raw hash: {ds_manifest.raw_hash[:16]}...")
    print(f"  Purified hash: {ds_manifest.purified_hash[:16]}...")
    print(f"  Quality: {ds_manifest.quality_report}")

    # Step 3: Load strategy
    print("\n[3/6] Loading strategy...")
    strat_reg = StrategyRegistry()
    try:
        import json as _json
        with open("data/strategies/strategies.json") as _f:
            _strats = _json.load(_f)
        _strat_list = _strats if isinstance(_strats, list) else _strats.get("strategies", [])
        if _strat_list:
            _s = _strat_list[0]
            strategy_logic = load_strategy_from_config(_s)
            strategy_id = _s.get("id", "unknown")
        else:
            raise ValueError("No strategies in registry")
    except Exception:
        # Fallback to default momentum
        def strategy_logic(df_inner):
            return df_inner.with_columns(
                pl.col("price").rolling_mean(args.lookback).alias("fast_ma"),
                pl.col("price").rolling_mean(max(args.lookback * 2, args.lookback + 10)).alias("slow_ma"),
            ).with_columns(
                pl.when(pl.col("fast_ma") > pl.col("slow_ma")).then(1.0)
                .when(pl.col("fast_ma") < pl.col("slow_ma")).then(-1.0)
                .otherwise(0.0).alias("signal")
            )
        strategy_id = f"momentum-{args.lookback}"

    identity = strat_reg.register_strategy(
        strategy_id=strategy_id,
        strategy_name=f"Strategy {strategy_id}",
        strategy_family="MOMENTUM",
        strategy_func=strategy_logic,
        parameter_schema={"lookback": {"type": "int", "min": 5, "max": 200, "default": args.lookback}},
    )
    print(f"  Strategy: {identity.strategy_id}")
    print(f"  Source hash: {identity.source_hash[:16]}...")

    # Step 4: Build config
    print("\n[4/6] Building experiment config...")
    em = build_execution_model(initial_capital=args.capital)
    pg = build_parameter_grid("lookback", list(range(10, 60, 5)))
    config = build_experiment_config(
        strategy=identity, execution_model=em, parameter_grid=pg,
        wfo_n_folds=args.folds,
    )
    print(f"  Config: {config.experiment_id}")
    print(f"  Config hash: {config.config_hash[:16]}...")

    # Step 5: Run orchestrator
    print("\n[5/6] Running backtest lifecycle...")
    def progress(stage, result):
        icon = "[OK]" if result.status.value == "PASSED" else "[FAIL]" if result.status.value == "FAILED" else "-"
        print(f"  {icon} {stage}: {result.status.value}")
        if result.error:
            print(f"    Error: {result.error}")

    orch = BacktestOrchestrator()
    run = orch.run_experiment(
        config=config, dataset_manifest=ds_manifest, df=df,
        strategy_logic=strategy_logic, callback=progress,
    )

    # Step 6: Report
    print(f"\n[6/6] Results")
    print("=" * 60)
    print(f"  Run ID:      {run.run_id}")
    print(f"  Status:      {run.status.value}")
    print(f"  Duration:    {run.completed_at - run.started_at:.1f}s")
    if run.final_gate:
        gate = run.final_gate
        print(f"  Final Gate:  {gate['decision']} ({gate['passed']}/{gate['total']} checks)")
    if run.oos_result:
        print(f"  OOS Sharpe:  {run.oos_result.get('pooled_sharpe', 0):.4f}")
        print(f"  OOS Return:  {run.oos_result.get('pooled_return', 0) * 100:.2f}%")
        print(f"  OOS Max DD:  {run.oos_result.get('pooled_max_dd', 0) * 100:.2f}%")
    if run.provenance_hash:
        print(f"  Provenance:  {run.provenance_hash[:16]}...")
    if run.artifact_manifest:
        print(f"  Artifact:    {run.artifact_manifest.artifact_hash[:16]}...")
    print("=" * 60)
    return 0 if run.status.value == "COMPLETED" else 1


def _research_list() -> int:
    from are.research import BacktestOrchestrator
    orch = BacktestOrchestrator()
    runs = orch.list_runs()
    if not runs:
        print("  No research runs found.")
        return 0
    print(f"{'Run ID':<30} {'Strategy':<20} {'Status':<12} {'Gate':<10}")
    print("-" * 72)
    for r in runs:
        print(f"{r['run_id']:<30} {r['strategy_id']:<20} {r['status']:<12} {r['gate']:<10}")
    return 0


def _research_inspect(args: argparse.Namespace) -> int:
    from are.research import BacktestOrchestrator
    orch = BacktestOrchestrator()
    try:
        run = orch.load_run(args.run_id)
        import json
        print(json.dumps(run.to_dict(), indent=2, default=str))
        return 0
    except FileNotFoundError:
        print(f"  Run {args.run_id} not found.")
        return 1


def _research_datasets() -> int:
    from are.research import DatasetRegistry
    reg = DatasetRegistry()
    datasets = reg.list_datasets()
    if not datasets:
        print("  No frozen datasets.")
        return 0
    for ds in datasets:
        print(f"  {ds.dataset_id}: {ds.symbol} {ds.raw_rows} rows, raw={ds.raw_hash[:12]}... pur={ds.purified_hash[:12]}...")
    return 0


def _research_strategies() -> int:
    from are.research import StrategyRegistry
    reg = StrategyRegistry()
    strategies = reg.list_strategies()
    if not strategies:
        print("  No registered strategies.")
        return 0
    for s in strategies:
        print(f"  {s.strategy_id}: {s.strategy_name} v{s.strategy_version} family={s.strategy_family} src={s.source_hash[:12]}...")
    return 0


def _research_replay(args: argparse.Namespace) -> int:
    """Deterministic replay: re-run a backtest from frozen config and verify hashes match."""
    import json as _json
    from are.research import BacktestOrchestrator, DatasetRegistry, StrategyRegistry, build_execution_model, build_parameter_grid, build_experiment_config
    from are.strategy_engine import load_strategy_from_config
    from are.hasher import compute_sha256
    import polars as pl

    print(f"=" * 60)
    print(f"  DETERMINISTIC REPLAY: {args.run_id}")
    print(f"=" * 60)

    # Load original run
    orch = BacktestOrchestrator()
    try:
        original_run = orch.load_run(args.run_id)
    except FileNotFoundError:
        print(f"  Run {args.run_id} not found.")
        return 1

    print(f"  Original status: {original_run.status.value}")
    print(f"  Original gate: {original_run.final_gate.get('decision', 'UNKNOWN') if original_run.final_gate else 'N/A'}")
    original_hash = original_run.artifact_manifest.artifact_hash if original_run.artifact_manifest else 'N/A'
    print(f"  Original artifact hash: {original_hash[:16]}...")

    # Load original config
    config_file = f"data/backtest_runs/{args.run_id}/config.json"
    try:
        with open(config_file) as f:
            config_data = _json.load(f)
    except FileNotFoundError:
        print(f"  Config file not found for {args.run_id}.")
        return 1

    print(f"  Config hash: {config_data.get('config_hash', 'N/A')[:16]}...")
    print(f"\n  Re-running from frozen config...")

    # Load dataset
    ds_reg = DatasetRegistry()
    ds_id = original_run.dataset_id
    try:
        df, ds_manifest = ds_reg.load_dataset(ds_id)
    except FileNotFoundError:
        print(f"  Dataset {ds_id} not found. Cannot replay.")
        return 1

    print(f"  Dataset: {ds_id} ({len(df)} bars)")

    # Load strategy
    try:
        with open("data/strategies/strategies.json") as _f:
            _strats = _json.load(_f)
        _strat_list = _strats if isinstance(_strats, list) else _strats.get("strategies", [])
        if _strat_list:
            _s = _strat_list[0]
            strategy_logic = load_strategy_from_config(_s)
            strategy_id = _s.get("id", "unknown")
        else:
            raise ValueError("No strategies")
    except Exception:
        def strategy_logic(df_inner):
            return df_inner.with_columns(
                pl.col("price").rolling_mean(20).alias("fast_ma"),
                pl.col("price").rolling_mean(50).alias("slow_ma"),
            ).with_columns(
                pl.when(pl.col("fast_ma") > pl.col("slow_ma")).then(1.0)
                .when(pl.col("fast_ma") < pl.col("slow_ma")).then(-1.0)
                .otherwise(0.0).alias("signal")
            )
        strategy_id = "momentum-20"

    # Rebuild config from frozen values
    from are.research.experiment_config import StrategyIdentity, ExecutionModel, ParameterGrid, ExperimentConfig
    strategy = StrategyIdentity(**config_data["strategy"]) if isinstance(config_data.get("strategy"), dict) else StrategyIdentity(
        strategy_id=strategy_id, strategy_name=strategy_id, strategy_version="1.0.0",
        strategy_family="MOMENTUM", source_hash="", parameter_schema={},
        signal_contract="discrete_ternary", lookback_bars=20, warmup_bars=50,
        execution_assumption="next_bar_open",
    )
    execution_model = ExecutionModel(**config_data["execution_model"]) if isinstance(config_data.get("execution_model"), dict) else build_execution_model()
    parameter_grid = ParameterGrid(**config_data["parameter_grid"]) if isinstance(config_data.get("parameter_grid"), dict) else build_parameter_grid("lookback", list(range(10, 60, 5)))

    replay_config = ExperimentConfig(
        experiment_id=config_data.get("experiment_id", "replay"),
        created_at=config_data.get("created_at", 0),
        strategy=strategy, execution_model=execution_model, parameter_grid=parameter_grid,
        wfo_train_window_bars=config_data.get("wfo_train_window_bars", 500),
        wfo_test_window_bars=config_data.get("wfo_test_window_bars", 100),
        wfo_step_bars=config_data.get("wfo_step_bars", 100),
        wfo_purge_bars=config_data.get("wfo_purge_bars", 10),
        wfo_warmup_bars=config_data.get("wfo_warmup_bars", 50),
        wfo_n_folds=config_data.get("wfo_n_folds", 5),
        wfo_selection_metric=config_data.get("wfo_selection_metric", "sharpe_ratio"),
        wfo_tie_breaker=config_data.get("wfo_tie_breaker", "(sharpe, -max_dd, -turnover)"),
        dsr_enabled=config_data.get("dsr_enabled", True),
        mc_enabled=config_data.get("mc_enabled", True),
        mc_simulations=config_data.get("mc_simulations", 1000),
        crisis_enabled=config_data.get("crisis_enabled", True),
        config_hash=config_data.get("config_hash", ""),
    )

    # Run replay
    def progress(stage, result):
        icon = "OK" if result.status.value == "PASSED" else "FAIL" if result.status.value == "FAILED" else "--"
        print(f"  [{icon}] {stage}: {result.status.value}")

    replay_run = orch.run_experiment(
        config=replay_config, dataset_manifest=ds_manifest, df=df,
        strategy_logic=strategy_logic, callback=progress,
    )

    # Compare
    replay_hash = replay_run.artifact_manifest.artifact_hash if replay_run.artifact_manifest else 'N/A'
    print(f"\n  Replay status: {replay_run.status.value}")
    print(f"  Replay artifact hash: {replay_hash[:16]}...")

    if original_hash == replay_hash:
        print(f"  MATCH: Artifact hashes identical. Replay is deterministic.")
        return 0
    else:
        print(f"  MISMATCH: Artifact hashes differ. Replay is NOT deterministic.")
        print(f"    Original: {original_hash[:16]}...")
        print(f"    Replay:   {replay_hash[:16]}...")
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "status":
        return handle_status(args)
    elif args.command == "run-cycle":
        return handle_run_cycle(args)
    elif args.command == "run-daemon":
        return handle_run_daemon(args)
    elif args.command == "champion":
        return handle_champion(args)
    elif args.command == "safety-kill":
        return handle_safety_kill(args)
    elif args.command == "safety-release":
        return handle_safety_release(args)
    elif args.command == "dashboard":
        return handle_dashboard(args)
    elif args.command == "backtest":
        return handle_backtest(args)
    elif args.command == "data":
        return handle_data(args)
    elif args.command == "research":
        return handle_research(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
