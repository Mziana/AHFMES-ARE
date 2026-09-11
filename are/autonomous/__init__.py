"""
Autonomous Agent Core Package
=============================

Core modules for the autonomous trading agent:
- memory: Episodic + Semantic + Working memory
- scheduler: Cron-style task scheduling
- planner: Goal decomposition → task graphs
- reasoner: CoT + Self-reflection + Critique (OpenRouter Nemotron 3 Ultra)
- executor: Tool orchestration with retries/fallbacks
- loops: Micro/Meso/Macro cycle orchestration
"""

from are.autonomous.memory import (
    AutonomousMemory,
    MemoryTier,
    EpisodicMemory,
    SemanticMemory,
    WorkingMemory
)

from are.autonomous.scheduler import (
    AutonomousScheduler,
    ScheduleType,
    ScheduledTask
)

from are.autonomous.planner import (
    AutonomousPlanner,
    Plan,
    PlanStep,
    TaskStatus,
    GoalType,
    GOAL_TEMPLATES
)

from are.autonomous.reasoner import (
    AutonomousReasoner,
    ReasoningType,
    Thought,
    ReasoningTrace,
    create_openrouter_client
)

from are.autonomous.executor import (
    AutonomousExecutor,
    ExecutionStatus,
    ToolCategory,
    ToolSpec,
    ExecutionRequest,
    ExecutionResult,
    ExecutionPlan
)

from are.autonomous.loops import (
    AutonomousLoops,
    LoopLevel,
    AgentState,
    LoopContext,
    LoopResult,
    create_autonomous_agent,
    default_micro_loop,
    default_meso_loop,
    default_macro_loop
)

__version__ = "1.0.0"

__all__ = [
    # Memory
    'AutonomousMemory',
    'MemoryTier',
    'EpisodicMemory',
    'SemanticMemory',
    'WorkingMemory',
    
    # Scheduler
    'AutonomousScheduler',
    'ScheduleType',
    'ScheduledTask',
    
    # Planner
    'AutonomousPlanner',
    'Plan',
    'PlanStep',
    'TaskStatus',
    'GoalType',
    'GOAL_TEMPLATES',
    
    # Reasoner
    'AutonomousReasoner',
    'ReasoningType',
    'Thought',
    'ReasoningTrace',
    'create_openrouter_client',
    
    # Executor
    'AutonomousExecutor',
    'ExecutionStatus',
    'ToolCategory',
    'ToolSpec',
    'ExecutionRequest',
    'ExecutionResult',
    'ExecutionPlan',
    
    # Loops
    'AutonomousLoops',
    'LoopLevel',
    'AgentState',
    'LoopContext',
    'LoopResult',
    'create_autonomous_agent',
    'default_micro_loop',
    'default_meso_loop',
    'default_macro_loop',
]