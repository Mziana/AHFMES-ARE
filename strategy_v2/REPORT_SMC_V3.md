# REPORT — SMC/ICT v3 Replay Studi Offline (2026-09-11 malam)

## Ringkasan
| | |
|---|---|
| Engine | `strategy_v2/smc.py` (SMC/ICT v3 — kandidat pengganti MICRO) |
| Jendela | 39.2 hari, 3 Agu 11:39 → 11 Sep 17:09 UTC (39.999 bar M1) |
| Replay | `scripts/smc_v3_study.py` — parity jendela live (M1/M5 400 bar, M15 300, H4 250), cooldown 5m, 1 posisi, eksekusi close M1, first-touch SL/TP (SL-priority ambigu), EXPIRE >24h |
| Biaya | sel R1 Stage 1: base 17 pts, must 27.5 pts — label `ESTIMATED_COST_MODEL` |
| **Verdict** | **KILL DITUNDA oleh owner** — n=139 ≥ 30, expNet_must = **−44.49 pts/trade** << 0; TAPI audit kepatuhan menemukan exit desain §4 (partial 50%+BE) belum direplay → lihat `REPORT_SMC_V3_CHECKLIST.md` |

## Hasil (engine fixed — lihat temuan bug di bawah)
| metrik | nilai |
|---|---|
| sinyal TAKE | 139 (3.54/hari) dari 36.644 evaluasi |
| Win rate | 32.4% (44 TP / 94 SL / 1 EXPIRE) |
| breakeven-gross | 34.2% (RR rata-rata 1.92) |
| gross | **−16.99 pts/trade** |
| net base | −33.99 pts/trade |
| net must | **−44.49 pts/trade** |
| avg SL / TP | 382.3 / 721.0 pts |
| by dir | BUY n=69 WR 30.4% gross −3169 · SELL n=70 WR 34.3% gross **+807** |
| by sesi | london WR 45.5% (+1757) · ny_late +2012 (WR 29.4%) · asia −1982 · overlap **−4149** |

Funnel: rr_gate 21.723 (59%) · bias H4 netral 12.990 (35%) · posisi terbuka 2.866 ·
tanpa target likuiditas 870 · tanpa SL struktural 638 · skor threshold 284 · cooldown 89.

## Temuan bug (replay pertama) — diperbaiki SEBELUM hasil dipakai
1. **SL terbalik dari sweep stale** (13 trade "SL" dgn gross positif, RR palsu
   5.95): anchor sweep memakai `ext < (sl_base or 1e9)` yang selalu true saat
   `sl_base=None` → extrem sweep lama yang sudah kedodoran harga jadi SL di sisi
   SALAH (BUY dgn sl > entry). Fix: anchor sweep wajib di sisi yang benar dari
   harga sekarang + guard fail-closed terakhir + 2 test regresi
   (`test_engine_never_takes_with_inverted_sl`, `test_engine_sl_side_invariant_on_take`).
2. **Zona OB body-only** → tinggi zona 0 di bar marubozu (test displacement gagal).
   Fix: zona OB = range penuh H/L (konsisten rencana §4 "SL di luar POI" —
   di belakang extrem wick, bukan di tengah wilayah wick).

Sebelum fix: WR 38.1% dgn RR nominal 2.24 tapi gross −1.25 (inkonsisten = alarm);
setelah fix: WR 32.4% vs breakeven 34.2% — koheren dan jujur.

## Interpretasi
- Engine sangat selektif (3.5 sinyal/hari) tapi **edge bruto tidak ada** di window
  ini — pola berulang dgn MICRO v2: geometri jauh (SL median ~300+ pts) + biaya
  must 27.5 pts memakan semua edge; TP jauh (median 536 pts) jarang tersentuh
  karakter M1.
- Dekomposisi (n kecil — lead, bukan konfirmasi): SELL +5.8 pts/tr vs BUY −45.9;
  london satu-satunya sesi WR di atas breakeven.
- **Keputusan**: SMC v3 TIDAK dijadwalkan swap ke arm live; tanpa tweak angka
  (kontrak R1). Arah riset berikutnya (menunggu owner): partial-TP 50%+BE di
  simulator, biaya real per jam dari deal history, atau biarkan shadow D/E
  mengumpulkan n≥30 dulu. Arm live & shadow TIDAK disentuh sesi ini.

## Artefak
`scripts/smc_v3_study.py` · `data/research/smc_v3/smc_v3_replay.json` ·
`data/research/smc_v3/replay_run.log` · DECISIONS.md §SMC v3
