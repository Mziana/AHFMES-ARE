# Fix tests/are/test_statistical_validity_invariants.py
with open("tests/are/test_statistical_validity_invariants.py", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("self.assertEqual(old_res.fold_count, new_res.fold_count)", "self.assertEqual(old_res[\"n_folds\"], new_res[\"n_folds\"])")
c = c.replace("self.assertEqual(old_res.mean_fold_oos_sharpe, new_res.mean_fold_oos_sharpe)", "self.assertEqual(old_res[\"mean_oos_sharpe\"], new_res[\"mean_oos_sharpe\"])")
with open("tests/are/test_statistical_validity_invariants.py", "w", encoding="utf-8") as f:
    f.write(c)

# Fix tests/are/test_scientific_reality_invariants.py
with open("tests/are/test_scientific_reality_invariants.py", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("self.assertIn(\"wfe_ratio\", first_fold)", "self.assertTrue(hasattr(first_fold, \"wfe\"))")
with open("tests/are/test_scientific_reality_invariants.py", "w", encoding="utf-8") as f:
    f.write(c)