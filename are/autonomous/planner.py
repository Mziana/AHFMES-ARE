"""
Autonomous Planner — Goal decomposition, task graph, execution planning
Converts high-level goals into executable task sequences with dependencies.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable
from enum import Enum
from collections import defaultdict


# ─── Configuration ──────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "autonomous"
PLANS_DIR = DATA_DIR / "plans"
PLANS_DIR.mkdir(parents=True, exist_ok=True)


# ─── Types & Enums ──────────────────────────────────────────────────────────────

class TaskStatus(Enum):
    PENDING = "pending"
    READY = "ready"           # Dependencies satisfied, ready to execute
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"       # Waiting for external condition


class GoalType(Enum):
    TRADING = "trading"               # Execute trades, manage positions
    RESEARCH = "research"             # Run backtests, analyze patterns
    LEARNING = "learning"             # Ingest knowledge, update models
    MAINTENANCE = "maintenance"       # Cleanup, diagnostics, health checks
    IMPROVEMENT = "improvement"       # Self-improvement, WFO, champion promotion
    SAFETY = "safety"                 # Risk checks, kill switch, CSK validation


@dataclass
class PlanStep:
    """A single step in a plan."""
    id: str
    name: str
    description: str
    tool: str                    # Tool/function to execute
    args: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Step IDs that must complete first
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5            # 1=highest
    estimated_duration: float = 30.0  # seconds
    timeout: float = 60.0
    retry_count: int = 0
    max_retries: int = 2
    result: Any = None
    error: str = ""
    started_at: float = 0
    completed_at: float = 0
    
    # Conditional execution
    condition: str = ""          # Python expression evaluated at runtime
    condition_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    """A complete execution plan for a goal."""
    id: str
    goal: str
    goal_type: GoalType
    steps: List[PlanStep] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    started_at: float = 0
    completed_at: float = 0
    status: TaskStatus = TaskStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Execution tracking
    current_step: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "goal_type": self.goal_type.value,
            "steps": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "tool": s.tool,
                    "args": s.args,
                    "dependencies": s.dependencies,
                    "status": s.status.value,
                    "priority": s.priority,
                    "estimated_duration": s.estimated_duration,
                    "timeout": s.timeout,
                    "retry_count": s.retry_count,
                    "max_retries": s.max_retries,
                    "result": s.result,
                    "error": s.error,
                    "started_at": s.started_at,
                    "completed_at": s.completed_at,
                    "condition": s.condition,
                    "condition_context": s.condition_context
                }
                for s in self.steps
            ],
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status.value,
            "metadata": self.metadata,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Plan':
        plan = cls(
            id=data["id"],
            goal=data["goal"],
            goal_type=GoalType(data["goal_type"]),
            created_at=data.get("created_at", time.time()),
            started_at=data.get("started_at", 0),
            completed_at=data.get("completed_at", 0),
            status=TaskStatus(data.get("status", "pending")),
            metadata=data.get("metadata", {}),
            current_step=data.get("current_step", 0),
            completed_steps=data.get("completed_steps", 0),
            failed_steps=data.get("failed_steps", 0)
        )
        plan.steps = []
        for s_data in data.get("steps", []):
            step = PlanStep(
                id=s_data["id"],
                name=s_data["name"],
                description=s_data["description"],
                tool=s_data["tool"],
                args=s_data.get("args", {}),
                dependencies=s_data.get("dependencies", []),
                status=TaskStatus(s_data.get("status", "pending")),
                priority=s_data.get("priority", 5),
                estimated_duration=s_data.get("estimated_duration", 30.0),
                timeout=s_data.get("timeout", 60.0),
                retry_count=s_data.get("retry_count", 0),
                max_retries=s_data.get("max_retries", 2),
                result=s_data.get("result"),
                error=s_data.get("error", ""),
                started_at=s_data.get("started_at", 0),
                completed_at=s_data.get("completed_at", 0),
                condition=s_data.get("condition", ""),
                condition_context=s_data.get("condition_context", {})
            )
            plan.steps.append(step)
        return plan


# ─── Goal Templates (Predefined plan patterns) ──────────────────────────────────

GOAL_TEMPLATES: Dict[str, Dict] = {
    "scan_opportunities": {
        "goal": "Scan market for trading opportunities",
        "goal_type": GoalType.TRADING,
        "steps": [
            {
                "name": "get_market_state",
                "description": "Get current market state (price, spread, session)",
                "tool": "get_mt5_live_data",
                "args": {"symbol": "XAUUSD"},
                "dependencies": [],
                "priority": 1
            },
            {
                "name": "check_safety",
                "description": "Verify CSK safety limits allow trading",
                "tool": "get_safety_limits",
                "args": {},
                "dependencies": [],
                "priority": 1
            },
            {
                "name": "check_news_impact",
                "description": "Check for high-impact news events",
                "tool": "check_trade_safety",
                "args": {},
                "dependencies": [],
                "priority": 2
            },
            {
                "name": "analyze_opportunity",
                "description": "Run opportunity engine scoring",
                "tool": "run_autonomous_cycle",
                "args": {"symbol": "XAUUSD"},
                "dependencies": ["get_market_state", "check_safety", "check_news_impact"],
                "priority": 1
            },
            {
                "name": "get_direction",
                "description": "Discover directional bias for current habitat",
                "tool": "get_are_status",
                "args": {},
                "dependencies": ["analyze_opportunity"],
                "priority": 2
            }
        ]
    },
    
    "execute_trade": {
        "goal": "Execute a trade based on analysis",
        "goal_type": GoalType.TRADING,
        "steps": [
            {
                "name": "verify_setup",
                "description": "Verify trade setup is valid",
                "tool": "get_mt5_live_data",
                "args": {"symbol": "XAUUSD"},
                "dependencies": [],
                "priority": 1
            },
            {
                "name": "calculate_position",
                "description": "Calculate position size from risk parameters",
                "tool": "calculate_position_size",
                "args": {"risk_percent": 2, "sl_points": 400, "tp_points": 600},
                "dependencies": ["verify_setup"],
                "priority": 1
            },
            {
                "name": "check_kill_switch",
                "description": "Ensure kill switch is not active",
                "tool": "get_safety_limits",
                "args": {},
                "dependencies": ["calculate_position"],
                "priority": 1
            },
            {
                "name": "execute_order",
                "description": "Execute the trade order",
                "tool": "execute_trade",
                "args": {"symbol": "XAUUSD", "direction": "BUY", "lot": 0.01, "sl_points": 400, "tp_points": 600},
                "dependencies": ["check_kill_switch"],
                "priority": 1,
                "condition": "context.get('position_calculated', False)"
            }
        ]
    },
    
    "run_backtest": {
        "goal": "Run backtest for strategy validation",
        "goal_type": GoalType.RESEARCH,
        "steps": [
            {
                "name": "list_strategies",
                "description": "List available strategies",
                "tool": "list_strategies",
                "args": {"status": "active"},
                "dependencies": [],
                "priority": 1
            },
            {
                "name": "run_backtest",
                "description": "Execute backtest on selected strategy",
                "tool": "run_backtest",
                "args": {"symbol": "XAUUSD", "timeframe": 60, "capital": 10000},
                "dependencies": ["list_strategies"],
                "priority": 1,
                "estimated_duration": 120
            },
            {
                "name": "analyze_results",
                "description": "Analyze backtest results for strengths/weaknesses",
                "tool": "analyze_results",
                "args": {"strategy_id": "s-1"},
                "dependencies": ["run_backtest"],
                "priority": 1
            },
            {
                "name": "save_knowledge",
                "description": "Save backtest insights to knowledge base",
                "tool": "save_knowledge",
                "args": {"category": "backtest", "title": "Backtest Results", "content": "Auto-saved from planner"},
                "dependencies": ["analyze_results"],
                "priority": 2
            }
        ]
    },
    
    "self_improvement": {
        "goal": "Run self-improvement cycle: WFO validation, champion promotion",
        "goal_type": GoalType.IMPROVEMENT,
        "steps": [
            {
                "name": "run_diagnostics",
                "description": "Run system diagnostics first",
                "tool": "run_diagnostics",
                "args": {},
                "dependencies": [],
                "priority": 1
            },
            {
                "name": "run_wfo",
                "description": "Run Walk-Forward Optimization validation",
                "tool": "run_wfo",
                "args": {"symbol": "XAUUSD", "timeframe": "M5", "windows": 6},
                "dependencies": ["run_diagnostics"],
                "priority": 1,
                "estimated_duration": 300
            },
            {
                "name": "get_champion_info",
                "description": "Get current champion status",
                "tool": "get_champion_info",
                "args": {},
                "dependencies": ["run_wfo"],
                "priority": 2
            },
            {
                "name": "promote_if_valid",
                "description": "Promote candidate if WFO passes",
                "tool": "promote_champion",
                "args": {},
                "dependencies": ["get_champion_info"],
                "priority": 1,
                "condition": "context.get('wfo_passed', False)"
            },
            {
                "name": "ingest_knowledge",
                "description": "Ingest new trades/backtests into knowledge base",
                "tool": "ingest_knowledge",
                "args": {},
                "dependencies": ["promote_if_valid"],
                "priority": 3
            }
        ]
    },
    
    "knowledge_ingestion": {
        "goal": "Ingest latest trades and backtests into knowledge base",
        "goal_type": GoalType.LEARNING,
        "steps": [
            {
                "name": "ingest_trades",
                "description": "Ingest recent trade history",
                "tool": "ingest_trades",
                "args": {"limit": 100},
                "dependencies": [],
                "priority": 1
            },
            {
                "name": "ingest_backtests",
                "description": "Ingest recent backtest results",
                "tool": "ingest_backtests",
                "args": {"limit": 50},
                "dependencies": [],
                "priority": 1
            },
            {
                "name": "backfill_embeddings",
                "description": "Generate embeddings for entries without vectors",
                "tool": "backfill_embeddings",
                "args": {"limit": 100},
                "dependencies": ["ingest_trades", "ingest_backtests"],
                "priority": 2,
                "estimated_duration": 120
            },
            {
                "name": "verify_stats",
                "description": "Verify knowledge base stats",
                "tool": "knowledge_stats",
                "args": {},
                "dependencies": ["backfill_embeddings"],
                "priority": 2
            }
        ]
    },
    
    "health_check": {
        "goal": "Comprehensive system health check",
        "goal_type": GoalType.MAINTENANCE,
        "steps": [
            {
                "name": "get_status",
                "description": "Get ARE engine status",
                "tool": "get_are_status",
                "args": {},
                "dependencies": [],
                "priority": 1
            },
            {
                "name": "run_diagnostics",
                "description": "Run full diagnostics",
                "tool": "run_diagnostics",
                "args": {},
                "dependencies": ["get_status"],
                "priority": 1
            },
            {
                "name": "check_mt5",
                "description": "Verify MT5 connection",
                "tool": "get_mt5_live_data",
                "args": {"symbol": "XAUUSD"},
                "dependencies": ["get_status"],
                "priority": 1
            },
            {
                "name": "check_safety",
                "description": "Verify safety kernel status",
                "tool": "get_safety_limits",
                "args": {},
                "dependencies": ["get_status"],
                "priority": 1
            },
            {
                "name": "get_evidence",
                "description": "Check evidence ledger integrity",
                "tool": "get_evidence",
                "args": {"limit": 10},
                "dependencies": ["run_diagnostics"],
                "priority": 2
            }
        ]
    }
}


# ─── Planner Core ────────────────────────────────────────────────────────────────

class AutonomousPlanner:
    """
    Decomposes high-level goals into executable task graphs.
    Handles dependency resolution, conditional execution, and dynamic replanning.
    """
    
    def __init__(self, tool_executor: Callable[[str, Dict], Any] = None):
        self.tool_executor = tool_executor
        self._plans: Dict[str, Plan] = {}
        self._active_plan: Optional[Plan] = None
        self._execution_context: Dict[str, Any] = {}
        self._lock = __import__('threading').RLock()
    
    # ─── Plan Creation ─────────────────────────────────────────────────────────
    
    def create_plan_from_template(
        self, 
        template_name: str, 
        overrides: Dict[str, Any] = None
    ) -> Plan:
        """Create a plan from a predefined template."""
        if template_name not in GOAL_TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = GOAL_TEMPLATES[template_name]
        overrides = overrides or {}
        
        plan = Plan(
            id=str(uuid.uuid4())[:8],
            goal=template["goal"],
            goal_type=template["goal_type"],
            metadata={"template": template_name, "overrides": overrides}
        )
        
        for step_data in template["steps"]:
            # Apply overrides to args
            args = dict(step_data.get("args", {}))
            if "args" in overrides and step_data["name"] in overrides["args"]:
                args.update(overrides["args"][step_data["name"]])
            
            step = PlanStep(
                id=str(uuid.uuid4())[:8],
                name=step_data["name"],
                description=step_data["description"],
                tool=step_data["tool"],
                args=args,
                dependencies=step_data.get("dependencies", []),
                priority=step_data.get("priority", 5),
                estimated_duration=step_data.get("estimated_duration", 30.0),
                timeout=step_data.get("timeout", 60.0),
                condition=step_data.get("condition", ""),
                condition_context=step_data.get("condition_context", {})
            )
            plan.steps.append(step)
        
        self._plans[plan.id] = plan
        return plan
    
    def create_custom_plan(
        self,
        goal: str,
        goal_type: GoalType,
        steps: List[Dict[str, Any]]
    ) -> Plan:
        """Create a custom plan from step definitions."""
        plan = Plan(
            id=str(uuid.uuid4())[:8],
            goal=goal,
            goal_type=goal_type
        )
        
        for step_data in steps:
            step = PlanStep(
                id=str(uuid.uuid4())[:8],
                name=step_data["name"],
                description=step_data.get("description", ""),
                tool=step_data["tool"],
                args=step_data.get("args", {}),
                dependencies=step_data.get("dependencies", []),
                priority=step_data.get("priority", 5),
                estimated_duration=step_data.get("estimated_duration", 30.0),
                timeout=step_data.get("timeout", 60.0),
                condition=step_data.get("condition", ""),
                condition_context=step_data.get("condition_context", {})
            )
            plan.steps.append(step)
        
        self._plans[plan.id] = plan
        return plan
    
    def create_plan_from_goal(
        self, 
        goal: str, 
        goal_type: GoalType,
        context: Dict[str, Any] = None
    ) -> Plan:
        """
        LLM-assisted plan generation (placeholder for future).
        For now, maps goal keywords to templates.
        """
        context = context or {}
        self._execution_context = context
        
        # Simple keyword matching to templates
        goal_lower = goal.lower()
        
        if any(kw in goal_lower for kw in ["scan", "opportunit", "market", "analyze"]):
            return self.create_plan_from_template("scan_opportunities", 
                {"args": {"get_market_state": {"symbol": context.get("symbol", "XAUUSD")}}})
        
        if any(kw in goal_lower for kw in ["trade", "buy", "sell", "execute", "order"]):
            direction = "BUY" if "buy" in goal_lower or "long" in goal_lower else "SELL"
            return self.create_plan_from_template("execute_trade",
                {"args": {"execute_order": {"direction": direction}}})
        
        if any(kw in goal_lower for kw in ["backtest", "validate", "test strateg"]):
            return self.create_plan_from_template("run_backtest")
        
        if any(kw in goal_lower for kw in ["improve", "wfo", "champion", "promote", "self-improv"]):
            return self.create_plan_from_template("self_improvement")
        
        if any(kw in goal_lower for kw in ["ingest", "knowledge", "learn", "memory"]):
            return self.create_plan_from_template("knowledge_ingestion")
        
        if any(kw in goal_lower for kw in ["health", "diagnostic", "check", "status"]):
            return self.create_plan_from_template("health_check")
        
        # Default: health check
        return self.create_plan_from_template("health_check")
    
    # ─── Dependency Resolution ─────────────────────────────────────────────────
    
    def get_ready_steps(self, plan: Plan) -> List[PlanStep]:
        """Get steps that are ready to execute (dependencies satisfied)."""
        ready = []
        completed_ids = {s.id for s in plan.steps if s.status == TaskStatus.COMPLETED}
        
        for step in plan.steps:
            if step.status != TaskStatus.PENDING:
                continue
            
            # Check dependencies
            deps_satisfied = all(dep in completed_ids for dep in step.dependencies)
            if not deps_satisfied:
                continue
            
            # Check condition
            if step.condition:
                try:
                    # Evaluate condition in context
                    cond_context = {**self._execution_context, **step.condition_context}
                    if not eval(step.condition, {"context": cond_context}):
                        step.status = TaskStatus.SKIPPED
                        continue
                except Exception:
                    step.status = TaskStatus.BLOCKED
                    step.error = f"Condition eval failed: {step.condition}"
                    continue
            
            step.status = TaskStatus.READY
            ready.append(step)
        
        # Sort by priority
        ready.sort(key=lambda s: s.priority)
        return ready
    
    def get_next_step(self, plan: Plan) -> Optional[PlanStep]:
        """Get the next step to execute."""
        ready = self.get_ready_steps(plan)
        return ready[0] if ready else None
    
    # ─── Plan Execution ────────────────────────────────────────────────────────
    
    def execute_plan(self, plan: Plan, step_by_step: bool = False) -> Dict[str, Any]:
        """Execute a plan (or single step if step_by_step)."""
        if not self.tool_executor:
            return {"success": False, "error": "No tool executor configured"}
        
        with self._lock:
            if plan.status == TaskStatus.PENDING:
                plan.status = TaskStatus.RUNNING
                plan.started_at = time.time()
            self._active_plan = plan
        
        results = {"plan_id": plan.id, "steps": []}
        
        while True:
            # Check if plan is complete
            pending = [s for s in plan.steps if s.status in (TaskStatus.PENDING, TaskStatus.READY, TaskStatus.RUNNING)]
            if not pending:
                plan.status = TaskStatus.COMPLETED
                plan.completed_at = time.time()
                break
            
            # Check for failed steps that block the plan
            failed = [s for s in plan.steps if s.status == TaskStatus.FAILED]
            if failed and not any(s.status == TaskStatus.RUNNING for s in plan.steps):
                plan.status = TaskStatus.FAILED
                plan.completed_at = time.time()
                break
            
            if step_by_step:
                # Execute just one step
                step = self.get_next_step(plan)
                if not step:
                    # No ready steps - might be waiting for running step
                    running = [s for s in plan.steps if s.status == TaskStatus.RUNNING]
                    if not running:
                        # Stuck - check for blocked
                        blocked = [s for s in plan.steps if s.status == TaskStatus.BLOCKED]
                        if blocked:
                            plan.status = TaskStatus.FAILED
                            plan.completed_at = time.time()
                    break
                
                result = self._execute_step(step, plan)
                results["steps"].append(result)
                break
            else:
                # Execute all ready steps (parallel-ish)
                ready = self.get_ready_steps(plan)
                if not ready:
                    # Check for running steps
                    running = [s for s in plan.steps if s.status == TaskStatus.RUNNING]
                    if not running:
                        # Stuck
                        blocked = [s for s in plan.steps if s.status == TaskStatus.BLOCKED]
                        if blocked:
                            plan.status = TaskStatus.FAILED
                        break
                    time.sleep(0.5)
                    continue
                
                # Execute ready steps sequentially for now
                for step in ready:
                    result = self._execute_step(step, plan)
                    results["steps"].append(result)
        
        return results
    
    def _execute_step(self, step: PlanStep, plan: Plan) -> Dict[str, Any]:
        """Execute a single step."""
        step.status = TaskStatus.RUNNING
        step.started_at = time.time()
        
        result = {
            "step_id": step.id,
            "step_name": step.name,
            "tool": step.tool,
            "success": False,
            "result": None,
            "error": "",
            "duration_ms": 0
        }
        
        try:
            # Execute tool
            tool_result = self.tool_executor(step.tool, step.args)
            
            step.result = tool_result
            step.status = TaskStatus.COMPLETED if tool_result.get("success", True) else TaskStatus.FAILED
            step.error = tool_result.get("error", "")
            
            result["success"] = step.status == TaskStatus.COMPLETED
            result["result"] = tool_result
            result["error"] = step.error
            
            # Update execution context with result
            self._execution_context[f"step_{step.name}"] = tool_result
            self._execution_context[f"step_{step.name}_success"] = result["success"]
            
        except Exception as e:
            step.status = TaskStatus.FAILED
            step.error = str(e)
            result["error"] = str(e)
            
            # Retry logic
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                step.status = TaskStatus.PENDING
                time.sleep(1 * step.retry_count)  # Backoff
        
        finally:
            step.completed_at = time.time()
            result["duration_ms"] = (step.completed_at - step.started_at) * 1000
            
            if step.status == TaskStatus.COMPLETED:
                plan.completed_steps += 1
            elif step.status == TaskStatus.FAILED:
                plan.failed_steps += 1
        
        return result
    
    def execute_step_by_step(self, plan: Plan) -> Dict[str, Any]:
        """Execute one step and return control to caller."""
        return self.execute_plan(plan, step_by_step=True)
    
    # ─── Plan Management ───────────────────────────────────────────────────────
    
    def get_plan(self, plan_id: str) -> Optional[Plan]:
        return self._plans.get(plan_id)
    
    def get_active_plan(self) -> Optional[Plan]:
        return self._active_plan
    
    def list_plans(self) -> List[Plan]:
        return list(self._plans.values())
    
    def save_plan(self, plan: Plan, path: str = None) -> str:
        """Save plan to disk."""
        path = path or str(PLANS_DIR / f"plan_{plan.id}.json")
        with open(path, 'w') as f:
            json.dump(plan.to_dict(), f, indent=2)
        return path
    
    def load_plan(self, path: str) -> Plan:
        """Load plan from disk."""
        with open(path, 'r') as f:
            data = json.load(f)
        plan = Plan.from_dict(data)
        self._plans[plan.id] = plan
        return plan
    
    def list_templates(self) -> Dict[str, Dict]:
        """List available goal templates."""
        return {
            name: {
                "goal": t["goal"],
                "goal_type": t["goal_type"].value,
                "step_count": len(t["steps"]),
                "steps": [s["name"] for s in t["steps"]]
            }
            for name, t in GOAL_TEMPLATES.items()
        }
    
    def get_plan_progress(self, plan: Plan) -> Dict[str, Any]:
        """Get execution progress of a plan."""
        total = len(plan.steps)
        completed = len([s for s in plan.steps if s.status == TaskStatus.COMPLETED])
        failed = len([s for s in plan.steps if s.status == TaskStatus.FAILED])
        running = len([s for s in plan.steps if s.status == TaskStatus.RUNNING])
        pending = len([s for s in plan.steps if s.status in (TaskStatus.PENDING, TaskStatus.READY)])
        skipped = len([s for s in plan.steps if s.status == TaskStatus.SKIPPED])
        
        return {
            "plan_id": plan.id,
            "goal": plan.goal,
            "status": plan.status.value,
            "total_steps": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "skipped": skipped,
            "progress_pct": round(completed / max(1, total) * 100, 1),
            "current_step": plan.current_step,
            "estimated_remaining": sum(
                s.estimated_duration for s in plan.steps 
                if s.status in (TaskStatus.PENDING, TaskStatus.READY, TaskStatus.RUNNING)
            )
        }


# ─── Module Exports ──────────────────────────────────────────────────────────────

__all__ = [
    'TaskStatus',
    'GoalType',
    'PlanStep',
    'Plan',
    'GOAL_TEMPLATES',
    'AutonomousPlanner',
]