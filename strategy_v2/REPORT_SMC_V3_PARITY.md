# Replay Full-Parity SMC v3 — Semua Gap Ditutup (G1+G2+G3+G4)

> **Status: BUKTI UNTUK REVIEW OWNER.** Tidak ada keputusan kill/viability di dokumen ini. Keputusan tetap di tangan owner.
>
> Tanggal: 2026-09-12 · Engine: `strategy_v2/smc.py` + `strategy_v2/smc_exits.py` · Replay: `scripts/smc_v3_parity_replay.py`

---

## 0\. Ringkasan Satu Halaman

**Pertanyaan yang dijawab:** apakah vonis baseline (gross −16.99 pts/trade, net-must −44.49) berubah setelah desain §0–§8 diimplement penuh di jalur evaluasi/replay?

**Jawaban singkat:**

|Varian|Apa yang diuji|n|WR|Breakeven-WR|Gross/tr|Net-must/tr|
|-|-|-|-|-|-|-|
|baseline|parity studi lama (regresi silang ✅)|139|32.4%|33.9%|−16.99|−44.49|
|g2_exit|G2: exit §4 penuh|137|32.1%|33.8%|−18.21|−45.71|
|g3_b36|G3: freshness BOS ≤36 bar M5|138|32.6%|33.8%|−13.21|−40.71|
|g1_gate|G1: gate item-8 (spread+ATR)|139|32.4%|33.9%|−16.99|−44.49|
|g4_d1|G4: bias wajib D1+H4 searah|11|45.5%|25.6%|+188.73|+161.23|
|**parity**|**G1+G2+G3(36)+G4 bersamaan**|**10**|**40.0%**|**26.4%**|**+125.65**|**+98.15**|

> Poin utama: **G2 (yang paling ditunggu) ternyata NETRAL** — manajemen exit §4 tidak mengubah vonis. Yang mengubah angka adalah **G4 (bias D1)** — tapi dengan n=10–11, angka itu terlalu rapuh untuk dijadikan dasar keputusan apa pun. Semua angka positif di tabel ini WAJIB dibaca dengan CI95 WR [10%, 70%].

---

## 1\. Metodologi

### 1.1 Jendela & Paritas Angka

|Item|Nilai|
|-|-|
|Jendela|39.2 hari, **dipin kedua tepi** ke artefak studi lama: 3 Agu 11:39 → 11 Sep 17:08 UTC|
|Bar M1 evaluasi|39.598|
|Biaya|sel R1 Stage 1: base 17 pts, must 27.5 pts (ESTIMATED_COST_MODEL)|
|Feed|emulasi kedalaman studi lama: M5 8.000, M15 3.000, H4 250 bar; M1 difilter ke jendela|
|Regresi silang|baseline **identik** studi lama: n 139 = 139, gross −16.99 = −16.99, outcomes TP44/SL94/EXPIRE1 = identik|

> Regresi silang identik berarti seluruh harness (window, funnel, semantik posisi) direplikasi dengan benar — angka varian dibandingkan pada fondasi yang sama persis dengan vonis lama.

### 1.2 Aturan Simulasi

- Satu posisi per varian, cooldown 5 menit, entry di close M1 bar sinyal, scan exit mulai bar berikutnya (anti-lookahead).
- SL-priority saat bar menyentuh dua level (konservatif, parity simulator lama).
- Posisi yang belum selesai di ujung jendela di-drop (`masih_open_di_akhir_data`) — parity studi lama.
- News gate **OFF** (keputusan owner); G1 hanya spread + band ATR.

### 1.3 Varian

|Varian|Exit|Filter entry tambahan|
|-|-|-|
|baseline|first-touch SL/TP penuh (parity lama)|-|
|g2_exit|**desain §4**: TP1 partial 50% → SL sisa ke entry (BE) → trailing structure/ATR (k=2.0); TP2 via trailing|-|
|g3_b24/36/48|legacy|BOS searah hanya dihitung bila umur ≤ N bar M5|
|g1_gate|legacy|spread > 35 pts skip; ATR-M5 di luar [120, 2500] pts skip|
|g4_d1|legacy|struktur D1 (rantai penuh M15→H4→D1, ≥25 bar) wajib searah bias H4; D1 netral/berlawanan = no-trade (desain §1.1)|
|parity|g2|g1 + g3(36) + g4|

