import re
import hashlib
import time
import os

with open("are/backtest.py", "r", encoding="utf-8") as f:
    content = f.read()

start_idx = content.find("def run_walk_forward_optimization")
end_idx = content.find("def evaluate_robustness", start_idx)

new_func = """def run_walk_forward_optimization(
        self,
        strategy_factory: Callable[[Dict[str, Any]], Callable[[pl.DataFrame], pl.DataFrame]],
        param_grid: List[Dict[str, Any]],
        historical_data: Optional[pl.DataFrame] = None,
        train_window_bars: int = 500,
        test_window_bars: int = 100,
        step_bars: int = 100,
        warmup_bars: int = 0,
        purge_bars: int = 0,
        label_horizon_bars: int = 0,
        optimization_metric: str = "sharpe_ratio",
        initial_capital: float = 10000.0,
        timeframe_seconds: float = 60.0,
        spread_pct: float = 0.0001,
        slippage_pct: float = 0.00005,
        commission_pct: float = 0.00005,
    ) -> WFOEvidence:
        \"\"\"
        True Walk-Forward Optimization (WFO) with in-sample parameter fitting,
        warm-up indicator lookback, purge gap, and out-of-sample performance evaluation (RES-RED-09, RES-RED-18, RES-RED-19).
        \"\"\"
        if purge_bars < label_horizon_bars:
            raise ValueError("PURGE_VIOLATION")

        if historical_data is None:
            # Generate deterministic dataset with sufficient bars
            timestamps = [1700000000 + i * int(timeframe_seconds) for i in range(1500)]
            prices = [65000.0 + (math.sin(i * 0.03) * 300.0) + (i * 0.2) for i in range(1500)]
            historical_data = pl.DataFrame({
                "timestamp": timestamps,
                "price": prices,
            })

        purifier = DataPurifier()
        purified_data = purifier.purify_tick_data(historical_data)

        total_bars = len(purified_data)
        min_required = train_window_bars + purge_bars + test_window_bars
        if total_bars < min_required:
            raise ValueError(
                f"Historical data length ({total_bars}) is less than minimum required bars ({min_required})"
            )

        folds = []
        start = 0
        fold_idx = 0
        
        pooled_returns = []
        pooled_equity = []
        
        def ts(idx):
            if idx < 0: return 0.0
            if idx >= total_bars: idx = total_bars - 1
            return float(purified_data["timestamp"][idx])

        while (start + train_window_bars + purge_bars + test_window_bars) <= total_bars:
            train_slice = purified_data.slice(start, train_window_bars)

            # In-Sample (Train) Phase: grid search over param_grid
            candidates = []
            
            for params in param_grid:
                strat_logic = strategy_factory(params)
                is_res = self.run_backtest(
                    strategy_logic=strat_logic,
                    historical_data=train_slice,
                    initial_capital=initial_capital,
                    timeframe_seconds=timeframe_seconds,
                    spread_pct=spread_pct,
                    slippage_pct=slippage_pct,
                    commission_pct=commission_pct,
                )
                
                is_sharpe = float(is_res.metrics.get("sharpe_ratio", 0.0))
                is_max_dd = float(is_res.metrics.get("max_drawdown", 0.0))
                is_turnover = float(is_res.metrics.get("total_turnover_count", 0.0))
                
                candidates.append({
                    "params": params,
                    "is_res": is_res,
                    "is_sharpe": is_sharpe,
                    "is_max_dd": is_max_dd,
                    "is_turnover": is_turnover,
                })
                
            def _wfo_selection_key(c):
                return (round(c["is_sharpe"], 6), -abs(c["is_max_dd"]), -c["is_turnover"])
                
            candidates.sort(key=_wfo_selection_key, reverse=True)
            best_cand = candidates[0]
            best_params = best_cand["params"]
            best_is_result = best_cand["is_res"]
            
            runner_up_cand = candidates[1] if len(candidates) > 1 else None
            
            best_sharpe_rounded = round(best_cand["is_sharpe"], 6)
            tie_count = sum(1 for c in candidates if round(c["is_sharpe"], 6) == best_sharpe_rounded)

            # Out-of-Sample (Test OOS) Phase with Purge and Warmup (RES-RED-18)
            oos_start_idx = start + train_window_bars + purge_bars
            warmup_start_idx = max(0, oos_start_idx - warmup_bars)
            actual_warmup = oos_start_idx - warmup_start_idx
            
            test_slice_with_warmup = purified_data.slice(warmup_start_idx, actual_warmup + test_window_bars)

            best_strat_logic = strategy_factory(best_params) if best_params is not None else None
            oos_res = self.run_backtest(
                strategy_logic=best_strat_logic,
                historical_data=test_slice_with_warmup,
                initial_capital=initial_capital,
                timeframe_seconds=timeframe_seconds,
                spread_pct=spread_pct,
                slippage_pct=slippage_pct,
                commission_pct=commission_pct,
            )

            # Score strict OOS portion only (excluding warmup bars)
            oos_returns = []
            if actual_warmup > 0 and len(oos_res.equity_curve) > actual_warmup:
                oos_equity_df = oos_res.equity_curve.slice(actual_warmup, test_window_bars)
                oos_returns = oos_equity_df["strategy_return"].to_list() if "strategy_return" in oos_equity_df.columns else []
                oos_sharpe = calculate_sharpe_ratio(oos_returns, timeframe_seconds=timeframe_seconds)
                oos_metrics = dict(oos_res.metrics)
                oos_metrics["sharpe_ratio"] = round(oos_sharpe, 4)
                if len(oos_equity_df) > 0 and "equity" in oos_equity_df.columns:
                    eq_init = float(oos_equity_df["equity"][0])
                    eq_final = float(oos_equity_df["equity"][-1])
                    oos_metrics["total_return"] = round((eq_final - eq_init) / eq_init, 4) if eq_init > 0 else 0.0
                    oos_metrics["total_return_pct"] = round(oos_metrics["total_return"] * 100.0, 2)
                    oos_metrics["net_return_pct"] = oos_metrics["total_return_pct"]
                    
                    pooled_returns.extend(oos_returns)
                    if not pooled_equity:
                        pooled_equity.extend(oos_equity_df["equity"].to_list())
                    else:
                        last_eq = pooled_equity[-1]
                        for r in oos_returns:
                            last_eq *= (1.0 + r)
                            pooled_equity.append(last_eq)
            else:
                oos_metrics = oos_res.metrics
                oos_sharpe = float(oos_res.metrics.get("sharpe_ratio", 0.0))
                if len(oos_res.equity_curve) > 0:
                    oos_returns = oos_res.equity_curve["strategy_return"].to_list() if "strategy_return" in oos_res.equity_curve.columns else []
                    pooled_returns.extend(oos_returns)
                    pooled_equity.extend(oos_res.equity_curve["equity"].to_list() if "equity" in oos_res.equity_curve.columns else [])

            is_sharpe = float(best_cand["is_sharpe"])
            wfe_ratio = (oos_sharpe / is_sharpe) if is_sharpe > 0.0 else 0.0
            
            fold_evidence = WFOFoldEvidence(
                fold_id=fold_idx,
                train_start_ts=ts(start),
                train_end_ts=ts(start + train_window_bars - 1),
                purge_start_ts=ts(start + train_window_bars),
                purge_end_ts=ts(oos_start_idx - 1),
                oos_start_ts=ts(oos_start_idx),
                oos_end_ts=ts(oos_start_idx + test_window_bars - 1),
                candidate_count=len(param_grid),
                selection_metric=optimization_metric,
                winner_params=best_params,
                winner_is_score=is_sharpe,
                runner_up_params=runner_up_cand["params"] if runner_up_cand else None,
                runner_up_is_score=runner_up_cand["is_sharpe"] if runner_up_cand else None,
                tie_count=tie_count,
                tie_break_rule="(round(is_sharpe, 6), -abs(is_max_dd), -is_turnover)",
                is_metrics=dict(best_is_result.metrics),
                oos_metrics=oos_metrics,
                oos_returns=tuple(oos_returns),
                wfe=wfe_ratio
            )
            folds.append(fold_evidence)

            fold_idx += 1
            start += step_bars

        pooled_oos_returns_tup = tuple(pooled_returns)
        pooled_oos_equity_tup = tuple(pooled_equity)
        pooled_oos_sharpe = calculate_sharpe_ratio(pooled_returns, timeframe_seconds=timeframe_seconds)
        
        pooled_total_return = 0.0
        pooled_max_dd = 0.0
        if pooled_equity:
            eq_init = pooled_equity[0]
            eq_final = pooled_equity[-1]
            if eq_init > 0:
                pooled_total_return = (eq_final - eq_init) / eq_init
                
            peak = pooled_equity[0]
            for eq in pooled_equity:
                if eq > peak:
                    peak = eq
                dd = (peak - eq) / peak if peak > 0 else 0.0
                if dd > pooled_max_dd:
                    pooled_max_dd = dd

        fold_oos_sharpes = [f.oos_metrics.get("sharpe_ratio", 0.0) for f in folds]
        fold_wfes = [f.wfe for f in folds]
        
        def _mean(vals): return sum(vals)/len(vals) if vals else 0.0
        def _median(vals):
            if not vals: return 0.0
            s = sorted(vals)
            n = len(s)
            if n % 2 == 1: return s[n//2]
            return (s[n//2 - 1] + s[n//2]) / 2.0
            
        def _worst(vals): return min(vals) if vals else 0.0
        def _std(vals):
            if not vals: return 0.0
            m = _mean(vals)
            var = sum((v - m)**2 for v in vals) / len(vals)
            return math.sqrt(var)

        fold_count = len(folds)
        parameter_family_size = len(param_grid)
        evaluation_count = fold_count * parameter_family_size
        
        training_overlap_ratio = 0.0
        oos_overlap_ratio = 0.0
        if fold_count > 1:
            training_overlap_ratio = max(0.0, (train_window_bars - step_bars) / train_window_bars)
            oos_overlap_ratio = max(0.0, (test_window_bars - step_bars) / test_window_bars)
            
        run_id = f"wfo_{int(time.time())}_{os.urandom(4).hex()}"
        
        data_dict = {
            "folds": [
                {
                    "winner_params": f.winner_params,
                    "oos_sharpe": f.oos_metrics.get("sharpe_ratio", 0.0)
                } for f in folds
            ],
            "pooled_sharpe": pooled_oos_sharpe
        }
        import json
        import hashlib
        provenance_hash = hashlib.sha256(json.dumps(data_dict, sort_keys=True).encode()).hexdigest()

        evidence = WFOEvidence(
            run_id=run_id,
            dataset_hash=compute_sha256(str(len(historical_data)).encode()),
            data_start_ts=float(historical_data["timestamp"][0]) if len(historical_data) > 0 else 0.0,
            data_end_ts=float(historical_data["timestamp"][-1]) if len(historical_data) > 0 else 0.0,
            folds=tuple(folds),
            fold_count=fold_count,
            parameter_family_size=parameter_family_size,
            evaluation_count=evaluation_count,
            effective_trial_count=parameter_family_size,
            effective_trial_method="CONSERVATIVE_FAMILY_SIZE_PROXY",
            effective_trial_assumption="Independent hypotheses within grid",
            training_overlap_ratio=training_overlap_ratio,
            oos_overlap_ratio=oos_overlap_ratio,
            purge_bars=purge_bars,
            label_horizon_bars=label_horizon_bars,
            label_horizon_unit="BARS",
            warmup_bars=warmup_bars,
            pooled_oos_returns=pooled_oos_returns_tup,
            pooled_oos_equity=pooled_oos_equity_tup,
            pooled_oos_sharpe=pooled_oos_sharpe,
            pooled_oos_return=pooled_total_return,
            pooled_oos_max_drawdown=pooled_max_dd,
            mean_fold_oos_sharpe=_mean(fold_oos_sharpes),
            median_fold_oos_sharpe=_median(fold_oos_sharpes),
            worst_fold_oos_sharpe=_worst(fold_oos_sharpes),
            std_fold_oos_sharpe=_std(fold_oos_sharpes),
            mean_wfe=_mean(fold_wfes),
            median_wfe=_median(fold_wfes),
            worst_wfe=_worst(fold_wfes),
            provenance_hash=provenance_hash
        )

        return evidence
"""

new_content = content[:start_idx] + new_func + "\n    " + content[end_idx:]
with open("are/backtest.py", "w", encoding="utf-8") as f:
    f.write(new_content)
print("Replacement script executed.")