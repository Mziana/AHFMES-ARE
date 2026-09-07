"""P1-09: serializer artifact backtest terpadu (skema union).

Akar bug: tiga penulis artifact `data/backtests/bkt-*.json` memakai tiga
skema berbeda:
  - are/cli.py          : {id, strategy_id, symbol, ..., metrics{python_keys}}
  - are/web_ui.py       : {id, strategyName, config{...}, results{camelCase},
                          equityCurve[], ...}
  - UI backtest route   : {id, strategyId, strategyName, config{...},
                          results{...}, equityCurve[], ...}
Akibat: `are backtest list` (pembaca skema CLI) menampilkan baris
`? / 0 bars` utk artifact UI, dan endpoint equity-curve UI gagal utk artifact
CLI. Solusi: SATU helper penulis dgn skema union (keys semua pembaca) sehingga
setiap pembaca tetap berfungsi tanpa perubahan, DAN setiap artifact punya
provenance (schema_version, strategy di semua penamaan, dsb.).
"""
import json
import os
import time


def _camel(s: str) -> str:
    parts = s.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])


def build_backtest_artifact(
    metrics: dict,
    equity_curve=None,
    bt_id: str = None,
    symbol: str = '',
    timeframe: str = '',
    start: str = '',
    end: str = '',
    initial_capital: float = 100000.0,
    strategy_id: str = 'unknown',
    strategy_name: str = 'Unknown',
    strategy_family: str = 'MOMENTUM',
    strategy_parameters: dict = None,
    timestamp_s: float = None,
) -> dict:
    """Bangun artifact dgn skema union: memuat keys yang dibaca semua
    pembaca (CLI list, web_ui endpoints, UI backtest page) + provenance."""
    ts = timestamp_s if timestamp_s is not None else time.time()
    bt_id = bt_id or f"bkt-{int(ts * 1000)}"

    # equity_curve: polars DataFrame -> sample utk equityCurve[];
    # list -> dipakai langsung; None/empty -> [].
    equity_data = []
    if equity_curve is not None and hasattr(equity_curve, 'columns'):
        if not equity_curve.is_empty():
            timestamps = equity_curve['timestamp'].to_list()
            equities = equity_curve['equity'].to_list()
            step = max(1, len(timestamps) // 200)
            for i in range(0, len(timestamps), step):
                equity_data.append({
                    'timestamp': int(timestamps[i]),
                    'equity': round(float(equities[i]), 2),
                })
    elif isinstance(equity_curve, list):
        equity_data = equity_curve

    cap = float(initial_capital)
    net_pnl = float(metrics.get('final_equity', cap)) - cap

    # Union metrics: python_keys (CLI) dan camelCase (UI) sekaligus
    m_out = dict(metrics)  # python keys utk CLI list
    results = {
        'totalTrades': metrics.get('total_trades', 0),
        'winRate': metrics.get('win_rate', 0),
        'netPnl': round(net_pnl, 2),
        'finalEquity': metrics.get('final_equity', cap),
        'sharpe': metrics.get('sharpe_ratio', 0),
        'sortino': metrics.get('sortino_ratio', 0),
        'calmar': metrics.get('calmar_ratio', 0),
        'cvar': metrics.get('cvar_5pct', 0),
        'profitFactor': metrics.get('profit_factor', 0),
        'maxDrawdown': metrics.get('max_drawdown_pct', 0),
        'avgWin': metrics.get('avg_win', 0),
        'avgLoss': metrics.get('avg_loss', 0),
        'maxConsecLoss': metrics.get('max_consecutive_losses', 0),
        'exposure': metrics.get('exposure_pct', 0),
        'totalReturnPct': metrics.get('total_return_pct', 0),
        'dataBars': metrics.get('total_bars', 0),
        'alpha': metrics.get('alpha_pct', 0),
        # provenance tambahan (dibaca siapa pun yang perlu)
        'rawDatasetHash': metrics.get('raw_dataset_hash', ''),
        'purifiedDatasetHash': metrics.get('purified_dataset_hash', ''),
        'signalTiming': metrics.get('signal_timing', ''),
        'executionModelId': metrics.get('execution_model_id', ''),
    }

    return {
        'id': bt_id,
        'schema_version': 2,
        # strategy dalam SEMUA penamaan yang ada di pembaca:
        'strategy_id': strategy_id,          # CLI list
        'strategyId': strategy_id,           # UI page
        'strategyName': strategy_name,       # web_ui + UI page
        'symbol': symbol,
        'timeframe': timeframe,
        'start': start,                       # CLI artifact
        'end': end,
        'initial_capital': cap,
        'config': {                           # web_ui + UI page
            'symbol': symbol,
            'timeframe': timeframe,
            'startDate': start,
            'endDate': end,
            'initialBalance': cap,
            'strategyFamily': strategy_family,
            'strategyParameters': strategy_parameters or {},
        },
        'metrics': m_out,                     # CLI list
        'results': results,                   # UI/web_ui page
        'equityCurve': equity_data,           # UI/web_ui equity-curve endpoint
        'equity_curve': [],                   # legacy CLI shape (empty = tidak disimpan
                                              # di skema CLI; curve utuh ada di equityCurve)
        'ranAt': time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(ts)),
        'saved_at': ts,
    }


def save_backtest_artifact(artifact: dict, bt_dir: str = None) -> str:
    """Tulis artifact ke data/backtests/<id>.json secara atomik. Return path."""
    bt_dir = bt_dir or os.path.join('data', 'backtests')
    os.makedirs(bt_dir, exist_ok=True)
    path = os.path.join(bt_dir, f"{artifact['id']}.json")
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(artifact, f, indent=2)
    os.replace(tmp, path)
    return path
