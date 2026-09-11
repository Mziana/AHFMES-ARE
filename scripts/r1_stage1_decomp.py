"""R1 — Dekomposisi lengkap Stage 1 (kontrak §3: "kembali ke owner dengan
dekomposisi lengkap"). TRAINING window saja (86014edf…) — OOS TIDAK disentuh.

Diagnostik untuk keputusan owner (bukan verdict, bukan tweak):
  D1  Dekomposisi sesi (blok koarse §6: Asia/London/Overlap/NY-late) + arah
      untuk champion & Arm A — di blok jam mana edge lahir/matir.
  D2  Break-even spread (sel wajib slip2): seberapa besar penurunan spread
      dari 25.5 poin agar expNet_must > 0 — menimbang opsi negosiasi broker.
  D3  Arm A stabilitas zona emas: expNet trade berdasarkan jarak B4 aktual
      (0-0.25 / 0.25-0.5 / 0.5-0.75 ATR) — apakah zona emas konsisten per band.
  D4  Biaya sebagai % dari TP: realisasi gross vs biaya per trade per arm.

Output: data/research/r1/stage1_decomp.json (ber-hash) + ringkasan stdout.
PURE diagnostik: tidak ada keputusan strategi baru, tidak ada penggantian param.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from strategy_v2 import broker_meta as bm
from strategy_v2 import registry
from strategy_v2.execution_m1 import run_execution_m1
from strategy_v2.replay import run_decision_replay, run_execution_replay

P3 = ROOT / "data" / "research" / "p3"
R1 = ROOT / "data" / "research" / "r1"
SESSION_BREAK_S = 3600
DISABLE_CHAMPION = ("b1_news", "b4_location")
BASE_SPREAD = 17.0
MUST_SPREAD = BASE_SPREAD * 1.5   # 25.5 poin
BALANCE = 1136.65

# Blok sesi koarse kontrak §6 (UTC)
SESSION_BLOCKS = (
    ("asia", 0, 7),
    ("london", 7, 12),
    ("overlap", 12, 16),
    ("ny_late", 16, 24),
)


def sessions(m5: list) -> list[list]:
    out, cur = [], [m5[0]]
    for b in m5[1:]:
        if int(b["time"]) - int(cur[-1]["time"]) >= SESSION_BREAK_S:
            out.append(cur)
            cur = [b]
        else:
            cur.append(b)
    out.append(cur)
    return out


def block_of(ts: int) -> str:
    h = (ts // 3600) % 24
    for name, lo, hi in SESSION_BLOCKS:
        if lo <= h < hi:
            return name
    return "ny_late"


def group_stats(trades: list) -> dict:
    n = len(trades)
    if not n:
        return {"n": 0, "net": 0.0, "exp_net": None, "wr": None}
    return {
        "n": n,
        "net": round(sum(t["net_usd"] for t in trades), 2),
        "exp_net": round(sum(t["net_usd"] for t in trades) / n, 4),
        "wr": round(sum(1 for t in trades if t["net_usd"] > 0) / n, 4),
    }


def decompose(trades: list, key_fn) -> dict:
    groups: dict = {}
    for t in trades:
        k = key_fn(t)
        groups.setdefault(k, []).append(t)
    return {k: group_stats(v) for k, v in sorted(groups.items())}


def breakeven_spread(recs: list, m5: list, profile: dict, meta: dict, engine: str) -> dict:
    """Cari spread terkecil (grid 1 poin) dengan slip=2 yang membuat expNet > 0.
    Baseline: dari 25.5 turun; juga laporkan expNet pada 17 (base) utk sanity."""
    grid = [25.5, 24.0, 22.0, 20.0, 18.0, 17.0]
    cells = []
    for sp in grid:
        if engine == "m5":
            ex = run_execution_replay(recs, m5, profile, spread_points=sp,
                                      slippage_points=2.0, delay_bars=0,
                                      broker_meta=meta, spread_label="DECOMP")
        else:
            ex = run_execution_m1(recs, m5, M1, profile, spread_points=sp,
                                  slippage_points=2.0, broker_meta=meta,
                                  spread_label="DECOMP")
        cells.append({"spread_points": sp, "n": ex["executed_trades"],
                      "exp_net": ex["expectancy_net_usd"], "net": ex["net_usd"]})
        print(f"  spread={sp:5.1f} n={ex['executed_trades']:3d} expNet={ex['expectancy_net_usd']:+.4f}")
    ok = [c for c in cells if c["exp_net"] > 0 and c["n"] >= 30]
    return {"cells": cells,
            "breakeven_spread": max(c["spread_points"] for c in ok) if ok else None,
            "note": "spread maksimum yang masih expNet>0 (slip2, n>=30)" if ok
                    else "tidak ada spread pada grid yang menyelamatkan"}


M1 = None   # diisi di main


def main() -> int:
    global M1
    m5 = json.loads((P3 / "dataset_m5.json").read_text(encoding="utf-8"))["candles"]
    m15 = json.loads((P3 / "dataset_m15.json").read_text(encoding="utf-8"))["candles"]
    M1 = json.loads((R1 / "dataset_m1.json").read_text(encoding="utf-8"))["candles"]
    acc = json.loads((P3 / "account_snapshot.json").read_text(encoding="utf-8"))
    dhash = json.loads((P3 / "qualification.json").read_text(encoding="utf-8"))["dataset_hash"]
    meta = bm.load_broker_meta(acc)
    reg = registry.load_hypothesis_registry()
    profile0 = registry.load_profile("MICRO")
    cfg = {"config_hash": "r1_decomp", "dataset_hash": dhash, "balance": BALANCE,
           "risk_percent": profile0["risk"]["risk_percent"], "spread_points": BASE_SPREAD}

    def replay(variant_profile, disable=DISABLE_CHAMPION):
        recs = []
        for sess in sessions(m5):
            if len(sess) < 40:
                continue
            recs.extend(run_decision_replay(sess, m15, variant_profile, reg, None, cfg,
                                            disable_gates=disable))
        return recs

    # ── champion & Arm A (sama dengan driver Stage 1 — deterministik) ────────
    champ = replay(profile0)
    profA = copy.deepcopy(profile0)
    profA["location"]["ema_pullback_distance_atr"] = \
        registry.hypothesis(reg, "H-LOC-03")["value"]["b4_max_distance_atr"]
    recsA = replay(profA, disable=("b1_news",))

    ex_champ = run_execution_replay(champ, m5, profile0, spread_points=BASE_SPREAD,
                                    slippage_points=0.0, delay_bars=0, broker_meta=meta,
                                    spread_label="SNAPSHOT_P3")
    ex_A = run_execution_replay(recsA, m5, profile0, spread_points=BASE_SPREAD,
                                slippage_points=0.0, delay_bars=0, broker_meta=meta,
                                spread_label="SNAPSHOT_P3")
    trades_champ, trades_A = ex_champ["trades"], ex_A["trades"]
    print(f"champion trades={len(trades_champ)}  armA trades={len(trades_A)}")

    out: dict = {"stage": "R1_STAGE1_DECOMP", "dataset_hash": dhash,
                 "purpose": "owner decision support (KILL_ALL decomposition)"}

    # ── D1: sesi × arah ──────────────────────────────────────────────────────
    def by_block_dir(t):
        return f"{block_of(t['signal_ts'])}|{'BUY' if t['direction'] == 'BUY' else 'SELL'}"

    d1 = {
        "champion_session_direction": decompose(trades_champ, by_block_dir),
        "armA_session_direction": decompose(trades_A, by_block_dir),
        "blocks": [b[0] for b in SESSION_BLOCKS],
    }
    print("\nD1 champion sesi|arah:")
    for k, v in d1["champion_session_direction"].items():
        print(f"  {k:20s} n={v['n']:3d} expNet={v['exp_net']}")
    print("D1 armA sesi|arah:")
    for k, v in d1["armA_session_direction"].items():
        print(f"  {k:20s} n={v['n']:3d} expNet={v['exp_net']}")

    # ── D2: break-even spread (sel wajib slip2) ─────────────────────────────
    print("\nD2 break-even spread champion (M5, slip2):")
    d2_champ = breakeven_spread(champ, m5, profile0, meta, "m5")
    print("D2 break-even spread Arm A (M5, slip2):")
    d2_A = breakeven_spread(recsA, m5, profile0, meta, "m5")

    # ── D3: Arm A zona emas per band jarak B4 aktual ────────────────────────
    def band_of(t):
        rec = next((r for r in recsA if r["evaluation_timestamp"] == t["signal_ts"]), None)
        dist = (rec or {}).get("setup") or {}
        d = dist.get("distance_atr")
        if d is None:
            return "na"
        if d <= 0.25:
            return "0-0.25"
        if d <= 0.5:
            return "0.25-0.5"
        return "0.5-0.75"

    d3 = {"armA_by_b4_distance_band": decompose(trades_A, band_of),
          "bands": ["0-0.25", "0.25-0.5", "0.5-0.75"]}
    print("\nD3 armA by B4 distance band:")
    for k, v in d3["armA_by_b4_distance_band"].items():
        print(f"  {k:10s} n={v['n']:3d} expNet={v['exp_net']}")

    # ── D4: biaya sebagai % dari TP realisasi ───────────────────────────────
    def cost_share(trades):
        gross = sum(t["gross_usd"] for t in trades)
        cost = sum(t["cost_usd"] for t in trades)
        win_t = [t for t in trades if t["net_usd"] > 0]
        return {"gross": round(gross, 2), "cost": round(cost, 2),
                "cost_pct_of_gross": round(cost / gross, 4) if gross else None,
                "avg_win_usd": round(sum(t["net_usd"] for t in win_t) / len(win_t), 4) if win_t else None}

    d4 = {"champion": cost_share(trades_champ), "armA": cost_share(trades_A)}
    print(f"\nD4 cost share: champion {d4['champion']['cost_pct_of_gross']} | "
          f"armA {d4['armA']['cost_pct_of_gross']}")

    out.update({"d1_session_direction": d1, "d2_breakeven_spread": {"champion": d2_champ, "armA": d2_A},
                "d3_armA_distance_bands": d3, "d4_cost_share": d4})
    blob = json.dumps(out, sort_keys=True, ensure_ascii=True)
    out["results_hash"] = hashlib.sha256(blob.encode()).hexdigest()
    R1.mkdir(parents=True, exist_ok=True)
    (R1 / "stage1_decomp.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    print(f"\nresults_hash: {out['results_hash'][:16]}…")
    print(f"artefak: {R1 / 'stage1_decomp.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
