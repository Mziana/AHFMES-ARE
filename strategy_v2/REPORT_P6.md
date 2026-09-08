# REPORT P6 — WFO + Statistik (gerbang GO/NO-GO demo)

Tanggal: 2026-09-08 · Mandat: docs/MANDAT_P3_P6_INTEGRATION.md §P6 · Driver: scripts/p6_wfo_stats.py

> **VERDICT AKHIR MANDAT: GAGAL_STATISTIK (2× iterasi) — budget revisi habis (3/3).**
> Keputusan lanjut **kembali ke owner** (desain §9). Bukti lengkap:
> `data/research/p6/wfo_stats.json` (iter-2, results_hash `9da243ea7d8928cb…`).

## Iterasi 2 — champion revisi H-REGIME-SLOPE-02 (EFEKTIF)

Parameter FROZEN dari P4 iter-3 (`disable_gates=("b1_news","b4_location")`, B3 slope dua-arah) · 6 fold OOS bergulir, embargo ≥ 1 hari · N_TRIALS=3 (artefak iter-3).

| Metrik | Nilai | Ambang | Status |
|---|---|---|---|
| SR pooled | +0.027 | — | — |
| PSR | 0.6251 | > 0.80 | ❌ |
| DSR (V[SR] dari 3 trial) | 0.5435 | > 0 | ✅ |
| CI95 expNet | [−3.56, +4.95] | lower > 0 | ❌ |
| Worst-fold expNet | **−15.39** (fold 5) | ≥ −2×avgCost (−2.68) | ❌ |
| Fold dispersion | std 9.09, range [−15.39, +10.29] | — | — |

Pola fold: profit terkonsentrasi di fold 2–4 (+4.3/+6.8/+10.3 — fase melt-up), **fold 5–6 negatif dalam (−15.4/−2.7)**. Revisi dua-arah justru **menambah sumber kerugian**: sisi SELL di downtrend fold 5–6 kalah biaya (spread round-trip 34 pts vs edge tipis). Robustness revisi **lebih buruk** dari iterasi-1.

## Iterasi 1 — champion lama long-only `no_b3_b4` (SEJARAH)

PSR 0.93 ✅ · DSR 0.52 ✅ · CI95 [−1.03, +7.47] ❌ · worst-fold −9.14 ❌ → pemicu revisi H-REGIME-SLOPE-02.

## Kesimpulan & serah terima owner

1. **Tidak ada arm yang lolos P5+P6 pada konfigurasi biaya broker ini.** Edge kotor per trade (iter-3 champion: +0.69 net di spread 17) tidak cukup tebal terhadap 2×spread = 34 pts/round-trip, dan sensitivitasnya struktural (SL ter-couple ke spread via `min_stop_params.spread_mult: 3` → set trade berubah saat spread naik).
2. **Kelemahan fundamental yang terukur dari data**: (a) profit terkonsentrasi regime (melt-up) — long-only maupun dua-arah sama-sama rapuh di fase berlawanan; (b) edge per trade terlalu tipis untuk biaya pasar XAUUSD demo ini; (c) delay 1 bar mematikan strategi (fill next-bar-open wajib persis — beban tinggi untuk Fase I).
3. **Jalur yang tersisa untuk keputusan owner** (mandat habis, bukan keputusan engineer):
   - **Revisi biaya** (hipotesis baru terdaftar → ulang P4): TP lebih lebar, frekuensi lebih rendah, atau SL tidak ter-couple ke spread (pisahkan `spread_mult` dari stop sizing).
   - **Faktor eksternal**: negosiasi/penurunan spread akun, atau instrumen lain dengan spread rendah relatif volatilitas.
   - **Hentikan jalur V2 live** dan pertahankan sebagai riset.
4. Status integration layer (Fase I): **tidak boleh dimulai** — prasyarat "P4 lulus + P5 LULUS + P6 GO" tidak terpenuhi (prinsip mandat: urutan tidak boleh dilompati).

## Status roadmap mandat (akhir sesi)

| Tahap | Status | Kunci lulus |
|---|---|---|
| T0 Identitas bersih | ✅ `e27f73f` | suite hijau + commit + push |
| P3 Qualification | ✅ `0e21741` — LAYAK, hash terkunci `86014edf…` | fail-closed 0, gap 0, 28.8 hari |
| P4 Baseline+ablation | ✅ `5034c19`+`2fb0653`+`f4be56f` — 3 iterasi, criteria ≥30 trade & net>0 terpenuhi tiap iterasi | funnel 100% ✅ |
| P5 Cost stress | ❌ iter-2 GAGAL (garis wajib −0.684) | edge tidak bertahan ×1.5+slip2 |
| P6 WFO+statistik | ❌ GAGAL_STATISTIK 2× | PSR/CI95/worst-fold gagal |
| Fase I Integration | ⛔ diblokir mandat | prasyarat tak terpenuhi |
| Fase D Demo | ⛔ diblokir mandat | — |
