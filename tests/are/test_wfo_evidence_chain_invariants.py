import hashlib
import json
import dataclasses
import pytest
import polars as pl
from typing import Dict, Any

from are.backtest import (
    IsolatedBacktestEngine,
    WFOEvidence,
    WFOFoldEvidence,
    BacktestResult,
    build_wfo_provenance_payload,
)
from are.preflight import Phase5PreFlightAuditor, GateStatus
from are.validation import validate_wfo_integrity


def make_consistent_evidence(ev: WFOEvidence) -> WFOEvidence:
    import dataclasses
    from are.backtest import calculate_sharpe_ratio, build_wfo_provenance_payload
    import hashlib
    import json
    
    cum_eq = 1.0
    peak = 1.0
    calc_max_dd = 0.0
    for r in ev.pooled_oos_returns:
        cum_eq *= (1.0 + r)
        if cum_eq > peak:
            peak = cum_eq
        dd = (peak - cum_eq) / peak if peak > 0.0 else 0.0
        if dd > calc_max_dd:
            calc_max_dd = dd
    calc_return = cum_eq - 1.0
    calc_sharpe = calculate_sharpe_ratio(list(ev.pooled_oos_returns), timeframe_seconds=60.0)
    
    recomputed_ev = dataclasses.replace(
        ev,
        pooled_oos_return=calc_return,
        pooled_oos_max_drawdown=calc_max_dd,
        pooled_oos_sharpe=calc_sharpe
    )
    payload = build_wfo_provenance_payload(recomputed_ev)
    valid_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return dataclasses.replace(recomputed_ev, provenance_hash=valid_hash)

def _compute_hash(ev: WFOEvidence) -> str:
    # Deprecated fallback
    from are.backtest import build_wfo_provenance_payload
    import hashlib, json
    payload = build_wfo_provenance_payload(ev)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()


def test_oos_overlap_rejection():
    # Construct a dummy WFOEvidence with overlapping OOS periods
    f1 = WFOFoldEvidence(1, 0, 100, 101, 105, 106, 200, 2, "sr", {}, 1.0, None, None, 0, "", {}, {}, (0.01,), 1.0)
    # f2 overlaps because its oos_start (150) is before f1's oos_end (200)
    f2 = WFOFoldEvidence(2, 50, 140, 141, 145, 150, 250, 2, "sr", {}, 1.0, None, None, 0, "", {}, {}, (0.01,), 1.0)
    
    ev = WFOEvidence(
        run_id="test",
        dataset_hash="hash",
        timeframe_seconds=60.0,
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
        provenance_hash="dummy"
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
            label_horizon_bars=10
        )


def test_evidence_tampering_detection():
    # Construct a valid evidence
    f1 = WFOFoldEvidence(1, 0, 100, 101, 105, 106, 200, 2, "sr", {"a":1}, 1.0, None, None, 0, "", {}, {"sharpe_ratio": 1.0}, (0.01,), 1.0)
    ev_base = WFOEvidence(
        run_id="test",
        dataset_hash="hash",
        timeframe_seconds=60.0,
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
        provenance_hash=""
    )
    valid_ev = make_consistent_evidence(ev_base)
    
    # 1. Untampered -> Valid
    res_valid = validate_wfo_integrity(valid_ev)
    assert res_valid.is_valid

    # 2. Tamper pooled_oos_sharpe
    tampered_sharpe = dataclasses.replace(valid_ev, pooled_oos_sharpe=2.5)
    res_tampered_sharpe = validate_wfo_integrity(tampered_sharpe)
    assert not res_tampered_sharpe.is_valid
    assert "hash mismatch" in res_tampered_sharpe.fail_reason.lower()

    # 3. Tamper pooled_oos_max_drawdown (RES-WFO-15)
    tampered_dd = dataclasses.replace(valid_ev, pooled_oos_max_drawdown=0.01)
    res_tampered_dd = validate_wfo_integrity(tampered_dd)
    assert not res_tampered_dd.is_valid
    assert "hash mismatch" in res_tampered_dd.fail_reason.lower()


def test_dataset_hash_content_sensitive():
    engine = IsolatedBacktestEngine()
    df1 = pl.DataFrame({
        "timestamp": [1000 + i * 60 for i in range(50)],
        "price": [100.0 + i for i in range(50)],
    })
    df2 = pl.DataFrame({
        "timestamp": [1000 + i * 60 for i in range(50)],
        "price": [200.0 - i for i in range(50)],
    })
    
    def dummy_factory(params):
        def logic(df):
            return df.with_columns(pl.lit(1.0).alias("signal"))
        return logic

    ev1 = engine.run_walk_forward_optimization(
        strategy_factory=dummy_factory,
        param_grid=[{"p": 1}],
        historical_data=df1,
        train_window_bars=20,
        test_window_bars=10,
        step_bars=10,
    )
    ev2 = engine.run_walk_forward_optimization(
        strategy_factory=dummy_factory,
        param_grid=[{"p": 1}],
        historical_data=df2,
        train_window_bars=20,
        test_window_bars=10,
        step_bars=10,
    )
    
    assert ev1.dataset_hash != ev2.dataset_hash


