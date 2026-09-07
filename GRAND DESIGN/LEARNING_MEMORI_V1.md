# DESAIN v1 — Learning Memory & Pola Candle untuk ARE

Status: **DESAIN (belum implementasi)** · Berlaku untuk: micro (utama), scalp (kedua)
Tujuan dokumen: spesifikasi lengkap sistem belajar otomatis — rekam kondisi entri, ingat pola candle, pelajari win/loss historis, dan jadikan gate selektivitas berbasis data.

---

## 1. Tujuan

Bot (micro lalu scalp) belajar dari pengalamannya sendiri:

1. **Rekam kondisi lengkap** setiap entri: indikator (RSI, ATR, EMA, AO), bentuk candle, volume, sesi, posisi range.
2. **Ingat semua entri** (bagus maupun buruk/SL) beserta kondisinya di satu sumber kebenaran.
3. **Jawab sebelum entri**: "kondisi seperti ini pernah entri N kali → X win / Y loss (Z%), rata-rata ±P poin".
4. **Gate selektivitas**: kondisi yang historisnya buruk → demote atau blokir entri.
5. **Belajar dari kesalahan**: loop tertutup capture → outcome → agregat → filter, terus menyempurna.

Batasan kejujuran: sistem memberikan **probabilitas bersyarat + ukuran sampel**, bukan janji arah pasti ("naik 100–200 poin"). Semakin banyak data, semakin akurat estimasinya.

---

## 2. Arsitektur & Alur

```
┌─ ENGINE (UI/src/app/api/are/decision/route.ts) ──────────┐
│ 1. Hitung sinyal seperti sekarang                        │
│ 2. Bangun FINGERPRINT kondisi saat ini                   │
│    (indikator + pola candle + AO + volume + konteks)     │
│ 3. Query MEMORI → statistik bucket serupa                │
│ 4. Soft gate: demote/blokir kalau historis jelek         │
│ 5. Respons: decision + fingerprint + ringkasan memori    │
└──────────────────────────┬───────────────────────────────┘
                           ▼
┌─ BOT (are/bot.py) ───────────────────────────────────────┐
│ 6. Saat entri dieksekusi: simpan fingerprint → memori    │
│ 7. Saat posisi close: tulis outcome (win/loss, poin,     │
│    alasan, durasi) → update bucket agregat               │
└──────────────────────────┬───────────────────────────────┘
                           ▼
┌─ MEMORI (data/learning/) ────────────────────────────────┐
│ trade_memory.jsonl  → sumber kebenaran (append-only)     │
│ buckets.json        → cache agregat (di-update cepat)    │
│ Di-seed awal dari backtest 2 tahun data parquet lokal    │
└──────────────────────────────────────────────────────────┘
```

Komponen baru: `are/learning.py` (logika bucket/query/decay) + `scripts/seed_memory.py` (bootstrap backtest).

---

## 3. Sidik Jari Kondisi (Fingerprint)

Satu record JSON per **keputusan entri** (disimpan saat posisi benar-benar terbuka), diperkaya **outcome** saat close.

```jsonc
{
  "id": "mem-20260904-1432-0001",
  "ts": "2026-09-04T14:32:00Z",
  "style": "micro", "symbol": "XAUUSD",
  "direction": "BUY", "entry_price": 4460.50,
  "sl_points": 390, "tp_points": 150, "lot": 0.03,
  "outcome": {
    "closed_at": "2026-09-04T14:47:00Z",
    "exit_price": 4462.00, "points": 150, "pnl": 4.50,
    "close_reason": "tp_sl", "held_bars_m5": 15, "win": true
  },
  "conditions": {
    "session": "london", "hour": 14,
    "spread_points": 17,
    "m1": {
      "rsi": 52, "atr": 1.9, "ema9_21": "bullish",
      "ao": { "osc": 0.35, "signal": 0.21, "hist": 0.14,
              "state": "bull_cross", "slope": 0.05 },
      "volume": { "ratio_last_avg20": 1.7, "surge": true,
                  "vol_slope20": 0.6, "up_vol_pct": 58,
                  "avg_vol20": 1400 },
      "pattern": ["engulfing_bull"],
      "body_profile": "3g_2r"
    },
    "m5": {
      "rsi": 55, "atr": 3.9, "ema9_21": "bullish",
      "ao": { "osc": 0.80, "signal": 0.50, "hist": 0.30,
              "state": "bull", "slope": 0.10 },
      "volume": { "ratio_last_avg20": 0.9, "surge": false,
                  "vol_slope20": -0.1, "up_vol_pct": 52,
                  "avg_vol20": 5200 },
      "pattern": ["inside_bar"],
      "candle_200": { "trend": "up", "range_pos_pct": 62 }
    },
    "m15": {
      "rsi": 58, "atr": 6.2, "ema9_21": "bullish",
      "pattern": []
    },
    "h4": { "bias": "BUY", "range_pos_pct": 55, "last_body_pct": 70 },
    "d1": { "trend": "up", "rsi": 55, "ema50_slope": "up" }
  }
}
```

