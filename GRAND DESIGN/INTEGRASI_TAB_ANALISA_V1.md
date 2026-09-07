# DESAIN v1 — Integrasi Tab Analisa ke Bot (Micro & Scalping)

Status: **DESAIN (belum implementasi)**
Latar: tab ANALISA (TECHNICAL ANALYSIS) menampilkan sinyal kaya (13 indikator + pola candle + volume + divergensi, MASTER SIGNAL BUY 75-88%, semua TF BUY), TETAPI bot micro/scalp memakai mesin decision yang berbeda dan lebih sederhana (hanya RSI + EMA9/21 + zone SR) — hasilnya sering bertolak belakang (tab bilang BUY 88%, bot bilang SELL/WAIT). Dokumen ini mendesain ulang: **arah entri bot berasal dari mesin analisa tab; bot hanya bertugas mencari posisi/timing entri**.

---

## 1. Akar Masalah (terbukti dari kode & data live)

| | Mesin analisa tab (`/api/are/tradingview`) | Mesin decision bot (`/api/are/decision`) |
|---|---|---|
| Indikator | 17-21 per TF: RSI, MACD, STOCH, BB, ADX, CCI, WR, MFI, ST, ICH, VWAP, pola candle, price action, volume, divergensi | RSI + EMA9/21 + zone SR + volume surge saja |
| Sinyal M5/M15 (live) | M5 BUY 51%, M15 BUY 66%, master BUY 75% | M5 BUY 55%, M15 SELL 71% (sering kontradiksi) |
| Latensi | ~0.1 detik (terukur 99 ms) | ~0.2 detik |

Fakta: `lib/signals.ts` SUDAH berisi `detectCandlePatterns`, `detectPriceAction`, `detectVolumeSignals`, `detectDivergences`, `applyMTFConfirmation`, `genConclusion` — mesin tab sudah lengkap; bot tidak memakainya.

---

## 2. Arsitektur Baru

```
┌─ lib/analysis.ts (BARU — hasil ekstraksi dari tradingview route) ─┐
│ analyzeMarket(symbol, timeframes[]) →                              │
│   { masterSignal, masterConfidence, buyCount, sellCount,           │
│     perTf: { M1:{conclusion, indicators, patterns, volume}, ... }, │
│     newsSignal }                                                   │
└───────────────┬───────────────────────────────┬────────────────────┘
                ▼                               ▼
   /api/are/tradingview               /api/are/decision (v2)
   (tab ANA — tampilan sama)          (bot micro & scalp)
                                      │
        1. ARAH = analyzeMarket (master + per-TF conclusion)
        2. TIMING/EKSEKUSI = mechanics lama (sesi, SL/TP, lot,
           cooldown, memory gate)
        3. PENCATATAN = taSnapshot → fingerprint → memori
```

Prinsip: **satu mesin analisa, dua konsumen**. Bot tidak lagi menghitung arah sendiri dengan skor sederhana — ia MEMBACA arah dari mesin yang sama dengan tab analisa.

---

## 3. Decision Engine v2 — alur per tick (micro & scalp)

1. Panggil `analyzeMarket(symbol, ['M1','M5','M15','H4','D1'])` (micro & scalp sama: entry M5/M15, timing M1, konteks H4/D1).
2. **Gate arah TA** (parameter per style, default sama untuk micro & scalp):
   - `taMaster` = masterSignal (bobot 2); `taM5`, `taM15`, `taM1` = conclusion per TF (bobot 1).
   - `taScore = (master==BUY?2:master==SELL?-2:0) + (M5 searah?1:-1) + (M15 searah?1:-1) + (M1 searah?1:0)`.
   - **Syarat BUY**: `taScore >= 3`; **SELL**: `taScore <= -3`; selain itu → `WAIT` dengan alasan `"TA: master BUY 75% tapi skor arah X/7 — belum cukup searah"`.
   - Ini menggantikan gate MTF lama (M5+M15 skor sederhana). Tidak ada lagi "M15 SELL 71%" dari mesin miskin.
3. **Timing halus (opsional, tambah skor)**: pola candle kuat di M5 (`detectCandlePatterns` → strength) searah menambah +1; volume surge searah +0.5 (sudah ada di lib).
4. **Mechanics tetap**: `dataFresh`, sesi, spread cost, SL/TP (micro tetap 150; scalp adaptif max(150,2xATR)), lot sizing, cooldown bot, memory gate (lihat LEARNING_MEMORI_V1).
5. **Respons v2** menambahkan field: `ta` (ringkasan master + per-TF) dan `taSnapshot` (lengkap untuk pencatatan).

Contoh alasan baru di panel: `"TA: master BUY 75% — M1 88 · M5 51 · M15 66 — skor 4/7"`.

---

## 4. Pencatatan (fingerprint → memori)

Sesuai permintaan "dijadikan pencatatan": setiap keputusan (dan entri) merekam **taSnapshot**:

