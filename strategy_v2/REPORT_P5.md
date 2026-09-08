# REPORT P5 — Cost Stress (arm juara P4, parameter FROZEN)

Tanggal: 2026-09-08 · Mandat: docs/MANDAT_P3_P6_INTEGRATION.md §P5 · Driver: scripts/p5_cost_stress.py
Arm: MICRO_V2 `disable_gates=("b1_news","b3_regime","b4_location")` · Parity P4 ✅ (220 sinyal identik)
Grid: spread {×1.25, ×1.5, ×2.0} × slippage {0,2,5} poin × delay {0,1} bar = 18 sel · results_hash `762fd27d…`

## Hasil (expNet USD/trade)

| spread | slip | delay | trades | net | expNet |
|---|---|---|---|---|---|
| ×1.25 | 0 | 0 | 138 | +239,83 | **+1,74** |
| ×1.25 | 2 | 0 | 140 | +189,94 | +1,36 |
| ×1.25 | 5 | 0 | 141 | +163,56 | +1,16 |
| ×1.5 | 0 | 0 | 141 | +119,60 | +0,85 |
| **×1.5** | **2** | **0** | **140** | **+92,35** | **+0,66 ← GARIS WAJIB: LULUS** |
| ×1.5 | 5 | 0 | 140 | +92,35 | +0,66 |
| ×2.0 | 0–5 | 0 | 139 | −22 … −77 | −0,16 … −0,55 (mati) |
| ×1.25–2.0 | * | **1** | 127–129 | semua negatif | −0,68 … −2,63 |

## Verdict

**LULUS** — edge bertahan `expNet > 0` pada garis wajib desain (×1.5 + slip2 + delay0), bahkan hingga slip 5 poin.

## Temuan material (untuk Fase I & P6)

1. **Delay 1 bar = fatal**: SEMUA sel delay=1 negatif. Edge hidup dari fill next-bar-open segera. Konsekuensi: adapter live HARUS fill pada open bar berikut (parity kontrak replay), dan slippage eksekusi nyata dipantau ketat.
2. **Batas spread ×2.0 (34 poin)**: edge mati. Spread live harus dipantau; di atas ~25 poin (×1.5) sistem masuk zona degradasi.
3. Degradasi halus dan monoton — tidak ada cliff aneh selain delay.

## Kriteria mandat §P5

| Kriteria | Status |
|---|---|
| expNet > 0 pada ×1.5 + slip2 + delay0 | ✅ +0,66 |
| ≥ 9 kombinasi | ✅ 18 sel |
| Kurva degradasi dilaporkan | ✅ (tabel + temuan delay/spread cap) |
