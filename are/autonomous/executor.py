"""
Autonomous Executor — Tool orchestration with retries, fallbacks, timeouts, parallel execution
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union
from enum import Enum
from collections import defaultdict


# ─── Configuration ──────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "autonomous"
EXECUTION_DIR = DATA_DIR / "executions"
EXECUTION_DIR.mkdir(parents=True, exist_ok=True)


# ─── Types & Enums ──────────────────────────────────────────────────────────────

class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    FALLBACK = "fallback"


class ToolCategory(Enum):
    TRADING = "trading"           # execute_trade, close_position, modify_position
    ANALYSIS = "analysis"         # run_backtest, analyze_results, scan_opportunities
    DATA = "data"                 # get_market_data, get_mt5_live_data, fetch_history
    KNOWLEDGE = "knowledge"       # search_knowledge, save_knowledge, ingest_*
    SAFETY = "safety"             # get_safety_limits, check_trade_safety, check_kill_switch
    SYSTEM = "system"             # get_are_status, run_diagnostics, promote_champion
    LEARNING = "learning"         # run_wfo, train_model, update_models


@dataclass
class ToolSpec:
    """Tool specification for the executor."""
    name: str
    category: ToolCategory
    function: Callable[[Dict[str, Any]], Dict[str, Any]]
    description: str = ""
    params_schema: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 60.0
    max_retries: int = 2
    retry_delay: float = 1.0
    fallback: Optional[str] = None  # Fallback tool name
    requires_confirmation: bool = False
    idempotent: bool = False
    parallel_safe: bool = True


@dataclass
class ExecutionRequest:
    """A single tool execution request."""
    id: str
    tool: str
    args: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5
    timeout: float = 0  # 0 = use tool default
    max_retries: int = 0  # 0 = use tool default
    depends_on: List[str] = field(default_factory=list)  # Other request IDs
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of a tool execution."""
    request_id: str
    tool: str
    status: ExecutionStatus
    result: Any = None
    error: str = ""
    duration_ms: float = 0
    retries: int = 0
    fallback_used: bool = False
    started_at: float = field(default_factory=time.time)
    completed_at: float = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "tool": self.tool,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "retries": self.retries,
            "fallback_used": self.fallback_used,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


@dataclass
class ExecutionPlan:
    """A plan of multiple tool executions with dependencies."""
    id: str
    requests: List[ExecutionRequest] = field(default_factory=list)
    status: ExecutionStatus = ExecutionStatus.PENDING
    results: Dict[str, ExecutionResult] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    started_at: float = 0
    completed_at: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "requests": [
                {
                    "id": r.id,
                    "tool": r.tool,
                    "args": r.args,
                    "context": r.context,
                    "priority": r.priority,
                    "timeout": r.timeout,
                    "max_retries": r.max_retries,
                    "depends_on": r.depends_on,
                    "metadata": r.metadata
                }
                for r in self.requests
            ],
            "status": self.status.value,
            "results": {k: v.to_dict() for k, v in self.results.items()},
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata
        }


# ─── Executor Core ──────────────────────────────────────────────────────────────

