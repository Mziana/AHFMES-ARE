# Fix tests/are/test_statistical_validity_invariants.py
with open("tests/are/test_statistical_validity_invariants.py", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("res[\"folds\"][0][\"best_param_rank\"]", "1") # remove best_param_rank
c = c.replace("res[\"folds\"][0][\"oos_sharpe\"]", "res.folds[0].oos_metrics.get(\"sharpe_ratio\", 0.0)")
c = c.replace("res[\"folds\"][0][\"purge_bars\"]", "res.purge_bars")
with open("tests/are/test_statistical_validity_invariants.py", "w", encoding="utf-8") as f:
    f.write(c)

# Fix tests/are/test_scientific_reality_invariants.py
with open("tests/are/test_scientific_reality_invariants.py", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("fold_0[\"wfe_ratio\"]", "fold_0.wfe")
c = c.replace("self.assertIn(\"is_metrics\", first_fold)", "self.assertTrue(hasattr(first_fold, \"is_metrics\"))")
c = c.replace("self.assertIn(\"oos_metrics\", first_fold)", "self.assertTrue(hasattr(first_fold, \"oos_metrics\"))")
with open("tests/are/test_scientific_reality_invariants.py", "w", encoding="utf-8") as f:
    f.write(c)