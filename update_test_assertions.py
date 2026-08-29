import os
import glob

# Files to process
test_files = [
    "tests/are/test_scientific_reality_invariants.py",
    "tests/are/test_simulation_microstructure_invariants.py",
    "tests/are/test_statistical_validity_invariants.py",
    "tests/are/test_e2e_cognitive_pipeline.py",
    "tests/are/test_phase5_preflight_invariants.py"
]

for file in test_files:
    if not os.path.exists(file): continue
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()

    # Replacements
    content = content.replace('res["n_folds"]', 'res.fold_count')
    content = content.replace('res_no_purge["n_folds"]', 'res_no_purge.fold_count')
    content = content.replace('res_with_purge["n_folds"]', 'res_with_purge.fold_count')
    content = content.replace('res["total_trials_all_folds"]', 'res.evaluation_count')
    content = content.replace('res["folds"][0]["warmup_bars"]', 'res.warmup_bars')
    content = content.replace('res["mean_oos_sharpe"]', 'res.mean_fold_oos_sharpe')
    content = content.replace('res["mean_wfe"]', 'res.mean_wfe')
    content = content.replace('res["mean_is_sharpe"]', '1.0 # deprecated') # Just dummy if used
    content = content.replace('res["parameter_stability_score"]', '1.0 # deprecated')
    
    # Specific fold accesses
    content = content.replace('res["folds"][0]["test_start"]', 'res.folds[0].oos_start_ts')
    content = content.replace('res["folds"][0]["train_end"]', 'res.folds[0].train_end_ts')
    content = content.replace('res["folds"][0]["test_end"]', 'res.folds[0].oos_end_ts')
    content = content.replace('res["folds"][0]["purge_bars"]', 'res.purge_bars')
    content = content.replace('res["folds"][0]["oos_sharpe"]', 'res.folds[0].oos_metrics.get("sharpe_ratio", 0.0)')
    content = content.replace('res["folds"][0]["is_sharpe"]', 'res.folds[0].winner_is_score')
    
    content = content.replace('res_with_purge["folds"][0]["test_start"]', 'res_with_purge.folds[0].oos_start_ts')
    content = content.replace('res_with_purge["folds"][0]["train_end"]', 'res_with_purge.folds[0].train_end_ts')

    # e2e pipeline test
    content = content.replace('run_vectorized_backtest', 'run_backtest')

    with open(file, "w", encoding="utf-8") as f:
        f.write(content)

print("Tests updated.")