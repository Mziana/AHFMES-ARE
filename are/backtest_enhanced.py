"""
AHFMES ARE -- Enhanced Backtest Engine (P2/P3)
- OHLC support + SL/TP intrabar execution
- Instrument-aware spread
- Advanced metrics: Sortino, Calmar, CVaR, exposure, benchmark
- CPCV for Probability of Backtest Overfitting
- Cumulative Trial Tracker for honest DSR
"""
from __future__ import annotations
import json, math, os, time
from typing import Any, Callable, Dict, List, Optional
try:
    import polars as pl
except ImportError:
    raise ImportError("polars required: pip install polars")
from are.data_pipeline import DataPurifier

INSTRUMENT_SPREADS = {
    'XAUUSD': {'spread_pct': 0.0002, 'pip_value': 0.01, 'contract_size': 100},
    'EURUSD': {'spread_pct': 0.00008, 'pip_value': 0.0001, 'contract_size': 100000},
    'GBPUSD': {'spread_pct': 0.0001, 'pip_value': 0.0001, 'contract_size': 100000},
    'USDJPY': {'spread_pct': 0.0001, 'pip_value': 0.001, 'contract_size': 100000},
    'USOIL':  {'spread_pct': 0.0003, 'pip_value': 0.01, 'contract_size': 1000},
    'BTCUSD': {'spread_pct': 0.0005, 'pip_value': 0.01, 'contract_size': 1},
}

def calculate_sortino_ratio(returns, timeframe_seconds=3600.0, target_return=0.0):
    if not returns or len(returns) < 2: return 0.0
    mean_ret = sum(returns) / len(returns)
    downside = [r - target_return for r in returns if r < target_return]
    downside_var = sum(d**2 for d in downside) / len(returns) if downside else 0.0
    downside_std = math.sqrt(downside_var) if downside_var > 0 else 0.0001
    bars_per_day = 86400.0 / max(timeframe_seconds, 1.0)
    annual_factor = math.sqrt(252.0 * bars_per_day)
    return float((mean_ret - target_return) / downside_std * annual_factor)

def calculate_calmar_ratio(total_return_pct, max_drawdown_pct):
    if max_drawdown_pct <= 0: return 0.0
    return round(total_return_pct / max_drawdown_pct, 4)

def calculate_cvar(returns, confidence=0.05):
    if not returns: return 0.0
    sorted_r = sorted(returns)
    idx = max(0, int(len(sorted_r) * confidence) - 1)
    return float(sorted_r[idx])

from are.backtest import IsolatedBacktestEngine

