"""ARE Performance Analytics - Real-time metrics calculation."""
import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Trade:
    id: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    lot: float
    pnl: float
    timestamp: float
    strategy: str = ""
    habitat: str = ""
    duration_minutes: float = 0


class PerformanceAnalytics:
    def __init__(self, initial_balance: float = 100000.0, risk_free_rate: float = 0.02):
        self.initial_balance = initial_balance
        self.rf = risk_free_rate
        self.trades: List[Trade] = []

    def add_trade(self, trade: Trade):
        self.trades.append(trade)

    def calculate_all(self) -> Dict[str, Any]:
        if not self.trades:
            return self._empty_metrics()
        returns = [t.pnl for t in self.trades]
        equity = self._equity_curve()
        wins = [r for r in returns if r > 0]
        losses = [r for r in returns if r < 0]
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        avg_win = gross_profit / len(wins) if wins else 0
        avg_loss = gross_loss / len(losses) if losses else 0
        total = len(returns)
        avg_return = sum(returns) / total if total > 0 else 0
        std_return = self._stddev(returns)
        sharpe = (avg_return - self.rf) / std_return if std_return > 0 else 0
        downside = [r for r in returns if r < 0]
        down_std = self._stddev(downside)
        sortino = (avg_return - self.rf) / down_std if down_std > 0 else 0
        peak, max_dd = self.initial_balance, 0
        for e in equity:
            peak = max(peak, e)
            dd = (peak - e) / peak * 100
            max_dd = max(max_dd, dd)
        final = equity[-1] if equity else self.initial_balance
        total_return = (final - self.initial_balance) / self.initial_balance * 100
        calmar = total_return / max_dd if max_dd > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        expectancy = (len(wins) / total * avg_win) - (len(losses) / total * avg_loss) if total > 0 else 0
        return {
            "total_trades": total,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(len(wins) / total * 100, 1) if total > 0 else 0,
            "profit_factor": round(profit_factor, 2),
            "expectancy": round(expectancy, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "max_drawdown": round(max_dd, 1),
            "total_return": round(total_return, 2),
            "final_equity": round(final, 2),
            "sharpe": round(sharpe, 2),
            "sortino": round(sortino, 2),
            "calmar": round(calmar, 2),
            "recovery_factor": round(abs(total_return / max_dd), 2) if max_dd > 0 else 0,
            "avg_rr": round(avg_win / avg_loss, 2) if avg_loss > 0 else 0,
            "largest_win": round(max(wins), 2) if wins else 0,
            "largest_loss": round(min(losses), 2) if losses else 0,
            "consecutive_wins": self._max_consecutive(returns, True),
            "consecutive_losses": self._max_consecutive(returns, False),
            "avg_trade_duration": round(sum(t.duration_minutes for t in self.trades) / total, 1) if total > 0 else 0,
            "equity_curve": equity,
            "monthly_returns": self._monthly_returns(),
        }

    def _equity_curve(self) -> List[float]:
        eq = [self.initial_balance]
        for t in self.trades:
            eq.append(eq[-1] + t.pnl)
        return eq

    def _monthly_returns(self) -> Dict[str, float]:
        monthly: Dict[str, float] = {}
        for t in self.trades:
            key = str(int(t.timestamp / 2592000))
            monthly[key] = monthly.get(key, 0) + t.pnl
        return {k: round(v, 2) for k, v in monthly.items()}

    def _max_consecutive(self, returns: List[float], winning: bool) -> int:
        max_c, current = 0, 0
        for r in returns:
            if (winning and r > 0) or (not winning and r < 0):
                current += 1
                max_c = max(max_c, current)
            else:
                current = 0
        return max_c

    @staticmethod
    def _stddev(data: List[float]) -> float:
        if len(data) < 2: return 0
        mean = sum(data) / len(data)
        return math.sqrt(sum((x - mean) ** 2 for x in data) / (len(data) - 1))

    def _empty_metrics(self) -> Dict[str, Any]:
        return {"total_trades": 0, "wins": 0, "losses": 0, "win_rate": 0, "profit_factor": 0, "expectancy": 0, "avg_win": 0, "avg_loss": 0, "max_drawdown": 0, "total_return": 0, "final_equity": self.initial_balance, "sharpe": 0, "sortino": 0, "calmar": 0, "recovery_factor": 0, "avg_rr": 0, "largest_win": 0, "largest_loss": 0, "consecutive_wins": 0, "consecutive_losses": 0, "avg_trade_duration": 0, "equity_curve": [self.initial_balance], "monthly_returns": {}}
