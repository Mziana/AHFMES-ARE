# GATE SEMANTICS — LAYER B (7 GATE, VETO BUKAN SKOR)

Layer B hanya berjalan atas data `DATA_VALID`. Setiap gate mengembalikan
`PASS:...` atau `FAIL:...`/reason eksplisit. Operational flow berhenti di
veto pertama (`first_veto_reason`); diagnostic engine (`evaluate_all`)
menilai SEMUA gate secara pure — keduanya dicatat terpisah (§2 desain).

## B1 News (FAIL-CLOSED, 4 reason code terpisah)

| Reason | Makna |
|---|---|
| `PASS` | tidak ada event high-impact USD dalam window T−30m..T+30m |
| `NEWS_EVENT_ACTIVE` | event high-impact (NFP/CPI/FOMC dst.) dalam window |
| `NEWS_PROVIDER_DOWN` | provider fetch gagal (policy FAIL_CLOSED → veto) |
| `NEWS_DATA_STALE` | data kalender ada tapi usia > 4 jam |
| `NEWS_CALENDAR_UNAVAILABLE` | feed hidup tapi kalender kosong/tak ter-parse |

Semua non-PASS → `NO_NEW_ENTRY` (posisi existing tetap dikelola).
`NEWS_DATA_POLICY=FAIL_CLOSED` default; `DEGRADED` hanya di replay research
eksplisit (konfigurasi, bukan default).

## B2 Session

- PASS jika UTC hour ∈ `session_windows` (data konfigurasi, bukan truth).
- FAIL → `FAIL:outside`. Registry `H-SESSION-01` (awal 07:00–17:00 UTC).

## B3 HTF Regime (M15 CLOSED)

- BUY_ONLY: close>EMA20 & EMA9>EMA21 & RSI>50 (RSI threshold = `H-RSI-BIAS-01`).
- SELL_ONLY: cermin (close<EMA20 & EMA9<EMA21 & RSI<50).
- Else `FAIL:NO_TRADE`.
- Indikator dihitung dari M15 bars ≤ T saja (slicing, PAGAR 2).

## B4 Setup Location (anti-lookahead)

- SCALP: harga dekat zona S/R searah — jarak ≤ 0.5×ATR(M15) (`H-LOC-01`).
  Zona dibangun oleh `strategy_v2/zones.py` dari M15 bars ≤ T (deterministik;
  DILARANG memanggil `getSupportResistanceZones` dari indicators.ts).
- MICRO: pullback EMA9/21 (M5), jarak ≤ 0.25×ATR(M5) (`H-LOC-02`).
- FAIL → `FAIL:far`; gate bisa `DISABLED` via profil (volume gate pattern).

## B5 Closed-Candle Trigger (M5)

- Pola hanya dari CLOSED bars. Sinyal @ bar close T; entry = open bar T+1.
- Morning/Evening Star = 3 closed bars (i−2, i−1, i).
- Pola harus searah mode B3 (BUY_ONLY → pattern bullish; SELL_ONLY → bearish).
- Reason: `PASS:<pattern>` | `FAIL:none` | `FAIL:forming_bar`.

## B6 Volume — tick-activity proxy (profil-dependent)

- MICRO wajib ON: `volume(candle sinyal) > ratio × mean(volume 5 bar SEBELUM
  candle sinyal)` — candle sinyal tidak ikut baseline (exclude-self).
- Zero-volume baseline / volume missing → `FAIL:baseline_invalid` (BUKAN PASS).
- SCALP: OFF → `DISABLED`. Ratio = registry `H-VOL-01` (awal 1.2).

## B7 Risk & Execution

- SL/TP multiplier ATR(M5): SCALP 1.5/1.5; MICRO 1.25/1.5 (`H-ATR-01`).
- `min_stop_poin = max(SL hitung, 3×spread_poin + stops_level + 10)`.
- Cap stop per profil: SCALP 400 / MICRO 250 poin. ATR×mult > cap →
  `FAIL:stop_bounds` (SKIP eksplisit, bukan clamp diam-diam).
- max_trades_per_day = RISK CAP (SCALP 6 / MICRO 20) → `FAIL:cap`.
- Cooldown (SCALP 30m / MICRO 5m) → `FAIL:cooldown`.
- PASS → `PASS`.

## Urutan veto (first_veto)

B1 → B2 → B3 → B4 → B5 → B6 → B7. Operational decision = first_veto_reason
atau PASS semua → decision BUY/SELL sesuai bias; tanpa sinyal → WAIT.
