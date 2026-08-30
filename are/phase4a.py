"""Phase 4: Production modules."""
import time, math
from typing import Dict, List

class ExecutionBridge:
    def __init__(self): self.connected=False; self.mt5=None; self.magic=20260830; self.orders=[]
    def connect(self):
        try:
            import MetaTrader5 as mt5
            if not mt5.initialize(): return {"ok":False,"error":"MT5 init failed"}
            i=mt5.account_info(); self.connected=True; self.mt5=mt5
            return {"ok":True,"account":{"login":i.login,"balance":i.balance,"equity":i.equity}}
        except ImportError: return {"ok":False,"error":"pip install MetaTrader5"}
        except Exception as e: return {"ok":False,"error":str(e)}
    def disconnect(self):
        if self.mt5: self.mt5.shutdown(); self.connected=False
    def send_order(self,sym,dir,lot,sl,tp,comment="ARE"):
        if not self.connected: return {"ok":False,"error":"Not connected"}
        mt5=self.mt5; tick=mt5.symbol_info_tick(sym)
        price=tick.ask if dir=="BUY" else tick.bid
        otype=mt5.ORDER_TYPE_BUY if dir=="BUY" else mt5.ORDER_TYPE_SELL
        req={"action":mt5.TRADE_ACTION_DEAL,"symbol":sym,"volume":lot,"type":otype,"price":price,"sl":sl,"tp":tp,"magic":self.magic,"comment":comment}
        r=mt5.order_send(req)
        if r.retcode!=mt5.TRADE_RETCODE_DONE: return {"ok":False,"error":r.comment}
        self.orders.append({"ticket":r.ticket,"sym":sym,"dir":dir,"lot":lot,"ts":time.time()})
        return {"ok":True,"ticket":r.ticket,"price":r.price}
    def close_all(self,sym=None):
        if not self.connected: return {"ok":False}
        pos=self.mt5.positions_get.magic(self.magic); closed=[]
        for p in (pos or []):
            if sym and p.symbol!=sym: continue
            ot=self.mt5.ORDER_TYPE_SELL if p.type==0 else self.mt5.ORDER_TYPE_BUY
            tk=self.mt5.symbol_info_tick(p.symbol); pr=tk.bid if p.type==0 else tk.ask
            r=self.mt5.order_send({"action":self.mt5.TRADE_ACTION_DEAL,"symbol":p.symbol,"volume":p.volume,"type":ot,"price":pr,"position":p.ticket,"magic":self.magic,"comment":"ARE_CLOSE"})
            if r and r.retcode==self.mt5.TRADE_RETCODE_DONE: closed.append(p.ticket)
        return {"ok":True,"closed":closed}
    def status(self): return {"connected":self.connected,"orders":len(self.orders)}

class AnomalyDetector:
    def __init__(self): self.buf=[]; self.threshold=3.0
    def add(self,p): self.buf.append(p); self.buf=self.buf[-100:]
    def detect(self):
        if len(self.buf)<20: return {"anomaly":False}
        r=self.buf[-20:]; m=sum(r)/len(r); s=math.sqrt(sum((x-m)**2 for x in r)/len(r))
        if s==0: return {"anomaly":False}
        z=(self.buf[-1]-m)/s
        if abs(z)>self.threshold: return {"anomaly":True,"zscore":round(z,2),"dir":"UP" if z>0 else "DOWN"}
        return {"anomaly":False,"zscore":round(z,2)}
    def status(self): return {"size":len(self.buf),"threshold":self.threshold}