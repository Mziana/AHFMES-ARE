# REPORT P3 — Data Qualification (XAUUSD M5+M15)

Tanggal: 2026-09-08 · Mandat: docs/MANDAT_P3_P6_INTEGRATION.md §P3 · Script: scripts/p3_qualify.py
Sumber: bridge MT5 `copy_rates_from_pos` (jalur range terbukti beku — tidak dipakai) + snapshot `/account`.

## Dataset

| TF | Bar | Window (UTC) | Hari trading |
|---|---|---|---|
| M5 | 8.300 | 2026-07-28 05:50 → 2026-09-08 13:20 | **28,82** |
| M15 | 2.900 | 2026-07-26 22:00 → 2026-09-08 13:15 | **30,20** |

## Kriteria mandat vs hasil terukur

| Kriteria | Ambang | M5 | M15 | Status |
|---|---|---|---|---|
| Duplicate timestamp | = 0 | 0 | 0 | ✅ |
| NaN / OHLC invalid | = 0 | 0 | 0 | ✅ |
| Volume missing/negatif | = 0 | 0 | 0 | ✅ |
| Gap intra-hari (< 3600s) | ≤ 0,1% bar | 0 (0,0000%) | 0 (0,0000%) | ✅ |
| Session break (≥ 3600s) | diklasifikasi | 30 (weekend) | 31 | ✅ |
| Kontinuitas grid timezone (Δ kelipatan interval) | 0 off-grid | 0 | 0 | ✅ |
| tick_volume distribusi | dilaporkan | p50/p95/p99 = 891/1671/2227 | 2673/4906/6488 | ✅ |
| Spread | snapshot + unit | raw 1700 PRICE_1E4 → **17,0 poin** | — | ✅ |
| Symbol spec | dari snapshot | contract_size 100, point 0,01, stops_level 10 | — | ✅ |
| Umur data | ≥ 14 hari | 28,82 | 30,20 | ✅ |

## Identitas eksperimen (DIKUNCI untuk P4–P6)

- `dataset_hash` = `86014edf84ad866d6a06a73832e6a67a3ca87c3b93831c1d49828c7c93735200`
- `broker_meta_hash` = lihat `data/research/p3/qualification.json` (source=BRIDGE_SYMBOL_INFO, pv=$1/poin/lot)
- tick_value broker (10,0) TIDAK dipakai — konflik vs `order_calc_profit` ($1/poin/lot) tercatat (`COMPUTED_CONFLICT`)
- Catatan spread: per-bar historis tidak tersedia dari candle bridge → model biaya P4 memakai snapshot 17 poin (label `ESTIMATED_COST_MODEL`)

## Keputusan

**LAYAK** untuk P4 (baseline + ablation) — dataset_hash terkunci; perubahan dataset apa pun setelah titik ini membatalkan angka P4–P6 dan mewajibkan pengulangan.
