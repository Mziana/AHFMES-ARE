"""A2 tahap 1 — tarik dataset backward OOS (multi-minggu) via bridge.

Satu sumber: bridge /candles jalur DEFAULT (copy_rates_from_pos — jalur yang
terbukti hidup di terminal ini; copy_rates_range terbukti beku). Read-only
terhadap MT5. Output deterministik ke data/research/backward/:
  dataset_m5.json, dataset_m15.json, account_snapshot.json, fetch_meta.json

Fail-closed: bridge down / not connected / dataset kosong -> exit 1, tanpa file.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research" / "backward"
TOKEN_FILE = ROOT / "data" / "bridge_token.txt"
BASE = "http://127.0.0.1:18888"

M5_COUNT = 27000   # ~53 minggu kalender trading; server memotong bila history lebih pendek
M15_COUNT = 11000  # ~57 minggu


def get(path: str) -> dict:
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    req = urllib.request.Request(BASE + path, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=60) as r:
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

    m5 = get(f"/candles?symbol=XAUUSD&timeframe=M5&count={M5_COUNT}")
    m15 = get(f"/candles?symbol=XAUUSD&timeframe=M15&count={M15_COUNT}")
    if not m5.get("candles") or not m15.get("candles"):
        print("FATAL: dataset kosong:", {k: bool(v.get('candles')) for k, v in (("m5", m5), ("m15", m15))})
        return 1

    (OUT / "dataset_m5.json").write_text(json.dumps(m5), encoding="utf-8")
    (OUT / "dataset_m15.json").write_text(json.dumps(m15), encoding="utf-8")
    (OUT / "account_snapshot.json").write_text(json.dumps(acc), encoding="utf-8")
    meta = {
        "fetched_utc": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        "elapsed_s": round(time.time() - t0, 2),
        "endpoint": "/candles (copy_rates_from_pos)",
        "symbol": "XAUUSD",
        "requested_counts": {"m5": M5_COUNT, "m15": M15_COUNT},
        "received_counts": {"m5": len(m5["candles"]), "m15": len(m15["candles"])},
        "truncated_by_server": {
            "m5": len(m5["candles"]) < M5_COUNT,
            "m15": len(m15["candles"]) < M15_COUNT,
        },
    }
    (OUT / "fetch_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    from datetime import datetime, timezone
    f = lambda ts: datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%MZ")
    print(f"m5 : {len(m5['candles'])} bar  {f(m5['candles'][0]['time'])} .. {f(m5['candles'][-1]['time'])}")
    print(f"m15: {len(m15['candles'])} bar  {f(m15['candles'][0]['time'])} .. {f(m15['candles'][-1]['time'])}")
    print(f"fetch selesai dalam {meta['elapsed_s']}s -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
