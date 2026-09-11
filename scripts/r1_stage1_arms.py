"""R1 Stage 1 — Kalibrasi & seleksi 4 arm paralel (kontrak PAKET_HIPOTESIS_R1.md §3).

Training window SAJA (dataset P3, hash 86014edf…). Model biaya identik semua
arm: base spread 17 poin, $1/poin/lot; sel wajib ×1.5 + slip2 + delay0
dilaporkan untuk setiap arm. REAL ORDER OFF — semua di replay.

Arm (tangga A ⊂ B ⊂ {C, D}; satu perubahan per arm):
  A (H-LOC-03)     : champion (B3 slope, B1+B4 off) + B4 ambang 0.75×ATR —
                     B4 diaktifkan KEMBALI dengan ambang baru dari registry.
                     Skala skor tak berubah → T*=60.1 tetap sah (kontrak §2).
  B (H-EXEC-M1-01) : champion persis (B4 tetap off) + eksekusi M1
                     (run_execution_m1, zero-delay first-available).
  C (H-VOL-02)     : B + kalibrasi ulang T* rule C1 persis (grid tetap,
                     "terendah yang lolos") — sweep 12 titik atas skor BQ
                     champion (bukan skor bermutasi — skala komponen tidak
                     berubah dengan perubahan weight murni, eksak menurut C1).
  D (H-IBREAK-01)  : B + trigger inside-bar (pending STOP, expiry 12 bar M1),
                     skor ≥ T* dievaluasi saat pemasangan (kontrak registry).

Aturan seleksi (dideklarasikan sebelum hasil — kontrak §3):
  - Arm lolos ⇔ expNet_base > 0 ∧ expNet_must > 0 ∧ n ≥ 30.
  - Pemenang = expNet_must tertinggi di antara yang lolos.
  - Selisih ≤ $0.5/trade → keduanya lanjut.
  - Semua gagal → KILL semua, kembali ke owner.

Output: data/research/r1/stage1_arms.json (ber-hash).
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
DISABLE_CHAMPION = ("b1_news", "b4_location")   # FROZEN champion P4 iter-3
BASE_SPREAD = 17.0
BALANCE = 1136.65
MIN_TRADES = 30
PARITY_SIGNALS = 199   # parity champion P4 iter-3 (identik P5/C1)


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


def pct(sorted_vals: list, p: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * p / 100.0
    f, c = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def worst_streak(trades: list) -> int:
    worst = cur = 0
    for t in trades:
        cur = cur + 1 if t["net_usd"] <= 0 else 0
        worst = max(worst, cur)
    return worst


def pf(trades: list) -> float:
    wins = sum(t["net_usd"] for t in trades if t["net_usd"] > 0)
    losses = -sum(t["net_usd"] for t in trades if t["net_usd"] < 0)
    return round(wins / losses, 4) if losses > 0 else (float("inf") if wins > 0 else 0.0)


def metrics(trades: list) -> dict:
    n = len(trades)
    return {"n": n,
            "wr": round(sum(1 for t in trades if t["net_usd"] > 0) / n, 4) if n else None,
            "pf": pf(trades) if n else None,
            "worst_streak": worst_streak(trades) if n else 0}


def main() -> int:
    m5 = json.loads((P3 / "dataset_m5.json").read_text(encoding="utf-8"))["candles"]
    m15 = json.loads((P3 / "dataset_m15.json").read_text(encoding="utf-8"))["candles"]
    m1 = json.loads((R1 / "dataset_m1.json").read_text(encoding="utf-8"))["candles"]
    qual = json.loads((R1 / "m1_qualification.json").read_text(encoding="utf-8"))
    if qual.get("verdict", "").startswith("LAYAK") is False:
        print(f"FATAL: dataset M1 tidak layak: {qual.get('verdict')}")
        return 1
    acc = json.loads((P3 / "account_snapshot.json").read_text(encoding="utf-8"))
    dhash = json.loads((P3 / "qualification.json").read_text(encoding="utf-8"))["dataset_hash"]
    meta = bm.load_broker_meta(acc)
    reg = registry.load_hypothesis_registry()
    profile0 = registry.load_profile("MICRO")

    cfg = {"config_hash": "r1_stage1", "dataset_hash": dhash, "balance": BALANCE,
           "risk_percent": profile0["risk"]["risk_percent"], "spread_points": BASE_SPREAD}

    # ── Decision replay SEKALI per varian kontrak (training window) ──────────
    def replay(variant_profile: dict, disable=DISABLE_CHAMPION):
        recs = []
        for sess in sessions(m5):
            if len(sess) < 40:
                continue
            recs.extend(run_decision_replay(sess, m15, variant_profile, reg, None, cfg,
                                            disable_gates=disable))
        return recs

    # Champion (dasar tangga; parity 199 wajib)
    champ = replay(profile0)
    n_champ = sum(1 for r in champ if r["decision"] in ("BUY", "SELL"))
    print(f"champion parity: {n_champ} signals (harus {PARITY_SIGNALS})")
    if n_champ != PARITY_SIGNALS:
        print("FATAL: parity champion pecah — identitas eksperimen berubah; Stage 1 batal")
        return 1

    # ── ARM A (H-LOC-03): B4 ON kembali dgn 0.75×ATR (registry) ──────────────
    profA = copy.deepcopy(profile0)
    profA["location"]["ema_pullback_distance_atr"] = \
        registry.hypothesis(reg, "H-LOC-03")["value"]["b4_max_distance_atr"]
    recsA = replay(profA, disable=("b1_news",))   # B4 aktif → hanya B1 yang off

    # ── ARM B (H-EXEC-M1-01): champion persis, eksekusi M1 ───────────────────
    recsB = champ

    # ── ARM C (H-VOL-02): champion + sweep T* rule C1 (BQ threshold sweep) ───
    # BQ aktif mode-on DENGAN thresholds.candidate=NULL (persis kondisi C1:
    # skor dicatat untuk SEMUA sinyal, BQ tidak memveto — semantik V5/V6).
    # Sweep T* = blank→WAIT atas skor, persis mekanisme C1 (tervalidasi V6:
    # identik dengan wiring BQ native).
    profC = copy.deepcopy(profile0)
    profC["scoring"] = {**profile0["scoring"], "mode": "on",
                        "thresholds": {**profile0["scoring"]["thresholds"], "candidate": None}}
    recsC_scored = replay(profC)

    # ── ARM D (H-IBREAK-01): B + inside-bar trigger (pending STOP) ───────────
    profD = copy.deepcopy(profile0)
    profD["b5_mode"] = "inside_bar"
    recsD = replay(profD)

    results: dict = {}

    def run_exec_m5(recs, spread, slip):
        return run_execution_replay(recs, m5, profile0, spread_points=spread,
                                    slippage_points=float(slip), delay_bars=0,
                                    broker_meta=meta, spread_label="SNAPSHOT_P3")

    def run_exec_m1(recs, spread, slip):
        return run_execution_m1(recs, m5, m1, profile0, spread_points=spread,
                                slippage_points=float(slip), broker_meta=meta,
                                spread_label="SNAPSHOT_P3")

    def arm_report(name, hyp, signals, base_ex, must_ex, extra=None):
        tb, tm = base_ex["trades"], must_ex["trades"]
        r = {
            "hypothesis": hyp,
            "signals": signals,
            "base": {"spread": BASE_SPREAD, "slip": 0, **metrics(tb),
                     "exp_net": base_ex["expectancy_net_usd"], "net": base_ex["net_usd"]},
            "must": {"spread": BASE_SPREAD * 1.5, "slip": 2, **metrics(tm),
                     "exp_net": must_ex["expectancy_net_usd"], "net": must_ex["net_usd"]},
            "pass": bool(base_ex["expectancy_net_usd"] > 0
                         and must_ex["expectancy_net_usd"] > 0
                         and len(tb) >= MIN_TRADES and len(tm) >= MIN_TRADES),
        }
        if extra:
            r.update(extra)
        results[name] = r
        print(f"{name}: signals={signals} base(n={r['base']['n']}, exp={r['base']['exp_net']:+.4f}) "
              f"must(n={r['must']['n']}, exp={r['must']['exp_net']:+.4f}) pass={r['pass']}")

    # Arm A/B: eksekusi M5 (A: skala tak berubah; B: identitas = champion tapi
    # wajib tetap dieksekusi M5 base utk baseline tangga) — B sendiri dieksekusi M1.
    baseA = run_exec_m5(recsA, BASE_SPREAD, 0.0)
    mustA = run_exec_m5(recsA, BASE_SPREAD * 1.5, 2.0)
    arm_report("A", "H-LOC-03", sum(1 for r in recsA if r["decision"] in ("BUY", "SELL")),
               baseA, mustA)

    baseB_m5 = run_exec_m5(recsB, BASE_SPREAD, 0.0)   # = champion 199 (sanity)
    mustB_m5 = run_exec_m5(recsB, BASE_SPREAD * 1.5, 2.0)
    arm_report("B_m5_champion", "H-SCORE-01 (baseline)",
               n_champ, baseB_m5, mustB_m5)

    baseB = run_exec_m1(recsB, BASE_SPREAD, 0.0)
    mustB = run_exec_m1(recsB, BASE_SPREAD * 1.5, 2.0)
    arm_report("B", "H-EXEC-M1-01", n_champ, baseB, mustB,
               extra={"pending_stats": None})

    # Arm C: sweep T* atas skor BQ champion (rule C1: terendah yang lolos)
    scores = [r["quality_score"]["final_score"] for r in recsC_scored
              if r["decision"] in ("BUY", "SELL") and isinstance(r.get("quality_score"), dict)]
    ss = sorted(scores)
    grid = sorted({round(pct(ss, p), 1) for p in
                   (0, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95)})
    n_scored = sum(1 for r in recsC_scored if r["decision"] in ("BUY", "SELL")
                   and isinstance(r.get("quality_score"), dict))
    print(f"Arm C: scored {n_scored}/{n_champ} signals")
    if n_scored != n_champ:
        print("FATAL: ada sinyal tanpa skor (fail-closed) — Arm C batal")
        return 1
    cells = []
    for T in grid:
        filt = [dict(r, decision="WAIT") if
                (r["decision"] in ("BUY", "SELL") and r["quality_score"]["final_score"] < T)
                else r for r in recsC_scored]
        kept = sum(1 for r in filt if r["decision"] in ("BUY", "SELL"))
        eb = run_exec_m1(filt, BASE_SPREAD, 0.0)          # C mewarisi eksekusi M1 (⊂ B)
        em = run_exec_m1(filt, BASE_SPREAD * 1.5, 2.0)
        cells.append({"threshold": T, "signals_kept": kept,
                      "trades_base": eb["executed_trades"], "exp_net_base": eb["expectancy_net_usd"],
                      "trades_must": em["executed_trades"], "exp_net_must": em["expectancy_net_usd"]})
        print(f"  C T={T:6.1f} kept={kept:3d} base: n={eb['executed_trades']:3d} "
              f"expNet={eb['expectancy_net_usd']:+.4f} | must: n={em['executed_trades']:3d} "
              f"expNet={em['expectancy_net_usd']:+.4f}")
    viable = [c for c in cells if c["exp_net_base"] > 0 and c["exp_net_must"] > 0
              and c["trades_base"] >= MIN_TRADES and c["trades_must"] >= MIN_TRADES]
    t_star = min(viable, key=lambda c: c["threshold"]) if viable else None
    results["C"] = {
        "hypothesis": "H-VOL-02",
        "signals": n_champ,
        "threshold_curve": cells,
        "n_trials_evaluated": len(cells),
        "selected_threshold": t_star["threshold"] if t_star else None,
        "selection_rule": "lowest T with exp_net_base>0 AND exp_net_must>0 AND trades>=30",
        "verdict": "T_FOUND" if t_star else "NO_VIABLE_THRESHOLD",
        "pass": bool(t_star),
    }
    print(f"C: T*={results['C']['selected_threshold']} verdict={results['C']['verdict']}")

    # Arm D: eksekusi M1 + pending STOP
    baseD = run_exec_m1(recsD, BASE_SPREAD, 0.0)
    mustD = run_exec_m1(recsD, BASE_SPREAD * 1.5, 2.0)
    # sel slippage wajib {2,5} untuk Arm D (kontrak §2)
    slip5 = run_exec_m1(recsD, BASE_SPREAD * 1.5, 5.0)
    arm_report("D", "H-IBREAK-01", sum(1 for r in recsD if r["decision"] in ("BUY", "SELL")),
               baseD, mustD,
               extra={"pending_stats": baseD.get("pending_stats"),
                      "must_slip5_exp_net": slip5["expectancy_net_usd"],
                      "must_slip5_n": slip5["executed_trades"]})

    # ── Seleksi (kontrak §3) ─────────────────────────────────────────────────
    passed = {k: v for k, v in results.items()
              if k in ("A", "B", "C", "D") and v.get("pass")}
    for k, v in passed.items():
        v["exp_must_for_selection"] = (v["must"]["exp_net"] if k != "C"
                                       else next((c["exp_net_must"] for c in v["threshold_curve"]
                                                  if c["threshold"] == v["selected_threshold"]), None))
    ranking = sorted(passed.items(), key=lambda kv: -(kv[1]["exp_must_for_selection"] or -9e9))
    if not ranking:
        selection = {"verdict": "KILL_ALL", "winners": [],
                     "note": "Semua arm gagal — kembali ke owner dengan dekomposisi lengkap"}
    else:
        best = ranking[0]
        winners = [k for k, v in ranking
                   if (best[1]["exp_must_for_selection"] or 0) - (v["exp_must_for_selection"] or 0) <= 0.5]
        selection = {"verdict": "WINNERS_SELECTED", "winners": winners,
                     "ranking": [{"arm": k, "exp_must": v["exp_must_for_selection"]}
                                 for k, v in ranking],
                     "dual_winner_rule": "selisih <= 0.5 $/trade → keduanya lanjut (kontrak §3)"}
    results["selection"] = selection
    print(f"\nSELEKSI: {selection['verdict']} winners={selection['winners']}")

    out = {
        "stage": "R1_STAGE_1",
        "contract": "docs/PAKET_HIPOTESIS_R1.md",
        "dataset_hash": dhash,
        "m1_dataset_hash": qual.get("m1_dataset_hash"),
        "m1_verdict": qual.get("verdict"),
        "owner_deviation_confirmed": "2026-09-09 'lanjut stage 1' = konfirmasi deviasi 5 gap 120s",
        "champion_parity_signals": n_champ,
        "strategy_version": registry.STRATEGY_VERSION,
        "arms": {k: v for k, v in results.items() if k != "selection"},
        "selection": selection,
    }
    blob = json.dumps(out, sort_keys=True, ensure_ascii=True)
    out["results_hash"] = hashlib.sha256(blob.encode()).hexdigest()
    R1.mkdir(parents=True, exist_ok=True)
    (R1 / "stage1_arms.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    print(f"results_hash: {out['results_hash'][:16]}…")
    print(f"artefak: {R1 / 'stage1_arms.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
