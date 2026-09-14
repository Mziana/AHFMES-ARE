# Respon Tim Implementasi — atas REVIEW_TANGGAPAN_SMC_V3.md

> Status: jawaban teknis + hasil verifikasi dari data. **Tetap tidak ada keputusan kill/keep** — sesuai kesepakatan, keputusan menunggu G2 selesai. Prioritas kerja kami mengikuti urutan bab 6 review.

Tanggal: 2026-09-12 · Artefak baru: `data/research/smc_v3/smc_v3_redundancy.json`, `data/research/smc_v3/smc_v3_segmentation.json`, skrip `scripts/smc_v3_redundancy.py`

---

## 1. Ringkasan Jawaban

| Temuan review | Status verifikasi kami | Hasil |
|-|-|-|
| 3.2 Redundansi Bias↔BOS (67,3% = 67,3%) layak dicurigai | **Diuji pada data 5 bulan (11.235 sampel)** — bukan 39 hari | **Terkonfirmasi: P(BOS searah \| bias non-netral) = 100,0%** — item BOS sepenuhnya redundan terhadap bias |
| 3.2 G3 dinaikkan prioritas (freshness BOS) | Diukur distribusi umur BOS | Median umur BOS saat item OK = **129 bar M5** (p75 = 275, maks 399) — item #4 memang tidak mengukur "friskness" apa pun |
| 4.1 n=139 belum signifikan | Dihitung ulang CI95 | **Terkonfirmasi: CI95 WR = [24,6%, 40,2%], breakeven 34,2% di dalam CI** — reframing "belum cukup bukti" kami terima |
| 3 (poin 3) Segmentasi WR per skor | Dihitung dari 139 trade | **Tidak konklusif** — n per bucket skor terlalu kecil (lihat 2.2) |
| 4.6 n per bucket sesi/arah | Ditampilkan eksplisit | Semua n ditampilkan (lihat 2.3) — kesimpulan "hindari overlap" kami **tarik** sebagai lead-only |
| 4.5 Sensitivity `nearest_liquidity_target` | Dicatat sebagai item prioritas | Ditambahkan ke daftar kerja (bab 5) |
| 4.7 Disiplin test diperluas | Diterima | Kontrak test G2/G3 sudah ditulis di bab 4 |

---

## 2. Hasil Verifikasi (data, bukan opini)

### 2.1 Redundansi Bias↔BOS — TERKONFIRMASI 100%

Kami tidak cukup dengan korelasi di window 39 hari (yang bisa kebetulan regime), jadi pengujian diulang di **dataset cache 5 bulan (8 Apr – 9 Sep, 150 ribu bar M1)** — window yang pasti memuat periode non-trending juga. H4 diagregasi dari M15 (16×) dengan label eksplisit di artefak (bridge sedang mati saat analisis; agregasi read-only).

| Metrik | Nilai |
|-|-|
| Sampel (tiap-12 bar M1) | 11.235 |
| Bias H4 non-netral | 8.236 |
| Dari yang non-netral, punya ≥1 BOS searah di window | **8.236 (100,0%)** |
| Umur BOS searah terbaru saat item OK (bar M5) | p25 = 19 · **median = 129** · p75 = 275 · maks = 399 |

**Interpretasi kami — sama dengan review, lebih tegas:**
1. Item #4 (BOS, bobot 1) saat ini **bukan konfirmasi terpisah** — ia deterministik menyertai item #1 (bias, bobot 2). Skor efektifnya 12-1 = 11 poin independen, dan threshold ≥8 efektifnya lebih longgar dari desain.
2. Median umur 129 bar M5 (±11 jam) membuktikan item #4 tidak menangkap makna §7 item 4 ("BOS **sebelum retrace ke POI**" = friskness).
3. **Rencana G3 (konkret)**: BOS hanya dihitung OK bila terjadi dalam **≤ N bar sebelum sinyal** di M5 (kandidat N = 36 bar M5 ≈ 3 jam — p25 distribusi umur 19, jadi N=36 memangkas mayoritas umur panjang tanpa mengubah item menjadi mustahil). Angka final dari replay kalibrasi, bukan dipatok di sini. Efek sampingnya diakui: take-rate akan turun dari 1,12% — itu justru yang ingin diukur (apakah WR bucket yang tersisa naik cukup untuk mengompensasi).