Catatan: semua nilai indikator **dibulatkan/discretisasi saat bucket**, fingerprint menyimpan nilai mentahnya.

---

## 4. Indikator Baru — AO (5,13,5,Close)

Moving Average of Oscillator (gaya MACD-histogram), dihitung per TF (M1/M5/M15):

```
median/close dipakai = CLOSE (sesuai permintaan user; opsi H+L/2 tersedia)
osc    = SMA(close, 5) − SMA(close, 13)
signal = SMA(osc, 5)
hist   = osc − signal
```

Direkam per TF: `osc`, `signal`, `hist`, `state`, `slope_hist` (selisih hist 3 bar terakhir).
`state` = `bull_cross` (osc memotong signal ke atas), `bear_cross`, `bull` (osc > signal), `bear` (osc < signal), `none`.

Catatan jujur: AO adalah **momentum harga** (Bill Williams), bukan volume — oleh karena itu volume dibaca terpisah (Bagian 6). Di engine, AO dipakai sebagai **fitur capture** (masuk fingerprint), bukan pengganti sinyal yang ada.

---

## 5. Pustaka Pola Candle (~20 pola standar, tanpa scraping)

Pola klasik yang terdokumentasi luas (literatur candlestick: Bulkowski, Morpheus/Jepang), diimplementasikan sebagai **fungsi deteksi murni** di `UI/src/lib/patterns.ts` — tidak ada scraping; daftar pola adalah himpunan tetap.

| Kategori | Pola |
|---|---|
| Reversal tunggal | Hammer, Hanging Man, Shooting Star, Inverted Hammer, Pin Bar (pinocchio), Doji, Long-Legged Doji, Spinning Top, Marubozu |
| Reversal 2 bar | Bullish/Bearish Engulfing, Bullish/Bearish Harami, Tweezer Top/Bottom, Inside Bar, Outside Bar |
| Reversal 3 bar | Morning Star, Evening Star, Three White Soldiers, Three Black Crows |
| Struktur | Higher-High / Lower-Low (3 bar), Gap Up/Down |

Setiap deteksi mengembalikan `{ name, direction: 'bull'|'bear', strength: 0-1, bar_index }`.
Beberapa pola bisa aktif bersamaan (mis. engulfing + inside bar di bar berbeda).
Validasi empiris: pola hanya "dipercaya" bila bucket memori menunjukkan edge (Bagian 7).

---

## 6. Pembacaan Volume (tick_volume)

Dari candle MT5 (`tick_volume`; fallback `volume`):

- `avg_vol20` — rata-rata volume 20 bar terakhir.
- `ratio_last_avg20` — volume bar terakhir / avg_vol20.
- `surge` — true jika `ratio > 1.5` (lonjakan, dipakai sinyal arah seperti engine sekarang).
- `vol_slope20` — kemiringan regresi sederhana volume 20 bar (naik/turun/datar).
- `up_vol_pct` — persentase volume candle naik (close > open) dalam 20 bar; > 60 = tekanan beli, < 40 = tekanan jual.
- `vol_on_pattern` — volume saat pola terdeteksi (mis. engulfing + surge → strength pola dinaikkan).

Volume masuk fingerprint di M1 dan M5 (micro) serta M5/M15 (scalp), dan menjadi salah satu dimensi bucket.

---

## 7. Penyimpanan Memori (satu sumber kebenaran)

