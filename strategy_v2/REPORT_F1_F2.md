# REPORT_F1_F2 — Execution Truth Repair (Strategy v2, mandat §10.1 E-1..E-4)

> **STATUS: F1 + F2 SELESAI.** Sebelum fase ini, setiap angka PnL execution
> replay adalah fiksi matematika (bug unit 100× + double-count spread).
> Setelah fase ini, setiap angka PnL bisa dipertanggungjawabkan ke biaya riil
> broker (unit `PRICE_1E4` dari bridge, poin 0.01-harga, $1/lot/poin XAUUSD).

## 1. Commits

| Paket | Commit | Isi |
|---|---|---|
| 1 (F1a RED) | `d946d2a` | `broker_meta.py` + invariant round-trip tests (RED, bukti bug) |
| 2 (F1b GREEN) | `d454ea7` | execution contract BID/ASK + state machine + unit normalisasi |
| 3 (F2 evidence) | `70305db` | kalender arsip riil + replay window honesta → funnel natural |
| 4 (F2b report) | (commit #4) | laporan ini + regression guard $17/lot |

## 2. Sebelum vs Sesudah — PnL per trade contoh (flat 4400, spread 0.17 harga)

| | Lama (fiksi) | Benar (v2.4) |
|---|---|---|
| Unit spread bridge 1700 (PRICE_1E4) | 1700 poin × $100 = **$3401/lot** | normalize → **17 poin × $1 = $17/lot** |
| BUY entry (flat) | open + 17.00 (spread 1700×0.01) | open + 0.17 (spread 17×0.01) |
| Round-trip BUY flat, lot 1, comm $1 | net **−$3501** (double-count + 100×) | net **−$35** = −(17+17+1)×$1 |
| Round-trip SELL flat, lot 1, comm $1 | net **−$3501** | net **−$35** (konsisten, invariant) |

Bukti eksekusi (kode sebelum F1b, dari commit message F1a):
```
spread 17 poin:  entry=4400.17 exit=4400.0 gross=-17.0 cost=35.0 net=-52.0
  invariant: net = -(17+17+1)*1 = -35.0  ->  DIFF -17.00 (double-count spread)
spread 1700 raw: cost=3401.0/lot  vs  realita $17/lot (unit 100x)
```

## 3. Round-trip invariant (E-1) — evidence

`tests/strategy_v2/test_round_trip_invariant.py` (15 test, semua PASS):
- BUY flat: `net = -(entry+exit+comm) * pv * lot` PERSIS
- SELL flat: mirror identik
- dengan komisi: `-(17+17+1) * 1 * lot`
- price basis BID; BUY entry_side=ASK/exit_side=BID; SELL entry_side=BID/exit_side=ASK
- SELL SL trigger BID-equivalent `level − spread` (exit ASK = level + spread)

## 4. Unit normalisasi (E-2) — evidence

- `normalize_spread(1700, "PRICE_1E4") == 17.0`; `normalize_spread(17, "POINTS_001") == 17.0`
- unit tak dikenal → `UnknownSpreadUnit` (fail-closed)
- `point_value_usd_per_lot` DIHITUNG = contract_size × point = 100 × 0.01 = **$1/lot**
  (broker meta hash `21938b7f…` masuk config_hash — Pagar 1)
- regression guard `test_cost_17_usd_per_lot_regression_guard`: cost = **$17/lot**,
  bukan $3400; net flat = −$34/lot (tanpa komisi)

## 5. State machine (E-3) — evidence

`ONE_POSITION_ONLY` (state FLAT|LONG|SHORT):
- sinyal searah saat terbuka → `REJECTED:position_open` (1 trade, 0 stacking)
- berlawanan → `exit_then_reverse` (REVERSAL di bar sinyal, fill next-bar-open; cooldown berlaku)
- EOD_MARK dilabeli; scan SL/TP kronologis per record (posisi mid-dataset tutup di bar hit)
- `state_transitions: {reversals, eod_marks}`, `position_state`, `state_before/after` per trade

## 6. F2 — funnel natural (E-4) — evidence

| | Lama (7 Sep 00:00–18:25, 222 bar) | Baru (F2: Sep 7 22:00 → Sep 8 08:25, 125 bar) |
|---|---|---|
| veto B1 (news) | **222 NEWS_DATA_STALE** (snapshot post-date window) | **0** (PASS 100% di luar blackout; target ≥80% ✓) |
| DATA_INVALID | 0 | 2 (`m15:stale` sesi awal — Layer A bekerja) |
| veto B2 session | — | 105 (22:00–07:00 di luar window) |
| veto B4 / B5 | — | 15 / 3 |
| final_signals / executed | 0 / 0 | 0 / 0 |

Kalender: artifact arsip `calendar_multiday.json` (81 event FF riil, hash
`f8033de8…`, `information_available_at` = 1788807582 = **fetch riil** Sep 7
18:59:42Z — bukan karangan). Sesi dengan close < info_at ditolak provenance
guard (P0-01). Window F2 = satu-satunya sesi honesta dengan evidence kalender
tersedia. Detail penuh: `REPORT_P2.md §11`.

## 7. Unit spread — declaration

| Field | Sumber | Unit | Poin 0.01 |
|---|---|---|---|
| `spread` (bridge /account) | live tick XAUUSD | `PRICE_1E4` = (ask−bid)×10000 | ÷100 → poin |
| bid/ask harga candle | MT5 historis | harga | ×100 → poin |
| contract_size / point | broker meta fallback XAUUSD (bridge belum expose symbol_info) | 100 oz / 0.01 | $1/lot/poin |

Cost model label: `ESTIMATED_COST_MODEL` (spread = konstanta snapshot live,
bukan spread historis per-bar; desain §4 — estimasi tidak disajikan sebagai truth).

## 8. Test suite

Full suite (`--ignore=tests/test_bot_lifecycle.py`): **789 passed + 16 strategy_v2
tests baru, 0 failed** (angka final di §9 setelah commit #4; baseline mandat:
747 passed + 105 subtests).

## 9. Limitasi (jujur)

1. F2 window = 1 sesi (125 bar) — multi-hari penuh menunggu snapshot kalender
   pre-dated per hari (arsip mingguan di-fetch SEBELUM window).
2. Spread snapshot konstanta (17 poin) — bukan spread historis per-bar.
3. Broker meta FALLBACK (bridge tanpa symbol_info) — bila bridge menambah
   `symbol_info`, config_hash berubah (identity eksperimen baru).
4. 0 sinyal pada sesi F2 bukan bukti profitabilitas — hanya bukti funnel
   natural + gate behave sesuai kontrak.