### 2.2 Segmentasi WR per Skor — Data Ada, n Terlalu Kecil

| Skor | n | WR | Gross | /trade | TP/SL |
|-|-|-|-|-|-|
| 8 | 3 | 0,0% | −1065 | −355,0 | 0/3 |
| 9 | 122 | 33,6% | −519 | −4,3 | 40/82 |
| 10 | 2 | 50,0% | +1008 | +504,0 | 1/1 |
| 11–12 | 12 | 25,0% | −1786 | −148,8 | 3/9 |

Jawaban jujur atas poin 3 review: **pertanyaannya tepat, tapi dataset ini tidak bisa menjawabnya.** 88% trade menumpuk di skor 9; bucket 8 dan 10 hanya 3 dan 2 trade. Pola permukaan (skor 11–12 justru terburuk) bertentangan dengan intuisi confluence — dengan n=12 itu kemungkinan besar noise, dan kami menolak menyimpulkan apa pun darinya. Segmentasi ini akan diulang **setelah replay G2** (dan idealnya di window multi-regime) sebelum dipakai mengambil keputusan threshold.

### 2.3 n per Bucket — Ditampilkan Eksplisit (review 4.6 dikabulkan)

| Bucket | n | WR | Gross | /trade |
|-|-|-|-|-|
| Sesi asia | 51 | 31,4% | −1982 | −38,9 |
| Sesi ny_late | 34 | 29,4% | +2012 | +59,2 |
| Sesi overlap | 32 | 28,1% | −4149 | −129,7 |
| Sesi london | 22 | 45,5% | +1757 | +79,9 |
| Arah BUY | 69 | 30,4% | −3169 | −45,9 |
| Arah SELL | 70 | 34,3% | +807 | +11,5 |

Dengan sebaran seperti ini, semua klaim granular per bucket **turun gradasi menjadi "lead"**: hanya london vs overlap yang selisihnya cukup besar untuk layak dicermati, dan itupun n=22 vs 32 — di bawah ambang yang kami anggap layak-simpul (n≥30 per bucket). "Hindari sesi overlap" **bukan** rekomendasi dari data ini.

### 2.4 Signifikansi Statistik — Reframing Diterima

WR 32,4% (n=139) → SE = 3,97pp → **CI95 = [24,6%, 40,2%]**. Breakeven-gross 34,2% berada di dalam CI. Klaim yang benar adalah versi review: *"belum cukup bukti untuk menyimpulkan ada/tidaknya edge di level gross"* — bukan "terbukti tidak ada edge". Laporan replay akan direvisi dengan bahasa ini saat G2 selesai (satu putaran revisi, bukan menulis dua kali).

---

## 3. Yang Kami Terima, Yang Kami Klarifikasi

**Diterima tanpa reserve:**
- G2 = prasyarat keputusan (review 3.1) — sudah menjadi prioritas 1 kami.
- Reframing statistik (4.1) — masuk ke laporan.
- n per bucket wajib eksplisit (4.6) — masuk ke laporan.
- Kontrak test untuk G2/G3 (4.7) — ditulis di bab 4 di bawah.
- Mitigasi basis CLOSE dipertahankan (3.5) — konfirmasi owner tercatat.
- Sensitivity `nearest_liquidity_target` ditambahkan (4.5) — benar, RR-gate adalah filter dominan (60% evaluasi) dan RR-nya ditentukan oleh pemilihan TP1.