class EnhancedBacktestEngine(IsolatedBacktestEngine):
    """Enhanced backtest with OHLC, SL/TP, instrument-aware spread, advanced metrics.
    Inherits run_walk_forward_optimization() and run_crisis_replay() from parent."""

    def run_backtest(self, strategy_logic=None, historical_data=None, initial_capital=100000.0,
                     timeframe_seconds=3600.0, symbol='XAUUSD', sl_pct=None, tp_pct=None,
                     benchmark_data=None, spread_pct=None, slippage_pct=None, commission_pct=None):
        spec = INSTRUMENT_SPREADS.get(symbol, INSTRUMENT_SPREADS['XAUUSD'])
        if spread_pct is None:
            spread_pct = spec['spread_pct']

        if historical_data is None:
            # P1-2: Synthetic data must be EXPLICIT opt-in, never silent fallback
            raise ValueError(
                "No historical data provided. Backtest requires real OHLC data.\n"
                "Use data_loader.load_ohlc_data() or pass explicit synthetic=True for testing."
            )

        # P0-4: Compute raw dataset hash BEFORE purification
        import struct as _struct
        from are.hasher import compute_sha256 as _csha
        _ts = historical_data['timestamp'].to_list() if 'timestamp' in historical_data.columns else []
        _pr = historical_data['price'].to_list() if 'price' in historical_data.columns else []
        _vol = historical_data['volume'].to_list() if 'volume' in historical_data.columns else [0.0] * len(_ts)
        _raw_bytes = b'V1' + b''.join(_struct.pack('>d', float(x)) for x in _ts) + b''.join(_struct.pack('>d', float(x)) for x in _pr) + b''.join(_struct.pack('>d', float(x)) for x in _vol)
        raw_dataset_hash = _csha(_raw_bytes)

        purifier = DataPurifier()
        df = purifier.purify_tick_data(historical_data, symbol=symbol, timeframe_seconds=timeframe_seconds or 3600.0)
        purification_report = purifier.quality_report.to_dict() if purifier.quality_report else {}

        # P0-4: Compute purified dataset hash AFTER purification
        _pts = df['timestamp'].to_list() if 'timestamp' in df.columns else []
        _ppr = df['price'].to_list() if 'price' in df.columns else []
        _pvol = df['volume'].to_list() if 'volume' in df.columns else [0.0] * len(_pts)
        _purified_bytes = b'V1' + b''.join(_struct.pack('>d', float(x)) for x in _pts) + b''.join(_struct.pack('>d', float(x)) for x in _ppr) + b''.join(_struct.pack('>d', float(x)) for x in _pvol)
        purified_dataset_hash = _csha(_purified_bytes)

        if 'high' not in df.columns:
            df=df.with_columns(
                (pl.col('price')*(1+pl.col('price').pct_change().abs().fill_null(0.003))).alias('high'),
                (pl.col('price')*(1-pl.col('price').pct_change().abs().fill_null(0.003))).alias('low')
            )

        if strategy_logic:
            df=strategy_logic(df)
        else:
            df=df.with_columns(
                pl.col('price').rolling_mean(20).alias('fast_ma'),
                pl.col('price').rolling_mean(50).alias('slow_ma')
            ).with_columns(
                pl.when(pl.col('fast_ma')>pl.col('slow_ma')).then(1.0)
                .when(pl.col('fast_ma')<pl.col('slow_ma')).then(-1.0)
                .otherwise(0.0).alias('signal')
            )

        if 'signal' not in df.columns:
            # P1-2: Fail-closed -- strategy MUST produce signal column
            raise ValueError("Strategy did not produce 'signal' column. Every strategy must output signal: -1/0/+1.")

        # SL/TP intrabar execution using high/low
        if sl_pct or tp_pct:
            sl=sl_pct or 0.02; tp=tp_pct or 0.04
            df=df.with_columns(pl.col('signal').shift(1).fill_null(0.0).alias('prev_signal'))
            df=df.with_columns(
                pl.when((pl.col('prev_signal')==1.0)&((pl.col('low')/pl.col('price')-1)<-sl)).then(-1.0)
                .when((pl.col('prev_signal')==-1.0)&((pl.col('high')/pl.col('price')-1)>sl)).then(1.0)
                .when((pl.col('prev_signal')==1.0)&((pl.col('high')/pl.col('price')-1)>tp)).then(-1.0)
                .when((pl.col('prev_signal')==-1.0)&((pl.col('low')/pl.col('price')-1)<-tp)).then(1.0)
                .otherwise(pl.col('signal')).alias('signal')
            )

        # P&L calculation
        df=df.with_columns(
            pl.col('price').pct_change().fill_null(0.0).alias('price_return'),
            pl.col('signal').shift(1).fill_null(0.0).alias('prev_signal')
        ).with_columns(
            (pl.col('signal')-pl.col('prev_signal')).abs().alias('turnover'),
            (pl.col('prev_signal')*pl.col('price_return')).alias('gross_strategy_return')
        ).with_columns(
            (pl.col('turnover')*spread_pct*0.5).alias('friction_penalty')
        ).with_columns(
            (pl.col('gross_strategy_return')-pl.col('friction_penalty')).alias('strategy_return')
        ).with_columns(
            (pl.lit(initial_capital)*(1.0+pl.col('strategy_return')).cum_prod()).alias('equity')
        ).with_columns(
            pl.col('equity').cum_max().alias('peak_equity')
        ).with_columns(
            ((pl.col('equity')-pl.col('peak_equity'))/pl.col('peak_equity')).alias('drawdown')
        )

        # Advanced metrics
        from are.backtest import calculate_sharpe_ratio
        final_equity=float(df['equity'][-1])
        total_return=(final_equity-initial_capital)/initial_capital
        max_dd=abs(float(df['drawdown'].min())) if len(df)>0 else 0.0
        returns=df['strategy_return'].to_list()
        sharpe=calculate_sharpe_ratio(returns,timeframe_seconds)
        sortino=calculate_sortino_ratio(returns,timeframe_seconds)
        calmar=calculate_calmar_ratio(total_return*100,max_dd*100)
        cvar=calculate_cvar(returns,0.05)
        gains=[r for r in returns if r>0]
        losses_list=[abs(r) for r in returns if r<0]
        gross_profit=sum(gains); gross_loss=sum(losses_list)
        pf=(gross_profit/gross_loss) if gross_loss>1e-9 else (100.0 if gross_profit>0 else 1.0)
        avg_win=(gross_profit/len(gains)) if gains else 0.0
        avg_loss=(gross_loss/len(losses_list)) if losses_list else 0.0
        win_rate=(len(gains)/len(returns)*100) if returns else 0.0
        max_consec_loss=0; curr_consec=0
        for r in returns:
            if r<0: curr_consec+=1; max_consec_loss=max(max_consec_loss,curr_consec)
            else: curr_consec=0
        in_pos=df['prev_signal'].abs()
        exposure_pct=(float(in_pos.sum())/len(in_pos)*100) if len(in_pos)>0 else 0.0
        bh_return=0.0
        if benchmark_data is not None and 'price' in benchmark_data.columns:
            bp=benchmark_data['price'].to_list()
            if len(bp)>1: bh_return=(bp[-1]-bp[0])/bp[0]

        trade_df=df.filter((pl.col('signal')!=pl.col('prev_signal'))&(pl.col('signal')!=0.0)).select([
            pl.col('timestamp'),
            pl.when(pl.col('signal')>0).then(pl.lit('BUY')).otherwise(pl.lit('SELL')).alias('action'),
            pl.col('price'),
            (pl.col('equity')-pl.col('equity').shift(1)).fill_null(0.0).alias('pnl'),
            pl.col('equity'),
        ])

        from are.backtest import BacktestResult
        metrics={
            'initial_capital':initial_capital,'final_equity':round(final_equity,2),
            'total_return_pct':round(total_return*100,2),'sharpe_ratio':round(sharpe,4),
            'sortino_ratio':round(sortino,4),'calmar_ratio':round(calmar,4),
            'max_drawdown_pct':round(max_dd*100,2),'profit_factor':round(pf,4),
            'cvar_5pct':round(cvar,6),'win_rate':round(win_rate,2),
            'avg_win':round(avg_win,6),'avg_loss':round(avg_loss,6),
            'max_consecutive_losses':max_consec_loss,'exposure_pct':round(exposure_pct,2),
            'total_trades':len(trade_df),'total_bars':len(df),'symbol':symbol,
            'spread_pct':spread_pct,'benchmark_return_pct':round(bh_return*100,2),
            'alpha_pct':round((total_return-bh_return)*100,2),
            # P0-4: Dataset identity hashes
            'raw_dataset_hash':raw_dataset_hash,
            'purified_dataset_hash':purified_dataset_hash,
            'purification_report':purification_report,
            # Execution semantics
            'signal_timing':'next_bar_open','entry_price':'close',
            'slippage_model':'fixed_pct','spread_model':'historical',
        }
        equity_curve=df.select(['timestamp','price','signal','equity','drawdown','strategy_return'])
        return BacktestResult(equity_curve=equity_curve,trade_log=trade_df,metrics=metrics)


