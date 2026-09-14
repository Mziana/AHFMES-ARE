# DECISIONS — strategy_v2 (append-only)

Format: tanggal | keputusan | alasan.

- 2026-09-08 | `zone clustering` di `zones.py` memakai definisi desain §B4
  (swing confirmed 5 kiri+kanan atas CLOSED bars, cluster 0.75×ATR(M15),
  band ±0.5×ATR, maks 5 zona/sisi, window 200 bar) | persis kontrak; DILARANG
  memanggil `getSupportResistanceZones` indicators.ts (lookahead `highs[i+k]`).
- 2026-09-08 | Dataset M5 7 Sep = 222 bar (00:00–18:25 UTC, kontinu) dari
  bridge `copy_rates_from_pos` (count=1200); jalur `copy_rates_range` beku
  200 bar (dokumentasi bridge P2-17). Bar 18:30–24:00 tidak tersedia →
  dicatat sebagai limitasi di REPORT_P2.md, TIDAK diinterpolasi/karangan.
- 2026-09-08 | Volume gate memakai `volume` dari dataset bridge (tick_volume
  broker) dengan terminologi "tick-activity proxy" | desain §B6.
- 2026-09-08 | News calendar 7 Sep tidak tersedia historis (bridge tidak
  menyediakan kalender historis) → replay P2 menjalankan B1 dengan
  policy `NEWS_CALENDAR_UNAVAILABLE` (fail-closed, reason code tetap
  terpisah dan teruji di invariant test) | jujur > karangan; desain mengizinkan
  reason code ini, dampaknya dihitung terpisah di funnel.
- 2026-09-08 | `spread` historis per-bar tidak ada di dataset candle bridge →
  cost model memakai fallback konstanta profil dengan label
  `ESTIMATED_COST_MODEL` di seluruh output | desain §4.
- 2026-09-08 | Bila M15 warmup < 50 bar pada awal window evaluasi (sebelum
  07:00 UTC), evaluasi sebelum warmup cukup tetap dijalankan tapi
  `H-Q1.min_bars_m15_warmup` dilaporkan di qualification report | transparan
  tanpa membuang data.
- 2026-09-08 | Schema gate enums diperluas dengan `DISABLED` utk semua gate
  (b4/b5/b6 sudah punya) | desain §1: DATA_INVALID → evaluasi strategi TIDAK
  dijalankan; schema wajib tetap bisa merepresentasikan record Layer B yang
  tidak berjalan tanpa melanggar `required: all_gate_results`.
- 2026-09-08 | SL final = `min_stop` (max dari SL ATR×mult dan floor spread);
  bila min_stop > cap → `FAIL:stop_bounds` (SKIP) | desain §B7 "SKIP, bukan
  clamp diam-diam" — SL tidak pernah dipaksa turun di bawah floor spread.
- 2026-09-08 | **Batasan max_trades_per_day (SCALP 6 / MICRO 20) DIHAPUS**
  dari profil, gate B7 (`FAIL:cap`), execution replay, dan schema —
  keputusan eksplisit owner. Override atas desain §B7 | kontrol risiko tetap
  terjaga via cooldown (30m/5m), stop bounds (SKIP), sizing konstan-dolar,
  dan Layer A. Per Pagar 1, perubahan ini = config_hash BARU = experiment
  identity baru; replay 7 Sep dijalankan ulang dengan identity baru.
- 2026-09-08 | P0-01 — Staleness B1 diukur dari `information_available_at`
  (waktu snapshot kalender diambil, field eksplisit artifact), BUKAN heuristic
  `max(event.ts)`; artifact tanpa provenance → fail-closed `NEWS_DATA_STALE`
  | temporal provenance: replay historis tidak boleh menganggap snapshot now
  tersedia di masa lalu; event_timestamp ≠ availability_timestamp.
- 2026-09-08 | P0-04 — Layer A kini memvalidasi M15 juga (regime/location
  timeframe): reason per-timeframe `DATA_INVALID:m15:<reason>`; M15 invalid →
  Layer B DISABLED (Pagar 3 tetap) | keputusan strategi bergantung M15, jadi
  M15 wajib tervalidasi sama seperti M5; schema pattern diperluas.
