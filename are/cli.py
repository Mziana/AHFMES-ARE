"""
AHFMES P001 — Unified CLI Command Center (ACC-503)

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
        description="AHFMES-ARE Autonomous Recursive Engine — CLI Command Center",
    )
    parser.add_argument("--db-path", default="ahfmes_are.db", help="Path to SQLite EventStore database")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. status
    status_parser = subparsers.add_parser("status", help="Show system, champion and safety status")
    status_parser.add_argument("--json", action="store_true", help="Output status as JSON")

    # 2. run-cycle
    cycle_parser = subparsers.add_parser("run-cycle", help="Run an autonomous scientific research cycle")
    cycle_parser.add_argument("--symbol", default="BTCUSDT", help="Target trading pair symbol")
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

    print(f"[CLI] Running autonomous research cycle for hypothesis {hyp_id}...")
    res = coordinator.run_autonomous_cycle(
        hypothesis_spec={"hypothesis_id": hyp_id, "symbol": args.symbol, "formula": "alpha_momentum_v1"},
        evaluation_func=lambda f: {"performance": 0.91, "score": 0.91},
        market_features={"volatility": 1.1, "trend_strength": 1.5},
        holdout_dataset=[{"timestamp": t_now, "score": 0.91}],
        assignment=assignment,
        as_of_cutoff=t_now + 100,
    )

    print(f"[CLI] Cycle Result: Status = {res.status}")
    print(f"[CLI] Details: {json.dumps(res.details, indent=2)}")

    store.close()
    ledger.close()
    return 0 if res.status == "PROMOTED" else 1


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
    """Persistent kill switch — writes to disk so running engine sees it."""
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
