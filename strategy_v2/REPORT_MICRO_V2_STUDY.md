# REPORT — STUDI OFFLINE MICRO v2 "SCALP-M1" (+ Kontrol SCALP M5)

Tanggal: 2026-09-11 · Status: **SELESAI — VERDICT KILL_ALL (tidak ada varian lolos)**
Skrip: `scripts/micro_v2_study.py` (studi), `scripts/micro_v2_control.py` (kontrol)
Artfakta: `data/research/micro_v2/study_results.json`, `data/research/micro_v2/control_scalp_m5.json`

## 1. Desain yang diuji (owner-locked 2026-09-11)

Replika persis mesin SCALP turun satu timeframe: eksekusi **M1 close**, bias momentum
**M5** (EMA9/21 + RSI 45/55), RSI guard M5+M1, skor candle SCALP (threshold 7) di M1,
SL/TP mult × **ATR M5**, cooldown 5 menit, satu posisi per arm, wajib close bar.

Grid (8 varian): volume wajib {1.0×, 1.2×} × RSI guard {65/35, 70/30} × SL/TP
{1.1/1.7 (usulan owner), 1.25/2.0 (parity)} — semua × ATR M5. Bonus +1 volume
di-decouple: hanya bar ≥1.2× avg5 yang dapat poin bonus, di semua varian.

## 2. Data & metodologi

| | |
|---|---|
| Sumber | bridge MT5 `/candles` (read-only), XAUUSD |
| Jendela | **41.2 hari** (2026-07-31 → 2026-09-10), 39.999 bar M1 + 7.999 bar M5 |
| Bar evaluasi | 39.599 close-bar M1 (setelah warmup 400 bar) |
| Jendela indikator | M1=400, M5=400 bar — **persis driver live** |
| Exit | first-touch SL/TP dari bar M1 berikutnya, SL-priority saat ambigu; 21 trade menyeberang gap weekend (ditandai, tidak dibuang) |
| Sel biaya | base **17 poin**; must **27.5 poin** (×1.5 + slip2) — kontrak R1 Stage 1 |
| Kriteria lolos | `expNet_must > 0` ∧ `n ≥ 30` (tanpa negosiasi) |
| Akuntansi funnel | Σ blok + entri = 39.599 bar **eksak** (tidak ada bar hilang) |

## 3. Hasil — 8/8 varian KILL

| Varian | n | W/L | WR% | expBase | expMust | $/tr@0.02 | n/hari | Verdict |
|---|---|---|---|---|---|---|---|---|
| v1.2\|70_30\|M1.1_T1.7 | 655 | 268/387 | 40.9 | −16.81 | **−27.31** | −0.55 | 15.9 | KILL |
| v1.2\|65_35\|M1.1_T1.7 | 568 | 232/336 | 40.8 | −16.82 | **−27.32** | −0.55 | 13.8 | KILL |
| v1.2\|65_35\|PAR125_T200 | 493 | 194/299 | 39.4 | −16.82 | **−27.32** | −0.55 | 12.0 | KILL |
| v1.0\|65_35\|PAR125_T200 | 658 | 260/398 | 39.5 | −16.85 | **−27.35** | −0.55 | 16.0 | KILL |
| v1.0\|70_30\|M1.1_T1.7 | 874 | 352/522 | 40.3 | −16.87 | **−27.37** | −0.55 | 21.2 | KILL |
| v1.2\|70_30\|PAR125_T200 | 562 | 220/342 | 39.1 | −16.88 | **−27.38** | −0.55 | 13.6 | KILL |
| **v1.0\|65_35\|M1.1_T1.7 (utama)** | 789 | 315/474 | 39.9 | −16.95 | **−27.45** | −0.55 | 19.1 | KILL |
| v1.0\|70_30\|PAR125_T200 | 711 | 275/436 | 38.7 | −16.96 | **−27.46** | −0.55 | 17.3 | KILL |

Per bulan (varian utama): Jul n=4 gross −4; **Aug n=562 gross +132** (expMust −27.3);
**Sep n=223 gross −93** (expMust −27.9). Bulan terbaik pun jauh dari lolos.

