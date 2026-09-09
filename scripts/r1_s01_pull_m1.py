"""R1 S0.1 tahap 1 — tarik dataset M1 + M5/M15 segar via bridge.

Satu sumber: bridge /candles jalur DEFAULT (copy_rates_from_pos — jalur terbukti).
Cakupan yang diminta: 150.000 bar M1 (±92 hari trading — mencakup window backward
OOS 23 Apr–28 Jul + window training 29 Jul–8 Sep). M5/M15 segar ikut ditarik dari
sumber yang sama SATU PULL — dipakai kualifikasi untuk cek silang M1<->M5 pada
pasangan identik, dan untuk verifikasi identitas window training/OOS terhadap
dataset terkunci P3 (86014edf) & A2 (da72f41e).

Fail-closed: bridge down / MT5 tidak connected / dataset kosong -> exit 1.
Output: data/research/r1/dataset_{m1,m5,m15}.json + fetch_meta_m1.json
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research" / "r1"
TOKEN_FILE = ROOT / "data" / "bridge_token.txt"
BASE = "http://127.0.0.1:18888"

M1_COUNT = 150000  # target; server memotong bila history lebih pendek


def get(path: str) -> dict:
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    req = urllib.request.Request(BASE + path, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    health = get("/health")
    if not health.get("mt5_connected"):
        print("FATAL: bridge hidup tapi MT5 tidak connected:", health)
        return 1

    acc = get("/account")
    if not acc.get("connected"):
        print("FATAL: /account not connected")
        return 1

    m1 = get(f"/candles?symbol=XAUUSD&timeframe=M1&count={M1_COUNT}")
    m5 = get("/candles?symbol=XAUUSD&timeframe=M5&count=27000")
    m15 = get("/candles?symbol=XAUUSD&timeframe=M15&count=11000")
    if not m1.get("candles") or not m5.get("candles") or not m15.get("candles"):
        print("FATAL: dataset kosong:", {
            k: bool(v.get("candles")) for k, v in (("m1", m1), ("m5", m5), ("m15", m15))})
        return 1

    (OUT / "dataset_m1.json").write_text(json.dumps(m1), encoding="utf-8")
    (OUT / "dataset_m5_fresh.json").write_text(json.dumps(m5), encoding="utf-8")
    (OUT / "dataset_m15_fresh.json").write_text(json.dumps(m15), encoding="utf-8")
    meta = {
        "fetched_utc": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        "elapsed_s": round(time.time() - t0, 2),
        "endpoint": "/candles (copy_rates_from_pos)",
        "symbol": "XAUUSD",
        "requested_count": M1_COUNT,
        "received_count": len(m1["candles"]),
        "truncated_by_server": len(m1["candles"]) < M1_COUNT,
        "fresh_m5_count": len(m5["candles"]),
        "fresh_m15_count": len(m15["candles"]),
    }
    (OUT / "fetch_meta_m1.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    from datetime import datetime, timezone
    f = lambda ts: datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%MZ")
    c = m1["candles"]
    print(f"m1 : {len(c)} bar  {f(c[0]['time'])} .. {f(c[-1]['time'])}  (truncated={meta['truncated_by_server']})")
    print(f"m5 : {len(m5['candles'])} bar (segar, utk cek silang) | m15: {len(m15['candles'])} bar")
    print(f"fetch selesai dalam {meta['elapsed_s']}s -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
