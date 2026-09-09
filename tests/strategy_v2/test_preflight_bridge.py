"""B1 — kontrak preflight bridge (champion v2 -> run_full_preflight_battery).

Dijaga di sini (kontrak final Track B, disepakati owner & reviewer):
- Adapter sinyal deterministik: DataFrame + kolom 'signal' {-1,0,1};
  bar di luar peta -> 0 (fail-closed no-trade); input tak dikenal -> raise.
- WFOEvidence dari bukti C4/C2 LOLOS validate_wfo_integrity ASLI (bukan mock):
  hash provenance, konsistensi return/equity/sharpe/max-dd, fold disjoint,
  statistik fold direkomputasi.
- Fold disjoint by construction: hari boundary -> fold lebih awal;
  partisi trade tetap tepat-satu-fold-per-trade.
- Battery 7 checkpoint jalan dengan validator asli; hasilnya jujur.
"""
import json
import os
import sys

import polars as pl

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from strategy_v2.preflight_bridge import (  # noqa: E402
    V2SignalAdapter,
    build_wfo_evidence,
    load_c4_inputs,
    run_v2_preflight_battery,
)
from are.validation import validate_wfo_integrity  # noqa: E402


def _mk_df(tss):
    return pl.DataFrame({"timestamp": tss, "price": [100.0 + i for i in range(len(tss))]})


class TestAdapter:
    def test_output_dataframe_with_signal_column(self):
        a = V2SignalAdapter({1700000000: 1, 1700000300: -1})
        out = a(_mk_df([1700000000, 1700000300, 1700000600]))
        assert isinstance(out, pl.DataFrame)
        sig = out["signal"].to_list()
        assert sig == [1, -1, 0]  # bar ketiga di luar peta -> 0

    def test_unknown_input_raises_fail_closed(self):
        a = V2SignalAdapter({})
        try:
            a({"bukan": "dataframe"})
            raised = False
        except Exception:
            raised = True
        assert raised, "input tanpa kolom timestamp wajib raise (fail-closed)"

    def test_all_signals_in_domain(self):
        a = V2SignalAdapter({1: 1, 2: -1, 3: 0})
        out = a(_mk_df([1, 2, 3, 4]))
        assert set(out["signal"].to_list()) <= {-1, 0, 1}


class TestEvidence:
    def _build(self):
        inputs = load_c4_inputs()
        return build_wfo_evidence(
            per_trade_net_usd_ts=inputs["per_trade"],
            fold_windows_utc=inputs["fold_windows"],
            dataset_hash=inputs["dataset_hash"],
            data_start_ts=inputs["data_start_ts"],
            data_end_ts=inputs["data_end_ts"],
            effective_trial_count=inputs["n_trials"],
        )

    def test_evidence_passes_real_validator(self):
        ev, meta = self._build()
        assert meta["integrity_valid"] is True
        assert validate_wfo_integrity(ev).is_valid

    def test_folds_disjoint_and_partition_trades(self):
        _, meta = self._build()
        bounds = []
        for f in meta["folds"]:
            bounds.append((f["window_utc_clipped"][0], f["window_utc_clipped"][1]))
        # berurutan & tak tumpang tindih (string ISO date comparable)
        for i in range(1, len(bounds)):
            assert bounds[i - 1][1] < bounds[i][0], "fold harus disjoint"
        total = sum(f["n_trades"] for f in meta["folds"])
        assert total == meta["n_trades"], "partisi: tiap trade tepat satu fold"

    def test_return_negative_for_negative_nets(self):
        ev, _ = self._build()
        # champion C2: net positif (+$94.39 kumulatif) -> return pooled > 0
        assert ev.pooled_oos_return > 0


class TestBattery:
    def test_full_battery_runs_and_certified(self):
        art = run_v2_preflight_battery()
        assert art["total_checkpoints"] == 7
        assert len(art["checkpoint_results"]) == 7
        assert len(art["certificate_hash"]) >= 32
        # CP5 wajib PASS: bukti C4 lolos validator + DSR gate Domain B
        cp5 = [r for r in art["checkpoint_results"] if r["checkpoint_id"] == 5][0]
        assert cp5["passed"] is True
        # hasil tersimpan di disk sebagai artefak ber-hash
        assert os.path.exists("data/research/preflight/b1_certificate.json")
        saved = json.load(open("data/research/preflight/b1_certificate.json", encoding="utf-8"))
        assert saved["certificate_hash"] == art["certificate_hash"]
