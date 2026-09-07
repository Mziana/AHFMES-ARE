# STRATEGY V2 — GATE ARCHITECTURE (DESIGN CONTRACT v2.2)

Status: **DESIGN ACCEPTED WITH REQUIRED CONTRACT HARDENING**
(v2.1 disetujui arahnya dengan 9 requirement wajib dari review tahap 2; semua terintegrasi di dokumen ini.
Bukan "FINAL" — status menjadi FINAL hanya setelah P0–P2 teraudit dan invariant test lolos.)

Basis: analisa 122 trade 7 Sep (MT5 riil) + riset multi-TF (dokumen user) + review desain 2 tahap
(14 koreksi + 9 requirement hardening) + audit infrastruktur AHFMES-ARE.

Prinsip induk:

```
LAMA:  Indicators → Score → BUY/SELL          (122 trade/hari, edge −5.5 poin)
BARU:  Data Validity → Regime → Permission → Location → Confirmation → Risk → Execution
```

Indikator bukan mesin prediksi — ia constraint terhadap kapan sistem boleh memutuskan.
Peringatan statistik: pada sampel 7 Sep, Gross Edge ≈ 0, Costs > 0, Net Edge < 0.
Tugas v2 membuktikan `Gross Edge > Costs + Statistical Noise` — bukan sekadar menurunkan frekuensi.
**WR adalah metrik deskriptif, BUKAN acceptance criterion** (koreksi review #9).

---

## 1. GATE STACK FINAL v2.2 — DUA LAPISAN TERPISAH (koreksi review #1)

### LAYER A — DATA/MARKET INTEGRITY (bukan bagian strategi)
```
GATE A — Data Integrity
```
Cek: stale tick, missing candle, duplicate timestamp, OHLC invalid (high<low dst),
spread invalid/negatif, abnormal price jump tanpa berita, clock inconsistency.
- Gagal → status **`DATA_INVALID`** — BUKAN `NO_TRADE`.
- Statistik Layer A TIDAK boleh tercampur statistik strategi: 500 evaluasi terblokir
  karena feed rusak bukan bukti strategi "selektif".
- Layer A = syarat masuk Layer B. Data invalid → evaluasi strategi TIDAK dijalankan.

### LAYER B — STRATEGY GATES (hanya berjalan atas data valid)
```
GATE B1 — News
GATE B2 — Session
GATE B3 — HTF Regime (M15, closed)
GATE B4 — Setup Location
GATE B5 — Closed-Candle Trigger (M5)
GATE B6 — Volume (profil-dependent)
GATE B7 — Risk & Execution
```

### Spesifikasi Layer B (perubahan dari v2.1 ditandai ▲)

**B1 News — FAIL-CLOSED dengan reason code TERPISAH (▲ koreksi review #2):**
```
NEWS_EVENT_ACTIVE       — event high-impact USD (NFP/CPI/FOMC), T−30m..T+30m
NEWS_PROVIDER_DOWN      — fetch gagal
NEWS_DATA_STALE         — data ada tapi > 4 jam
NEWS_CALENDAR_UNAVAILABLE — feed hidup tapi kalender kosong/tak ter-parse
```
Semua → `NO_NEW_ENTRY` (posisi existing tetap dikelola normal), tapi reason code
disimpan terpisah agar analisa performa bisa membedakan "strategi tidak menemukan edge"
dari "infrastruktur informasi bermasalah". `NEWS_DATA_POLICY=FAIL_CLOSED` default;
`DEGRADED` hanya di replay research eksplisit.

**B2 Session:** hypothesis registry `H-SESSION-01` (awal: 07:00–17:00 UTC) — bukan truth.
Konfigurasi berupa data (`session_windows`), diverifikasi di WFO multi-minggu.
Jam rugi 7 Sep TIDAK dipermanenkan (one-day regime fitting dilarang).

**B3 HTF Regime (M15 closed bar):** BUY-only (close>EMA20 & EMA9>EMA21 & RSI>50) /
SELL-only (cermin) / NO-TRADE. RSI threshold = registry `H-RSI-BIAS-01`, bukan angka sakral.

**B4 Setup Location — DETERMINISTIK + ANTI-LOOKAHEAD (▲ koreksi review #4, BUKTI KODE):**
`findSwingPoints` (indicators.ts:315–319) mengakses `highs[i+k]` — swing di bar i baru
terkonfirmasi setelah `lookback` bar MASA DEPAN. Di live aman (array hanya bar ≤ now);
di REPLAY ini LOOKAHEAD NYATA bila array berisi seluruh dataset. Kontrak wajib:
- Zona S/R pada waktu T dibangun HANYA dari bar ≤ T (evaluation-time slice).
- Definisi deterministik: swing = bar dengan high tertinggi / low terendah vs 5 bar
  kiri+kanan (confirmed); cluster distance = 0.75×ATR(M15); zona = level rata-rata
  cluster ± 0.5×ATR band; maks 5 zona per sisi; lookback window 200 bar M15.
- SCALP: harga dekat zona searah (≤ 0.5×ATR(M15)). MICRO: pullback EMA9/21 (M5),
  jarak ≤ 0.25×ATR(M5) — registry `H-LOC-01`/`H-LOC-02`.
- Invariant test wajib: `zone(T)` identik untuk input `bars[0..T]` dihitung ulang
  kapan pun (pure function), dan TIDAK identik bila input menyertakan bar > T.

**B5 Closed-Candle Trigger:** pola hanya dari CLOSED bars; timestamp sinyal = bar close
dari candle trigger; Morning/Evening Star membutuhkan 3 closed bars (i−2, i−1, i);
entry tetap next-bar-open. Pola searah mode B3. Contract pattern semantics masuk invariant
(koreksi review #5).

**B6 Volume — tick-activity proxy (▲ koreksi review #6):**
- MICRO wajib: `volume(candle sinyal) > H-VOL-01.ratio × mean(volume dari 5 bar SEBELUM
  candle sinyal)` — candle sinyal TIDAK ikut baseline; guard: zero-volume baseline →
  FAIL (bukan pass); bar volume missing → FAIL (bukan pass); hanya XAUUSD SCALP yang OFF.
- Bahasa desain: "tick-activity proxy", BUKAN "institutional volume".
- Ratio 1.2 = hipotesis registry `H-VOL-01`, grid-nya dihitung di trial accounting.

**B7 Risk & Execution:**
- SL/TP: SCALP 1.5/1.5×ATR(M5); MICRO 1.25/1.5×ATR(M5).
- min_stop = max(SL hitung, 3×spread + stops_level broker + 10); max_stop cap per profil
  (SCALP 400 / MICRO 250 poin); ATR×mult > cap → SKIP (bukan clamp diam-diam).
- Lot = risk% × balance ÷ SL poin (sizing konstan-dolar, cap profil tetap).
- Entry semantics (INVARIANT): sinyal @ bar close T; eksekusi paling awal = open bar T+1;
  backtest wajib `signal_timing='next_bar_open'`; dilarang menghitung PnL dari close bar sinyal.
- maxTradesPerDay = RISK CAP (SCALP 6 / MICRO 20); **TIDAK ADA KPI FREKUENSI** —
  0 trade adalah outcome valid (▲ diperkuat review: bot tidak boleh mengejar kuota).
- Cooldown: SCALP 30m / MICRO 5m — juga risk cap.

---

## 2. DECISION LOG — first veto + FULL DIAGNOSTIC (▲ koreksi review #2)

Operational flow berhenti di veto pertama; **diagnostic engine mengevaluasi SEMUA gate
secara pure/offline** untuk riset. Satu evaluasi = satu record JSONL:

```json
{
  "ts": 1788799380, "profile": "micro|scalp",
  "engine_version": "...", "config_hash": "...",
  "layer_a": "VALID|DATA_INVALID:<detail>",
  "gate_results": {              // FULL DIAGNOSTIC — semua gate dinilai
    "b1_news":  "PASS|NEWS_EVENT_ACTIVE|NEWS_PROVIDER_DOWN|NEWS_DATA_STALE|NEWS_CALENDAR_UNAVAILABLE",
    "b2_session": "PASS|FAIL:outside",
    "b3_regime":  "PASS:BUY_ONLY|PASS:SELL_ONLY|FAIL:NO_TRADE",
    "b4_location":"PASS:<ref>|FAIL:far|DISABLED",
    "b5_trigger": "PASS:<pattern>|FAIL:none|FAIL:forming_bar",
    "b6_volume":  "PASS|FAIL:ratio|FAIL:baseline_invalid|DISABLED",
    "b7_risk":    "PASS|FAIL:cap|FAIL:cooldown|FAIL:stop_bounds"
  },
  "first_veto_reason": "B1:NEWS_EVENT_ACTIVE",   // OPERATIONAL DECISION
  "bias": "BUY_ONLY|SELL_ONLY|NO_TRADE",
  "setup": {"kind":"sr_zone|ema_pullback","ref":"...","distance_atr":0.0},
  "trigger": {"pattern":"...","bar_ts":0},
  "decision": "BUY|SELL|WAIT",
  "sl_points":0,"tp_points":0,"lot":0.0,
  "market_snapshot": {"spread":0,"atr":0,"vol_ratio":0,"rsi_m15":0,"rsi_m5":0}
}
```

---

## 3. HYPOTHESIS REGISTRY & FAMILY ACCOUNTING

Registry wajib (semua threshold = hipotesis, bukan truth):
`H-SESSION-01`, `H-RSI-BIAS-01`, `H-RSI-ENTRY-01` (zona pullback M5 40–55 awal),
`H-LOC-01` (SR distance), `H-LOC-02` (EMA pullback), `H-VOL-01` (ratio),
`H-ATR-01` (multiplier SL/TP), `H-Q1` (market quality bounds).

Family accounting: `SCALP_V2`, `MICRO_V2_BASE`, `MICRO_V2_VOL` — keluarga TERPISAH.
DSR `effective_trial_count` per keluarga mencakup SEMUA kombinasi yang diuji di keluarga
itu (grid + varian session/RSI/volume/ATR). Dilarang memilih terbaik antar keluarga lalu
menghitung DSR seolah satu hipotesis. Dilarang mining di luar registry.
Scalp vs micro tidak saling "berkompetisi" tanpa accounting.

---

## 4. COST MODEL SEJAK P0 (▲ koreksi review #7)

Replay P0–P2 SUDAH memakai cost model komponen — bukan satu angka statis:
spread at entry, spread at exit, commission (jika ada), slippage, execution delay.
Sumber spread historis: bila tick-spread per-bar tersedia → pakai; bila tidak →
fallback konstanta diberi label **`ESTIMATED_COST_MODEL`** di semua output —
tidak pernah disajikan sebagai market truth.

## 5. DUA HASIL REPLAY (▲ koreksi review #8)

- **Decision Replay**: berapa keputusan dihasilkan, distribusi gate results, distribusi
  rejection reasons, frekuensi vs sistem lama. TIDAK menghitung PnL.
- **Execution Replay**: keputusan → execution simulator (next-bar-open + cost model) →
  PnL / expectancy.
Tujuan pemisahan: kalau hasil buruk, kita bisa membedakan "gate salah memilih setup"
vs "setup bagus tapi execution/cost menghancurkan edge".

---

## 6. ARSITEKTUR ALIRAN (kontrak P0–P2)

```
            MARKET DATA
                 │
        DATA INTEGRITY GATE (Layer A)
                 │  VALID            DATA_INVALID → log & stop
                 ▼
           GATE ENGINE (Layer B, pure functions)
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
OPERATIONAL DECISION   FULL DIAGNOSTIC
(first_veto_reason)    (all_gate_results)
      └──────────┬──────────┘
                 ▼
           DECISION LOG (JSONL)
                 │
       ┌─────────┴─────────┐
       ▼                   ▼
DECISION REPLAY     EXECUTION SIMULATOR
(frequencies,             │
 rejection dist)          ▼
                     COST MODEL (labeled)
                          │
                   TRADE / NO TRADE
                          │
                  PERFORMANCE OUTPUT
```

---

## 7. PIPELINE P0–P8 (urutan final — scope P0–P2 diperjelas sesuai review)

| Phase | Isi | Catatan |
|---|---|---|
| **P0 Deterministic contracts** | Data validity contract, timestamp contract (closed-bar semantics), gate semantics (veto, reason codes), profile config (scalp/micro), hypothesis registry. MURNI DEFINISI + SCHEMA | tanpa MT5/DB/UI |
| **P1 Pure Gate Engine** | Layer A + Layer B sebagai fungsi murni + decision log JSONL + diagnostic full-evaluation | tanpa MT5/DB/UI/order |
| **P2 Replay 7 Sep** | Decision Replay + Execution Replay (dengan cost model berlabel). Tujuan: timing, gate behavior, rejection logging, frekuensi, cost behavior, **bukti no-lookahead** — BUKAN bukti profit | dataset 7 Sep |
| P3 Data qualification | multi-hari/bulan: gaps, duplikat, timezone, OHLC, spread, tick_volume, symbol spec | sebelum backtest serius |
| P4 Baseline + ablation | OLD-MICRO vs V2-MICRO vs V2-SCALP (data/cost/execution sama); ablation per gate; gate tanpa kontribusi expectancy = dibuang | |
| P5 Cost stress | spread ×1.25/×1.5/×2.0 + slippage + delay; edge harus bertahan ×1.5 | |
| P6 WFO + statistik | WFO purge/embargo, frozen params, PSR, DSR (momen nyata), CI, worst-fold, fold dispersion. OOS buruk → revisi HIPOTESIS (terdaftar), bukan tweak diam-diam | |
| P7 Shadow execution-gap | sinyal vs eksekusi nyata: expected vs actual entry/SL/spread | |
| P8 Demo kecil | 2 minggu lot minimum; safety stack (equity breaker, kill switch, reset harian) sudah terpasang | |

### Invariant tests WAJIB (acceptance P0–P2)
1. **No-lookahead system-wide**: engine tidak dapat membaca candle > T (bukti kebutuhan: `findSwingPoints` mengonfirmasi swing dengan bar masa depan — di replay wajib evaluation-time slicing).
2. Closed-bar semantics: tidak ada keputusan dari forming bar.
3. Execution ≥ T+1 open; tak pernah lebih awal.
4. Replay determinism: input+config sama → decision log identik bit-per-bit, diulang.
5. Reason codes news terpisah (4 kode).
6. Layer A ≠ Layer B statistik (DATA_INVALID tidak masuk distribusi rejection strategi).
7. Volume baseline guard (exclude-self, zero-volume, missing-data = FAIL).
8. Diagnostic full-evaluation tidak mengubah operational decision.

---

## 8. YANG TIDAK MASUK BASELINE V2 (tetap)
SMT-lite DXY/USDJPY (fase eksperimen terpisah), multi-instrument, perubahan jalur eksekusi live.
Target WR per profil DIHAPUS sebagai acceptance — diganti expectancy-after-cost + CI +
sample size + max drawdown + loss streak + OOS robustness (koreksi review #9).

## 9. STATUS & LANGKAH BERIKUTNYA
- v2.2 = kontrak implementasi yang disepakati dua reviewer (status: ACCEPTED WITH REQUIRED
  CONTRACT HARDENING; menjadi FINAL setelah P0–P2 teraudit + invariant lolos).
- Mandat berikutnya: **"GATE ENGINE & DETERMINISTIC REPLAY (Strategy v2 P0–P2)"** — scope persis
  P0–P2 di atas, tanpa menyentuh live engine, tanpa WFO.
- Keputusan live (start bot) tetap milik user.
