import pytest
import dataclasses
import polars as pl
from typing import Dict, Any

from are.backtest import IsolatedBacktestEngine, WFOEvidence, WFOFoldEvidence, BacktestResult
from are.preflight import Phase5PreFlightAuditor, GateStatus
from are.validation import validate_wfo_integrity

def test_oos_overlap_rejection():
    # Construct a dummy WFOEvidence with overlapping OOS periods
    f1 = WFOFoldEvidence(1, 0, 100, 101, 105, 106, 200, 2, "sr", {}, 1.0, None, None, 0, "", {}, {}, (0.01,), 1.0)
    # f2 overlaps because its oos_start (150) is before f1's oos_end (200)
    f2 = WFOFoldEvidence(2, 50, 140, 141, 145, 150, 250, 2, "sr", {}, 1.0, None, None, 0, "", {}, {}, (0.01,), 1.0)
    
    ev = WFOEvidence(
        run_id="test",
        dataset_hash="hash",
        data_start_ts=0,
        data_end_ts=250,
        folds=(f1, f2),
        fold_count=2,
        parameter_family_size=2,
        evaluation_count=4,
        effective_trial_count=2,
        effective_trial_method="M",
        effective_trial_assumption="A",
        training_overlap_ratio=0.0,
        oos_overlap_ratio=0.0,
        purge_bars=0,
        label_horizon_bars=0,
        label_horizon_unit="BARS",
        warmup_bars=0,
        pooled_oos_returns=(0.01, 0.01),
        pooled_oos_equity=(1.0, 1.0),
        pooled_oos_sharpe=1.0,
        pooled_oos_return=0.1,
        pooled_oos_max_drawdown=0.05,
        mean_fold_oos_sharpe=1.0,
        median_fold_oos_sharpe=1.0,
        worst_fold_oos_sharpe=1.0,
        std_fold_oos_sharpe=0.0,
        mean_wfe=1.0,
        median_wfe=1.0,
        worst_wfe=1.0,
        provenance_hash="dummy" # This will cause a hash mismatch anyway, but we want to check overlap count
    )
    
    res = validate_wfo_integrity(ev)
    assert not res.is_valid
    assert res.overlap_count > 0

def test_purge_violation():
    engine = IsolatedBacktestEngine()
    def dummy_factory(params):
        def logic(df):
            return df
        return logic
        
    with pytest.raises(ValueError, match="PURGE_VIOLATION"):
        engine.run_walk_forward_optimization(
            strategy_factory=dummy_factory,
            param_grid=[{"p": 1}],
            purge_bars=5,
            label_horizon_bars=10  # label_horizon > purge_bars
        )

def test_evidence_tampering_detection():
    # Construct a valid evidence but tamper with pooled_oos_sharpe
    f1 = WFOFoldEvidence(1, 0, 100, 101, 105, 106, 200, 2, "sr", {"a":1}, 1.0, None, None, 0, "", {}, {}, (0.01,), 1.0)
    ev = WFOEvidence(
        run_id="test",
        dataset_hash="hash",
        data_start_ts=0,
        data_end_ts=250,
        folds=(f1,),
        fold_count=1,
        parameter_family_size=2,
        evaluation_count=2,
        effective_trial_count=2,
        effective_trial_method="M",
        effective_trial_assumption="A",
        training_overlap_ratio=0.0,
        oos_overlap_ratio=0.0,
        purge_bars=0,
        label_horizon_bars=0,
        label_horizon_unit="BARS",
        warmup_bars=0,
        pooled_oos_returns=(0.01, 0.01),
        pooled_oos_equity=(1.0, 1.0),
        pooled_oos_sharpe=1.0,
        pooled_oos_return=0.1,
        pooled_oos_max_drawdown=0.05,
        mean_fold_oos_sharpe=1.0,
        median_fold_oos_sharpe=1.0,
        worst_fold_oos_sharpe=1.0,
        std_fold_oos_sharpe=0.0,
        mean_wfe=1.0,
        median_wfe=1.0,
        worst_wfe=1.0,
        provenance_hash="invalid" # Tampered!
    )
    
    res = validate_wfo_integrity(ev)
    assert not res.is_valid
    assert "hash mismatch" in res.fail_reason.lower()