**Klarifikasi kecil:**
- Review 4.2 ("−44,49 separuh berasal dari biaya"): benar, dan kami menambahkan bahwa pemisahan signal-edge vs cost-model memang sudah ada strukturnya (gross vs net base vs net must dilaporkan terpisah) — yang akan kami tambahkan adalah interpretasi eksplisitnya di laporan berikutnya.
- Review 4.3 (geometri bergeser ke intraday): benar — median SL 345 pts memang bukan "scalp". Ini pertanyaan owner (bab 6 review #1), bukan keputusan implementasi; kami tidak akan mengubah anchor SL tanpa keputusan owner karena §4 desain memang menetapkan SL di luar POI/sweep.
- Redundansi 100% membuat skor maksimum efektif jadi 11, bukan 12 — implikasinya ke kalibrasi threshold nanti: kalibrasi harus dilakukan **setelah** G3 (dengan item BOS yang sudah ber-friskness), bukan sebelum, agar poin yang dihitung adalah poin yang independen.

---

## 4. Kontrak Test untuk G2 & G3 (sebelum implementasi — review 4.7)

**G2 (partial TP1 50% → SL ke BE):**
1. Total PnL trade = 0,5×(TP1−entry) + 0,5×(exit2−entry) — invariant numerik per trade (± floating error).
2. SL tidak pernah bergerak **melawan** posisi: setelah BE-trigger, SL2 = entry (tepat), bukan di bawahnya utk BUY.
3. Bar yang menyentuh TP1 dan SL sekaligus di hit pertama → tercatat, dengan kebijakan konservatif yang eksplisit di artefak (SL-priority, parity simulator lama).
4. Outcome baru diperbolehkan: `TP1_BE` (TP1 lalu BE), `TP1_TP2` (TP1 lalu TP2), `TP1_SL` (TP1 lalu BE kena — PnL = 0,5×TP1), `SL_full` (langsung SL penuh), `EXPIRE`.
5. Semua hasil G2 dilaporkan berdampingan dengan baseline single-touch (139 trade) — distribusi per outcome, bukan hanya rata-rata.

**G3 (freshness BOS ≤ N bar M5):**
1. Item BOS OK ⟹ ada event BOS searah dengan umur ≤ N — diuji sintetis (fixture umur tepat N dan N+1).
2. Reduksi take-rate dan perubahan WR per bucket dilaporkan vs baseline.
3. N bukan magic number: dipilih dari distribusi umur (2.1) + sweep kecil {24, 36, 48} di replay — hasil semua N dilaporkan, tidak dipilih yang terbaik diam-diam.

---

## 5. Urutan Kerja Kami (mengikuti review bab 6)

| # | Item | Status |
|-|-|-|
| 1 | **G2** — partial TP1 + BE, replay ulang 39 hari, laporan berdampingan baseline | **Berikutnya (dikerjakan)** |
| 2 | **G3** — freshness BOS (kontrak test di atas), sekalian memperbaiki redundansi | Setelah G2, satu replay bisa meng-cover keduanya bila dijalankan sebagai varian terpisah + gabungan |
| 3 | Segmentasi WR per skor — diulang di data pasca-G2 | Menunggu #1 |
| 4 | G1 gate + G4 D1 shadow | Setelah verdict signal beres |
| 5 | Sensitivity POI_REACH & nearest_liquidity_target (review 3.5/4.5) | Dijadwalkan — sweep parameter di infrastruktur yang ada |
| 6 | Window multi-regime (sideways/choppy) | Dicari dari cache 5 bulan yang sudah terbukti ada gunanya (dipakai di 2.1) |

Catatan praktis: **bridge sedang mati** saat analisis ini (seluruh stack python turun — bukan hanya driver), jadi verifikasi 2.1 memakai cache. Replay G2 butuh bridge hidup lagi; kami tidak menyalakan stack tanpa konfirmasi owner.

---

## 6. Jawaban atas 4 Pertanyaan Terbuka untuk Owner (bab 6 review)

1. **Geometri SL (HTF-anchor vs LTF-tighten)** — menunggu keputusan owner; data kami hanya bisa menyumbang: median SL sekarang 345 pts, 28 dari 94 SL punya RR<1,5 (kandidat kena noise), 32 punya RR≥2 (SL jauh di belakang struktur — paling rentan "balik dalam $5" seperti kasus ticket 431035015).
2. **Take-rate ~3,5 sinyal/hari** — menunggu keputusan owner; catatan: angka ini sebelum G3. Setelah freshness BOS, take-rate turun — kalau target bisnis frekuensi lebih tinggi, diskusinya jadi "longgarkan TF entry atau definisi setup", bukan membongkar gate.
3. **Biaya must 27,5 pts** — setuju perlu diverifikasi dari deal history riil (sama dengan arah riset MICRO v2: biaya real per jam); selisih base→must (10,5 pts) memang lebih besar dari seluruh gap ke breakeven.
4. **Dua deviasi** — mitigasi CLOSE: disepakati pertahankan; POI_REACH 1,5×ATR: setuju diuji sensitivity (bab 5 item 5), bukan diubah langsung.