class AutonomousExecutor:
    """
    Tool orchestration engine with:
    - Dependency resolution (DAG execution)
    - Retry with exponential backoff
    - Fallback tool chains
    - Parallel execution with concurrency limits
    - Timeout enforcement
    - Execution tracing and replay
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        default_timeout: float = 60.0,
        enable_tracing: bool = True
    ):
        self.max_workers = max_workers
        self.default_timeout = default_timeout
        self.enable_tracing = enable_tracing
        
        self._tools: Dict[str, ToolSpec] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running: Dict[str, ExecutionResult] = {}
        self._completed: Dict[str, ExecutionResult] = {}
        self._plans: Dict[str, ExecutionPlan] = {}
        self._lock = __import__('threading').RLock()
        self._event_hooks: Dict[str, List[Callable]] = defaultdict(list)
        
        # Register default tools
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register built-in tool stubs - replace with actual implementations."""
        # These are placeholders; actual tools should be registered via register_tool()
        default_tools = [
            ToolSpec("get_mt5_live_data", ToolCategory.DATA, self._stub_tool, "Get live MT5 data"),
            ToolSpec("execute_trade", ToolCategory.TRADING, self._stub_tool, "Execute trade order", requires_confirmation=True),
            ToolSpec("close_position", ToolCategory.TRADING, self._stub_tool, "Close position"),
            ToolSpec("run_backtest", ToolCategory.ANALYSIS, self._stub_tool, "Run backtest", timeout=300),
            ToolSpec("search_knowledge", ToolCategory.KNOWLEDGE, self._stub_tool, "Search knowledge base"),
            ToolSpec("save_knowledge", ToolCategory.KNOWLEDGE, self._stub_tool, "Save to knowledge base"),
            ToolSpec("get_safety_limits", ToolCategory.SAFETY, self._stub_tool, "Get safety limits"),
            ToolSpec("check_trade_safety", ToolCategory.SAFETY, self._stub_tool, "Check trade safety"),
            ToolSpec("get_are_status", ToolCategory.SYSTEM, self._stub_tool, "Get ARE status"),
            ToolSpec("run_diagnostics", ToolCategory.SYSTEM, self._stub_tool, "Run diagnostics"),
            ToolSpec("promote_champion", ToolCategory.SYSTEM, self._stub_tool, "Promote champion"),
            ToolSpec("run_wfo", ToolCategory.LEARNING, self._stub_tool, "Run WFO", timeout=600),
        ]
        for tool in default_tools:
            self._tools[tool.name] = tool
    
    def _stub_tool(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Stub tool for testing."""
        return {"success": True, "message": "Stub executed", "args": args}
    
    # ─── Tool Registry ─────────────────────────────────────────────────────────
    
    def register_tool(self, tool: ToolSpec) -> None:
        """Register a tool implementation."""
        with self._lock:
            self._tools[tool.name] = tool
    
    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool."""
        with self._lock:
            if name in self._tools:
                del self._tools[name]
                return True
            return False
    
    def get_tool(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)
    
    def list_tools(self, category: ToolCategory = None) -> List[ToolSpec]:
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools
    
    # ─── Event Hooks ───────────────────────────────────────────────────────────
    
    def on(self, event: str, callback: Callable) -> None:
        """Register event hook: 'start', 'complete', 'error', 'retry', 'fallback'"""
        self._event_hooks[event].append(callback)
    
    def _emit(self, event: str, *args, **kwargs) -> None:
        for callback in self._event_hooks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception:
                pass
    
    # ─── Single Tool Execution ─────────────────────────────────────────────────
    
    def execute(
        self,
        tool: str,
        args: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        timeout: float = 0,
        max_retries: int = 0
    ) -> ExecutionResult:
        """Execute a single tool with retries and fallback."""
        request = ExecutionRequest(
            id=str(uuid.uuid4())[:8],
            tool=tool,
            args=args or {},
            context=context or {},
            timeout=timeout,
            max_retries=max_retries
        )
        return self._execute_request(request)
    
    def _execute_request(self, request: ExecutionRequest) -> ExecutionResult:
        """Internal: execute a single request with full retry/fallback logic."""
        tool_spec = self._tools.get(request.tool)
        if not tool_spec:
            return ExecutionResult(
                request_id=request.id,
                tool=request.tool,
                status=ExecutionStatus.FAILED,
                error=f"Tool not found: {request.tool}"
            )
        
        # Resolve timeout and retries
        timeout = request.timeout or tool_spec.timeout
        max_retries = request.max_retries or tool_spec.max_retries
        
        result = ExecutionResult(
            request_id=request.id,
            tool=request.tool,
            status=ExecutionStatus.PENDING
        )
        
        with self._lock:
            self._running[request.id] = result
        
        self._emit("start", request, tool_spec)
        
        # Retry loop
        for attempt in range(max_retries + 1):
            result.retries = attempt
            result.status = ExecutionStatus.RUNNING if attempt == 0 else ExecutionStatus.RETRYING
            
            if attempt > 0:
                delay = tool_spec.retry_delay * (2 ** (attempt - 1))
                time.sleep(delay)
                self._emit("retry", request, tool_spec, attempt)
            
            # Execute with timeout
            try:
                future = self._executor.submit(tool_spec.function, request.args)
                tool_result = future.result(timeout=timeout)
                
                # Check success
                if isinstance(tool_result, dict) and tool_result.get("success", True):
                    result.status = ExecutionStatus.COMPLETED
                    result.result = tool_result
                    result.completed_at = time.time()
                    result.duration_ms = (result.completed_at - result.started_at) * 1000
                    
                    with self._lock:
                        self._running.pop(request.id, None)
                        self._completed[request.id] = result
                    
                    self._emit("complete", request, result)
                    return result
                else:
                    # Tool returned failure
                    error = tool_result.get("error", "Tool returned failure") if isinstance(tool_result, dict) else str(tool_result)
                    result.error = error
                    
            except Exception as e:
                result.error = f"Execution error: {str(e)}"
                if "timeout" in str(e).lower() or isinstance(e, TimeoutError):
                    result.status = ExecutionStatus.TIMEOUT
        
        # All retries exhausted - try fallback
        if tool_spec.fallback and tool_spec.fallback in self._tools:
            self._emit("fallback", request, tool_spec)
            fallback_spec = self._tools[tool_spec.fallback]
            result.fallback_used = True
            result.status = ExecutionStatus.FALLBACK
            
            try:
                future = self._executor.submit(fallback_spec.function, request.args)
                fallback_result = future.result(timeout=fallback_spec.timeout)
                
                if isinstance(fallback_result, dict) and fallback_result.get("success", True):
                    result.status = ExecutionStatus.COMPLETED
                    result.result = fallback_result
                    result.completed_at = time.time()
                    result.duration_ms = (result.completed_at - result.started_at) * 1000
                    
                    with self._lock:
                        self._running.pop(request.id, None)
                        self._completed[request.id] = result
                    
                    self._emit("complete", request, result)
                    return result
            except Exception as e:
                result.error = f"Fallback also failed: {str(e)}"
        
        # Complete failure
        result.status = ExecutionStatus.FAILED
        result.completed_at = time.time()
        result.duration_ms = (result.completed_at - result.started_at) * 1000
        
        with self._lock:
            self._running.pop(request.id, None)
            self._completed[request.id] = result
        
        self._emit("error", request, result)
        return result
    
    # ─── Plan Execution (DAG) ──────────────────────────────────────────────────
    
    def create_plan(self, requests: List[ExecutionRequest]) -> ExecutionPlan:
        """Create an execution plan from requests."""
        plan = ExecutionPlan(
            id=str(uuid.uuid4())[:8],
            requests=requests
        )
        with self._lock:
            self._plans[plan.id] = plan
        return plan
    
    def execute_plan(self, plan: ExecutionPlan, parallel: bool = True) -> Dict[str, ExecutionResult]:
        """Execute a plan respecting dependencies."""
        plan.status = ExecutionStatus.RUNNING
        plan.started_at = time.time()
        
        # Build dependency graph
        req_map = {r.id: r for r in plan.requests}
        dep_graph = {r.id: set(r.depends_on) for r in plan.requests}
        completed = set()
        
        while True:
            # Find ready requests
            ready = [
                r for r in plan.requests
                if r.id not in completed
                and r.id not in plan.results
                and all(d in completed for d in r.depends_on)
            ]
            
            if not ready:
                # Check if any still running
                running = [r for r in plan.requests if r.id not in completed and r.id not in plan.results]
                if not running:
                    break  # All done or stuck
                if parallel:
                    time.sleep(0.1)
                    continue
            
            if parallel and len(ready) > 1:
                # Execute ready requests in parallel
                futures = {}
                for req in ready:
                    future = self._executor.submit(self._execute_request, req)
                    futures[future] = req
                
                for future in as_completed(futures):
                    req = futures[future]
                    try:
                        result = future.result()
                        plan.results[req.id] = result
                        if result.status == ExecutionStatus.COMPLETED:
                            completed.add(req.id)
                        else:
                            # Failed - decide whether to continue
                            if not self._should_continue_on_failure(plan, req):
                                plan.status = ExecutionStatus.FAILED
                                plan.completed_at = time.time()
                                return plan.results
                    except Exception as e:
                        plan.results[req.id] = ExecutionResult(
                            request_id=req.id,
                            tool=req.tool,
                            status=ExecutionStatus.FAILED,
                            error=str(e)
                        )
            else:
                # Sequential execution
                for req in ready:
                    result = self._execute_request(req)
                    plan.results[req.id] = result
                    if result.status == ExecutionStatus.COMPLETED:
                        completed.add(req.id)
                    else:
                        if not self._should_continue_on_failure(plan, req):
                            plan.status = ExecutionStatus.FAILED
                            plan.completed_at = time.time()
                            return plan.results
        
        # Check final status
        failed = [r for r in plan.results.values() if r.status == ExecutionStatus.FAILED]
        plan.status = ExecutionStatus.FAILED if failed else ExecutionStatus.COMPLETED
        plan.completed_at = time.time()
        
        return plan.results
    
    def _should_continue_on_failure(self, plan: ExecutionPlan, failed_req: ExecutionRequest) -> bool:
        """Determine if plan should continue after a failure."""
        # Check if any remaining requests depend on this one
        for req in plan.requests:
            if failed_req.id in req.depends_on and req.id not in plan.results:
                return False  # Blocking dependency failed
        return True  # No blocking dependencies
    
    # ─── Convenience Methods ───────────────────────────────────────────────────
    
    def execute_sequence(
        self,
        steps: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> List[ExecutionResult]:
        """Execute a sequence of tools sequentially."""
        requests = []
        for i, step in enumerate(steps):
            req = ExecutionRequest(
                id=f"seq_{i}_{str(uuid.uuid4())[:6]}",
                tool=step["tool"],
                args=step.get("args", {}),
                context=context or {},
                depends_on=[requests[-1].id] if requests else []
            )
            requests.append(req)
        
        plan = self.create_plan(requests)
        self.execute_plan(plan, parallel=False)
        return list(plan.results.values())
    
    def execute_parallel(
        self,
        steps: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> List[ExecutionResult]:
        """Execute multiple tools in parallel."""
        requests = [
            ExecutionRequest(
                id=f"par_{i}_{str(uuid.uuid4())[:6]}",
                tool=step["tool"],
                args=step.get("args", {}),
                context=context or {}
            )
            for i, step in enumerate(steps)
        ]
        
        plan = self.create_plan(requests)
        self.execute_plan(plan, parallel=True)
        return list(plan.results.values())
    
    # ─── Status & Tracing ──────────────────────────────────────────────────────
    
    def get_running(self) -> Dict[str, ExecutionResult]:
        return dict(self._running)
    
    def get_result(self, request_id: str) -> Optional[ExecutionResult]:
        return self._completed.get(request_id) or self._running.get(request_id)
    
    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        return self._plans.get(plan_id)
    
    def save_execution(self, plan: ExecutionPlan, path: str = None) -> str:
        path = path or str(EXECUTION_DIR / f"exec_{plan.id}.json")
        with open(path, 'w') as f:
            json.dump(plan.to_dict(), f, indent=2)
        return path
    
    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the executor."""
        self._executor.shutdown(wait=wait)
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.shutdown()


# ─── Module Exports ──────────────────────────────────────────────────────────────

__all__ = [
    'ExecutionStatus',
    'ToolCategory',
    'ToolSpec',
    'ExecutionRequest',
    'ExecutionResult',
    'ExecutionPlan',
    'AutonomousExecutor',
]