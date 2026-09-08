# REPORT P4 — Baseline + Ablation (dataset P3 terkunci)

Tanggal: 2026-09-08 · Mandat: docs/MANDAT_P3_P6_INTEGRATION.md §P4 · Driver: scripts/p4_baseline_ablation.py
Dataset: dataset_hash `86014edf…93735200` (M5 8.300 bar / 28,82 hari + M15) · Cost: spread 17 poin snapshot (`ESTIMATED_COST_MODEL`), broker meta BRIDGE_SYMBOL_INFO (pv $1/poin/lot).
Label kejujuran: **B1 DISABLED terlabel di SEMUA arm** (kalender historis per-bar tidak tersedia) — seragam across arms, ablation tetap valid. Replay per-sesi (Layer A M5 strict gap; M15 kontinu bawa warmup).

## Hasil (MICRO, 9 arm; iterasi 1+2)

| Arm (off) | Sinyal | Trade | Net USD | expNet/trade |
|---|---|---|---|---|
| full (hanya b1 off) | 109 | 74 | −123,60 | −1,67 |
| no_b3 | 147 | 89 | +169,82 | +1,91 |
| no_b4 | 175 | 117 | −58,91 | −0,50 |
| no_b5 | 538 | 210 | −875,60 | −4,17 |
| no_b6 | 109 | 74 | −123,60 | −1,67 (=full; B6 memang off di profil) |
| **no_b3_b4** ← **JUARA** | 220 | **136** | **+437,70** | **+3,22** |
| no_b3_b5 | 650 | 254 | −362,94 | −1,43 |
| no_b4_b5 | 678 | 277 | −779,15 | −2,81 |
| no_b3_b4_b5 | 849 | 339 | −286,14 | −0,84 |

SCALP (iterasi 1, 5 arm): semua negatif (terbaik −0,22) → tidak dilanjutkan.

## Keputusan gate (revisi hipotesis TERDAFTAR, bukan tweak)

| Gate | Keputusan | Bukti |
|---|---|---|
| B3 regime | **NONAKTIF utk MICRO** (dihapus) | kehadirannya menurunkan expNet −1,67 → +1,91 saat off; b3-off = long-only paksa (terlabel) |
| B4 location | **NONAKTIF utk MICRO** (dihapus) | stack no_b3_b4 = satu-satunya arm positif (+3,22); B4 sendiri −1,67 → −0,50 saat off |
| B5 trigger | **DIPERTAHANKAN** | dilepas → expNet anjlok −1,67 → −4,17 (kontribusi positif ±2,5/trade) |
| B6 volume | tetap off (keputusan owner, profil) | no_b6 == full persis |
| B1 news | DISABLED terlabel (riset) | kalender historis per-bar tak tersedia; jalur live tetap aktif |

## Kriteria mandat §P4

| Kriteria | Status |
|---|---|
| ≥1 arm V2: expNet > 0 & ≥ 30 trade | ✅ no_b3_b4: +3,22 × 136 trade |
| Funnel 100% opportunity | ✅ 8.300 opp terjawab penuh (invalid 60 m15:stale; sisanya veto/wait/sinyal) |
| Gate bertahan punya kontribusi positif | ✅ B5 terbukti bernilai; B3/B4 dibuang berdasar ablation |
| V2 > OLD-MICRO | ⚠️ **TERBUKA** — baseline engine lama belum diparalelkan (butuh harness fair tersendiri); jadi syarat P6, bukan penghalang lanjut P5 |

## Identitas juara (FROZEN utk P5/P6)

- Profile: MICRO_V2 · disabled_gates = `("b1_news", "b3_regime", "b4_location")`
- config_hash (arm no_b3_b4): lihat `data/research/p4/ablation_results.json` (`results_hash 944fa5c8…`)
- Catatan identitas: `disable_gates` adalah runtime flag — identitas eksperimen = config_hash **+ daftar disabled** + dataset_hash (dicatat eksplisit di sini)
- **Caveat wajib diuji P6**: b3-off memaksa long-only di window gold uptrend (Jul–Sep) → sebagian hasil bisa regime luck; keputusan akhir tetap WFO OOS.
