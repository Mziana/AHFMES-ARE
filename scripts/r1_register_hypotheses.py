"""R1 — registrasi 4 hipotesis paket (kontrak: docs/PAKET_HIPOTESIS_R1.md).

Idempoten: jika ID sudah ada di registry, keluar tanpa mengubah apa pun.
Deterministik: config_hash = sha256(canonical JSON value)[:16].
Genealogy wajib: parent_id minimal satu (kontrak WAJIB #4) — divalidasi
oleh strategy_v2.genealogy.new_hypothesis.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from strategy_v2.genealogy import new_hypothesis  # noqa: E402

REGISTRY = ROOT / "strategy_v2" / "contracts" / "hypothesis_registry.json"
CONTRACT = ROOT / "docs" / "PAKET_HIPOTESIS_R1.md"

MANIFEST = json.loads((ROOT / "strategy_v2" / "BACKWARD_OOS_MANIFEST.json").read_text(encoding="utf-8"))
TRAIN_WINDOW = MANIFEST["dataset_training_window"]
TRAIN_HASH = MANIFEST["dataset_training_hash"]


def cfg_hash(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]


VALUES = {
    "H-LOC-03": {
        "b4_max_distance_atr": 0.75,
        "previous_value_atr": 0.25,
        "scope": "MICRO",
        "frozen_basis": "training-window B4 distance diagnostic 2026-09-09",
        "expectation": "buckets 0.25-0.75 ATR = +2.09/+2.01 per trade; >0.75 = -2.90 (diagnostik training)",
        "threshold_t_star": 60.1,
        "threshold_note": "skala skor tak berubah -> T* champion tetap sah",
    },
    "H-EXEC-M1-01": {
        "execution_timeframe": "M1",
        "signal_timeframe": "M5",
        "bias_timeframe": "M15",
        "entry_rule": "first M1 open >= T (M5 signal bar close)",
        "no_lookahead": True,
        "expectation": "delay 1 bar M5 terbukti fatal (P5: -2.89..-5.56); ini perbaikan eksekusi, bukan edge",
    },
    "H-VOL-02": {
        "volume_component": "graded",
        "graded_definition": "volume_confirmation dari VR = volume sinyal / mean 5 bar sebelumnya (0..1, tanpa cliff-edge)",
        "binary_veto": "off",
        "inherits": "H-EXEC-M1-01 (M1 execution)",
        "recalibrate_threshold": True,
        "threshold_rule": "C1 rule dideklarasikan ulang persis: lowest T with exp_net_base>0 AND exp_net_must(x1.5+slip2)>0 AND trades>=30 (grid tetap)",
        "n_grid_points": 12,
    },
    "H-IBREAK-01": {
        "family": "inside_bar_breakout",
        "order_type": "pending_stop",
        "entry_rule": "STOP di luar range inside bar, arah = bias B3; skor >= T* dievaluasi saat pemasangan",
        "expiry_m1_bars": 12,
        "cancel_on_opposite_signal": True,
        "location_constraint": "dist_to_ema <= 0.75*ATR (sama Arm A) atau zona S/R M15",
        "fill_assumption": "trigger price + sel slippage (replay tidak tahu jalur intrabar)",
        "mandatory_slippage_cells_pts": [2, 5],
        "inherits": "H-EXEC-M1-01 (M1 execution)",
    },
}

SPEC = {
    "H-LOC-03": {
        "parents": ["H-LOC-02", "H-SCORE-01"],
        "statement": "Ambang lokasi B4 longgar dari 0.25 ke 0.75xATR mengembalikan zona emas (0.25-0.75) tanpa memasukkan zona rugi (>0.75) -> expectancy net naik.",
        "reason": "KILL_REVISE A5 + keputusan owner K1 (diagnostik bucket menunjukkan B4 0.25 membuang zona untung)",
        "source": "R1_package_arm_A",
    },
    "H-EXEC-M1-01": {
        "parents": ["H-SCORE-01"],
        "statement": "Eksekusi di M1 (open pertama >= close bar sinyal M5) memangkas delay 5 menit menjadi ~1 menit -> kerusakan delay turun drastis.",
        "reason": "KILL_REVISE A5 + keputusan owner K2 (P5/C3: delay 1 bar M5 membunuh semua sel biaya)",
        "source": "R1_package_arm_B",
    },
    "H-VOL-02": {
        "parents": ["H-VOL-01"],
        "statement": "Volume sebagai komponen skor graded (bukan veto biner) menambah informasi seleksi tanpa cliff-edge -> expectancy net arm C lebih baik dari arm B.",
        "reason": "Keputusan owner K4 (volume layak diuji dalam bentuk graded); konsekuensi: T* arm C dikalibrasi ulang dengan rule C1",
        "source": "R1_package_arm_C",
    },
    "H-IBREAK-01": {
        "parents": ["H-SCORE-01"],
        "statement": "Entri breakout Inside-Bar (pending STOP, expiry 12 bar M1, lokasi dekat EMA/S-R) menghasilkan set trade beda sifat yang expectancy net-nya unggul atas entri market-on-open.",
        "reason": "Keputusan owner K5+K8 (uji paralel entri beda sifat); fondasi: Varian 1 dokumen penelitian owner",
        "source": "R1_package_arm_D",
    },
}


def main() -> int:
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    hyps = reg["hypotheses"]

    existing = [k for k in VALUES if k in hyps]
    if existing:
        print(f"SKIP: sudah terdaftar: {existing}")
        return 0

    for hid, value in VALUES.items():
        spec = SPEC[hid]
        entry = new_hypothesis(
            id_=hid,
            parent_ids=spec["parents"],
            statement=spec["statement"],
            reason=spec["reason"],
            data_used=[
                "training window B4 distance diagnostic (2026-09-09)",
                "P5 cost-stress artifacts",
                "C1 threshold calibration artifacts",
                "docs/PAKET_HIPOTESIS_R1.md (kontrak owner)",
            ],
            data_period=f"{TRAIN_WINDOW} (dataset_hash {TRAIN_HASH})",
            config_hash=cfg_hash(value),
        )
        entry_full = {
            "id": hid,
            "value": value,
            "status": "HYPOTHESIS",
            "source": spec["source"],
            "genealogy": entry,
        }
        hyps[hid] = entry_full
        print(f"REGISTERED {hid} (config_hash {entry['config_hash']}, parents {spec['parents']})")

    # sanity: contract doc harus ada dan menyebut semua ID
    contract_text = CONTRACT.read_text(encoding="utf-8")
    missing = [hid for hid in VALUES if hid not in contract_text]
    if missing:
        raise SystemExit(f"kontrak tidak menyebut: {missing}")

    REGISTRY.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"registry total: {len(hyps)} hipotesis")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
