"""Validasi independen siklus C0-C4 (uji implementasi, bukan salinan klaim).

Pemeriksaan (semua independen terhadap isi REPORT_C.md):
  V1  Kontrak: STRATEGY_VERSION, H-SCORE-01.threshold, profil mode/candidate
  V2  Hash artefak: results_hash c1/c2/c3/c4 direkomputasi ulang == tersimpan
  V3  Determinisme scorer: evaluate_quality 2x pada input sama -> byte-identik
  V4  Determinisme replay: run_decision_replay 2x pada sesi sama -> byte-identik
  V5  Parity C1: replay threshold-null -> 199 sinyal, semua tercatat skornya
  V6  Semantik veto BQ: run T*=60.1 NATIVE (wiring kontrak) vs mekanisme
      blank->WAIT C1 pada replay threshold-null -> HARUS identik persis
      (membuktikan wiring BQ == simulasi kalibrasi)
  V7  Reproduksi C2: angka binary & scorer (base+must) == artefak c2
  V8  Reproduksi C3: sel wajib x1.5+slip2 == artefak c3
  V9  Reproduksi sel C1 T=60.1 == baris artefak c1

Output: data/research/validation/c_cycle_validation.json (ber-hash).
Exit 0 hanya jika SEMUA check PASS (fail-closed).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from strategy_v2 import broker_meta as bm
from strategy_v2 import registry
from strategy_v2 import scoring as SC
from strategy_v2.replay import run_decision_replay, run_execution_replay

P3 = ROOT / "data" / "research" / "p3"
SESSION_BREAK_S = 3600
DISABLE = ("b1_news", "b4_location")
BASE_SPREAD = 17.0
BALANCE = 1136.65
checks: list[dict] = []


def check(name: str, ok: bool, detail: str) -> None:
    checks.append({"check": name, "pass": bool(ok), "detail": detail})
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")


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


def results_hash(art: dict) -> str:
    blob = json.dumps({k: v for k, v in art.items() if k != "results_hash"},
                      sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def close(a, b, tol=1e-9) -> bool:
    return abs(float(a) - float(b)) <= tol


def main() -> int:
    m5 = json.loads((P3 / "dataset_m5.json").read_text(encoding="utf-8"))["candles"]
    m15 = json.loads((P3 / "dataset_m15.json").read_text(encoding="utf-8"))["candles"]
    acc = json.loads((P3 / "account_snapshot.json").read_text(encoding="utf-8"))
    dhash = json.loads((P3 / "qualification.json").read_text(encoding="utf-8"))["dataset_hash"]
    profile = registry.load_profile("MICRO")
    reg = registry.load_hypothesis_registry()
    meta = bm.load_broker_meta(acc)
    chash = registry.compute_config_hash(profile, reg, calendar_artifact_hash=None,
                                         broker_meta_hash=bm.broker_meta_hash(meta))
    cfg = {"config_hash": chash, "dataset_hash": dhash, "balance": BALANCE,
           "risk_percent": profile["risk"]["risk_percent"], "spread_points": BASE_SPREAD}

    # ── V1 kontrak ───────────────────────────────────────────────────────────
    h = registry.hypothesis(reg, "H-SCORE-01")["value"]
    check("V1.version", registry.STRATEGY_VERSION == "strategy_v2/0.4.1-c1",
          registry.STRATEGY_VERSION)
    check("V1.h_score_threshold", close(h["threshold"], 60.1), f"{h['threshold']}")
    check("V1.profile_mode_off", profile["scoring"]["mode"] == "off",
          f"mode={profile['scoring']['mode']} (kontrak tidak mengubah perilaku live)")
    check("V1.profile_candidate", close(profile["scoring"]["thresholds"]["candidate"], 60.1),
          str(profile["scoring"]["thresholds"]["candidate"]))

    # ── V2 integritas hash artefak ───────────────────────────────────────────
    arts = {}
    for name, path in (("c1", "c1/score_calibration.json"), ("c2", "c2/scorer_vs_binary.json"),
                       ("c3", "c3/scorer_cost_stress.json"), ("c4", "c4/scorer_wfo_stats.json")):
        art = json.loads((ROOT / "data/research" / path).read_text(encoding="utf-8"))
        arts[name] = art
        recomputed = results_hash(art)
        check(f"V2.hash_{name}", recomputed == art["results_hash"],
              f"{recomputed[:16]}… == {art['results_hash'][:16]}…")

    # ── V3/V4 determinisme ───────────────────────────────────────────────────
    sl_calc = {"sl_points": 250.0, "tp_points": 300.0, "skip": False}
    bars = m5[:120]
    base = SC.evaluate_quality(bars, None, "BUY_ONLY", 1.2, 17.0, sl_calc,
                               "hammer", profile["scoring"]["weights"], dict(h))
    base2 = SC.evaluate_quality(bars, None, "BUY_ONLY", 1.2, 17.0, sl_calc,
                                "hammer", profile["scoring"]["weights"], dict(h))
    check("V3.scorer_deterministic", json.dumps(base, sort_keys=True) == json.dumps(base2, sort_keys=True),
          f"final_score={base['final_score']} identik 2x")

    ss = sessions(m5)
    long_sess = max((s for s in ss if len(s) >= 40), key=len)[:400]
    r1 = run_decision_replay(long_sess, m15, profile, reg, None, cfg, disable_gates=DISABLE)
    r2 = run_decision_replay(long_sess, m15, profile, reg, None, cfg, disable_gates=DISABLE)
    check("V4.replay_deterministic",
          json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True),
          f"{len(r1)} record identik 2x")

    # ── V5 parity threshold-null (mode replay C1) ────────────────────────────
    prof_null = {**profile, "scoring": {**profile["scoring"], "mode": "score",
                                        "thresholds": {"candidate": None, "strong": None,
                                                       "premium": None}}}
    recs_null: list[dict] = []
    for sess in ss:
        if len(sess) < 40:
            continue
        recs_null.extend(run_decision_replay(sess, m15, prof_null, reg, None, cfg,
                                             disable_gates=DISABLE))
    sig_null = [r for r in recs_null if r["decision"] in ("BUY", "SELL")]
    all_scored = all(isinstance(r.get("quality_score"), dict) for r in sig_null)
    check("V5.parity_signals", len(sig_null) == 199, f"{len(sig_null)} == 199 (parity P4/P5)")
    check("V5.all_signals_scored", all_scored, f"{sum(all_scored is False for _ in [0])} tanpa skor")

    # ── V6/V7 replay T*=60.1 NATIVE + binary + eksekusi ──────────────────────
    prof_t = {**profile, "scoring": {**profile["scoring"], "mode": "score"}}
    recs_t: list[dict] = []
    for sess in ss:
        if len(sess) < 40:
            continue
        recs_t.extend(run_decision_replay(sess, m15, prof_t, reg, None, cfg,
                                          disable_gates=DISABLE))
    sig_t = [r for r in recs_t if r["decision"] in ("BUY", "SELL")]
    vetoed = [r for r in recs_t if r["all_gate_results"]["b8_quality"] == "FAIL:score_low"]
    thr = 60.1
    scores_below = [r for r in sig_null if r["quality_score"]["final_score"] < thr]
    check("V6.native_kept_equals_blank_mechanism", len(sig_t) == len(sig_null) - len(scores_below),
          f"native {len(sig_t)} == null {len(sig_null)} - veto {len(scores_below)}")
    check("V6.kept_scores_above_threshold",
          all(r["quality_score"]["final_score"] >= thr for r in sig_t),
          f"min kept score = {min(r['quality_score']['final_score'] for r in sig_t):.2f}")
    check("V6.veto_count", len(vetoed) == len(scores_below),
          f"{len(vetoed)} veto BQ native == {len(scores_below)} simulasi")

    ex_b_base = run_execution_replay(recs_null, m5, profile, spread_points=BASE_SPREAD,
                                     slippage_points=0.0, delay_bars=0, broker_meta=meta,
                                     spread_label="SNAPSHOT_P3")
    ex_b_must = run_execution_replay(recs_null, m5, profile, spread_points=BASE_SPREAD * 1.5,
                                     slippage_points=2.0, delay_bars=0, broker_meta=meta,
                                     spread_label="ESTIMATED_COST_MODEL")
    ex_s_base = run_execution_replay(recs_t, m5, prof_t, spread_points=BASE_SPREAD,
                                     slippage_points=0.0, delay_bars=0, broker_meta=meta,
                                     spread_label="SNAPSHOT_P3")
    ex_s_must = run_execution_replay(recs_t, m5, prof_t, spread_points=BASE_SPREAD * 1.5,
                                     slippage_points=2.0, delay_bars=0, broker_meta=meta,
                                     spread_label="ESTIMATED_COST_MODEL")

    b = arts["c2"]["binary"]
    s = arts["c2"]["scorer"]
    check("V7.binary_base", close(ex_b_base["expectancy_net_usd"], b["base"]["exp_net"])
          and ex_b_base["executed_trades"] == b["base"]["trades"],
          f"{ex_b_base['executed_trades']} trade, expNet {ex_b_base['expectancy_net_usd']:+.4f}")
    check("V7.binary_must", close(ex_b_must["expectancy_net_usd"], b["must_x15_slip2"]["exp_net"]),
          f"{ex_b_must['expectancy_net_usd']:+.4f}")
    check("V7.scorer_base", close(ex_s_base["expectancy_net_usd"], s["base"]["exp_net"])
          and ex_s_base["executed_trades"] == s["base"]["trades"],
          f"{ex_s_base['executed_trades']} trade, expNet {ex_s_base['expectancy_net_usd']:+.4f}")
    check("V7.scorer_must", close(ex_s_must["expectancy_net_usd"], s["must_x15_slip2"]["exp_net"]),
          f"{ex_s_must['expectancy_net_usd']:+.4f}")

    cell3 = arts["c3"]["must_pass_cell"]
    check("V8.c3_must_cell", close(ex_s_must["expectancy_net_usd"], cell3["expectancy_net_usd"]),
          f"artefak {cell3['expectancy_net_usd']:+.4f}")

    c1row = next(c for c in arts["c1"]["causal_threshold_curve"] if c["threshold"] == 60.1)
    check("V9.c1_row_T60.1", close(c1row["exp_net_base"], ex_s_base["expectancy_net_usd"])
          and close(c1row["exp_net_must"], ex_s_must["expectancy_net_usd"]),
          f"base {c1row['exp_net_base']:+.4f} / must {c1row['exp_net_must']:+.4f}")

    n_fail = sum(1 for c in checks if not c["pass"])
    out = {
        "dataset_hash": dhash, "strategy_version": registry.STRATEGY_VERSION,
        "n_checks": len(checks), "n_fail": n_fail,
        "checks": checks,
        "verdict": "ALL_PASS" if n_fail == 0 else f"FAILED({n_fail})",
    }
    blob = json.dumps({k: v for k, v in out.items() if k != "results_hash"},
                      sort_keys=True, ensure_ascii=True)
    out["results_hash"] = hashlib.sha256(blob.encode()).hexdigest()
    vdir = ROOT / "data" / "research" / "validation"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "c_cycle_validation.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    print(f"\nVERDICT: {out['verdict']} ({len(checks) - n_fail}/{len(checks)} PASS) "
          f"| results_hash: {out['results_hash'][:16]}…")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
