#!/usr/bin/env python3
"""Qualification script for AI strategy proposals.
Called by Next.js API: python are/qualify_proposal.py <symbol> <timeframe> <start> <end>
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

    # Ensure ARE is importable
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

        eq_curve = []
        try:
            eq_curve = result.equity_curve.to_dicts()[-100:] if hasattr(result.equity_curve, 'to_dicts') else []
        except Exception:
            pass

        print(json.dumps({
            "success": True,
            "qualification": {
                "win_rate": round(m.get('profit_factor', 0) * 50, 1),
                "sharpe": sharpe,
                "total_return": m.get('total_return_pct', 0),
                "max_drawdown": m.get('max_drawdown_pct', 0),
                "profit_factor": m.get('profit_factor', 0),
                "trades": n_trades,
                "equity_curve": eq_curve,
                "qualified": n_trades >= 10 and sharpe > 0.5,
                "status": "QUALIFIED" if (n_trades >= 10 and sharpe > 0.5) else "NOT_QUALIFIED",
            }
        }))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == '__main__':
    main()
