# Audit SMC/ICT v3 — Checklist Kepatuhan vs Desain Owner (§0–§8)

> **Status: KILL DITUNDA oleh owner.** Laporan ini adalah bukti untuk review manual sebelum keputusan final. Tidak ada keputusan kill/viability yang diambil di luar owner.
>
> Tanggal audit: 2026-09-11 malam · Engine: `strategy_v2/smc.py` (SMC/ICT v3, kandidat pengganti MICRO)
>
> **UPDATE 2026-09-12: G1 & G2 TERTUTUP.** Keempat gap G1–G4 kini sudah diimplement dan direplay (bab 4 + laporan parity `REPORT_SMC_V3_PARITY.md`). Keputusan tetap di tangan owner.

---

## 0\. Ringkasan & Sumber Bukti

**Fungsi laporan**: memverifikasi baris-per-baris bahwa logika program (engine + replay) sesuai desain `rencana-trading-scalping-xauusd.md` §0–§8, dan menyajikan bukti data agar owner bisa memutuskan sendiri.

|Sumber bukti|Isi|
|-|-|
|`data/research/smc_v3/smc_v3_audit.json`|Sampling 6.600 bar M1 (tiap-6 bar, 39.0 hari) — re-evaluasi engine per sampel, pass-rate item, asersi sisi SL, trace kasus|
|`data/research/smc_v3/smc_v3_replay.json`|Replay penuh 39.2 hari — 139 trade, outcome TP/SL, PnL per trade|
|`data/research/smc_v3/smc_v3_parity_replay.json`|Replay multi-varian full-parity (G1+G2+G3+G4 + baseline yang regressed identik ke studi lama)|
|`scripts/smc_v3_study.py` · `scripts/smc_v3_audit.py` · `scripts/smc_v3_parity_replay.py`|Replay, audit & replay parity (read-only, tanpa menyentuh jalur live)|

**Hasil singkat:**

|Aspek|Hasil|
|-|-|
|Mekanika inti vs desain|Sesuai (bias→POI→BOS→sweep→CHoCH→pola→gate RR; bobot skor persis §7)|
|Hasil replay|Koheren & jujur: WR 32.4% vs breakeven-gross 34.2% → gross −16.99 pts/trade|
|Gap kepatuhan|G1–G4 **sudah diimplement & direplay** (bab 4 — status CLOSED) — vonis tetap di tangan owner|
|Keputusan|**Ditunda ke owner** — bukti lengkap di bab 2–4 + laporan parity|

---

## 1\. Checklist Kepatuhan Baris-per-Baris

> Legenda: ✅ sesuai · 🟡 sesuai dengan catatan / deviasi disengaja · ❌ belum diimplement. Kode gap G1–G4 dirinci di bab 4.

### 1.1 Filosofi Top-Down (desain §0)

|Desain|Implementasi|Status|
|-|-|-|
|HTF bias → MTF setup → LTF trigger; tidak ada entry 1-TF saja|H4 bias → M15/M5 POI+BOS → M1 sweep/CHoCH/pola; arah SELALU = bias H4 (aturan emas §3.3 terpenuhi struktural)|✅|
|Lapisan Bias = **1D & 4H**|H4 di engine; D1 (rantai M15→H4→D1) sebagai varian G4 — direplay: menyaring 425/436 sinyal|🟡 engine H4 · G4 CLOSED sebagai varian (lihat bab 4.4)|
|Lapisan Setup = 4H/1H/15M|M15+M5 (1H tidak diambil dari bridge; fungsi sama ter-cover)|🟡|
|Lapisan Entry = 5M/1M|M1 (+ sweep mikro dihitung juga di M5/M15)|✅|

### 1.2 Lapisan Bias — Direction (desain §1.1)

|Desain|Implementasi|Status|
|-|-|-|
|Swing/fractal k kiri-kanan, kronologis, klasifikasi HH/HL-LH/LL|fractal k=2 + dedupe searah; HH/HL vs LH/LL dari perbandingan swing sejenis (high vs high, low vs low)|✅|
|Ranging → no trade|return None → veto (pass-rate item 67.3%, veto 32.7% sampel)|✅|
|EMA50 vs EMA200 4H sebagai **filter kedua** (bukan penentu)|veto bila EMA50<EMA200 melawan bias BULL; fired 0× di window ini (trend H4 bull sepanjang window)|✅|

