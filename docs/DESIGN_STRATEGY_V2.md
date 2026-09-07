# STRATEGY V2 — GATE ARCHITECTURE (DESIGN CONTRACT v2.1)

Status: **DESIGN — DISETUJUI UNTUK IMPLEMENTASI RESEARCH/BACKTEST, BELUM LIVE**
Basis: analisa 122 trade 7 Sep (MT5 riil) + riset multi-TF (dokumen user) + 14 koreksi review (sesi desain) + audit infrastruktur AHFMES-ARE.

Prinsip induk (perubahan paradigma):

```
LAMA:  Indicators → Score → BUY/SELL          (122 trade/hari, edge −5.5 poin)
BARU:  Regime → Permission → Location → Confirmation → Risk → Execution
```

Indikator bukan lagi mesin prediksi — ia adalah **constraint terhadap kapan sistem boleh memutuskan**.

Peringatan kejujuran statistik: pada sampel 7 Sep, **Gross Edge ≈ 0, Costs > 0, Net Edge < 0**.
Satu hari tidak cukup menyimpulkan sinyal netral. Tugas v2 membuktikan:

```
Gross Edge > Costs + Statistical Noise
```

Bukan sekadar mengurangi frekuensi.

---

## 1. GATE STACK FINAL (9 GATE — semua VETO, bukan skor)

```
GATE 0 — System & Data Integrity
GATE 1 — Market Quality (microstructure)
GATE 2 — News
GATE 3 — Session
GATE 4 — HTF Regime (M15)
GATE 5 — Setup Location
GATE 6 — Closed-Candle Trigger (M5)
GATE 7 — Volume (profil-dependent)
GATE 8 — Risk & Execution
```

Aturan global: **semua gate = veto**. Lolos semua → entry. Satu gagal → WAIT,
dengan `rejection_reason` eksplisit yang tercatat (lihat §4 — rejection adalah data ablation).

### GATE 0 — System & Data Integrity
- Bridge MT5 hidup & /health OK; MT5_CONNECTED true.
- Data M5 kontinu: gap antar bar ≤ 2.5× median interval (purifier sudah menandai market-closed; gate ini menolak bila data gap abnormal *saat entry evaluation*).
- Timestamp candle lolos sanity (offset epoch terkuantisasi, P2-17).
- engineVersion & config_hash terisi — keputusan tanpa provenance tidak valid.

### GATE 1 — Market Quality (baru — hasil review)
Veto bila kondisi microstructure buruk, threshold rolling (bukan hardcoded absolut):
- **Spread** > 1.5× median spread rolling-24h → reject.
- **Stale tick** > 30 detik → reject.
- **Tick gap abnormal**: pergerakan > 4× ATR(M5) dalam 1 bar tanpa berita → reject (mencurigakan).
- **ATR regime filter**: ATR(M5) di luar band [P10, P95] distribusi rolling-30 hari → reject (market tidak dalam regime normal; strategi tidak teruji di regime ekstrem).
- Definisi angka di atas adalah **hipotesis awal (H-Q1)**, masuk hypothesis registry dan diuji di WFO — bukan fakta.

### GATE 2 — News (kebijakan FAIL-CLOSED — koreksi review)
- `NEWS_DATA_POLICY = FAIL_CLOSED` (default paper/live):
  - Event high-impact USD (NFP/CPI/FOMC) → **NO NEW ENTRY** dari T−30m sampai T+30m.
  - **Kalender UNKNOWN / stale > 4 jam → NO NEW ENTRY.** Tidak ada degraded-to-trading.
  - Posisi existing tetap dikelola normal (trailing/close = risk-reducing).
- `DEGRADED` mode hanya untuk research/replay eksplisit, tidak pernah default live.
- Sumber: feed ForexFactory yang sudah di-fetch `news/route.ts`, ditambah parser field impact/waktu. Cache 24 jam; kegagalan parser → status UNKNOWN → fail-closed.

### GATE 3 — Session (HIPOTESIS, bukan fakta satu hari — koreksi review)
- Jam 7 Sep (05/10/12/15 rugi) **TIDAK dipermanenkan**. Itu one-day regime fitting.
- H-S1 (hipotesis awal): sesi likuid 07:00–17:00 UTC. Diverifikasi di WFO multi-minggu
  sebagai parameter keluarga hipotesis, bukan konstanta kebenaran.
- Konfigurasi session bersifat data (`session_windows: [...]`), sehingga varian sesi
  bisa diuji sebagai hipotesis terdaftar, bukan edit kode.

### GATE 4 — HTF Regime (M15, closed bar)
- BUY-only: close > EMA20 & EMA9 > EMA21 & RSI(14) > 50.
- SELL-only: cermin sempurna.
- Selain itu → NO-TRADE (regime ambigu = tidak ada edge yang diklaim).
- M15 bar juga wajib closed (semantik bar-closed berlaku semua TF).

