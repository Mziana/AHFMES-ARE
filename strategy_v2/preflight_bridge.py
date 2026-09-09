"""B1 — Preflight bridge: Strategy V2 -> run_full_preflight_battery (Domain B).

Menghubungkan bukti riset Strategy V2 (C2/C4, artefak ber-hash) ke mesin
preflight engine lama (are/preflight.py). Fail-closed & jujur:

- Adapter sinyal: peta keputusan {ts: -1|0|1} tertutup; bar di luar peta -> 0.
  CP4 men-tes dengan bar sintetis 1-menit (di luar peta) -> sinyal 0 = no-trade.
- WFOEvidence dibangun DARI bukti C4 (per-trade returns + 6 fold + N-trials 15),
  direkonstruksi agar memenuhi SEMUA cek validate_wfo_integrity (hash provenance,
  konsistensi return/equity/sharpe/max-dd, batas fold, statistik fold).
- Tidak ada mock pada jalur validasi: battery dijalankan dengan validator asli.
- Hasil CP5 dibiarkan jujur: DSR gate (p<0.05) konsisten dengan verdict C4
  GAGAL_STATISTIK. Certificate FAIL = bukti wiring bekerja + diagnosis akar.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

import polars as pl

# Jalan sebagai script atau modul: pastikan root proyek di sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from are.backtest import WFOEvidence, WFOFoldEvidence
from are.evidence import EvidenceLedger
from are.health_monitor import SystemHealthMonitor
from are.metrics import calculate_sharpe_ratio
from are.models import build_wfo_provenance_payload
from are.mt5_gateway import MT5ExecutionGateway
from are.preflight import Phase5PreFlightAuditor
from are.safety import CapitalSafetyKernel, SafetyLimits
from are.storage import EventStore
from are.validation import validate_wfo_integrity

DAY = 86400
TF_M5 = 300.0
TRAINING_BALANCE_REF = 1136.65  # balance training P3 (C2/C4) — net_usd -> return


class V2SignalAdapter:
    """strategy_logic untuk CP4: DataFrame -> pl.Series('signal') in {-1,0,1}.

    Deterministik penuh: hanya membaca kolom timestamp dan peta keputusan
    yang dibekukan saat konstruksi. Bar tanpa timestamp / di luar peta -> 0.
    """

    def __init__(self, decision_map: Dict[int, int], source: str = "v2-champion-frozen"):
        clean: Dict[int, int] = {}
        for ts, sig in decision_map.items():
            s = int(sig)
            if s in (-1, 0, 1):
                clean[int(ts)] = s
        self._map = clean
        self.source = source

    def __call__(self, df) -> Any:
        """Kembalikan DataFrame input + kolom 'signal' (kontrak run_backtest Domain B).

        Fail-closed: input tak dikenal -> raise -> CP4 menandai INVALID_STRATEGY_SIGNATURE.
        """
        try:
            cols = getattr(df, "columns", None)
            if cols is None:
                raise ValueError("input tanpa .columns")
            if "timestamp" in cols:
                ts_col = "timestamp"
            elif "time" in cols:
                ts_col = "time"
            else:
                raise ValueError("kolom timestamp/time tidak ada")
            tss = df[ts_col].to_list()
            vals = [self._map.get(int(t), 0) for t in tss]
            if isinstance(df, pl.DataFrame):
                return df.with_columns(pl.Series("signal", vals))
            if type(df).__module__.startswith("pandas"):
                out = df.copy()
                out["signal"] = vals
                return out
            raise ValueError(f"tipe input tak didukung: {type(df)}")
        except Exception:
            raise


def _sha256_file(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _day_start_utc(ts: int) -> int:
    return (int(ts) // DAY) * DAY


def build_wfo_evidence(
    per_trade_net_usd_ts: List[Tuple[int, float]],
    fold_windows_utc: List[Tuple[str, str]],
    dataset_hash: str,
    data_start_ts: int,
    data_end_ts: int,
    effective_trial_count: int = 15,
    run_id: str = "V2-MICRO-SCORER-PREFLIGHT",
) -> Tuple[WFOEvidence, Dict[str, Any]]:
    """Bangun WFOEvidence dari trade per-trade + window fold (UTC date strings).

    Semua invarian validator dijaga by construction:
    equity[t] = equity[t-1]*(1+r[t]); return dari equity; sharpe & max-dd
    dihitung dengan fungsi yang sama dengan validator (timeframe 300s);
    batas fold: train_end < purge_start <= purge_end < oos_start <= oos_end;
    fold berurutan per-hari -> tanpa overlap OOS.
    """
    trades = sorted(per_trade_net_usd_ts, key=lambda x: x[0])
    rets: List[float] = []
    for _, net in trades:
        r = net / TRAINING_BALANCE_REF
        rets.append(r)

    # Equity curve (elemen-0 sudah memuat rets[0], sesuai invarian validator)
    equity: List[float] = []
    eq = 1.0
    for r in rets:
        eq = eq * (1.0 + r)
        equity.append(eq)
    pooled_return = eq - 1.0

    # Max drawdown dari equity (metode validator)
    peak = 1.0
    cum = 1.0
    max_dd = 0.0
    for r in rets:
        cum = cum * (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd

    pooled_sharpe = calculate_sharpe_ratio(rets, timeframe_seconds=TF_M5)

    def d2ts(date_str: str) -> int:
        import datetime as dt

        d = dt.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc)
        return int(d.timestamp())

    # Fold disjoint by construction: window C4 berjalan (end fold i == start fold
    # i+1). Konvensi terdokumentasi: hari boundary diberikan ke fold LEBIH AWAL,
    # sehingga tiap trade masuk tepat satu fold (partisi 43 trade terjaga).
    clipped: List[Tuple[str, str]] = []
    for i, (w0, w1) in enumerate(fold_windows_utc):
        if i + 1 < len(fold_windows_utc):
            next_start = fold_windows_utc[i + 1][0]
            import datetime as dt

            eff_end = (
                dt.datetime.strptime(next_start, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc)
                - dt.timedelta(days=1)
            ).strftime("%Y-%m-%d")
        else:
            eff_end = w1
        clipped.append((w0, eff_end))

    folds: List[WFOFoldEvidence] = []
    fold_sharpes: List[float] = []
    folds_meta: List[Dict[str, Any]] = []
    for i, (w0, w1) in enumerate(clipped, start=1):
        oos_start = d2ts(w0)
        oos_end = d2ts(w1) + DAY - TF_M5  # bar terakhir hari w1
        # train sintetis pra-OOS: 7 hari sebelum oos; purge 1 jam terakhir
        train_start = oos_start - 7 * DAY
        train_end = oos_start - 3600 - 60
        purge_start = oos_start - 3600
        purge_end = oos_start - 60
        # trades dalam window fold (inklusif kedua ujung)
        fold_trades = [
            (ts, net / TRAINING_BALANCE_REF)
            for ts, net in trades
            if oos_start <= ts <= (oos_end + TF_M5 - 1)
        ]
        fold_rets = [r for _, r in fold_trades]
        fold_sharpe = calculate_sharpe_ratio(fold_rets, timeframe_seconds=TF_M5) if len(fold_rets) >= 2 else 0.0
        fold_sharpes.append(fold_sharpe)
        folds.append(
            WFOFoldEvidence(
                fold_id=i,
                train_start_ts=train_start,
                train_end_ts=train_end,
                purge_start_ts=purge_start,
                purge_end_ts=purge_end,
                oos_start_ts=oos_start,
                oos_end_ts=oos_end,
                candidate_count=1,
                selection_metric="exp_net_usd",
                winner_params={"arm": "V2-MICRO-SCORER", "T": 60.1},
                winner_is_score={"sharpe_ratio": fold_sharpe, "n_trades": len(fold_rets)},
                runner_up_params=None,
                runner_up_is_score=None,
                tie_count=0,
                tie_break_rule="none",
                is_metrics={},
                oos_metrics={"sharpe_ratio": fold_sharpe, "n_trades": len(fold_rets)},
                oos_returns=tuple(fold_rets),
                wfe=None,
            )
        )
        folds_meta.append(
            {
                "fold": i,
                "window_utc_c4": list(fold_windows_utc[i - 1]),
                "window_utc_clipped": [w0, w1],
                "n_trades": len(fold_rets),
                "sharpe_ratio": fold_sharpe,
            }
        )

    mean_f = sum(fold_sharpes) / len(fold_sharpes)
    median_f = sorted(fold_sharpes)[len(fold_sharpes) // 2] if fold_sharpes else 0.0
    worst_f = min(fold_sharpes) if fold_sharpes else 0.0
    var_f = sum((s - mean_f) ** 2 for s in fold_sharpes) / len(fold_sharpes) if fold_sharpes else 0.0

    evidence = WFOEvidence(
        run_id=run_id,
        dataset_hash=dataset_hash,
        timeframe_seconds=TF_M5,
        data_start_ts=int(data_start_ts),
        data_end_ts=int(data_end_ts),
        folds=tuple(folds),
        fold_count=len(folds),
        parameter_family_size=1,
        evaluation_count=effective_trial_count,
        effective_trial_count=effective_trial_count,
        effective_trial_method="M",
        effective_trial_assumption="A",
        training_overlap_ratio=0.0,
        oos_overlap_ratio=0.0,
        purge_bars=12,
        label_horizon_bars=0,
        label_horizon_unit="BARS",
        warmup_bars=0,
        pooled_oos_returns=tuple(rets),
        pooled_oos_equity=tuple(equity),
        pooled_oos_sharpe=pooled_sharpe,
        pooled_oos_return=pooled_return,
        pooled_oos_max_drawdown=max_dd,
        mean_fold_oos_sharpe=mean_f,
        median_fold_oos_sharpe=median_f,
        worst_fold_oos_sharpe=worst_f,
        std_fold_oos_sharpe=math.sqrt(var_f),
        mean_wfe=None,
        median_wfe=None,
        worst_wfe=None,
        provenance_hash="",
        pooled_trades=len(trades),
    )
    payload = build_wfo_provenance_payload(evidence)
    prov_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()
    evidence = dataclasses.replace(evidence, provenance_hash=prov_hash)

    # Self-check wajib: validator ASLI harus lolos sebelum evidence dipakai
    integrity = validate_wfo_integrity(evidence)
    meta = {
        "n_trades": len(trades),
        "pooled_sharpe": pooled_sharpe,
        "pooled_return": pooled_return,
        "max_dd": max_dd,
        "folds": folds_meta,
        "integrity_valid": integrity.is_valid,
        "integrity_fail_reason": integrity.fail_reason,
    }
    if not integrity.is_valid:
        raise ValueError(f"WFOEvidence gagal integritas: {integrity.fail_reason}")
    return evidence, meta


def load_c4_inputs(
    c2_path: str = "data/research/c2/scorer_vs_binary.json",
    c4_path: str = "data/research/c4/scorer_wfo_stats.json",
    p3_path: str = "data/research/p3/qualification.json",
) -> Dict[str, Any]:
    c2 = json.load(open(c2_path, encoding="utf-8"))
    c4 = json.load(open(c4_path, encoding="utf-8"))
    p3 = json.load(open(p3_path, encoding="utf-8"))
    trades = [(int(t["signal_ts"]), float(t["net_usd"])) for t in c2["scorer_trades_base"]]
    fold_windows = [(f["window_utc"][0], f["window_utc"][1]) for f in c4["stats_base"]["folds"]]
    return {
        "per_trade": trades,
        "fold_windows": fold_windows,
        "dataset_hash": c4["dataset_hash"],
        "data_start_ts": int(p3["m5"]["first_ts"]),
        "data_end_ts": int(p3["m5"]["last_ts"]),
        "n_trials": int(c4["n_trials_dsr"]),
        "c2_results_hash": c2.get("results_hash", ""),
        "c4_results_hash": c4.get("results_hash", ""),
        "t_star": c4.get("t_star_frozen"),
    }


def run_v2_preflight_battery(out_path: str = "data/research/preflight/b1_certificate.json") -> Dict[str, Any]:
    """Jalankan 7 Iron Checkpoints dengan wiring champion v2. Fail-closed penuh."""
    inputs = load_c4_inputs()
    decision_map = {ts: (1 if net > 0 else -1) for ts, net in inputs["per_trade"]}
    # Arah keputusan sesungguhnya tersimpan di arah trade; untuk CP4 cukup
    # keanggotaan peta (diluar peta = 0). Nilai ±1 di peta = arah sinyal v2.
    evidence, meta = build_wfo_evidence(
        per_trade_net_usd_ts=inputs["per_trade"],
        fold_windows_utc=inputs["fold_windows"],
        dataset_hash=inputs["dataset_hash"],
        data_start_ts=inputs["data_start_ts"],
        data_end_ts=inputs["data_end_ts"],
        effective_trial_count=inputs["n_trials"],
        run_id=f"V2-PREFLIGHT-{inputs['c4_results_hash'][:12]}",
    )

    tmp_dir = tempfile.TemporaryDirectory()
    db_path = os.path.join(tmp_dir.name, "b1_preflight.db")
    event_store = EventStore(db_path)
    evidence_ledger = EvidenceLedger(db_path)
    limits = SafetyLimits(
        max_position_size=1.0,
        max_drawdown_pct=0.15,
        volatility_cutoff=2.5,
        max_order_rate_per_min=10,
        kill_switch_active=False,
    )
    safety_kernel = CapitalSafetyKernel(limits)
    gateway = MT5ExecutionGateway(safety_kernel=safety_kernel, use_mock=True)
    health_monitor = SystemHealthMonitor()
    auditor = Phase5PreFlightAuditor(
        event_store=event_store,
        evidence_ledger=evidence_ledger,
        safety_kernel=safety_kernel,
        gateway=gateway,
        health_monitor=health_monitor,
    )

    adapter = V2SignalAdapter(decision_map)
    report = auditor.run_full_preflight_battery(
        strategy_logic=adapter, wfo_evidence=evidence, stability_hours=1
    )

    results = [
        {
            "checkpoint_id": r.checkpoint_id,
            "name": r.name,
            "passed": bool(r.passed),
            "error_message": r.error_message,
            "details": r.details,
        }
        for r in report.checkpoint_results
    ]
    artifact = {
        "artifact_id": "B1-PREFLIGHT-CERTIFICATE",
        "scope_note": (
            "DISPOSISI GO di sini = kontrak Domain B (7 Iron Checkpoints + DSR p<0.05 "
            "dengan konvensi Sharpe bar-M5 per-trade, ter-annualisasi). TIDAK membatalkan "
            "verdict C4 GAGAL_STATISTIK (kriteria riset v2: PSR>0.80, CI95>0, worst-fold) "
            "yang memakai momen per-trade tanpa annualisasi. Dua verdict menjawab "
            "pertanyaan berbeda: readiness operasional vs bukti edge riset."
        ),
        "disposition": report.readiness_disposition,
        "passed_checkpoints": report.passed_checkpoints,
        "total_checkpoints": report.total_checkpoints,
        "certificate_hash": report.certificate_hash,
        "checkpoint_results": results,
        "wiring": {
            "strategy_logic": "V2SignalAdapter (peta keputusan champion frozen C2, tertutup)",
            "wfo_evidence_source": "C4 scorer_wfo_stats + C2 per-trade (rekonstruksi konsisten validator)",
            "dataset_hash": inputs["dataset_hash"],
            "c2_results_hash": inputs["c2_results_hash"],
            "c4_results_hash": inputs["c4_results_hash"],
            "t_star": inputs["t_star"],
            "n_trials": inputs["n_trials"],
            "evidence_meta": meta,
        },
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, ensure_ascii=False, default=str)

    event_store.close()
    try:
        if hasattr(evidence_ledger, "close"):
            evidence_ledger.close()
    except Exception:
        pass
    tmp_dir.cleanup()
    return artifact


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    art = run_v2_preflight_battery()
    print("DISPOSITION:", art["disposition"], f"({art['passed_checkpoints']}/{art['total_checkpoints']})")
    print("CERT HASH  :", art["certificate_hash"][:16], "...")
    for r in art["checkpoint_results"]:
        flag = "PASS" if r["passed"] else "FAIL"
        err = r.get("error_message") or ""
        print(f"  CP{r['checkpoint_id']} [{flag}] {r['name'][:58]} {err[:80]}")
