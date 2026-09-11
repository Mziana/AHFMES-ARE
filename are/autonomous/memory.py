"""
Autonomous Memory System — Episodic + Semantic + Working Memory
Tier 1: Episodic (EventStore - immutable, append-only)
Tier 2: Semantic (SQLite - facts, patterns, rules)
Tier 3: Working (in-memory - current context, goals, scratchpad)
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import hashlib
from enum import Enum


# ─── Memory Tier Enum ────────────────────────────────────────────────────────────

class MemoryTier(Enum):
    """Memory tier classification."""
    EPISODIC = "episodic"      # Tier 1: Immutable event log (EventStore)
    SEMANTIC = "semantic"      # Tier 2: Facts, patterns, rules (SQLite)
    WORKING = "working"        # Tier 3: Current context, goals, scratchpad


# ─── Configuration ──────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "autonomous"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EPISODIC_DB = DATA_DIR / "episodic.db"  # EventStore backed
SEMANTIC_DB = DATA_DIR / "semantic.db"  # Knowledge/facts
WORKING_DIR = DATA_DIR / "working"       # Current session scratchpad
WORKING_DIR.mkdir(exist_ok=True)


# ─── Episodic Memory (EventStore backed) ────────────────────────────────────────

@dataclass(frozen=True)
class EpisodicEvent:
    """Immutable event from EventStore - never modified after creation."""
    stream_id: str
    revision: int
    event_hash: str
    timestamp: float
    payload: Dict[str, Any]
    prev_hash: str


class EpisodicMemory:
    """
    Read-only view of EventStore for autonomous reasoning.
    Provides query interface over immutable event log.
    """
    
    def __init__(self, event_store_path: str = None):
        # We read from the main ARE EventStore
        self.event_store_path = event_store_path or str(
            Path(__file__).resolve().parents[1] / "are_interactive.db"
        )
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
    
    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            with self._lock:
                if self._conn is None:
                    self._conn = sqlite3.connect(self.event_store_path, check_same_thread=False)
                    self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def get_stream_events(
        self, 
        stream_id: str, 
        since_revision: int = 0, 
        limit: int = 100
    ) -> List[EpisodicEvent]:
        """Get events from a specific stream."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT stream_id, revision, event_hash, timestamp, payload, prev_hash
            FROM events
            WHERE stream_id = ? AND revision > ?
            ORDER BY revision ASC
            LIMIT ?
            """,
            (stream_id, since_revision, limit)
        )
        rows = cursor.fetchall()
        
        events = []
        for row in rows:
            payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
            events.append(EpisodicEvent(
                stream_id=row["stream_id"],
                revision=row["revision"],
                event_hash=row["event_hash"],
                timestamp=row["timestamp"],
                payload=payload,
                prev_hash=row["prev_hash"]
            ))
        return events
    
    def get_recent_events(self, stream_ids: List[str], limit_per_stream: int = 50) -> Dict[str, List[EpisodicEvent]]:
        """Get recent events from multiple streams."""
        result = {}
        for stream_id in stream_ids:
            result[stream_id] = self.get_stream_events(stream_id, limit=limit_per_stream)
        return result
    
    def get_trade_history(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Get recent trade events from evidence_ledger and operational_signals."""
        conn = self._get_conn()
        
        # Get from evidence_ledger
        cursor = conn.execute(
            "SELECT payload FROM events WHERE stream_id = 'evidence_ledger' ORDER BY revision DESC LIMIT ?",
            (limit,)
        )
        trades = []
        for row in cursor.fetchall():
            payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
            trades.append(payload)
        
        return trades
    
    def get_champion_history(self) -> List[Dict[str, Any]]:
        """Get champion promotion/demotion history."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT payload FROM events WHERE stream_id = 'champion_registry' ORDER BY revision ASC"
        )
        champs = []
        for row in cursor.fetchall():
            payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
            champs.append(payload)
        return champs


# ─── Semantic Memory (SQLite - facts, patterns, rules) ──────────────────────────

@dataclass
class SemanticFact:
    """A learned fact/pattern/rule with confidence and provenance."""
    id: Optional[int]
    category: str          # 'pattern', 'rule', 'parameter', 'regime', 'lesson', 'strategy'
    key: str               # Unique identifier for this fact
    content: str           # Human-readable description
    data: Dict[str, Any]   # Structured data
    confidence: float      # 0.0 - 1.0
    source: str            # 'trade', 'backtest', 'champion', 'web', 'self_discovered'
    evidence_refs: List[str]  # Event hashes that support this fact
    created_at: float
    updated_at: float
    access_count: int = 0
    last_accessed: float = 0


class SemanticMemory:
    """
    Long-term factual memory for patterns, rules, and learned knowledge.
    Supports CRUD, similarity search, and confidence-weighted retrieval.
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(SEMANTIC_DB)
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
        self._init_db()
    
    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            with self._lock:
                if self._conn is None:
                    self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
                    self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS semantic_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL,
                data TEXT NOT NULL DEFAULT '{}',
                confidence REAL NOT NULL DEFAULT 0.5,
                source TEXT NOT NULL DEFAULT 'self_discovered',
                evidence_refs TEXT NOT NULL DEFAULT '[]',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                access_count INTEGER NOT NULL DEFAULT 0,
                last_accessed REAL NOT NULL DEFAULT 0
            );
            
            CREATE INDEX IF NOT EXISTS idx_semantic_category ON semantic_facts(category);
            CREATE INDEX IF NOT EXISTS idx_semantic_confidence ON semantic_facts(confidence DESC);
            CREATE INDEX IF NOT EXISTS idx_semantic_key ON semantic_facts(key);
            CREATE INDEX IF NOT EXISTS idx_semantic_updated ON semantic_facts(updated_at DESC);
            
            CREATE VIRTUAL TABLE IF NOT EXISTS semantic_fts USING fts5(
                key, content, category,
                content='semantic_facts',
                content_rowid='id',
                tokenize='porter unicode61'
            );
            
            CREATE TRIGGER IF NOT EXISTS semantic_ai AFTER INSERT ON semantic_facts BEGIN
                INSERT INTO semantic_fts(rowid, key, content, category)
                VALUES (new.id, new.key, new.content, new.category);
            END;
            
            CREATE TRIGGER IF NOT EXISTS semantic_ad AFTER DELETE ON semantic_facts BEGIN
                INSERT INTO semantic_fts(semantic_fts, rowid, key, content, category)
                VALUES ('delete', old.id, old.key, old.content, old.category);
            END;
            
            CREATE TRIGGER IF NOT EXISTS semantic_au AFTER UPDATE ON semantic_facts BEGIN
                INSERT INTO semantic_fts(semantic_fts, rowid, key, content, category)
                VALUES ('delete', old.id, old.key, old.content, old.category);
                INSERT INTO semantic_fts(rowid, key, content, category)
                VALUES (new.id, new.key, new.content, new.category);
            END;
        """)
        conn.commit()
    
    def add_fact(
        self,
        category: str,
        key: str,
        content: str,
        data: Dict[str, Any] = None,
        confidence: float = 0.5,
        source: str = 'self_discovered',
        evidence_refs: List[str] = None
    ) -> int:
        """Add or update a semantic fact."""
        now = time.time()
        conn = self._get_conn()
        
        # Check if exists
        existing = conn.execute(
            "SELECT id, confidence, evidence_refs FROM semantic_facts WHERE key = ?",
            (key,)
        ).fetchone()
        
        if existing:
            # Merge: update confidence (weighted avg), append evidence
            old_conf = existing["confidence"]
            old_refs = json.loads(existing["evidence_refs"] or "[]")
            new_refs = list(set(old_refs + (evidence_refs or [])))
            
            # Weighted confidence update
            merged_conf = (old_conf + confidence) / 2
            
            conn.execute(
                """
                UPDATE semantic_facts SET
                    content = ?, data = ?, confidence = ?, source = ?,
                    evidence_refs = ?, updated_at = ?, access_count = access_count + 1
                WHERE key = ?
                """,
                (content, json.dumps(data or {}), merged_conf, source,
                 json.dumps(new_refs), now, key)
            )
            fact_id = existing["id"]
        else:
            cursor = conn.execute(
                """
                INSERT INTO semantic_facts
                (category, key, content, data, confidence, source, evidence_refs, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (category, key, content, json.dumps(data or {}), confidence,
                 source, json.dumps(evidence_refs or []), now, now)
            )
            fact_id = cursor.lastrowid
        
        conn.commit()
        return fact_id
    
    def get_fact(self, key: str) -> Optional[SemanticFact]:
        """Get a fact by key."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM semantic_facts WHERE key = ?", (key,)
        ).fetchone()
        
        if not row:
            return None
        
        # Update access stats
        conn.execute(
            "UPDATE semantic_facts SET access_count = access_count + 1, last_accessed = ? WHERE key = ?",
            (time.time(), key)
        )
        conn.commit()
        
        return self._row_to_fact(row)
    
    def query_facts(
        self,
        category: str = None,
        min_confidence: float = 0.0,
        limit: int = 50,
        order_by: str = 'confidence'
    ) -> List[SemanticFact]:
        """Query facts with filters."""
        conn = self._get_conn()
        
        where = ["1=1"]
        params = []
        
        if category:
            where.append("category = ?")
            params.append(category)
        if min_confidence > 0:
            where.append("confidence >= ?")
            params.append(min_confidence)
        
        order_map = {
            'confidence': 'confidence DESC',
            'updated': 'updated_at DESC',
            'created': 'created_at DESC',
            'access': 'access_count DESC'
        }
        order = order_map.get(order_by, 'confidence DESC')
        
        params.append(limit)
        
        cursor = conn.execute(
            f"SELECT * FROM semantic_facts WHERE {' AND '.join(where)} ORDER BY {order} LIMIT ?",
            params
        )
        
        return [self._row_to_fact(row) for row in cursor.fetchall()]
    
    def search_facts(self, query: str, limit: int = 20) -> List[Tuple[SemanticFact, float]]:
        """Full-text search with BM25 ranking."""
        conn = self._get_conn()
        
        terms = query.lower().split()
        fts_query = " OR ".join(f'"{t}"*' for t in terms if len(t) > 2)
        
        if not fts_query:
            return []
        
        cursor = conn.execute(
            """
            SELECT sf.*, bm25(semantic_fts) as bm25_score
            FROM semantic_fts
            JOIN semantic_facts sf ON sf.id = semantic_fts.rowid
            WHERE semantic_fts MATCH ?
            ORDER BY bm25_score
            LIMIT ?
            """,
            (fts_query, limit)
        )
        
        results = []
        for row in cursor.fetchall():
            fact = self._row_to_fact(row)
            score = max(0, 1 - (row["bm25_score"] / 10))
            results.append((fact, score))
        
        return results
    
    def update_confidence(self, key: str, delta: float, evidence_ref: str = None) -> bool:
        """Adjust confidence of a fact (for reinforcement learning)."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT confidence, evidence_refs FROM semantic_facts WHERE key = ?", (key,)
        ).fetchone()
        
        if not row:
            return False
        
        new_conf = max(0.0, min(1.0, row["confidence"] + delta))
        refs = json.loads(row["evidence_refs"] or "[]")
        if evidence_ref and evidence_ref not in refs:
            refs.append(evidence_ref)
        
        conn.execute(
            "UPDATE semantic_facts SET confidence = ?, evidence_refs = ?, updated_at = ? WHERE key = ?",
            (new_conf, json.dumps(refs), time.time(), key)
        )
        conn.commit()
        return True
    
    def _row_to_fact(self, row: sqlite3.Row) -> SemanticFact:
        return SemanticFact(
            id=row["id"],
            category=row["category"],
            key=row["key"],
            content=row["content"],
            data=json.loads(row["data"] or "{}"),
            confidence=row["confidence"],
            source=row["source"],
            evidence_refs=json.loads(row["evidence_refs"] or "[]"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            access_count=row["access_count"],
            last_accessed=row["last_accessed"]
        )
    
    def get_stats(self) -> Dict[str, Any]:
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) as c FROM semantic_facts").fetchone()["c"]
        by_cat = conn.execute(
            "SELECT category, COUNT(*) as c FROM semantic_facts GROUP BY category"
        ).fetchall()
        by_source = conn.execute(
            "SELECT source, COUNT(*) as c FROM semantic_facts GROUP BY source"
        ).fetchall()
        avg_conf = conn.execute(
            "SELECT AVG(confidence) as c FROM semantic_facts"
        ).fetchone()["c"]
        
        return {
            "total": total,
            "by_category": {r["category"]: r["c"] for r in by_cat},
            "by_source": {r["source"]: r["c"] for r in by_source},
            "avg_confidence": round(avg_conf or 0, 3)
        }


