"""Phase 3: Adaptive Learning, Sentiment, Calendar, Evolution."""
import time, math
from typing import Dict, List

class AdaptiveLearning:
    def __init__(self):
        self.experiences = []
        self.habitat_memory = {}
        self.pattern_memory = []

    def record_experience(self, trade):
        self.experiences.append({**trade, "ts": time.time()})
        h = trade.get("habitat", "unknown")
        if h not in self.habitat_memory:
            self.habitat_memory[h] = {"trades": 0, "wins": 0, "pnl": 0}
        hm = self.habitat_memory[h]
        hm["trades"] += 1
        if trade.get("pnl", 0) > 0: hm["wins"] += 1
        hm["pnl"] += trade.get("pnl", 0)

    def should_trade(self, habitat):
        hm = self.habitat_memory.get(habitat)
        if not hm or hm["trades"] < 5: return {"rec": "NO_DATA", "conf": 0}
        wr = hm["wins"] / hm["trades"] * 100
        if wr >= 60: return {"rec": "TRADE", "conf": min(wr, 95), "wr": round(wr,1)}
        if wr >= 45: return {"rec": "CAUTION", "conf": 50, "wr": round(wr,1)}
        return {"rec": "AVOID", "conf": round(100-wr,1), "wr": round(wr,1)}

    def best_habitats(self, n=5):
        ranked = []
        for h, m in self.habitat_memory.items():
            if m["trades"] >= 5:
                ranked.append({"habitat": h, "trades": m["trades"], "wr": round(m["wins"]/m["trades"]*100,1), "pnl": round(m["pnl"],2)})
        return sorted(ranked, key=lambda x: x["pnl"], reverse=True)[:n]

    def status(self):
        return {"experiences": len(self.experiences), "habitats": len(self.habitat_memory), "best": self.best_habitats(3)}


class NewsSentiment:
    BULL = ["surge","rally","gain","rise","bullish","breakout","strong","recovery","growth","up"]
    BEAR = ["crash","drop","fall","decline","bearish","plunge","weak","recession","fear","down"]
    HIGH_IMPACT = ["nfp","cpi","fed","fomc","rate decision","gdp","inflation","employment"]

    def __init__(self): self.cache = []; self.score = 0

    def analyze(self, headline):
        h = headline.lower()
        b = sum(1 for w in self.BULL if w in h)
        s = sum(1 for w in self.BEAR if w in h)
        hi = any(w in h for w in self.HIGH_IMPACT)
        sc = (b - s) / max(b + s, 1)
        label = "BULLISH" if sc > 0.2 else "BEARISH" if sc < -0.2 else "NEUTRAL"
        return {"headline": headline[:60], "score": round(sc,2), "label": label, "impact": hi}

    def update(self, headlines):
        results = [self.analyze(h) for h in headlines]
        avg = sum(r["score"] for r in results) / len(results) if results else 0
        self.score = round(avg, 2)
        self.cache = results
        return {"sentiment": self.score, "label": "BULLISH" if avg > 0.15 else "BEARISH" if avg < -0.15 else "NEUTRAL", "count": len(results)}

    def status(self): return {"sentiment": self.score, "cached": len(self.cache)}


class EconomicCalendar:
    def __init__(self): self.events = []

    def add(self, name, ts, impact, currency="USD"):
        self.events.append({"name": name, "time": ts, "impact": impact, "currency": currency})

    def should_pause(self, buffer=30):
        now = time.time()
        for e in self.events:
            diff = (e["time"] - now) / 60
            if 0 <= diff <= buffer and e["impact"] == "high":
                return {"pause": True, "reason": e["name"], "minutes": round(diff,0)}
        return {"pause": False}

    def upcoming(self, hours=24):
        now = time.time()
        return [e for e in self.events if 0 <= (e["time"]-now)/3600 <= hours]

    def status(self): return {"total": len(self.events), "upcoming": len(self.upcoming(24))}


class StrategyEvolution:
    def __init__(self): self.history = []

    def record(self, sid, params, results):
        self.history.append({"sid": sid, "params": params.copy(), "results": results.copy(), "ts": time.time()})

    def suggest(self, sid):
        runs = [h for h in self.history if h["sid"] == sid]
        if len(runs) < 2: return {"msg": "Need more runs", "runs": len(runs)}
        best = max(runs, key=lambda x: x["results"].get("profit_factor", 0))
        worst = min(runs, key=lambda x: x["results"].get("profit_factor", 0))
        diffs = [{"param": k, "best": v, "worst": worst["params"].get(k)} for k, v in best["params"].items() if v != worst["params"].get(k)]
        return {"best_pf": best["results"].get("profit_factor",0), "improvements": diffs, "runs": len(runs)}

    def status(self): return {"runs": len(self.history), "strategies": len(set(h["sid"] for h in self.history))}
