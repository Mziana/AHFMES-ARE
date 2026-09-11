"""
Autonomous Reasoner — Chain-of-Thought + Self-Reflection + Critique
Implements structured reasoning for autonomous decision making.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from collections import deque


# ─── Configuration ──────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "autonomous"
REASONING_DIR = DATA_DIR / "reasoning"
REASONING_DIR.mkdir(parents=True, exist_ok=True)


# ─── Types & Enums ──────────────────────────────────────────────────────────────

class ReasoningType(Enum):
    OBSERVATION = "observation"       # Raw perception of state
    ANALYSIS = "analysis"             # Break down situation
    PLANNING = "planning"             # Formulate action plan
    DECISION = "decision"             # Choose action
    REFLECTION = "reflection"         # Post-action review
    CRITIQUE = "critique"             # Self-critique of reasoning
    HYPOTHESIS = "hypothesis"         # Formulate testable hypothesis


class ConfidenceLevel(Enum):
    VERY_LOW = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9


@dataclass
class Thought:
    """A single reasoning step."""
    id: str
    type: ReasoningType
    content: str
    confidence: float = 0.5
    evidence: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    alternatives_considered: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    parent_id: str = ""  # For thought chains
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "assumptions": self.assumptions,
            "alternatives_considered": self.alternatives_considered,
            "timestamp": self.timestamp,
            "parent_id": self.parent_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Thought':
        return cls(
            id=data["id"],
            type=ReasoningType(data["type"]),
            content=data["content"],
            confidence=data.get("confidence", 0.5),
            evidence=data.get("evidence", []),
            assumptions=data.get("assumptions", []),
            alternatives_considered=data.get("alternatives_considered", []),
            timestamp=data.get("timestamp", time.time()),
            parent_id=data.get("parent_id", "")
        )


@dataclass
class ReasoningTrace:
    """Complete reasoning trace for a decision cycle."""
    id: str
    trigger: str                    # What triggered this reasoning
    context: Dict[str, Any]         # State snapshot at reasoning time
    thoughts: List[Thought] = field(default_factory=list)
    conclusion: str = ""
    action: str = ""                # Recommended action
    confidence: float = 0.5
    started_at: float = field(default_factory=time.time)
    completed_at: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "trigger": self.trigger,
            "context": self.context,
            "thoughts": [t.to_dict() for t in self.thoughts],
            "conclusion": self.conclusion,
            "action": self.action,
            "confidence": self.confidence,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReasoningTrace':
        trace = cls(
            id=data["id"],
            trigger=data["trigger"],
            context=data["context"],
            conclusion=data.get("conclusion", ""),
            action=data.get("action", ""),
            confidence=data.get("confidence", 0.5),
            started_at=data.get("started_at", time.time()),
            completed_at=data.get("completed_at", 0),
            metadata=data.get("metadata", {})
        )
        trace.thoughts = [Thought.from_dict(t) for t in data.get("thoughts", [])]
        return trace


# ─── Reasoning Prompts (Templates for LLM) ──────────────────────────────────────

REASONING_PROMPTS = {
    ReasoningType.OBSERVATION: """
You are an autonomous trading agent observing the current market state.
Analyze the provided data and produce a structured observation.

Context: {context}

Output JSON with:
{{
  "observation": "What you see in the data",
  "key_factors": ["factor1", "factor2"],
  "anomalies": ["anything unusual"],
  "confidence": 0.0-1.0
}}
""",
    
    ReasoningType.ANALYSIS: """
You are analyzing a trading situation. Break down the observation into components.

Observation: {observation}
Context: {context}

Output JSON with:
{{
  "analysis": "Detailed breakdown",
  "supporting_evidence": ["evidence1", "evidence2"],
  "contradicting_evidence": ["evidence1"],
  "risk_factors": ["risk1", "risk2"],
  "opportunity_factors": ["opp1", "opp2"],
  "confidence": 0.0-1.0
}}
""",
    
    ReasoningType.PLANNING: """
Formulate a plan to achieve the goal given the analysis.

Goal: {goal}
Analysis: {analysis}
Context: {context}
Available Tools: {tools}

Output JSON with:
{{
  "plan": "Step-by-step plan",
  "steps": [
    {{"tool": "tool_name", "args": {{}}, "reason": "why this step"}}
  ],
  "fallback_plan": "Alternative if primary fails",
  "success_criteria": ["criterion1", "criterion2"],
  "confidence": 0.0-1.0
}}
""",
    
    ReasoningType.DECISION: """
