import pytest
import dataclasses
from are.backtest import WFOEvidence, WFOFoldEvidence
from are.validation import validate_wfo_integrity

def create_valid_evidence():
    # Setup dummy WFOEvidence with a known valid hash
    from are.backtest import build_wfo_provenance_payload
    import hashlib
    import json
    import math

    folds = (
        WFOFoldEvidence(1, 0, 100, 101, 105, 106, 200, 2, "sr", {"a":1}, 1.0, None, None, 0, "", {}, {"sharpe_ratio": 1.0}, (0.01,), 1.0),
    )
    
    evidence = WFOEvidence(
        run_id="test_run",
        dataset_hash="hash_data",
        timeframe_seconds=60.0,
        data_start_ts=100.0,
        data_end_ts=300.0,
        folds=folds,
        fold_count=1,
        parameter_family_size=10,
        evaluation_count=10,
        effective_trial_count=10,
        effective_trial_method="MOCK",
        effective_trial_assumption="MOCK",
        training_overlap_ratio=0.0,
        oos_overlap_ratio=0.0,
        purge_bars=0,
        label_horizon_bars=1,
        label_horizon_unit="BARS",
        warmup_bars=0,
        pooled_oos_returns=(0.01, 0.02, -0.01),
        pooled_oos_equity=(1.01, 1.0302, 1.0199),
        pooled_oos_sharpe=1.5,
        pooled_oos_return=0.0199,
        pooled_oos_max_drawdown=0.01,
        mean_fold_oos_sharpe=1.5,
        median_fold_oos_sharpe=1.5,
        worst_fold_oos_sharpe=1.5,
        std_fold_oos_sharpe=0.0,
        mean_wfe=0.75,
        median_wfe=0.75,
        worst_wfe=0.75,
        provenance_hash=""
    )
    
    # We must construct a valid hash via the exact recompute logic of validation.py
    # Recompute invariants
    cum_eq = 1.0
    peak = 1.0
    calc_max_dd = 0.0
    for r in evidence.pooled_oos_returns:
        cum_eq *= (1.0 + r)
        if cum_eq > peak:
            peak = cum_eq
        dd = (peak - cum_eq) / peak if peak > 0.0 else 0.0
        if dd > calc_max_dd:
            calc_max_dd = dd
    calc_return = cum_eq - 1.0
    
    from are.backtest import calculate_sharpe_ratio
    calc_sharpe = calculate_sharpe_ratio(list(evidence.pooled_oos_returns), timeframe_seconds=60.0)
    
    recomputed_evidence = dataclasses.replace(
        evidence,
        pooled_oos_return=calc_return,
        pooled_oos_max_drawdown=calc_max_dd,
        pooled_oos_sharpe=calc_sharpe
    )
    
    payload = build_wfo_provenance_payload(recomputed_evidence)
    calc_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()
    
    # Also inject the correctly recomputed values into the "saved" evidence to simulate what a real backtest outputs
    return dataclasses.replace(
        evidence, 
        pooled_oos_return=calc_return,
        pooled_oos_max_drawdown=calc_max_dd,
        pooled_oos_sharpe=calc_sharpe,
        provenance_hash=calc_hash
    )

def test_wfo_mutation_invariants():
    base_evidence = create_valid_evidence()
    
    # 1. Base should be valid
    res = validate_wfo_integrity(base_evidence)
    assert res.is_valid, f"Base evidence invalid: {res.fail_reason}"
    
    # 2. Mutate pooled_oos_returns
    mutated_returns = list(base_evidence.pooled_oos_returns)
    mutated_returns[0] = 0.99  # fake large return
    mutated_ev_1 = dataclasses.replace(base_evidence, pooled_oos_returns=tuple(mutated_returns))
    res_1 = validate_wfo_integrity(mutated_ev_1)
    assert not res_1.is_valid, "Mutation in pooled_oos_returns should be detected"
    
    # 3. Mutate max_drawdown in payload
    mutated_ev_2 = dataclasses.replace(base_evidence, pooled_oos_max_drawdown=0.0)
    # Mutating max_drawdown without modifying the provenance hash doesn't fail directly in our recompute,
    # because validate_wfo_integrity recalculates the hash from the TRUE pooled_oos_returns. 
    # To truly bypass it, an attacker would have to replace BOTH max_drawdown AND provenance_hash, 
    # but the hash must match the fake max_drawdown payload!
    from are.backtest import build_wfo_provenance_payload
    import hashlib, json
    payload = build_wfo_provenance_payload(mutated_ev_2)
    fake_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()
    mutated_ev_2_fake_hash = dataclasses.replace(mutated_ev_2, provenance_hash=fake_hash)
    
    res_2 = validate_wfo_integrity(mutated_ev_2_fake_hash)
    assert not res_2.is_valid, "Mutation in max_drawdown + fake hash should be detected"

    # 4. Mutate winner_params
    folds = list(base_evidence.folds)
    folds[0] = dataclasses.replace(folds[0], winner_params={"period": 99})
    mutated_ev_3 = dataclasses.replace(base_evidence, folds=tuple(folds))
    res_3 = validate_wfo_integrity(mutated_ev_3)
    assert not res_3.is_valid, "Mutation in winner_params should be detected"
