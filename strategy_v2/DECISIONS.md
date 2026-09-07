# DECISIONS — strategy_v2 (append-only)

Format: tanggal | keputusan | alasan.

- 2026-09-08 | `zone clustering` di `zones.py` memakai definisi desain §B4
  (swing confirmed 5 kiri+kanan atas CLOSED bars, cluster 0.75×ATR(M15),
  band ±0.5×ATR, maks 5 zona/sisi, window 200 bar) | persis kontrak; DILARANG
  memanggil `getSupportResistanceZones` indicators.ts (lookahead `highs[i+k]`).
- 2026-09-08 | Dataset M5 7 Sep = 222 bar (00:00–18:25 UTC, kontinu) dari
  bridge `copy_rates_from_pos` (count=1200); jalur `copy_rates_range` beku
  200 bar (dokumentasi bridge P2-17). Bar 18:30–24:00 tidak tersedia →
  dicatat sebagai limitasi di REPORT_P2.md, TIDAK diinterpolasi/karangan.
- 2026-09-08 | Volume gate memakai `volume` dari dataset bridge (tick_volume
  broker) dengan terminologi "tick-activity proxy" | desain §B6.
- 2026-09-08 | News calendar 7 Sep tidak tersedia historis (bridge tidak
  menyediakan kalender historis) → replay P2 menjalankan B1 dengan
  policy `NEWS_CALENDAR_UNAVAILABLE` (fail-closed, reason code tetap
  terpisah dan teruji di invariant test) | jujur > karangan; desain mengizinkan
  reason code ini, dampaknya dihitung terpisah di funnel.
- 2026-09-08 | `spread` historis per-bar tidak ada di dataset candle bridge →
  cost model memakai fallback konstanta profil dengan label
  `ESTIMATED_COST_MODEL` di seluruh output | desain §4.
- 2026-09-08 | Bila M15 warmup < 50 bar pada awal window evaluasi (sebelum
  07:00 UTC), evaluasi sebelum warmup cukup tetap dijalankan tapi
  `H-Q1.min_bars_m15_warmup` dilaporkan di qualification report | transparan
  tanpa membuang data.
- 2026-09-08 | Schema gate enums diperluas dengan `DISABLED` utk semua gate
  (b4/b5/b6 sudah punya) | desain §1: DATA_INVALID → evaluasi strategi TIDAK
  dijalankan; schema wajib tetap bisa merepresentasikan record Layer B yang
  tidak berjalan tanpa melanggar `required: all_gate_results`.
- 2026-09-08 | SL final = `min_stop` (max dari SL ATR×mult dan floor spread);
  bila min_stop > cap → `FAIL:stop_bounds` (SKIP) | desain §B7 "SKIP, bukan
  clamp diam-diam" — SL tidak pernah dipaksa turun di bawah floor spread.
- 2026-09-08 | **Batasan max_trades_per_day (SCALP 6 / MICRO 20) DIHAPUS**
  dari profil, gate B7 (`FAIL:cap`), execution replay, dan schema —
  keputusan eksplisit owner. Override atas desain §B7 | kontrol risiko tetap
  terjaga via cooldown (30m/5m), stop bounds (SKIP), sizing konstan-dolar,
  dan Layer A. Per Pagar 1, perubahan ini = config_hash BARU = experiment
  identity baru; replay 7 Sep dijalankan ulang dengan identity baru.