- 2026-09-08 | P0-01b — Look-ahead guard B1: `information_available_at` >
  now_ts → `NEWS_DATA_STALE` (informasi dari masa depan TIDAK tersedia pada T);
  artifact arsip menandai `archived: True` → age-check dilewati (jadwal
  mingguan memang berumur saat direplay) | replay historis tidak boleh
  menganggap snapshot now tersedia di masa lalu; snapshot FF 7 Sep di-fetch
  18:59Z SETELAH window evaluasi → B1 fail-closed 222/222 (klaim lama
  "PASS 222/222" adalah artefak heuristic max(event.ts)).
- 2026-09-08 | P0-04b — Layer A M15 mengizinkan gap >= 3600 dtk (break sesi
  pasar: maintenance harian broker ~4500 dtk, weekend ~177300 dtk — terukur
  nyata di dataset 7 Sep); gap 1–3 bar intra-sesi tetap `missing_bar` |
  struktur kalender pasar bukan korupsi data; konsisten dengan
  qualify_dataset (gap dilaporkan, tidak meng-invalidate).
- 2026-09-08 | P0-03 opsi A — slippage & delay DITERAPKAN nyata di execution
  replay: fill digeser delay_bars (rejection `delay_no_bar` bila bar tidak
  ada), slippage adverse pada harga fill (BUY +, SELL −); slippage TIDAK masuk
  deduksi USD (spread+commission saja) — double counting tertangkap test dan
  difix | cost model kini penuh, bukan fail-closed-only.
- 2026-09-08 | Pre-flight provenance: `run_profile` gagal cepat bila snapshot
  kalender non-archived postdates window evaluasi | funnel 100% veto B1 valid
  secara formal tapi tidak informatif — lebih baik gagal jelas di awal.
- 2026-09-08 | `archived` flag HANYA ditulis oleh save_calendar_artifact;
  load_calendar membacanya dari file (tidak lagi hard-coded True) | jalur
  live (snapshot provider) tetap kena age-check staleness.
- 2026-09-08 (F1b) | Bentuk exit BID/ASK (desain §10.1 E-1, PILIH SATU):
  BUY entry = open(BID) + spread + slippage (fill ASK), exit = level pada
  basis BID (tanpa spread di path), cost_usd = exit_spread + commission.
  SELL entry = open(BID) − slippage (dijual di BID, tanpa spread), exit =
  level + spread (tutup ASK; trigger ekuivalen BID = level − spread),
  cost_usd = entry_spread + commission | spread muncul TEPAT SATU KALI per
  arah per trade; round-trip flat invariant = −(entry+exit+comm)×pv×lot
  PERSIS untuk BUY & SELL (test_round_trip_invariant).
