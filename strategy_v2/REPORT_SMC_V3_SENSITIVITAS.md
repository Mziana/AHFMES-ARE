# REPORT — SMC v3 Sensitivity & Multi-Regime (prio 7, 8, 4 review)

> **STATUS: BUKTI UNTUK OWNER — TIDAK ADA KEPUTUSAN KILL/KEEP.**
> Semua angka = replay offline; biaya pakai sel R1 (base 17 / must 27.5 pts,
> `ESTIMATED_COST_MODEL`). Sim **sistematis meremehkan biaya live** (sim A
> −12.34$ vs live −28.32$) — yang dipakai sebagai bukti adalah **arah
> perbandingan antar-varian**, bukan dollar persisnya.

---

## 0. Ringkasan eksekutif

| # | Temuan | Bukti |
|---|--------|-------|
| 1 | **POI lebih ketat = konsisten lebih baik di KEDUA window** — arah yang sama di trending & sideways. `strict` (desain §3.1 literal) adalah yang terbaik | Tabel 1.1 & 1.2 |
| 2 | **Di window sideways, strict satu-satunya sel bersih**: +111.3 net-must/trade (legacy) / +2.5 (G2), WR 43.8% — sementara default 1.5×ATR −204.1 / −274.1, WR 33.3% | Tabel 1.2 |
| 3 | **G2 exit §4 konsisten MENGURAGI hasil vs first-touch** di kedua window (kecuali strict/side yang tetap positif) — netral-ke-negatif sebagai manajemen exit di engine ini | Tabel 1.1/1.2 baris g2 |
| 4 | **Kurva threshold TERBALIK**: WR & gross M MONOTON TURUN seiring skor naik (6→11). Skor ≥10 = terburuk (WR 17.9–24%, gross −219 s/d −349/trade). Tambahan skor TIDAK menambah kualitas — konsisten dengan redundansi Bias↔BOS yang terukur 100% | Tabel 2.1 |
| 5 | **Skor BUKAN fitur seleksi yang sehat** di bentuk sekarang; kalibrasi threshold dari data ini dilarang sebelum redundansi beres (prio 4 tetap tertahan) | Tabel 2.1 |
| 6 | Validasi harness: `poi_d150/legacy` mereproduksi parity persis (n 139, gross −16.99) — semua sel lain berdiri di fondasi yang sama | §3 |

---

## 1. Sensitivity POI (prio 7) — 4 konfigurasi × 2 window × 2 exit

Konfigurasi: `poi_d150` = default 1.5×ATR (legacy) · `poi_d075` = 0.75×ATR ·
`poi_d050` = 0.5×ATR · `poi_strict` = harga WAJIB di dalam zona (desain
§3.1 literal). Angka = lapis **trades** (gating posisi parity, skor ≥ 8).

### 1.1 Window TRENDING (39.23 hari terpin, 39.598 bar evaluasi)

| Konfig | Exit | n | WR % | Gross/tr | Net-must/tr |
|---|---|---|---|---|---|
| poi_d150 | legacy | 139 | 32.4 | −16.99 | −44.49 |
| poi_d150 | g2 | 139 | 32.4 | −17.08 | −44.58 |
| poi_d075 | legacy | 141 | 32.6 | −12.70 | −40.20 |
| poi_d075 | g2 | 141 | 32.6 | −12.92 | −40.42 |
| poi_d050 | legacy | 150 | 33.3 | −10.64 | −38.14 |
| poi_d050 | g2 | 150 | 33.3 | −10.93 | −38.43 |
| **poi_strict** | legacy | 133 | 33.8 | **−1.36** | **−28.86** |
| **poi_strict** | g2 | 133 | 33.8 | **−1.03** | **−28.53** |

> Monoton: makin ketat jangkauan POI, makin baik gross (−16.99 → −1.36).
> Strict memotong sinyal (1066→775, −27%) dan menyisakan yang paling dekat
> zona — premis "reaksi presisi di zona institusional" (§3.1) terkonfirmasi
> arah. Tetap negatif di window ini — perbaikan arah, bukan keajaiban.

### 1.2 Window SIDEWAYS (7.95 hari dari cache, ER 0.0044, trend None)