### 1.3 Liquidity Mayor (desain §1.2)

|Desain|Implementasi|Status|
|-|-|-|
|EQH/EQL, toleransi ±0.1–0.2×ATR|`equal_levels`, toleransi 0.15×ATR|✅|
|Old high/low belum di-sweep|fallback "old high/low TERETABLISH" (region lama closing, bukan extremum segar)|✅|
|Trendline liquidity|tidak diimplement|❌ minor|
|Fungsi: target + filter zona|dipakai sebagai TP1 (`nearest_liquidity_target`) + basis sweep|✅|

### 1.4 Supply & Demand + Premium/Discount (desain §1.3)

|Desain|Implementasi|Status|
|-|-|-|
|Zona base sebelum leg impulsif; fresh > tested|`order_blocks`: fresh = belum di-close-tembus (lihat deviasi mitigasi di bab 4.5)|🟡|
|Premium/discount 50% range 4H|`premium_discount` (window 60 bar H4)|✅ koding — pass-rate hanya 2.8% (lihat catatan di bawah tabel)|
|Output: bias + 1–2 POI mayor + target|1 POI terdekat (OB/FVG M15/M5, bukan S&D 4H mayor)|🟡|

> Catatan item premium/discount: di window uptrend H4, harga hampir selalu di PREMIUM sementara bias BULL → item praktis mati (2.8%). Konsekuensi: hampir semua sinyal berjalan tanpa poin ini (bukti di bab 2.3).

### 1.5 Trend / BOS-CHoCH / Reversal (desain §2.1–2.3)

|Desain|Implementasi|Status|
|-|-|-|
|Konfirmasi trend 15M searah bias → continuation|tidak ada cek trend M15 eksplisit; continuation diimplisitkan lewat POI searah bias|🟡|
|BOS = break searah; CHoCH = break berlawanan; deteksi via close|`bos_choch`: break via CLOSE, anti-lookahead (swing baru dipakai hanya setelah k bar kanan close — diuji test), BOS pertama / CHoCH pembalikan|✅|
|**BOS "sebelum retrace ke POI"** (temporal)|`bos_fresh_bars` (G3) di engine — BOS hanya dihitung bila umur ≤ N bar M5; sweep N∈{24,36,48} direplay semua hasilnya|✅ CLOSED (G3)|
|SFP = sweep + CHoCH segera setelahnya|sweep (usia ≤12 bar di TF-nya) + CHoCH mikro M1 (≤30 bar); dua item skor terpisah, tidak dipaksa berurutan|🟡|

### 1.6 Order Block (desain §2.4)

|Desain|Implementasi|Status|
|-|-|-|
|OB = candle berlawanan terakhir sebelum leg impulsif|persis|✅|
|Displacement kuat|gate 1.2×ATR window penuh (teruji test displacement)|✅|
|Menyebabkan BOS/CHoCH struktural|tidak dicek eksplisit (OB dari swing leg; BOS dicari terpisah)|🟡|
|**Mitigasi = harga menyentuh zona**|fresh = belum ada CLOSE menembus sisi jauh; sentuhan wick TIDAK memitigasi — deviasi disengaja, mohon konfirmasi owner (bab 4.5)|🟡|
|Refined OB (50% zona / FVG dalam OB)|tidak diimplement — POI = zona penuh H/L|❌ minor|

### 1.7 Fair Value Gap (desain §2.5)

|Desain|Implementasi|Status|
|-|-|-|
|FVG 3-candle bull/bear|`fvgs` 3-candle, gap_min 0.05×ATR (buang noise)|✅|
|OB+FVG overlap = POI prioritas|tidak diimplement (OB dan FVG setara dalam daftar POI)|❌ minor|

### 1.8 Lapisan Entry (desain §3.1–3.3)

