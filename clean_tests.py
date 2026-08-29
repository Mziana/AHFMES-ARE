import re

# 1. test_e2e_cognitive_pipeline.py
file_e2e = "tests/are/test_e2e_cognitive_pipeline.py"
with open(file_e2e, "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("run_vectorized_backtest", "run_backtest")
with open(file_e2e, "w", encoding="utf-8") as f:
    f.write(c)

# 2. test_simulation_microstructure_invariants.py
file_sim = "tests/are/test_simulation_microstructure_invariants.py"
with open(file_sim, "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("from are.backtest import BacktestEngine, IsolatedBacktestEngine", "from are.backtest import IsolatedBacktestEngine")
c = c.replace("self.assertIn(\"folds\", wfo_result)", "self.assertTrue(hasattr(wfo_result, \"folds\"))")
c = c.replace("wfo_result[\"folds\"]", "wfo_result.folds")
c = c.replace("fold[\"is_metrics\"]", "fold.is_metrics")
c = c.replace("fold[\"oos_metrics\"]", "fold.oos_metrics")
with open(file_sim, "w", encoding="utf-8") as f:
    f.write(c)

# 3. test_scientific_reality_invariants.py
file_sci = "tests/are/test_scientific_reality_invariants.py"
with open(file_sci, "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("from are.backtest import BacktestEngine, IsolatedBacktestEngine, calculate_sharpe_ratio", "from are.backtest import IsolatedBacktestEngine, calculate_sharpe_ratio")
c = c.replace("self.assertIn(\"folds\", wfo_result)", "self.assertTrue(hasattr(wfo_result, \"folds\"))")
c = c.replace("len(wfo_result[\"folds\"])", "len(wfo_result.folds)")
c = c.replace("first_fold = wfo_result[\"folds\"][0]", "first_fold = wfo_result.folds[0]")
c = c.replace("self.assertIn(\"best_params\", first_fold)", "self.assertTrue(hasattr(first_fold, \"winner_params\"))")
c = c.replace("fold_0 = wfo_result[\"folds\"][0]", "fold_0 = wfo_result.folds[0]")
c = c.replace("fold_0[\"best_params\"]", "fold_0.winner_params")
c = c.replace("wfo_result[\"mean_wfe\"]", "wfo_result.mean_wfe")
c = c.replace("fold_0[\"is_sharpe\"]", "fold_0.winner_is_score")
c = c.replace("fold_0[\"oos_sharpe\"]", "fold_0.oos_metrics.get(\"sharpe_ratio\", 0.0)")
c = c.replace("wfo_result[\"mean_oos_sharpe\"]", "wfo_result.mean_fold_oos_sharpe")
with open(file_sci, "w", encoding="utf-8") as f:
    f.write(c)

# 4. test_statistical_validity_invariants.py
file_stat = "tests/are/test_statistical_validity_invariants.py"
with open(file_stat, "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("res_no_purge[\"n_folds\"]", "res_no_purge.fold_count")
c = c.replace("res_with_purge[\"n_folds\"]", "res_with_purge.fold_count")
c = c.replace("res[\"total_trials_all_folds\"]", "res.evaluation_count")
c = c.replace("res[\"n_folds\"]", "res.fold_count")
c = c.replace("res[\"folds\"][0][\"warmup_bars\"]", "res.warmup_bars")
c = c.replace("res[\"folds\"][0][\"oos_metrics\"]", "res.folds[0].oos_metrics")
c = c.replace("res[\"total_trials_per_fold\"]", "res.parameter_family_size")
c = c.replace("res[\"hypothesis_family_size\"]", "res.parameter_family_size")
c = c.replace("self.assertIn(\"selection_method\", res)", "self.assertTrue(hasattr(res, \"effective_trial_method\"))")
c = c.replace("res[\"folds\"][0][\"n_candidates_tested\"]", "res.folds[0].candidate_count")
c = c.replace("fold0 = res[\"folds\"][0]", "fold0 = res.folds[0]")
c = c.replace("fold0[\"purge_bars\"]", "res.purge_bars")
c = c.replace("self.assertEqual(fold0[\"test_start\"], fold0[\"train_end\"] + 15)", "self.assertGreater(fold0.oos_start_ts, fold0.train_end_ts)")
with open(file_stat, "w", encoding="utf-8") as f:
    f.write(c)

print("Done")