---

## 2\. Atribusi Per-Trade

### 2.1 G2 — Siapa Berubah Saat Exit §4 Aktif (136 trade matched)

|Transisi|Jumlah|Makna|
|-|-|-|
|SL → SL_full|92|SL awal tertembak sebelum TP1 — partial/BE tidak sempat bekerja|
|TP → TP1_TRAIL|40|TP1 tercapai (leg 50% fix) → sisa di-trailing|
|TP → TP1_BE|3|**BE menyelamatkan 3 trade** (harga sentuh TP1 lalu berbalik ke entry): hasil +355.5 / +89.5 / +182.5 pts, bukan −335 dst.|
|SL → TP1_BE / SL → TP1_TRAIL|0|**Tidak ada satupun trade SL yang diselamatkan BE** — SL struktural terlalu jauh (median > 300 pts) untuk perjalanan TP1→BE sebelum SL tertembak|
|EXPIRE → EXPIRE|1|time-stop|

|Metrik|Baseline (exit penuh)|G2 (§4)|
|-|-|-|
|WR|32.4%|32.1%|
|Avg win|715.9 pts|716.4 pts|
|Avg loss|367.9 pts|365.8 pts|
|Breakeven-WR|33.9%|33.8%|
|Gross/trade|−16.99|−18.21|

> Trade TP-penuh yang jadi TP1_TRAIL rata-rata justru sedikit lebih untung (696.1 → 711.6 pts) — trailing menahan sisa posisi dengan baik saat tren lanjut. Tapi efeknya cuma −4.7 pts total di 137 trade: **exit §4 netral**, bukan penyelamat dan bukan pembunuh.

### 2.2 G3 — Apa yang Dibuang Freshness BOS

|Item|Nilai|
|-|-|
|Trade dihapus (b36)|1 dari 139: SELL 3 Sep, SL −539 pts → penghapusan menguntungkan|
|Perubahan|n 139→138; gross −16.99→−13.21; net-must −44.49→−40.71|
|b24 = b36 = b48|identik — median umur BOS saat item OK = 129 bar M5, jadi semua threshold menangkap objek yang sama|
|Sisa masalah|redundansi Bias↔BOS (P(BOS searah\|bias)=100%, cache 5 bulan) TETAP ADA — item #4 masih bukan konfirmasi independen; kalibrasi threshold tetap ditahan|

### 2.3 G1 — Gate Item-8

|Item|Nilai|
|-|-|
|Blok di window ini|0 (spread snapshot 17 pts < 35; ATR-M5 min 171 / p50 426 / maks 1168 — semua di dalam band [120, 2500])|
|Status|aktif di kode (`gates=True`), siap live parity; di replay memang tidak ada kondisi yang dilarang item-8|
|Catatan|efek gate hanya bisa dibuktikan di window/insiden lain (news/spread historis tidak tersedia; policy fail-closed tetap)|

### 2.4 G4 — Siapa yang Lolos Filter D1

Funnel: 436 sinyal take → 213 veto struktural (D1 berlawanan/netral) + 212 masa warmup D1 (window < 25 bar D1) → **11 selamat**.

|Karakteristik 11 trade selamat|Nilai|
|-|-|
|Semua BUY|ya — D1 BULL memang diuntungkan oleh regime window ini|
|WR|45.5% (5W/6L) — CI95 [16%, 75%]|
|Avg win / avg loss|707.2 / 243.3 pts → breakeven-WR 25.6% (vs WR aktual 45.5%)|
|Gross|+2.076 pts total (+188.7/tr); net-must +161.2/tr|
|Sebaran|24–27 Agu (satu regim bull D1 yang padat); sesi overlap & ny_late|

> **Peringatan interpretasi (wajib):** (1) 212 dari 425 "pembunuhan" berasal dari warmup D1 — efek filter sesungguhnya terukur pada 213 veto; (2) 11 trade menumpuk di 4 hari — bukan sampel independen; (3) CI95 mencakup 16%–75% — angka +188.7/tr tidak signifikan; (4) semua BUY di window bull = regime-fit, bukan bukti edge lintas-regime. Ini **bukti untuk dites lebih lanjut**, bukan hasil.

### 2.5 Parity Penuh (G1+G2+G3+G4)

