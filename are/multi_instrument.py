"""ARE Multi-Instrument, Correlation, Rotation, RiskBudget."""
import time, math
from typing import Dict, List, Any, Optional

INSTRUMENTS = {
    "XAUUSD": {"name": "Gold", "cat": "commodity", "pip": 0.01, "size": 100},
    "XAGUSD": {"name": "Silver", "cat": "commodity", "pip": 0.001, "size": 5000},
    "EURUSD": {"name": "Euro", "cat": "forex", "pip": 0.0001, "size": 100000},
    "GBPUSD": {"name": "Pound", "cat": "forex", "pip": 0.0001, "size": 100000},
    "USDJPY": {"name": "Yen", "cat": "forex", "pip": 0.01, "size": 100000},
    "AUDUSD": {"name": "Aussie", "cat": "forex", "pip": 0.0001, "size": 100000},
    "USOIL": {"name": "Oil", "cat": "commodity", "pip": 0.01, "size": 1000},
    "BTCUSD": {"name": "Bitcoin", "cat": "crypto", "pip": 1.0, "size": 1},
    "ETHUSD": {"name": "Ethereum", "cat": "crypto", "pip": 0.1, "size": 1},
    "SPX500": {"name": "S&P500", "cat": "index", "pip": 0.25, "size": 50},
    "NAS100": {"name": "Nasdaq", "cat": "index", "pip": 0.25, "size": 20},
}

class CorrelationEngine:
    def __init__(self): self.price_history = {}; self.lookback = 100
    def add_price(self, sym, price):
        self.price_history.setdefault(sym, []).append(price)
        if len(self.price_history[sym]) > self.lookback: self.price_history[sym] = self.price_history[sym][-self.lookback:]
    def get_returns(self, sym):
        p = self.price_history.get(sym, [])
        return [(p[i]-p[i-1])/p[i-1] for i in range(1, len(p))] if len(p) > 1 else []
    def calc_corr(self, s1, s2):
        r1, r2 = self.get_returns(s1), self.get_returns(s2)
        n = min(len(r1), len(r2))
        if n < 10: return 0
        r1, r2 = r1[-n:], r2[-n:]
        m1, m2 = sum(r1)/n, sum(r2)/n
        cov = sum((r1[i]-m1)*(r2[i]-m2) for i in range(n))/n
        s1d = math.sqrt(sum((r-m1)**2 for r in r1)/n)
        s2d = math.sqrt(sum((r-m2)**2 for r in r2)/n)
        return round(cov/(s1d*s2d), 4) if s1d>0 and s2d>0 else 0
    def matrix(self):
        syms = list(self.price_history.keys())
        return {s1: {s2: 1.0 if s1==s2 else self.calc_corr(s1,s2) for s2 in syms} for s1 in syms}
    def uncorrelated(self, threshold=0.3):
        m = self.matrix(); syms = list(m.keys()); pairs = []
        for i,s1 in enumerate(syms):
            for s2 in syms[i+1:]:
                c = abs(m[s1].get(s2,0))
                if c < threshold: pairs.append((s1,s2,c))
        return sorted(pairs, key=lambda x: x[2])

class StrategyRotation:
    def __init__(self): self.strategies = {}; self.active = None
    def register(self, sid, cfg): self.strategies[sid] = {"cfg": cfg, "score": 0, "trades": 0, "pnl": 0}
    def update(self, sid, pnl):
        if sid not in self.strategies: return
        s = self.strategies[sid]; s["trades"] += 1; s["pnl"] += pnl
        avg = s["pnl"]/s["trades"] if s["trades"]>0 else 0
        s["score"] = round(avg * math.sqrt(s["trades"]), 4)
    def select_best(self):
        if not self.strategies: return None
        best = max(self.strategies.items(), key=lambda x: x[1]["score"])
        self.active = best[0]; return best[0]
    def status(self): return {"active": self.active, "strategies": {s: {"score": v["score"],"trades": v["trades"],"pnl": round(v["pnl"],2)} for s,v in self.strategies.items()}}

class RiskBudget:
    def __init__(self, total=100000, max_risk=2.0): self.total=total; self.max_risk=max_risk; self.alloc={}
    def allocate(self, sid, pct): self.alloc[sid] = round(pct, 2)
    def max_position(self, sid): return round(self.total * self.alloc.get(sid,0)/100 * self.max_risk/100, 2)
    def status(self): return {"total": self.total, "max_risk": self.max_risk, "alloc": self.alloc, "allocated": round(sum(self.alloc.values()),2)}