|Desain|Implementasi|Status|
|-|-|-|
|Harga masuk POI|jarak harga-ke-POI ≤ 1.5×ATR (di dalam zona = 0.0) — lebih longgar dari "masuk zona"|🟡|
|Liquidity sweep mikro + ditolak|`detect_sweep` SFP: wick ≥0.05×ATR menembus, close kembali; usia ≤12 bar|✅|
|CHoCH mikro setelah sweep|item CHoCH M1 ≤30 bar (tidak dipaksa SETELAH sweep secara eksplisit)|🟡|
|Pola candle tabel 3.2|engine pola 12 pola: engulfing bull/bear, hammer/pin, shooting star, morning/evening star, marubozu, piercing, dark cloud, tweezer, 3 soldiers/crows — **inside-bar breakout tidak ada**|🟡|
|"Pola menutup di dalam/di atas POI"|arah pola dicek searah bias; posisi close vs POI tidak dicek (harga wajib dalam 1.5×ATR POI)|🟡|
|Model A continuation / Model B reversal|keduanya hidup sebagai item skor; data: 62% take tanpa sweep segar (Model A), 38% dengan sweep|✅|
|Aturan emas: arah akhir selaras bias|arah = bias H4 selalu; tidak ada counter-trend|✅|

### 1.9 Manajemen Exit (desain §4)

|Desain|Implementasi|Status|
|-|-|-|
|SL di luar POI/extrem sweep + buffer 0.1–0.2×ATR + spread|SL = anchor struktural ∓ (0.15×ATR-M5 + topup 30 pts + spread); asersi sisi 74/74 sinyal benar, 0 pelanggaran (bug SL-terbalik sudah difix + 2 test regresi)|✅|
|TP1 = likuiditas terdekat searah|`nearest_liquidity_target` (swing + EQH/EQL M5)|✅|
|**TP1 partial 50% → SL ke BE**|`smc_exits.py` mode `g2` — TP1 50% → SL ke entry → trailing sisa posisi; unit-tested (kontrak bab 4 RESPON_REVIEW) & direplay|✅ **G2 CLOSED**|
|TP2 / trailing struktur/ATR|trailing = max(structure swing LTF, k×ATR-M1), k=2.0 dari rentang desain 1.5–2.5; TP2 via trailing|✅ CLOSED|
|Time-based exit N candle|tidak diimplement (replay pakai EXPIRE >24 jam); desain: opsional|🟡|

### 1.10 Manajemen Risiko (desain §5)

|Desain|Implementasi|Status|
|-|-|-|
|RR ≥ 1.3 setelah biaya|gate MIN_RR=1.3 — RR ke TP1, SL sudah termasuk topup spread+komisi|✅ (60.2% sampel ditahan gate ini — saringan terbesar)|
|Position sizing otomatis|di luar scope engine (replay mengukur edge dalam pts, lot konstan); rule lot live tetap yang lama|🟡 n/a|

### 1.11 Filter Tambahan (desain §6)

|Desain|Implementasi|Status|
|-|-|-|
|**Item 8 checklist: berita + spread normal = WAJIB (gate)**|`smc.py` gates=True — spread & band ATR; news tetap OFF (keputusan owner)|✅ **G1 CLOSED** (news tetap OFF sesuai keputusan owner)|
|Spread > 35 pts → skip|`GATE_MAX_SPREAD_PTS=35` — di replay no-op (spread snapshot 17 pts)|✅ CLOSED|
|ATR(5M) di luar rentang → skip|band [120, 2500] pts; distribusi window: min 171 / p50 426 / maks 1168 → 0 blok|✅ CLOSED|
|Filter sesi (adaptasi Asia)|tidak ada filter; dekomposisi sesi hanya analitik (overlap justru terburuk −4149 pts)|❌|
|Filter korelasi DXY|tidak diimplement|✅ (desain: opsional)|

> Catatan G1: news historis memang mustahil (policy `NEWS_CALENDAR_UNAVAILABLE` fail-closed sudah jadi kontrak repo — DECISIONS P0-01), dan news tetap OFF sesuai keputusan owner. Spread di replay konstanta 17 pts → gate no-op di replay, tapi gate-nya sudah ada untuk live parity. Band ATR juga tidak pernah memblok di window ini (semua sampel ATR-M5 di dalam band) — gate aktif namun tidak mengubah hasil 39 hari.

### 1.12 Checklist Confluence (desain §7)