n=10 (9 dari 11 trade G4; 1 habis karena freshness G3; 1 kalah cooldown chain), WR 40.0%, breakeven 26.4%, gross +125.7/tr, net-must +98.2/tr. Distribusi skor bergeser (3 trade skor-8 justru menang) — artefak n-kecil, jangan dibaca sebagai sinyal threshold. CI95 WR [10%, 70%].

---

## 3\. Batas Kejujuran Simulasi

1. **Sim ini secara sistematis UNDERSTATE biaya live.** Bukti dari sel R1 sebelumnya: sim A −12.34$ vs live −28.32$ (≈ 2.3× lebih buruk di live). Sel biaya base 17 / must 27.5 pts adalah ESTIMATED_COST_MODEL dari spread snapshot, bukan spread/komisi/slippage historis per-bar. Artinya: **arah perbandingan antar-varian yang jadi bukti, bukan dolar/dolarnya.** Selisih antar varian (mis. G2 −1.2 pts vs baseline) jauh lebih kecil dari bias biaya — konklusi "netral" harus dibaca sebagai "dalam resolusi pengukuran ini".
2. G2 memakai estimasi eksekusi partial: leg-1 fix di TP1, leg-2 exit di level trail — tanpa modeling partial-fill/broker. Live partial close bisa lebih buruk.
3. G4 memakai D1 dari agregasi M15→H4→D1 (bukan feed D1 native) — struktur swing bisa beda tipis vs D1 broker.
4. Window 39 hari = SATU regime (review: trending/bull di H4; D1 bull di paruh kedua). Ketahanan sideways kini terjawab sebagian (14 Sep): pass sideways 7.95 hari di `REPORT_SMC_V3_SENSITIVITAS.md` — default 1.5×ATR makin hancur di sideways (−204.1), strict satu-satunya positif (+111.3). Window panjang multi-regime tetap di antrian.
5. n per bucket kecil (sesi 22–51; arah 69–70; skor 2–124; G4 11) — semua breakdown lead-only, bukan konfirmasi.

---

## 4\. Status Gap (ringkas)

|Gap|Status|Efek di replay 39 hari|
|-|-|-|
|G1 gate item-8|CLOSED (kode)|no-op (0 blok)|
|G2 exit §4|CLOSED (kode + test)|netral: −44.49 → −45.71 net-must|
|G3 freshness BOS|CLOSED (kode)|hampir nol: −44.49 → −40.71 (1 trade)|
|G4 bias D1|CLOSED (varian)|n=11, gross +188.7/tr — TIDAK disimpulkan|

Deviasi disengaja (mitigasi basis CLOSE; POI_REACH 1.5×ATR) tetap menunggu konfirmasi owner seperti sebelumnya. Sensitivity POI_REACH sudah DIJALANKAN (14 Sep, `REPORT_SMC_V3_SENSITIVITAS.md`): POI ketat konsisten lebih baik di kedua window — keputusan mengganti default tetap milik owner.

---

## 5\. yang Terbuka untuk Owner

1. Angka G4/parity (+98 s.d. +161 pts/tr net-must, n≈10) — cukup menarik untuk replay window panjang (D1 matang, multi-regime), cukup rapuh untuk tidak mengubah apa pun hari ini.
2. Vonis baseline tidak berubah setelah G2+G3+G1: gross per trade masih negatif di luar subset G4. Keputusan kill/keep/jadwal-replay-panjang sepenuhnya milik owner.
3. Antrian riset yang tersisa (urut prioritas review): bereskan redundansi Bias↔BOS → kalibrasi threshold (peta kurva tersedia di `REPORT_SMC_V3_SENSITIVITAS.md`, monotone turun — tidak dipakai kalibrasi); replay window panjang multi-regime (D1 matang).

---

## 6\. Artefak

|File|Isi|
|-|-|
|`data/research/smc_v3/smc_v3_parity_replay.json`|replay 8 varian + meta + trades per varian|
|`data/research/smc_v3/parity_run.log`|log run + regresi silang baseline|
|`scripts/smc_v3_parity_replay.py`|skrip replay multi-varian (read-only)|
|`strategy_v2/smc_exits.py`|simulator exit legacy + g2 (unit-tested)|
|`tests/strategy_v2/test_smc_exits.py`, `test_smc_gates_freshness.py`|kontrak exit §4, gate item-8, freshness BOS|