### GATE 5 — Setup Location
- **SCALP (Varian 1)**: harga dekat zona S/R searah bias (jarak ≤ 0.5×ATR(M15))
  — `getSupportResistanceZones` sudah ada.
- **MICRO (Varian 2)**: pullback ke EMA9/EMA21 (M5), jarak ≤ 0.25×ATR(M5) dari EMA,
  dalam arah bias — continuation, bukan counter-trend.
- Dua setup **berbeda** → dua keluarga hipotesis terpisah (lihat §5).

### GATE 6 — Closed-Candle Trigger (M5, wajib CLOSED)
- Sinyal hanya dievaluasi pada **bar M5 yang baru saja TUTUP**; forming bar diabaikan total.
- Pola: Scalp = engulfing / pin bar / star (STRONG patterns). Micro = pin bar / engulfing ringan.
- Pola harus searah mode Gate 4. Ini jawaban langsung atas "entry saat candle sekilas berubah warna".

### GATE 7 — Volume (profil-dependent; HYPOTHESIS H-V1)
- MICRO wajib: volume candle sinyal > 1.2× rata-rata volume 5 candle sebelumnya.
- **1.2× adalah hipotesis awal** — diuji via WFO sebagai parameter keluarga
  (grid 1.0/1.1/1.2/1.3 — diperhitungkan di trial accounting). DILARANG parameter
  mining di luar registry.
- `tick_volume` = aktivitas tick broker, proxy — bukan volume pasar sebenarnya; kesimpulan
  hanya dari OOS.
- SCALP: gate volume OFF (beda keluarga hipotesis).

### GATE 8 — Risk & Execution
- **ATR adaptive + regime bounds** (koreksi review):
  - SCALP: SL = 1.5×ATR(M5), TP = 1.5×ATR. MICRO: SL = 1.25×ATR, TP = 1.5×ATR.
  - `min_stop` = max(SL hitung, 3×spread + stops_level broker + 10) — spread-aware floor (clamp bot P0-01-era sudah ada, diformalkan).
  - `max_stop` cap absolut per profil (SCALP 400 poin, MICRO 250 poin). ATR×multiplier > cap → **skip trade** (regime terlalu liar), bukan clamp diam-diam.
  - Lot = risk% × balance ÷ SL poin (sizing konstan-dolar; cap per profil tetap).