- **`data/learning/trade_memory.jsonl`** — append-only JSONL, satu baris per trade (fingerprint + outcome). Ini SATU-SATUNYA sumber kebenaran riwayat. Tidak pernah ditulis ulang massal; recovery bucket bisa dibangun ulang dari file ini.
- **`data/learning/buckets.json`** — cache agregat: `{ bucket_key: { n, wins, losses, sum_points, first_ts, last_ts } }`. Bisa di-rebuild kapan saja dari JSONL (`python -m are.learning rebuild`).
- Direktori `data/learning/` adalah artefak runtime (masuk `.gitignore`-style, seperti `bot_state_*.json`), bukan kode.

**Bucket key (discretisasi kasar, anti-overfitting):**

```
style | direction | session | h4_bias | pattern_m5 | rsi_band_m5 (10-pt) |
atr_band_m5 (1-pt) | ao_state_m5 | vol_surge
```

Contoh: `micro|BUY|london|BUY|engulfing_bull|r50-60|a3-4|bull|surge`.
Bucket dibuat **kasar** (band, bukan nilai presisi) supaya sampel cukup banyak dan tidak overfit ke nilai eksak.

---

## 8. Agregasi & Kapan Diperbarui

- **Saat entri**: bot menulis record OPEN ke JSONL (`outcome: null`) — sekali, sinkron, murah.
- **Saat close** (TP/SL/reversal/time-exit): bot meng-update record yang sama (`outcome` terisi) + update `buckets.json` untuk 1 bucket terkait — operasi O(1).
- **Query engine**: hanya baca `buckets.json` (cache), tidak baca JSONL — latensi mikro detik.
- **Rebuild bucket**: `are.learning rebuild` (dipakai oleh seeding & recovery).
- **Decay recency**: saat agregat dibaca, bobot trade lebih tua dari 60 hari mengecil 50%/bulan (pasar non-stasioner; dihitung dari `last_ts` bucket).

---

## 9. Query & Soft Gate

Sebelum entri, engine:

1. Hitung bucket key kondisi saat ini → ambil `{n, wins, losses, avg_points, winrate}`.
2. **Estimasi arah** (opsional, ditampilkan): dari bucket, `P(naik ≥100pt dalam 30 bar M5)`, `P(turun ≥100pt)`, `P(tidak keduanya)` — dengan catatan ukuran sampel.
3. **Gate lunak (fase 1)**:
   - `n < minSamples (default 10)` → tampilkan "memori: belum cukup data (n=N)" → **tidak memblokir**.
   - `n ≥ 10` dan `winrate ≥ 60%` → tampilkan "memori: N entri, W/L (X%) — kondisi kuat" → **izinkan** (+ optional boost keyakinan).
   - `n ≥ 10` dan `winrate < 45%` → **DEMOTE**: keputusan dipaksa `WAIT` dengan alasan `"memori: kondisi ini N entri, W/L (X%) — historis buruk"` (masuk telemetri rejections sebagai kategori `memory`).
   - Ambang per style di `TRADING_STYLES`: `memoryMinSamples`, `memoryMinWinRate`.
4. **Pelaporan jujur**: angka memori selalu ditampilkan bersama `n` (ukuran sampel); tanpa `n`, angka tidak dianggap.

Gate selalu **lunak di fase 1** (informasi + demote), **keras di fase 2** (blokir penuh) setelah backtest membuktikan gate memperbaiki P&L.

---

## 10. Loop Belajar & Laporan

- Setiap close → bucket ter-update → statistik kondisi berubah → gate menyesuaikan otomatis.
- **Laporan berkala** (skrip `scripts/report_memory.py`, bisa dijadwalkan): top-10 kondisi dengan ekspektasi terbaik/terburuk per style → dasar rekomendasi filter manual tambahan.
- **Kategori rejections baru**: `memory` (ditolak gate memori) — tampil di panel CHAMPION seperti kategori lain.

---

## 11. Bootstrap Memori dari Backtest 2 Tahun

Trade nyata baru ~20 — tidak cukup untuk statistik. Solusi: **seeding dari data lokal** (tanpa MT5):

1. Baca parquet lokal `XAUUSD_M1/M5/M15` (2 tahun, hingga 1 Sep 2026) via polars.
2. Replay logika sinyal engine (replikasi `route.ts` — sama seperti `scripts/backtest_scalp_adaptive.py`) untuk micro (TP 150) dan scalp (TP adaptif).
3. Setiap entri simulasi → tulis fingerprint + outcome (TP/SL dari jalur M1) ke `trade_memory.jsonl`.
4. Rebuild `buckets.json` → bot live mulai dengan ribuan pengalaman valid sejak hari pertama.
5. Trade nyata kemudian menyempurnakan memori (tidak menghapus hasil seeding; recency decay memberi bobot lebih ke data terbaru).

