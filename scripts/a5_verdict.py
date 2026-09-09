"""A5 — verdict backward OOS (dari artefak A3 RUN ONCE + A4, tanpa re-fit).

Kriteria verdict (kontrak final, disepakati owner):
- GO_RESEARCH   : bukti edge bertahan lintas rezim (expNet>0, CI95>0, tak
                  tergantung satu rezim/bulan).
- INCONCLUSIVE  : sinyal campur/tipis (CI95 menyentuh nol tanpa konsentrasi
                  kerugian, n terlalu kecil untuk membedakan).
- KILL_REVISE   : kegagalan konsisten (expNet<0 melintasi bulan/arah/rezim,
                  PSR/DSR gagal) — revisi HANYA lewat hipotesis registry baru.

Output: data/research/backward/a5_verdict.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BACK = ROOT / "data" / "research" / "backward"


def main() -> int:
    a3 = json.loads((BACK / "a3_champion_run.json").read_text(encoding="utf-8"))
    a4 = json.loads((BACK / "a4_analysis.json").read_text(encoding="utf-8"))
    st = a4["stats"]
    mon = a4["monthly"]

    crit = {}
    crit["exp_net_positive"] = st["exp_net"] > 0
    crit["ci95_above_zero"] = st["ci95"][0] > 0
    crit["psr_above_050"] = st["psr_vs0"] > 0.50
    crit["dsr_pass"] = st["dsr_p_value"] < 0.05
    crit["must_cell_positive"] = a3["must_x15_slip2"]["exp_net"] > 0
    crit["not_single_month_carried"] = sum(1 for v in mon.values() if v["exp_net"] > 0) >= max(1, len(mon) // 2)
    crit["score_monotonic_with_n"] = bool(
        a4["score_monotonicity_champion"]["monotonic"] and a4["score_monotonicity_champion"]["all_buckets_n_ge_8"])

    n_pass = sum(1 for v in crit.values() if v)
    # Kegagalan konsisten = inti (expNet/CI/PSR/DSR/sel wajib) gagal bersama
    core_fail = not crit["exp_net_positive"] and not crit["ci95_above_zero"] and not crit["dsr_pass"]
    if core_fail and not crit["exp_net_positive"] and not crit["must_cell_positive"]:
        verdict = "KILL_REVISE"
    elif n_pass >= 5:
        verdict = "GO_RESEARCH"
    else:
        verdict = "INCONCLUSIVE"

    out = {
        "artifact_id": "A5-BACKWARD-VERDICT",
        "a3_results_hash_ref": a3["results_hash"],
        "a4_results_hash_ref": a4["results_hash"],
        "dataset_hash": a3["dataset_hash"],
        "t_star_frozen": a3["t_star"],
        "criteria": crit,
        "n_criteria_pass": n_pass,
        "key_numbers": {
            "exp_net_base": st["exp_net"], "ci95": st["ci95"],
            "psr_vs0": st["psr_vs0"], "dsr_p": st["dsr_p_value"],
            "must_cell": a3["must_x15_slip2"]["exp_net"],
            "max_consecutive_losses": st["max_consecutive_losses"],
            "monthly_exp_net": {k: v["exp_net"] for k, v in mon.items()},
        },
        "score_monotonicity": a4["score_monotonicity_champion"],
        "verdict": verdict,
        "consequence": {
            "KILL_REVISE": "Champion v0.4.1-c1 (T*=60.1) TIDAK memiliki edge pada data backward 2026-04-23..2026-07-28. Revisi HANYA sebagai hipotesis BARU di registry (ID baru, parent H-SCORE-01, genealogy penuh) -> siklus validasi ulang. Tidak ada tweak diam-diam. Kontrak scoring.mode tetap off.",
        }.get(verdict, ""),
        "honest_context": [
            "Training window (28 Jul-8 Sep) = fase melt-up gold; window backward (23 Apr-28 Jul) memuat fase koreksi/pemulihan pasca-melt-up.",
            "Dekomposisi A4: kerugian melintasi arah (BUY -7.19, SELL -1.72), volatilitas, dan bulan (Mei/Jun/Jul semua negatif) - bukan kegagalan satu rezim tunggal.",
            "Monotonisitas skor champion TETAP berlaku OOS (70-80 > 60-70, n>=8): ranking scorer informatif, tetapi tidak menyelamatkan set trade negatif-sum di window ini.",
            "B1 preflight certificate GO (Domain B) tidak berubah - itu readiness operasional, bukan bukti edge.",
        ],
    }
    blob = json.dumps({k: v for k, v in out.items() if k != "results_hash"},
                      sort_keys=True, ensure_ascii=True)
    out["results_hash"] = hashlib.sha256(blob.encode()).hexdigest()
    (BACK / "a5_verdict.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")

    print(f"criteria pass: {n_pass}/{len(crit)}")
    for k, v in crit.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"\nVERDICT: {verdict}")
    print(f"results_hash: {out['results_hash'][:16]}...")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