| Konfig | Exit | n | WR % | Gross/tr | Net-must/tr |
|---|---|---|---|---|---|
| poi_d150 | legacy | 21 | 33.3 | −176.62 | −204.12 |
| poi_d150 | g2 | 21 | 33.3 | −246.62 | −274.12 |
| poi_d075 | legacy | 22 | 36.4 | −88.36 | −115.86 |
| poi_d075 | g2 | 22 | 36.4 | −186.10 | −213.60 |
| poi_d050 | legacy | 21 | 38.1 | −43.24 | −70.74 |
| poi_d050 | g2 | 21 | 38.1 | −145.62 | −173.12 |
| **poi_strict** | legacy | 16 | 43.8 | **+138.81** | **+111.31** |
| **poi_strict** | g2 | 16 | 43.8 | **+29.99** | **+2.49** |

> Di sideways, kontras antar-konfig JAUH lebih tajam: default 1.5×ATR
> hancur (−204), strict satu-satunya positif (+111 legacy / +2.5 g2 — g2
> memangkas 78% dari keunggulan legacy; lihat temuan 3).

### 1.3 Jarak POI saat entry (diagnostik premis)

Sinyal lapis (tanpa gating), rerata jarak harga→POI dalam ×ATR saat take:
konfig ketat menurunkan rerata jarak entry dan menaikkan WR pada bucket
jarak kecil — detail per-bucket [n, wr, gross] ada di artefak
(`smc_v3_sensitivity_replay.json`, field `poi_dist_atr` per sinyal).

---

## 2. Kurva threshold (prio 4) — sinyal bebas seleksi (skor ≥ 6)

> Metodologi: semua sinyal dengan skor ≥ 6 & jalur skor penuh (RR/SL lolos)
> dicatat **tanpa** gating posisi — kurva bebas bias seleksi. Net-must pakai
> biaya must 27.5.

### 2.1 TRENDING (sinyal poi_d150 / g2: 1.066 sinyal)

| Threshold | n | WR % | Gross/sinyal | Net-must/sinyal |
|---|---|---|---|---|
| ≥6 | 1.066 | 33.4 | +48.28 | +20.78 |
| ≥7 | 1.060 | 33.2 | +46.02 | +18.52 |
| ≥8 (engine) | 445 | 29.9 | +5.45 | −22.05 |
| ≥9 | 421 | 27.6 | −28.47 | −55.97 |
| ≥10 | 50 | 24.0 | −203.06 | −230.56 |
| ≥11 | 39 | 17.9 | −327.22 | −354.72 |

> **M monoton turun.** Lonjakan antara ≥7 (1.060) dan ≥8 (445): mayoritas
> sinyal skor 7 (615 unit) punya gross AGREGAT positif besar (+46.352 pts,
> WR 35.6%), sementara skor 9 (371 unit, WR 28.0%) dan 11 (39 unit, WR
> 17.9%) agregat negatif. Skor tinggi ≠ kualitas tinggi — saling mengunci
> dengan temuan redundansi (BOS 100% mengikuti bias; item bobot-tinggi
> saling menumpuk, bukan independen).
>
> Peringatan: bucket skor 6 (n=6, +2.695) dan skor 8 (n=24, +14.408) kecil —
> lead, bukan konfirmasi. Yang solid: **monotonisitas menurun dari ≥6→≥11**.

### 2.2 SIDEWAYS (sinyal poi_d150 / g2: 291 sinyal)

| Threshold | n | WR % | Gross/sinyal | Net-must/sinyal |
|---|---|---|---|---|
| ≥6 / ≥7 | 291 | 43.0 | +36.86 | +9.36 |
| ≥8 / ≥9 | 92 | 38.0 | −66.10 | −93.60 |
| ≥10 / ≥11 | 2 | 0.0 | −513.00 | −540.50 |

> Pola yang sama (skor naik → hasil turun), meski n jauh lebih kecil.
> Strict/side: ≥8 = WR 45.3%, +98.85 gross — kontras regime x POI ketat
> (lihat 1.2).

---

## 3. Catatan jujur & batasan