def test_wfo_pooling_always_long_uptrend_no_equity_jump():
    engine = IsolatedBacktestEngine()
    # 4 folds of purely increasing prices
    prices = [100.0 * (1.001 ** i) for i in range(100)]
    df = pl.DataFrame({
        "timestamp": [1000 + i * 60 for i in range(100)],
        "price": prices,
    })
    
    def always_long_factory(params):
        def logic(data_df):
            return data_df.with_columns(pl.lit(1.0).alias("signal"))
        return logic
        
    ev = engine.run_walk_forward_optimization(
        strategy_factory=always_long_factory,
        param_grid=[{"p": 1}],
        historical_data=df,
        train_window_bars=20,
        test_window_bars=15,
        step_bars=15,
        warmup_bars=0,
        spread_pct=0.0,
        slippage_pct=0.0,
        commission_pct=0.0,
    )
    
    eq = list(ev.pooled_oos_equity)
    assert len(eq) > 0
    # Assert monotonic increase without artificial jump-down across fold boundaries
    for i in range(1, len(eq)):
        assert eq[i] >= eq[i-1] - 1e-6, f"Equity dropped at index {i}: {eq[i-1]} -> {eq[i]}"


def _make_test_data():
    import math
    timestamps = [1700000000 + i * 3600 for i in range(2000)]
    prices = [100.0 + (math.sin(i * 0.05) * 5.0) + (i * 0.02) for i in range(2000)]
    return pl.DataFrame({"timestamp": timestamps, "price": prices})


def test_deterministic_tie_breaker(monkeypatch):
    engine = IsolatedBacktestEngine()
    
    def mock_run_backtest(strategy_logic=None, historical_data=None, **kwargs):
        if not hasattr(mock_run_backtest, "counter"):
            mock_run_backtest.counter = 0
            
        c = mock_run_backtest.counter
        mock_run_backtest.counter += 1
        
        if c == 0:
            metrics = {"sharpe_ratio": 2.0, "max_drawdown": 0.15, "total_turnover_count": 50}
        elif c == 1:
            metrics = {"sharpe_ratio": 2.0, "max_drawdown": 0.10, "total_turnover_count": 60}
        elif c == 2:
            metrics = {"sharpe_ratio": 2.0, "max_drawdown": 0.10, "total_turnover_count": 40}
        else:
            metrics = {"sharpe_ratio": 1.5, "max_drawdown": 0.12, "total_turnover_count": 40}
            
        df = pl.DataFrame({"equity": [1.0, 1.1], "strategy_return": [0.1, 0.1]})
        return BacktestResult(equity_curve=df, trade_log=pl.DataFrame(), metrics=metrics)
        
    monkeypatch.setattr(engine, "run_backtest", mock_run_backtest)
    
    def dummy_factory(params):
        def logic(df): return df
        return logic
        
    test_data = _make_test_data()
    ev = engine.run_walk_forward_optimization(
        historical_data=test_data,
        strategy_factory=dummy_factory,
        param_grid=[{"id": 1}, {"id": 2}, {"id": 3}],
        train_window_bars=10,
        test_window_bars=5,
        step_bars=1000
    )
    
    assert ev.folds[0].winner_params["id"] == 3
    assert ev.folds[0].tie_count == 3


from unittest.mock import patch
@patch("are.preflight.validate_wfo_integrity")
def test_final_gate_permutations(mock_val):
    from are.validation import WFOIntegrityResult
    mock_val.return_value = WFOIntegrityResult(True, None, 0)
    auditor = Phase5PreFlightAuditor(None, None, None, None, None)

    # 1. wfo_evidence = None -> INVALID
    res1 = auditor.audit_checkpoint_5_institutional_rigor(wfo_evidence=None)
    assert res1.passed == False
    assert res1.details["gate_status"] == GateStatus.INVALID.value

    # Helper to create valid evidence with modifiable fields
    def make_ev(pooled_sharpe, p_val_adjust=False):
        f1 = WFOFoldEvidence(1, 0, 100, 101, 105, 106, 200, 2, "sr", {"a":1}, 1.0, None, None, 0, "", {}, {"sharpe_ratio": 1.0}, (0.01,), 1.0)
        ev_count = 1 if p_val_adjust else 100000

        ev_proto = WFOEvidence(
            run_id="test",
            dataset_hash="hash",
            timeframe_seconds=60.0,
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
            pooled_oos_returns=tuple([0.01]*1000),
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
            provenance_hash=""
        )

        return ev_proto

    # 2. FAIL due to DSR (Sharpe < 0)
    ev2 = make_ev(pooled_sharpe=-1.0, p_val_adjust=False)
    res2 = auditor.audit_checkpoint_5_institutional_rigor(wfo_evidence=ev2)
    assert res2.passed == False
    assert res2.details["gate_status"] == GateStatus.FAIL.value

    # 3. BORDERLINE due to Performance
    ev3 = make_ev(pooled_sharpe=0.9, p_val_adjust=True)
    res3 = auditor.audit_checkpoint_5_institutional_rigor(wfo_evidence=ev3)
    assert res3.passed == False
    assert res3.details["gate_status"] == GateStatus.BORDERLINE.value

    # 4. PASS
    ev4 = make_ev(pooled_sharpe=2.5, p_val_adjust=True)
    res4 = auditor.audit_checkpoint_5_institutional_rigor(wfo_evidence=ev4)
    assert res4.passed == True
    assert res4.details["gate_status"] == GateStatus.PASS.value