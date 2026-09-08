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

---

## ADDENDUM — Iterasi 3 (revisi H-REGIME-SLOPE-02, budget terakhir 3/3)

> Status efektif P4 = iterasi 3. Artefak kanonik: `data/research/p4/ablation_results.json`
> (results_hash `db04cb340367e6f1…`); iterasi 2 diarsipkan `ablation_results_iter2.json`.

| Arm (MICRO, B1 disabled terlabel) | Sig | Trade | Net | ExpNet |
|---|---|---|---|---|
| `no_b3_b4` — baseline juara iter-2 (long-only paksa) | 220 | 136 | +437.70 | **+3.22** |
| `slope` — revisi B3 dua-arah (EMA20 M15), B4 off | 199 | 136 | +94.39 | **+0.69 ← dibawa ke P5/P6** |
| `slope_b4` — revisi slope + B4 + B5 | 133 | 93 | +30.17 | +0.32 |

- Semua arm memenuhi kriteria mandatorial (≥30 trade, net > 0) — tapi hanya sebagai set in-sample.
- Revisi slope berfungsi sesuai desain (dua arah terbukti di data: SELL 148 / BUY 30 / NO_TRADE 3 pada sesi uji; saring chop aktif) — namun expNet lebih rendah dari long-only paksa yang menunggangi melt-up gold. Dipilih tetap `slope` untuk P5/P6 karena long-only paksa sudah terbukti rapuh OOS (P6 iter-1: worst-fold −9.14 di fold downtrend) — memilih baseline in-sample tertinggi berarti memilih bias regime.
- Ablation konsisten lintas iterasi: **B4 menurunkan expectancy** (0.69 → 0.32), **B5 bernilai** (dilepas → anjlok), B6 off via profil (sanity identik).
- **Regresi yang ditemukan & diperbaiki di iterasi 3**: sufiks diagnostic `|slope=…` bocor ke `bias` → exact-match B4/B5 gagal → 0 sinyal. Fix `f4be56f` + regression test `c937d20` (`tests/strategy_v2/test_p6_slope.py`, 4 kontrak).
- Kriteria "V2 > OLD-MICRO" tetap TERBUKA (harness engine lama belum diparalelkan).
- Nasib champion `slope` di P5/P6: lihat REPORT_P5.md (GAGAL) dan REPORT_P6.md (GAGAL_STATISTIK) — **kembali ke owner**.
