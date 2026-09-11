"""
Autonomous Scheduler — Cron-style task scheduling for ARE cycles
Supports: recurring cycles, one-shot tasks, priority queue, persistence
"""

from __future__ import annotations

import heapq
import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
import uuid
from enum import Enum


# ─── Schedule Type Enum ────────────────────────────────────────────────────────

class ScheduleType(Enum):
    """Schedule type classification."""
    INTERVAL = "interval"   # Recurring at fixed interval
    CRON = "cron"           # Cron expression based
    ONCE = "once"           # One-shot at specific time
    EVENT = "event"         # Triggered by event


# ─── Configuration ──────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "autonomous"
SCHEDULE_FILE = DATA_DIR / "schedule.json"
TASK_LOG_FILE = DATA_DIR / "task_log.jsonl"

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ─── Task Definitions ───────────────────────────────────────────────────────────

@dataclass
class ScheduledTask:
    """A scheduled task with timing and execution metadata."""
    id: str
    name: str
    func_name: str                    # Function to call (registered in scheduler)
    args: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    schedule_type: str = "interval"   # 'interval', 'cron', 'once', 'event'
    interval_seconds: float = 300     # For interval type
    cron_expression: str = ""         # For cron type (simplified)
    run_at: float = 0                 # For once type (timestamp)
    event_trigger: str = ""           # For event type
    
    # Execution control
    priority: int = 5                 # 1=highest, 10=lowest
    max_retries: int = 3
    timeout_seconds: float = 60
    enabled: bool = True
    
    # State
    created_at: float = field(default_factory=time.time)
    last_run: float = 0
    next_run: float = 0
    run_count: int = 0
    failure_count: int = 0
    last_error: str = ""
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    description: str = ""
    
    def __lt__(self, other: 'ScheduledTask') -> bool:
        """For priority queue ordering: earlier next_run first, then priority."""
        if self.next_run != other.next_run:
            return self.next_run < other.next_run
        return self.priority < other.priority
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "func_name": self.func_name,
            "args": self.args,
            "schedule_type": self.schedule_type,
            "interval_seconds": self.interval_seconds,
            "cron_expression": self.cron_expression,
            "run_at": self.run_at,
            "event_trigger": self.event_trigger,
            "priority": self.priority,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "run_count": self.run_count,
            "failure_count": self.failure_count,
            "last_error": self.last_error,
            "tags": self.tags,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledTask':
        return cls(**data)
    
    def calculate_next_run(self, now: float = None) -> float:
        """Calculate next run time based on schedule type."""
        now = now or time.time()
        
        if self.schedule_type == "interval":
            if self.last_run == 0:
                return now  # Run immediately first time
            return self.last_run + self.interval_seconds
        
        elif self.schedule_type == "once":
            return self.run_at
        
        elif self.schedule_type == "cron":
            # Simplified cron: only support basic patterns
            # For now, treat as interval
            if self.last_run == 0:
                return now
            return self.last_run + self.interval_seconds
        
        elif self.schedule_type == "event":
            # Event-driven: next_run stays 0 until triggered
            return 0
        
        return now + self.interval_seconds


@dataclass
class TaskResult:
    """Result of task execution."""
    task_id: str
    task_name: str
    success: bool
    result: Any = None
    error: str = ""
    started_at: float = 0
    completed_at: float = 0
    duration_ms: float = 0
    retry_count: int = 0


# ─── Function Registry ──────────────────────────────────────────────────────────

class FunctionRegistry:
    """Registry of callable functions for scheduled tasks."""
    
    def __init__(self):
        self._functions: Dict[str, Callable] = {}
        self._metadata: Dict[str, Dict] = {}
    
    def register(self, name: str, func: Callable, description: str = "", 
                 params_schema: Dict = None):
        """Register a function for use in scheduled tasks."""
        self._functions[name] = func
        self._metadata[name] = {
            "description": description,
            "params_schema": params_schema or {},
            "registered_at": time.time()
        }
    
    def get(self, name: str) -> Optional[Callable]:
        return self._functions.get(name)
    
    def list_functions(self) -> Dict[str, Dict]:
        return self._metadata.copy()
    
    def call(self, name: str, args: Dict[str, Any]) -> Any:
        func = self._functions.get(name)
        if not func:
            raise ValueError(f"Function '{name}' not registered")
        return func(**args)