|#|Desain|Implementasi|Status|
|-|-|-|-|
|1|Bias 4H searah (2)|bias_h4=2|✅|
|2|Discount/premium (1)|discount=1 (pass 2.8% di window ini)|✅ koding, 🟡 efek|
|3|POI fresh searah (2)|poi_fresh=2 (OB/FVG M15/M5)|✅|
|4|BOS searah (1)|bos=1 (catatan G3 temporal)|✅/G3|
|5|Liquidity sweep (2)|sweep=2|✅|
|6|CHoCH mikro (2)|choch_micro=2|✅|
|7|Pola candle (2)|pattern=2|✅|
|8|Berita + spread normal — **WAJIB gate**|gate spread+ATR di `smc.py` (news OFF sesuai keputusan owner)|✅ G1 CLOSED|
|9|RR ≥ minimum — **WAJIB gate**|ada|✅|
|—|Max 12; threshold ≥8 via backtest|threshold=8 (belum dikalibrasi; dipakai apa-adanya sesuai desain)|🟡|

### 1.13 Arsitektur (desain §8)

|Desain|Implementasi|Status|
|-|-|-|
|Package modular (feed/structure/zones/liquidity/patterns/signal/risk/execution/manager/backtest)|bentuk beda, fungsi sama: `smc.py` = structure+zones+liquidity+patterns+scorer+entry (pure, tanpa I/O, import whitelist dijaga test); `demo_driver.py` = feed+execution+manager; `smc_v3_study.py`/`smc_v3_audit.py` = backtest engine read-only|✅ setara|
|Logger/journal|checklist manusia-baca per keputusan (`checklist` di return) + artefak JSON|✅|

---

## 2\. Bukti Empiris (6.600 sampel, tiap-6 bar, 39.0 hari)

### 2.1 Funnel Keputusan

|Tahap|Sampel|Persen|
|-|-|-|
|RR gate (ditahan)|21.723|60.2%|
|Bias H4 netral (veto)|—|32.7%|
|Skor < 8 (wait)|—|1.8%|
|Tanpa target likuiditas|—|2.2%|
|Tanpa SL struktural|—|1.9%|
|**Sinyal TAKE**|**74**|**1.12%**|

### 2.2 Pass-Rate Item Checklist

|Item|Pass|
|-|-|
|Bias H4|67.3%|
|BOS searah|67.3%|
|POI fresh dalam jangkauan|65.7%|
|CHoCH mikro M1|54.2%|
|Liquidity sweep (SFP)|38.9%|
|Pola candle M1|24.8%|
|Premium/Discount|**2.8%** (item praktis mati di window uptrend)|

### 2.3 Sinyal TAKE (74 sampled)

- Kombo terbanyak (41×): Bias + BOS + POI + CHoCH + Pola = skor 9 — **tanpa sweep** (jalur Model A).
- 17×: + sweep tanpa pola · 8×: full sweep + pola · 4×: dengan premium/discount.
- Take tanpa item bobot-2: tanpa sweep 46 · tanpa pola 21 · tanpa CHoCH 3.
- **Asersi sisi SL: 74/74 benar, 0 pelanggaran** (fix SL-terbalik terbukti bekerja).
- RR rata-rata sampled 2.30 (semua ≥ 1.3 by gate).

### 2.4 Histogram Skor (semua sampel)

|Skor|0|5|7|8|9|10|11|12|
|-|-|-|-|-|-|-|-|-|
|Sampel|13.009|1.149|7.141|293|10.244|421|4.007|176|

> Skor 7 = 0 poin dari premium/sweep/pola → tetap wait. Threshold 8 bekerja.

---

## 3\. Bukti Kasus (Trace Ulang Trade Nyata)

### 3.1 Kasus 1 — TP (+670 pts) · BUY 10 Agu 20:08 UTC

- Skor 9/12 · arah BUY (bias H4 BULL).
- POI bull 4386.23–4393.98 — harga di dalam zona (jarak 0.00×ATR) ✅
- BOS searah 30 event ✅ · CHoCH mikro 2 event ✅ · **hammer** di POI ✅
- RR 3.14 (SL 214 pts / TP1 670 pts) ✅
- Premium ✗ (PREMIUM vs BULL) · Sweep ✗

**Kesimpulan kasus**: entry sah jalur Model A; TP tersentuh — logika masuk-keluar sesuai desain.