Make a final decision based on the reasoning chain.

Context: {context}
Analysis: {analysis}
Plan: {plan}
Risk Assessment: {risk}

Output JSON with:
{{
  "decision": "EXECUTE | WAIT | ABORT | MODIFY",
  "action": "Specific action to take",
  "reasoning": "Why this decision",
  "confidence": 0.0-1.0,
  "conditions": ["condition1", "condition2"]
}}
""",
    
    ReasoningType.REFLECTION: """
Reflect on the outcome of the previous action.

Previous Action: {action}
Expected Outcome: {expected}
Actual Outcome: {actual}
Context: {context}

Output JSON with:
{{
  "reflection": "What happened vs expected",
  "lessons_learned": ["lesson1", "lesson2"],
  "what_worked": ["item1"],
  "what_failed": ["item1"],
  "adjustments": ["adjustment1"],
  "confidence": 0.0-1.0
}}
""",
    
    ReasoningType.CRITIQUE: """
Critique your own reasoning for biases, gaps, or errors.

Reasoning Trace: {trace}
Outcome: {outcome}

Output JSON with:
{{
  "critique": "Critical assessment",
  "biases_found": ["bias1", "bias2"],
  "gaps": ["gap1", "gap2"],
  "overconfidence_areas": ["area1"],
  "improvement_suggestions": ["suggestion1"],
  "confidence": 0.0-1.0
}}
""",
    
    ReasoningType.HYPOTHESIS: """
Formulate a testable hypothesis based on observations.

Observation: {observation}
Pattern: {pattern}
Context: {context}