## 4. Kontrol — SCALP M5 asli di jendela yang sama

`decide()` produksi dijalankan di 41 hari yang sama (exit grid M5, parity eksekusi replay R1):

| n | W/L | WR% | avgGross | expBase | expMust | $/tr@0.02 |
|---|---|---|---|---|---|---|
| 267 | 108/159 | 40.4 | +13.2 pts | −3.78 | **−14.28** | −0.29 |

### Interpretasi (penting)

1. **Seluruh pipeline pola-candle ini gross-breakeven di window 41 hari** — bukan hanya
   turunan M1. SCALP M5 asli (yang live 4W/1L, +39.90$) juga KILL di replay panjang
   (WR 40.4%, expMust −14.28). WR live 80% dari 5 trade adalah sampel terlalu kecil:
   4W/1L sangat mungkin dari proses 40% WR.
2. Turun ke M1 **tidak menambah edge** (konsisten temuan Arm B R1 Stage 1: M1
   +0.35 vs M5 +0.69). Guard 65/35 vs 70/30 dan volume 1.0 vs 1.2 hampir tak
   mengubah hasil — seleksi bukan masalahnya, **gross edge ≈ nol** itulah masalahnya
   (avg gross varian utama ≈ **+0.05 poin/trade**).
3. **Insight "receh"**: SL/TP 1.1/1.7 × ATR M5 **tidak menghasilkan poin kecil** —
   ATR M5 tinggi membuat rata-rata TP varian utama **811 poin** (SL 525). Target
   "receh" via multiplier ATR M5 tidak bisa mencapai TP 100–300 poin; kalau
   dipaksa poin tetap kecil, biaya 17–27.5 poin jadi 10–25% dari TP — jebakan
   MICRO v1 persis. Dilema ini struktural di akun demo Finex (spread ~20 poin).
4. Breakeven-gross WR di struktur rata-rata ini ≈ 39.3%; semua varian berada di
   38.7–40.9%. Untuk lolos must dibutuhkan gross ≥ 27.5 poin/trade — misalnya WR
   ~41.4%+ pada rasio yang sama, atau seleksi yang melipatgandakan gross per trade.

## 5. Verdict & rekomendasi

**KILL_ALL untuk swap MICRO v2** — mengikuti kontrak (satu perubahan = satu hipotesis
terdaftar; gagal = KILL tanpa tweak). Konsekuensi:

- **Arm MICRO tetap NONAKTIF** (toggle owner) — ini keadaan yang benar, bukan sementara.
- **SCALP M5 tetap jalan** seperti sekarang (tidak disentuh studi ini), dengan catatan
  jujur: replay 41 hari menunjukkan arm ini pun gross-breakeven — 4W/1L live belum
  jadi bukti edge. Kill switch 3L/30m + toggle adalah rem yang tepat; review ulang
  setelah n live ≥ 20.
- Jurnal direkonsiliasi penuh (backfill rev5): 23 open / 23 close / 0 null.
  **GLOBAL +0.10$** = MICRO −39.80 (5W/13L, 28%) + SCALP +39.90 (4W/1L, 80%).

## 6. Arah riset berikutnya (bukan tweak varian ini)

1. **Dekomposisi sumber gross**: bucket sesi/jam × arah × pola pada 789 trade varian
   utama — cari sub-sel dengan gross/trade ≥ 27.5 poin (analog "zona emas" Arm A R1:
   0-0.25 ATR = +2.17). Kalau ada, itu hipotesis terdaftar berikutnya.
2. **Biaya real per eksekusi**: sel must mengasumsikan worst-case; ukur spread aktual
   deal history per jam (menang di jam spread sempit = edge biaya, bukan edge sinyal).
3. Terima temuan struktural: dengan biaya ~17–27 poin dan edge pola gross ~0,
   strategi pola-candle frekuensi tinggi di XAUUSD demo ini **tidak viable** —
   geser riset ke frekuensi lebih rendah (TP lebih besar dari noise) atau sumber
   sinyal lain (order flow / level likuiditas).

---
*Studi read-only; tidak ada perubahan driver/live path. Semua angka reproducible
dari skrip + JSON artefak.*
