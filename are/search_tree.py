"""
AHFMES ARE-3 — Search Tree & Budget Engine (Slice-1 Part B)

Implements:
- ProgramBudget: immutable-consumption budget envelope with strict non-resetting invariant (ACC-301).
- SearchTreeNode: genealogy node for research hypothesis trees.
- SearchTreeEngine: research genealogy management, node spawning, and deterministic stopping rules (ACC-302, SC-06, SC-12).

Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class BudgetExhaustedError(Exception):
    """Raised when an operation attempts to consume from an exhausted budget."""
    pass


class ProgramBudget:
    """
    Budget envelope with monotonic non-refundable consumption.
    Once consumed, budget cannot be refunded, reset, or bypassed (ACC-301).
    """

    def __init__(self, total_budget: float, consumed_budget: float = 0.0):
        if total_budget < 0.0:
            raise ValueError(f"Total budget cannot be negative: {total_budget}")
        if consumed_budget < 0.0:
            raise ValueError(f"Consumed budget cannot be negative: {consumed_budget}")
        self._total_budget = float(total_budget)
        self._consumed_budget = float(consumed_budget)

    @property
    def total_budget(self) -> float:
        return self._total_budget

    @property
    def consumed_budget(self) -> float:
        return self._consumed_budget

    @property
    def remaining_budget(self) -> float:
        return max(0.0, self._total_budget - self._consumed_budget)

    @property
    def is_exhausted(self) -> bool:
        return self._consumed_budget >= self._total_budget

    def consume(self, amount: float) -> float:
        """
        Consume budget amount monotonically.
        Returns the remaining budget after consumption.
        """
        if amount < 0.0:
            raise ValueError(f"Cannot consume negative budget amount: {amount}")
        if self.is_exhausted:
            raise BudgetExhaustedError("Program budget is completely exhausted")
        if self._consumed_budget + amount > self._total_budget:
            # Consume remaining and exhaust
            self._consumed_budget = self._total_budget
        else:
            self._consumed_budget += amount
        return self.remaining_budget


@dataclass(frozen=True)
class SearchTreeNode:
    node_id: str
    parent_id: Optional[str]
    family_root: str
    hypothesis_data: Dict[str, Any]
    depth: int
    status: str = "EXPLORING"
    node_hash: str = ""

    def __post_init__(self):
        if not self.node_hash:
            canonical_repr = {
                "node_id": self.node_id,
                "parent_id": self.parent_id,
                "family_root": self.family_root,
                "hypothesis_data": self.hypothesis_data,
                "depth": self.depth,
                "status": self.status,
            }
            raw = json.dumps(canonical_repr, sort_keys=True).encode("utf-8")
            digest = hashlib.sha256(raw).hexdigest()
            object.__setattr__(self, "node_hash", digest)


class SearchTreeEngine:
    """
    Manages hypothesis search trees, genealogical ancestry, and stopping rules (SC-06, SC-12).
    """

    def __init__(self, budget: ProgramBudget, max_consecutive_failures: int = 3):
        self.budget = budget
        self.max_consecutive_failures = max_consecutive_failures
        self._nodes: Dict[str, SearchTreeNode] = {}
        self._families: Dict[str, List[str]] = {}
        self._family_failures: Dict[str, int] = {}
        self._counter = 0

    def spawn_node(
        self,
        parent_node: Optional[SearchTreeNode],
        hypothesis_data: Dict[str, Any],
        budget_cost: float = 1.0,
    ) -> SearchTreeNode:
        """
        Spawns a new node in the research tree.
        Deducts budget_cost from program budget.
        """
        if self.budget.is_exhausted:
            raise BudgetExhaustedError("Cannot spawn node: program budget exhausted")

        self.budget.consume(budget_cost)
        self._counter += 1

        if parent_node is None:
            node_id = f"NODE_ROOT_{self._counter:04d}"
            parent_id = None
            family_root = node_id
            depth = 0
        else:
            node_id = f"NODE_{parent_node.node_id}_{self._counter:04d}"
            parent_id = parent_node.node_id
            family_root = parent_node.family_root
            depth = parent_node.depth + 1

        node = SearchTreeNode(
            node_id=node_id,
            parent_id=parent_id,
            family_root=family_root,
            hypothesis_data=hypothesis_data,
            depth=depth,
            status="EXPLORING",
        )

        self._nodes[node_id] = node
        self._families.setdefault(family_root, []).append(node_id)
        return node

    def record_node_outcome(self, node_id: str, success: bool) -> SearchTreeNode:
        """Updates node status based on research experiment outcome."""
        node = self._nodes.get(node_id)
        if not node:
            raise KeyError(f"Node {node_id} not found in search tree")

        new_status = "VALIDATED" if success else "PRUNED"
        updated_node = SearchTreeNode(
            node_id=node.node_id,
            parent_id=node.parent_id,
            family_root=node.family_root,
            hypothesis_data=node.hypothesis_data,
            depth=node.depth,
            status=new_status,
        )
        self._nodes[node_id] = updated_node

        fam = node.family_root
        if not success:
            self._family_failures[fam] = self._family_failures.get(fam, 0) + 1
        else:
            self._family_failures[fam] = 0

        return updated_node

    def evaluate_stopping_rule(self, family_root: str) -> Optional[str]:
        """
        Evaluates whether research in family should terminate.
        Returns "NO_EDGE_FOUND" if budget exhausted or failure threshold exceeded (ACC-302).
        """
        if self.budget.is_exhausted:
            return "NO_EDGE_FOUND"

        failures = self._family_failures.get(family_root, 0)
        if failures >= self.max_consecutive_failures:
            return "NO_EDGE_FOUND"

        return None

    def get_node(self, node_id: str) -> Optional[SearchTreeNode]:
        return self._nodes.get(node_id)

    def get_family_nodes(self, family_root: str) -> List[SearchTreeNode]:
        node_ids = self._families.get(family_root, [])
        return [self._nodes[nid] for nid in node_ids if nid in self._nodes]

    def get_ancestry(self, node_id: str) -> List[SearchTreeNode]:
        ancestry = []
        curr = self._nodes.get(node_id)
        while curr is not None:
            ancestry.append(curr)
            if curr.parent_id is None:
                break
            curr = self._nodes.get(curr.parent_id)
        return list(reversed(ancestry))