### 3.2 Kasus 2 — SL (−226 pts) · BUY 11 Agu 02:21 UTC

- Skor 9/12, struktur sama (POI 4429.38–4431.62 di harga, tweezer_bottom).
- RR 1.68, SL 226 pts di bawah struktur.
- Trade kalah normal — bukan indikasi bug; WR engine 32.4% vs breakeven 34.2% konsisten dengan kondisi ini.

### 3.3 Kasus 3 — Skor Maks 11/12, Tetap SL (−335 pts) · BUY 13 Agu 05:48 UTC

- Semua item kecuali premium: sweep EQL @4395.72 ✅ + morning_star ✅ + CHoCH ✅ + POI 0.00×ATR ✅.
- RR 1.31 (mepet gate).

**Kesimpulan kasus**: bahkan konfluen hampir sempurna kalah di window ini — masalahnya **edge bruto di kondisi pasar window ini**, bukan mekanika skor.

---

## 4\. Daftar Gap Kepatuhan

### 4.1 G2 — Exit Desain §4 — **CLOSED (direplay, hasil netral)**

- Implementasi: `strategy_v2/smc_exits.py` mode `g2` — TP1 partial 50% → SL sisa ke entry (BE) → trailing sisa posisi (structure swing LTF / k×ATR-M1, k=2.0; TP2 via trailing). Unit-tested; SL tidak pernah mundur dari BE (kontrak test).
- Replay (jendela dipin 39.2 hari, biaya R1 base 17 / must 27.5, seluruh funnel dapat dibaca di laporan parity): n 139→137, WR 32.4%→32.1%, breakeven-WR 33.9%→33.8%, gross −16.99→−18.21 pts/trade, net-must −44.49→−45.71.
- Atribusi per-trade (136 trade matched): 92 SL→SL_full; 40 TP→TP1_TRAIL (TP penuh rata-rata 696 pts → 711.6 pts, justru sedikit lebih baik); 3 TP→TP1_BE (BE berhasil menyelamatkan 3 trade: +355.5 / +89.5 / +182.5 pts alih-alih −335 dst.); 0 SL→BE. Delta total hanya −4.7 pts.
- Membaca: BE-move jarang tersentuh karena SL struktural terlalu jauh (median > 300 pts) — manajemen exit desain §4 **netral** di window ini; vonis baseline praktis tidak berubah (−44.49 → −45.71). TAPI n-kecil (3 rescue, n=137) → CI lebar; kesimpulan kuat tidak dibolehkan.

### 4.2 G1 — Gate Item-8 §7 — **CLOSED (diimplement; no-op di window ini)**

- Implementasi: `smc.py` `gates=True` — spread > 35 pts skip; ATR-M5 di luar band [120, 2500] pts skip. News tetap OFF (keputusan owner).
- Replay: n=139, hasil identik baseline (0 blok — spread snapshot 17 pts < 35; distribusi ATR-M5 window: min 171 / p50 426 / maks 1168, semua di dalam band).
- Membaca: gate aktif di kode dan siap live parity; di data 39 hari ini memang tidak ada kondisi yang dilarang item-8. Bukti aktual perlu window lain (news/spread historis tidak tersedia di replay — fail-closed policy tetap).

### 4.2 G1 — Gate Item-8 §7 Belum Ada (wajib sebelum live)

- Desain §7 item 8: "tidak dalam window berita high-impact & spread normal" — **gate, bukan skor**.
- Engine: belum ada gate spread (>35 pts skip) dan ATR-M5 di luar rentang skip.
- Konteks: news historis mustahil (kontrak repo P0-01 — `NEWS_CALENDAR_UNAVAILABLE` fail-closed); spread replay konstanta 17 pts → gate spread no-op di replay, tapi wajib ada untuk live parity.

### 4.3 G3 — BOS "Sebelum Retrace ke POI" — **CLOSED (direplay sweep N∈{24,36,48})**

