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
| Kalender | ForexFactory `ff_calendar_thisweek.json` → artifact arsip `data/research/calendar/calendar_d306217f.json` (81 event, 22 pada 7 Sep; `information_available_at` = 2026-09-07T18:59:42Z, hash masuk config_hash) |
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
veto B1 (news STALE)       : 222   (provenance: snapshot 18:59Z > window 00:00–18:25Z)
final_signals              :   0
executed_trades            :   0
rejected_executions        :   0
gross / costs / net        : 0.0 / 0.0 / 0.0 USD
distinct gate states       : 102
```

Verifikasi aritmetika: 222 = **222** = layer_b_evaluated →
**ke mana semua kandidat trade hilang terjawab penuh** (0 sinyal final).
Catatan: B1 memveto SEMUA bar karena snapshot kalender di-fetch SETELAH window
evaluasi — look-ahead guard (P0-01) bekerja jujur; B2–B7 tetap dievaluasi
full-diagnostic di `all_gate_results` (distinct gate states 102).

## 4. Funnel — SCALP_V2

```
evaluation_opportunities   : 222
DATA_INVALID               :   0
veto B1 (news STALE)       : 222   (provenance: snapshot 18:59Z > window 00:00–18:25Z)
final_signals              :   0
executed_trades            :   0
```

Verifikasi: 222 = **222**. B1 memveto semua bar (provenance fail-closed);
B2–B7 full-diagnostic tetap di `all_gate_results`.

## 5. Gate behavior penting

- **B1 News**: `NEWS_DATA_STALE` 222/222 — snapshot kalender di-fetch
  2026-09-07T18:59:42Z, SETELAH window evaluasi (00:00–18:25Z) → look-ahead
  guard (P0-01) menolak sebagai informasi yang belum tersedia pada T. Klaim
  lama "PASS 222/222" (heuristic `max(event.ts)`) adalah artefak bug
  provenance — sekarang fail-closed jujur. Reason codes 4 arah terpisah
  teruji di invariant suite (test_inv5).
- **B3 Regime**: SELL_ONLY 137 / BUY_ONLY 58 / NO_TRADE 27 — hari turun
  (XAUUSD 4412 → turun), bias mengikuti M15 closed bar, tanpa lookahead.
- **B4 Location**: veto dominan (62 MICRO / 75 SCALP) — zona S/R anti-lookahead
  & pullback EMA jarang tepat pada bar mana pun. Ini sesuai desain:
  "indikator bukan mesin prediksi".
- **B6 Volume**: 11 veto `FAIL:ratio` (MICRO) — baseline exclude-self terjaga.
- **0 trade adalah outcome valid** — TIDAK ADA KPI FREKUENSI (desain §B7).
- **Revisi keputusan owner (2026-09-08)**: batasan `max_trades_per_day`
  (SCALP 6 / MICRO 20) **dihapus** dari B7/execution replay/schema — tidak
  ada cap frekuensi harian. Kontrol risiko tetap: cooldown, stop bounds
  (SKIP), sizing konstan-dolar. Per Pagar 1 ini = config_hash BARU
  (micro `7cd4cc05…`, scalp `d656358e…`) = experiment identity baru;
  funnel di report ini dijalankan ulang dan angkanya identik (0 sinyal
  baik dengan maupun tanpa cap — B7 cap tidak pernah tercapai pada
  dataset 7 Sep).
- **Revisi audit (2026-09-08)**: P0-01..P1-03 fix — provenance kalender
  (look-ahead guard), calendar hash in config_hash (identity baru:
  micro `c732ade7…`, scalp `e149fc0d…`), fail-closed cost model,
  Layer A M15 (gap break sesi ≥ 1h diizinkan), schema validation.
  Funnel di atas = identity baru dengan provenance jujur.

## 6. Perbandingan vs baseline lama (122 trade, −$42.02, 7 Sep)

| | Baseline lama | V2 MICRO | V2 SCALP |
|---|---|---|---|
| Trade | 122 | 0 | 0 |
| Evaluasi | — | 222 | 222 |
| Veto terbanyak | — | B1 news STALE (222) | B1 news STALE (222) |
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
4. Kalender FF adalah snapshot minggu ini, di-fetch 18:59Z 7 Sep — SETELAH
   window evaluasi → B1 fail-closed `NEWS_DATA_STALE` untuk seluruh bar
   (look-ahead guard P0-01). Untuk replay multi-hari, arsip kalender perlu
   di-fetch SEBELUM window (provenance eksplisit per artifact).
5. M15 gap 13 bar (weekend) di warmup — tidak mempengaruhi evaluasi 7 Sep.

## 10. Keputusan yang bisa dijalankan

1. **Lanjut P3** (data qualification multi-hari/bulan) — pipeline sudah siap,
   dataset 1 hari tidak cukup untuk hipotesis apapun.
2. **B4 location adalah gate paling membatasi setelah session** — kandidat
   ablation pertama di P4.
3. **Cost model perlu spread historis** sebelum P5 (cost stress) bermakna.
4. Jangan men-tune parameter berdasarkan 1 hari ini — mining di luar registry
   dilarang (kontrak §3).