1. **G2 exit §4 di sini KONSISTEN MENGURAGI vs first-touch** (trend: −44.49→
   −44.58; side default: −204→−274; hanya strict/side yang tetap positif
   tapi terpangkas +111→+2.5). Ini BERBEDA arah dari varian parity (g2 ≈
   netral, −45.71). Perbedaan konteks: di sini TP1 = target likuiditas
   terdekat yang SAMA dengan exit first-touch, dan trailing structure/ATR
   memberi balik sebelum TP penuh pada gerakan satu-leg. Interpretasi:
   manajemen §4 butuh TP2/likuiditas lebih jauh untuk menangkap leg — bukan
   bukti menolak §4, tapi BUKTI bahwa §4-versi-engine-saat-ini bukan
   penambah PnL di kedua window. Keputusan geometri tetap MILIK OWNER.
2. **Window sideways bukan independen penuh** dari window trending: cache
   M1/M5/M15 menutup 8 Apr–12 Jun hanya menutup sebagian — window terpilih
   (4–12 Jun) BERADA di era berbeda dari 3 Agu–11 Sep, tapi tetap satu
   dataset sim. Arah kontras regime valid; magnitudo tidak digeneralisasi.
   Juga n kecil (16–22 trade per konfig) — semua [n] ditampilkan eksplisit.
3. **Kurva threshold TIDAK boleh dipakai mengkalibrasi** (mis. "turunkan ke
   7"): redundansi Bias↔BOS belum diresolusi (P=100%, umur median 129 bar
   M5) — skor yang dikalibrasi masih skor yang salah. Prio 4 tetap status
   DITAHAN sesuai keputusan sebelumnya; tabel ini = peta masalah, bukan
   resep angka.
4. News gate OFF (keputusan owner); spread snapshot konstan 17 pts; M1
   sintetis 5-bar/M5 dipakai HANYA di pass sideways untuk exit-sim
   (struktur sinyal dari M5/M15 asli; pola M1 = pola M5 — labeled
   eksplisit).
5. Biaya = `ESTIMATED_COST_MODEL` sel R1; arah perbandingan antar-varian
   yang jadi bukti, bukan dolar.

---

## 4. Provenance & repro

| Item | Nilai |
|---|---|
| Artefak | `data/research/smc_v3/smc_v3_sensitivity_replay.json` (63.7 KB) |
| Regime scan (buta PnL) | `scripts/smc_v3_regime_scan.py` → `smc_v3_regime_scan.json`; kriteria ER-Kaufman H4 250-bar, range/ATR-H4, `structure_trend`, ATR5-mean ≥ 150p; dipilih 2026-06-04T21:52+10d (ER 0.0044, rng 16.0×ATR, trend None) |
| Replay | `scripts/smc_v3_sensitivity_replay.py` — 4 konfig POI dievaluasi terpisah di engine; 2 lapis hasil (signals/trades); exit via `smc_exits.simulate` (unit-tested) |
| Window trending | terpin ke studi lama: 03 Agu 11:39 → 11 Sep 17:08 UTC (39.23 hari, 39.598 bar) |
| Window sideways | 04 Jun 22:00 → 12 Jun 20:54 UTC dari cache R1 (7.95 hari efektif — cache M5 berakhir ~12 Jun) |
| Regresi silang | poi_d150/legacy = n 139, gross −16.99, net-must −44.49 == parity baseline (identik) |
| Engine | `strategy_v2/smc.py` + `poi_mode`/`poi_reach`/`min_score` (default = perilaku lama persis; test `test_smc_sensitivity_params.py`) |
| Test | suite strategy_v2 hijau penuh (lihat DECISIONS) |

## 5. Yang terbuka untuk owner (tanpa dijawab di sini)

1. Apakah arah "POI lebih ketat" cukup bukti untuk mengganti default
   POI_REACH 1.5×ATR → strict/0.5×ATR di konfigurasi kandidat berikutnya?
2. Geometri exit: pertahankan §4 versi engine saat ini, atau evaluasi TP2/
   trailing yang menangkap leg penuh (temuan 3.1)?
3. Kalibrasi threshold tetap ditahan sampai redundansi Bias↔BOS beres —
   apakah mau lanjut ke resolusi redundansi sekarang?
