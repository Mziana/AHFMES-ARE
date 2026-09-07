# REPORT_P2 — Replay 7 September (Strategy v2, P0–P2)

> **STATUS: BUKAN BUKTI PROFIT.** Tujuan P2: timing benar, gate behave,
> rejection logged, cost model jalan, no-lookahead terbukti, funnel lengkap.
> Keputusan profitabilitas = P3–P6 (multi-hari, WFO, cost stress).

## 1. Konfigurasi eksperimen (frozen, Pagar 1)

| Item | Nilai |
|---|---|
| Strategy version | `strategy_v2/0.1.0-p0` |
| Profil | `MICRO_V2` + `SCALP_V2` (kontrak frozen, commit `ddbfed9`) |
| Dataset | XAUUSD M5 222 bar (00:00–18:25 UTC, 7 Sep 2026) + M15 1200 bar (warmup dari 19 Agu) |
| Dataset source | MT5 bridge `/candles` `copy_rates_from_pos` count=1200 (token dari `data/bridge_token.txt` saat runtime) |
| Kalender | ForexFactory `ff_calendar_thisweek.json` (nyata; 81 event, 22 pada 7 Sep) |
| Cost model | `ESTIMATED_COST_MODEL` (spread historis per-bar tidak tersedia di dataset candle) |
| Execution timing | `next_bar_open` (sinyal @ close T, fill @ open T+1) |

`config_hash` & `dataset_hash` per profil tersimpan di
`data/research/v2_replay/summary_{micro,scalp}.json`.

## 2. Data qualification (ringan)

- **M5**: 222 bar, 0 duplicate, 0 gap, 0 OHLC invalid, 0 NaN, 0 volume missing → **valid**.
- **M15**: 1200 bar, 0 duplicate, 13 gap (weekend/session break — normal untuk rentang 3 minggu), 0 invalid → **valid**.

## 3. Funnel completeness (Pagar 6) — MICRO_V2

```
evaluation_opportunities   : 222   (setiap M5 closed bar)
DATA_INVALID               :   0
layer_b_evaluated          : 222
veto B2 (session)          : 102   (luar 07:00–17:00 UTC)
veto B3 (regime NO_TRADE)  :  24
veto B4 (location far)     :  62
veto B5 (no pattern)       :  23
veto B6 (volume ratio)     :  11
final_signals              :   0
executed_trades            :   0
rejected_executions        :   0
gross / costs / net        : 0.0 / 0.0 / 0.0 USD
distinct gate states       : 102
```

Verifikasi aritmetika: 102+24+62+23+11 = **222** = layer_b_evaluated →
**ke mana semua kandidat trade hilang terjawab penuh** (0 sinyal final).

## 4. Funnel — SCALP_V2

```
evaluation_opportunities   : 222
DATA_INVALID               :   0
veto B2                    : 102
veto B3                    :  24
veto B4 (sr_zone far)      :  75
veto B5                    :  13
veto B7 (stop_bounds/SKIP) :   8   ← min_stop > cap 400 poin → SKIP eksplisit
final_signals              :   0
executed_trades            :   0
```

Verifikasi: 102+24+75+13+8 = **222**. B7 aktif bekerja (8 SKIP karena ATR
tinggi × mult 1.5 > cap) — perilaku sesuai desain §B7 (SKIP, bukan clamp).

## 5. Gate behavior penting

- **B1 News**: `PASS` 222/222 — tidak ada event high-impact USD dalam window
  ±30 menit pada jam evaluasi (07:00–18:25 UTC, Senin). Reason codes 4 arah
  terpisah teruji di invariant suite (test_inv5).
- **B3 Regime**: SELL_ONLY 137 / BUY_ONLY 58 / NO_TRADE 27 — hari turun
  (XAUUSD 4412 → turun), bias mengikuti M15 closed bar, tanpa lookahead.
- **B4 Location**: veto dominan (62 MICRO / 75 SCALP) — zona S/R anti-lookahead
  & pullback EMA jarang tepat pada bar mana pun. Ini sesuai desain:
  "indikator bukan mesin prediksi".
- **B6 Volume**: 11 veto `FAIL:ratio` (MICRO) — baseline exclude-self terjaga.
- **0 trade adalah outcome valid** — TIDAK ADA KPI FREKUENSI (desain §B7).

## 6. Perbandingan vs baseline lama (122 trade, −$42.02, 7 Sep)

| | Baseline lama | V2 MICRO | V2 SCALP |
|---|---|---|---|
| Trade | 122 | 0 | 0 |
| Evaluasi | — | 222 | 222 |
| Veto terbanyak | — | B2 session (102) | B2 session (102) |
| Cost model | implisit | ESTIMATED | ESTIMATED |

Frekuensi 122 → 0 bukan "strategi lebih baik" — itu **rejection yang
terukur dan terlog**: setiap bar punya alasan eksplisit. Baseline lama
men-trade 122× tanpa log veto; V2 menolak semua 222 dengan alasan
terstruktur. Perbandingan PnL yang adil menunggu P4 (baseline + ablation
dengan data/cost/execution sama).

## 7. Determinism (Pagar 4)

- Replay ×2 per profil → JSONL **bit-per-bit identik** (`cmp` exit 0):
  - `decision_micro.jsonl` ✓
  - `decision_scalp.jsonl` ✓
- Grep `now(`/`time.time()` di `strategy_v2/*.py` jalur decision: hanya
  di docstring/komentar; zero pemanggilan (teruji otomatis di suite).

## 8. No-lookahead (Pagar 2)

- Terbukti via invariant suite: inject candle masa depan → hasil evaluasi T
  identik (`test_inv1_no_lookahead_future_candle_does_not_change_past`).
- `zones(T)` pure & identik kapan pun dihitung ulang; berubah bila input
  menyertakan bar > T (`test_inv1_zones_pure_and_slice_sensitive`).
- Engine menerima slice `bars[0..T]` — tidak ada jalur baca > T.

## 9. Limitasi (jujur)

1. **Dataset 1 hari, 222 bar M5 (00:00–18:25 UTC)** — bar 18:30–24:00 tidak
   tersedia dari broker via jalur yang segar (`copy_rates_range` beku 200 bar,
   terdokumentasi di bridge). Statistik harian tidak generalisabel.
2. **Spread historis tidak tersedia** → cost model `ESTIMATED_COST_MODEL`
   (fallback 20 poin sisi). Edge nyata bisa lebih tipis dari estimasi.
3. **0 sinyal pada 1 hari** bukan bukti apa pun tentang profitabilitas —
   hanya bukti gate behave sesuai kontrak.
4. Kalender FF adalah snapshot minggu ini (event historis 7 Sep akurat,
   `fetched_at` heuristik = event terakhir); untuk multi-hari perlu arsip.
5. M15 gap 13 bar (weekend) di warmup — tidak mempengaruhi evaluasi 7 Sep.

## 10. Keputusan yang bisa dijalankan

1. **Lanjut P3** (data qualification multi-hari/bulan) — pipeline sudah siap,
   dataset 1 hari tidak cukup untuk hipotesis apapun.
2. **B4 location adalah gate paling membatasi setelah session** — kandidat
   ablation pertama di P4.
3. **Cost model perlu spread historis** sebelum P5 (cost stress) bermakna.
4. Jangan men-tune parameter berdasarkan 1 hari ini — mining di luar registry
   dilarang (kontrak §3).