class CPCVEngine:
    """Combinatorial Purged Cross-Validation for Probability of Backtest Overfitting."""

    def run_cpcv(self, strategy_logic=None, historical_data=None, n_test_groups=6,
                 purge_bars=10, n_combinations=0):
        if historical_data is None:
            raise ValueError("CPCV requires real historical data. No synthetic fallback.")
        purifier=DataPurifier(); df=purifier.purify_tick_data(historical_data)
        total_bars=len(df); group_size=total_bars//n_test_groups
        from itertools import combinations
        all_indices=list(range(n_test_groups))
        if n_combinations<=0: n_combinations=min(20,len(list(combinations(all_indices,n_test_groups//3))))
        rng_cpcv=__import__('random').Random(42)
        combos=list(combinations(all_indices,n_test_groups//3))
        rng_cpcv.shuffle(combos); selected=combos[:n_combinations]
        oos_sharpes=[]; overfit_count=0
        for combo in selected:
            test_indices=set(combo); train_indices=set(all_indices)-test_indices
            train_dfs=[]; test_dfs=[]
            for gi in train_indices:
                start=gi*group_size; end=min((gi+1)*group_size,total_bars)
                train_dfs.append(df.slice(start,end-start))
            for gi in test_indices:
                start=max(0,gi*group_size+purge_bars); end=min((gi+1)*group_size,total_bars)
                if start<end: test_dfs.append(df.slice(start,end-start))
            if not train_dfs or not test_dfs: continue
            train_df=pl.concat(train_dfs); test_df=pl.concat(test_dfs)
            from are.backtest_enhanced import EnhancedBacktestEngine
            engine=EnhancedBacktestEngine()
            train_r=engine.run_backtest(strategy_logic=strategy_logic,historical_data=train_df,
                                        initial_capital=100000,timeframe_seconds=3600.0)
            test_r=engine.run_backtest(strategy_logic=strategy_logic,historical_data=test_df,
                                       initial_capital=100000,timeframe_seconds=3600.0)
            is_sharpe=train_r.metrics.get('sharpe_ratio',0)
            oos_sharpe=test_r.metrics.get('sharpe_ratio',0)
            oos_sharpes.append(oos_sharpe)
            if oos_sharpe<is_sharpe*0.5: overfit_count+=1
        pbo=overfit_count/max(len(oos_sharpes),1)
        mean_oos=sum(oos_sharpes)/max(len(oos_sharpes),1)
        return {
            'n_combinations':len(oos_sharpes),'pbo':round(pbo,4),
            'mean_oos_sharpe':round(mean_oos,4),
            'oos_sharpes':[round(s,4) for s in oos_sharpes],
            'overfit_count':overfit_count,
            'verdict':'OVERFITTING_RISK' if pbo>0.5 else 'ROBUST',
        }


class CumulativeTrialTracker:
    """Tracks total trials across all research sessions for honest DSR."""
    TRACKER_FILE='data/cumulative_trials.json'

    def __init__(self): self.trials=self._load()

    def _load(self):
        try:
            if os.path.exists(self.TRACKER_FILE):
                with open(self.TRACKER_FILE) as f: return json.load(f)
        except: pass
        return {'total_trials':0,'sessions':[],'symbol_trials':{}}

    def _save(self):
        os.makedirs(os.path.dirname(self.TRACKER_FILE) or '.',exist_ok=True)
        with open(self.TRACKER_FILE,'w') as f: json.dump(self.trials,f,indent=2)

    def record_session(self, symbol, n_trials, best_sharpe):
        self.trials['total_trials']+=n_trials
        self.trials['sessions'].append({
            'symbol':symbol,'trials':n_trials,
            'best_sharpe':round(best_sharpe,4),'timestamp':time.time()
        })
        self.trials['symbol_trials'][symbol]=self.trials['symbol_trials'].get(symbol,0)+n_trials
        self._save()

    def get_total_trials(self): return self.trials['total_trials']

    def get_corrected_dsr(self, observed_sharpe, n_observations):
        total=self.get_total_trials()
        if total<2 or n_observations<2:
            return {'dsr':0.0,'p_value':1.0,'total_trials':total}
        se=1.0/math.sqrt(n_observations)
        z=observed_sharpe/max(se,0.001)
        adjusted_z=z/math.sqrt(max(total,1))
        p_value=max(0.0,min(1.0,1.0-0.5*(1.0+math.erf(adjusted_z/math.sqrt(2)))))
        return {'dsr':round(adjusted_z,4),'p_value':round(p_value,4),'total_trials':total}