def test_deterministic_tie_breaker(monkeypatch):
    engine = IsolatedBacktestEngine()
    
    # Mock run_backtest to return identical sharpe for 3 candidates, but different Max DD / Turnover
    def mock_run_backtest(strategy_logic, **kwargs):
        # Determine candidate by inspecting strategy_logic params closure or something
        # For simplicity, let's just make it stateful based on a counter
        if not hasattr(mock_run_backtest, "counter"):
            mock_run_backtest.counter = 0
            
        c = mock_run_backtest.counter
        mock_run_backtest.counter += 1
        
        # We have 3 candidates in train_window (IS), then 1 in test (OOS)
        # IS responses:
        if c == 0:
            metrics = {"sharpe_ratio": 2.0, "max_drawdown": 0.15, "total_turnover_count": 50}
        elif c == 1:
            metrics = {"sharpe_ratio": 2.0, "max_drawdown": 0.10, "total_turnover_count": 60} # Better max_dd
        elif c == 2:
            metrics = {"sharpe_ratio": 2.0, "max_drawdown": 0.10, "total_turnover_count": 40} # Best! Same max_dd, lower turnover
        else:
            # OOS
            metrics = {"sharpe_ratio": 1.5, "max_drawdown": 0.12, "total_turnover_count": 40}
            
        # We need equity curve and trade log for OOS
        df = pl.DataFrame({"equity": [1.0, 1.1], "strategy_return": [0.1, 0.1]})
        return BacktestResult(equity_curve=df, trade_log=pl.DataFrame(), metrics=metrics)
        
    monkeypatch.setattr(engine, "run_backtest", mock_run_backtest)
    
    def dummy_factory(params):
        def logic(df): return df
        return logic
        
    ev = engine.run_walk_forward_optimization(
        strategy_factory=dummy_factory,
        param_grid=[{"id": 1}, {"id": 2}, {"id": 3}],
        train_window_bars=10,
        test_window_bars=5,
        step_bars=1000 # Only 1 fold
    )
    
    # Candidate 3 should win because it has lowest max_dd (0.10) and then lowest turnover (40)
    assert ev.folds[0].winner_params["id"] == 3
    assert ev.folds[0].tie_count == 3

def test_final_gate_permutations():
    auditor = Phase5PreFlightAuditor(None, None, None, None, None)
    
    # 1. wfo_evidence = None -> INVALID
    res1 = auditor.audit_checkpoint_5_institutional_rigor(wfo_evidence=None)
    assert res1.passed == False
    assert res1.details["gate_status"] == GateStatus.INVALID.value
    
    # Helper to create valid evidence with modifiable fields
    def make_ev(pooled_sharpe, p_val_adjust=False):
        f1 = WFOFoldEvidence(1, 0, 100, 101, 105, 106, 200, 2, "sr", {"a":1}, 1.0, None, None, 0, "", {}, {}, (0.01,), 1.0)
        # Adjust evaluation count so DSR passes/fails
        ev_count = 1 if p_val_adjust else 100000 
        
        # Calculate proper hash
        import json, hashlib
        data_dict = {
            "folds": [
                {
                    "winner_params": f1.winner_params,
                    "oos_sharpe": f1.oos_metrics.get("sharpe_ratio", 0.0)
                }
            ],
            "pooled_sharpe": pooled_sharpe
        }
        computed_hash = hashlib.sha256(json.dumps(data_dict, sort_keys=True).encode()).hexdigest()
        
        return WFOEvidence(
            run_id="test",
            dataset_hash="hash",
            data_start_ts=0,
            data_end_ts=250,
            folds=(f1,),
            fold_count=1,
            parameter_family_size=ev_count,
            evaluation_count=ev_count,
            effective_trial_count=ev_count,
            effective_trial_method="M",
            effective_trial_assumption="A",
            training_overlap_ratio=0.0,
            oos_overlap_ratio=0.0,
            purge_bars=0,
            label_horizon_bars=0,
            label_horizon_unit="BARS",
            warmup_bars=0,
            pooled_oos_returns=tuple([0.01]*1000), # Enough obs
            pooled_oos_equity=tuple([1.0]*1000),
            pooled_oos_sharpe=pooled_sharpe,
            pooled_oos_return=0.1,
            pooled_oos_max_drawdown=0.05,
            mean_fold_oos_sharpe=1.0,
            median_fold_oos_sharpe=1.0,
            worst_fold_oos_sharpe=1.0,
            std_fold_oos_sharpe=0.0,
            mean_wfe=1.0,
            median_wfe=1.0,
            worst_wfe=1.0,
            provenance_hash=computed_hash
        )
    
    # 2. FAIL due to DSR
    ev2 = make_ev(pooled_sharpe=0.1, p_val_adjust=False) # High trials, low sharpe -> bad DSR p-val
    res2 = auditor.audit_checkpoint_5_institutional_rigor(wfo_evidence=ev2)
    assert res2.passed == False
    assert res2.details["gate_status"] == GateStatus.FAIL.value
    
    # 3. BORDERLINE due to Performance
    ev3 = make_ev(pooled_sharpe=0.9, p_val_adjust=True) # Low trials, passes DSR, but sharpe < 1.0 fails Perf
    res3 = auditor.audit_checkpoint_5_institutional_rigor(wfo_evidence=ev3)
    assert res3.passed == False
    assert res3.details["gate_status"] == GateStatus.BORDERLINE.value
    
    # 4. PASS
    ev4 = make_ev(pooled_sharpe=2.5, p_val_adjust=True) 
    res4 = auditor.audit_checkpoint_5_institutional_rigor(wfo_evidence=ev4)
    assert res4.passed == True
    assert res4.details["gate_status"] == GateStatus.PASS.value