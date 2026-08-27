"""
Unit Tests for AHFMES ARE-3 Search Tree & Budget Engine (ACC-301, ACC-302)
"""

import unittest
from are.search_tree import BudgetExhaustedError, ProgramBudget, SearchTreeEngine, SearchTreeNode


class TestSearchTreeAndBudget(unittest.TestCase):
    def test_budget_monotonic_consumption_no_reset(self):
        budget = ProgramBudget(total_budget=10.0)
        self.assertEqual(budget.total_budget, 10.0)
        self.assertEqual(budget.consumed_budget, 0.0)
        self.assertEqual(budget.remaining_budget, 10.0)
        self.assertFalse(budget.is_exhausted)

        rem = budget.consume(4.0)
        self.assertEqual(rem, 6.0)
        self.assertEqual(budget.consumed_budget, 4.0)
        self.assertFalse(budget.is_exhausted)

        rem2 = budget.consume(6.0)
        self.assertEqual(rem2, 0.0)
        self.assertEqual(budget.consumed_budget, 10.0)
        self.assertTrue(budget.is_exhausted)

        # Further consumption raises BudgetExhaustedError
        with self.assertRaises(BudgetExhaustedError):
            budget.consume(1.0)

    def test_search_tree_genealogy_and_ancestry(self):
        budget = ProgramBudget(total_budget=50.0)
        engine = SearchTreeEngine(budget=budget)

        root = engine.spawn_node(parent_node=None, hypothesis_data={"alpha": "root_hyp"}, budget_cost=5.0)
        self.assertEqual(root.depth, 0)
        self.assertIsNone(root.parent_id)
        self.assertEqual(root.family_root, root.node_id)
        self.assertEqual(budget.remaining_budget, 45.0)

        child = engine.spawn_node(parent_node=root, hypothesis_data={"alpha": "child_hyp"}, budget_cost=5.0)
        self.assertEqual(child.depth, 1)
        self.assertEqual(child.parent_id, root.node_id)
        self.assertEqual(child.family_root, root.node_id)

        grandchild = engine.spawn_node(parent_node=child, hypothesis_data={"alpha": "grandchild_hyp"}, budget_cost=5.0)
        self.assertEqual(grandchild.depth, 2)
        self.assertEqual(grandchild.parent_id, child.node_id)
        self.assertEqual(grandchild.family_root, root.node_id)

        ancestry = engine.get_ancestry(grandchild.node_id)
        self.assertEqual(len(ancestry), 3)
        self.assertEqual(ancestry[0].node_id, root.node_id)
        self.assertEqual(ancestry[1].node_id, child.node_id)
        self.assertEqual(ancestry[2].node_id, grandchild.node_id)

    def test_stopping_rule_on_budget_exhaustion(self):
        budget = ProgramBudget(total_budget=10.0)
        engine = SearchTreeEngine(budget=budget)

        root = engine.spawn_node(None, {"alpha": "h1"}, budget_cost=10.0)
        self.assertTrue(budget.is_exhausted)

        stopping = engine.evaluate_stopping_rule(root.family_root)
        self.assertEqual(stopping, "NO_EDGE_FOUND")

    def test_stopping_rule_on_consecutive_failures(self):
        budget = ProgramBudget(total_budget=100.0)
        engine = SearchTreeEngine(budget=budget, max_consecutive_failures=3)

        root = engine.spawn_node(None, {"alpha": "h1"}, budget_cost=1.0)
        n1 = engine.spawn_node(root, {"alpha": "h2"}, budget_cost=1.0)
        n2 = engine.spawn_node(root, {"alpha": "h3"}, budget_cost=1.0)
        n3 = engine.spawn_node(root, {"alpha": "h4"}, budget_cost=1.0)

        engine.record_node_outcome(n1.node_id, success=False)
        self.assertIsNone(engine.evaluate_stopping_rule(root.family_root))

        engine.record_node_outcome(n2.node_id, success=False)
        self.assertIsNone(engine.evaluate_stopping_rule(root.family_root))

        engine.record_node_outcome(n3.node_id, success=False)
        self.assertEqual(engine.evaluate_stopping_rule(root.family_root), "NO_EDGE_FOUND")


if __name__ == "__main__":
    unittest.main()