```jsonc
"taSnapshot": {
  "master": { "signal": "BUY", "confidence": 75 },
  "perTf": {
    "M1":  { "signal": "BUY", "confidence": 88, "patterns": ["engulfing_bull"], "volume_surge": true },
    "M5":  { "signal": "BUY", "confidence": 51, "patterns": [] },
    "M15": { "signal": "BUY", "confidence": 66, "patterns": [] },
    "H4":  { "signal": "NEUTRAL", "confidence": 50 },
    "D1":  { "signal": "NEUTRAL", "confidence": 50 }
  },
  "taScore": 4
}
```

- Fingerprint LEARNING_MEMORI_V1 diperbarui: dimensi bucket utama menjadi `taMaster` + `pattern_m5` + `rsi/atr band` + `vol_surge` (arah dari TA, bukan skor lama).
- `bot.py` menyimpan taSnapshot saat entri → memori; outcome ditulis saat close (loop belajar tetap seperti desain memori).

---

## 5. Perubahan File

| File | Perubahan |
|---|---|
| `UI/src/lib/analysis.ts` | BARU — `analyzeMarket()` (ekstraksi logika dari tradingview route) |
| `UI/src/app/api/are/tradingview/route.ts` | refactor: panggil `analyzeMarket()` (output tidak berubah) |
| `UI/src/app/api/are/decision/route.ts` | v2: gate arah TA + taSnapshot + alasan baru; buang gate MTF sederhana |
| `UI/src/app/page.tsx` | tampilkan alasan TA di panel CHAMPION |
| `are/bot.py` | simpan taSnapshot saat entri (memori) |
| `GRAND DESIGN/LEARNING_MEMORI_V1.md` | bucket arah diganti berbasis TA |

---

## 6. Verifikasi & Gate Rilis

1. **Unit/sanity**: `analyzeMarket()` mengembalikan struktur yang sama dengan respons tradingview sekarang (diff field); decision v2 tidak merusak test suite existing (95/95) — asersi yang bergantung gate MTF lama disesuaikan ke gate TA.
2. **Live A/B**: catat 1 hari `taScore` vs `decision` lama (dari bot_logs) — ukur berapa % keputusan berubah arah dan ke arah mana; pastikan "tab bilang BUY → bot juga BUY" (tidak ada lagi kontradiksi).
3. **Backtest sebagai gate rilis** (fase 2, perlu replikasi lib/signals.ts di Python): varian A (mesin lama) vs B (arah TA) — syarat rilis P&L(B) ≥ P&L(A). Hasil dilampirkan di dokumen ini.
4. **Sanity live 3-5 hari**: alasan TA tampil di panel; tidak ada entri melawan master TA; telemetri rejections kategori baru `ta` tercatat; latensi decision tetap < 1 detik (cache analisa 2-3 detik per simbol bila perlu).

---

## 7. Keputusan yang Perlu Dikonfirmasi User

1. **Ambang skor**: `taScore >= 3` (dari max 7) sebagai syarat entry — atau lebih ketat (>=4)?
2. **M1 ikut arah?**: M1 hanya timing (opsional +1) — atau wajib searah?
3. **D1/H4**: dipakai sebagai konteks (bobot 0) atau wajib searah seperti bias H4 sekarang?
4. **Gaya lain (day/swing/position)**: ikut migrasi ke gate TA di fase berikutnya, atau micro & scalp dulu?
5. **Rejections kategori baru**: `ta` ditambahkan ke daftar kategori di bot.py/UI (seperti `rr`, `mtf`).

---

## 8. Catatan

- Latensi terukur `/api/are/tradingview` = 99 ms — aman dipanggil tiap tick 5 detik (2 bot = 2 req/5s).
- Mesin tab SUDAH punya deteksi pola candle (`detectCandlePatterns`) — tidak perlu buat pustaka pola baru; LEARNING_MEMORI_V1 yang menyebut `patterns.ts` baru disesuaikan: reuse `lib/signals.ts`.
- AO (5,13,5,Close) tetap ditambahkan sebagai fitur capture di fingerprint (belum ada di lib) — sesuai permintaan sebelumnya.

*Lampiran hasil backtest A/B diisi setelah verifikasi.*

---

## 9. Keputusan Terpilih (dikonfirmasi user, 2026-09-04)

1. **Ambang taScore = 3** (dari max 7) — master + minimal 1 TF searah cukup untuk entry.
2. **M1 = bonus saja** — M1 searah menambah skor (+1); M1 melawan TIDAK menghalangi entry.
3. **Ruang lingkup: micro & scalp dulu** — day/swing/position menyusul setelah terbukti (backtest + live).
4. Kategori rejections baru: `ta` (sesuai desain Bagian 7 no.5, default disetujui).
5. D1/H4 sebagai konteks (bobot 0) — tidak wajib searah pada fase ini.

**Status: DESAIN FINAL — menunggu konfirmasi eksekusi Fase Implementasi.**
