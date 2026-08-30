"""Phase 4b: Session, Momentum, Recovery, ProfitLock."""
import time, math
from datetime import datetime

class SessionAnalyzer:
    SESSIONS={"asian":(0,8,"low"),"london":(7,16,"high"),"new_york":(13,22,"high"),"overlap":(13,16,"very_high")}
    def current(self):
        h=datetime.utcnow().hour
        for n,(s,e,v) in self.SESSIONS.items():
            if s<=h<e: return {"session":n,"volatility":v,"hour":h}
        return {"session":"dead","volatility":"none","hour":h}
    def is_overlap(self): return self.current()["session"]=="overlap"
    def status(self): return self.current()

class MomentumDetector:
    def __init__(self): self.prices=[]; self.lookback=20
    def add(self,p): self.prices.append(p); self.prices=self.prices[-60:]
    def detect(self):
        if len(self.prices)<self.lookback: return {"exhaustion":False}
        r=self.prices[-self.lookback:]
        mom=r[-1]-r[0]
        vel=(r[-1]-r[-3])/3 if len(r)>=3 else 0
        pvel=(r[-3]-r[-6])/3 if len(r)>=6 else 0
        decel=abs(vel)<abs(pvel)*0.5 and abs(pvel)>0
        if decel and abs(mom)>0:
            return {"exhaustion":True,"dir":"LONG" if mom>0 else "SHORT","mom":round(mom,4),"vel":round(vel,4)}
        return {"exhaustion":False,"mom":round(mom,4),"vel":round(vel,4)}
    def status(self): return {"prices":len(self.prices)}

class DrawdownRecovery:
    def __init__(self,max_dd=15,recovery=5):
        self.max_dd=max_dd; self.recovery=recovery; self.peak=0; self.eq=0; self.recovering=False; self.reduced=False
    def update(self,equity):
        self.eq=equity; self.peak=max(self.peak,equity)
        dd=(self.peak-equity)/self.peak*100 if self.peak>0 else 0
        if dd>=self.max_dd and not self.recovering: self.recovering=True; self.reduced=True
        if self.recovering and dd<=self.recovery: self.recovering=False; self.reduced=False
        return {"dd":round(dd,1),"recovery":self.recovering,"reduced":self.reduced}
    def risk_mult(self): return 0.5 if self.reduced else 1.0
    def status(self):
        dd=(self.peak-self.eq)/self.peak*100 if self.peak>0 else 0
        return {"dd":round(dd,1),"max":self.max_dd,"recovery":self.recovering,"reduced":self.reduced}

class ProfitLock:
    def __init__(self,lock_at=2.0,trail=1.0):
        self.lock_at=lock_at; self.trail=trail; self.peak_pnl=0; self.locked=0; self.is_locked=False
    def update(self,pnl_pct):
        self.peak_pnl=max(self.peak_pnl,pnl_pct)
        if self.peak_pnl>=self.lock_at:
            nl=self.peak_pnl-self.trail
            if nl>self.locked: self.locked=nl
            self.is_locked=True
        return {"locked":self.is_locked,"level":round(self.locked,2),"peak":round(self.peak_pnl,2)}
    def should_close(self,pnl_pct):
        if self.is_locked and pnl_pct<=self.locked: return {"close":True,"reason":"Profit lock"}
        return {"close":False}
    def status(self): return {"locked":self.is_locked,"level":round(self.locked,2),"peak":round(self.peak_pnl,2)}