# ─── Working Memory (In-memory scratchpad for current session) ──────────────────

@dataclass
class WorkingMemory:
    """
    Current session context - goals, active tasks, scratchpad, recent observations.
    Reset on each autonomous cycle / session.
    """
    session_id: str
    started_at: float = field(default_factory=time.time)
    
    # Goal stack (current objectives)
    goals: List[Dict[str, Any]] = field(default_factory=list)
    
    # Active task decomposition
    task_graph: Dict[str, Any] = field(default_factory=dict)
    
    # Scratchpad for intermediate reasoning
    scratchpad: Dict[str, Any] = field(default_factory=dict)
    
    # Recent observations from current cycle
    observations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Hypotheses being tested
    hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    
    # Current market context
    market_context: Dict[str, Any] = field(default_factory=dict)
    
    # Performance tracking for this session
    cycle_count: int = 0
    decisions_made: int = 0
    tools_used: Dict[str, int] = field(default_factory=dict)
    
    def add_observation(self, source: str, data: Dict[str, Any]):
        self.observations.append({
            "source": source,
            "data": data,
            "timestamp": time.time()
        })
        # Keep last 100
        if len(self.observations) > 100:
            self.observations = self.observations[-100:]
    
    def set_goal(self, goal: str, priority: int = 1, metadata: Dict = None):
        self.goals.append({
            "goal": goal,
            "priority": priority,
            "metadata": metadata or {},
            "created_at": time.time(),
            "status": "active"
        })
        self.goals.sort(key=lambda g: -g["priority"])
    
    def complete_goal(self, goal: str):
        for g in self.goals:
            if g["goal"] == goal and g["status"] == "active":
                g["status"] = "completed"
                g["completed_at"] = time.time()
                break
    
    def add_hypothesis(self, hypothesis: str, test_plan: Dict = None):
        self.hypotheses.append({
            "hypothesis": hypothesis,
            "test_plan": test_plan or {},
            "status": "pending",
            "created_at": time.time()
        })
    
    def record_tool_use(self, tool: str):
        self.tools_used[tool] = self.tools_used.get(tool, 0) + 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "goals": self.goals,
            "task_graph": self.task_graph,
            "scratchpad": self.scratchpad,
            "observations": self.observations[-20:],  # Recent only
            "hypotheses": self.hypotheses,
            "market_context": self.market_context,
            "cycle_count": self.cycle_count,
            "decisions_made": self.decisions_made,
            "tools_used": self.tools_used
        }
    
    def save(self, path: str = None):
        path = path or str(WORKING_DIR / f"working_{self.session_id}.json")
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: str) -> 'WorkingMemory':
        with open(path, 'r') as f:
            data = json.load(f)
        wm = cls(session_id=data["session_id"])
        wm.started_at = data.get("started_at", time.time())
        wm.goals = data.get("goals", [])
        wm.task_graph = data.get("task_graph", {})
        wm.scratchpad = data.get("scratchpad", {})
        wm.observations = data.get("observations", [])
        wm.hypotheses = data.get("hypotheses", [])
        wm.market_context = data.get("market_context", {})
        wm.cycle_count = data.get("cycle_count", 0)
        wm.decisions_made = data.get("decisions_made", 0)
        wm.tools_used = data.get("tools_used", {})
        return wm


