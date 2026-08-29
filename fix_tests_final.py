# Fix tests/are/test_simulation_microstructure_invariants.py
with open("tests/are/test_simulation_microstructure_invariants.py", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("wfo_result[\"folds\"]", "wfo_result.folds")
with open("tests/are/test_simulation_microstructure_invariants.py", "w", encoding="utf-8") as f:
    f.write(c)

# Fix tests/are/test_statistical_validity_invariants.py
with open("tests/are/test_statistical_validity_invariants.py", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("res[\"hypothesis_family_size\"]", "res.parameter_family_size")
c = c.replace("fold0[\"purge_bars\"]", "res.purge_bars")
c = c.replace("res.folds[0][\"oos_metrics\"]", "res.folds[0].oos_metrics")
with open("tests/are/test_statistical_validity_invariants.py", "w", encoding="utf-8") as f:
    f.write(c)

# Fix tests/are/test_scientific_reality_invariants.py
with open("tests/are/test_scientific_reality_invariants.py", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("len(wfo_result[\"folds\"])", "len(wfo_result.folds)")
c = c.replace("self.assertIn(\"folds\", wfo_result)", "self.assertTrue(hasattr(wfo_result, \"folds\"))")
with open("tests/are/test_scientific_reality_invariants.py", "w", encoding="utf-8") as f:
    f.write(c)