Peringatan: data parquet berakhir 1 Sep 2026 — seeding memakai window tersedia; data live mengisi sisanya.

---

## 12. File yang Disentuh

| File | Perubahan |
|---|---|
| `UI/src/lib/indicators.ts` | + `ao()`, `volumeFeatures()` |
| `UI/src/lib/patterns.ts` | BARU — deteksi ~20 pola |
| `UI/src/app/api/are/decision/route.ts` | bangun fingerprint, query memori, soft gate, field `fingerprint` + `memory` di respons |
| `are/bot.py` | simpan fingerprint saat entri; tulis outcome saat close; update bucket |
| `are/learning.py` | BARU — bucket, query, decay, rebuild, laporan |
| `scripts/seed_memory.py` | BARU — replay backtest → seed memori |
| `scripts/report_memory.py` | BARU — laporan kondisi terbaik/terburuk |
| `data/learning/` | BARU — artefak runtime (untracked) |
| `UI/src/app/page.tsx` | panel ringkas memori (fase 2) |

---

## 13. Fase Implementasi (Milestone)

**Fase 1 — Inti capture & memori**
- [ ] M1: `ao()` + `volumeFeatures()` + `patterns.ts` (20 pola) + unit test masing-masing
- [ ] M2: fingerprint di engine (field `fingerprint` di respons decision)
- [ ] M3: `are/learning.py` (JSONL append, bucket, query, rebuild) + unit test
- [ ] M4: bot.py capture entri + outcome close + update bucket
- [ ] M5: `scripts/seed_memory.py` — seeding 2 tahun backtest
- [ ] M6: soft gate di engine (demote WAIT + kategori `memory`) + verifikasi backtest

**Fase 2 — Penguatan**
- [ ] Hard gate (blokir penuh) setelah backtest membuktikan manfaat
- [ ] Panel UI memori (ringkasan bucket terbaik/terburuk)
- [ ] Decay recency aktif penuh + laporan berkala `report_memory.py`
- [ ] Estimasi arah 100–200 poin (distribusi probabilitas + sampel) di reasoning

---

## 14. Rencana Verifikasi (Gate Rilis)

Setiap milestone wajib lolos sebelum lanjut:

1. **Unit test** (tanpa MT5): `ao()`, `volumeFeatures()`, tiap deteksi pola (kasus sintetis), bucket add/query/rebuild, decay.
2. **Test suite existing**: `tests/test_decision_engine_behavior.py` tetap hijau (95/95) — fingerprint/gate tidak boleh merusak decision path.
3. **Backtest sebagai gate rilis**: jalankan backtest 2 tahun TIGA varian —
   - A: tanpa memori (baseline),
   - B: dengan soft gate memori,
   - C: dengan hard gate.
   Syarat rilis: P&L(B) > P&L(A) **dan** P&L(C) ≥ P&L(B) (atau perbedaan wajar < 5%) → baru gate boleh dinaikkan ke fase 2. Hasil dicatat di dokumen ini sebagai lampiran.
4. **Sanity live**: setelah Fase 1 aktif, amati 3–5 hari — tidak ada entri yang diblokir tanpa alasan jelas di reasoning; telemetri `memory` tercatat; panel tidak error.

---

## 15. Risiko & Batasan (jujur)

- **Bukan prediksi pasti** — probabilitas bersyarat; sampel kecil = tidak dipercaya (min 10).
- **Overfitting** dicegah: bucket kasar, ambang sampel, validasi backtest.
- **Non-stasioner** — recency decay + evaluasi berkala; re-seed hanya jika pasar berubah rezim drastis.
- **Data M1 lokal** berakhir 1 Sep 2026 — seeding terbatas pada window itu.
- **Memori per simbol** (XAUUSD) — jangan dicampur antar simbol.
- **Biaya** (spread/komisi) belum masuk bucket — keputusan akhir tetap memakai hitungan biaya engine yang ada.

---

*Lampiran: hasil backtest A/B/C akan dilampirkan di bawah ini setelah Fase 1-M6 selesai.*