Output JSON with:
{{
  "hypothesis": "Testable statement",
  "variables": ["independent_var", "dependent_var"],
  "prediction": "Expected outcome if true",
  "test_method": "How to validate",
  "confidence": 0.0-1.0
}}
"""
}


# ─── Reasoner Core ──────────────────────────────────────────────────────────────

class AutonomousReasoner:
    """
    Chain-of-Thought reasoning with self-reflection and critique.
    Uses LLM (OpenRouter Nemotron 3 Ultra) for structured reasoning.
    """
    
    def __init__(
        self, 
        llm_client: Callable[[str], Dict[str, Any]] = None,
        enable_critique: bool = True,
        enable_reflection: bool = True,
        max_thought_depth: int = 10
    ):
        self.llm_client = llm_client or self._mock_llm
        self.enable_critique = enable_critique
        self.enable_reflection = enable_reflection
        self.max_thought_depth = max_thought_depth
        self._traces: Dict[str, ReasoningTrace] = {}
        self._thought_chain: List[Thought] = []
        self._lock = __import__('threading').RLock()
    
    def _mock_llm(self, prompt: str) -> Dict[str, Any]:
        """Mock LLM for testing - replace with OpenRouter call."""
        return {
            "success": True,
            "content": json.dumps({
                "observation": "Mock observation",
                "analysis": "Mock analysis",
                "plan": "Mock plan",
                "decision": "WAIT",
                "action": "No action",
                "reasoning": "Mock reasoning",
                "confidence": 0.5,
                "reflection": "Mock reflection",
                "lessons_learned": [],
                "critique": "Mock critique",
                "biases_found": [],
                "hypothesis": "Mock hypothesis"
            })
        }
    
    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Call LLM with structured output parsing."""
        try:
            result = self.llm_client(prompt)
            if not result.get("success"):
                return {"success": False, "error": result.get("error", "LLM failed")}
            
            # Parse JSON from response
            content = result.get("content", "{}")
            # Try to extract JSON from markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(content)
            return {"success": True, "parsed": parsed}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON parse error: {e}", "raw": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ─── Main Reasoning Pipeline ───────────────────────────────────────────────
    
    def reason(
        self,
        trigger: str,
        context: Dict[str, Any],
        goal: str = "",
        available_tools: List[str] = None
    ) -> ReasoningTrace:
        """
        Full reasoning pipeline: Observation → Analysis → Planning → Decision → [Reflection] → [Critique]
        """
        trace = ReasoningTrace(
            id=str(uuid.uuid4())[:8],
            trigger=trigger,
            context=context.copy()
        )
        
        available_tools = available_tools or []
        
        # Step 1: Observation
        obs_thought = self._think(ReasoningType.OBSERVATION, {
            "context": json.dumps(context, indent=2)
        })
        trace.thoughts.append(obs_thought)
        
        # Step 2: Analysis
        analysis_thought = self._think(ReasoningType.ANALYSIS, {
            "observation": obs_thought.content,
            "context": json.dumps(context, indent=2)
        })
        analysis_thought.parent_id = obs_thought.id
        trace.thoughts.append(analysis_thought)
        
        # Step 3: Planning (if goal provided)
        if goal:
            plan_thought = self._think(ReasoningType.PLANNING, {
                "goal": goal,
                "analysis": analysis_thought.content,
                "context": json.dumps(context, indent=2),
                "tools": json.dumps(available_tools, indent=2)
            })
            plan_thought.parent_id = analysis_thought.id
            trace.thoughts.append(plan_thought)
        else:
            plan_thought = None
        
        # Step 4: Decision
        decision_thought = self._think(ReasoningType.DECISION, {
            "context": json.dumps(context, indent=2),
            "analysis": analysis_thought.content,
            "plan": plan_thought.content if plan_thought else "No plan",
            "risk": self._assess_risk(context, analysis_thought)
        })
        decision_thought.parent_id = (plan_thought or analysis_thought).id
        trace.thoughts.append(decision_thought)
        
        # Extract conclusion and action
        decision_data = self._extract_json(decision_thought.content)
        trace.conclusion = decision_data.get("reasoning", decision_thought.content)
        trace.action = decision_data.get("action", "No action")
        trace.confidence = decision_data.get("confidence", decision_thought.confidence)
        
        # Step 5: Self-Critique (optional)
        if self.enable_critique:
            critique_thought = self._critique(trace)
            trace.thoughts.append(critique_thought)
            
            # Adjust confidence based on critique
            critique_data = self._extract_json(critique_thought.content)
            if critique_data.get("confidence"):
                trace.confidence = (trace.confidence + critique_data["confidence"]) / 2
        
        trace.completed_at = time.time()
        
        with self._lock:
            self._traces[trace.id] = trace
        
        return trace
    
    def _think(self, rtype: ReasoningType, variables: Dict[str, str]) -> Thought:
        """Generate a single thought using LLM."""
        prompt_template = REASONING_PROMPTS.get(rtype, "")
        if not prompt_template:
            return Thought(
                id=str(uuid.uuid4())[:8],
                type=rtype,
                content=f"No template for {rtype.value}",
                confidence=0.1
            )
        
        prompt = prompt_template.format(**variables)
        result = self._call_llm(prompt)
        
        if result["success"]:
            parsed = result["parsed"]
            # Extract main content based on type
            content_key = rtype.value
            content = parsed.get(content_key, str(parsed))
            confidence = parsed.get("confidence", 0.5)
            evidence = parsed.get("supporting_evidence", parsed.get("evidence", []))
            assumptions = parsed.get("assumptions", [])
            alternatives = parsed.get("alternatives_considered", [])
        else:
            content = f"LLM error: {result.get('error', 'Unknown')}"
            confidence = 0.1
            evidence = []
            assumptions = []
            alternatives = []
        
        return Thought(
            id=str(uuid.uuid4())[:8],
            type=rtype,
            content=content,
            confidence=confidence,
            evidence=evidence,
            assumptions=assumptions,
            alternatives_considered=alternatives
        )
    
    def _critique(self, trace: ReasoningTrace) -> Thought:
        """Self-critique the reasoning trace."""
        trace_json = json.dumps([t.to_dict() for t in trace.thoughts], indent=2)
        
        prompt = REASONING_PROMPTS[ReasoningType.CRITIQUE].format(
            trace=trace_json,
            outcome=f"Action: {trace.action}, Confidence: {trace.confidence}"
        )
        
        result = self._call_llm(prompt)
        
        if result["success"]:
            parsed = result["parsed"]
            content = parsed.get("critique", str(parsed))
            confidence = parsed.get("confidence", 0.5)
        else:
            content = f"Critique failed: {result.get('error')}"
            confidence = 0.3
        
        return Thought(
            id=str(uuid.uuid4())[:8],
            type=ReasoningType.CRITIQUE,
            content=content,
            confidence=confidence,
            parent_id=trace.thoughts[-1].id if trace.thoughts else ""
        )
    
    def reflect(
        self,
        action: str,
        expected: str,
        actual: str,
        context: Dict[str, Any]
    ) -> Thought:
        """Post-action reflection."""
        prompt = REASONING_PROMPTS[ReasoningType.REFLECTION].format(
            action=action,
            expected=expected,
            actual=actual,
            context=json.dumps(context, indent=2)
        )
        
        result = self._call_llm(prompt)
        
        if result["success"]:
            parsed = result["parsed"]
            content = parsed.get("reflection", str(parsed))
            confidence = parsed.get("confidence", 0.5)
        else:
            content = f"Reflection failed: {result.get('error')}"
            confidence = 0.3
        
        thought = Thought(
            id=str(uuid.uuid4())[:8],
            type=ReasoningType.REFLECTION,
            content=content,
            confidence=confidence
        )
        
        with self._lock:
            self._thought_chain.append(thought)
        
        return thought
    
    def hypothesize(
        self,
        observation: str,
        pattern: str,
        context: Dict[str, Any]
    ) -> Thought:
        """Formulate a testable hypothesis."""
        prompt = REASONING_PROMPTS[ReasoningType.HYPOTHESIS].format(
            observation=observation,
            pattern=pattern,
            context=json.dumps(context, indent=2)
        )
        
        result = self._call_llm(prompt)
        
        if result["success"]:
            parsed = result["parsed"]
            content = parsed.get("hypothesis", str(parsed))
            confidence = parsed.get("confidence", 0.5)
        else:
            content = f"Hypothesis failed: {result.get('error')}"
            confidence = 0.3
        
        return Thought(
            id=str(uuid.uuid4())[:8],
            type=ReasoningType.HYPOTHESIS,
            content=content,
            confidence=confidence
        )
    
    def _assess_risk(self, context: Dict[str, Any], analysis: Thought) -> str:
        """Quick risk assessment for decision making."""
        risk_factors = []
        
        # Check safety limits
        if context.get("safety", {}).get("kill_switch"):
            risk_factors.append("Kill switch active")
        
        if context.get("safety", {}).get("daily_loss_limit_reached"):
            risk_factors.append("Daily loss limit reached")
        
        # Check market conditions
        if context.get("market", {}).get("spread", 0) > 50:
            risk_factors.append("High spread")
        
        if context.get("market", {}).get("news_impact") == "HIGH":
            risk_factors.append("High impact news")
        
        # Check analysis confidence
        if analysis.confidence < 0.5:
            risk_factors.append("Low analysis confidence")
        
        return "; ".join(risk_factors) if risk_factors else "No significant risks detected"
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text."""
        try:
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)
        except:
            return {}
    
    # ─── Trace Management ──────────────────────────────────────────────────────
    
    def get_trace(self, trace_id: str) -> Optional[ReasoningTrace]:
        return self._traces.get(trace_id)
    
    def list_traces(self, limit: int = 50) -> List[ReasoningTrace]:
        traces = list(self._traces.values())
        traces.sort(key=lambda t: t.started_at, reverse=True)
        return traces[:limit]
    
    def save_trace(self, trace: ReasoningTrace, path: str = None) -> str:
        path = path or str(REASONING_DIR / f"trace_{trace.id}.json")
        with open(path, 'w') as f:
            json.dump(trace.to_dict(), f, indent=2)
        return path
    
    def get_recent_thoughts(self, count: int = 20) -> List[Thought]:
        return self._thought_chain[-count:]
    
    def clear_thought_chain(self):
        self._thought_chain.clear()


# ─── OpenRouter Client (Nemotron 3 Ultra) ──────────────────────────────────────

def create_openrouter_client(api_key: str, model: str = "nvidia/nemotron-3-ultra-550b-a55b:free") -> Callable[[str], Dict[str, Any]]:
    """Create an OpenRouter client for Nemotron 3 Ultra."""
    import requests
    
    def client(prompt: str) -> Dict[str, Any]:
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/ahfmes-are",
                    "X-Title": "AHFMES-ARE Autonomous Reasoner"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are an autonomous trading agent. Always output valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000,
                    "response_format": {"type": "json_object"}
                },
                timeout=60
            )
            
            if response.status_code != 200:
                return {"success": False, "error": f"API error: {response.status_code} - {response.text}"}
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return {"success": True, "content": content}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    return client


# ─── Module Exports ──────────────────────────────────────────────────────────────

__all__ = [
    'ReasoningType',
    'ConfidenceLevel',
    'Thought',
    'ReasoningTrace',
    'REASONING_PROMPTS',
    'AutonomousReasoner',
    'create_openrouter_client',
]