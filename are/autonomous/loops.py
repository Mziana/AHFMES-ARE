"""
Autonomous Loops — Micro/Meso/Macro cycle orchestration
Ties together Memory, Scheduler, Planner, Reasoner, Executor into the main agent loop.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
from collections import defaultdict


# ─── Configuration ──────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "autonomous"
LOOPS_DIR = DATA_DIR / "loops"
LOOPS_DIR.mkdir(parents=True, exist_ok=True)

# Import autonomous modules
from are.autonomous.memory import AutonomousMemory, MemoryTier
from are.autonomous.scheduler import AutonomousScheduler, ScheduleType, ScheduledTask
from are.autonomous.planner import AutonomousPlanner, Plan, GoalType, PlanStep, TaskStatus
from are.autonomous.reasoner import AutonomousReasoner, ReasoningType, ReasoningTrace, create_openrouter_client
from are.autonomous.executor import AutonomousExecutor, ExecutionRequest, ExecutionStatus, ToolCategory, ToolSpec


# ─── Types & Enums ──────────────────────────────────────────────────────────────

class LoopLevel(Enum):
    MICRO = "micro"       # Per-tick (1-5 sec): perception → decision → action
    MESO = "meso"         # Per-cycle (1-5 min): analysis → planning → execution
    MACRO = "macro"       # Per-session (hours): strategy evolution → learning → improvement


class AgentState(Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class LoopContext:
    """Context passed through each loop iteration."""
    loop_level: LoopLevel
    iteration: int
    timestamp: float
    market_state: Dict[str, Any] = field(default_factory=dict)
    agent_state: Dict[str, Any] = field(default_factory=dict)
    safety_state: Dict[str, Any] = field(default_factory=dict)
    memory_snapshot: Dict[str, Any] = field(default_factory=dict)
    previous_action: str = ""
    previous_result: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoopResult:
    """Result of a loop iteration."""
    loop_level: LoopLevel
    iteration: int
    success: bool
    actions_taken: List[str] = field(default_factory=list)
    reasoning_trace_id: str = ""
    plan_id: str = ""
    execution_results: List[Any] = field(default_factory=list)
    duration_ms: float = 0
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# ─── Loop Handlers (Default implementations) ────────────────────────────────────

def default_micro_loop(context: LoopContext, components: Dict[str, Any]) -> LoopResult:
    """
    Micro loop (1-5 sec): Fast perception → decision → action
    Used for: tick processing, position management, safety checks
    """
    start = time.time()
    actions = []
    
    try:
        executor: AutonomousExecutor = components["executor"]
        memory: AutonomousMemory = components["memory"]
        
        # 1. Perception - get market state
        market_result = executor.execute("get_mt5_live_data", {"symbol": "XAUUSD"})
        if market_result.status == ExecutionStatus.COMPLETED:
            context.market_state = market_result.result
            actions.append("market_data_updated")
        
        # 2. Safety check
        safety_result = executor.execute("get_safety_limits")
        if safety_result.status == ExecutionStatus.COMPLETED:
            context.safety_state = safety_result.result
            actions.append("safety_checked")
            
            # Kill switch check
            if safety_result.result.get("kill_switch"):
                return LoopResult(
                    loop_level=LoopLevel.MICRO,
                    iteration=context.iteration,
                    success=True,
                    actions_taken=actions + ["kill_switch_active"],
                    duration_ms=(time.time() - start) * 1000
                )
        
        # 3. Quick position management
        # (Actual position management would be here)
        actions.append("position_monitored")
        
        # 4. Store episodic memory
        memory.store_episodic(
            event_type="micro_loop",
            content={"market": context.market_state, "safety": context.safety_state},
            tags=["micro", "tick"]
        )
        
        return LoopResult(
            loop_level=LoopLevel.MICRO,
            iteration=context.iteration,
            success=True,
            actions_taken=actions,
            duration_ms=(time.time() - start) * 1000
        )
        
    except Exception as e:
        return LoopResult(
            loop_level=LoopLevel.MICRO,
            iteration=context.iteration,
            success=False,
            actions_taken=actions,
            error=str(e),
            duration_ms=(time.time() - start) * 1000
        )


def default_meso_loop(context: LoopContext, components: Dict[str, Any]) -> LoopResult:
    """
    Meso loop (1-5 min): Analysis → Planning → Execution
    Used for: opportunity scanning, trade execution, backtest scheduling
    """
    start = time.time()
    actions = []
    
    try:
        executor: AutonomousExecutor = components["executor"]
        planner: AutonomousPlanner = components["planner"]
        reasoner: AutonomousReasoner = components["reasoner"]
        memory: AutonomousMemory = components["memory"]
        
        # 1. Reason about current state
        trace = reasoner.reason(
            trigger="meso_cycle",
            context={
                "market": context.market_state,
                "safety": context.safety_state,
                "agent": context.agent_state
            },
            goal="Scan for trading opportunities and manage positions",
            available_tools=executor.list_tools()
        )
        actions.append(f"reasoning:{trace.id}")
        
        # 2. Create and execute plan based on reasoning
        if trace.action and trace.action != "No action":
            plan = planner.create_plan_from_goal(
                trace.action,
                GoalType.TRADING,
                context={
                    "market": context.market_state,
                    "safety": context.safety_state
                }
            )
            actions.append(f"plan:{plan.id}")
            
            # Execute step by step
            result = planner.execute_step_by_step(plan)
            if result.get("steps"):
                actions.append(f"executed:{result['steps'][0]['step_name']}")
        
        # 3. Ingest any new knowledge
        # (Would be triggered by completed trades/backtests)
        
        # 4. Store episodic memory
        memory.store_episodic(
            event_type="meso_loop",
            content={
                "reasoning": trace.action,
                "confidence": trace.confidence,
                "actions": actions
            },
            tags=["meso", "cycle"]
        )
        
        return LoopResult(
            loop_level=LoopLevel.MESO,
            iteration=context.iteration,
            success=True,
            actions_taken=actions,
            reasoning_trace_id=trace.id,
            duration_ms=(time.time() - start) * 1000
        )
        
    except Exception as e:
        return LoopResult(
            loop_level=LoopLevel.MESO,
            iteration=context.iteration,
            success=False,
            actions_taken=actions,
            error=str(e),
            duration_ms=(time.time() - start) * 1000
        )


def default_macro_loop(context: LoopContext, components: Dict[str, Any]) -> LoopResult:
    """
    Macro loop (hours): Strategy evolution → Learning → Improvement
    Used for: WFO validation, champion promotion, model retraining, knowledge consolidation
    """
    start = time.time()
    actions = []
    
    try:
        executor: AutonomousExecutor = components["executor"]
        planner: AutonomousPlanner = components["planner"]
        reasoner: AutonomousReasoner = components["reasoner"]
        memory: AutonomousMemory = components["memory"]
        scheduler: AutonomousScheduler = components["scheduler"]
        
        # 1. Run self-improvement cycle
        plan = planner.create_plan_from_template("self_improvement")
        actions.append(f"plan:{plan.id}")
        
        result = planner.execute_plan(plan)
        completed = len([s for s in plan.steps if s.status == TaskStatus.COMPLETED])
        actions.append(f"improvement_completed:{completed}/{len(plan.steps)}")
        
        # 2. Knowledge consolidation
        plan2 = planner.create_plan_from_template("knowledge_ingestion")
        result2 = planner.execute_plan(plan2)
        completed2 = len([s for s in plan2.steps if s.status == TaskStatus.COMPLETED])
        actions.append(f"knowledge_ingested:{completed2}/{len(plan2.steps)}")
        
        # 3. Health check
        plan3 = planner.create_plan_from_template("health_check")
        result3 = planner.execute_plan(plan3)
        actions.append("health_check_done")
        
        # 4. Promote insights to semantic memory
        # Extract patterns from recent episodes
        recent = memory.query_episodic(limit=100, tags=["trade", "backtest"])
        for ep in recent:
            if ep.content.get("insight"):
                memory.store_semantic(
                    key=f"insight_{ep.id}",
                    value=ep.content["insight"],
                    category="learned_pattern",
                    confidence=ep.content.get("confidence", 0.7),
                    source="macro_loop"
                )
        actions.append("insights_consolidated")
        
        # 5. Schedule next macro loop
        scheduler.schedule_task(
            name="macro_loop",
            func=lambda: None,  # Handled by main loop
            schedule_type=ScheduleType.INTERVAL,
            interval_hours=4
        )
        
        return LoopResult(
            loop_level=LoopLevel.MACRO,
            iteration=context.iteration,
            success=True,
            actions_taken=actions,
            duration_ms=(time.time() - start) * 1000
        )
        
    except Exception as e:
        return LoopResult(
            loop_level=LoopLevel.MACRO,
            iteration=context.iteration,
            success=False,
            actions_taken=actions,
            error=str(e),
            duration_ms=(time.time() - start) * 1000
        )


# ─── Main Autonomous Loops Class ────────────────────────────────────────────────

class AutonomousLoops:
    """
    Main orchestration class for the autonomous agent.
    Runs micro/meso/macro loops with shared components.
    """
    
    def __init__(
        self,
        openrouter_api_key: str = None,
        model: str = "nvidia/nemotron-3-ultra-550b-a55b:free",
        micro_interval: float = 5.0,
        meso_interval: float = 120.0,
        macro_interval: float = 14400.0  # 4 hours
    ):
        # Core components
        self.memory = AutonomousMemory()
        self.scheduler = AutonomousScheduler()
        self.planner = AutonomousPlanner(tool_executor=self._tool_executor)
        self.reasoner = AutonomousReasoner(
            llm_client=create_openrouter_client(openrouter_api_key, model) if openrouter_api_key else None
        )
        self.executor = AutonomousExecutor(max_workers=4)
        
        # Loop configuration
        self.micro_interval = micro_interval
        self.meso_interval = meso_interval
        self.macro_interval = macro_interval
        
        # State
        self.state = AgentState.INITIALIZING
        self._running = False
        self._loop_threads: Dict[LoopLevel, Any] = {}
        self._iteration_counts = {level: 0 for level in LoopLevel}
        self._loop_handlers = {
            LoopLevel.MICRO: default_micro_loop,
            LoopLevel.MESO: default_meso_loop,
            LoopLevel.MACRO: default_macro_loop
        }
        self._custom_handlers: Dict[LoopLevel, Callable] = {}
        
        # Context
        self._context = LoopContext(
            loop_level=LoopLevel.MICRO,
            iteration=0,
            timestamp=time.time()
        )
        
        # History
        self._loop_history: List[LoopResult] = []
        self._max_history = 10000
        
        # Component registry for tool executor
        self._components = {
            "memory": self.memory,
            "scheduler": self.scheduler,
            "planner": self.planner,
            "reasoner": self.reasoner,
            "executor": self.executor,
            "loops": self
        }
        
        # Register actual tools from the system
        self._register_system_tools()
        
        # Lock
        self._lock = __import__('threading').RLock()
    
    def _register_system_tools(self):
        """Register actual system tools (MT5, backtest, etc.) with executor."""
        # These would be imported from the actual ARE modules
        # For now, keeping stubs - real integration happens in engine.py
        pass
    
    def _tool_executor(self, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool executor for planner - delegates to executor."""
        result = self.executor.execute(tool, args)
        return {
            "success": result.status == ExecutionStatus.COMPLETED,
            "result": result.result,
            "error": result.error
        }
    
    # ─── Loop Control ──────────────────────────────────────────────────────────
    
    def start(self) -> None:
        """Start all loops."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self.state = AgentState.RUNNING
        
        # Schedule loops
        self.scheduler.schedule_task(
            name="micro_loop",
            func=self._run_micro_loop,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=self.micro_interval,
            priority=1
        )
        
        self.scheduler.schedule_task(
            name="meso_loop",
            func=self._run_meso_loop,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=self.meso_interval,
            priority=5
        )
        
        self.scheduler.schedule_task(
            name="macro_loop",
            func=self._run_macro_loop,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=self.macro_interval,
            priority=10
        )
        
        self.scheduler.start()
    
    def stop(self) -> None:
        """Stop all loops."""
        with self._lock:
            self._running = False
            self.state = AgentState.STOPPING
        
        self.scheduler.stop()
        self.executor.shutdown(wait=True)
        self.state = AgentState.STOPPED
    
    def pause(self) -> None:
        """Pause loops (keep scheduler running but skip executions)."""
        with self._lock:
            self.state = AgentState.PAUSED
    
    def resume(self) -> None:
        """Resume loops."""
        with self._lock:
            if self.state == AgentState.PAUSED:
                self.state = AgentState.RUNNING
    
    # ─── Loop Runners ──────────────────────────────────────────────────────────
    
    def _run_micro_loop(self) -> None:
        if self.state != AgentState.RUNNING:
            return
        
        self._iteration_counts[LoopLevel.MICRO] += 1
        context = LoopContext(
            loop_level=LoopLevel.MICRO,
            iteration=self._iteration_counts[LoopLevel.MICRO],
            timestamp=time.time(),
            market_state=self._context.market_state,
            agent_state=self._get_agent_state(),
            safety_state=self._context.safety_state
        )
        
        handler = self._custom_handlers.get(LoopLevel.MICRO) or self._loop_handlers[LoopLevel.MICRO]
        result = handler(context, self._components)
        
        self._record_result(result)
        self._context = context  # Update shared context
    
    def _run_meso_loop(self) -> None:
        if self.state != AgentState.RUNNING:
            return
        
        self._iteration_counts[LoopLevel.MESO] += 1
        context = LoopContext(
            loop_level=LoopLevel.MESO,
            iteration=self._iteration_counts[LoopLevel.MESO],
            timestamp=time.time(),
            market_state=self._context.market_state,
            agent_state=self._get_agent_state(),
            safety_state=self._context.safety_state
        )
        
        handler = self._custom_handlers.get(LoopLevel.MESO) or self._loop_handlers[LoopLevel.MESO]
        result = handler(context, self._components)
        
        self._record_result(result)
        self._context = context
    
    def _run_macro_loop(self) -> None:
        if self.state != AgentState.RUNNING:
            return
        
        self._iteration_counts[LoopLevel.MACRO] += 1
        context = LoopContext(
            loop_level=LoopLevel.MACRO,
            iteration=self._iteration_counts[LoopLevel.MACRO],
            timestamp=time.time(),
            market_state=self._context.market_state,
            agent_state=self._get_agent_state(),
            safety_state=self._context.safety_state
        )
        
        handler = self._custom_handlers.get(LoopLevel.MACRO) or self._loop_handlers[LoopLevel.MACRO]
        result = handler(context, self._components)
        
        self._record_result(result)
        self._context = context
    
    def _get_agent_state(self) -> Dict[str, Any]:
        """Get current agent state snapshot."""
        return {
            "state": self.state.value,
            "iterations": dict(self._iteration_counts),
            "memory_stats": self.memory.get_stats(),
            "scheduler_stats": self.scheduler.get_stats(),
            "executor_stats": {
                "running": len(self.executor.get_running()),
                "completed": len(self.executor._completed)
            }
        }
    
    def _record_result(self, result: LoopResult) -> None:
        """Record loop result to history."""
        with self._lock:
            self._loop_history.append(result)
            if len(self._loop_history) > self._max_history:
                self._loop_history = self._loop_history[-self._max_history:]
    
    # ─── Customization ─────────────────────────────────────────────────────────
    
    def set_loop_handler(self, level: LoopLevel, handler: Callable[[LoopContext, Dict], LoopResult]) -> None:
        """Set custom handler for a loop level."""
        self._custom_handlers[level] = handler
    
    def register_tool(self, tool: ToolSpec) -> None:
        """Register a tool with the executor."""
        self.executor.register_tool(tool)
    
    # ─── Status & Monitoring ───────────────────────────────────────────────────
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status."""
        return {
            "state": self.state.value,
            "running": self._running,
            "iterations": dict(self._iteration_counts),
            "intervals": {
                "micro": self.micro_interval,
                "meso": self.meso_interval,
                "macro": self.macro_interval
            },
            "memory": self.memory.get_stats(),
            "scheduler": self.scheduler.get_stats(),
            "executor": {
                "running": len(self.executor.get_running()),
                "completed": len(self.executor._completed),
                "tools": len(self.executor.list_tools())
            },
            "reasoner": {
                "traces": len(self.reasoner._traces)
            },
            "planner": {
                "plans": len(self.planner._plans)
            },
            "recent_loops": [
                {
                    "level": r.loop_level.value,
                    "iteration": r.iteration,
                    "success": r.success,
                    "actions": r.actions_taken,
                    "duration_ms": r.duration_ms,
                    "error": r.error
                }
                for r in self._loop_history[-20:]
            ]
        }
    
    def get_loop_history(self, level: LoopLevel = None, limit: int = 100) -> List[LoopResult]:
        """Get loop execution history."""
        history = self._loop_history
        if level:
            history = [r for r in history if r.loop_level == level]
        return history[-limit:]
    
    # ─── Manual Triggers ───────────────────────────────────────────────────────
    
    def trigger_micro(self) -> LoopResult:
        """Manually trigger a micro loop iteration."""
        self._iteration_counts[LoopLevel.MICRO] += 1
        context = LoopContext(
            loop_level=LoopLevel.MICRO,
            iteration=self._iteration_counts[LoopLevel.MICRO],
            timestamp=time.time(),
            market_state=self._context.market_state,
            agent_state=self._get_agent_state(),
            safety_state=self._context.safety_state
        )
        handler = self._custom_handlers.get(LoopLevel.MICRO) or self._loop_handlers[LoopLevel.MICRO]
        result = handler(context, self._components)
        self._record_result(result)
        self._context = context
        return result
    
    def trigger_meso(self) -> LoopResult:
        """Manually trigger a meso loop iteration."""
        self._iteration_counts[LoopLevel.MESO] += 1
        context = LoopContext(
            loop_level=LoopLevel.MESO,
            iteration=self._iteration_counts[LoopLevel.MESO],
            timestamp=time.time(),
            market_state=self._context.market_state,
            agent_state=self._get_agent_state(),
            safety_state=self._context.safety_state
        )
        handler = self._custom_handlers.get(LoopLevel.MESO) or self._loop_handlers[LoopLevel.MESO]
        result = handler(context, self._components)
        self._record_result(result)
        self._context = context
        return result
    
    def trigger_macro(self) -> LoopResult:
        """Manually trigger a macro loop iteration."""
        self._iteration_counts[LoopLevel.MACRO] += 1
        context = LoopContext(
            loop_level=LoopLevel.MACRO,
            iteration=self._iteration_counts[LoopLevel.MACRO],
            timestamp=time.time(),
            market_state=self._context.market_state,
            agent_state=self._get_agent_state(),
            safety_state=self._context.safety_state
        )
        handler = self._custom_handlers.get(LoopLevel.MACRO) or self._loop_handlers[LoopLevel.MACRO]
        result = handler(context, self._components)
        self._record_result(result)
        self._context = context
        return result
    
    # ─── Persistence ───────────────────────────────────────────────────────────
    
    def save_state(self, path: str = None) -> str:
        """Save agent state to disk."""
        path = path or str(LOOPS_DIR / f"agent_state_{int(time.time())}.json")
        state = {
            "state": self.state.value,
            "iterations": dict(self._iteration_counts),
            "intervals": {
                "micro": self.micro_interval,
                "meso": self.meso_interval,
                "macro": self.macro_interval
            },
            "context": {
                "market_state": self._context.market_state,
                "agent_state": self._context.agent_state,
                "safety_state": self._context.safety_state
            },
            "loop_history": [r.__dict__ for r in self._loop_history[-100:]]
        }
        with open(path, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        return path
    
    def load_state(self, path: str) -> None:
        """Load agent state from disk."""
        with open(path, 'r') as f:
            state = json.load(f)
        
        self.state = AgentState(state.get("state", "stopped"))
        self._iteration_counts = state.get("iterations", {level: 0 for level in LoopLevel})
        self.micro_interval = state.get("intervals", {}).get("micro", 5.0)
        self.meso_interval = state.get("intervals", {}).get("meso", 120.0)
        self.macro_interval = state.get("intervals", {}).get("macro", 14400.0)
        self._context.market_state = state.get("context", {}).get("market_state", {})
        self._context.agent_state = state.get("context", {}).get("agent_state", {})
        self._context.safety_state = state.get("context", {}).get("safety_state", {})


# ─── Factory Function ──────────────────────────────────────────────────────────

def create_autonomous_agent(
    openrouter_api_key: str = None,
    model: str = "nvidia/nemotron-3-ultra-550b-a55b:free",
    config: Dict[str, Any] = None
) -> AutonomousLoops:
    """
    Factory to create a fully configured autonomous agent.
    
    Args:
        openrouter_api_key: OpenRouter API key for Nemotron 3 Ultra
        model: Model to use (default: Nemotron 3 Ultra)
        config: Optional config dict with intervals, etc.
    
    Returns:
        Configured AutonomousLoops instance ready to start()
    """
    config = config or {}
    
    agent = AutonomousLoops(
        openrouter_api_key=openrouter_api_key,
        model=model,
        micro_interval=config.get("micro_interval", 5.0),
        meso_interval=config.get("meso_interval", 120.0),
        macro_interval=config.get("macro_interval", 14400.0)
    )
    
    # Register any custom tools from config
    for tool_def in config.get("tools", []):
        tool = ToolSpec(**tool_def)
        agent.register_tool(tool)
    
    # Set custom loop handlers if provided
    for level_name, handler in config.get("handlers", {}).items():
        try:
            level = LoopLevel(level_name)
            agent.set_loop_handler(level, handler)
        except ValueError:
            pass
    
    return agent


# ─── Module Exports ──────────────────────────────────────────────────────────────

__all__ = [
    'LoopLevel',
    'AgentState',
    'LoopContext',
    'LoopResult',
    'AutonomousLoops',
    'create_autonomous_agent',
    'default_micro_loop',
    'default_meso_loop',
    'default_macro_loop',
]