- Implementasi: `smc.py` `bos_fresh_bars` — item BOS hanya dihitung bila event searah terbaru berumur ≤ N bar M5.
- Replay: b24 = b36 = b48 identik (n=138, gross −13.21, net-must −40.71). Hanya 1 trade berbeda dari baseline (dihapus: SELL −539 pts — penghapusan menguntungkan). Median umur BOS saat item OK = 129 bar M5 → sweep sampai 48 masih menangkap hampir semua.
- Membaca: freshness BOS hampir tanpa efek di window ini — redundansi Bias↔BOS (100% kondisional, cache 5 bulan) tetap isu struktural yang harus dibereskan SEBELUM kalibrasi threshold.

### 4.4 G4 — Bias D1 — **CLOSED (direplay; penyaring paling agresif, n terlalu kecil utk disimpulkan)**

- Implementasi: varian — struktur D1 dari rantai penuh M15→H4→D1 (99 hari; hanya bar closed; minimum 25 bar D1). Veto bila D1 berlawanan ATAU netral (desain §1.1).
- Replay: 436 sinyal take → 213 veto struktural + 212 masa warmup D1 (window 39 hari < 25 bar D1 full) → **11 selamat** (semua BUY — window memang bull di D1 periode itu). n=11 → CI95 WR [16%, 75%] — **terlalu kecil untuk disimpulkan apa pun**; 212 pembunuhan berasal dari warmup, bukan sinyal G4.
- Membaca: menunjukkan POTENSI besar (WR 45.5%, breakeven 25.6%, gross +188.7 pts/tr) tapi buktinya lemah. Perlu window yang lebih panjang untuk data D1 yang matang.

### 4.4b Parity penuh (G1+G2+G3(36)+G4) — n=10, gross +125.7 pts/tr

- Semua gap diterapkan bersamaan: hasil paling menarik tapi paling tidak stabil (n=10, CI95 [10%, 70%]). Status: **bukti untuk review, bukan rekomendasi.**

### 4.5 Deviasi Disengaja — Mohon Konfirmasi Owner

- **Mitigasi OB/FVG basis CLOSE** (menembus sisi jauh), bukan "harga menyentuh zona" (desain §2.4). Alasan: wick di zona = liquidity grab yang justru mau direact-kan; sudah diuji test khusus.
- **POI_REACH 1.5×ATR** — lebih longgar dari "masuk zona" (desain §3.1).

---

## 5\. Kesimpulan & Rekomendasi

### 5.1 Kesimpulan

1. **Mekanika inti sesuai desain**: bias→POI→BOS→sweep→CHoCH→pola→gate RR; bobot skor persis §7; aturan emas arah terpenuhi; anti-lookahead BOS/CHoCH teruji test; SL-side invariant terbukti 74/74.
2. **Hasil replay koheren** — tidak ada lagi inkonsistensi label (bug SL-terbalik sudah difix); WR 32.4% < breakeven 34.2% menjelaskan angka negatif apa adanya.
3. **Keempat gap (G1–G4) sudah diimplement & direplay** (bab 4, status CLOSED; detail di `REPORT_SMC_V3_PARITY.md`) — hasil: G1 no-op di window ini, G2 netral, G3 hampir tanpa efek, G4 penyaring agresif dengan n terlalu kecil. Vonis tetap di tangan owner.

### 5.2 Rekomendasi Langkah (menunggu owner)

1. ~~Implement + replay G2~~ → **SELESAI** — hasil netral (−44.49 → −45.71); vonis angka baseline praktis tidak berubah.
2. ~~Gate item-8~~ → **SELESAI** — aktif di kode; no-op di window ini.
3. ~~Freshness BOS + bias D1~~ → **SELESAI** — G3 tanpa efek; G4 menjanjikan tapi n=11. Lanjut: replay window lebih panjang (D1 matang) + bereskan redundansi Bias↔BOS sebelum kalibrasi threshold + sensitivity POI_REACH/TP1-target + window multi-regime.
4. ~~Sensitivity POI_REACH + window sideways~~ → **SELESAI (14 Sep)** — POI makin ketat makin baik di KEDUA window (trend: −16.99→−1.36 gross/tr; sideways: strict satu-satunya positif +111.3 net-must, default 1.5×ATR −204.1); kurva threshold MONOTON TURUN (skor tinggi = terburuk) → kalibrasi tetap ditahan. Bukti: `REPORT_SMC_V3_SENSITIVITAS.md` · `smc_v3_sensitivity_replay.json`. Keputusan ganti default POI_REACH = milik owner.
