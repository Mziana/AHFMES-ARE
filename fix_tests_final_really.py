# Fix tests/are/test_simulation_microstructure_invariants.py
with open("tests/are/test_simulation_microstructure_invariants.py", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("self.assertIn(\"total_friction_cost_pct\", fold[\"is_metrics\"])", "self.assertIn(\"total_friction_cost_pct\", fold.is_metrics)")
c = c.replace("fold[\"is_metrics\"]", "fold.is_metrics")
with open("tests/are/test_simulation_microstructure_invariants.py", "w", encoding="utf-8") as f:
    f.write(c)

# Fix tests/are/test_statistical_validity_invariants.py
with open("tests/are/test_statistical_validity_invariants.py", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("self.assertIn(\"selection_method\", res)", "self.assertTrue(hasattr(res, \"effective_trial_method\"))")
c = c.replace("fold0[\"test_start\"]", "fold0.oos_start_ts")
c = c.replace("fold0[\"train_end\"]", "fold0.train_end_ts")
with open("tests/are/test_statistical_validity_invariants.py", "w", encoding="utf-8") as f:
    f.write(c)

# Fix tests/are/test_scientific_reality_invariants.py
with open("tests/are/test_scientific_reality_invariants.py", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("wfo_result[\"folds\"][0]", "wfo_result.folds[0]")
c = c.replace("first_fold[\"winner_params\"]", "first_fold.winner_params")
c = c.replace("first_fold[\"is_sharpe\"]", "first_fold.winner_is_score")
c = c.replace("first_fold[\"oos_sharpe\"]", "first_fold.oos_metrics.get(\"sharpe_ratio\", 0.0)")
c = c.replace("wfo_result[\"mean_oos_sharpe\"]", "wfo_result.mean_fold_oos_sharpe")

c = c.replace("fold_0[\"winner_params\"]", "fold_0.winner_params")
c = c.replace("fold_0[\"is_sharpe\"]", "fold_0.winner_is_score")
c = c.replace("fold_0[\"oos_sharpe\"]", "fold_0.oos_metrics.get(\"sharpe_ratio\", 0.0)")
c = c.replace("wfo_result[\"mean_wfe\"]", "wfo_result.mean_wfe")
with open("tests/are/test_scientific_reality_invariants.py", "w", encoding="utf-8") as f:
    f.write(c)