---

## 7\. Pemetaan Status vs REVIEW_TANGGAPAN_SMC_V3.md

### 7.1 Prioritas bab 5 (review)

|Prio|Item review|Status|
|-|-|-|
|1|G2 — implement + replay partial TP1 + BE|**SELESAI** — `smc_exits.py` + replay; hasil netral (bab 2.1) — vonis baseline tidak berubah|
|2|Cek redundansi Bias↔BOS|**SELESAI** (lebih dari diminta) — bukan query audit 39 hari, tapi cache 5 bulan (11.235 sampel): P(BOS searah\|bias)=100%, umur median 129 bar M5 → kalibrasi ditahan (`RESPON_REVIEW_SMC_V3.md`)|
|3|Segmentasi WR by skor|**SELESAI, tidak konklusif** — 88% trade menumpuk di skor 9 (n bucket 2–3); post-G2 by_score di artefak parity juga n-kecil — jujur dilaporkan, bukan dipakai menyimpulkan|
|4|Kalibrasi ulang threshold (wajib multi-regime)|**SENGAJA DITAHAN** — sesuai review: redundansi belum beres + window bull-only; tercatat di antrian (bab 5.3)|
|5|G1 gate item-8|**SELESAI** di kode (live parity); no-op di replay — persis prediksi review 3.3|
|6|G4 bias D1 shadow|**SELESAI** sebagai varian replay (baseline tidak disentuh); hipotesis review "mengurangi trade, menaikkan WR" terkonfirmasi arah (139→11 trade; WR 32.4%→45.5%) TAPI n=11 → tidak disimpulkan|
|7|Sensitivity POI_REACH & nearest_liquidity_target|**BELUM** — antrian (infrastruktur replay siap, parameter sweep tinggal dijalankan)|
|8|Jendela sideways/choppy terpisah|**BELUM** — antrian; diidentifikasi sebagai syarat sebelum kalibrasi (prio 4)|
|9|Keputusan geometri SL (HTF vs LTF-tighten)|**MILIK OWNER** — pertanyaan terbuka 1 review; bukan pekerjaan implementasi|

### 7.2 Temuan tambahan review bab 4

|Item review|Status|
|-|-|
|4.1 Reframing statistik (n=139 belum cukup bukti)|**DITERIMA** — CI95 WR [24,6%; 40,2%] memuat breakeven 34,2%; bahasa laporan diganti "belum cukup bukti"|
|4.2 Pisahkan edge-sinyal vs asumsi biaya|**TERPENUHI secara struktural** — semua tabel memisahkan gross / net-base / net-must; catatan kejujuran sim (bab 3) eksplisit; verifikasi biaya riil tetap pertanyaan owner (bab 6.3 review)|
|4.3 Geometri trade bergeser ke intraday|**DICATAT sebagai keputusan owner** — belum diputuskan; terkait pertanyaan terbuka 1|
|4.4 Jangan kalibrasi dari window bull-only|**DITAATI** — kalibrasi ditahan sampai multi-regime + redundansi beres|
|4.5 RR-gate + bias veto dominan (~95%) → sensitivity target likuiditas sama pentingnya|**DITERIMA sebagai antrian** (prio 7 di atas); take-rate 3,5/hari dilaporkan eksplisit di meta/varian|
|4.6 n per bucket tampilkan eksplisit|**TERPENUHI** — semua breakdown di artefak & laporan menyertakan [n, wr, gross] per bucket; klaim bucket turun jadi lead-only|
|4.7 Perluas disiplin test ke G2/G3|**TERPENUHI** — test kontrak BE-move (SL tidak pernah mundur dari BE) di `test_smc_exits.py`; test freshness BOS (event harus dalam N bar) di `test_smc_gates_freshness.py`|

### 7.3 Pertanyaan terbuka review (bab 6) — tetap MILIK OWNER

1. Geometri SL HTF vs LTF-tighten — belum diputuskan (temuan 4.3).
2. Target take-rate ~3,5 sinyal/hari vs ekspektasi frekuensi — belum diputuskan.
3. Verifikasi biaya "must" 27,5 pts dari deal history riil — belum ada deal history untuk ini.
4. Konfirmasi dua deviasi (mitigasi CLOSE: sudah disetujui owner; POI_REACH: menunggu sensitivity test prio 7).