- **Entry semantics (kontrak formal — koreksi review #9)**:
  ```
  Sinyal dievaluasi pada bar close (T).
  Keputusan timestamp = T.
  Harga eksekusi paling awal = harga pasar tersedia setelah T (next bar open + latensi).
  Backtest WAJIB memakai execution_model.signal_timing='next_bar_open'
  (sudah ada di are/backtest.py — P0-2) agar backtest ≡ live.
  DILARANG menghitung PnL dari harga close bar sinyal.
  ```
- **maxTradesPerDay = RISK CAP, bukan target produksi** (koreksi review #8):
  SCALP cap 6, MICRO cap 20. 0 trade = hasil valid. Tidak ada mekanisme "kejar kuota".
- Cooldown antar entry: SCALP 30m, MICRO 5m — juga risk cap.

---

## 2. KONTRAK KEPUTUSAN (deterministic strategy contract — P1)

Setiap evaluasi (per bar M5 closed) menghasilkan satu record JSONL, trade ATAU rejection:

```json
{
  "ts": 1788799380,            // epoch bar close M5 yang dievaluasi
  "profile": "micro|scalp",
  "engine_version": "...",
  "config_hash": "...",        // fingerprint seluruh konfigurasi gate
  "gate_results": {
    "g0_data_integrity": "PASS|FAIL:<detail>",
    "g1_market_quality": "PASS|FAIL:spread|stale|gap|atr_regime",
    "g2_news":           "PASS|FAIL:blackout|fail_closed_unknown",
    "g3_session":        "PASS|FAIL:outside",
    "g4_regime":         "PASS:BUY_ONLY|PASS:SELL_ONLY|FAIL:NO_TRADE",
    "g5_location":       "PASS:<zone_ref>|FAIL:far",
    "g6_trigger":        "PASS:<pattern>|FAIL:none|FAIL:forming_bar",
    "g7_volume":         "PASS|FAIL:ratio|DISABLED",
    "g8_risk":           "PASS|FAIL:cap|cooldown|stop_bounds"
  },
  "bias": "BUY_ONLY|SELL_ONLY|NO_TRADE",
  "setup": {"kind": "sr_zone|ema_pullback", "ref": "...", "distance_atr": 0.0},
  "trigger": {"pattern": "...", "bar_ts": 0},
  "decision": "BUY|SELL|WAIT",
  "rejection_reason": "g4_regime:NO_TRADE",   // gate pertama yang veto
  "sl_points": 0, "tp_points": 0, "lot": 0.0,
  "market_snapshot": {"spread": 0, "atr": 0, "vol_ratio": 0, "rsi_m15": 0, "rsi_m5": 0}
}
```

Rejection adalah data: log JSONL ini menjadi dataset utama **ablation study** —
kita tahu persis gate mana yang memotong trade mana, tanpa menduga-duga.

---

## 3. HYPOTHESIS REGISTRY & MULTIPLE-TESTING ACCOUNTING (koreksi review #5, #11)

- Semua evaluasi backtest/WFO mendaftar ke `CumulativeTrialTracker` (wiring P3-20 sudah ada)
  dengan **label keluarga hipotesis** baru:
  - `SCALP_V2` (bias+SR+pattern, tanpa volume)
  - `MICRO_V2_BASE` (bias+pullback+pattern, tanpa volume)
  - `MICRO_V2_VOL` (base + volume filter)
  - varian session/ATR/volume-threshold = entri terpisah dalam keluarga masing-masing.
- DSR `effective_trial_count` per keluarga = **jumlah seluruh kombinasi yang diuji di
  keluarga itu** (grid + varian), bukan satu run. Tracker di-extend: field `family`.
- DILARANG: memilih hasil terbaik antar keluarga lalu menghitung DSR seolah satu hipotesis.
- DILARANG: grid-mining volume threshold di luar registry.

---

## 4. PIPELINE VALIDASI P0–P8 (diperketat — koreksi review #14)

| Phase | Isi | Kriteria lolos | Infra yang dipakai |
|---|---|---|---|
| **P0 Gate engine murni** | `UI/src/lib/gates.ts` (fungsi murni, profile-driven, feature-flag per gate). LIVE TIDAK DISINGGUNG | unit test per gate + determinism | — |
| **P1 Decision contract** | Schema §2 + JSONL logger + config_hash | schema test + hash stabil | — |
| **P2 Deterministic replay** | Replay 7 Sep (sanity) + replay determinism: input sama + config sama = decision log identik, diulang | 2 run identik bit-per-bit | data deals/candles 7 Sep |
| **P3 Data qualification** | Missing candles, duplikat, timezone, OHLC integrity, spread integrity, tick_volume, weekend gaps, symbol spec (contract size/digits/point) sebelum data masuk replay/WFO | quality report bersih | `DataPurifier` + dataset registry |
| **P4 Baseline + Ablation** | OLD-MICRO vs V2-MICRO vs V2-SCALP pada data sama; lalu ablation: bias → +location → +candle → +RSI-pullback → +volume. Gate yang tidak menambah expectancy = dibuang | tiap gate yang dipertahankan menambah expectancy OOS | replay engine + decision log |
| **P5 Cost stress** | Spread ×1.0 / ×1.25 / ×1.5 / ×2.0 + slippage + delay eksekusi | edge bertahan di ×1.5 | `INSTRUMENT_SPREADS` + `execution_model` (sudah ada) |
| **P6 WFO + statistik** | WFO purge/embargo, parameter frozen per fold, lalu PSR, DSR (momen nyata, P1-08), CI, **worst-fold & fold dispersion** (bukan hanya pooled) | pooled Sharpe ≥ 1.0, DSR p<0.05, worst-fold > 0 | `run_walk_forward_optimization` + `validation.py` |
| **P7 Shadow execution-gap** | Bandingkan sinyal vs eksekusi nyata: signal time, expected entry vs actual price, expected vs actual spread/SL — ukur backtest-live gap | gap ≤ 1×spread median | `shadow_ab` + log bot |
| **P8 Demo kecil** | Micro v2 lot minimum, 2 minggu | net positif, breaker tak menyala | bot + safety stack (breaker equity, kill switch, reset harian — sudah terpasang) |

Urutan bersifat menara: gagal di fase mana pun = berhenti, evaluasi, revisi hipotesis —
bukan lanjut sambil berharap.

---

## 5. YANG TIDAK MASUK BASELINE V2 (disepakati)
- SMT-lite DXY/USDJPY → fase eksperimen terpisah SETELAH baseline terbukti (satu perubahan per eksperimen).
- Multi-instrument (EURUSD dll) → setelah v2 terbukti di XAUUSD.
- Perubahan jalur eksekusi live (bridge/bot order path) → bukan lingkup v2; v2 hanya mengubah KEPUTUSAN.

---

## 6. STATUS & LANGKAH BERIKUTNYA
- Desain: FINAL v2.1 (dokumen ini = kontrak implementasi).
- Mandat implementasi berikutnya: **P0–P2 saja** (gate engine murni + contract + replay 7 Sep).
  P3–P8 = mandat berurutan setelah P0–P2 teraudit.
- Keputusan live (start bot) tetap milik user, di luar mandat engineering mana pun.
