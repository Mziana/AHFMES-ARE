# REPORT C0–C4 — COGNITIVE LAYER v2.1 (implementasi + pengujian penuh)

Tanggal: 2026-09-09 · Dataset terkunci: P3 `86014edf…` (8.300 bar M5, 28,8 hari) ·
Versi strategi: `strategy_v2/0.4.1-c1` · Arm: MICRO, `disable_gates=(b1_news, b4_location)`, B3 slope (H-REGIME-SLOPE-02)

## Ringkasan eksekutif

Cognitive Layer **diimplementasi penuh dan diuji end-to-end** (C0 → C4). Hasilnya
jujur dan dua sisi:

1. **Sebagai SELEKTOR, scorer terbukti bekerja** — mengungguli champion binary
   di kedua kriteria (C2), dan untuk pertama kalinya sepanjang riset membuat
   **garis wajib desain ×1.5+slip2 menjadi POSITIF** (+0.2023 vs binary −0.684) (C3).
2. **Sebagai BUKTI EDGE untuk GO demo, statistik masih GAGAL** (C4):
   PSR 0.747 < 0.80, CI95 expNet [−4.98, +10.25] menyentuh nol, worst-fold −25.39.
   Konsentrasi rezim (fold 4–5 rugi dua arah) **belum teratasi** oleh scorer.

Kontrak tetap `scoring.mode="off"` — tidak ada perilaku live yang berubah tanpa
kelulusan statistik.

## Per tahap

| Tahap | Isi | Hasil | Commit |
|---|---|---|---|
| **C0** | Scorer 8 komponen deterministik + gate BQ + schema + profil + 112 test hijau; parity mode-off == score-on(thr=null) | ✅ | `a15a264` |
| **C1** | Kalibrasi threshold DARI DATA: sweep 12 ambang (blank→WAIT), dua sel biaya; rule = ambang TERENDAH dengan base>0 AND must>0 AND ≥30 trade | ✅ **T\* = 60.1** (base +2.64 n=43; must +0.20 n=44) | `44b6262` |
| **C2** | Head-to-head scorer vs binary, identitas eksperimen identik | ✅ **SCORER_MENANG**: base +2.6354 (n=43, WR .535) vs +0.694 (n=136); must +0.2023 vs −0.6844; parity binary persis P4/P5 | `bf9f044` |
| **C3** | Grid biaya 18 sel (T\* frozen) | ✅ **LULUS** garis wajib +0.2023; 6/18 sel positif (semua delay=0 kecuali ×2.0); delay=1 membunuh semua sel (−3.78 s/d −5.24) — konsisten P5 | `db2f621` |
| **C4** | WFO 6 fold + embargo 1 hari + purge; PSR/DSR (N-trials=15: 3 arm P4 + 12 sweep C1, V[SR]=0.003215); CI95; fold per arah | ❌ **GAGAL_STATISTIK** (3/5 kriteria gagal) | artefak `2ecefc60…` |

## Detail C4 (base = biaya 17/slip0; must = ×1.5+slip2)

| Metrik | Base | Must |
|---|---|---|
| n trade | 43 | 44 |
| expNet | **+2.6354** | +0.2023 |
| SR / PSR / DSR | +0.1034 / 0.7472 / 0.4838 ✅ | +0.0079 / 0.5207 / 0.2521 |
| CI95 expNet | **[−4.98, +10.25] ❌** | [−7.35, +7.76] |

| Fold | Window (UTC) | n | expNet | BUY / SELL |
|---|---|---|---|---|
| 1 | 07-29 → 08-04 | 10 | **+15.80** | +79.9 (7) / +78.1 (3) |
| 2 | 08-04 → 08-11 | 6 | +9.75 | +5.0 (2) / +53.5 (4) |
| 3 | 08-11 → 08-18 | 8 | +7.19 | +54.7 (4) / +2.8 (4) |
| 4 | 08-18 → 08-25 | 2 | **−25.39** | −50.8 (2) / — |
| 5 | 08-25 → 09-01 | 7 | **−17.26** | −70.9 (5) / −49.9 (2) |
| 6 | 09-01 → 09-07 | 10 | +1.10 | +5.8 (8) / +5.2 (2) |

## Interpretasi jujur (bukan yesman)

- **Scorer menyelesaikan masalah yang bisa diselesaikannya**: seleksi trade.
  Efisiensi 3.8×, WR naik 49.3%→53.5%, garis wajib positif pertama kalinya.
- **Scorer TIDAK menyelesaikan masalah rezim**: fold 4–5 rugi di KEDUA arah
  (bukan lagi ketimpangan SELL seperti iterasi-2) — periode 18 Agu–1 Sep rugi
  regardless arah. Edge tetap terkonsentrasi rezim tren/forward yang sehat.
- **n=43 terlalu kecil** untuk PSR>0.80 dan CI95>0 pada std ~$25/trade — ini
  keterbatasan data, bukan (hanya) keterbatasan strategi.
- DSR positif setelah deflasi 15 trial — sesuatu, tapi bukan gerbang GO.

## Opsi untuk owner (urutan rekomendasi saya)

1. **Backward OOS + forward treadmill** (rekomendasi kuat): tarik history lebih
   lama via bridge, jalankan champion C3 ini FROZEN di periode yang belum pernah
   dilihat — satu-satunya cara menaikkan n dan menguji stabilitas rezim tanpa
   fitting. Infrastruktur C0–C4 bisa dipakai ulang apa adanya.
2. **Revisi hipotesis terdaftar baru** menargetkan rezim rugi fold 4–5
   (filter rezim M15 lebih ketat / sit-out volatilitas tinggi-tanpa-arah) →
   siklus C baru (budget disiplin: maks 3 iterasi).
3. **Terima NO-GO untuk demo** dan pertahankan V2 sebagai riset.

## Catatan disiplin

- T\* 60.1 berasal dari data (C1), provenance + n_trials=12 tercatat di H-SCORE-01.
- Deflasi DSR C4 memakai 15 trial (komposisi terdokumentasi di artefak).
- Preflight Certificate (`run_full_preflight_battery()`) tetap item terbuka
  tercatat-jujur (milik engine lama, Domain B).
- Artefak ber-hash: `data/research/c1…c4/*.json` (gitignored, konvensi repo);
  semua driver di `scripts/` deterministik dan bisa direproduksi.
- **Fase I (integration) tetap TIDAK dimulai** — prasyarat P6-setara lulus tidak terpenuhi.