# ─── Scheduler Core ─────────────────────────────────────────────────────────────

class AutonomousScheduler:
    """
    Priority-based task scheduler for autonomous cycles.
    Supports recurring, one-shot, and event-driven tasks.
    """
    
    def __init__(self, function_registry: FunctionRegistry = None):
        self.registry = function_registry or FunctionRegistry()
        self._tasks: Dict[str, ScheduledTask] = {}
        self._queue: List[ScheduledTask] = []  # heap queue
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._event_triggers: Dict[str, List[str]] = {}  # event -> task_ids
        self._shutdown_event = threading.Event()
        
        # Load persisted schedule
        self._load_schedule()
        self._rebuild_queue()
    
    def _load_schedule(self):
        """Load tasks from persisted schedule file."""
        try:
            if SCHEDULE_FILE.exists():
                with open(SCHEDULE_FILE, 'r') as f:
                    data = json.load(f)
                for task_data in data.get("tasks", []):
                    task = ScheduledTask.from_dict(task_data)
                    self._tasks[task.id] = task
        except Exception as e:
            print(f"[Scheduler] Failed to load schedule: {e}")
    
    def _save_schedule(self):
        """Persist tasks to schedule file."""
        try:
            data = {
                "tasks": [task.to_dict() for task in self._tasks.values()],
                "saved_at": time.time()
            }
            with open(SCHEDULE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Scheduler] Failed to save schedule: {e}")
    
    def _rebuild_queue(self):
        """Rebuild priority queue from tasks."""
        with self._lock:
            self._queue = []
            now = time.time()
            for task in self._tasks.values():
                if task.enabled:
                    task.next_run = task.calculate_next_run(now)
                    if task.next_run > 0:
                        heapq.heappush(self._queue, task)
    
    def _log_task_result(self, result: TaskResult):
        """Log task execution result."""
        try:
            log_entry = {
                "task_id": result.task_id,
                "task_name": result.task_name,
                "success": result.success,
                "error": result.error,
                "started_at": result.started_at,
                "completed_at": result.completed_at,
                "duration_ms": result.duration_ms,
                "retry_count": result.retry_count
            }
            with open(TASK_LOG_FILE, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
    
    # ─── Task Management ───────────────────────────────────────────────────────
    
    def add_task(
        self,
        name: str,
        func_name: str,
        args: Dict[str, Any] = None,
        schedule_type: str = "interval",
        interval_seconds: float = 300,
        cron_expression: str = "",
        run_at: float = 0,
        event_trigger: str = "",
        priority: int = 5,
        max_retries: int = 3,
        timeout_seconds: float = 60,
        tags: List[str] = None,
        description: str = "",
        task_id: str = None
    ) -> str:
        """Add a new scheduled task."""
        task_id = task_id or str(uuid.uuid4())[:8]
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            func_name=func_name,
            args=args or {},
            schedule_type=schedule_type,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            run_at=run_at,
            event_trigger=event_trigger,
            priority=priority,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            tags=tags or [],
            description=description
        )
        
        # Calculate initial next_run
        now = time.time()
        task.next_run = task.calculate_next_run(now)
        
        with self._lock:
            self._tasks[task_id] = task
            if task.enabled and task.next_run > 0:
                heapq.heappush(self._queue, task)
            
            # Register event trigger
            if event_trigger:
                if event_trigger not in self._event_triggers:
                    self._event_triggers[event_trigger] = []
                self._event_triggers[event_trigger].append(task_id)
        
        self._save_schedule()
        return task_id
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a task from scheduler."""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks.pop(task_id)
                # Remove from event triggers
                for event, tasks in self._event_triggers.items():
                    if task_id in tasks:
                        tasks.remove(task_id)
                self._save_schedule()
                return True
        return False
    
    def enable_task(self, task_id: str, enabled: bool = True) -> bool:
        """Enable/disable a task."""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                if task.enabled != enabled:
                    task.enabled = enabled
                    if enabled:
                        task.next_run = task.calculate_next_run(time.time())
                        heapq.heappush(self._queue, task)
                    self._save_schedule()
                return True
        return False
    
    def trigger_event(self, event_name: str, event_data: Dict = None):
        """Trigger all tasks listening for an event."""
        task_ids = self._event_triggers.get(event_name, [])
        for task_id in task_ids:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                # Merge event data into task args
                merged_args = {**task.args, **(event_data or {})}
                # Execute immediately (fire and forget)
                self._execute_task_async(task, merged_args)
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        return self._tasks.get(task_id)
    
    def list_tasks(self, enabled_only: bool = False) -> List[ScheduledTask]:
        with self._lock:
            tasks = list(self._tasks.values())
            if enabled_only:
                tasks = [t for t in tasks if t.enabled]
            return sorted(tasks, key=lambda t: (t.next_run if t.next_run > 0 else float('inf'), t.priority))
    
    # ─── Execution Loop ────────────────────────────────────────────────────────
    
    def start(self):
        """Start the scheduler loop in background thread."""
        if self._running:
            return
        
        self._running = True
        self._shutdown_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
    
    def stop(self, timeout: float = 10):
        """Stop the scheduler."""
        self._running = False
        self._shutdown_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
    
    def _run_loop(self):
        """Main scheduler loop."""
        while self._running and not self._shutdown_event.is_set():
            try:
                self._process_due_tasks()
            except Exception as e:
                print(f"[Scheduler] Loop error: {e}")
            
            # Sleep briefly, check shutdown
            self._shutdown_event.wait(1.0)
    
    def _process_due_tasks(self):
        """Check and execute due tasks."""
        now = time.time()
        due_tasks = []
        
        with self._lock:
            # Pop all due tasks
            while self._queue and self._queue[0].next_run <= now:
                task = heapq.heappop(self._queue)
                if task.enabled and task.id in self._tasks:
                    due_tasks.append(task)
        
        # Execute outside lock
        for task in due_tasks:
            self._execute_task(task)
    
    def _execute_task(self, task: ScheduledTask):
        """Execute a task with retry logic."""
        func = self.registry.get(task.func_name)
        if not func:
            self._record_failure(task, f"Function '{task.func_name}' not registered")
            return
        
        last_error = ""
        for attempt in range(task.max_retries + 1):
            result = TaskResult(
                task_id=task.id,
                task_name=task.name,
                success=False,
                started_at=time.time(),
                retry_count=attempt
            )
            
            try:
                # Execute with timeout
                result.result = func(**task.args)
                result.success = True
                result.completed_at = time.time()
                result.duration_ms = (result.completed_at - result.started_at) * 1000
                
                self._record_success(task, result)
                break
                
            except Exception as e:
                last_error = str(e)
                result.error = last_error
                result.completed_at = time.time()
                result.duration_ms = (result.completed_at - result.started_at) * 1000
                
                if attempt < task.max_retries:
                    time.sleep(1 * (attempt + 1))  # Backoff
        
        if not result.success:
            self._record_failure(task, last_error, result)
        
        self._log_task_result(result)
    
    def _execute_task_async(self, task: ScheduledTask, args: Dict):
        """Execute task in background thread (for event triggers)."""
        thread = threading.Thread(
            target=self._execute_task_with_args,
            args=(task, args),
            daemon=True
        )
        thread.start()
    
    def _execute_task_with_args(self, task: ScheduledTask, args: Dict):
        """Execute task with overridden args."""
        func = self.registry.get(task.func_name)
        if not func:
            return
        
        result = TaskResult(
            task_id=task.id,
            task_name=task.name,
            success=False,
            started_at=time.time()
        )
        
        try:
            result.result = func(**args)
            result.success = True
        except Exception as e:
            result.error = str(e)
        finally:
            result.completed_at = time.time()
            result.duration_ms = (result.completed_at - result.started_at) * 1000
            self._log_task_result(result)
    
    def _record_success(self, task: ScheduledTask, result: TaskResult):
        with self._lock:
            task.last_run = result.started_at
            task.run_count += 1
            task.failure_count = 0
            task.last_error = ""
            
            # Calculate next run
            if task.schedule_type != "once" and task.schedule_type != "event":
                task.next_run = task.calculate_next_run(task.last_run)
                if task.next_run > 0:
                    heapq.heappush(self._queue, task)
            elif task.schedule_type == "once":
                # Disable one-shot tasks after completion
                task.enabled = False
        
        self._save_schedule()
    
    def _record_failure(self, task: ScheduledTask, error: str, result: TaskResult = None):
        with self._lock:
            task.failure_count += 1
            task.last_error = error
            
            if task.failure_count >= task.max_retries:
                # Disable after max retries exceeded
                task.enabled = False
                task.next_run = 0
            else:
                # Retry soon
                task.next_run = time.time() + 60  # 1 min retry
                heapq.heappush(self._queue, task)
        
        self._save_schedule()
    
    # ─── Predefined Cycle Tasks ────────────────────────────────────────────────
    
    def setup_default_cycles(self, engine_funcs: Dict[str, Callable]):
        """Set up default autonomous cycles."""
        # Register engine functions
        for name, func in engine_funcs.items():
            self.registry.register(name, func, f"Engine function: {name}")
        
        # Micro cycle: every 30 seconds (process tick, update state)
        self.add_task(
            name="micro_cycle",
            func_name="process_market_tick",
            schedule_type="interval",
            interval_seconds=30,
            priority=1,
            tags=["cycle", "micro"],
            description="Process market tick through full pipeline"
        )
        
        # Meso cycle: every 5 minutes (opportunity scan, direction check)
        self.add_task(
            name="meso_cycle",
            func_name="run_opportunity_scan",
            schedule_type="interval",
            interval_seconds=300,
            priority=2,
            tags=["cycle", "meso"],
            description="Scan for trading opportunities"
        )
        
        # Macro cycle: every hour (champion evaluation, strategy review)
        self.add_task(
            name="macro_cycle",
            func_name="run_strategy_review",
            schedule_type="interval",
            interval_seconds=3600,
            priority=3,
            tags=["cycle", "macro"],
            description="Review champion performance, strategy evolution"
        )
        
        # Daily: knowledge ingestion, cleanup
        self.add_task(
            name="daily_ingestion",
            func_name="ingest_knowledge",
            schedule_type="interval",
            interval_seconds=86400,
            priority=5,
            tags=["maintenance", "daily"],
            description="Ingest trades/backtests into knowledge base"
        )
        
        # Weekly: self-improvement, WFO validation
        self.add_task(
            name="weekly_self_improve",
            func_name="run_self_improvement",
            schedule_type="interval",
            interval_seconds=604800,
            priority=4,
            tags=["improvement", "weekly"],
            description="Run WFO validation, promote champions"
        )


# ─── Default Engine Functions (to be wired up) ──────────────────────────────────

def create_default_registry() -> FunctionRegistry:
    """Create registry with placeholder functions."""
    registry = FunctionRegistry()
    
    # These will be replaced with real implementations
    def placeholder(**kwargs):
        return {"status": "placeholder", "args": kwargs}
    
    registry.register("process_market_tick", placeholder, "Process single market tick")
    registry.register("run_opportunity_scan", placeholder, "Scan for opportunities")
    registry.register("run_strategy_review", placeholder, "Review strategy performance")
    registry.register("ingest_knowledge", placeholder, "Ingest knowledge base")
    registry.register("run_self_improvement", placeholder, "Run self-improvement cycle")
    registry.register("run_wfo_validation", placeholder, "Run Walk-Forward Optimization")
    registry.register("promote_champion", placeholder, "Promote candidate to champion")
    registry.register("run_diagnostics", placeholder, "Run system diagnostics")
    
    return registry


# ─── Module Exports ──────────────────────────────────────────────────────────────

__all__ = [
    'ScheduledTask',
    'TaskResult',
    'FunctionRegistry',
    'AutonomousScheduler',
    'create_default_registry',
]