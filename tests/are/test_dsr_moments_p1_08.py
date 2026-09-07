# -*- coding: utf-8 -*-
"""Regression test P1-08: DSR memakai momen data nyata.

Akar bug: evaluate_dsr_from_evidence memanggil calculate_deflated_sharpe_ratio
tanpa skewness/kurtosis/var_sharpe (default: 0 / 3 / 1.0) — asumsi normal
murni. Return trading riil ber-skew negatif & fat-tail, jadi p-value DSR bias
(biasanya terlalu optimis). Perbaikan: estimate_dsr_moments() dari pooled OOS
returns (Lopez de Prado 2013), signature fungsi lama tidak berubah.
"""
import math

import pytest

from are.validation import (
    estimate_dsr_moments,
    evaluate_dsr_from_evidence,
    calculate_deflated_sharpe_ratio,
)
from are.models import WFOEvidence


def _evidence(returns, trials=5):
    return WFOEvidence(
        run_id="t", dataset_hash="h", timeframe_seconds=3600.0,
        data_start_ts=0.0, data_end_ts=1.0,
        folds=(), fold_count=1, parameter_family_size=trials,
        evaluation_count=trials, effective_trial_count=trials,
        effective_trial_method="t", effective_trial_assumption="t",
        training_overlap_ratio=0.0, oos_overlap_ratio=0.0,
        purge_bars=0, label_horizon_bars=0, label_horizon_unit="BARS",
        warmup_bars=0,
        pooled_oos_returns=tuple(returns),
        pooled_oos_equity=(), pooled_oos_sharpe=1.0,
        pooled_oos_return=0.05, pooled_oos_max_drawdown=0.05,
        mean_fold_oos_sharpe=0.0, median_fold_oos_sharpe=0.0,
        worst_fold_oos_sharpe=0.0, std_fold_oos_sharpe=0.0,
        mean_wfe=0.0, median_wfe=0.0, worst_wfe=0.0,
        provenance_hash="", pooled_trades=(),
    )


def test_normal_returns_yield_theoretical_moments():
    """Return iid normal harus menghasilkan skew~0, kurt~3 (estimator menangkap
    normalitas — bukan asumsi buta)."""
    import random
    rng = random.Random(42)
    rets = [rng.gauss(0.001, 0.01) for _ in range(5000)]
    skew, kurt, _ = estimate_dsr_moments(rets)
    assert abs(skew) < 0.15
    assert 2.7 < kurt < 3.3


def test_fat_tail_returns_detected():
    """Fat-tail: kurtosis harus jauh di atas 3 (bukan default 3)."""
    import random
    rng = random.Random(7)
    rets = []
    for _ in range(5000):
        if rng.random() < 0.02:
            rets.append(rng.choice([-0.12, 0.10]))  # outlier besar
        else:
            rets.append(rng.gauss(0.0005, 0.004))
    _, kurt, _ = estimate_dsr_moments(rets)
    assert kurt > 4.0, "fat-tail harus terdeteksi (kurt > 4)"


def test_negative_skew_detected():
    """Crash-biased returns: skew negatif terdeteksi."""
    import random
    rng = random.Random(11)
    rets = []
    for _ in range(5000):
        rets.append(-0.03 if rng.random() < 0.1 else rng.gauss(0.002, 0.003))
    skew, _, _ = estimate_dsr_moments(rets)
    assert skew < -0.5


def test_dsr_uses_real_moments_wiring():
    """Wire test: evaluate_dsr_from_evidence harus SAMA dengan pemanggilan
    eksplisit memakai momen yang diestimasi dari data — bukan default normal.
    (Catatan: dgn n besar, var_sharpe ~ 1/n jauh lebih kecil dari default 1.0;
    efek kurtosis fat-tail menjaga p-value tetap jujur per sampel, bukan
    'selalu lebih ketat'.)"""
    import random
    rng = random.Random(7)
    rets = []
    for _ in range(2000):
        if rng.random() < 0.02:
            rets.append(rng.choice([-0.12, 0.10]))
        else:
            rets.append(rng.gauss(0.0005, 0.004))
    ev = _evidence(rets)
    res_real = evaluate_dsr_from_evidence(ev)

    skew, kurt, var_sharpe = estimate_dsr_moments(rets)
    _, p_explicit = calculate_deflated_sharpe_ratio(
        observed_sharpe=ev.pooled_oos_sharpe, num_trials=5,
        num_observations=len(rets), skewness=skew, kurtosis=kurt,
        var_sharpe=var_sharpe)
    assert res_real.p_value == pytest.approx(p_explicit)

    # dan hasilnya harus BERBEDA dari path asumsi lama (default 0/3/1.0) —
    # bukti momen nyata benar-benar mengubah perhitungan
    _, p_naive = calculate_deflated_sharpe_ratio(
        observed_sharpe=ev.pooled_oos_sharpe, num_trials=5,
        num_observations=len(rets))
    assert p_naive != res_real.p_value


def test_degenerate_sample_falls_back():
    assert estimate_dsr_moments([]) == (0.0, 3.0, 1.0)
    assert estimate_dsr_moments([0.001]) == (0.0, 3.0, 1.0)
    assert estimate_dsr_moments([0.0, 0.0, 0.0, 0.0]) == (0.0, 3.0, 1.0)
    assert estimate_dsr_moments([float('nan'), 0.01, -0.01, 0.005]) == (0.0, 3.0, 1.0)
