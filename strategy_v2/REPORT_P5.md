# REPORT P5 — Cost Stress (arm juara P4, parameter FROZEN)

Tanggal: 2026-09-08 · Mandat: docs/MANDAT_P3_P6_INTEGRATION.md §P5 · Driver: scripts/p5_cost_stress.py

> ⚠️ **ITERASI 2 (champion revisi slope) — VERDICT: GAGAL.** Laporan ini memuat
> kedua iterasi; angka iterasi-1 dipertahankan sebagai sejarah, verdict efektif
> adalah iterasi-2. Artefak kanonik: `data/research/p5/cost_stress.json`
> (results_hash iter-2 `d0ef7376cc224afa…`, 199 sinyal, 18 sel).

## Iterasi 2 — champion revisi H-REGIME-SLOPE-02 (EFEKTIF)

Arm: MICRO_V2 `disable_gates=("b1_news","b4_location")` (B3 slope dua-arah) · Parity P4 iter-3 ✅ (199 sinyal identik) · Base spread 17 pts.

| spread | slip | delay | trades | net | expNet |
|---|---|---|---|---|---|
| ×1.25 | 0 | 0 | 136 | −0.41 | **−0.003** (edge kotor habis di kenaikan pertama) |
| ×1.5 | 0 | 0 | 138 | −94.28 | −0.68 |
| **×1.5** | **2** | **0** | **138** | **−94.44** | **−0.684 ← GARIS WAJIB: GAGAL** |
| ×2.0 | 0 | 0 | 137 | −206.75 | −1.51 |
| ×* | * | 1 | 128–129 | semua ≤ −369 | −2.89 … −5.56 (delay mematikan total) |

**Diagnosis:** sensitivitas struktural, bukan linear saja — SL ter-couple ke spread
(`min_stop_params.spread_mult: 3` → SL melebar saat spread naik), sehingga set
trade berubah (136→138 trades) dan biaya entry+exit (2× spread ≈ 43–51 pts/round-trip)
melampaui edge kotor per trade. **H-SPREADCAP-03 (cap 34 pts = 2×) tidak
mencukupi**: edge sudah negatif jauh sebelum cap tersentuh.

## Iterasi 1 — champion lama long-only `no_b3_b4` (SEJARAH — tidak efektif)

Arm: `disable_gates=("b1_news","b3_regime","b4_location")` · Parity ✅ (220 sinyal) · results_hash `762fd27d…`

Garis wajib ×1.5+slip2+delay0 → expNet **+0.66 = LULUS**; edge mati di ×2.0; delay 1 bar mematikan semua sel. (Tetap tercatat: arm ini long-only paksa yang menunggangi melt-up gold — P6 iter-1 membuktikan rapuh OOS: worst-fold −9.14.)

## Implikasi & status mandat

- **Tidak ada arm yang lolos P5 iterasi 2** → strategi **tidak layak live** pada biaya broker ini (spread efektif 2×17 = 34 pts/round-trip vs edge kotor ~5.5 pts/trade setelah revisi).
- Budget revisi mandat habis (3/3 iterasi P4). Sesuai mandat: **kembali ke owner** dengan dua jalur yang tersisa: (a) revisi hipotesis biaya — TP lebih lebar / frekuensi lebih rendah / arm berbiaya rendah; (b) prioritas ke farktor eksternal: negosiasi spread/akun, atau pindah instrumen ber-spread lebih rendah relatif terhadap volatilitas.
- P6 iterasi 2 tetap dijalankan untuk kelengkapan bukti atas champion revisi (lihat REPORT_P6.md).