# ─── Unified Memory Interface ──────────────────────────────────────────────────

class AutonomousMemory:
    """
    Unified memory interface combining all three tiers.
    Provides high-level operations for autonomous reasoning.
    """
    
    def __init__(self, event_store_path: str = None):
        self.episodic = EpisodicMemory(event_store_path)
        self.semantic = SemanticMemory()
        self.working: Optional[WorkingMemory] = None
        self._current_session_id: Optional[str] = None
    
    def start_session(self, session_id: str = None) -> WorkingMemory:
        """Start a new working memory session."""
        self._current_session_id = session_id or f"session_{int(time.time())}"
        self.working = WorkingMemory(session_id=self._current_session_id)
        return self.working
    
    def end_session(self) -> Optional[Dict]:
        """End current session, persist working memory."""
        if self.working:
            self.working.save()
            summary = self.working.to_dict()
            self.working = None
            return summary
        return None
    
    def get_working(self) -> Optional[WorkingMemory]:
        return self.working
    
    # High-level memory operations
    
    def learn_from_trade(self, trade_event: Dict[str, Any]) -> List[str]:
        """Extract and store patterns from a completed trade."""
        learned_keys = []
        
        # Extract regime/pattern combination
        if "fp" in trade_event:
            fp = trade_event["fp"]
            style = trade_event.get("style", "unknown")
            direction = fp.get("_dir") or fp.get("direction", "unknown")
            win = trade_event.get("win", 0)
            pnl = trade_event.get("pnl", 0)
            
            # Build pattern key
            pattern_key = f"trade_pattern|{style}|{direction}|{fp.get('master')}|{fp.get('m5_rsi')}|{fp.get('m5_atr')}"
            
            self.semantic.add_fact(
                category="pattern",
                key=pattern_key,
                content=f"{style} {direction} in {fp.get('master')} regime: {'WIN' if win else 'LOSS'} ({pnl})",
                data={
                    "style": style,
                    "direction": direction,
                    "master_regime": fp.get('master'),
                    "rsi_bucket": fp.get('m5_rsi'),
                    "atr_bucket": fp.get('m5_atr'),
                    "win": bool(win),
                    "pnl": pnl
                },
                confidence=0.6 if win else 0.4,
                source="trade",
                evidence_refs=[trade_event.get("event_hash", "")]
            )
            learned_keys.append(pattern_key)
        
        return learned_keys
    
    def learn_from_backtest(self, backtest_result: Dict[str, Any]) -> List[str]:
        """Extract strategy-level insights from backtest."""
        learned_keys = []
        
        metrics = backtest_result.get("results", {})
        config = backtest_result.get("config", {})
        strategy_name = backtest_result.get("strategyName", "unknown")
        
        key = f"strategy_perf|{strategy_name}|{config.get('symbol')}|{config.get('timeframe')}"
        
        self.semantic.add_fact(
            category="strategy",
            key=key,
            content=f"{strategy_name} on {config.get('symbol')} {config.get('timeframe')}: WR={metrics.get('winRate')}% PF={metrics.get('profitFactor')} Sharpe={metrics.get('sharpe')}",
            data={
                "strategy": strategy_name,
                "symbol": config.get('symbol'),
                "timeframe": config.get('timeframe'),
                "metrics": metrics
            },
            confidence=min(0.5 + (metrics.get('sharpe', 0) * 0.1), 0.95),
            source="backtest",
            evidence_refs=[backtest_result.get("id", "")]
        )
        learned_keys.append(key)
        
        return learned_keys
    
    def get_relevant_context(self, query: str, categories: List[str] = None) -> Dict[str, Any]:
        """Get relevant memories for a query/reasoning task."""
        if categories is None:
            categories = ['pattern', 'rule', 'regime', 'lesson', 'strategy']
        
        context = {
            "semantic_facts": [],
            "episodic_summary": {},
            "working_scratchpad": self.working.scratchpad if self.working else {}
        }
        
        # Semantic search
        for cat in categories:
            facts = self.semantic.query_facts(category=cat, min_confidence=0.5, limit=10)
            context["semantic_facts"].extend([{
                "category": f.category,
                "key": f.key,
                "content": f.content,
                "confidence": f.confidence,
                "data": f.data
            } for f in facts])
        
        # Also search by query
        search_results = self.semantic.search_facts(query, limit=10)
        context["semantic_facts"].extend([{
            "category": f.category,
            "key": f.key,
            "content": f.content,
            "confidence": f.confidence,
            "data": f.data,
            "relevance": score
        } for f, score in search_results])
        
        # Recent episodic summary
        recent = self.episodic.get_recent_events([
            'evidence_ledger', 'operational_signals', 'champion_registry'
        ], limit_per_stream=20)
        context["episodic_summary"] = {
            stream: len(events) for stream, events in recent.items()
        }
        
        return context
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "semantic": self.semantic.get_stats(),
            "working_session": self._current_session_id,
            "working_cycles": self.working.cycle_count if self.working else 0
        }


# ─── Module Exports ──────────────────────────────────────────────────────────────

__all__ = [
    'EpisodicMemory',
    'EpisodicEvent',
    'SemanticMemory',
    'SemanticFact',
    'WorkingMemory',
    'AutonomousMemory',
]