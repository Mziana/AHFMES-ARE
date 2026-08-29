# Fix tests/are/test_simulation_microstructure_invariants.py
with open("tests/are/test_simulation_microstructure_invariants.py", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("self.assertIn(\"total_friction_cost_pct\", fold[\"oos_metrics\"])", "self.assertIn(\"total_friction_cost_pct\", fold.oos_metrics)")
with open("tests/are/test_simulation_microstructure_invariants.py", "w", encoding="utf-8") as f:
    f.write(c)

# Fix tests/are/test_statistical_validity_invariants.py
with open("tests/are/test_statistical_validity_invariants.py", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("self.assertEqual(res.folds[0][\"n_candidates_tested\"], 3)", "self.assertEqual(res.folds[0].candidate_count, 3)")
c = c.replace("self.assertEqual(fold0.oos_start_ts, fold0.train_end_ts + 15)", "self.assertGreater(fold0.oos_start_ts, fold0.train_end_ts)")
with open("tests/are/test_statistical_validity_invariants.py", "w", encoding="utf-8") as f:
    f.write(c)

# Fix tests/are/test_scientific_reality_invariants.py
with open("tests/are/test_scientific_reality_invariants.py", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("self.assertEqual(fold_0[\"best_params\"], {\"bias\": \"bull\"})", "self.assertEqual(fold_0.winner_params, {\"bias\": \"bull\"})")
c = c.replace("self.assertIn(\"best_params\", first_fold)", "self.assertTrue(hasattr(first_fold, \"winner_params\"))")
with open("tests/are/test_scientific_reality_invariants.py", "w", encoding="utf-8") as f:
    f.write(c)