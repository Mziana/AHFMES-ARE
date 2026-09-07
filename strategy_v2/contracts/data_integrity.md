# DATA INTEGRITY — LAYER A

Layer A adalah syarat masuk Layer B: bila gagal → status `DATA_INVALID:<reason>`,
evaluasi strategi **TIDAK dijalankan** untuk bar tersebut. Statistik Layer A
TIDAK boleh dicampur statistik strategi (tiga truth terpisah, PAGAR 3).

## Aturan DATA_INVALID (gagal → label eksplisit)

| Reason | Aturan |
|---|---|
| `DATA_INVALID:stale` | T - bar_terakhir_close > max_staleness (default 3× bar_seconds) |
| `DATA_INVALID:missing_bar` | gap antar bar M5 berurutan != bar_seconds (broker lunch/holiday ≠ dianggap normal) |
| `DATA_INVALID:duplicate_ts` | dua bar dengan open time sama |
| `DATA_INVALID:ohlc` | high < max(open,close) atau low > min(open,close) atau harga <= 0 |
| `DATA_INVALID:nan` | NaN/None pada OHLCV |
| `DATA_INVALID:volume_missing` | volume (tick-activity proxy) missing/negatif pada bar M5 |
| `DATA_INVALID:spread_extreme` | spread <= 0 atau > spread_cap_poin (dari profil) bila spread tersedia |

## Catatan

- Layer A dievaluasi **per evaluation time T** atas `bars_until_T`.
- `DATA_INVALID` TIDAK masuk distribusi rejection strategi (Layer B) —
  dihitung terpisah dalam funnel completeness (PAGAR 6).
- DATA_VALID → Layer B dijalankan penuh.