- 2026-09-08 (F1b) | Reversal policy (desain §10.1 E-3): `exit_then_reverse`
  — sinyal berlawanan saat posisi terbuka → posisi lama tutup pada bar sinyal
  (REVERSAL, mark-to-market close), sinyal baru fill next-bar-open + delay.
  Cooldown tetap berlaku untuk entry reversal (konsisten E-3 "Cooldown tetap
  berlaku"). Policy SAMA untuk scalp & micro pada baseline ini | satu pilihan
  konsisten, teruji di state machine tests.
- 2026-09-08 (F1b) | Scan SL/TP KRONOLOGIS: posisi terbuka di-scan pada
  SETIAP record (cursor per posisi), bukan hanya saat sinyal berikutnya —
  posisi yang hit SL/TP di tengah dataset tutup pada bar hit-nya, dan
  sinyal setelahnya melihat state FLAT yang benar | tanpa ini posisi dengan
  hit di tengah dataset menggantung sampai EOD_MARK (PnL salah).
- 2026-09-08 (F1b) | Broker meta: bridge /account TIDAK expose `symbol_info`
  (verified) → `load_broker_meta({})` fallback konstanta XAUUSD dengan label
  FALLBACK; `point_value_usd_per_lot` DIHITUNG = contract_size × point
  (100 × 0.01 = $1/lot), bukan hardcode | Pagar 1: broker_meta_hash masuk
  config_hash; bila bridge menambah symbol_info, identity eksperimen berubah.
- 2026-09-08 (F1b) | Unit spread dideklarasi EKSPLISIT di satu-satunya
  tempat (run_profile): bridge spread = PRICE_1E4 (1700 = 0.17 harga = 17
  poin 0.01) → `normalize_spread(1700, PRICE_1E4)` = 17.0; replay menerima
  poin yang SUDAH dinormalisasi | unit tak dikenal → fail-closed
  (UnknownSpreadUnit); dilarang hardcode price_mult (E-2).
- 2026-09-08 (F2) | Window replay honesta = sesi dengan close ≥
  information_available_at kalender riil (Sep 7 18:59:42Z) → satu-satunya
  sesi: Sep 7 22:00 → Sep 8 08:25 (125 bar). Sesi Sep 1–4 + Sep 7 pagi
  ditolak provenance guard (P0-01) — kalender memang belum tersedia saat itu
  | jujur > window besar; JANGAN mengarang data (mandat §4).
- 2026-09-08 (F2) | Cost label: spread snapshot live (17 poin) diberi label
  `ESTIMATED_COST_MODEL`, BUKAN HISTORICAL — spread konstanta snapshot bukan
  spread historis per-bar; compute_cost menerima `spread_label` override
  eksplisit | desain §4: estimasi tidak pernah disajikan sebagai market truth.
- 2026-09-08 (F2) | Dataset multi-sesi M5 (Sep 1–8, 6 sesi) ditarik via
  bridge copy_rates_from_pos count=1200; replay per sesi (break maintenance
  bukan korupsi data; M5 Layer A strict gap tetap). F2 memakai sesi honesta
  saja | M5 tidak bisa di-concat silang break (mengarang data).

## Analyst Desk v2.5 (2026-09-09) — layer presentasi 7-langkah (plan .hermes/plans/2026-09-08_133000)
- Step 4/6/7 diimplement sebagai layer DI ATAS gate engine: H-SCORE-DESK-01
  (deskriptif, triage WATCH>=40/PAPER>=60/TRADE>=75), trade plan narrative
  deterministik (template + angka record, dilarang LLM), journal paper
  append-only + review report USULAN (tanpa auto-tune). Pagar 1: semua param
  baru via registry; skor TIDAK dipakai decide() — layer separation teruji
  (hapus/mutasi H-SCORE-DESK-01 → keputusan identik).
- Trade plan bahasa Inggris (konsisten decision log; open question plan §2).
- Tier PAPER di-paper-trade OTOMATIS di research plane memakai simulator F1b
  yang sama (run_execution_replay — satu simulator, anti cost-soup); approval
  manual hanya untuk live (open question plan §1).
- Field decision log baru OPTIONAL (backward-compatible): setup_score,
  trade_plan, risk_calc, market_snapshot.close. Record lama tetap valid.

## P4 (2026-09-08) — Keputusan gate hasil ablation (dataset 86014edf…)
- B3 regime + B4 location: NONAKTIF utk MICRO — kehadirannya menurunkan expNet (−1,67 → +3,22 saat keduanya off, 136 trade). Revisi hipotesis terdaftar, bukan tweak.
- B5 trigger: DIPERTAHANKAN — dilepas expNet −1,67 → −4,17 (kontribusi ±2,5/trade).
- B1 news: DISABLED terlabel utk replay riset (kalender historis per-bar tidak ada); jalur live tetap aktif.
- Juara P4: MICRO no_b3_b4 (+b1 off) — expNet +3,22/trade. Frozen utk P5/P6; caveat long-only di uptrend diuji WFO OOS.

## MICRO v2 "SCALP-M1" (2026-09-11) — studi offline, VERDICT KILL_ALL
- Desain owner-lock (diskusi 2026-09-11): replika mesin SCALP turun satu TF —
  eksekusi M1 close, bias momentum M5 (EMA9/21+RSI 45/55), RSI guard M5+M1,
  skor candle SCALP thr 7, SL/TP mult × ATR M5, cooldown 5 menit, satu posisi/arm.
  Grid 8 varian: volume {1.0,1.2}× × RSI {65/35, 70/30} × SL/TP {1.1/1.7, 1.25/2.0}.
  Bonus +1 volume di-decouple (tetap hanya di ≥1.2×).
- Hasil (41.2 hari, 39.999 bar M1, sel biaya R1 base 17 / must 27.5 poin):
  SEMUA varian KILL — expMust −27.31 s/d −27.46 poin/trade, WR 38.7–40.9% vs
  breakeven-gross 39.3% (gross edge ≈ +0.05 poin/trade). n 493–874 (≥30 semua).
- Kontrol SCALP M5 produksi di jendela sama: KILL juga (n=267, WR 40.4%,
  expMust −14.28) → seluruh pipeline pola-candle ini gross-breakeven di window
  ini; SCALP live 4W/1L (+39.90$) = sampel terlalu kecil untuk klaim edge.
- Konsekuensi keputusan: (1) swap MICRO v2 TIDAK dilakukan; arm MICRO tetap
  NONAKTIF (toggle owner); (2) SCALP M5 tetap jalan + kill switch 3L/30m +
  review ulang setelah n live ≥ 20; (3) tanpa tweak varian (kontrak R1).
- Pelajaran struktural: SL/TP × ATR M5 tidak bisa menghasilkan "receh"
  (TP rata-rata varian utama 811 poin) — target TP kecil + spread demo ~20 poin
  = jebakan biaya MICRO v1 berulang. Arah riset berikutnya: dekomposisi bucket
  gross (sesi/jam/arah/pola), biaya real per jam dari deal history, atau geser
  frekuensi/sumber sinyal.
- Rekonsiliasi jurnal (backfill rev5): open+close SCALP 429141720 (+18.04,
  BUY 4405.03→4414.05) yang hilang saat restart driver direkonstruksi eksak
  position_id dari deal IN `R1-SCALP` → jurnal 23/23 open-close, 0 null,
  GLOBAL +0.10$ (MICRO −39.80 · 5W/13L · 28% | SCALP +39.90 · 4W/1L · 80%).
- Artefak: scripts/micro_v2_study.py · scripts/micro_v2_control.py ·
  data/research/micro_v2/study_results.json · control_scalp_m5.json ·
  strategy_v2/REPORT_MICRO_V2_STUDY.md

## MICRO v2.1 "SCALP-M1 0.9/1.4" (2026-09-11) — GO live demo (owner "oke mulai")
- Owner menyetujui implementasi mesin MICRO v2.1 dgn geometri revisi
  SL 0.9 / TP 1.4 × ATR M5 (menggantikan 1.1/1.7 dari studi), sengaja TANPA
  lensa biaya: "jangan pikirkan biaya spread dulu, kita lihat realnya dulu".
  Keputusan owner FINAL meski studi offline menunjukkan varian ini gross-flat
  (WR 40.1%, n=983, 41 hari) dan KILL di sel must — diuji langsung di demo.
- Konfigurasi live = replika persis studi varian v1.0|65_35|M0.9_T1.4:
  eksekusi M1 close, bias momentum M5 (EMA9/21+RSI 45/55), RSI guard 65/35
  M5+M1, volume wajib 1.0x (bonus +1 tetap hanya 1.2x), threshold 7, cooldown
  5 menit, lot rule lama. Tag jurnal tetap "MICRO" (UI/toggle/KS tetap).
- Implementasi: strategy_v2/micro_v2.py (pure decision layer, replika
  score_for_variant studi) + wiring demo_driver._run_arm (MICRO ->
  MICRO_V2.decide; SCALP tetap SV.decide produksi). Validasi: py_compile OK,
  smoke test live (guard RSI 33<=35 memblokir SELL — perilaku tepat), rasio
  TP/SL 1.556 terverifikasi (SL 451p/TP 702p @ ATR 501p), test kontrak rev3
  18 passed, tsc demo bersih, deskripsi kartu UI di-update.
- Driver restart via kontrol resmi (PID 28208); MICRO DIAKTIFKAN owner-toggle
  (persisten dari rev5 tetap NONAKTIF setelah restart — diaktifkan eksplisit).
- Review: setelah n>=20 trade live, bandingkan WR & expectancy vs replay
  (WR 40.1%, gross-flat; kontrol SCALP M5 40.4%/expMust -14.28). Kriteria
  keputusan review menyusul data live; kill switch 3L/30m tetap aktif.
- Artefak: strategy_v2/micro_v2.py · strategy_v2/demo_driver.py ·
  UI/src/app/demo/page.tsx (kartu) · data/research/micro_v2/study_results_
  v2_sl09_tp14.json (basis replika)
- Klarifikasi record live SCALP (konfirmasi owner 2026-09-11): 1 loss
  (428419669, -14.66, SL 08:05 WIB 10 Sep) terjadi SEBELUM rev2 — config lama
  yg masih pakai struktur HH/HL + H4. Record live config SCALP-rev2 (struktur
  dihapus, arah dari momentum M15) = 4W/0L (429141720/429235206/428889314/
  428858312). Sampel rev2 tetap 4 trade — review n>=20 tetap berlaku; replay
  kontrol (config rev2) di hari yg sama 5W/2L — live menghindari 2 loss itu
  krn rem operasional (1 posisi/arm, cooldown, KS) + timing, bukan krn config
  berbeda.

## OPS-REV6 - Watchdog + spawn WMI (2026-09-11, owner request)
Akar kasus "6 jam tanpa eksekusi": driver demo anak proses Next dev-server,
bridge anak shell Freebuff -> keduanya mewarisi Windows job object
kill-on-close; Freebuff ditutup 01:26 WIB => bridge+driver mati diam-diam
sampai launcher di-restart 06:04 (log r1_demo_2026-09-10T23-04-55.log).
Perbaikan (logic entry TIDAK disentuh):
- scripts/wmi-spawn.ps1: spawn via WMI Win32_Process.Create -> proses anak
  WmiPrvSE, di luar job Freebuff (kebal penutupan Freebuff).
- scripts/are_watchdog.ps1: watchdog 30s (bridge /health + heartbeat driver),
  toast Windows saat putus/pulih, auto-restart bridge/driver via WMI,
  heartbeat data/logs/are_watchdog_heartbeat.json (badge UI).
- Route demo/control START -> WMI; driver teelog driver_log.txt; bridge
  teelog bridge_server.log; fix teks pesan volume gate (kosmetik saja).
Migrasi live: bridge PID 16376, driver PID 18344 (keduanya anak WmiPrvSE),
watchdog PID 7804; toast WinRT teruji.
- Revisi MICRO v2.1 -> v2.1.1 (owner 2026-09-11 sore): gate volume M1
  diperketat 1.0x -> 1.1x avg5 ("MICRO masih lucky shot"; 2W/1L perdana
  terlalu kecil sampel). Bonus +1 tetap hanya di >=1.2x (decouple).
  Hanya konstanta VOL_MIN di strategy_v2/micro_v2.py — logic entry lain
  tidak disentuh. Ekspektasi dari replay 41 hari: antara v1.0 (983 trade,
  WR 40.1%) dan v1.2 (673, WR 42.2%). Driver restart PID 27020 (WMI).

## OPS-REV7 - Shadow A/B + dekomposisi sesi (2026-09-11 malam, owner approve)
Pertanyaan owner: beda sesi London vs lainnya di replay MICRO v1.1 (807 trade,
41.3 hari)? Temuan dekomposisi (scripts/micro_v2_session_decomp.py, artefak
data/research/micro_v2/session_decomp_v11.json):
- WR per sesi hampir datar: asia 43.1%, london 43.4%, overlap 42.2%,
  ny_late 39.2% - sesi BUKAN pembeda WR utama.
- London pembeda terbesarnya ARAH: SELL 48.5% (n=101, gross +0.8 pts/tr)
  vs BUY 37.9% (n=95, gross -0.1). Asia justru WR terbaik utk BUY.
- Overlap BUY 47.5% (+1.0) tapi SELL 34.9% (-1.3) - polar, n kecil.
- London jam 09:00 UTC WR 52.8% (n=36) terbaik; 08:00 terburuk 34.2%.
Keputusan owner: (1) shadow A/B runner - strategy_v2/shadow_ab.py, kandidat
A_base (mirror live) / B_london_sell (London SELL-only) / C_london_all,
dievaluasi tiap close M1 tanpa order, state persisten, journal
shadow_ab_journal.jsonl, ringkasan di driver_state.shadow; (2) varian
"jendela emas London" tidak diimplementasi langsung - menunggu data shadow
(n>=30 per kandidat) sebelum swap. Arm live TIDAK berubah.

## OPS-EXITGEO - Exit Geometry MICRO D+E (2026-09-11 malam, owner approve)
Akar masalah: geometri 0.9/1.4xATR-M5 memberi TP tak terjangkau karakter M1
(ticket 431035015: TP 923.9 pts, harga balik dalam $5; MICRO v2.1.1 hari ini
1W/7L, kill switch 4x memotong streak 7). Doktrin exit owner 7 butir
(doktrin 1-7) dipetakan ke dua kandidat shadow (owner pilih DUA-DUANYA):
- D_exit (EXIT-D-01): entry parity A_base, SL tetap 0.9xATR-M5; exit diganti
  D1 cap TP 600 pts + D2 clamp 0.25xATR sebelum swing berlawanan M5/M15
  (sisa TP < 100 pts -> REJECT, fail-closed) + D4 RSI-burn (pola searah bias
  & RSI-M1 >60 BULL / <40 BEAR -> TP x0.7) + D5 early exit (posisi profit +
  pola berbalik ATAU momentum habis + EMA9/21 M1 cross ATAU RSI patah 50).
  Urutan deterministik: cap -> burn -> clamp (clamp selalu terakhir).
- E_atr_m1 (EXIT-E-01): SL/TP 0.9/1.4 x ATR-M1 - skala ikut TF eksekusi,
  jawaban fundamental saat ATR-M5 membesar; tanpa cap/clamp/burn.
Implementasi: strategy_v2/exit_geometry.py (pure, whitelist import dijaga
test struktural); kandidat D/E append ke shadow_ab.py (A/B/C bit-identik);
on_m1_close terima m15 utk clamp; registry EXIT-D-01/EXIT-E-01 parent
H-EXEC-M1-01 (Pagar 1 - semua angka di registry/modul). TDD: RED dulu
(20 test), full suite 1079 passed. D7 (SL anti-hunt) = studi data
(sl_hunt_study), bukan rule; buffer sl_buffer_pts=0 sampai dikalifikasi.
Rollout 19:50 WIB: restart driver via jalur resmi (watchdog respawn, PID
24524) - dipilih saat tidak ada posisi open live/shadow. Kandidat D/E
n=0; review pada n>=30 per kandidat (kontrak shadow swap).

## SMC v3 - replay studi offline + bug-fix SL (2026-09-11 malam)
Engine kandidat pengganti MICRO (strategy_v2/smc.py, rencana owner 11 Sep:
POI + sweep + CHoCH mikro + pola, skor 12, RR>=1.3) direplay offline 39.2
hari (scripts/smc_v3_study.py, parity jendela live M1/M5 400 bar, cooldown
5m, 1 posisi, sel biaya R1 base 17/must 27.5). Dua temuan:
- BUG engine ditemukan replay pertama & diperbaiki SEBELUM hasil dipakai:
  anchor SL dari extrem sweep STALE di sisi salah harga (`ext < (sl_base
  or 1e9)` selalu true saat sl_base None) → BUY dgn SL di ATAS entry, RR
  palsu (5.95) lolos gate, 13 trade "SL" dgn gross positif. Fix: anchor
  sweep wajib di sisi benar dari harga sekarang + guard fail-closed
  "SL wajib di sisi benar" + 2 test regresi (test_engine_never_takes_with_
  inverted_sl, test_engine_sl_side_invariant_on_take). Zona OB juga diperbaiki
  body-only → range penuh H/L (SL di luar wick, test displacement hijau).
- HASIL honesta (engine fixed, n=139, 36.6k evaluasi): VERDICT KILL -
  WR 32.4% vs breakeven-gross 34.2% (RR rata-rata 1.92, avg SL 382/TP 721
  pts); gross -16.99 pts/trade → net must -44.49. Kontrak keputusan terpenuhi
  (n>=30, expNet_must << 0). Dekomposisi (n kecil, lead bukan konfirmasi):
  SELL gross ~+5.8/tr vs BUY -45.9/tr; london 45.5% (+1757 pts) & ny_late
  positif gross, overlap terburuk (-4149). Funnel: rr_gate 59% + bias H4
  netral 35% → engine sangat selektif (3.5 sinyal/hari) tapi edge bruto
  tidak ada di window ini - pola sama dgn MICRO v2: geometri jauh (SL 382
  pts) + biaya must 27.5 pts memakan semua edge.
- Keputusan: KILL DITUNDA oleh owner (11 Sep malam) setelah audit kepatuhan
  vs desain - lihat REPORT_SMC_V3_CHECKLIST.md. Bukti audit (sampling 6.600
  bar): mekanika inti sesuai desain (SL-side invariant 74/74, bobot skor
  persis §7, aturan emas arah terpenuhi) TAPI 4 gap kepatuhan: G2 exit
  desain (partial 50%+BE) belum direplay = vonis mengukur engine tanpa
  manajemen exit desain; G1 gate item-8 (spread/ATR) belum ada; G3 BOS
  "sebelum retrace POI" tidak dienforce temporal; G4 bias D1 belum dipakai.
  Mitigasi OB/FVG basis CLOSE = deviasi disengaja, menunggu konfirmasi owner.

## SMC v3 - verifikasi review + redundansi BOS (2026-09-12)
Owner (via REVIEW_TANGGAPAN_SMC_V3.md) setuju KILL DITUNDA; G2 = prasyarat
keputusan; review menemukan kecurigaan redundansi Bias<->BOS (pass-rate
67,3% = 67,3%). Diverifikasi pada cache 5 bulan (8 Apr-9 Sep, 11.235 sampel,
H4 = agregasi 16xM15, bridge sedang mati): P(BOS searah | bias non-netral)
= 100,0% -> item BOS (bobot 1) DETERMINISTIK menyertai bias (bobot 2) -
skor efektif max 11 bukan 12; threshold >=8 efektif lebih longgar. Umur BOS
saat item OK: median 129 bar M5 (p75 275, maks 399) -> item #4 tidak
mengukur friskness sama sekali. Konsekuensi keputusan: (1) kalibrasi
threshold DILARANG sebelum G3 (poin harus independen dulu); (2) G3 = BOS
hanya dihitung bila umur <= N bar M5, N dari sweep {24,36,48} di replay
(tanpa pilih diam-diam); (3) reframing statistik diterima: CI95 WR
[24,6%, 40,2%] memuat breakeven 34,2% -> 'belum cukup bukti', bukan
'terbukti tidak ada edge'; (4) segmentasi WR per skor TIDAK konklusif
(88% trade di skor 9; n bucket 2-3) - diulang pasca-G2; (5) klaim per
bucket sesi/arah turun jadi lead-only (n 22-70); (6) kontrak test G2/G3
tertulis di RESPON_REVIEW_SMC_V3.md bab 4 (SL tak pernah mundur dari BE,
invariant 50/50, sweep N dilaporkan semua). KONSEKUENSI OPERASIONAL:
semua python stack (bridge+driver+watchdog) mati saat analisis - TIDAK
dinyalakan tanpa konfirmasi owner; replay G2 butuh bridge hidup.
Artefak: strategy_v2/RESPON_REVIEW_SMC_V3.md · data/research/smc_v3/
smc_v3_redundancy.json · smc_v3_segmentation.json · scripts/smc_v3_
redundancy.py. Prioritas kerja mengikuti review bab 6: G2 -> G3+kalibrasi
-> segmentasi ulang -> G1/G4 -> sensitivity POI_REACH & TP1-target ->
window multi-regime.
- Artefak: scripts/smc_v3_study.py · data/research/smc_v3/smc_v3_replay.json
  · data/research/smc_v3/replay_run.log · strategy_v2/REPORT_SMC_V3.md
- 2026-09-12 | Replay full-parity SMC v3 (G1+G2+G3+G4) DIJALANKAN, SEMUA gap
  CLOSED di jalur evaluasi/replay; TIDAK ADA keputusan kill/viability —
  bukti diserahkan ke owner | hasil: baseline regressed IDENTIK ke studi
  lama (n=139, gross −16.99, TP44/SL94/EXPIRE1) → harness valid. G2 exit §4
  (TP1 50%→BE→trailing, smc_exits.py): NETRAL — n 137, net-must −44.49→
  −45.71; atribusi 136 matched: 92 SL→SL_full, 40 TP→TP1_TRAIL (696→711.6
  pts), 3 TP→TP1_BE (BE menyelamatkan +355.5/+89.5/+182.5), 0 SL→BE (SL
  struktural median >300 pts terlalu jauh utk perjalanan TP1→BE). G3
  freshness BOS b24=b36=b48 identik (1 trade dihapus, SELL −539) — hampir
  tanpa efek; redundansi Bias↔BOS tetap diblokir utk kalibrasi. G1 gate
  item-8 aktif tapi no-op di window (spread snapshot 17<35; ATR-M5 171–
  1168 di dalam band [120,2500], 0 blok). G4 bias D1 (rantai penuh
  M15→H4→D1, ≥25 bar): 436 take → 213 veto + 212 warmup D1 → 11 selamat
  (semua BUY, 24–27 Agu), WR 45.5% vs breakeven 25.6%, gross +188.7/tr,
  CI95 WR [16%,75%] → TIDAK disimpulkan; parity penuh n=10 gross +125.7/tr.
  Catatan kejujuran: sim UNDERSTATE biaya live (sim A −12.34$ vs live
  −28.32$) → arah perbandingan antar-varian yang jadi bukti, bukan dolar.
  Jendela dipin kedua tepi (3 Agu 11:39→11 Sep 17:08 UTC) + emulasi feed
  lama (M5 8k/M15 3k/H4 250) — baseline identik = regresi silang. Rumah
  angka: strategy_v2/REPORT_SMC_V3_PARITY.md · data/research/smc_v3/
  smc_v3_parity_replay.json · scripts/smc_v3_parity_replay.py. Suite test
  159 hijau; arm live/shadow tidak disentuh. Antrian berikut (urut review
  owner): replay window panjang multi-regime (D1 matang) → bereskan
  redundansi Bias↔BOS → kalibrasi threshold → sensitivity POI_REACH/TP1.
- 2026-09-14 | Sensitivity POI (prio 7) + window sideways (prio 8) + kurva
  threshold (prio 4, peta saja) DIJALANKAN dalam satu replay 2-pass; TIDAK
  ADA keputusan kill/keep — bukti ke owner | pass TREND: jendela terpin
  39.23 hari (== parity), 39.598 bar; pass SIDE: 2026-06-04T21:52+10d dari
  cache R1, DIPILIH OLEH regime-scan BUTA PnL (ER-Kaufman 0.0044 terendah,
  rng 16.0xATR-H4, trend None, ATR5 674p; efektif 7.95 hari — cache M5
  berakhir ~12 Jun). 4 konfig POI dievaluasi terpisah di engine
  (poi_reach/poi_mode param baru, default = perilaku lama persis; test
  test_smc_sensitivity_params.py). HASIL: (a) POI makin ketat makin baik
  di KEDUA window — trend: gross/tr −16.99→−1.36 (strict), side: strict
  satu-satunya positif +111.3 net-must (legacy) / +2.5 (G2), WR 43.8%
  sementara default 1.5xATR −204.1/−274.1; (b) G2 exit §4 versi engine
  saat ini KONSISTEN MENGURANGI vs first-touch (lawan arah dari parity —
  TP1 sini = target likuiditas sama, trailing memberi balik sebelum leg
  penuh; keputusan geometri tetap owner); (c) kurva threshold MONOTON
  TURUN (≥6 WR 33.4% → ≥11 WR 17.9%, gross +48→−327/sinyal) — skor tinggi
  ≠ kualitas; konsisten redundansi Bias↔BOS; kalibrasi TETAP DITAHAN
  (redundansi belum beres). Regresi silang: poi_d150/legacy == parity
  baseline PERSIS (139 / −16.99 / −44.49). Keterbatasan jujur: window
  side dari dataset sim sama (bukan independen penuh), n side kecil
  (16–22), news gate OFF, spread snapshot, M1 sintetis 5-bar/M5 di pass
  side (exit-sim saja), sim understates live. Rumah angka:
  strategy_v2/REPORT_SMC_V3_SENSITIVITAS.md · data/research/smc_v3/
  smc_v3_sensitivity_replay.json · smc_v3_regime_scan.json · scripts/
  smc_v3_sensitivity_replay.py · scripts/smc_v3_regime_scan.py. Pertanyaan
  terbuka owner: ganti default POI_REACH?; geometri exit (§4 vs TP2-leg);
  lanjut resolusi redundansi Bias↔BOS?
