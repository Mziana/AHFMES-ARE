#!/usr/bin/env python3
"""
AHFMES-ARE Proposal Screening Script

IMPORTANT: This is a PRELIMINARY SCREENING tool, NOT a research qualification.
It runs a quick backtest to estimate strategy viability before the full
research pipeline (WFO → DSR → Holdout → Final Gate) is executed.

Status meanings:
  SCREENED_PASS   = passed preliminary screening (trades >= 10 AND sharpe > 0.5)
  SCREENED_FAIL   = failed preliminary screening
  RESEARCH_NEEDED = must run full research pipeline for actual qualification

Usage: python -m are.qualify_proposal.py <symbol> <timeframe> <start> <end>
Output: JSON to stdout.
"""
import json
import sys
import os

def main():
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'XAUUSD'
    timeframe = sys.argv[2] if len(sys.argv) > 2 else 'H1'
    start = sys.argv[3] if len(sys.argv) > 3 else '2025-01-01'
    end = sys.argv[4] if len(sys.argv) > 4 else '2026-08-01'

    are_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, are_dir)
    os.chdir(are_dir)

    from are.backtest import IsolatedBacktestEngine
    from are.data_loader import load_ohlc_data

    try:
        df = load_ohlc_data(symbol, timeframe, start, end)
        if df is None or df.is_empty():
            print(json.dumps({"error": f"No data loaded for {symbol} {timeframe}"}))
            return

        engine = IsolatedBacktestEngine()
        result = engine.run_backtest(historical_data=df, initial_capital=100000.0)

        m = result.metrics
        n_trades = m.get('total_trades', 0)
        sharpe = m.get('sharpe_ratio', 0)
        win_rate = m.get('win_rate', 0.0)

        eq_curve = []
        try:
            eq_curve = result.equity_curve.to_dicts()[-100:] if hasattr(result.equity_curve, 'to_dicts') else []
        except Exception:
            pass

        # SCREENING only — not research qualification
        # A strategy that passes this must still go through:
        # WFO → OOS → DSR → Crisis → Holdout → Final Gate
        screening_pass = n_trades >= 10 and sharpe > 0.5

        print(json.dumps({
            "success": True,
            "screening": {
                "win_rate": win_rate,
                "sharpe": sharpe,
                "total_return": m.get('total_return_pct', 0),
                "max_drawdown": m.get('max_drawdown_pct', 0),
                "profit_factor": m.get('profit_factor', 0),
                "trades": n_trades,
                "equity_curve": eq_curve,
                "screened": screening_pass,
                "status": "SCREENED_PASS" if screening_pass else "SCREENED_FAIL",
                "next_step": "RESEARCH_NEEDED" if screening_pass else "STRATEGY_REJECTED",
                "disclaimer": "This is preliminary screening only. Run 'are research run' for actual qualification through WFO→DSR→Holdout→FinalGate.",
            }
        }))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == '__main__':
    main()
